from __future__ import annotations

from pathlib import Path
import re

from engine.ziwei.capabilities import get_capability


_REQUIRED_STATES = {
    "ziwei.transformations": "implemented/stable/on_demand",
    "ziwei.flying": "implemented/stable/on_demand",
    "ziwei.flow_month_stem": "implemented/experimental/on_demand",
    "ziwei.flow_day_stem": "implemented/experimental/on_demand",
    "ziwei.flow_hour_stem": "implemented/experimental/on_demand",
    "ziwei.natal_chart": "implemented/experimental/on_demand",
    "ziwei.flowing_stars": "implemented/experimental/on_demand",
}

_EXPECTED_RELEASE_IDENTITY = "v1.4.0"


def _state(capability_id: str) -> str:
    capability = get_capability(capability_id)
    maturity = capability["maturity"]
    maturity_text = "none" if maturity is None else str(maturity)
    return "%s/%s/%s" % (
        capability["implementation"],
        maturity_text,
        capability["routing"],
    )


def _release_identity(version_text: str) -> str:
    match = re.search(r"Metaphysics Lab Core：\*\*(v\d+\.\d+\.\d+)\*\*", version_text)
    return match.group(1) if match else "UNKNOWN"


def check_phase2c_rule_source() -> dict:
    checks = {
        capability_id: _state(capability_id)
        for capability_id in _REQUIRED_STATES
    }
    version_text = Path("VERSION.md").read_text(encoding="utf-8")
    release_identity = _release_identity(version_text)
    status = (
        "PASS"
        if checks == _REQUIRED_STATES and release_identity == _EXPECTED_RELEASE_IDENTITY
        else "FAIL"
    )
    return {
        "status": status,
        "checks": checks,
        "release_identity": release_identity,
        "expected_release_identity": _EXPECTED_RELEASE_IDENTITY,
        "main_baseline": "a5874fe6cb05d4eb8d8f4b3f757b17af45a5506e-or-legal-successor",
    }
