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
    "distribution.prospective_validation": {
        "id": "distribution.prospective_validation",
        "implementation": "implemented",
        "maturity": "experimental",
        "routing": "on_demand",
        "rule_version": "prospective-validation-v2-exp",
        "module": "engine.distribution.prospective_validation",
        "dependencies": ("distribution.prospective_forecast_governance",),
        "output_classification": "Validation governance metadata",
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
    "distribution.historical_personalization": {
        "id": "distribution.historical_personalization",
        "implementation": "implemented",
        "maturity": "experimental",
        "routing": "on_demand",
        "rule_version": "lin_tianji_historical_personalization_v1-exp",
        "module": "engine.distribution.historical_personalization",
        "dependencies": ("distribution.evidence_engine",),
        "output_classification": "Historical personalization metadata",
        "ranking_authority": False,
    },
    "distribution.case_revision_integrity": {
        "id": "distribution.case_revision_integrity",
        "implementation": "implemented",
        "maturity": "experimental",
        "routing": "on_demand",
        "rule_version": "case-revision-v1-exp",
        "module": "engine.distribution.case_revision",
        "dependencies": (),
        "output_classification": "Case governance metadata",
        "ranking_authority": False,
    },
    "distribution.lock_provenance": {
        "id": "distribution.lock_provenance",
        "implementation": "implemented",
        "maturity": "experimental",
        "routing": "on_demand",
        "rule_version": "2.0-exp",
        "module": "engine.distribution.lock_provenance",
        "dependencies": ("distribution.case_revision_integrity",),
        "output_classification": "Lock governance metadata",
        "ranking_authority": False,
    },
    "distribution.guided_natal_build": {
        "id": "distribution.guided_natal_build",
        "implementation": "implemented",
        "maturity": "experimental",
        "routing": "on_demand",
        "rule_version": "1.0-exp",
        "module": "engine.distribution.guided_natal_build",
        "dependencies": ("distribution.case_revision_integrity",),
        "output_classification": "Natal workflow governance metadata",
        "ranking_authority": False,
    },
    "distribution.interpretation_contract": {
        "id": "distribution.interpretation_contract",
        "implementation": "implemented",
        "maturity": "experimental",
        "routing": "on_demand",
        "rule_version": "lin_tianji_interpretation_contract_v1-exp",
        "supported_profiles": (
            "lin_tianji_interpretation_contract_v1-exp",
            "lin_tianji_interpretation_contract_v2-exp",
        ),
        "module": "engine.distribution.interpretation_contract",
        "dependencies": ("distribution.evidence_engine",),
        "output_classification": "Interpretation contract metadata",
        "ranking_authority": False,
    },
}


def get_capability(capability_id: str) -> dict:
    return dict(_CAPABILITIES[capability_id])


def can_execute(capability_id: str) -> bool:
    return get_capability(capability_id)["implementation"] == "implemented"


def should_run_by_default(capability_id: str) -> bool:
    cap = get_capability(capability_id)
    return cap["implementation"] == "implemented" and cap["routing"] == "default"