"""Capability registry for Phase 2C0 birth foundation."""
from __future__ import annotations

_CAPABILITIES = {
    "birth.input_resolution": {
        "id": "birth.input_resolution",
        "implementation": "implemented",
        "maturity": "experimental",
        "routing": "on_demand",
        "rule_version": "1.0-exp",
        "module": "engine.birth.input_resolution",
        "dependencies": (),
    },
    "birth.location_resolution": {
        "id": "birth.location_resolution",
        "implementation": "implemented",
        "maturity": "experimental",
        "routing": "on_demand",
        "rule_version": "1.0-exp",
        "module": "engine.birth.location",
        "dependencies": ("birth.input_resolution",),
    },
    "birth.true_solar_time": {
        "id": "birth.true_solar_time",
        "implementation": "implemented",
        "maturity": "experimental",
        "routing": "on_demand",
        "rule_version": "1.0-exp",
        "module": "engine.birth.time_views",
        "dependencies": ("birth.location_resolution",),
    },
}


def get_capability(capability_id: str) -> dict:
    return dict(_CAPABILITIES[capability_id])


def can_execute(capability_id: str) -> bool:
    return get_capability(capability_id)["implementation"] == "implemented"


def should_run_by_default(capability_id: str) -> bool:
    capability = get_capability(capability_id)
    return (
        capability["implementation"] == "implemented"
        and capability["routing"] == "default"
    )
