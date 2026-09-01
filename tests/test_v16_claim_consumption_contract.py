import copy
import hashlib
import json

import pytest

from engine.distribution.claim_consumption_contract import (
    CLAIM_CONSUMPTION_PROFILE_VERSION,
    build_claim_consumption_bundle,
)


CLAIM_PROFILE = "lin_tianji_claim_evidence_v1-exp"
COORDINATION_PROFILE = "lin_tianji_coordination_v1-exp"
TARGET_SCOPE = "yearly"
RANKING_DIGEST = "a" * 64
STRUCTURAL_DIGEST = "b" * 64


def canonical_digest(value):
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def evidence(system, feature_id, *, role="target_evidence", scope=TARGET_SCOPE, dependency=None):
    return {
        "feature_id": feature_id,
        "system": system,
        "scope": scope,
        "role": role,
        "strength_class": "strong",
        "maturity": "stable",
        "qualification_status": "qualified",
        "source_family": f"synthetic.{system}",
        "dependency_family": dependency or f"dep:{feature_id}",
        "provenance": {"fixture": True, "feature": feature_id},
    }


def packet(
    domain,
    *,
    bazi=(),
    ziwei=(),
    legacy=None,
    effective="event_family",
    confidence="moderate_confidence",
    abstentions=(),
):
    rows = list(bazi) + list(ziwei)
    return {
        "claim_id": f"claim:{TARGET_SCOPE}:{domain}",
        "primary_domain": domain,
        "event_family_candidates": ["synthetic_family"],
        "time_scope": TARGET_SCOPE,
        "bazi_evidence": list(bazi),
        "ziwei_evidence": list(ziwei),
        "source_layers": sorted({row["scope"] for row in rows}),
        "independent_support_count": len({row["dependency_family"] for row in rows}),
        "cross_system_relation": legacy,
        "conflicts": (
            [{"reason": "synthetic_legacy_conflict"}]
            if legacy == "conflict_or_divergence"
            else []
        ),
        "assumptions": [],
        "base_allowed_specificity": effective,
        "effective_specificity": effective,
        "abstention_status": list(abstentions),
        "confidence_class": confidence,
        "reasoning_chain": {
            "phase3_ranking_digest": RANKING_DIGEST,
            "structural_interpretation_digest": STRUCTURAL_DIGEST,
            "selected_feature_ids": [row["feature_id"] for row in rows],
            "specificity_authority": "phase3_with_existing_local_window_cap",
        },
    }


def claim_bundle(packets):
    result = {
        "profile_version": CLAIM_PROFILE,
        "target_scope": TARGET_SCOPE,
        "base_ranking_digest": RANKING_DIGEST,
        "structural_interpretation_digest": STRUCTURAL_DIGEST,
        "packets": list(packets),
        "global_conflicts": [],
    }
    result["claim_evidence_digest"] = canonical_digest(result)
    return result


def coordination_row(
    domain,
    relation,
    *,
    cap="event_family",
    support_count=1,
    systems=("bazi",),
    legacy=None,
    parallel_domains=(),
):
    return {
        "primary_domain": domain,
        "legacy_cross_system_relation": legacy,
        "coordination_relation": relation,
        "dependency_independence_class": (
            "multiple_independent_dependencies" if support_count > 1 else "single_dependency"
        ),
        "independent_dependency_count": max(support_count, 1),
        "system_support_count": support_count,
        "same_scope_target_systems": list(systems),
        "parallel_domains": list(parallel_domains),
        "conflict_evidence_status": "unavailable",
        "coordination_specificity_cap": cap,
    }


def coordination_bundle(relations, *, ranking_digest=RANKING_DIGEST, structural_digest=STRUCTURAL_DIGEST):
    result = {
        "policy_version": COORDINATION_PROFILE,
        "target_scope": TARGET_SCOPE,
        "relations": list(relations),
        "source_ranking_digest": ranking_digest,
        "source_interpretation_digest": structural_digest,
    }
    result["coordination_digest"] = canonical_digest(result)
    return result


