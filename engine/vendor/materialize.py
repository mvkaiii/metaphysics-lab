"""Materialize pinned private runtime dependencies from committed artifact shards.

Repository storage keeps checksum-protected base64 shards of deterministic XZ
streams. Materialization validates each storage layer before extracting the
approved private package tree.
"""

from __future__ import annotations

import atexit
import ast
import base64
import hashlib
import io
import lzma
import shutil
import stat
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Mapping, Optional

from .manifest import bundled_dependency


_RUNTIME_ROOT: Optional[Path] = None


class VendorMaterializationError(RuntimeError):
    pass


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _safe_archive_path(name: str) -> bool:
    if not isinstance(name, str) or not name or "\\" in name:
        return False
    path = PurePosixPath(name)
    return not path.is_absolute() and all(part not in ("", ".", "..") for part in path.parts)


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


def _artifact_bytes(repo_root: Path, row: Mapping[str, object]) -> bytes:
    shards = row.get("artifact_shards")
    shard_hashes = row.get("artifact_shard_sha256")
    if not isinstance(shards, (list, tuple)) or not shards:
        raise VendorMaterializationError("vendor artifact shards are missing")
    if not isinstance(shard_hashes, Mapping):
        raise VendorMaterializationError("vendor artifact shard hashes are missing")

    encoded_parts = []
    for relative in shards:
        if not isinstance(relative, str) or not _safe_archive_path(relative):
            raise VendorMaterializationError("invalid vendor artifact shard path")
        path = repo_root / relative
        try:
            payload = path.read_bytes()
        except OSError as exc:
            raise VendorMaterializationError(
                "vendor artifact shard is unavailable: %s" % relative
            ) from exc
        expected_shard = shard_hashes.get(relative)
        actual_shard = hashlib.sha256(payload).hexdigest()
        if not isinstance(expected_shard, str) or actual_shard != expected_shard:
            raise VendorMaterializationError(
                "vendor artifact shard digest mismatch: %s" % relative
            )
        try:
            encoded_parts.append(payload.decode("ascii").strip())
        except UnicodeDecodeError as exc:
            raise VendorMaterializationError(
                "vendor artifact shard is not ASCII: %s" % relative
            ) from exc

    encoding = row.get("artifact_storage_encoding", "base64")
    if encoding != "base64":
        raise VendorMaterializationError(
            "unsupported vendor artifact storage encoding: %r" % (encoding,)
        )
    try:
        stored = base64.b64decode(
            "".join(encoded_parts).encode("ascii"), validate=True
        )
    except Exception as exc:
        raise VendorMaterializationError("vendor artifact base64 is invalid") from exc

    expected_storage = row.get("artifact_storage_sha256")
    if expected_storage is not None:
        actual_storage = hashlib.sha256(stored).hexdigest()
        if not isinstance(expected_storage, str) or actual_storage != expected_storage:
            raise VendorMaterializationError("vendor artifact storage digest mismatch")

    compression = row.get("artifact_compression", "none")
    if compression in (None, "none"):
        artifact = stored
    elif compression == "xz":
        try:
            artifact = lzma.decompress(stored, format=lzma.FORMAT_XZ)
        except lzma.LZMAError as exc:
            raise VendorMaterializationError(
                "vendor artifact XZ stream is invalid"
            ) from exc
    else:
        raise VendorMaterializationError(
            "unsupported vendor artifact compression: %r" % (compression,)
        )

    expected_artifact = row.get("artifact_sha256")
    actual_artifact = hashlib.sha256(artifact).hexdigest()
    if not isinstance(expected_artifact, str) or actual_artifact != expected_artifact:
        raise VendorMaterializationError("vendor artifact digest mismatch")
    return artifact


def _extract_lunar(artifact: bytes, private_root: Path) -> None:
    target_root = private_root / "lunar_python"
    with tarfile.open(fileobj=io.BytesIO(artifact), mode="r:gz") as archive:
        members = archive.getmembers()
        for member in members:
            if not _safe_archive_path(member.name):
                raise VendorMaterializationError(
                    "unsafe lunar archive member: %s" % member.name
                )
            if member.issym() or member.islnk() or member.isdev():
                raise VendorMaterializationError(
                    "lunar archive links/devices are not allowed: %s" % member.name
                )
        copied = 0
        for member in members:
            if not member.isfile():
                continue
            parts = PurePosixPath(member.name).parts
            try:
                index = parts.index("lunar_python")
            except ValueError:
                continue
            relative_parts = parts[index + 1 :]
            if not relative_parts:
                continue
            source = archive.extractfile(member)
            if source is None:
                raise VendorMaterializationError(
                    "unable to read lunar archive member"
                )
            target = target_root.joinpath(*relative_parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read())
            copied += 1
        if copied == 0 or not (target_root / "__init__.py").is_file():
            raise VendorMaterializationError("lunar package subtree is missing")


