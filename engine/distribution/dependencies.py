"""Inspect bundled core and optional execution-environment dependencies."""

from __future__ import annotations

import importlib.util
from importlib import metadata
from pathlib import Path
from typing import Callable, Dict, Optional

from engine.vendor.manifest import bundled_dependency


_DEPENDENCIES = {
    "lunar-python": {
        "import_name": "lunar_python",
        "expected_version": "1.4.8",
        "role": "calendar",
        "required_for": ["calendar_resolution", "build_natal", "resolve_forecast_context"],
    },
    "tzdata": {
        "import_name": "tzdata",
        "expected_version": "2026.3",
        "role": "timezone",
        "required_for": ["calendar_resolution", "build_natal", "resolve_forecast_context"],
    },
    "geopy": {
        "import_name": "geopy",
        "expected_version": "2.5.0",
        "role": "location",
        "required_for": ["network_location_resolution"],
    },
    "timezonefinder": {
        "import_name": "timezonefinder",
        "expected_version": "8.2.0",
        "role": "location",
        "required_for": ["network_location_resolution"],
    },
}

_BUNDLED_CORE = ("lunar-python", "tzdata")
_OPTIONAL_EXTERNAL = ("geopy", "timezonefinder")


def _default_version_getter(distribution_name: str) -> Optional[str]:
    try:
        return metadata.version(distribution_name)
    except metadata.PackageNotFoundError:
        return None


def inspect_dependency(
    package_name: str,
    *,
    find_spec: Callable[[str], object] = importlib.util.find_spec,
    version_getter: Callable[[str], Optional[str]] = _default_version_getter,
) -> Dict[str, object]:
    if package_name not in _DEPENDENCIES:
        raise KeyError(package_name)
    config = _DEPENDENCIES[package_name]
    import_name = str(config["import_name"])
    try:
        spec = find_spec(import_name)
    except (ImportError, ModuleNotFoundError, ValueError):
        spec = None
    installed = spec is not None
    version = version_getter(package_name) if installed else None
    expected = str(config["expected_version"])
    return {
        "package": package_name,
        "import_name": import_name,
        "expected_version": expected,
        "installed": installed,
        "version": version,
        "matches_pin": bool(installed and version == expected),
        "role": str(config["role"]),
        "required_for": list(config["required_for"]),
    }


def inspect_optional_external_dependencies() -> Dict[str, Dict[str, object]]:
    return {name: inspect_dependency(name) for name in _OPTIONAL_EXTERNAL}


def inspect_external_dependencies() -> Dict[str, Dict[str, object]]:
    """Backward-compatible execution-environment diagnostics only."""
    result = {}
    for name in sorted(_DEPENDENCIES):
        row = inspect_dependency(name)
        row["deprecated"] = True
        row["authority"] = "diagnostic_only"
        result[name] = row
    return result


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def inspect_bundled_dependencies() -> Dict[str, Dict[str, object]]:
    """Report bundled-core authority without consulting public package state."""
    result: Dict[str, Dict[str, object]] = {}
    for name in _BUNDLED_CORE:
        config = _DEPENDENCIES[name]
        row = {
            "package": name,
            "expected_version": str(config["expected_version"]),
            "version": None,
            "bundled": True,
            "available": False,
            "runtime_uses_environment_package": False,
            "source_revision": None,
            "artifact_sha256": None,
            "vendored_tree_sha256": None,
            "license": None,
            "role": str(config["role"]),
            "required_for": list(config["required_for"]),
        }
        try:
            manifest_row = bundled_dependency(name)
            vendored_path = manifest_row.get("vendored_path")
            available = isinstance(vendored_path, str) and (_repo_root() / vendored_path).is_dir()
            row.update(
                {
                    "version": manifest_row.get("version"),
                    "available": bool(available),
                    "source_revision": manifest_row.get("source_revision"),
                    "artifact_sha256": manifest_row.get("artifact_sha256"),
                    "vendored_tree_sha256": manifest_row.get("vendored_tree_sha256"),
                    "license": manifest_row.get("license_spdx"),
                }
            )
        except (KeyError, RuntimeError, ValueError):
            pass
        result[name] = row
    return result
