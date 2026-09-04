from __future__ import annotations

import copy
import hashlib
import json
import unittest

from engine.distribution.errors import DistributionError
from engine.distribution.evidence_models import EvidenceFeature
from engine.distribution.evidence_ranker import rank_evidence
from engine.distribution.event_family_attribution import (
    EVENT_FAMILY_ATTRIBUTION_PROFILE_VERSION,
    build_event_family_attribution_bundle,
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
    scope="yearly",
    domain="career",
    families=(),
    role="target_evidence",
    maturity="stable",
    qualification="qualified",
    dependency="dep:a",
):
    return EvidenceFeature(
        feature_id=feature_id,
        system=system,
        scope=scope,
        reference_window={"label": scope},
        primary_domain=domain,
        event_family_support=tuple(families),
        strength_class="strong",
        maturity=maturity,
        qualification_status=qualification,
        source_family="synthetic",
        dependency_family=dependency,
        role=role,
        provenance={"fixture": feature_id},
    )


def structural_bundle(features, target_scope="yearly"):
    body = {
        "target_scope": target_scope,
        "features": [item.to_dict() for item in features],
    }
    body["interpretation_digest"] = canonical_digest(body)
    return body


def structural_bundle_from_rows(rows, target_scope="yearly"):
    body = {
        "target_scope": target_scope,
        "features": copy.deepcopy(rows),
    }
    body["interpretation_digest"] = canonical_digest(body)
    return body


def ranking_with_extra_candidates(ranking, domain, *families):
    result = copy.deepcopy(ranking)
    for row in result["domains"]:
        if row["primary_domain"] == domain:
            row["event_families"] = sorted(set(row["event_families"]) | set(families))
            break
    result.pop("ranking_digest", None)
    result["ranking_digest"] = canonical_digest(result)
    return result


def child_map(bundle):
    return {
        (row["primary_domain"], row["event_family"]): row
        for row in bundle["children"]
    }


