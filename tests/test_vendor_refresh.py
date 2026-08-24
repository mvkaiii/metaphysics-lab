import hashlib
import io
import json
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from tools import vendor_refresh


LUNAR_NAME = "lunar_python-1.4.8.tar.gz"
TZDATA_NAME = "tzdata-2026.3-py2.py3-none-any.whl"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _add_tar_file(archive: tarfile.TarFile, name: str, payload: bytes) -> None:
    info = tarfile.TarInfo(name)
    info.size = len(payload)
    info.mtime = 0
    archive.addfile(info, io.BytesIO(payload))


def _write_lunar_sdist(path: Path, *, forbidden_public_import: bool = False) -> None:
    with tarfile.open(path, mode="w:gz") as archive:
        root = "lunar_python-1.4.8"
        _add_tar_file(
            archive,
            root + "/lunar_python/__init__.py",
            b'__version__ = "1.4.8"\nfrom .Solar import Solar\n',
        )
        solar = b"import lunar_python\n" if forbidden_public_import else b"class Solar:\n    pass\n"
        _add_tar_file(archive, root + "/lunar_python/Solar.py", solar)
        _add_tar_file(archive, root + "/LICENSE", b"Synthetic MIT license text for extraction tests.\n")


def _write_tzdata_wheel(path: Path) -> bytes:
    tzif = b"TZif2\x00\xffsynthetic-binary-zone\x00"
    with zipfile.ZipFile(path, mode="w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr(
            "tzdata/__init__.py",
            '__version__ = "2026.3"\nIANA_VERSION = "2026c"\n',
        )
        archive.writestr("tzdata/zones", "Asia/Taipei\nAmerica/New_York\n")
        archive.writestr("tzdata/zoneinfo/__init__.py", "")
        archive.writestr("tzdata/zoneinfo/Asia/Taipei", tzif)
        archive.writestr(
            "tzdata-2026.3.dist-info/licenses/LICENSE",
            "Synthetic Apache-2.0 license text for extraction tests.\n",
        )
    return tzif


class VendorRefreshTests(unittest.TestCase):
    def test_refresh_copies_complete_tzdata_package_root_and_binary_resources(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            repo = temp / "repo"
            repo.mkdir()
            lunar = temp / LUNAR_NAME
            tzdata = temp / TZDATA_NAME
            _write_lunar_sdist(lunar)
            tzif = _write_tzdata_wheel(tzdata)

            with patch.object(vendor_refresh, "LUNAR_SHA256", _sha256(lunar)), patch.object(
                vendor_refresh, "TZDATA_SHA256", _sha256(tzdata)
            ):
                manifest = vendor_refresh.refresh_vendor(repo, lunar, tzdata)

            self.assertEqual(
                (repo / "_metaphysics_lab_vendor" / "tzdata" / "zones").read_text(encoding="utf-8"),
                "Asia/Taipei\nAmerica/New_York\n",
            )
            self.assertEqual(
                (repo / "_metaphysics_lab_vendor" / "tzdata" / "zoneinfo" / "Asia" / "Taipei").read_bytes(),
                tzif,
            )
            self.assertTrue((repo / "vendor" / "licenses" / "lunar-python-LICENSE.txt").is_file())
            self.assertTrue((repo / "vendor" / "licenses" / "tzdata-LICENSE.txt").is_file())
            self.assertEqual(
                json.loads((repo / "vendor" / "manifest.json").read_text(encoding="utf-8")),
                manifest,
            )

    def test_artifact_hash_mismatch_fails_before_replacing_existing_vendor_tree(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            repo = temp / "repo"
            existing = repo / "_metaphysics_lab_vendor"
            existing.mkdir(parents=True)
            marker = existing / "keep.txt"
            marker.write_text("keep\n", encoding="utf-8")
            lunar = temp / LUNAR_NAME
            tzdata = temp / TZDATA_NAME
            _write_lunar_sdist(lunar)
            _write_tzdata_wheel(tzdata)

            with patch.object(vendor_refresh, "LUNAR_SHA256", "0" * 64):
                with self.assertRaises(vendor_refresh.VendorRefreshError):
                    vendor_refresh.refresh_vendor(repo, lunar, tzdata)

            self.assertEqual(marker.read_text(encoding="utf-8"), "keep\n")
            self.assertFalse((repo / "vendor").exists())

    def test_forbidden_public_vendor_import_is_rejected_before_repo_mutation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            repo = temp / "repo"
            repo.mkdir()
            lunar = temp / LUNAR_NAME
            tzdata = temp / TZDATA_NAME
            _write_lunar_sdist(lunar, forbidden_public_import=True)
            _write_tzdata_wheel(tzdata)

            with patch.object(vendor_refresh, "LUNAR_SHA256", _sha256(lunar)), patch.object(
                vendor_refresh, "TZDATA_SHA256", _sha256(tzdata)
            ):
                with self.assertRaises(vendor_refresh.VendorRefreshError):
                    vendor_refresh.refresh_vendor(repo, lunar, tzdata)

            self.assertFalse((repo / "_metaphysics_lab_vendor").exists())
            self.assertFalse((repo / "vendor").exists())


if __name__ == "__main__":
    unittest.main()
