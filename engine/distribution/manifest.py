"""Read and validate canonical capability registries without importing engines."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional


CAPABILITY_MANIFEST_VERSION = "1.0"

_REGISTRY_FILES = (
    "birth/capabilities.py",
    "bazi/capabilities.py",
    "distribution/capabilities.py",
    "historical/capabilities.py",
    "natal/capabilities.py",
    "ziwei/capabilities.py",
)

_REQUIRED_FIELDS = frozenset(
    {
        "id",
        "implementation",
        "maturity",
        "routing",
        "rule_version",
        "module",
        "dependencies",
    }
)
_OPTIONAL_FIELDS = frozenset(
    {
        "output_classification",
        "ranking_authority",
        "qualification_status",
        "supported_scopes",
        "required_inputs",
        "supported_profiles",
        "conditional_dependencies",
        # Existing registry-specific metadata retained as part of the
        # canonical registry truth instead of being silently discarded.
        "profile_id",
        "ranking_basis",
    }
)
_IMPLEMENTATIONS = frozenset({"implemented", "not_implemented"})
_MATURITIES = frozenset({"stable", "experimental"})
_ROUTINGS = frozenset({"default", "on_demand", "unavailable"})


def _engine_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _json_safe(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    return value


def _nonblank_text(value: object, field: str, capability_id: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            "capability %s field %s must be non-blank text"
            % (capability_id, field)
        )
    return value


def _validate_dependency_list(
    value: object, field: str, capability_id: str
) -> None:
    if not isinstance(value, list):
        raise ValueError(
            "capability %s field %s must be a sequence"
            % (capability_id, field)
        )
    for dependency in value:
        if not isinstance(dependency, str) or not dependency.strip():
            raise ValueError(
                "capability %s field %s must contain only non-blank dependency ids"
                % (capability_id, field)
            )


def validate_capability_registry_entry(
    capability_id: str, capability: Mapping[str, object]
) -> dict:
    """Validate and JSON-normalize one capability registry entry."""
    if not isinstance(capability_id, str) or not capability_id.strip():
        raise ValueError("capability id must be non-blank text")
    if not isinstance(capability, Mapping):
        raise ValueError("capability %s must be a mapping" % capability_id)

    keys = set(capability)
    missing = sorted(_REQUIRED_FIELDS - keys)
    unknown = sorted(keys - (_REQUIRED_FIELDS | _OPTIONAL_FIELDS))
    if missing or unknown:
        raise ValueError(
            "capability %s fields do not match manifest v1 contract; missing=%s unknown=%s"
            % (capability_id, missing, unknown)
        )

    normalized = _json_safe(capability)
    if normalized.get("id") != capability_id:
        raise ValueError("capability id/key mismatch for %s" % capability_id)

    for field in ("id", "rule_version", "module"):
        _nonblank_text(normalized.get(field), field, capability_id)

    implementation = normalized.get("implementation")
    maturity = normalized.get("maturity")
    routing = normalized.get("routing")
    if implementation not in _IMPLEMENTATIONS:
        raise ValueError(
            "capability %s has unsupported implementation: %r"
            % (capability_id, implementation)
        )
    if maturity not in _MATURITIES:
        raise ValueError(
            "capability %s has unsupported maturity: %r"
            % (capability_id, maturity)
        )
    if routing not in _ROUTINGS:
        raise ValueError(
            "capability %s has unsupported routing: %r"
            % (capability_id, routing)
        )

    _validate_dependency_list(
        normalized.get("dependencies"), "dependencies", capability_id
    )

    conditional = normalized.get("conditional_dependencies")
    if conditional is not None:
        if not isinstance(conditional, Mapping):
            raise ValueError(
                "capability %s conditional_dependencies must be a mapping"
                % capability_id
            )
        for scope, dependencies in conditional.items():
            _nonblank_text(scope, "conditional_dependencies scope", capability_id)
            _validate_dependency_list(
                dependencies,
                "conditional_dependencies.%s" % scope,
                capability_id,
            )

    try:
        json.dumps(
            normalized,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "capability %s contains non-JSON-safe metadata" % capability_id
        ) from exc

    return normalized


def _read_registry(path: Path) -> Dict[str, Dict[str, Any]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    registry_node = None
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "_CAPABILITIES":
                registry_node = node.value
                break
        if registry_node is not None:
            break
    if registry_node is None:
        raise ValueError("capability registry missing _CAPABILITIES: %s" % path)

    raw = ast.literal_eval(registry_node)
    if not isinstance(raw, dict):
        raise ValueError("capability registry must be a dict: %s" % path)

    result = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not isinstance(value, dict):
            raise ValueError("invalid capability registry entry in %s" % path)
        result[key] = validate_capability_registry_entry(key, value)
    return result


def load_capability_manifest(engine_root: Optional[Path] = None) -> dict:
    """Return deterministic manifest metadata plus sorted capabilities."""
    root = _engine_root() if engine_root is None else Path(engine_root)
    combined = {}
    for relative in _REGISTRY_FILES:
        registry = _read_registry(root / relative)
        for capability_id, capability in registry.items():
            if capability_id in combined:
                raise ValueError("duplicate capability id: %s" % capability_id)
            combined[capability_id] = capability
    return {
        "manifest_version": CAPABILITY_MANIFEST_VERSION,
        "capabilities": {key: combined[key] for key in sorted(combined)},
    }


def load_capabilities(engine_root: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    """Backward-compatible capability-id to metadata mapping."""
    return load_capability_manifest(engine_root)["capabilities"]
