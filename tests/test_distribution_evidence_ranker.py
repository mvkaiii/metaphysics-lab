import json
import unittest

from engine.distribution.evidence_policy import (
    EXPERIMENTAL_FACTOR_DEN,
    EXPERIMENTAL_FACTOR_NUM,
    INDEPENDENT_CONVERGENCE_BONUS,
    MODIFIER_CAP,
    POLICY_VERSION,
    ROLE_CONTRIBUTION_ORDER,
    SPECIFICITY_LEVELS,
    STABLE_FACTOR_DEN,
    STABLE_FACTOR_NUM,
    TARGET_SCOPE_BASE,
    TIMING_TRIGGER_CAP,
)
from engine.distribution.evidence_ranker import (
    detect_local_spike,
    evaluate_feature_eligibility,
    rank_evidence,
)


class EvidencePolicyProfileTests(unittest.TestCase):
    def test_policy_version_and_specificity_levels_are_frozen(self):
        self.assertEqual(POLICY_VERSION, "lin_tianji_rank_v1-exp")
        self.assertEqual(
            SPECIFICITY_LEVELS,
            ("domain", "event_family", "concrete_event", "highly_specific_event"),
        )
        self.assertEqual(
            ROLE_CONTRIBUTION_ORDER,
            ("target_evidence", "modifier", "timing_trigger"),
        )

    def test_initial_ordinal_policy_constants_match_approved_profile(self):
        self.assertEqual(TARGET_SCOPE_BASE, 4)
        self.assertEqual(INDEPENDENT_CONVERGENCE_BONUS, 2)
        self.assertEqual(MODIFIER_CAP, 1)
        self.assertEqual(TIMING_TRIGGER_CAP, 1)
        self.assertEqual((STABLE_FACTOR_NUM, STABLE_FACTOR_DEN), (2, 2))
        self.assertEqual((EXPERIMENTAL_FACTOR_NUM, EXPERIMENTAL_FACTOR_DEN), (1, 2))

    def test_policy_profile_contains_no_probability_semantics(self):
        exported_names = {
            name.lower()
            for name in (
                "POLICY_VERSION",
                "SPECIFICITY_LEVELS",
                "ROLE_CONTRIBUTION_ORDER",
                "TARGET_SCOPE_BASE",
                "INDEPENDENT_CONVERGENCE_BONUS",
                "MODIFIER_CAP",
                "TIMING_TRIGGER_CAP",
                "STABLE_FACTOR_NUM",
                "STABLE_FACTOR_DEN",
                "EXPERIMENTAL_FACTOR_NUM",
                "EXPERIMENTAL_FACTOR_DEN",
            )
        }
        for forbidden in ("probability", "likelihood", "chance", "percent"):
            self.assertFalse(any(forbidden in name for name in exported_names))


