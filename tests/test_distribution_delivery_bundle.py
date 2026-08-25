import base64
import hashlib
import io
import unittest
import zipfile

from engine.distribution.runtime import dispatch


class DistributionDeliveryBundleTests(unittest.TestCase):
    def test_build_delivery_bundle_returns_verified_zip_and_individual_markdown_from_same_bytes(self):
        files = {
            "命主索引.md": "# 命主索引\n\n- Amy\n",
            "Amy_A91B4D_00_專案索引.md": "# Amy｜專案索引\n",
        }
        result = dispatch("build_delivery_bundle", {"files": files})

        self.assertTrue(result["ok"], result)
        data = result["data"]
        self.assertEqual(data["filename"], "metaphysics_lab_case.zip")
        self.assertEqual(data["media_type"], "application/zip")
        self.assertEqual(data["encoding"], "base64")
        self.assertEqual(data["format_profile"], "zip-deflate-flat-markdown-v1")
        self.assertIs(data["status"]["generated"], True)
        self.assertIs(data["status"]["integrity_verified"], True)
        self.assertEqual(data["status"]["delivered"], "unknown")
        self.assertEqual(data["members"], sorted(files))

        individual = data["individual_files"]
        self.assertEqual([record["filename"] for record in individual], sorted(files))
        individual_bytes = {}
        for record in individual:
            filename = record["filename"]
            expected = files[filename].encode("utf-8")
            self.assertEqual(record["media_type"], "text/markdown")
            self.assertEqual(record["charset"], "utf-8")
            self.assertEqual(record["encoding"], "base64")
            self.assertIs(record["status"]["generated"], True)
            self.assertIs(record["status"]["integrity_verified"], True)
            self.assertEqual(record["status"]["delivered"], "unknown")
            decoded = base64.b64decode(record["content_base64"], validate=True)
            self.assertEqual(decoded, expected)
            self.assertEqual(record["size_bytes"], len(expected))
            self.assertEqual(record["sha256"], hashlib.sha256(expected).hexdigest())
            individual_bytes[filename] = decoded

        raw = base64.b64decode(data["content_base64"], validate=True)
        self.assertTrue(raw.startswith(b"PK"))
        self.assertEqual(len(raw), data["size_bytes"])

        with zipfile.ZipFile(io.BytesIO(raw), "r") as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(archive.namelist(), sorted(files))
            for info in archive.infolist():
                self.assertEqual(info.compress_type, zipfile.ZIP_DEFLATED)
                self.assertNotIn("/", info.filename)
                self.assertNotIn("\\", info.filename)
            for filename, expected in files.items():
                archived = archive.read(filename)
                self.assertEqual(archived, expected.encode("utf-8"))
                self.assertEqual(archived, individual_bytes[filename])

        repeated = dispatch("build_delivery_bundle", {"files": files})
        self.assertTrue(repeated["ok"], repeated)
        self.assertEqual(repeated["data"]["sha256"], data["sha256"])
        self.assertEqual(repeated["data"]["content_base64"], data["content_base64"])
        self.assertEqual(repeated["data"]["individual_files"], individual)

    def test_build_delivery_bundle_rejects_non_flat_or_non_markdown_members(self):
        for filename in ("../escape.md", "nested/file.md", "nested\\file.md", "/absolute.md", "notes.txt"):
            with self.subTest(filename=filename):
                result = dispatch("build_delivery_bundle", {"files": {filename: "demo"}})
                self.assertFalse(result["ok"])
                self.assertEqual(result["error"]["code"], "invalid_delivery_bundle_member")


if __name__ == "__main__":
    unittest.main()