def build(packets, relations):
    return build_claim_consumption_bundle(
        claim_evidence_bundle=claim_bundle(packets),
        coordination_bundle=coordination_bundle(relations),
    )


def test_direct_same_domain_convergence_can_render_without_extra_caveat():
    p = packet(
        "career",
        bazi=[evidence("bazi", "b1")],
        ziwei=[evidence("ziwei", "z1")],
        legacy="independent_convergence",
        effective="concrete_event",
        confidence="high_confidence",
    )
    r = coordination_row(
        "career",
        "direct_domain_convergence",
        cap="concrete_event",
        support_count=2,
        systems=("bazi", "ziwei"),
        legacy="independent_convergence",
    )
    result = build([p], [r])
    decision = result["decisions"][0]
    assert result["profile_version"] == CLAIM_CONSUMPTION_PROFILE_VERSION
    assert result["claim_consumption_digest"]
    assert decision["decision"] == "render"
    assert decision["authorized_specificity"] == "concrete_event"
    assert decision["reason_codes"] == []


def test_layered_complement_is_rendered_with_caveat_without_creating_target_claim():
    p = packet(
        "career",
        bazi=[evidence("bazi", "b1")],
        ziwei=[evidence("ziwei", "z1", role="modifier", scope="decadal")],
        legacy="layered_complement",
    )
    r = coordination_row(
        "career",
        "layered_complement",
        support_count=1,
        systems=("bazi",),
        legacy="layered_complement",
    )
    decision = build([p], [r])["decisions"][0]
    assert decision["claim_id"] == "claim:yearly:career"
    assert decision["decision"] == "render_with_caveat"
    assert decision["reason_codes"] == ["layered_complement"]


def test_disjoint_domains_remain_parallel_and_independently_consumable():
    packets = [
        packet(
            "career",
            bazi=[evidence("bazi", "b-car")],
            legacy="conflict_or_divergence",
        ),
        packet(
            "finance",
            ziwei=[evidence("ziwei", "z-fin")],
            legacy="conflict_or_divergence",
        ),
    ]
    relations = [
        coordination_row(
            "career",
            "parallel_signals",
            systems=("bazi",),
            legacy="conflict_or_divergence",
            parallel_domains=("career", "finance"),
        ),
        coordination_row(
            "finance",
            "parallel_signals",
            systems=("ziwei",),
            legacy="conflict_or_divergence",
            parallel_domains=("career", "finance"),
        ),
    ]
    result = build(packets, relations)
    assert {row["primary_domain"] for row in result["decisions"]} == {"career", "finance"}
    assert {row["coordination_relation"] for row in result["decisions"]} == {"parallel_signals"}
    assert {row["decision"] for row in result["decisions"]} == {"render_with_caveat"}
    assert {tuple(row["reason_codes"]) for row in result["decisions"]} == {("parallel_signals",)}


def test_single_system_support_is_caveated_without_inventing_cross_system_support():
    p = packet("career", bazi=[evidence("bazi", "b1")])
    r = coordination_row("career", "single_system_support", systems=("bazi",))
    decision = build([p], [r])["decisions"][0]
    assert decision["coordination_relation"] == "single_system_support"
    assert decision["decision"] == "render_with_caveat"
    assert decision["reason_codes"] == ["single_system_support"]


def test_tampered_claim_bundle_digest_fails_closed():
    p = packet("career", bazi=[evidence("bazi", "b1")])
    r = coordination_row("career", "single_system_support")
    claims = claim_bundle([p])
    claims["packets"][0]["confidence_class"] = "low_confidence"
    with pytest.raises(ValueError):
        build_claim_consumption_bundle(
            claim_evidence_bundle=claims,
            coordination_bundle=coordination_bundle([r]),
        )


def test_valid_source_bundles_with_mismatched_ranking_provenance_fail_closed():
    p = packet("career", bazi=[evidence("bazi", "b1")])
    r = coordination_row("career", "single_system_support")
    with pytest.raises(ValueError):
        build_claim_consumption_bundle(
            claim_evidence_bundle=claim_bundle([p]),
            coordination_bundle=coordination_bundle([r], ranking_digest="c" * 64),
        )


