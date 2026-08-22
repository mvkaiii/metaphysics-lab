from __future__ import annotations

from pathlib import Path

from engine.ziwei.capabilities import get_capability


_REQUIRED_STATES = {
    "ziwei.transformations": "implemented/stable/on_demand",
    "ziwei.flying": "implemented/stable/on_demand",
    "ziwei.flow_month_stem": "implemented/experimental/on_demand",
    "ziwei.flow_day_stem": "implemented/experimental/on_demand",
    "ziwei.flow_hour_stem": "implemented/experimental/on_demand",
    "ziwei.natal_chart": "implemented/experimental/on_demand",
    "ziwei.flowing_stars": "planned/none/on_demand",
}


def _state(capability_id: str) -> str:
    capability = get_capability(capability_id)
    maturity = capability["maturity"]
    maturity_text = "none" if maturity is None else str(maturity)
    return "%s/%s/%s" % (
        capability["implementation"],
        maturity_text,
        capability["routing"],
    )


def check_phase2c_rule_source() -> dict:
    checks = {
        capability_id: _state(capability_id)
        for capability_id in _REQUIRED_STATES
    }
    version_text = Path("VERSION.md").read_text(encoding="utf-8")
    release_identity = "v1.2.0" if "Metaphysics Lab Core：**v1.2.0**" in version_text else "UNKNOWN"
    status = "PASS" if checks == _REQUIRED_STATES and release_identity == "v1.2.0" else "FAIL"
    return {
        "status": status,
        "checks": checks,
        "release_identity": release_identity,
        "main_baseline": "bb08ded1d8ed9b026bcd3d8719f00515da6054c3-or-legal-successor",
    }
