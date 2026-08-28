import copy
import unittest

from engine.distribution.errors import DistributionError
from engine.distribution.evidence_ranker import rank_evidence
from engine.distribution.historical_personalization import personalize_ranking


class HistoricalPersonalizationTests(unittest.TestCase):
    def feature(self, feature_id, **overrides):
        payload = {
            "feature_id": feature_id,
            "system": "bazi",
            "scope": "yearly",
            "reference_window": {"scope": "yearly", "reference": "fixture"},
            "primary_domain": "career",
            "event_family_support": ["role_change", "responsibility"],
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

    def base_ranking(self):
        return rank_evidence(
            [
                self.feature("career"),
                self.feature(
                    "finance",
                    primary_domain="finance",
                    event_family_support=["earned_income", "resource_management"],
                    strength_class="weak",
                ),
            ],
            target_scope="yearly",
        )

    def career_only_base(self):
        return rank_evidence([self.feature("career")], target_scope="yearly")

    @staticmethod
    def domain(result, domain_id):
        return next(row for row in result["domains"] if row["primary_domain"] == domain_id)

    def record(
        self,
        year,
        record_id=None,
        domains=None,
        families=None,
        role="high_activation",
        blindness="blind",
        verification_state="matched",
        domain_status="matched",
        event_form_status="matched",
        timing_status="exact_flow_year",
        actual_event="synthetic event",
        hypothesis="synthetic blind hypothesis",
    ):
        return {
            "record_id": record_id or "HC-001-%s" % year,
            "record_type": "historical_calibration",
            "calibration_id": "HC-001",
            "origin": "canonical",
            "blind_prediction": {
                "predicted_flow_year": year,
                "role": role,
                "primary_domains": list(domains or ["career"]),
                "event_family": list(families or ["role_change"]),
                "blindness_status": blindness,
                "hypothesis": hypothesis,
            },
            "evaluation": {
                "verification_state": verification_state,
                "domain_status": domain_status,
                "event_form_status": event_form_status,
                "timing_status": timing_status,
                "offset_flow_years": 0,
                "boundary_ambiguity": False,
            },
            "user_confirmed_actual": {
                "actual_event": actual_event,
                "actual_date": "%04d-06-01" % year,
            },
        }

    def missed_record(self, year, **overrides):
        payload = {
            "verification_state": "not_matched",
            "domain_status": "missed",
            "event_form_status": "missed",
            "timing_status": "missed",
        }
        payload.update(overrides)
        return self.record(year, **payload)

    def test_tampered_base_ranking_digest_fails_closed(self):
        base = self.base_ranking()
        base["domains"][0]["ordinal_score_scaled"] += 1
        with self.assertRaises(DistributionError):
            personalize_ranking(base, "basic", [])

    def test_legacy_domain_normalizes_but_legacy_family_remains_unmapped(self):
        result = personalize_ranking(
            self.base_ranking(),
            "basic",
            [
                self.record(
                    2020,
                    domains=["工作／職責"],
                    families=["職務或責任結構改變"],
                )
            ],
        )
        self.assertEqual(result["eligible_record_count"], 1)
        self.assertEqual(result["excluded_record_counts"]["unmapped_event_family"], 1)
        self.assertEqual(
            [row["primary_domain"] for row in result["domains"]],
            [row["primary_domain"] for row in self.base_ranking()["domains"]],
        )

    def test_actual_event_and_hypothesis_are_not_part_of_historical_source_identity(self):
        first = self.record(2020, actual_event="A", hypothesis="X")
        second = copy.deepcopy(first)
        second["user_confirmed_actual"]["actual_event"] = "完全不同的自由文字"
        second["blind_prediction"]["hypothesis"] = "另一段盲判文字"

        a = personalize_ranking(self.base_ranking(), "basic", [first])
        b = personalize_ranking(self.base_ranking(), "basic", [second])

        self.assertEqual(a["historical_source_digest"], b["historical_source_digest"])
        self.assertEqual(a["personalization_digest"], b["personalization_digest"])
        self.assertEqual(a["domains"], b["domains"])

    def test_no_history_shell_preserves_base_truth(self):
        base = self.base_ranking()
        result = personalize_ranking(base, "basic", [])
        self.assertEqual(result["base_policy_version"], base["policy_version"])
        self.assertEqual(result["base_ranking_digest"], base["ranking_digest"])
        self.assertEqual(
            [row["primary_domain"] for row in result["domains"]],
            [row["primary_domain"] for row in base["domains"]],
        )
        for output_row, base_row in zip(result["domains"], base["domains"]):
            self.assertEqual(output_row["base_rank"], base_row["rank"])
            self.assertEqual(
                output_row["base_ordinal_score_scaled"],
                base_row["ordinal_score_scaled"],
            )
            self.assertEqual(output_row["allowed_specificity"], base_row["allowed_specificity"])
            self.assertEqual(output_row["base_event_families"], base_row["event_families"])
            self.assertEqual(output_row["historical_modifier_scaled"], 0)
        self.assertEqual(result["personalization_status"], "no_op")
        self.assertTrue(result["personalization_digest"])

    def test_contaminated_cannot_recall_and_control_do_not_score(self):
        rows = [
            self.record(2018, blindness="contaminated"),
            self.record(
                2019,
                verification_state="cannot_recall",
                domain_status="unscorable",
                event_form_status="unscorable",
                timing_status="unscorable",
            ),
            self.record(2020, role="control"),
        ]
        result = personalize_ranking(self.base_ranking(), "basic", rows)
        self.assertEqual(result["eligible_record_count"], 0)
        self.assertTrue(all(row["historical_modifier_scaled"] == 0 for row in result["domains"]))
        self.assertEqual(result["control_audit"]["record_count"], 1)
        self.assertEqual(result["personalization_status"], "no_op")

    def test_same_year_only_first_valid_blind_high_activation_scores(self):
        rows = [
            self.record(2020, record_id="A", blindness="contaminated"),
            self.record(2020, record_id="B", domain_status="matched"),
            self.missed_record(2020, record_id="C"),
            self.record(2021, record_id="D", domain_status="matched"),
        ]
        result = personalize_ranking(self.base_ranking(), "basic", rows)
        career = self.domain(result, "career")
        self.assertEqual(career["supporting_record_ids"], ["B", "D"])
        self.assertEqual(result["excluded_record_counts"]["duplicate_reference_year"], 1)
        self.assertEqual(career["historical_modifier_scaled"], 2)

    def test_multi_domain_aggregate_match_does_not_split_votes(self):
        rows = [
            self.record(2020, domains=["career", "finance"]),
            self.record(2021, domains=["career", "finance"]),
        ]
        result = personalize_ranking(self.base_ranking(), "basic", rows)
        self.assertEqual(result["excluded_record_counts"]["ambiguous_multi_domain"], 2)
        self.assertTrue(all(row["historical_modifier_scaled"] == 0 for row in result["domains"]))
        self.assertEqual(result["personalization_status"], "no_op")

    def test_history_cannot_create_domain_absent_from_base(self):
        rows = [
            self.record(2020, domains=["health"]),
            self.record(2021, domains=["health"]),
        ]
        result = personalize_ranking(self.career_only_base(), "basic", rows)
        self.assertEqual([row["primary_domain"] for row in result["domains"]], ["career"])
        self.assertEqual(result["excluded_record_counts"]["domain_not_in_base"], 2)
        self.assertEqual(result["personalization_status"], "no_op")

    def test_two_matches_apply_positive_modifier_without_rewriting_base(self):
        base = self.base_ranking()
        result = personalize_ranking(
            base,
            "basic",
            [self.record(2020), self.record(2021)],
        )
        career = self.domain(result, "career")
        base_career = self.domain(base, "career")
        self.assertEqual(career["historical_modifier_scaled"], 2)
        self.assertEqual(
            career["personalized_ordering_score_scaled"],
            base_career["ordinal_score_scaled"] + 2,
        )
        self.assertEqual(career["base_ordinal_score_scaled"], base_career["ordinal_score_scaled"])
        self.assertEqual(career["allowed_specificity"], base_career["allowed_specificity"])
        self.assertEqual(result["base_ranking_digest"], base["ranking_digest"])
        self.assertEqual(result["personalization_status"], "applied")

    def test_one_sample_is_insufficient_and_no_op(self):
        result = personalize_ranking(self.base_ranking(), "basic", [self.record(2020)])
        career = self.domain(result, "career")
        self.assertEqual(career["historical_modifier_scaled"], 0)
        self.assertEqual(career["historical_support_class"], "insufficient")
        self.assertEqual(result["personalization_status"], "no_op")

    def test_two_misses_apply_negative_modifier_and_many_samples_stay_bounded(self):
        negative = [self.missed_record(2020), self.missed_record(2021)]
        result = personalize_ranking(self.base_ranking(), "basic", negative)
        self.assertEqual(self.domain(result, "career")["historical_modifier_scaled"], -2)

        positive_many = [
            self.record(1900 + index, record_id="P%03d" % index)
            for index in range(100)
        ]
        negative_many = [
            self.missed_record(2100 + index, record_id="N%03d" % index)
            for index in range(100)
        ]
        self.assertEqual(
            self.domain(personalize_ranking(self.base_ranking(), "basic", positive_many), "career")[
                "historical_modifier_scaled"
            ],
            2,
        )
        self.assertEqual(
            self.domain(personalize_ranking(self.base_ranking(), "basic", negative_many), "career")[
                "historical_modifier_scaled"
            ],
            -2,
        )

    def test_matched_and_missed_are_mixed_without_probability_semantics(self):
        result = personalize_ranking(
            self.base_ranking(),
            "basic",
            [self.record(2020), self.missed_record(2021)],
        )
        career = self.domain(result, "career")
        self.assertEqual(career["historical_modifier_scaled"], 0)
        self.assertEqual(career["historical_support_class"], "mixed")
        self.assertEqual(result["personalization_status"], "applied")

    def test_uncalibrated_forces_no_op_even_with_many_matching_records(self):
        base = self.base_ranking()
        result = personalize_ranking(
            base,
            "uncalibrated",
            [self.record(2020), self.record(2021), self.record(2022)],
        )
        self.assertEqual(result["personalization_status"], "no_op")
        self.assertEqual(
            [row["primary_domain"] for row in result["domains"]],
            [row["primary_domain"] for row in base["domains"]],
        )
        self.assertTrue(all(row["historical_modifier_scaled"] == 0 for row in result["domains"]))


if __name__ == "__main__":
    unittest.main()
