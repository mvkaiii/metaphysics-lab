"""Inspect external runtime dependencies without importing them."""

from __future__ import annotations

import importlib.util
from importlib import metadata
from typing import Callable, Dict, Optional


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


def inspect_external_dependencies() -> Dict[str, Dict[str, object]]:
    return {
        name: inspect_dependency(name)
        for name in sorted(_DEPENDENCIES)
    }
