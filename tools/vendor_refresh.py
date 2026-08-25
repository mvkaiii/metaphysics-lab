#!/usr/bin/env python3
"""Verify or materialize pinned private calendar dependency storage.

This is an explicit maintenance tool. Normal builds and runtime execution must
never download dependencies or invoke this module automatically. Upstream
artifact bytes must already exist in a local artifact directory.
"""
from __future__ import annotations

import argparse
import ast
import base64
import hashlib
import json
import lzma
import os
import shutil
import stat
import sys
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
LUNAR_SHARD_CHARACTERS = 9600

TZDATA_ARTIFACT = "tzdata-2026.3-py2.py3-none-any.whl"
TZDATA_SHA256 = "dc096730c87af6cab1b171c9d532be840741ff5d459015e7f6947bd7d7e54931"
TZDATA_VERSION = "2026.3"
TZDATA_IANA_VERSION = "2026c"
TZDATA_SOURCE_REPOSITORY = "https://github.com/python/tzdata"
TZDATA_SOURCE_REVISION = "a44279419071b7aa41ebe7eca301ebb2e759571a"
TZDATA_SHARD_CHARACTERS = 4800

FORBIDDEN_PUBLIC_IMPORT_ROOTS = frozenset(("lunar_python", "tzdata"))
MANIFEST_SCHEMA_VERSION = "1.0"
STORAGE_PROFILE = "artifact-shards-base64-xz-private-tree-v1"
ARTIFACT_STORAGE_ENCODING = "base64"
ARTIFACT_COMPRESSION = "xz"
ARTIFACT_XZ_PRESET = 9


class VendorRefreshError(RuntimeError):
    pass


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


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


def _verified_artifacts(artifact_dir: Path) -> Tuple[Path, Path]:
    artifact_dir = Path(artifact_dir)
    if not artifact_dir.is_dir():
        raise VendorRefreshError("artifact directory not found: %s" % artifact_dir)
    lunar = _verified_artifact(artifact_dir / LUNAR_ARTIFACT, LUNAR_ARTIFACT, LUNAR_SHA256)
    tzdata = _verified_artifact(artifact_dir / TZDATA_ARTIFACT, TZDATA_ARTIFACT, TZDATA_SHA256)
    return lunar, tzdata


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
    files = sorted(path for path in root.rglob("*") if path.is_file() and not path.is_symlink())
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
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                names = [node.module or ""]
            else:
                continue
            for name in names:
                if name.split(".", 1)[0] in FORBIDDEN_PUBLIC_IMPORT_ROOTS:
                    violations.append((path, getattr(node, "lineno", 0), name))
    if violations:
        formatted = ", ".join("%s:%s:%s" % item for item in violations[:20])
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


def _extract_lunar(sdist: Path, private_root: Path, license_root: Path) -> None:
    package_target = private_root / "lunar_python"
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
    (license_root / "lunar-python-LICENSE.txt").write_bytes(license_payload)


def _zip_member_is_symlink(info: zipfile.ZipInfo) -> bool:
    mode = (info.external_attr >> 16) & 0xFFFF
    return stat.S_ISLNK(mode)


def _extract_tzdata(wheel: Path, private_root: Path, license_root: Path) -> None:
    package_target = private_root / "tzdata"
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
            elif parts and "dist-info" in parts[0] and any(
                part.upper().startswith("LICENSE") for part in parts[1:]
            ):
                if license_payload is None:
                    license_payload = payload
    if package_files == 0 or zoneinfo_files == 0 or not (package_target / "__init__.py").is_file():
        raise VendorRefreshError("tzdata wheel did not contain expected package and zoneinfo resources")
    if not (package_target / "zoneinfo" / "__init__.py").is_file():
        raise VendorRefreshError("tzdata wheel missing tzdata/zoneinfo/__init__.py")
    if license_payload is None:
        raise VendorRefreshError("tzdata wheel did not contain a license file")
    (license_root / "tzdata-LICENSE.txt").write_bytes(license_payload)


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


def _store_artifact(
    artifact: Path, artifact_root: Path, shard_characters: int
) -> Tuple[Sequence[str], Dict[str, str], str, Sequence[Dict[str, object]]]:
    if shard_characters <= 0 or shard_characters % 4:
        raise VendorRefreshError("artifact shard size must be a positive multiple of 4")
    raw = Path(artifact).read_bytes()
    compressed = lzma.compress(raw, format=lzma.FORMAT_XZ, preset=ARTIFACT_XZ_PRESET)
    encoded = base64.b64encode(compressed).decode("ascii")
    artifact_root.mkdir(parents=True, exist_ok=True)
    paths = []
    hashes: Dict[str, str] = {}
    parts = []
    prefix = artifact.name + ".xz.b64part"
    for index, offset in enumerate(range(0, len(encoded), shard_characters), start=1):
        name = "%s%02d" % (prefix, index)
        relative = "vendor/artifacts/" + name
        payload = encoded[offset : offset + shard_characters].encode("ascii")
        (artifact_root / name).write_bytes(payload)
        sha256 = _sha256_bytes(payload)
        paths.append(relative)
        hashes[relative] = sha256
        parts.append({"path": relative, "char_count": len(payload), "sha256": sha256})
    return paths, hashes, _sha256_bytes(compressed), parts


