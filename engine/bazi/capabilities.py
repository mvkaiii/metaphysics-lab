"""Bazi capability registry for Metaphysics Lab."""
from __future__ import annotations

_CAPABILITIES = {
    "bazi.natal_chart": {
        "id": "bazi.natal_chart",
        "implementation": "implemented",
        "maturity": "experimental",
        "routing": "on_demand",
        "rule_version": "1.0-exp",
        "module": "engine.bazi.natal",
        "dependencies": ("birth.input_resolution", "calendar.resolve"),
    },
}


def get_capability(capability_id: str) -> dict:
    return dict(_CAPABILITIES[capability_id])


def can_execute(capability_id: str) -> bool:
    return get_capability(capability_id)["implementation"] == "implemented"


def should_run_by_default(capability_id: str) -> bool:
    cap = get_capability(capability_id)
    return cap["implementation"] == "implemented" and cap["routing"] == "default"
