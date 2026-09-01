import copy
import hashlib
import json

from engine.distribution.claim_evidence import build_claim_evidence_packets
from engine.distribution.interpretation_contract import build_interpretation_contract
from engine.distribution.interpretation_contract_v2 import READING_POLICY, build_interpretation_contract_v2


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def evidence(feature_id, system, domain, *, scope="yearly", role="target_evidence", dependency=None):
    return {
        "feature_id": feature_id,
        "system": system,
        "scope": scope,
        "role": role,
        "primary_domain": domain,
        "strength_class": "strong",
        "maturity": "stable",
        "qualification_status": "qualified",
        "source_family": f"synthetic.{system}",
        "dependency_family": dependency or f"dep:{feature_id}",
        "provenance": {"fixture": True},
    }


def fixtures(disjoint=False):
    if disjoint:
        features = [evidence("b1", "bazi", "career"), evidence("z1", "ziwei", "finance")]
        domains = [
            {
                "primary_domain": "career",
                "rank": 1,
                "event_families": ["formal_role"],
                "feature_ids": ["b1"],
                "allowed_specificity": "event_family",
                "independent_dependency_count": 1,
            },
            {
                "primary_domain": "finance",
                "rank": 2,
                "event_families": ["income_assets"],
                "feature_ids": ["z1"],
                "allowed_specificity": "event_family",
                "independent_dependency_count": 1,
            },
        ]
    else:
        features = [evidence("b1", "bazi", "career"), evidence("z1", "ziwei", "career")]
        domains = [
            {
                "primary_domain": "career",
                "rank": 1,
                "event_families": ["formal_role"],
                "feature_ids": ["b1", "z1"],
                "allowed_specificity": "concrete_event",
                "independent_dependency_count": 2,
            },
        ]
    base = {"policy_version": "lin_tianji_rank_v1-exp", "target_scope": "yearly", "domains": domains}
    base["ranking_digest"] = digest(base)
    structural = {"target_scope": "yearly", "features": features}
    structural["interpretation_digest"] = digest(structural)
    anchor = {"status": "ok", "question_reference": "synthetic"}
    return base, structural, anchor


def test_wrapper_adds_coordination_without_rewriting_legacy_claim_packets():
    base, structural, anchor = fixtures(False)
    v1 = build_interpretation_contract(base, anchor)
    legacy = build_claim_evidence_packets(
        base_ranking=base,
        structural_interpretation=structural,
        domain_interpretation=v1["domain_interpretation"],
    )
    result = build_interpretation_contract_v2(base, anchor, structural_interpretation=structural)
    assert result["claim_evidence_packets"] == legacy["packets"]
    assert result["claim_evidence_digest"] == legacy["claim_evidence_digest"]
    assert result["coordination_relations"][0]["coordination_relation"] == "direct_domain_convergence"
    assert result["coordination_relations"][0]["legacy_cross_system_relation"] == "independent_convergence"


def test_disjoint_domain_coordination_is_parallel_but_v1_order_and_legacy_conflict_remain():
    base, structural, anchor = fixtures(True)
    v1 = build_interpretation_contract(base, anchor)
    result = build_interpretation_contract_v2(base, anchor, structural_interpretation=structural)
    assert result["primary_domains"] == v1["primary_domains"]
    assert result["secondary_domains"] == v1["secondary_domains"]
    assert {p["cross_system_relation"] for p in result["claim_evidence_packets"]} == {"conflict_or_divergence"}
    assert {r["coordination_relation"] for r in result["coordination_relations"]} == {"parallel_signals"}


def test_v2_call_keeps_repeated_v1_digest_immutable():
    base, structural, anchor = fixtures(True)
    before = build_interpretation_contract(base, anchor)
    frozen = copy.deepcopy(before)
    build_interpretation_contract_v2(base, anchor, structural_interpretation=structural)
    after = build_interpretation_contract(base, anchor)
    assert before == frozen == after


def test_reading_policy_exposes_coordination_guards():
    guards = READING_POLICY["guards"]
    assert guards["coordination_relation_is_v2_interpretation_authority"] is True
    assert guards["parallel_signals_must_not_be_rewritten_as_conflict"] is True
    assert guards["legacy_cross_system_relation_is_audit_provenance"] is True
    assert guards["coordination_must_not_raise_specificity"] is True