def test_coordination_cap_can_only_downgrade_authorized_specificity():
    p = packet(
        "career",
        bazi=[evidence("bazi", "b1")],
        ziwei=[evidence("ziwei", "z1")],
        legacy="independent_convergence",
        effective="concrete_event",
        confidence="high_confidence",
    )
    r = coordination_row(
        "career",
        "direct_domain_convergence",
        cap="event_family",
        support_count=2,
        systems=("bazi", "ziwei"),
        legacy="independent_convergence",
    )
    decision = build([p], [r])["decisions"][0]
    assert decision["original_effective_specificity"] == "concrete_event"
    assert decision["authorized_specificity"] == "event_family"
    assert decision["decision"] == "render_with_caveat"
    assert decision["reason_codes"] == ["specificity_downgraded"]


def test_coordination_cap_more_permissive_than_packet_authority_fails_closed():
    p = packet("career", bazi=[evidence("bazi", "b1")], effective="event_family")
    r = coordination_row(
        "career",
        "single_system_support",
        cap="concrete_event",
        systems=("bazi",),
    )
    with pytest.raises(ValueError):
        build([p], [r])


def test_same_source_bundles_are_deterministic_and_decisions_use_canonical_domain_order():
    packets = [
        packet("finance", ziwei=[evidence("ziwei", "z-fin")]),
        packet("career", bazi=[evidence("bazi", "b-car")]),
    ]
    relations = [
        coordination_row("finance", "parallel_signals", systems=("ziwei",), parallel_domains=("career", "finance")),
        coordination_row("career", "parallel_signals", systems=("bazi",), parallel_domains=("career", "finance")),
    ]
    claims = claim_bundle(packets)
    coordination = coordination_bundle(relations)
    first = build_claim_consumption_bundle(
        claim_evidence_bundle=claims,
        coordination_bundle=coordination,
    )
    second = build_claim_consumption_bundle(
        claim_evidence_bundle=claims,
        coordination_bundle=coordination,
    )
    assert first == second
    assert first["claim_consumption_digest"] == second["claim_consumption_digest"]
    assert [row["primary_domain"] for row in first["decisions"]] == ["career", "finance"]


def test_legacy_conflict_never_overrides_python_parallel_authority():
    p = packet(
        "career",
        bazi=[evidence("bazi", "b-car")],
        legacy="conflict_or_divergence",
    )
    r = coordination_row(
        "career",
        "parallel_signals",
        systems=("bazi",),
        legacy="conflict_or_divergence",
        parallel_domains=("career", "finance"),
    )
    decision = build([p], [r])["decisions"][0]
    assert decision["coordination_relation"] == "parallel_signals"
    assert decision["decision"] == "render_with_caveat"
    assert "parallel_signals" in decision["reason_codes"]


def test_builder_does_not_mutate_source_bundles():
    p = packet("career", bazi=[evidence("bazi", "b1")])
    r = coordination_row("career", "single_system_support", systems=("bazi",))
    claims = claim_bundle([p])
    coordination = coordination_bundle([r])
    frozen_claims = copy.deepcopy(claims)
    frozen_coordination = copy.deepcopy(coordination)
    build_claim_consumption_bundle(
        claim_evidence_bundle=claims,
        coordination_bundle=coordination,
    )
    assert claims == frozen_claims
    assert coordination == frozen_coordination


def test_zero_same_scope_target_support_abstains_claim():
    p = packet(
        "career",
        ziwei=[evidence("ziwei", "z-background", role="modifier", scope="decadal")],
    )
    r = coordination_row(
        "career",
        "single_system_support",
        support_count=0,
        systems=(),
    )
    decision = build([p], [r])["decisions"][0]
    assert decision["decision"] == "abstain_claim"
    assert decision["reason_codes"] == ["no_same_scope_target_support"]
