"""Read canonical capability registries without importing engine packages."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Dict, Mapping


_REGISTRY_FILES = (
    "birth/capabilities.py",
    "bazi/capabilities.py",
    "natal/capabilities.py",
    "ziwei/capabilities.py",
)


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
        capability_id = value.get("id")
        if capability_id != key:
            raise ValueError("capability id/key mismatch for %s in %s" % (key, path))
        result[key] = _json_safe(value)
    return result


def load_capabilities(engine_root: Path = None) -> Dict[str, Dict[str, Any]]:
    root = _engine_root() if engine_root is None else Path(engine_root)
    combined = {}
    for relative in _REGISTRY_FILES:
        registry = _read_registry(root / relative)
        for capability_id, capability in registry.items():
            if capability_id in combined:
                raise ValueError("duplicate capability id: %s" % capability_id)
            combined[capability_id] = capability
    return {key: combined[key] for key in sorted(combined)}
