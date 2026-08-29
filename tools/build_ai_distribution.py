#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the portable AI-first Metaphysics Lab distribution assets.

The source tree stays modular. This builder creates exactly three deterministic
artifacts for end users:

- metaphysics_lab.py
- metaphysics_core.md
- project_instructions.txt
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sys
import tempfile
import zlib
from pathlib import Path, PurePosixPath
from typing import Dict, Iterable, List, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from engine.birth.errors import BirthFoundationError
from engine.birth.offline_registry import load_offline_birth_place_registry
from engine.distribution.constants import (
    CASE_SCHEMA_VERSION,
    DISTRIBUTION_RUNTIME_VERSION,
    PROJECT_CONTRACT_VERSION,
    RUNTIME_SCHEMA_VERSION,
)
from engine.vendor.manifest import bundled_vendor_manifest
from engine.vendor.materialize import materialize_private_vendor


BUILD_FORMAT_VERSION = "1.1"
MAX_BUNDLE_BYTES = 5 * 1024 * 1024
ARTIFACT_NAMES = (
    "metaphysics_core.md",
    "metaphysics_lab.py",
    "project_instructions.txt",
)
_FIRST_PARTY_TEXT_PREFIXES = ("engine/", "templates/")
_SINGLE_BUNDLE_INPUTS = (
    "vendor/manifest.json",
    "data/birth_places/registry.v1.json",
    "data/birth_places/schema.v1.json",
    "data/birth_places/SOURCES.md",
)
_DIRECTORY_BUNDLE_INPUTS = (
    "_metaphysics_lab_vendor",
    "vendor/artifacts",
    "vendor/licenses",
)
_REQUIRED_REGISTRY_SUPPORT = (
    "data/birth_places/registry.v1.json",
    "data/birth_places/schema.v1.json",
    "data/birth_places/SOURCES.md",
)
_REQUIRED_VENDOR_NOTICE = "vendor/licenses/THIRD_PARTY_NOTICES.md"

_BOOTSTRAP = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# GENERATED FILE - DO NOT EDIT
"""Portable Metaphysics Lab runtime bundle.

Generated from the modular repository source. Core portable dependencies and
runtime data, when present in the approved bundle input set, are embedded as
checksum-protected bytes and loaded from a private temporary runtime root.
"""

from __future__ import annotations

import argparse
import atexit
import base64
import hashlib
import importlib
import json
import shutil
import sys
import tempfile
import zlib
from pathlib import Path, PurePosixPath

BUILD_FORMAT_VERSION = @@BUILD_FORMAT_VERSION@@
SOURCE_DIGEST = @@SOURCE_DIGEST@@
PROJECT_CONTRACT_VERSION = @@PROJECT_CONTRACT_VERSION@@
RUNTIME_SCHEMA_VERSION = @@RUNTIME_SCHEMA_VERSION@@
CASE_SCHEMA_VERSION = @@CASE_SCHEMA_VERSION@@
DISTRIBUTION_RUNTIME_VERSION = @@DISTRIBUTION_RUNTIME_VERSION@@
_SOURCE_FILES = json.loads(@@SOURCE_FILES_JSON@@)
_PAYLOAD_B64 = @@PAYLOAD_B64@@
_RUNTIME_ROOT = None


def _ok(action, data):
    return {
        "ok": True,
        "action": action,
        "runtime_version": DISTRIBUTION_RUNTIME_VERSION,
        "data": dict(data),
    }


def _error(action, code, message, details=None):
    return {
        "ok": False,
        "action": action,
        "runtime_version": DISTRIBUTION_RUNTIME_VERSION,
        "error": {
            "code": code,
            "message": message,
            "details": dict(details or {}),
        },
    }


