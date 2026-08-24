#!/usr/bin/env python3
"""Refresh pinned private calendar dependencies from verified upstream artifacts.

This is an explicit maintenance tool. Normal builds and runtime execution must
never download dependencies or invoke this module automatically.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import shutil
import stat
import tarfile
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Dict, Optional, Sequence, Tuple

LUNAR_ARTIFACT = "lunar_python-1.4.8.tar.gz"
LUNAR_SHA256 = "3aa11cc73c25e70ddf0ba5bdac7398c03acc9491a3aa512a91c9642973b669d6"
LUNAR_VERSION = "1.4.8"
LUNAR_SOURCE_REPOSITORY = "https://github.com/6tail/lunar-python"
LUNAR_SOURCE_REVISION = "000c8a3d74eed098d6256a28fdd51b869324c559"

TZDATA_ARTIFACT = "tzdata-2026.3-py2.py3-none-any.whl"
TZDATA_SHA256 = "dc096730c87af6cab1b171c9d532be840741ff5d459015e7f6947bd7d7e54931"
TZDATA_VERSION = "2026.3"
TZDATA_IANA_VERSION = "2026c"
TZDATA_SOURCE_REPOSITORY = "https://github.com/python/tzdata"
TZDATA_SOURCE_REVISION = "a44279419071b7aa41ebe7eca301ebb2e759571a"

FORBIDDEN_PUBLIC_IMPORT_ROOTS = frozenset(("lunar_python", "tzdata"))
MANIFEST_SCHEMA_VERSION = "1.0"


class VendorRefreshError(RuntimeError):
    pass


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verified_artifact(path: Path, expected_name: str, expected_sha256: str) -> Path:
    path = Path(path)
    if not path.is_file():
        raise VendorRefreshError("artifact not found: %s" % path)
    if path.name != expected_name:
        raise VendorRefreshError("expected artifact %s, got %s" % (expected_name, path.name))
    actual = _sha256_file(path)
    if actual != expected_sha256:
        raise VendorRefreshError(
            "artifact SHA256 mismatch for %s: expected %s, got %s"
            % (expected_name, expected_sha256, actual)
        )
    return path


def _safe_archive_path(name: str) -> PurePosixPath:
    if not isinstance(name, str) or not name:
        raise VendorRefreshError("archive contains an empty path")
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or normalized.startswith("/"):
        raise VendorRefreshError("archive contains absolute path: %s" % name)
    if any(part in ("", ".", "..") for part in path.parts):
        raise VendorRefreshError("archive contains unsafe path: %s" % name)
    return path


def _tree_sha256(root: Path) -> str:
    root = Path(root)
    digest = hashlib.sha256()
    files = sorted(
        path for path in root.rglob("*")
        if path.is_file() and not path.is_symlink()
    )
    if not files:
        raise VendorRefreshError("vendored tree is empty: %s" % root)
    for path in files:
        relative = path.relative_to(root).as_posix().encode("utf-8")
        payload = path.read_bytes()
        digest.update(relative)
        digest.update(b"\0")
        digest.update(hashlib.sha256(payload).digest())
    return digest.hexdigest()


def _scan_private_imports(package_root: Path) -> None:
    violations = []
    for path in sorted(Path(package_root).rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (UnicodeDecodeError, SyntaxError) as exc:
            raise VendorRefreshError("cannot scan vendored Python file %s: %s" % (path, exc)) from exc
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".", 1)[0]
                    if root in FORBIDDEN_PUBLIC_IMPORT_ROOTS:
                        violations.append((path, node.lineno, alias.name))
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                module = node.module or ""
                root = module.split(".", 1)[0]
                if root in FORBIDDEN_PUBLIC_IMPORT_ROOTS:
                    violations.append((path, node.lineno, module))
    if violations:
        formatted = ", ".join(
            "%s:%s:%s" % (path, lineno, module)
            for path, lineno, module in violations[:20]
        )
        raise VendorRefreshError("vendored package imports public vendor namespace: %s" % formatted)


def _reject_symlinks(root: Path) -> None:
    links = [path for path in Path(root).rglob("*") if path.is_symlink()]
    if links:
        raise VendorRefreshError("vendored tree contains symlink: %s" % links[0])


def _write_file(root: Path, relative: PurePosixPath, payload: bytes) -> Path:
    target = root.joinpath(*relative.parts)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    return target


def _extract_lunar(sdist: Path, staging_vendor_root: Path, staging_license_root: Path) -> None:
    package_target = staging_vendor_root / "lunar_python"
    license_payload = None
    package_files = 0
    with tarfile.open(str(sdist), mode="r:gz") as archive:
        for member in archive.getmembers():
            path = _safe_archive_path(member.name)
            if member.issym() or member.islnk() or member.isdev():
                raise VendorRefreshError("lunar sdist contains forbidden member type: %s" % member.name)
            if member.isdir():
                continue
            if not member.isfile():
                raise VendorRefreshError("lunar sdist contains unsupported member type: %s" % member.name)
            handle = archive.extractfile(member)
            if handle is None:
                raise VendorRefreshError("cannot read lunar sdist member: %s" % member.name)
            payload = handle.read()
            parts = path.parts
            if len(parts) >= 3 and parts[1] == "lunar_python":
                relative = PurePosixPath(*parts[2:])
                if relative.parts:
                    _write_file(package_target, relative, payload)
                    package_files += 1
            elif len(parts) == 2 and parts[1].upper().startswith("LICENSE"):
                license_payload = payload
    if package_files == 0 or not (package_target / "__init__.py").is_file():
        raise VendorRefreshError("lunar sdist did not contain expected lunar_python package")
    if license_payload is None:
        raise VendorRefreshError("lunar sdist did not contain a root license file")
    (staging_license_root / "lunar-python-LICENSE.txt").write_bytes(license_payload)


def _zip_member_is_symlink(info: zipfile.ZipInfo) -> bool:
    mode = (info.external_attr >> 16) & 0xFFFF
    return stat.S_ISLNK(mode)


def _extract_tzdata(wheel: Path, staging_vendor_root: Path, staging_license_root: Path) -> None:
    package_target = staging_vendor_root / "tzdata"
    license_payload = None
    package_files = 0
    zoneinfo_files = 0
    with zipfile.ZipFile(str(wheel), mode="r") as archive:
        for info in archive.infolist():
            name = info.filename.rstrip("/") if info.filename.endswith("/") else info.filename
            path = _safe_archive_path(name)
            if _zip_member_is_symlink(info):
                raise VendorRefreshError("tzdata wheel contains symlink: %s" % info.filename)
            if info.is_dir():
                continue
            payload = archive.read(info)
            parts = path.parts
            if parts and parts[0] == "tzdata":
                if len(parts) == 2 and parts[1] == "__init__.py":
                    _write_file(package_target, PurePosixPath("__init__.py"), payload)
                    package_files += 1
                elif len(parts) >= 3 and parts[1] == "zoneinfo":
                    _write_file(package_target, PurePosixPath(*parts[1:]), payload)
                    package_files += 1
                    zoneinfo_files += 1
            elif "dist-info" in parts[0] and any(part.upper().startswith("LICENSE") for part in parts[1:]):
                if license_payload is None:
                    license_payload = payload
    if package_files == 0 or zoneinfo_files == 0 or not (package_target / "__init__.py").is_file():
        raise VendorRefreshError("tzdata wheel did not contain expected package and zoneinfo resources")
    if not (package_target / "zoneinfo" / "__init__.py").is_file():
        raise VendorRefreshError("tzdata wheel missing tzdata/zoneinfo/__init__.py")
    if license_payload is None:
        raise VendorRefreshError("tzdata wheel did not contain a license file")
    (staging_license_root / "tzdata-LICENSE.txt").write_bytes(license_payload)


def _tzdata_versions(init_path: Path) -> Tuple[Optional[str], Optional[str]]:
    tree = ast.parse(init_path.read_text(encoding="utf-8"), filename=str(init_path))
    values = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in ("__version__", "IANA_VERSION"):
                try:
                    values[name] = ast.literal_eval(node.value)
                except (ValueError, TypeError):
                    pass
    return values.get("__version__"), values.get("IANA_VERSION")


def _manifest(lunar_tree: str, tzdata_tree: str) -> Dict[str, object]:
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "packages": [
            {
                "package_name": "lunar-python",
                "import_namespace": "_metaphysics_lab_vendor.lunar_python",
                "version": LUNAR_VERSION,
                "source_repository": LUNAR_SOURCE_REPOSITORY,
                "source_revision": LUNAR_SOURCE_REVISION,
                "source_artifact": LUNAR_ARTIFACT,
                "artifact_sha256": LUNAR_SHA256,
                "vendored_tree_sha256": lunar_tree,
                "vendored_path": "_metaphysics_lab_vendor/lunar_python",
                "license_spdx": "MIT",
                "license_file": "vendor/licenses/lunar-python-LICENSE.txt",
                "bundled": True,
                "runtime_authority": "bundled",
            },
            {
                "package_name": "tzdata",
                "import_namespace": "_metaphysics_lab_vendor.tzdata",
                "version": TZDATA_VERSION,
                "source_repository": TZDATA_SOURCE_REPOSITORY,
                "source_revision": TZDATA_SOURCE_REVISION,
                "source_artifact": TZDATA_ARTIFACT,
                "artifact_sha256": TZDATA_SHA256,
                "vendored_tree_sha256": tzdata_tree,
                "vendored_path": "_metaphysics_lab_vendor/tzdata",
                "license_spdx": "Apache-2.0",
                "license_file": "vendor/licenses/tzdata-LICENSE.txt",
                "bundled": True,
                "runtime_authority": "bundled",
                "iana_version": TZDATA_IANA_VERSION,
            },
        ],
    }


def _notices() -> str:
    return """# Third-Party Notices

