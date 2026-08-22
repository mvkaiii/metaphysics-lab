"""Cross-system natal capability registry for Metaphysics Lab."""
from __future__ import annotations

_CAPABILITIES = {
    "natal.reconciliation": {
        "id": "natal.reconciliation",
        "implementation": "implemented",
        "maturity": "stable",
        "routing": "on_demand",
        "rule_version": "1.0",
        "module": "engine.natal.reconciliation",
        "dependencies": (),
    },
    "natal.markdown_export": {
        "id": "natal.markdown_export",
        "implementation": "implemented",
        "maturity": "stable",
        "routing": "on_demand",
        "rule_version": "1.0",
        "module": "engine.natal.export",
        "dependencies": ("natal.reconciliation",),
    },
}


def get_capability(capability_id: str) -> dict:
    return dict(_CAPABILITIES[capability_id])


def can_execute(capability_id: str) -> bool:
    return get_capability(capability_id)["implementation"] == "implemented"


def should_run_by_default(capability_id: str) -> bool:
    cap = get_capability(capability_id)
    return cap["implementation"] == "implemented" and cap["routing"] == "default"
