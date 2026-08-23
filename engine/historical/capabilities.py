"""Historical calibration capability registry."""
from __future__ import annotations

_CAPABILITIES = {
    "historical.activation_selector": {
        "id": "historical.activation_selector",
        "implementation": "implemented",
        "maturity": "experimental",
        "routing": "on_demand",
        "rule_version": "1.0-exp",
        "profile_id": "historical-activation-bazi-v1",
        "module": "engine.historical.selector",
        "dependencies": ("bazi.natal_chart",),
        "output_classification": "Project 推導盤面",
        "ranking_basis": "bazi_only",
    },
}


def get_capability(capability_id: str) -> dict:
    return dict(_CAPABILITIES[capability_id])


def can_execute(capability_id: str) -> bool:
    return get_capability(capability_id)["implementation"] == "implemented"


def should_run_by_default(capability_id: str) -> bool:
    cap = get_capability(capability_id)
    return cap["implementation"] == "implemented" and cap["routing"] == "default"
