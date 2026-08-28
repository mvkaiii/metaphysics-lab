"""Distribution-level capability registry for forecast governance."""
from __future__ import annotations

_CAPABILITIES = {
    "distribution.prospective_forecast_governance": {
        "id": "distribution.prospective_forecast_governance",
        "implementation": "implemented",
        "maturity": "experimental",
        "routing": "on_demand",
        "rule_version": "lin_tianji_v1.5-exp",
        "module": "engine.distribution.prospective",
        "dependencies": (),
        "output_classification": "Forecast governance metadata",
        "ranking_authority": False,
    },
    "distribution.structural_interpretation": {
        "id": "distribution.structural_interpretation",
        "implementation": "implemented",
        "maturity": "experimental",
        "routing": "on_demand",
        "rule_version": "lin_tianji_structural_v1-exp",
        "module": "engine.distribution.structural_interpretation",
        "dependencies": ("distribution.prospective_forecast_governance",),
        "output_classification": "Project 推導盤面",
        "ranking_authority": False,
    },
    "distribution.evidence_engine": {
        "id": "distribution.evidence_engine",
        "implementation": "implemented",
        "maturity": "experimental",
        "routing": "on_demand",
        "rule_version": "lin_tianji_v1.5-exp",
        "module": "engine.distribution.evidence_ranker",
        "dependencies": ("distribution.prospective_forecast_governance",),
        "output_classification": "Project 推導盤面",
        "ranking_authority": True,
    },
}


def get_capability(capability_id: str) -> dict:
    return dict(_CAPABILITIES[capability_id])


def can_execute(capability_id: str) -> bool:
    return get_capability(capability_id)["implementation"] == "implemented"


def should_run_by_default(capability_id: str) -> bool:
    cap = get_capability(capability_id)
    return cap["implementation"] == "implemented" and cap["routing"] == "default"