def _extract_tzdata(artifact: bytes, private_root: Path) -> None:
    target_root = private_root / "tzdata"
    with zipfile.ZipFile(io.BytesIO(artifact), mode="r") as archive:
        copied_init = False
        copied_zoneinfo = 0
        for info in archive.infolist():
            if not _safe_archive_path(info.filename):
                raise VendorMaterializationError(
                    "unsafe tzdata wheel member: %s" % info.filename
                )
            mode = (info.external_attr >> 16) & 0o170000
            if mode == stat.S_IFLNK:
                raise VendorMaterializationError(
                    "tzdata wheel links are not allowed: %s" % info.filename
                )
            if info.is_dir():
                continue
            if info.filename == "tzdata/__init__.py":
                relative = "__init__.py"
                copied_init = True
            elif info.filename.startswith("tzdata/zoneinfo/"):
                relative = info.filename[len("tzdata/") :]
                copied_zoneinfo += 1
            else:
                continue
            target = target_root.joinpath(*PurePosixPath(relative).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(info))
        if not copied_init or copied_zoneinfo == 0:
            raise VendorMaterializationError(
                "tzdata wheel package resources are missing"
            )


def _validate_python_imports(private_root: Path) -> None:
    forbidden = {"lunar_python", "tzdata"}
    for path in private_root.rglob("*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, UnicodeDecodeError, SyntaxError) as exc:
            raise VendorMaterializationError(
                "invalid vendored Python source: %s" % path
            ) from exc
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module]
            else:
                continue
            if any(name.split(".", 1)[0] in forbidden for name in names):
                raise VendorMaterializationError(
                    "vendored source imports a public dependency name: %s" % path
                )


def materialize_private_vendor(repo_root: Path, target_root: Path) -> Path:
    repo_root = Path(repo_root).resolve()
    target_root = Path(target_root).resolve()
    private_root = target_root / "_metaphysics_lab_vendor"
    if private_root.exists():
        raise VendorMaterializationError("private vendor target already exists")
    private_root.mkdir(parents=True)
    (private_root / "__init__.py").write_text(
        '"""Project-private bundled third-party runtime dependencies."""\n',
        encoding="utf-8",
    )

    try:
        manifest_path = repo_root / "vendor" / "manifest.json"
        lunar = bundled_dependency("lunar-python", manifest_path)
        tzdata = bundled_dependency("tzdata", manifest_path)
        _extract_lunar(_artifact_bytes(repo_root, lunar), private_root)
        _extract_tzdata(_artifact_bytes(repo_root, tzdata), private_root)
        _validate_python_imports(private_root)
        for row, package_dir in ((lunar, "lunar_python"), (tzdata, "tzdata")):
            expected = row.get("vendored_tree_sha256")
            actual = _tree_sha256(private_root / package_dir)
            if not isinstance(expected, str) or actual != expected:
                raise VendorMaterializationError(
                    "vendored package tree digest mismatch: %s"
                    % row.get("package_name")
                )
    except Exception:
        shutil.rmtree(str(private_root), ignore_errors=True)
        raise
    return private_root


def _cleanup_runtime_root() -> None:
    global _RUNTIME_ROOT
    if _RUNTIME_ROOT is not None:
        shutil.rmtree(str(_RUNTIME_ROOT), ignore_errors=True)
        _RUNTIME_ROOT = None


def ensure_private_vendor_root() -> Path:
    global _RUNTIME_ROOT
    if _RUNTIME_ROOT is not None:
        return _RUNTIME_ROOT / "_metaphysics_lab_vendor"
    root = Path(tempfile.mkdtemp(prefix="metaphysics_lab_vendor_"))
    try:
        private_root = materialize_private_vendor(_repo_root(), root)
    except Exception:
        shutil.rmtree(str(root), ignore_errors=True)
        raise
    _RUNTIME_ROOT = root
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    atexit.register(_cleanup_runtime_root)
    return private_root
