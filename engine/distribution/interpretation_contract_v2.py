"""Versioned Interpretation vNext wrapper preserving Phase 3/4/5 authority."""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Mapping, Sequence

from .claim_consumption_contract import build_claim_consumption_bundle
from .claim_evidence import build_claim_evidence_packets
from .coordination_policy_v2 import build_coordination_bundle
from .event_family_attribution import build_event_family_attribution_bundle
from .hierarchical_claim_authority import build_hierarchical_claim_authority_bundle
from .hybrid_claim_composer import build_hybrid_claim_composer_bundle
from .hybrid_output_contract import build_hybrid_output_contract
from .interpretation_contract import build_interpretation_contract


INTERPRETATION_PROFILE_VERSION_V2 = "lin_tianji_interpretation_contract_v2-exp"

READING_POLICY = {
    "bazi_order": [
        "day_master_and_pillar_roles",
        "month_command",
        "strength_evidence_if_materialized",
        "pattern_and_useful_god_if_materialized",
        "natal_interactions_and_distance_if_materialized",
        "shensha_auxiliary_if_materialized",
        "decadal",
        "yearly",
        "qualified_fine_time",
    ],
    "ziwei_order": [
        "ming_shen_fude",
        "ming_cai_guan_qian",
        "opposition_axes",
        "stars_in_palace_context",
        "natal_transformations",
        "natal_flying_if_materialized",
        "decadal",
        "yearly",
        "small_limit_if_materialized",
        "qualified_fine_cycle",
        "repeated_domain_activation",
    ],
    "guards": {
        "missing_layer_must_abstain": True,
        "five_element_count_is_not_strength_conclusion": True,
        "ten_god_is_not_event_formula": True,
        "shensha_auxiliary_only": True,
        "bazi_cannot_rewrite_ziwei": True,
        "ziwei_cannot_rewrite_bazi": True,
        "cross_system_conflict_must_be_preserved": True,
        "coordination_relation_is_python_authority": True,
    },
}


def _digest(value: object) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def build_interpretation_contract_v2(
    base_ranking: Mapping[str, object],
    anchor: Mapping[str, object],
    *,
    structural_interpretation: Mapping[str, object],
    personalization: Mapping[str, object] | None = None,
    local_windows: Sequence[Mapping[str, object]] | None = None,
    locked_forecast: Mapping[str, object] | None = None,
) -> dict:
    v1 = build_interpretation_contract(
        base_ranking,
        anchor,
        personalization=personalization,
        local_windows=local_windows,
        locked_forecast=locked_forecast,
    )
    claim_bundle = build_claim_evidence_packets(
        base_ranking=base_ranking,
        structural_interpretation=structural_interpretation,
        domain_interpretation=v1["domain_interpretation"],
    )
    phase3_caps = {
        str(row["primary_domain"]): str(row["allowed_specificity"])
        for row in base_ranking.get("domains", [])
        if isinstance(row, Mapping)
    }
    coordination_bundle = build_coordination_bundle(
        claim_evidence_packets=claim_bundle["packets"],
        target_scope=str(base_ranking["target_scope"]),
        source_ranking_digest=str(base_ranking["ranking_digest"]),
        source_interpretation_digest=str(structural_interpretation["interpretation_digest"]),
        phase3_specificity_by_domain=phase3_caps,
    )
    claim_consumption_bundle = build_claim_consumption_bundle(
        claim_evidence_bundle=claim_bundle,
        coordination_bundle=coordination_bundle,
    )
    event_family_attribution_bundle = build_event_family_attribution_bundle(
        base_ranking=base_ranking,
        structural_interpretation=structural_interpretation,
    )
    hierarchical_claim_authority_bundle = build_hierarchical_claim_authority_bundle(
        claim_consumption_bundle=claim_consumption_bundle,
        event_family_attribution_bundle=event_family_attribution_bundle,
        claim_evidence_bundle=claim_bundle,
    )
    hybrid_claim_composer_bundle = build_hybrid_claim_composer_bundle(
        hierarchical_authority_bundle=hierarchical_claim_authority_bundle,
        event_family_attribution_bundle=event_family_attribution_bundle,
        interpretation_contract=v1,
        claim_evidence_bundle=claim_bundle,
    )
    hybrid_output_contract_bundle = build_hybrid_output_contract(
        hybrid_claim_composer_bundle=hybrid_claim_composer_bundle,
    )

    result = copy.deepcopy(v1)
    result["profile_version"] = INTERPRETATION_PROFILE_VERSION_V2
    result["claim_evidence_profile_version"] = claim_bundle["profile_version"]
    result["claim_evidence_digest"] = claim_bundle["claim_evidence_digest"]
    result["claim_evidence_packets"] = copy.deepcopy(claim_bundle["packets"])
    result["global_conflicts"] = copy.deepcopy(claim_bundle["global_conflicts"])
    result["coordination_policy_version"] = coordination_bundle["policy_version"]
    result["coordination_digest"] = coordination_bundle["coordination_digest"]
    result["coordination_relations"] = copy.deepcopy(coordination_bundle["relations"])
    result["claim_consumption_profile_version"] = claim_consumption_bundle["profile_version"]
    result["claim_consumption_digest"] = claim_consumption_bundle["claim_consumption_digest"]
    result["claim_consumption_decisions"] = copy.deepcopy(claim_consumption_bundle["decisions"])

    result["event_family_attribution_profile_version"] = event_family_attribution_bundle["profile_version"]
    result["event_family_attribution_digest"] = event_family_attribution_bundle["event_family_attribution_digest"]
    result["event_family_attribution_children"] = copy.deepcopy(event_family_attribution_bundle["children"])
    result["hierarchical_claim_authority_profile_version"] = hierarchical_claim_authority_bundle["profile_version"]
    result["hierarchical_claim_authority_digest"] = hierarchical_claim_authority_bundle["hierarchical_claim_authority_digest"]
    result["hierarchical_claim_authority_decisions"] = copy.deepcopy(hierarchical_claim_authority_bundle["decisions"])
    result["hybrid_claim_composer_profile_version"] = hybrid_claim_composer_bundle["profile_version"]
    result["hybrid_claim_composer_digest"] = hybrid_claim_composer_bundle["hybrid_claim_composer_digest"]
    result["hybrid_claim_composer_children"] = copy.deepcopy(hybrid_claim_composer_bundle["children"])
    result["hybrid_composition_groups"] = copy.deepcopy(hybrid_claim_composer_bundle["composition_groups"])
    result["hybrid_output_contract_profile_version"] = hybrid_output_contract_bundle["profile_version"]
    result["hybrid_output_contract_digest"] = hybrid_output_contract_bundle["hybrid_output_contract_digest"]
    result["hybrid_render_units"] = copy.deepcopy(hybrid_output_contract_bundle["render_units"])

    result["reading_policy"] = copy.deepcopy(READING_POLICY)
    result["global_abstentions"] = [] if result["domain_interpretation"] else ["abstain_domain"]
    result.pop("interpretation_contract_digest", None)
    result["interpretation_contract_digest"] = _digest(result)
    return result
