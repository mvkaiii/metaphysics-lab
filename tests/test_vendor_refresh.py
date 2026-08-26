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


def _write_artifacts(directory: Path, *, forbidden_public_import: bool = False):
    directory.mkdir(parents=True, exist_ok=True)
    lunar = directory / LUNAR_NAME
    tzdata = directory / TZDATA_NAME
    _write_lunar_sdist(lunar, forbidden_public_import=forbidden_public_import)
    tzif = _write_tzdata_wheel(tzdata)
    return lunar, tzdata, tzif


class VendorRefreshTests(unittest.TestCase):
    def _patched_hashes(self, lunar: Path, tzdata: Path):
        return (
            patch.object(vendor_refresh, "LUNAR_SHA256", _sha256(lunar)),
            patch.object(vendor_refresh, "TZDATA_SHA256", _sha256(tzdata)),
        )

    def test_materialize_uses_artifact_dir_writes_only_vendor_storage_and_preserves_resources(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            repo = temp / "repo"
            repo.mkdir()
            artifacts = temp / "artifacts"
            lunar, tzdata, tzif = _write_artifacts(artifacts)
            lunar_patch, tz_patch = self._patched_hashes(lunar, tzdata)
            with lunar_patch, tz_patch:
                manifest = vendor_refresh.materialize_vendor(repo, artifacts)

            self.assertFalse((repo / "_metaphysics_lab_vendor").exists())
            self.assertEqual(
                json.loads((repo / "vendor" / "manifest.json").read_text(encoding="utf-8")),
                manifest,
            )
            self.assertTrue((repo / "vendor" / "licenses" / "lunar-python-LICENSE.txt").is_file())
            self.assertTrue((repo / "vendor" / "licenses" / "tzdata-LICENSE.txt").is_file())
            rows = {row["package_name"]: row for row in manifest["packages"]}
            self.assertRegex(rows["lunar-python"]["vendored_tree_sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(rows["tzdata"]["vendored_tree_sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(rows["tzdata"]["iana_version"], "2026c")
            self.assertTrue(tzif.startswith(b"TZif"))

    def test_manifest_has_ordered_artifact_parts_with_exact_counts_and_hashes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            repo = temp / "repo"
            repo.mkdir()
            artifacts = temp / "artifacts"
            lunar, tzdata, _ = _write_artifacts(artifacts)
            lunar_patch, tz_patch = self._patched_hashes(lunar, tzdata)
            with lunar_patch, tz_patch:
                manifest = vendor_refresh.materialize_vendor(repo, artifacts)

            for row in manifest["packages"]:
                parts = row["artifact_parts"]
                self.assertEqual([part["path"] for part in parts], row["artifact_shards"])
                for part in parts:
                    payload = (repo / part["path"]).read_bytes()
                    self.assertEqual(part["char_count"], len(payload))
                    self.assertEqual(part["sha256"], hashlib.sha256(payload).hexdigest())
                    self.assertEqual(row["artifact_shard_sha256"][part["path"]], part["sha256"])

    def test_check_is_non_mutating_and_detects_repository_vendor_drift(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            repo = temp / "repo"
            repo.mkdir()
            artifacts = temp / "artifacts"
            lunar, tzdata, _ = _write_artifacts(artifacts)
            lunar_patch, tz_patch = self._patched_hashes(lunar, tzdata)
            with lunar_patch, tz_patch:
                vendor_refresh.materialize_vendor(repo, artifacts)
                before = {p.relative_to(repo).as_posix(): p.read_bytes() for p in (repo / "vendor").rglob("*") if p.is_file()}
                vendor_refresh.check_vendor(repo, artifacts)
                after = {p.relative_to(repo).as_posix(): p.read_bytes() for p in (repo / "vendor").rglob("*") if p.is_file()}
                self.assertEqual(after, before)
                shard = next((repo / "vendor" / "artifacts").iterdir())
                shard.write_bytes(shard.read_bytes() + b"drift")
                with self.assertRaises(vendor_refresh.VendorRefreshError):
                    vendor_refresh.check_vendor(repo, artifacts)
                self.assertTrue(shard.read_bytes().endswith(b"drift"))

    def test_cli_supports_artifact_dir_check_and_materialize_modes(self):
        parser = vendor_refresh._parser()
        materialize = parser.parse_args(["--artifact-dir", "/tmp/vendor", "--materialize"])
        check = parser.parse_args(["--artifact-dir", "/tmp/vendor", "--check"])
        self.assertTrue(materialize.materialize)
        self.assertFalse(materialize.check)
        self.assertTrue(check.check)
        self.assertFalse(check.materialize)

    def test_artifact_hash_mismatch_fails_before_replacing_existing_vendor_tree(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            repo = temp / "repo"
            existing = repo / "vendor"
            existing.mkdir(parents=True)
            marker = existing / "keep.txt"
            marker.write_text("keep\n", encoding="utf-8")
            artifacts = temp / "artifacts"
            lunar, tzdata, _ = _write_artifacts(artifacts)

            with patch.object(vendor_refresh, "LUNAR_SHA256", "0" * 64), patch.object(
                vendor_refresh, "TZDATA_SHA256", _sha256(tzdata)
            ):
                with self.assertRaises(vendor_refresh.VendorRefreshError):
                    vendor_refresh.materialize_vendor(repo, artifacts)

            self.assertEqual(marker.read_text(encoding="utf-8"), "keep\n")

    def test_forbidden_public_vendor_import_is_rejected_before_repo_mutation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            repo = temp / "repo"
            repo.mkdir()
            artifacts = temp / "artifacts"
            lunar, tzdata, _ = _write_artifacts(artifacts, forbidden_public_import=True)
            lunar_patch, tz_patch = self._patched_hashes(lunar, tzdata)
            with lunar_patch, tz_patch:
                with self.assertRaises(vendor_refresh.VendorRefreshError):
                    vendor_refresh.materialize_vendor(repo, artifacts)

            self.assertFalse((repo / "_metaphysics_lab_vendor").exists())
            self.assertFalse((repo / "vendor").exists())


if __name__ == "__main__":
    unittest.main()