def _manifest_row(
    *,
    package_name: str,
    import_namespace: str,
    version: str,
    source_repository: str,
    source_revision: str,
    source_artifact: str,
    artifact_sha256: str,
    vendored_tree_sha256: str,
    vendored_path: str,
    license_spdx: str,
    license_file: str,
    artifact_storage: Tuple[Sequence[str], Dict[str, str], str, Sequence[Dict[str, object]]],
    iana_version: Optional[str] = None,
) -> Dict[str, object]:
    paths, hashes, storage_sha, parts = artifact_storage
    row: Dict[str, object] = {
        "package_name": package_name,
        "import_namespace": import_namespace,
        "version": version,
        "source_repository": source_repository,
        "source_revision": source_revision,
        "source_artifact": source_artifact,
        "artifact_sha256": artifact_sha256,
        "artifact_storage_encoding": ARTIFACT_STORAGE_ENCODING,
        "artifact_compression": ARTIFACT_COMPRESSION,
        "artifact_storage_sha256": storage_sha,
        "artifact_parts": list(parts),
        "artifact_shards": list(paths),
        "artifact_shard_sha256": dict(hashes),
        "vendored_tree_sha256": vendored_tree_sha256,
        "vendored_path": vendored_path,
        "license_spdx": license_spdx,
        "license_file": license_file,
        "bundled": True,
        "runtime_authority": "bundled",
        "storage_mode": "artifact_shards_materialized",
    }
    if iana_version is not None:
        row["iana_version"] = iana_version
    return row


def _manifest(
    lunar_tree: str,
    tzdata_tree: str,
    lunar_storage: Tuple[Sequence[str], Dict[str, str], str, Sequence[Dict[str, object]]],
    tzdata_storage: Tuple[Sequence[str], Dict[str, str], str, Sequence[Dict[str, object]]],
) -> Dict[str, object]:
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "storage_profile": STORAGE_PROFILE,
        "packages": [
            _manifest_row(
                package_name="lunar-python",
                import_namespace="_metaphysics_lab_vendor.lunar_python",
                version=LUNAR_VERSION,
                source_repository=LUNAR_SOURCE_REPOSITORY,
                source_revision=LUNAR_SOURCE_REVISION,
                source_artifact=LUNAR_ARTIFACT,
                artifact_sha256=LUNAR_SHA256,
                vendored_tree_sha256=lunar_tree,
                vendored_path="_metaphysics_lab_vendor/lunar_python",
                license_spdx="MIT",
                license_file="vendor/licenses/lunar-python-LICENSE.txt",
                artifact_storage=lunar_storage,
            ),
            _manifest_row(
                package_name="tzdata",
                import_namespace="_metaphysics_lab_vendor.tzdata",
                version=TZDATA_VERSION,
                source_repository=TZDATA_SOURCE_REPOSITORY,
                source_revision=TZDATA_SOURCE_REVISION,
                source_artifact=TZDATA_ARTIFACT,
                artifact_sha256=TZDATA_SHA256,
                vendored_tree_sha256=tzdata_tree,
                vendored_path="_metaphysics_lab_vendor/tzdata",
                license_spdx="Apache-2.0",
                license_file="vendor/licenses/tzdata-LICENSE.txt",
                artifact_storage=tzdata_storage,
                iana_version=TZDATA_IANA_VERSION,
            ),
        ],
    }


