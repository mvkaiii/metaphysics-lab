from __future__ import annotations

import copy
import hashlib
import json
import unittest

from engine.distribution.claim_evidence import build_claim_evidence_packets
from engine.distribution.evidence_models import EvidenceFeature
from engine.distribution.evidence_ranker import rank_evidence
from engine.distribution.event_family_attribution import build_event_family_attribution_bundle
from engine.distribution.hierarchical_claim_authority import (
    C2_REASON_ORDER,
    HIERARCHICAL_CLAIM_AUTHORITY_PROFILE_VERSION,
    build_hierarchical_claim_authority_bundle,
)


def canonical_digest(value):
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def feature(
    feature_id,
    *,
    system,
    family,
    role="target_evidence",
    scope="yearly",
    maturity="stable",
    qualification="qualified",
    dependency="dep:a",
):
    return EvidenceFeature(
        feature_id=feature_id,
        system=system,
        scope=scope,
        reference_window={"label": scope},
        primary_domain="career",
        event_family_support=(family,),
        strength_class="strong",
        maturity=maturity,
        qualification_status=qualification,
        source_family="synthetic",
        dependency_family=dependency,
        role=role,
        provenance={"fixture": feature_id},
    )


def structural_bundle(features):
    body = {
        "target_scope": "yearly",
        "features": [item.to_dict() for item in features],
    }
    body["interpretation_digest"] = canonical_digest(body)
    return body


def ranking_with_extra_candidates(ranking, *families):
    result = copy.deepcopy(ranking)
    result["domains"][0]["event_families"] = sorted(
        set(result["domains"][0]["event_families"]) | set(families)
    )
    result.pop("ranking_digest", None)
    result["ranking_digest"] = canonical_digest(result)
    return result


def domain_interpretation_from_ranking(ranking):
    return [
        {
            "primary_domain": row["primary_domain"],
            "event_family_candidates": list(row["event_families"]),
            "effective_specificity": row["allowed_specificity"],
            "base_allowed_specificity": row["allowed_specificity"],
            "evidence_explanation_classes": [],
        }
        for row in ranking["domains"]
    ]


def c1_bundle(
    claim_evidence,
    *,
    decision="render",
    authorized_specificity="concrete_event",
    reason_codes=(),
):
    packet = claim_evidence["packets"][0]
    body = {
        "profile_version": "lin_tianji_claim_consumption_v1-exp",
        "claim_evidence_digest": claim_evidence["claim_evidence_digest"],
        "coordination_digest": "0" * 64,
        "target_scope": claim_evidence["target_scope"],
        "decisions": [
            {
                "claim_id": packet["claim_id"],
                "primary_domain": packet["primary_domain"],
                "decision": decision,
                "original_effective_specificity": authorized_specificity,
                "authorized_specificity": authorized_specificity,
                "confidence_class": "moderate_confidence",
                "coordination_relation": "direct_domain_convergence",
                "reason_codes": list(reason_codes),
            }
        ],
    }
    body["claim_consumption_digest"] = canonical_digest(body)
    return body


def sources(
    features,
    *,
    extra_families=(),
    parent_decision="render",
    parent_specificity="concrete_event",
    parent_reasons=(),
):
    ranking = rank_evidence(features, "yearly")
    if extra_families:
        ranking = ranking_with_extra_candidates(ranking, *extra_families)
    structural = structural_bundle(features)
    claim_evidence = build_claim_evidence_packets(
        base_ranking=ranking,
        structural_interpretation=structural,
        domain_interpretation=domain_interpretation_from_ranking(ranking),
    )
    efa = build_event_family_attribution_bundle(
        base_ranking=ranking,
        structural_interpretation=structural,
    )
    c1 = c1_bundle(
        claim_evidence,
        decision=parent_decision,
        authorized_specificity=parent_specificity,
        reason_codes=parent_reasons,
    )
    return claim_evidence, efa, c1


def decision_by_family(bundle, family):
    return next(row for row in bundle["decisions"] if row["event_family"] == family)


def build_c2(claim_evidence, efa, c1):
    return build_hierarchical_claim_authority_bundle(
        claim_consumption_bundle=c1,
        event_family_attribution_bundle=efa,
        claim_evidence_bundle=claim_evidence,
    )