Metaphysics Lab bundles the following unmodified dependency package data under a private runtime namespace.

## lunar-python 1.4.8

- Upstream: https://github.com/6tail/lunar-python
- Source revision: 000c8a3d74eed098d6256a28fdd51b869324c559
- Source artifact: lunar_python-1.4.8.tar.gz
- Artifact SHA256: 3aa11cc73c25e70ddf0ba5bdac7398c03acc9491a3aa512a91c9642973b669d6
- License: MIT (see `lunar-python-LICENSE.txt`)

## tzdata 2026.3 / IANA 2026c

- Upstream: https://github.com/python/tzdata
- Source revision: a44279419071b7aa41ebe7eca301ebb2e759571a
- Source artifact: tzdata-2026.3-py2.py3-none-any.whl
- Artifact SHA256: dc096730c87af6cab1b171c9d532be840741ff5d459015e7f6947bd7d7e54931
- License: Apache-2.0 (see `tzdata-LICENSE.txt`)
"""


def _replace_tree(source: Path, target: Path) -> None:
    backup = target.with_name(target.name + ".vendor-refresh-backup")
    if backup.exists():
        shutil.rmtree(str(backup))
    if target.exists():
        os.replace(str(target), str(backup))
    try:
        os.replace(str(source), str(target))
    except Exception:
        if backup.exists() and not target.exists():
            os.replace(str(backup), str(target))
        raise
    if backup.exists():
        shutil.rmtree(str(backup))


def refresh_vendor(repo_root: Path, lunar_sdist: Path, tzdata_wheel: Path) -> dict:
    repo_root = Path(repo_root).resolve()
    lunar_sdist = _verified_artifact(Path(lunar_sdist), LUNAR_ARTIFACT, LUNAR_SHA256)
    tzdata_wheel = _verified_artifact(Path(tzdata_wheel), TZDATA_ARTIFACT, TZDATA_SHA256)

    with tempfile.TemporaryDirectory(prefix="metaphysics_vendor_refresh_") as temp_dir:
        staging = Path(temp_dir)
        private_root = staging / "_metaphysics_lab_vendor"
        licenses_root = staging / "vendor" / "licenses"
        private_root.mkdir(parents=True)
        licenses_root.mkdir(parents=True)
        (private_root / "__init__.py").write_text(
            '"""Project-private bundled third-party runtime dependencies."""\n',
            encoding="utf-8",
        )
        _extract_lunar(lunar_sdist, private_root, licenses_root)
        _extract_tzdata(tzdata_wheel, private_root, licenses_root)
        _reject_symlinks(private_root)
        _scan_private_imports(private_root)
        actual_tz_version, actual_iana = _tzdata_versions(private_root / "tzdata" / "__init__.py")
        if actual_tz_version != TZDATA_VERSION or actual_iana != TZDATA_IANA_VERSION:
            raise VendorRefreshError(
                "tzdata package metadata mismatch: expected %s/%s, got %r/%r"
                % (TZDATA_VERSION, TZDATA_IANA_VERSION, actual_tz_version, actual_iana)
            )
        lunar_tree = _tree_sha256(private_root / "lunar_python")
        tzdata_tree = _tree_sha256(private_root / "tzdata")
        manifest = _manifest(lunar_tree, tzdata_tree)
        manifest_dir = staging / "vendor"
        (manifest_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (licenses_root / "THIRD_PARTY_NOTICES.md").write_text(_notices(), encoding="utf-8")

        target_private = repo_root / "_metaphysics_lab_vendor"
        target_vendor = repo_root / "vendor"
        target_private.parent.mkdir(parents=True, exist_ok=True)
        target_vendor.parent.mkdir(parents=True, exist_ok=True)
        private_stage = staging / "private-final"
        vendor_stage = staging / "vendor-final"
        os.replace(str(private_root), str(private_stage))
        os.replace(str(manifest_dir), str(vendor_stage))
        _replace_tree(private_stage, target_private)
        _replace_tree(vendor_stage, target_vendor)
    return manifest


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Refresh pinned Metaphysics Lab private vendor dependencies")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--lunar-sdist", required=True)
    parser.add_argument("--tzdata-wheel", required=True)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        manifest = refresh_vendor(Path(args.repo_root), Path(args.lunar_sdist), Path(args.tzdata_wheel))
    except VendorRefreshError as exc:
        print("vendor refresh failed: %s" % exc)
        return 1
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
