"""Ziwei capability registry for Metaphysics Lab.

Capability state separates implementation, maturity, and routing. An
on-demand capability can be executable without being part of the default
analysis path.
"""
from __future__ import annotations

_CAPABILITIES = {
    "ziwei.flow_month_palaces": {
        "id": "ziwei.flow_month_palaces",
        "implementation": "implemented",
        "maturity": "stable",
        "routing": "default",
        "rule_version": "1.0",
        "module": "engine.ziwei.month",
        "dependencies": (),
    },
    "ziwei.flow_day_palaces": {
        "id": "ziwei.flow_day_palaces",
        "implementation": "implemented",
        "maturity": "experimental",
        "routing": "on_demand",
        "rule_version": "1.0-exp",
        "module": "engine.ziwei.day",
        "dependencies": ("ziwei.flow_month_palaces",),
    },
    "ziwei.flow_hour_palaces": {
        "id": "ziwei.flow_hour_palaces",
        "implementation": "implemented",
        "maturity": "experimental",
        "routing": "on_demand",
        "rule_version": "1.0-exp",
        "module": "engine.ziwei.hour",
        "dependencies": ("ziwei.flow_day_palaces",),
    },
    "ziwei.transformations": {
        "id": "ziwei.transformations",
        "implementation": "implemented",
        "maturity": "experimental",
        "routing": "on_demand",
        "rule_version": "1.0-exp",
        "module": "engine.ziwei.transformations",
        "dependencies": (),
    },
    "ziwei.flying": {
        "id": "ziwei.flying",
        "implementation": "implemented",
        "maturity": "experimental",
        "routing": "on_demand",
        "rule_version": "1.0-exp",
        "module": "engine.ziwei.flying",
        "dependencies": ("ziwei.transformations",),
    },
    "ziwei.flow_month_transformations": {
        "id": "ziwei.flow_month_transformations",
        "implementation": "planned",
        "maturity": None,
        "routing": "on_demand",
        "rule_version": None,
        "module": "engine.ziwei.transformations",
        "dependencies": ("ziwei.flow_month_palaces", "ziwei.transformations"),
    },
    "ziwei.flow_day_transformations": {
        "id": "ziwei.flow_day_transformations",
        "implementation": "planned",
        "maturity": None,
        "routing": "on_demand",
        "rule_version": None,
        "module": "engine.ziwei.transformations",
        "dependencies": ("ziwei.flow_day_palaces", "ziwei.transformations"),
    },
    "ziwei.flow_hour_transformations": {
        "id": "ziwei.flow_hour_transformations",
        "implementation": "planned",
        "maturity": None,
        "routing": "on_demand",
        "rule_version": None,
        "module": "engine.ziwei.transformations",
        "dependencies": ("ziwei.flow_hour_palaces", "ziwei.transformations"),
    },
    "ziwei.flow_month_flying": {
        "id": "ziwei.flow_month_flying",
        "implementation": "planned",
        "maturity": None,
        "routing": "on_demand",
        "rule_version": None,
        "module": "engine.ziwei.flying",
        "dependencies": ("ziwei.flow_month_transformations", "ziwei.flying"),
    },
    "ziwei.flow_day_flying": {
        "id": "ziwei.flow_day_flying",
        "implementation": "planned",
        "maturity": None,
        "routing": "on_demand",
        "rule_version": None,
        "module": "engine.ziwei.flying",
        "dependencies": ("ziwei.flow_day_transformations", "ziwei.flying"),
    },
    "ziwei.flow_hour_flying": {
        "id": "ziwei.flow_hour_flying",
        "implementation": "planned",
        "maturity": None,
        "routing": "on_demand",
        "rule_version": None,
        "module": "engine.ziwei.flying",
        "dependencies": ("ziwei.flow_hour_transformations", "ziwei.flying"),
    },
    "ziwei.flowing_stars": {
        "id": "ziwei.flowing_stars",
        "implementation": "planned",
        "maturity": None,
        "routing": "on_demand",
        "rule_version": None,
        "module": "engine.ziwei.stars",
        "dependencies": (),
    },
}


def get_capability(capability_id: str) -> dict:
    """Return a copy of one capability record or raise ``KeyError``."""
    return dict(_CAPABILITIES[capability_id])


def can_execute(capability_id: str) -> bool:
    """Whether a capability has a formal executable implementation."""
    return get_capability(capability_id)["implementation"] == "implemented"


def should_run_by_default(capability_id: str) -> bool:
    """Whether the router should run an executable capability by default."""
    cap = get_capability(capability_id)
    return cap["implementation"] == "implemented" and cap["routing"] == "default"
