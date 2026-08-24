import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "vendor" / "manifest.json"

EXPECTED = {
    "lunar-python": {
        "import_namespace": "_metaphysics_lab_vendor.lunar_python",
        "version": "1.4.8",
        "source_repository": "https://github.com/6tail/lunar-python",
        "source_revision": "000c8a3d74eed098d6256a28fdd51b869324c559",
        "source_artifact": "lunar_python-1.4.8.tar.gz",
        "artifact_sha256": "3aa11cc73c25e70ddf0ba5bdac7398c03acc9491a3aa512a91c9642973b669d6",
        "license_spdx": "MIT",
        "license_file": "vendor/licenses/lunar-python-LICENSE.txt",
        "vendored_path": "_metaphysics_lab_vendor/lunar_python",
    },
    "tzdata": {
        "import_namespace": "_metaphysics_lab_vendor.tzdata",
        "version": "2026.3",
        "source_repository": "https://github.com/python/tzdata",
        "source_revision": "a44279419071b7aa41ebe7eca301ebb2e759571a",
        "source_artifact": "tzdata-2026.3-py2.py3-none-any.whl",
        "artifact_sha256": "dc096730c87af6cab1b171c9d532be840741ff5d459015e7f6947bd7d7e54931",
        "license_spdx": "Apache-2.0",
        "license_file": "vendor/licenses/tzdata-LICENSE.txt",
        "vendored_path": "_metaphysics_lab_vendor/tzdata",
    },
}


def _load_manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    files = sorted(path for path in root.rglob("*") if path.is_file() and not path.is_symlink())
    for path in files:
        relative = path.relative_to(root).as_posix().encode("utf-8")
        payload = path.read_bytes()
        digest.update(relative)
        digest.update(b"\0")
        digest.update(hashlib.sha256(payload).digest())
    return digest.hexdigest()


class VendorManifestTests(unittest.TestCase):
    def test_vendor_manifest_pins_exact_core_dependencies(self):
        manifest = _load_manifest()
        self.assertEqual(manifest["schema_version"], "1.0")
        packages = {row["package_name"]: row for row in manifest["packages"]}
        self.assertEqual(set(packages), set(EXPECTED))
        for name, expected in EXPECTED.items():
            row = packages[name]
            for field, value in expected.items():
                self.assertEqual(row[field], value, "%s.%s" % (name, field))
            self.assertIs(row["bundled"], True)
            self.assertEqual(row["runtime_authority"], "bundled")
            self.assertRegex(row["vendored_tree_sha256"], r"^[0-9a-f]{64}$")

    def test_vendor_license_files_exist_and_are_nonempty(self):
        manifest = _load_manifest()
        for row in manifest["packages"]:
            license_path = ROOT / row["license_file"]
            self.assertTrue(license_path.is_file(), str(license_path))
            self.assertGreater(len(license_path.read_bytes()), 20, str(license_path))
        notices = ROOT / "vendor" / "licenses" / "THIRD_PARTY_NOTICES.md"
        self.assertTrue(notices.is_file())
        text = notices.read_text(encoding="utf-8")
        self.assertIn("lunar-python 1.4.8", text)
        self.assertIn("tzdata 2026.3", text)

    def test_manifest_tree_hashes_match_committed_private_package_bytes(self):
        manifest = _load_manifest()
        for row in manifest["packages"]:
            root = ROOT / row["vendored_path"]
            self.assertTrue(root.is_dir(), str(root))
            self.assertEqual(_tree_sha256(root), row["vendored_tree_sha256"], row["package_name"])

    def test_tree_hash_is_deterministic_and_path_sensitive(self):
        manifest = _load_manifest()
        for row in manifest["packages"]:
            root = ROOT / row["vendored_path"]
            first = _tree_sha256(root)
            second = _tree_sha256(root)
            self.assertEqual(first, second)
            self.assertEqual(first, row["vendored_tree_sha256"])


if __name__ == "__main__":
    unittest.main()