class EvidenceRankerTests(unittest.TestCase):
    def feature(self, feature_id, **overrides):
        payload = {
            "feature_id": feature_id,
            "system": "bazi",
            "scope": "yearly",
            "reference_window": {"scope": "yearly", "reference": "fixture"},
            "primary_domain": "career",
            "event_family_support": ["formal_role"],
            "strength_class": "moderate",
            "maturity": "stable",
            "qualification_status": "qualified",
            "source_family": "fixture.bazi",
            "dependency_family": "dep:" + feature_id,
            "role": "target_evidence",
            "provenance": {"fixture": feature_id},
        }
        payload.update(overrides)
        return payload

    @staticmethod
    def canonical_bytes(value):
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")

    def test_eligibility_distinguishes_target_modifier_and_unqualified(self):
        target = evaluate_feature_eligibility(
            self.feature("target"),
            target_scope="yearly",
        )
        modifier = evaluate_feature_eligibility(
            self.feature(
                "modifier",
                scope="decadal",
                reference_window={"scope": "decadal"},
                role="modifier",
            ),
            target_scope="yearly",
        )
        unqualified = evaluate_feature_eligibility(
            self.feature("unqualified", qualification_status="unqualified"),
            target_scope="yearly",
        )

        self.assertTrue(target["eligible"])
        self.assertTrue(target["can_open_domain"])
        self.assertGreater(target["ordinal_contribution_scaled"], 0)
        self.assertTrue(modifier["eligible"])
        self.assertFalse(modifier["can_open_domain"])
        self.assertGreater(modifier["ordinal_contribution_scaled"], 0)
        self.assertFalse(unqualified["eligible"])
        self.assertEqual(unqualified["reason"], "unqualified")
        self.assertEqual(unqualified["ordinal_contribution_scaled"], 0)

    def test_stronger_target_evidence_cannot_rank_below_weaker_peer(self):
        result = rank_evidence(
            [
                self.feature(
                    "weak-career",
                    primary_domain="career",
                    strength_class="weak",
                    dependency_family="dep:career",
                ),
                self.feature(
                    "strong-finance",
                    primary_domain="finance",
                    event_family_support=["earned_income"],
                    strength_class="strong",
                    dependency_family="dep:finance",
                ),
            ],
            target_scope="yearly",
        )

        self.assertEqual(
            [item["primary_domain"] for item in result["domains"]],
            ["finance", "career"],
        )
        self.assertGreaterEqual(
            result["domains"][0]["ordinal_score_scaled"],
            result["domains"][1]["ordinal_score_scaled"],
        )

    def test_modifier_cannot_open_domain_without_target_scope_ownership(self):
        result = rank_evidence(
            [
                self.feature(
                    "year-career",
                    primary_domain="career",
                    strength_class="weak",
                    dependency_family="dep:year-career",
                ),
                self.feature(
                    "decade-finance",
                    scope="decadal",
                    reference_window={"scope": "decadal"},
                    primary_domain="finance",
                    event_family_support=["income_assets"],
                    strength_class="strong",
                    dependency_family="dep:decade-finance",
                    role="modifier",
                ),
            ],
            target_scope="yearly",
        )

        self.assertEqual(
            [item["primary_domain"] for item in result["domains"]],
            ["career"],
        )
        self.assertNotIn("finance", result["opened_domains"])

    def test_same_dependency_family_does_not_stack_as_independent_votes(self):
        shared = rank_evidence(
            [
                self.feature("shared-a", dependency_family="dep:shared"),
                self.feature(
                    "shared-b",
                    system="ziwei",
                    source_family="fixture.ziwei",
                    dependency_family="dep:shared",
                ),
            ],
            target_scope="yearly",
        )
        independent = rank_evidence(
            [
                self.feature("independent-a", dependency_family="dep:a"),
                self.feature(
                    "independent-b",
                    system="ziwei",
                    source_family="fixture.ziwei",
                    dependency_family="dep:b",
                ),
            ],
            target_scope="yearly",
        )

        shared_domain = shared["domains"][0]
        independent_domain = independent["domains"][0]
        self.assertEqual(shared_domain["independent_dependency_count"], 1)
        self.assertEqual(independent_domain["independent_dependency_count"], 2)
        self.assertGreater(
            independent_domain["ordinal_score_scaled"],
            shared_domain["ordinal_score_scaled"],
        )

    def test_cross_system_convergence_raises_rank_without_bypassing_ownership(self):
        single = rank_evidence(
            [self.feature("bazi-career", dependency_family="dep:bazi")],
            target_scope="yearly",
        )
        converged = rank_evidence(
            [
                self.feature("bazi-career", dependency_family="dep:bazi"),
                self.feature(
                    "ziwei-career",
                    system="ziwei",
                    source_family="fixture.ziwei",
                    dependency_family="dep:ziwei",
                ),
                self.feature(
                    "decade-finance",
                    scope="decadal",
                    reference_window={"scope": "decadal"},
                    primary_domain="finance",
                    event_family_support=["income_assets"],
                    system="ziwei",
                    source_family="fixture.ziwei",
                    dependency_family="dep:decade-finance",
                    role="modifier",
                ),
            ],
            target_scope="yearly",
        )

        self.assertGreater(
            converged["domains"][0]["ordinal_score_scaled"],
            single["domains"][0]["ordinal_score_scaled"],
        )
        self.assertEqual(converged["domains"][0]["system_count"], 2)
        self.assertEqual(converged["opened_domains"], ["career"])

    def test_experimental_only_target_is_capped_at_event_family_specificity(self):
        result = rank_evidence(
            [
                self.feature(
                    "experimental-a",
                    maturity="experimental",
                    dependency_family="dep:a",
                ),
                self.feature(
                    "experimental-b",
                    system="ziwei",
                    source_family="fixture.ziwei",
                    maturity="experimental",
                    dependency_family="dep:b",
                ),
            ],
            target_scope="yearly",
        )

        domain = result["domains"][0]
        self.assertEqual(domain["allowed_specificity"], "event_family")
        self.assertNotIn(
            domain["allowed_specificity"],
            ("concrete_event", "highly_specific_event"),
        )

    def test_stable_independent_target_convergence_can_reach_concrete_event(self):
        result = rank_evidence(
            [
                self.feature("stable-a", dependency_family="dep:a"),
                self.feature(
                    "stable-b",
                    system="ziwei",
                    source_family="fixture.ziwei",
                    dependency_family="dep:b",
                ),
            ],
            target_scope="yearly",
        )

        self.assertEqual(result["domains"][0]["allowed_specificity"], "concrete_event")

    def test_unqualified_target_does_not_open_domain(self):
        result = rank_evidence(
            [self.feature("bad", qualification_status="unqualified")],
            target_scope="yearly",
        )
        self.assertEqual(result["opened_domains"], [])
        self.assertEqual(result["domains"], [])
        self.assertEqual(result["evaluated_features"][0]["reason"], "unqualified")

    def test_ranker_is_byte_deterministic_for_same_input_order(self):
        features = [
            self.feature("a", dependency_family="dep:a"),
            self.feature(
                "b",
                system="ziwei",
                source_family="fixture.ziwei",
                dependency_family="dep:b",
            ),
        ]
        first = rank_evidence(features, target_scope="yearly")
        second = rank_evidence(features, target_scope="yearly")
        self.assertEqual(self.canonical_bytes(first), self.canonical_bytes(second))
        self.assertEqual(first["ranking_digest"], second["ranking_digest"])

    def test_yearly_weak_monthly_strong_is_local_spike_without_mutating_parent(self):
        parent = rank_evidence(
            [self.feature("year-weak", strength_class="weak")],
            target_scope="yearly",
        )
        child = rank_evidence(
            [
                self.feature(
                    "month-strong",
                    scope="monthly",
                    reference_window={"scope": "monthly", "reference": "fixture"},
                    strength_class="strong",
                )
            ],
            target_scope="monthly",
            parent_ranking=parent,
        )
        parent_before = self.canonical_bytes(parent)
        child_before = self.canonical_bytes(child)

        windows = detect_local_spike(parent, child)

        self.assertEqual(len(windows), 1)
        window = windows[0]
        self.assertTrue(window["local_spike"])
        self.assertEqual(window["window_type"], "local_spike")
        self.assertEqual(window["primary_domain"], "career")
        self.assertEqual(window["parent_ranking_digest"], parent["ranking_digest"])
        self.assertEqual(window["child_ranking_digest"], child["ranking_digest"])
        self.assertEqual(self.canonical_bytes(parent), parent_before)
        self.assertEqual(self.canonical_bytes(child), child_before)

    def test_day_only_spike_with_weak_parent_cannot_claim_major_event_specificity(self):
        year = rank_evidence(
            [self.feature("year-weak", strength_class="weak")],
            target_scope="yearly",
        )
        month = rank_evidence(
            [
                self.feature(
                    "month-weak",
                    scope="monthly",
                    reference_window={"scope": "monthly", "reference": "fixture"},
                    strength_class="weak",
                )
            ],
            target_scope="monthly",
            parent_ranking=year,
        )
        day = rank_evidence(
            [
                self.feature(
                    "day-strong-a",
                    scope="daily",
                    reference_window={"scope": "daily", "reference": "fixture"},
                    strength_class="strong",
                    dependency_family="dep:day-a",
                ),
                self.feature(
                    "day-strong-b",
                    system="ziwei",
                    source_family="fixture.ziwei",
                    scope="daily",
                    reference_window={"scope": "daily", "reference": "fixture"},
                    strength_class="strong",
                    dependency_family="dep:day-b",
                ),
            ],
            target_scope="daily",
            parent_ranking=month,
        )
        self.assertEqual(day["domains"][0]["allowed_specificity"], "concrete_event")

        windows = detect_local_spike(month, day)

        self.assertEqual(len(windows), 1)
        window = windows[0]
        self.assertTrue(window["local_spike"])
        self.assertEqual(window["source_allowed_specificity"], "concrete_event")
        self.assertEqual(window["allowed_specificity"], "event_family")
        self.assertTrue(window["specificity_capped"])
        self.assertNotIn(
            window["allowed_specificity"],
            ("concrete_event", "highly_specific_event"),
        )

    def test_yearly_strong_monthly_same_direction_is_active_window_not_local_spike(self):
        parent = rank_evidence(
            [self.feature("year-strong", strength_class="strong")],
            target_scope="yearly",
        )
        child = rank_evidence(
            [
                self.feature(
                    "month-strong",
                    scope="monthly",
                    reference_window={"scope": "monthly", "reference": "fixture"},
                    strength_class="strong",
                )
            ],
            target_scope="monthly",
            parent_ranking=parent,
        )

        windows = detect_local_spike(parent, child)

        self.assertEqual(len(windows), 1)
        window = windows[0]
        self.assertFalse(window["local_spike"])
        self.assertEqual(window["window_type"], "active_window")
        self.assertEqual(window["primary_domain"], "career")
        self.assertEqual(window["parent_ranking_digest"], parent["ranking_digest"])
        self.assertEqual(window["child_ranking_digest"], child["ranking_digest"])


if __name__ == "__main__":
    unittest.main()