def _validated_record(record, seen):
    if not isinstance(record, dict):
        raise RuntimeError("embedded file record must be an object")
    relative = record.get("path")
    if not isinstance(relative, str) or not relative:
        raise RuntimeError("embedded file path must be non-empty text")
    if "\\" in relative:
        raise RuntimeError("embedded file path must use POSIX separators: %s" % relative)
    pure = PurePosixPath(relative)
    if pure.is_absolute() or any(part in ("", ".", "..") for part in pure.parts):
        raise RuntimeError("unsafe embedded file path: %s" % relative)
    canonical = pure.as_posix()
    if canonical != relative:
        raise RuntimeError("non-canonical embedded file path: %s" % relative)
    if canonical in seen:
        raise RuntimeError("duplicate embedded file path: %s" % canonical)
    seen.add(canonical)

    if record.get("encoding") != "base64":
        raise RuntimeError("unsupported embedded file encoding: %s" % canonical)
    content = record.get("content")
    expected = record.get("sha256")
    if not isinstance(content, str) or not isinstance(expected, str):
        raise RuntimeError("embedded file record is incomplete: %s" % canonical)
    try:
        decoded = base64.b64decode(content.encode("ascii"), validate=True)
    except Exception as exc:
        raise RuntimeError("invalid embedded base64 content: %s" % canonical) from exc
    actual = hashlib.sha256(decoded).hexdigest()
    if actual != expected:
        raise RuntimeError("embedded file digest mismatch: %s" % canonical)
    manifest_digest = _SOURCE_FILES.get(canonical)
    if manifest_digest != expected:
        raise RuntimeError("embedded source manifest mismatch: %s" % canonical)
    return canonical, decoded


def _cleanup_runtime_root():
    global _RUNTIME_ROOT
    if _RUNTIME_ROOT is not None:
        shutil.rmtree(str(_RUNTIME_ROOT), ignore_errors=True)
        _RUNTIME_ROOT = None


def _ensure_runtime_root():
    global _RUNTIME_ROOT
    if _RUNTIME_ROOT is not None:
        return _RUNTIME_ROOT

    raw = zlib.decompress(base64.b64decode(_PAYLOAD_B64.encode("ascii")))
    if hashlib.sha256(raw).hexdigest() != SOURCE_DIGEST:
        raise RuntimeError("embedded source digest mismatch")
    payload = json.loads(raw.decode("utf-8"))
    if payload.get("build_format_version") != BUILD_FORMAT_VERSION:
        raise RuntimeError("embedded build format mismatch")
    records = payload.get("files")
    if not isinstance(records, list):
        raise RuntimeError("embedded source payload is invalid")

    seen = set()
    decoded_records = [_validated_record(record, seen) for record in records]
    if set(seen) != set(_SOURCE_FILES):
        raise RuntimeError("embedded source manifest file set mismatch")

    root = Path(tempfile.mkdtemp(prefix="metaphysics_lab_runtime_"))
    resolved_root = root.resolve()
    try:
        for relative, decoded in decoded_records:
            target = root.joinpath(*PurePosixPath(relative).parts)
            resolved_target = target.resolve()
            try:
                resolved_target.relative_to(resolved_root)
            except ValueError as exc:
                raise RuntimeError("embedded file escaped runtime root: %s" % relative) from exc
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(decoded)
    except Exception:
        shutil.rmtree(str(root), ignore_errors=True)
        raise

    _RUNTIME_ROOT = root
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    atexit.register(_cleanup_runtime_root)
    return root


def dispatch(action, payload=None):
    if not isinstance(action, str) or not action.strip():
        return _error(str(action), "invalid_action", "action must be a non-empty string")
    try:
        _ensure_runtime_root()
        runtime = importlib.import_module("engine.distribution.runtime")
        return runtime.dispatch(action, {} if payload is None else payload)
    except ModuleNotFoundError as exc:
        return _error(
            action,
            "dependency_unavailable",
            "required runtime dependency is unavailable",
            {"missing_module": exc.name},
        )
    except RuntimeError as exc:
        return _error(action, "bundle_runtime_error", str(exc))


def _read_request(path):
    if path == "-":
        text = sys.stdin.read()
    else:
        text = Path(path).read_text(encoding="utf-8")
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("request JSON must be an object")
    action = value.get("action")
    payload = value.get("payload")
    return action, payload