class HierarchicalClaimAuthorityTests(unittest.TestCase):
    def test_profile_and_reason_order_are_frozen(self):
        self.assertEqual(
            HIERARCHICAL_CLAIM_AUTHORITY_PROFILE_VERSION,
            "lin_tianji_hierarchical_claim_authority_v1-exp",
        )
        self.assertEqual(
            C2_REASON_ORDER,
            (
                "parent_requires_caveat",
                "single_system_support",
                "needs_verification",
                "experimental_only",
                "specificity_downgraded",
            ),
        )

    def test_parent_abstain_fails_closed_for_every_child(self):
        features = [
            feature("target", system="bazi", family="role_change"),
            feature(
                "modifier",
                system="ziwei",
                family="context_only",
                role="modifier",
                scope="decadal",
                dependency="dep:context",
            ),
        ]
        claim_evidence, efa, c1 = sources(
            features,
            extra_families=("context_only",),
            parent_decision="abstain_claim",
            parent_specificity="event_family",
        )
        result = build_c2(claim_evidence, efa, c1)

        self.assertEqual(
            {row["decision"] for row in result["decisions"]},
            {"abstain_child"},
        )
        self.assertTrue(
            all(row["reason_codes"] == ["parent_abstained"] for row in result["decisions"])
        )
        self.assertTrue(all(row["authorized_specificity"] is None for row in result["decisions"]))

    def test_child_without_direct_target_support_abstains_for_child_only(self):
        features = [
            feature("target", system="bazi", family="role_change"),
            feature(
                "modifier",
                system="ziwei",
                family="context_only",
                role="modifier",
                scope="decadal",
                dependency="dep:context",
            ),
        ]
        claim_evidence, efa, c1 = sources(
            features,
            extra_families=("context_only",),
            parent_specificity="event_family",
        )
        result = build_c2(claim_evidence, efa, c1)
        row = decision_by_family(result, "context_only")

        self.assertEqual(row["decision"], "abstain_child")
        self.assertEqual(row["reason_codes"], ["no_direct_target_support"])
        self.assertIsNone(row["authorized_specificity"])

    def test_parent_domain_specificity_blocks_event_family_rendering(self):
        features = [feature("target", system="bazi", family="role_change")]
        claim_evidence, efa, c1 = sources(
            features,
            parent_specificity="domain",
        )
        row = decision_by_family(build_c2(claim_evidence, efa, c1), "role_change")

        self.assertEqual(row["decision"], "abstain_child")
        self.assertEqual(row["reason_codes"], ["parent_specificity_below_event_family"])
        self.assertIsNone(row["authorized_specificity"])

    def test_specificity_is_capped_by_parent_and_requires_caveat(self):
        features = [
            feature(
                "bazi",
                system="bazi",
                family="role_change",
                dependency="dep:bazi",
            ),
            feature(
                "ziwei",
                system="ziwei",
                family="role_change",
                dependency="dep:ziwei",
            ),
        ]
        claim_evidence, efa, c1 = sources(
            features,
            parent_specificity="event_family",
        )
        row = decision_by_family(build_c2(claim_evidence, efa, c1), "role_change")

        self.assertEqual(row["family_specificity_ceiling"], "concrete_event")
        self.assertEqual(row["authorized_specificity"], "event_family")
        self.assertEqual(row["decision"], "render_with_caveat")
        self.assertEqual(row["reason_codes"], ["specificity_downgraded"])

    def test_parent_caveat_propagates(self):
        features = [
            feature("b", system="bazi", family="role_change", dependency="dep:b"),
            feature("z", system="ziwei", family="role_change", dependency="dep:z"),
        ]
        claim_evidence, efa, c1 = sources(
            features,
            parent_decision="render_with_caveat",
            parent_specificity="concrete_event",
            parent_reasons=("existing_abstention",),
        )
        row = decision_by_family(build_c2(claim_evidence, efa, c1), "role_change")
        self.assertEqual(row["decision"], "render_with_caveat")
        self.assertEqual(row["reason_codes"], ["parent_requires_caveat"])

    def test_needs_verification_requires_caveat(self):
        features = [
            feature(
                "b",
                system="bazi",
                family="role_change",
                qualification="needs_verification",
                dependency="dep:b",
            ),
            feature("z", system="ziwei", family="role_change", dependency="dep:z"),
        ]
        claim_evidence, efa, c1 = sources(features, parent_specificity="concrete_event")
        row = decision_by_family(build_c2(claim_evidence, efa, c1), "role_change")
        self.assertEqual(row["decision"], "render_with_caveat")
        self.assertEqual(row["reason_codes"], ["needs_verification"])

    def test_experimental_only_requires_caveat_without_specificity_upgrade(self):
        features = [
            feature(
                "b",
                system="bazi",
                family="role_change",
                maturity="experimental",
                dependency="dep:b",
            ),
            feature(
                "z",
                system="ziwei",
                family="role_change",
                maturity="experimental",
                dependency="dep:z",
            ),
        ]
        claim_evidence, efa, c1 = sources(features, parent_specificity="event_family")
        row = decision_by_family(build_c2(claim_evidence, efa, c1), "role_change")
        self.assertEqual(row["family_specificity_ceiling"], "event_family")
        self.assertEqual(row["authorized_specificity"], "event_family")
        self.assertEqual(row["decision"], "render_with_caveat")
        self.assertEqual(row["reason_codes"], ["experimental_only"])

    def test_single_direct_system_remains_renderable_with_caveat(self):
        features = [feature("b", system="bazi", family="role_change")]
        claim_evidence, efa, c1 = sources(features, parent_specificity="event_family")
        row = decision_by_family(build_c2(claim_evidence, efa, c1), "role_change")
        self.assertEqual(row["decision"], "render_with_caveat")
        self.assertEqual(row["source_systems"], ["bazi"])
        self.assertEqual(row["reason_codes"], ["single_system_support"])

    def test_clean_two_system_direct_child_renders_without_caveat(self):
        features = [
            feature("b", system="bazi", family="role_change", dependency="dep:b"),
            feature("z", system="ziwei", family="role_change", dependency="dep:z"),
        ]
        claim_evidence, efa, c1 = sources(features, parent_specificity="concrete_event")
        row = decision_by_family(build_c2(claim_evidence, efa, c1), "role_change")
        self.assertEqual(row["decision"], "render")
        self.assertEqual(row["authorized_specificity"], "concrete_event")
        self.assertEqual(row["source_systems"], ["bazi", "ziwei"])
        self.assertEqual(row["reason_codes"], [])

    def test_reason_codes_follow_frozen_order(self):
        features = [
            feature(
                "b",
                system="bazi",
                family="role_change",
                maturity="experimental",
                qualification="needs_verification",
            )
        ]
        claim_evidence, efa, c1 = sources(
            features,
            parent_decision="render_with_caveat",
            parent_specificity="concrete_event",
        )
        row = decision_by_family(build_c2(claim_evidence, efa, c1), "role_change")
        self.assertEqual(
            row["reason_codes"],
            [
                "parent_requires_caveat",
                "single_system_support",
                "needs_verification",
                "experimental_only",
            ],
        )

    def test_claim_evidence_identity_bridge_fails_closed_on_c1_source_mismatch(self):
        features = [feature("b", system="bazi", family="role_change")]
        claim_evidence, efa, c1 = sources(features, parent_specificity="event_family")
        bad = copy.deepcopy(c1)
        bad["claim_evidence_digest"] = "f" * 64
        bad.pop("claim_consumption_digest", None)
        bad["claim_consumption_digest"] = canonical_digest(bad)
        with self.assertRaises(ValueError):
            build_c2(claim_evidence, efa, bad)

    def test_claim_evidence_identity_bridge_fails_closed_on_efa_ranking_mismatch(self):
        features = [feature("b", system="bazi", family="role_change")]
        claim_evidence, efa, c1 = sources(features, parent_specificity="event_family")
        bad = copy.deepcopy(efa)
        bad["base_ranking_digest"] = "e" * 64
        bad.pop("event_family_attribution_digest", None)
        bad["event_family_attribution_digest"] = canonical_digest(bad)
        with self.assertRaises(ValueError):
            build_c2(claim_evidence, bad, c1)

    def test_parent_child_identity_and_scope_mismatch_fail_closed(self):
        features = [feature("b", system="bazi", family="role_change")]
        claim_evidence, efa, c1 = sources(features, parent_specificity="event_family")

        bad_parent = copy.deepcopy(efa)
        bad_parent["children"][0]["parent_claim_id"] = "claim:yearly:other"
        bad_parent.pop("event_family_attribution_digest", None)
        bad_parent["event_family_attribution_digest"] = canonical_digest(bad_parent)
        with self.assertRaises(ValueError):
            build_c2(claim_evidence, bad_parent, c1)

        bad_scope = copy.deepcopy(efa)
        bad_scope["target_scope"] = "monthly"
        bad_scope.pop("event_family_attribution_digest", None)
        bad_scope["event_family_attribution_digest"] = canonical_digest(bad_scope)
        with self.assertRaises(ValueError):
            build_c2(claim_evidence, bad_scope, c1)


if __name__ == "__main__":
    unittest.main()
