"""Canonical path order, not host Path comparison, determines vendor identity."""

import hashlib
import tempfile
import unittest
from pathlib import Path

from engine.vendor import materialize
from engine.vendor.manifest import bundled_dependency
from tools import vendor_refresh


ROOT = Path(__file__).resolve().parents[1]


class VendorDigestPortabilityTests(unittest.TestCase):
    # Explicit order includes case and directory-prefix traps. No case-only
    # duplicate filenames: the same fixture is representable on Windows/Linux.
    FILES = (
        ("Z.py", b"upper\n"),
        ("a.py", b"lower\r\n"),
        ("dir-1.txt", b"sibling\x00"),
        ("dir/a.txt", b"nested\n"),
    )

    def assert_canonical_fixture(self, calculate):
        expected = hashlib.sha256()
        for name, payload in self.FILES:
            expected.update(name.encode("utf-8") + b"\0")
            expected.update(hashlib.sha256(payload).digest())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, payload in reversed(self.FILES):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
            self.assertEqual(calculate(root), expected.hexdigest())
            (root / "a.py").write_bytes(b"lower\n")
            self.assertNotEqual(calculate(root), expected.hexdigest())

    def test_runtime_digest_uses_relative_posix_string_order(self):
        self.assert_canonical_fixture(materialize._tree_sha256)

    def test_maintenance_digest_uses_relative_posix_string_order(self):
        self.assert_canonical_fixture(vendor_refresh._tree_sha256)

    def assert_pinned_package(self, name, directory, extract):
        row = bundled_dependency(name, ROOT / "vendor" / "manifest.json")
        with tempfile.TemporaryDirectory() as target:
            root = Path(target)
            extract(materialize._artifact_bytes(ROOT, row), root)
            for calculate in (materialize._tree_sha256, vendor_refresh._tree_sha256):
                self.assertEqual(
                    calculate(root / directory), row["vendored_tree_sha256"], name
                )

    def test_lunar_python_raw_bytes_match_existing_manifest(self):
        self.assert_pinned_package("lunar-python", "lunar_python", materialize._extract_lunar)

    def test_tzdata_raw_bytes_match_existing_manifest(self):
        self.assert_pinned_package("tzdata", "tzdata", materialize._extract_tzdata)


if __name__ == "__main__":
    unittest.main()