def _print_json(value, pretty):
    print(json.dumps(value, ensure_ascii=False, indent=2 if pretty else None, sort_keys=bool(pretty)))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Metaphysics Lab portable runtime")
    sub = parser.add_subparsers(dest="command", required=True)

    info = sub.add_parser("runtime-info", help="show runtime manifest and dependency status")
    info.add_argument("--pretty", action="store_true")

    request = sub.add_parser("request", help="execute one JSON request")
    request.add_argument("--input", required=True, help="JSON request file or - for stdin")
    request.add_argument("--pretty", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "runtime-info":
        _print_json(dispatch("runtime_info", {}), args.pretty)
        return 0

    try:
        action, payload = _read_request(args.input)
        result = dispatch(action, payload)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = _error("request", "invalid_request", str(exc))
    _print_json(result, args.pretty)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def _normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").rstrip() + "\n"


def _regular_files_under(root: Path, relative_dir: str) -> Iterable[str]:
    base = root / relative_dir
    if not base.exists():
        return ()
    if base.is_symlink():
        raise ValueError("bundle input directory must not be a symlink: %s" % relative_dir)
    result = []
    for path in base.rglob("*"):
        if path.is_symlink():
            raise ValueError("bundle input must not be a symlink: %s" % path.relative_to(root).as_posix())
        if path.is_file():
            result.append(path.relative_to(root).as_posix())
    return result


def discover_bundle_inputs(repo_root: Path) -> List[str]:
    root = Path(repo_root)
    paths = []
    for path in (root / "engine").rglob("*.py"):
        if path.is_symlink():
            raise ValueError("bundle input must not be a symlink: %s" % path.relative_to(root).as_posix())
        if path.is_file():
            paths.append(path.relative_to(root).as_posix())
    for path in (root / "templates").rglob("*.tmpl"):
        if path.is_symlink():
            raise ValueError("bundle input must not be a symlink: %s" % path.relative_to(root).as_posix())
        if path.is_file():
            paths.append(path.relative_to(root).as_posix())
    for relative_dir in _DIRECTORY_BUNDLE_INPUTS:
        paths.extend(_regular_files_under(root, relative_dir))
    for relative in _SINGLE_BUNDLE_INPUTS:
        path = root / relative
        if path.exists():
            if path.is_symlink() or not path.is_file():
                raise ValueError("bundle input must be a regular file: %s" % relative)
            paths.append(relative)
    return sorted(set(paths))


def discover_owned_sources(repo_root: Path) -> List[str]:
    """Backward-compatible alias for callers predating build format 1.1."""
    return discover_bundle_inputs(repo_root)


def build_file_record(repo_root: Path, relative_path: str) -> Dict[str, str]:
    root = Path(repo_root)
    path = root / relative_path
    if path.is_symlink() or not path.is_file():
        raise ValueError("bundle input must be a regular file: %s" % relative_path)
    raw = path.read_bytes()
    if relative_path.startswith(_FIRST_PARTY_TEXT_PREFIXES):
        try:
            raw = _normalize_text(raw.decode("utf-8")).encode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("first-party runtime source is not UTF-8: %s" % relative_path) from exc
    return {
        "path": relative_path,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "encoding": "base64",
        "content": base64.b64encode(raw).decode("ascii"),
    }


def _source_records(repo_root: Path, paths: Sequence[str]) -> List[Dict[str, str]]:
    return [build_file_record(repo_root, relative) for relative in paths]


def _payload(repo_root: Path):
    paths = discover_bundle_inputs(repo_root)
    records = _source_records(repo_root, paths)
    data = {"build_format_version": BUILD_FORMAT_VERSION, "files": records}
    raw = json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    encoded = base64.b64encode(zlib.compress(raw, level=9)).decode("ascii")
    source_files = {record["path"]: record["sha256"] for record in records}
    return encoded, digest, source_files


def _render_project_instructions(repo_root: Path) -> str:
    return _normalize_text((Path(repo_root) / "core" / "核心提示詞.md").read_text(encoding="utf-8"))


def _render_metaphysics_core(repo_root: Path) -> str:
    root = Path(repo_root)
    sections = []
    for relative in ("core/AI工作流程.md", "core/命理分析作業規範.md", "core/林氏天機預測驗證契約.md"):
        text = _normalize_text((root / relative).read_text(encoding="utf-8")).rstrip()
        sections.append("<!-- Source: %s -->\n%s" % (relative, text))
    return "\n\n---\n\n".join(sections).rstrip() + "\n"


def _compact_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _render_bundle(repo_root: Path) -> str:
    root = Path(repo_root)
    payload_b64, source_digest, source_files = _payload(root)
    replacements = {
        "@@BUILD_FORMAT_VERSION@@": repr(BUILD_FORMAT_VERSION),
        "@@SOURCE_DIGEST@@": repr(source_digest),
        "@@PROJECT_CONTRACT_VERSION@@": repr(PROJECT_CONTRACT_VERSION),
        "@@RUNTIME_SCHEMA_VERSION@@": repr(RUNTIME_SCHEMA_VERSION),
        "@@CASE_SCHEMA_VERSION@@": repr(CASE_SCHEMA_VERSION),
        "@@DISTRIBUTION_RUNTIME_VERSION@@": repr(DISTRIBUTION_RUNTIME_VERSION),
        "@@SOURCE_FILES_JSON@@": repr(_compact_json(source_files)),
        "@@PAYLOAD_B64@@": repr(payload_b64),
    }
    rendered = _BOOTSTRAP
    for token, value in replacements.items():
        rendered = rendered.replace(token, value)
    unresolved = [token for token in replacements if token in rendered]
    if unresolved:
        raise RuntimeError("unresolved bundle placeholders: %s" % unresolved)
    return _normalize_text(rendered)


def _required_regular_nonempty_file(root: Path, relative: str, *, missing_code: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise RuntimeError(missing_code)
    pure = PurePosixPath(relative)
    if pure.is_absolute() or pure.as_posix() != relative or any(part in ("", ".", "..") for part in pure.parts):
        raise RuntimeError(missing_code)
    target = root.joinpath(*pure.parts)
    if target.is_symlink() or not target.is_file():
        raise RuntimeError(missing_code)
    if not target.read_bytes():
        raise RuntimeError(missing_code)
    return target


def verify_vendor_inputs(repo_root: Path) -> None:
    """Fail closed before distribution emission if bundled authorities are invalid."""
    root = Path(repo_root)
    manifest_path = root / "vendor" / "manifest.json"
    try:
        manifest = bundled_vendor_manifest(path=manifest_path)
    except (OSError, ValueError, RuntimeError) as exc:
        raise RuntimeError("vendor_manifest_invalid") from exc

    packages = manifest.get("packages")
    if not isinstance(packages, tuple) or not packages:
        raise RuntimeError("vendor_manifest_invalid")
    for package in packages:
        license_file = package.get("license_file")
        if not isinstance(license_file, str):
            raise RuntimeError("vendor_license_missing")
        _required_regular_nonempty_file(root, license_file, missing_code="vendor_license_missing")
    _required_regular_nonempty_file(root, _REQUIRED_VENDOR_NOTICE, missing_code="vendor_license_missing")

    for relative in _REQUIRED_REGISTRY_SUPPORT:
        _required_regular_nonempty_file(root, relative, missing_code="offline_registry_unavailable")
    try:
        load_offline_birth_place_registry(root / "data" / "birth_places" / "registry.v1.json")
    except BirthFoundationError as exc:
        raise RuntimeError("offline_registry_invalid") from exc

    try:
        with tempfile.TemporaryDirectory(prefix="metaphysics_lab_build_vendor_") as temp_dir:
            materialize_private_vendor(root, Path(temp_dir))
    except Exception as exc:
        raise RuntimeError("vendor_integrity_check_failed") from exc


def enforce_size_limit(content: str) -> None:
    if not isinstance(content, str):
        raise TypeError("distribution content must be text")
    if len(content.encode("utf-8")) > MAX_BUNDLE_BYTES:
        raise RuntimeError("distribution_size_limit_exceeded")


def render_distribution(repo_root: Path) -> Dict[str, bytes]:
    root = Path(repo_root)
    verify_vendor_inputs(root)
    bundle = _render_bundle(root)
    enforce_size_limit(bundle)
    artifacts = {
        "project_instructions.txt": _render_project_instructions(root).encode("utf-8"),
        "metaphysics_core.md": _render_metaphysics_core(root).encode("utf-8"),
        "metaphysics_lab.py": bundle.encode("utf-8"),
    }
    return {name: artifacts[name] for name in ARTIFACT_NAMES}


def build_distribution(repo_root: Path, output_dir: Path) -> Dict[str, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    artifacts = render_distribution(Path(repo_root))
    result = {}
    for name in ARTIFACT_NAMES:
        target = output / name
        target.write_bytes(artifacts[name])
        result[name] = target
    return result


def check_distribution(repo_root: Path, output_dir: Path) -> List[str]:
    output = Path(output_dir)
    expected = render_distribution(Path(repo_root))
    drift = []
    for name in ARTIFACT_NAMES:
        target = output / name
        if not target.exists() or target.read_bytes() != expected[name]:
            drift.append(name)
    extras = sorted(
        path.name for path in output.iterdir()
        if path.is_file() and path.name not in ARTIFACT_NAMES
    ) if output.exists() else []
    drift.extend(extras)
    return drift


def main(argv: Sequence[str] = None) -> int:
    parser = argparse.ArgumentParser(description="Build Metaphysics Lab AI distribution assets")
    parser.add_argument("--output-dir", default="dist/ai")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[1]
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = repo_root / output_dir

    if args.check:
        drift = check_distribution(repo_root, output_dir)
        if drift:
            print("AI distribution drift detected: %s" % ", ".join(drift), file=sys.stderr)
            return 1
        print("AI distribution is up to date")
        return 0

    build_distribution(repo_root, output_dir)
    print("Built AI distribution: %s" % output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