class EventFamilyAttributionTests(unittest.TestCase):
    def test_profile_version_is_explicit(self):
        self.assertEqual(
            EVENT_FAMILY_ATTRIBUTION_PROFILE_VERSION,
            "lin_tianji_event_family_attribution_v1-exp",
        )

    def test_complete_structural_evidence_survives_phase3_dependency_dedup(self):
        features = [
            feature(
                "bazi-role",
                system="bazi",
                families=("role_change",),
                dependency="dep:shared",
            ),
            feature(
                "ziwei-lead",
                system="ziwei",
                families=("leadership_change",),
                dependency="dep:shared",
            ),
        ]
        ranking = rank_evidence(features, "yearly")
        self.assertEqual(len(ranking["domains"][0]["feature_ids"]), 1)

        result = build_event_family_attribution_bundle(
            base_ranking=ranking,
            structural_interpretation=structural_bundle(features),
        )
        children = child_map(result)

        self.assertTrue(children[("career", "role_change")]["child_opened"])
        self.assertTrue(children[("career", "leadership_change")]["child_opened"])
        self.assertEqual(
            children[("career", "role_change")]["bazi_target_feature_ids"],
            ["bazi-role"],
        )
        self.assertEqual(
            children[("career", "leadership_change")]["ziwei_target_feature_ids"],
            ["ziwei-lead"],
        )

    def test_only_same_scope_target_evidence_opens_child(self):
        features = [
            feature("target", system="bazi", families=("role_change",)),
            feature(
                "modifier",
                system="ziwei",
                scope="decadal",
                families=("context_only",),
                role="modifier",
            ),
            feature(
                "timing",
                system="ziwei",
                scope="monthly",
                families=("timing_only",),
                role="timing_trigger",
            ),
            feature(
                "wrong-scope-target",
                system="ziwei",
                scope="monthly",
                families=("wrong_scope",),
            ),
            feature(
                "unqualified-target",
                system="ziwei",
                families=("unqualified",),
                qualification="unqualified",
            ),
        ]
        ranking = ranking_with_extra_candidates(
            rank_evidence(features, "yearly"),
            "career",
            "context_only",
            "timing_only",
            "wrong_scope",
            "unqualified",
        )

        result = build_event_family_attribution_bundle(
            base_ranking=ranking,
            structural_interpretation=structural_bundle(features),
        )
        children = child_map(result)

        self.assertTrue(children[("career", "role_change")]["child_opened"])
        self.assertFalse(children[("career", "context_only")]["child_opened"])
        self.assertFalse(children[("career", "timing_only")]["child_opened"])
        self.assertFalse(children[("career", "wrong_scope")]["child_opened"])
        self.assertFalse(children[("career", "unqualified")]["child_opened"])
        self.assertEqual(
            children[("career", "context_only")]["modifier_feature_ids"],
            ["modifier"],
        )
        self.assertEqual(
            children[("career", "timing_only")]["timing_trigger_feature_ids"],
            ["timing"],
        )

    def test_maturity_verification_and_family_specificity_are_child_local(self):
        features = [
            feature(
                "stable-one",
                system="bazi",
                families=("role_change",),
                dependency="dep:one",
            ),
            feature(
                "verify-one",
                system="ziwei",
                families=("verification_needed",),
                qualification="needs_verification",
                dependency="dep:verify",
            ),
            feature(
                "experimental-one",
                system="ziwei",
                families=("experimental_signal",),
                maturity="experimental",
                dependency="dep:experimental",
            ),
            feature(
                "conv-a",
                system="bazi",
                families=("income_change",),
                domain="finance",
                dependency="dep:wealth",
            ),
            feature(
                "conv-b",
                system="ziwei",
                families=("income_change",),
                domain="finance",
                dependency="dep:finance-palace",
            ),
        ]
        ranking = rank_evidence(features, "yearly")
        result = build_event_family_attribution_bundle(
            base_ranking=ranking,
            structural_interpretation=structural_bundle(features),
        )
        children = child_map(result)

        self.assertEqual(
            children[("career", "role_change")]["family_specificity_ceiling"],
            "event_family",
        )
        self.assertTrue(
            children[("career", "verification_needed")]["required_verification_caveat"]
        )
        self.assertEqual(
            children[("career", "experimental_signal")]["family_specificity_ceiling"],
            "event_family",
        )
        self.assertEqual(
            children[("finance", "income_change")]["family_specificity_ceiling"],
            "concrete_event",
        )

    def test_phase3_candidate_without_direct_target_support_is_preserved_for_audit(self):
        features = [
            feature("target", system="bazi", families=("role_change",)),
            feature(
                "modifier",
                system="ziwei",
                scope="decadal",
                families=("context_only",),
                role="modifier",
            ),
        ]
        ranking = ranking_with_extra_candidates(
            rank_evidence(features, "yearly"),
            "career",
            "context_only",
        )
        result = build_event_family_attribution_bundle(
            base_ranking=ranking,
            structural_interpretation=structural_bundle(features),
        )
        row = child_map(result)[("career", "context_only")]

        self.assertFalse(row["child_opened"])
        self.assertIsNone(row["family_specificity_ceiling"])
        self.assertEqual(row["candidate_source"], "phase3")
        self.assertEqual(row["modifier_feature_ids"], ["modifier"])

    def test_same_validated_source_identity_is_byte_deterministic_and_inputs_are_not_mutated(self):
        features = [
            feature("a", system="bazi", families=("role_change",), dependency="dep:a"),
            feature("b", system="ziwei", families=("role_change",), dependency="dep:b"),
        ]
        ranking = rank_evidence(features, "yearly")
        structural = structural_bundle(features)
        ranking_before = copy.deepcopy(ranking)
        structural_before = copy.deepcopy(structural)

        first = build_event_family_attribution_bundle(
            base_ranking=ranking,
            structural_interpretation=structural,
        )
        second = build_event_family_attribution_bundle(
            base_ranking=ranking,
            structural_interpretation=structural,
        )

        self.assertEqual(first, second)
        self.assertEqual(ranking, ranking_before)
        self.assertEqual(structural, structural_before)
        self.assertEqual(
            first["children"][0]["direct_target_dependency_families"],
            ["dep:a", "dep:b"],
        )
        self.assertEqual(first["children"][0]["direct_target_systems"], ["bazi", "ziwei"])

    def test_source_identity_changes_are_preserved_while_child_membership_is_canonical(self):
        features = [
            feature("a", system="bazi", families=("role_change",), dependency="dep:a"),
            feature("b", system="ziwei", families=("role_change",), dependency="dep:b"),
        ]
        first_ranking = rank_evidence(features, "yearly")
        first_structural = structural_bundle(features)
        second_ranking = rank_evidence(list(reversed(features)), "yearly")
        second_structural = structural_bundle(list(reversed(features)))

        first = build_event_family_attribution_bundle(
            base_ranking=first_ranking,
            structural_interpretation=first_structural,
        )
        second = build_event_family_attribution_bundle(
            base_ranking=second_ranking,
            structural_interpretation=second_structural,
        )

        self.assertEqual(
            [
                (row["primary_domain"], row["event_family"], row["direct_target_dependency_families"])
                for row in first["children"]
            ],
            [
                (row["primary_domain"], row["event_family"], row["direct_target_dependency_families"])
                for row in second["children"]
            ],
        )
        self.assertEqual(first["base_ranking_digest"], first_ranking["ranking_digest"])
        self.assertEqual(second["base_ranking_digest"], second_ranking["ranking_digest"])
        self.assertEqual(
            first["structural_interpretation_digest"],
            first_structural["interpretation_digest"],
        )
        self.assertEqual(
            second["structural_interpretation_digest"],
            second_structural["interpretation_digest"],
        )

    def test_fail_closed_on_source_digest_scope_duplicate_candidate_and_invalid_feature(self):
        valid = [feature("target", system="bazi", families=("role_change",))]
        ranking = rank_evidence(valid, "yearly")
        structural = structural_bundle(valid)

        bad_ranking = copy.deepcopy(ranking)
        bad_ranking["domains"][0]["rank"] = 99
        with self.assertRaises(DistributionError):
            build_event_family_attribution_bundle(
                base_ranking=bad_ranking,
                structural_interpretation=structural,
            )

        bad_structural = copy.deepcopy(structural)
        bad_structural["features"][0]["strength_class"] = "weak"
        with self.assertRaises(DistributionError):
            build_event_family_attribution_bundle(
                base_ranking=ranking,
                structural_interpretation=bad_structural,
            )

        wrong_scope = structural_bundle(valid, target_scope="monthly")
        with self.assertRaises(DistributionError):
            build_event_family_attribution_bundle(
                base_ranking=ranking,
                structural_interpretation=wrong_scope,
            )

        duplicate_candidate = copy.deepcopy(ranking)
        duplicate_candidate["domains"][0]["event_families"].append("role_change")
        duplicate_candidate.pop("ranking_digest", None)
        duplicate_candidate["ranking_digest"] = canonical_digest(duplicate_candidate)
        with self.assertRaises(DistributionError):
            build_event_family_attribution_bundle(
                base_ranking=duplicate_candidate,
                structural_interpretation=structural,
            )

        invalid_row = valid[0].to_dict()
        invalid_row["system"] = "invalid-system"
        invalid_structural = structural_bundle_from_rows([invalid_row])
        with self.assertRaises(DistributionError):
            build_event_family_attribution_bundle(
                base_ranking=ranking,
                structural_interpretation=invalid_structural,
            )


if __name__ == "__main__":
    unittest.main()
