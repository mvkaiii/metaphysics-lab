import base64
import io
import unittest
import zipfile

from engine.distribution.runtime import dispatch


class DistributionDeliveryBundleTests(unittest.TestCase):
    def test_build_delivery_bundle_returns_verified_flat_standard_zip(self):
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
                self.assertEqual(archive.read(filename), expected.encode("utf-8"))

        repeated = dispatch("build_delivery_bundle", {"files": files})
        self.assertTrue(repeated["ok"], repeated)
        self.assertEqual(repeated["data"]["sha256"], data["sha256"])
        self.assertEqual(repeated["data"]["content_base64"], data["content_base64"])

    def test_build_delivery_bundle_rejects_non_flat_or_non_markdown_members(self):
        for filename in ("../escape.md", "nested/file.md", "nested\\file.md", "/absolute.md", "notes.txt"):
            with self.subTest(filename=filename):
                result = dispatch("build_delivery_bundle", {"files": {filename: "demo"}})
                self.assertFalse(result["ok"])
                self.assertEqual(result["error"]["code"], "invalid_delivery_bundle_member")


if __name__ == "__main__":
    unittest.main()
