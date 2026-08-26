"""Read committed bundled-dependency metadata without consulting site-packages."""

from __future__ import annotations

import json
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Tuple


_MANIFEST_RELATIVE_PATH = Path("vendor") / "manifest.json"
_REQUIRED_PACKAGE_FIELDS = (
    "package_name",
    "import_namespace",
    "version",
    "source_repository",
    "source_revision",
    "source_artifact",
    "artifact_sha256",
    "vendored_tree_sha256",
    "license_spdx",
    "license_file",
    "bundled",
    "runtime_authority",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _freeze(value):
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _validated_manifest(raw: object) -> Mapping[str, object]:
    if not isinstance(raw, Mapping):
        raise ValueError("vendor manifest root must be an object")
    if raw.get("schema_version") != "1.0":
        raise ValueError("unsupported vendor manifest schema_version")
    packages = raw.get("packages")
    if not isinstance(packages, list) or not packages:
        raise ValueError("vendor manifest packages must be a non-empty list")

    seen = set()
    validated = []
    for row in packages:
        if not isinstance(row, Mapping):
            raise ValueError("vendor manifest package row must be an object")
        missing = [field for field in _REQUIRED_PACKAGE_FIELDS if field not in row]
        if missing:
            raise ValueError("vendor manifest package row missing fields: %s" % ", ".join(missing))
        name = row.get("package_name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("vendor manifest package_name must be non-empty text")
        if name in seen:
            raise ValueError("vendor manifest package_name values must be unique")
        seen.add(name)
        if row.get("bundled") is not True:
            raise ValueError("bundled core dependency must declare bundled=true")
        if row.get("runtime_authority") != "bundled":
            raise ValueError("bundled core dependency must declare runtime_authority=bundled")
        validated.append(dict(row))

    normalized = dict(raw)
    normalized["packages"] = validated
    return _freeze(normalized)


def bundled_vendor_manifest(path: Path = None) -> Mapping[str, object]:
    target = Path(path) if path is not None else _repo_root() / _MANIFEST_RELATIVE_PATH
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("bundled vendor manifest is unavailable: %s" % exc) from exc
    return _validated_manifest(raw)


def bundled_dependency(package_name: str, path: Path = None) -> Mapping[str, object]:
    if not isinstance(package_name, str) or not package_name:
        raise KeyError(package_name)
    manifest = bundled_vendor_manifest(path)
    packages = manifest["packages"]
    for row in packages:
        if row["package_name"] == package_name:
            return row
    raise KeyError(package_name)
