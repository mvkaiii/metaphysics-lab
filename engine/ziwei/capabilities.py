"""Ziwei capability registry for Metaphysics Lab.

Capability state separates implementation, maturity, and routing. An
on-demand capability can be executable without being part of the default
analysis path.
"""
from __future__ import annotations

_CAPABILITIES = {
    "ziwei.flow_month_palaces": {
        "id": "ziwei.flow_month_palaces", "implementation": "implemented",
        "maturity": "stable", "routing": "default", "rule_version": "1.0",
        "module": "engine.ziwei.month", "dependencies": (),
        "supported_scopes": ("monthly",),
    },
    "ziwei.flow_day_palaces": {
        "id": "ziwei.flow_day_palaces", "implementation": "implemented",
        "maturity": "experimental", "routing": "on_demand", "rule_version": "1.0-exp",
        "module": "engine.ziwei.day", "dependencies": ("ziwei.flow_month_palaces",),
        "supported_scopes": ("daily",),
    },
    "ziwei.flow_hour_palaces": {
        "id": "ziwei.flow_hour_palaces", "implementation": "implemented",
        "maturity": "experimental", "routing": "on_demand", "rule_version": "1.0-exp",
        "module": "engine.ziwei.hour", "dependencies": ("ziwei.flow_day_palaces",),
        "supported_scopes": ("hourly",),
    },
    "ziwei.transformations": {
        "id": "ziwei.transformations", "implementation": "implemented",
        "maturity": "stable", "routing": "on_demand", "rule_version": "1.0",
        "module": "engine.ziwei.transformations", "dependencies": (),
    },
    "ziwei.flying": {
        "id": "ziwei.flying", "implementation": "implemented",
        "maturity": "stable", "routing": "on_demand", "rule_version": "1.0",
        "module": "engine.ziwei.flying", "dependencies": ("ziwei.transformations",),
    },
    "ziwei.natal_chart": {
        "id": "ziwei.natal_chart", "implementation": "implemented",
        "maturity": "experimental", "routing": "on_demand", "rule_version": "1.0-exp",
        "module": "engine.ziwei.natal", "dependencies": ("birth.true_solar_time", "ziwei.transformations", "ziwei.flying"),
    },
    "ziwei.flow_month_stem": {
        "id": "ziwei.flow_month_stem", "implementation": "implemented",
        "maturity": "experimental", "routing": "on_demand", "rule_version": "1.0-exp",
        "module": "engine.ziwei.fine_cycle_stems", "dependencies": (),
        "supported_scopes": ("monthly",),
    },
    "ziwei.flow_day_stem": {
        "id": "ziwei.flow_day_stem", "implementation": "implemented",
        "maturity": "experimental", "routing": "on_demand", "rule_version": "1.0-exp",
        "module": "engine.ziwei.fine_cycle_stems", "dependencies": (),
        "supported_scopes": ("daily",),
    },
    "ziwei.flow_hour_stem": {
        "id": "ziwei.flow_hour_stem", "implementation": "implemented",
        "maturity": "experimental", "routing": "on_demand", "rule_version": "1.0-exp",
        "module": "engine.ziwei.fine_cycle_stems", "dependencies": (),
        "supported_scopes": ("hourly",),
    },
    "ziwei.flow_month_transformations": {
        "id": "ziwei.flow_month_transformations", "implementation": "implemented",
        "maturity": "experimental", "routing": "on_demand", "rule_version": "1.0-exp",
        "module": "engine.ziwei.fine_cycle", "dependencies": ("ziwei.flow_month_stem", "ziwei.transformations"),
        "supported_scopes": ("monthly",),
    },
    "ziwei.flow_day_transformations": {
        "id": "ziwei.flow_day_transformations", "implementation": "implemented",
        "maturity": "experimental", "routing": "on_demand", "rule_version": "1.0-exp",
        "module": "engine.ziwei.fine_cycle", "dependencies": ("ziwei.flow_day_stem", "ziwei.transformations"),
        "supported_scopes": ("daily",),
    },
    "ziwei.flow_hour_transformations": {
        "id": "ziwei.flow_hour_transformations", "implementation": "implemented",
        "maturity": "experimental", "routing": "on_demand", "rule_version": "1.0-exp",
        "module": "engine.ziwei.fine_cycle", "dependencies": ("ziwei.flow_hour_stem", "ziwei.transformations"),
        "supported_scopes": ("hourly",),
    },
    "ziwei.flow_month_flying": {
        "id": "ziwei.flow_month_flying", "implementation": "implemented",
        "maturity": "experimental", "routing": "on_demand", "rule_version": "1.0-exp",
        "module": "engine.ziwei.fine_cycle", "dependencies": ("ziwei.flow_month_transformations", "ziwei.flying"),
        "supported_scopes": ("monthly",),
    },
    "ziwei.flow_day_flying": {
        "id": "ziwei.flow_day_flying", "implementation": "implemented",
        "maturity": "experimental", "routing": "on_demand", "rule_version": "1.0-exp",
        "module": "engine.ziwei.fine_cycle", "dependencies": ("ziwei.flow_day_transformations", "ziwei.flying"),
        "supported_scopes": ("daily",),
    },
    "ziwei.flow_hour_flying": {
        "id": "ziwei.flow_hour_flying", "implementation": "implemented",
        "maturity": "experimental", "routing": "on_demand", "rule_version": "1.0-exp",
        "module": "engine.ziwei.fine_cycle", "dependencies": ("ziwei.flow_hour_transformations", "ziwei.flying"),
        "supported_scopes": ("hourly",),
    },
    "ziwei.flowing_stars": {
        "id": "ziwei.flowing_stars", "implementation": "implemented",
        "maturity": "experimental", "routing": "on_demand", "rule_version": "1.0-exp",
        "module": "engine.ziwei.flowing_stars", "dependencies": (),
        "supported_scopes": ("decadal", "yearly", "monthly", "daily", "hourly"),
        "conditional_dependencies": {
            "decadal": ("ziwei.natal_chart",),
            "yearly": (),
            "monthly": ("ziwei.flow_month_stem",),
            "daily": ("ziwei.flow_day_stem",),
            "hourly": ("ziwei.flow_hour_stem",),
        },
    },
}


def get_capability(capability_id: str) -> dict:
    return dict(_CAPABILITIES[capability_id])


def can_execute(capability_id: str) -> bool:
    return get_capability(capability_id)["implementation"] == "implemented"


def should_run_by_default(capability_id: str) -> bool:
    cap = get_capability(capability_id)
    return cap["implementation"] == "implemented" and cap["routing"] == "default"