import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from engine.vendor.manifest import bundled_dependency, bundled_vendor_manifest
from engine.vendor.materialize import materialize_private_vendor


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

    def test_public_manifest_api_returns_recursively_immutable_metadata(self):
        manifest = bundled_vendor_manifest()
        with self.assertRaises(TypeError):
            manifest["schema_version"] = "broken"

        tzdata = bundled_dependency("tzdata")
        with self.assertRaises(TypeError):
            tzdata["version"] = "0.0.fake"

        parts = tzdata["artifact_parts"]
        self.assertIsInstance(parts, tuple)
        self.assertGreater(len(parts), 0)
        with self.assertRaises(TypeError):
            parts[0]["path"] = "vendor/artifacts/fake"

    def test_manifest_loader_rejects_duplicate_packages_and_unsupported_schema(self):
        original = _load_manifest()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)

            duplicate = dict(original)
            duplicate["packages"] = list(original["packages"]) + [dict(original["packages"][0])]
            duplicate_path = temp / "duplicate.json"
            duplicate_path.write_text(json.dumps(duplicate), encoding="utf-8")
            with self.assertRaises(ValueError):
                bundled_vendor_manifest(duplicate_path)

            unsupported = dict(original)
            unsupported["schema_version"] = "999"
            unsupported_path = temp / "unsupported.json"
            unsupported_path.write_text(json.dumps(unsupported), encoding="utf-8")
            with self.assertRaises(ValueError):
                bundled_vendor_manifest(unsupported_path)

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

    def test_manifest_tree_hashes_match_materialized_private_package_bytes(self):
        manifest = _load_manifest()
        with tempfile.TemporaryDirectory() as temp_dir:
            materialize_private_vendor(ROOT, Path(temp_dir))
            for row in manifest["packages"]:
                root = Path(temp_dir) / row["vendored_path"]
                self.assertTrue(root.is_dir(), str(root))
                self.assertEqual(_tree_sha256(root), row["vendored_tree_sha256"], row["package_name"])

    def test_tree_hash_is_deterministic_across_materializations(self):
        manifest = _load_manifest()
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            materialize_private_vendor(ROOT, Path(first_dir))
            materialize_private_vendor(ROOT, Path(second_dir))
            for row in manifest["packages"]:
                first = _tree_sha256(Path(first_dir) / row["vendored_path"])
                second = _tree_sha256(Path(second_dir) / row["vendored_path"])
                self.assertEqual(first, second)
                self.assertEqual(first, row["vendored_tree_sha256"])


if __name__ == "__main__":
    unittest.main()
