#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the portable AI-first Metaphysics Lab distribution assets.

The source tree stays modular. This builder creates exactly three deterministic
artifacts for end users:

- metaphysics_lab.py
- METAPHYSICS_CORE.md
- PROJECT_INSTRUCTIONS.md
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import shutil
import sys
import tempfile
import zlib
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence

from engine.distribution.constants import (
    CASE_SCHEMA_VERSION,
    DISTRIBUTION_RUNTIME_VERSION,
    PROJECT_CONTRACT_VERSION,
    RUNTIME_SCHEMA_VERSION,
    SUPPORTED_ACTIONS,
)
from engine.distribution.dependencies import _DEPENDENCIES
from engine.distribution.manifest import load_capabilities


BUILD_FORMAT_VERSION = "1.0"
ARTIFACT_NAMES = (
    "METAPHYSICS_CORE.md",
    "PROJECT_INSTRUCTIONS.md",
    "metaphysics_lab.py",
)

_BOOTSTRAP = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# GENERATED FILE - DO NOT EDIT
"""Portable Metaphysics Lab runtime bundle.

Generated from the modular repository source. Third-party packages are not
vendored; runtime-info remains available even when calculation dependencies are
missing.
"""

from __future__ import annotations

import argparse
import atexit
import base64
import hashlib
import importlib
import importlib.util
import json
import shutil
import sys
import tempfile
import zlib
from importlib import metadata
from pathlib import Path

BUILD_FORMAT_VERSION = @@BUILD_FORMAT_VERSION@@
SOURCE_DIGEST = @@SOURCE_DIGEST@@
PROJECT_CONTRACT_VERSION = @@PROJECT_CONTRACT_VERSION@@
RUNTIME_SCHEMA_VERSION = @@RUNTIME_SCHEMA_VERSION@@
CASE_SCHEMA_VERSION = @@CASE_SCHEMA_VERSION@@
DISTRIBUTION_RUNTIME_VERSION = @@DISTRIBUTION_RUNTIME_VERSION@@
_SUPPORTED_ACTIONS = json.loads(@@SUPPORTED_ACTIONS_JSON@@)
_CAPABILITIES = json.loads(@@CAPABILITIES_JSON@@)
_DEPENDENCIES = json.loads(@@DEPENDENCIES_JSON@@)
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


def _version_getter(distribution_name):
    try:
        return metadata.version(distribution_name)
    except metadata.PackageNotFoundError:
        return None


def _inspect_dependencies():
    result = {}
    for package_name in sorted(_DEPENDENCIES):
        config = _DEPENDENCIES[package_name]
        import_name = str(config["import_name"])
        try:
            spec = importlib.util.find_spec(import_name)
        except (ImportError, ModuleNotFoundError, ValueError):
            spec = None
        installed = spec is not None
        version = _version_getter(package_name) if installed else None
        expected = str(config["expected_version"])
        result[package_name] = {
            "package": package_name,
            "import_name": import_name,
            "expected_version": expected,
            "installed": installed,
            "version": version,
            "matches_pin": bool(installed and version == expected),
            "role": str(config["role"]),
            "required_for": list(config["required_for"]),
        }
    return result


def runtime_info():
    return {
        "project_contract_version": PROJECT_CONTRACT_VERSION,
        "runtime_schema_version": RUNTIME_SCHEMA_VERSION,
        "case_schema_version": CASE_SCHEMA_VERSION,
        "distribution_runtime_version": DISTRIBUTION_RUNTIME_VERSION,
        "supported_actions": list(_SUPPORTED_ACTIONS),
        "capabilities": _CAPABILITIES,
        "external_dependencies": _inspect_dependencies(),
    }


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
    records = payload.get("files")
    if not isinstance(records, list):
        raise RuntimeError("embedded source payload is invalid")

    root = Path(tempfile.mkdtemp(prefix="metaphysics_lab_runtime_"))
    try:
        for record in records:
            relative = str(record["path"])
            text = str(record["text"])
            expected = str(record["sha256"])
            encoded = text.encode("utf-8")
            if hashlib.sha256(encoded).hexdigest() != expected:
                raise RuntimeError("embedded file digest mismatch: %s" % relative)
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(encoded)
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
    if action == "runtime_info":
        return _ok(action, runtime_info())

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


def discover_owned_sources(repo_root: Path) -> List[str]:
    root = Path(repo_root)
    paths = []
    for path in (root / "engine").rglob("*.py"):
        if path.is_file():
            paths.append(path.relative_to(root).as_posix())
    for path in (root / "templates").rglob("*.tmpl"):
        if path.is_file():
            paths.append(path.relative_to(root).as_posix())
    return sorted(set(paths))


def _source_records(repo_root: Path, paths: Sequence[str]) -> List[Dict[str, str]]:
    root = Path(repo_root)
    records = []
    for relative in paths:
        raw = (root / relative).read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("owned runtime source is not UTF-8: %s" % relative) from exc
        normalized = _normalize_text(text)
        encoded = normalized.encode("utf-8")
        records.append(
            {
                "path": relative,
                "sha256": hashlib.sha256(encoded).hexdigest(),
                "text": normalized,
            }
        )
    return records


def _payload(repo_root: Path):
    paths = discover_owned_sources(repo_root)
    records = _source_records(repo_root, paths)
    data = {"files": records}
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
    for relative in ("core/AI工作流程.md", "core/命理分析作業規範.md"):
        text = _normalize_text((root / relative).read_text(encoding="utf-8")).rstrip()
        sections.append("<!-- Source: %s -->\n%s" % (relative, text))
    return "\n\n---\n\n".join(sections).rstrip() + "\n"


def _compact_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _render_bundle(repo_root: Path) -> str:
    root = Path(repo_root)
    payload_b64, source_digest, source_files = _payload(root)
    capabilities = load_capabilities(root / "engine")
    dependencies = {name: dict(_DEPENDENCIES[name]) for name in sorted(_DEPENDENCIES)}

    replacements = {
        "@@BUILD_FORMAT_VERSION@@": repr(BUILD_FORMAT_VERSION),
        "@@SOURCE_DIGEST@@": repr(source_digest),
        "@@PROJECT_CONTRACT_VERSION@@": repr(PROJECT_CONTRACT_VERSION),
        "@@RUNTIME_SCHEMA_VERSION@@": repr(RUNTIME_SCHEMA_VERSION),
        "@@CASE_SCHEMA_VERSION@@": repr(CASE_SCHEMA_VERSION),
        "@@DISTRIBUTION_RUNTIME_VERSION@@": repr(DISTRIBUTION_RUNTIME_VERSION),
        "@@SUPPORTED_ACTIONS_JSON@@": repr(_compact_json(list(SUPPORTED_ACTIONS))),
        "@@CAPABILITIES_JSON@@": repr(_compact_json(capabilities)),
        "@@DEPENDENCIES_JSON@@": repr(_compact_json(dependencies)),
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


def render_distribution(repo_root: Path) -> Dict[str, bytes]:
    root = Path(repo_root)
    artifacts = {
        "PROJECT_INSTRUCTIONS.md": _render_project_instructions(root).encode("utf-8"),
        "METAPHYSICS_CORE.md": _render_metaphysics_core(root).encode("utf-8"),
        "metaphysics_lab.py": _render_bundle(root).encode("utf-8"),
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