def _notices() -> str:
    return """# Third-Party Notices

Metaphysics Lab bundles the following dependency package data under a private runtime namespace.

## lunar-python 1.4.8

- Upstream: https://github.com/6tail/lunar-python
- Source revision: 000c8a3d74eed098d6256a28fdd51b869324c559
- Source artifact: lunar_python-1.4.8.tar.gz
- Artifact SHA256: 3aa11cc73c25e70ddf0ba5bdac7398c03acc9491a3aa512a91c9642973b669d6
- Repository storage: deterministic XZ, base64 shards
- License: MIT (see `lunar-python-LICENSE.txt`)

## tzdata 2026.3 / IANA 2026c

- Upstream: https://github.com/python/tzdata
- Source revision: a44279419071b7aa41ebe7eca301ebb2e759571a
- Source artifact: tzdata-2026.3-py2.py3-none-any.whl
- Artifact SHA256: dc096730c87af6cab1b171c9d532be840741ff5d459015e7f6947bd7d7e54931
- Repository storage: deterministic XZ, base64 shards
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


def _write_manifest(vendor_root: Path, manifest: Dict[str, object]) -> None:
    payload = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    (vendor_root / "manifest.json").write_text(payload, encoding="utf-8")


def _build_candidate(staging: Path, lunar_sdist: Path, tzdata_wheel: Path) -> Tuple[Path, Dict[str, object]]:
    private_root = staging / "_metaphysics_lab_vendor"
    vendor_root = staging / "vendor"
    licenses_root = vendor_root / "licenses"
    artifacts_root = vendor_root / "artifacts"
    private_root.mkdir(parents=True)
    licenses_root.mkdir(parents=True)
    artifacts_root.mkdir(parents=True)
    (private_root / "__init__.py").write_text(
        '"""Project-private bundled third-party runtime dependencies."""\n', encoding="utf-8"
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
    lunar_storage = _store_artifact(lunar_sdist, artifacts_root, LUNAR_SHARD_CHARACTERS)
    tzdata_storage = _store_artifact(tzdata_wheel, artifacts_root, TZDATA_SHARD_CHARACTERS)
    manifest = _manifest(lunar_tree, tzdata_tree, lunar_storage, tzdata_storage)
    _write_manifest(vendor_root, manifest)
    (licenses_root / "THIRD_PARTY_NOTICES.md").write_text(_notices(), encoding="utf-8")
    return vendor_root, manifest


def _file_map(root: Path) -> Dict[str, bytes]:
    root = Path(root)
    if not root.is_dir():
        return {}
    _reject_symlinks(root)
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _candidate_from_files(lunar_sdist: Path, tzdata_wheel: Path, staging: Path) -> Tuple[Path, Dict[str, object]]:
    lunar_sdist = _verified_artifact(Path(lunar_sdist), LUNAR_ARTIFACT, LUNAR_SHA256)
    tzdata_wheel = _verified_artifact(Path(tzdata_wheel), TZDATA_ARTIFACT, TZDATA_SHA256)
    return _build_candidate(staging, lunar_sdist, tzdata_wheel)


def materialize_vendor(repo_root: Path, artifact_dir: Path) -> Dict[str, object]:
    repo_root = Path(repo_root).resolve()
    lunar_sdist, tzdata_wheel = _verified_artifacts(artifact_dir)
    with tempfile.TemporaryDirectory(prefix="metaphysics_vendor_refresh_") as temp_dir:
        staging = Path(temp_dir)
        vendor_root, manifest = _build_candidate(staging, lunar_sdist, tzdata_wheel)
        target = repo_root / "vendor"
        target.parent.mkdir(parents=True, exist_ok=True)
        vendor_stage = staging / "vendor-final"
        os.replace(str(vendor_root), str(vendor_stage))
        _replace_tree(vendor_stage, target)
    return manifest


def check_vendor(repo_root: Path, artifact_dir: Path) -> Dict[str, object]:
    repo_root = Path(repo_root).resolve()
    lunar_sdist, tzdata_wheel = _verified_artifacts(artifact_dir)
    with tempfile.TemporaryDirectory(prefix="metaphysics_vendor_check_") as temp_dir:
        staging = Path(temp_dir)
        vendor_root, manifest = _build_candidate(staging, lunar_sdist, tzdata_wheel)
        expected = _file_map(vendor_root)
        actual = _file_map(repo_root / "vendor")
        if actual != expected:
            missing = sorted(set(expected) - set(actual))
            extra = sorted(set(actual) - set(expected))
            changed = sorted(path for path in set(actual) & set(expected) if actual[path] != expected[path])
            details = []
            if missing:
                details.append("missing=%s" % ",".join(missing[:10]))
            if extra:
                details.append("extra=%s" % ",".join(extra[:10]))
            if changed:
                details.append("changed=%s" % ",".join(changed[:10]))
            raise VendorRefreshError("committed vendor storage differs from verified candidate: %s" % "; ".join(details))
    return manifest


def refresh_vendor(repo_root: Path, lunar_sdist: Path, tzdata_wheel: Path) -> Dict[str, object]:
    """Backward-compatible explicit-file materialization helper.

    Unlike the historical implementation, this writes only repository vendor
    storage. The private import tree is staging-only and is materialized at
    runtime from committed shards.
    """
    repo_root = Path(repo_root).resolve()
    with tempfile.TemporaryDirectory(prefix="metaphysics_vendor_refresh_") as temp_dir:
        staging = Path(temp_dir)
        vendor_root, manifest = _candidate_from_files(lunar_sdist, tzdata_wheel, staging)
        target = repo_root / "vendor"
        target.parent.mkdir(parents=True, exist_ok=True)
        vendor_stage = staging / "vendor-final"
        os.replace(str(vendor_root), str(vendor_stage))
        _replace_tree(vendor_stage, target)
    return manifest


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--artifact-dir", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--materialize", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.check:
            manifest = check_vendor(args.repo_root, args.artifact_dir)
        else:
            manifest = materialize_vendor(args.repo_root, args.artifact_dir)
    except VendorRefreshError as exc:
        print("vendor refresh failed: %s" % exc, file=sys.stderr)
        return 1
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
