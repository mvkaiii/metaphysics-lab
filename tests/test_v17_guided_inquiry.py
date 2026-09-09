import json
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from engine.distribution.errors import DistributionError
from engine.distribution.guided_inquiry import suppression_reason, suggest_inquiries


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "v1.7-guided-inquiry.synthetic.json"


class GuidedInquiryPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scenarios = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def scenario(self, scenario_id):
        return deepcopy(self.scenarios[scenario_id])

    def test_fixture_contains_exact_required_scenarios(self):
        self.assertEqual(
            set(self.scenarios),
            {"GI-%02d" % index for index in range(1, 13)},
        )

    def test_entry_pass_returns_exactly_three_suggestions(self):
        result = suggest_inquiries(self.scenario("GI-01"))
        self.assertFalse(result["suppressed"])
        self.assertIsNone(result["suppression_reason"])
        self.assertEqual(len(result["suggestions"]), 3)
        self.assertEqual(result["policy_version"], "guided_inquiry_v1")

    def test_entry_warn_puts_integrity_first_and_keeps_total_three(self):
        result = suggest_inquiries(self.scenario("GI-02"))
        self.assertFalse(result["suppressed"])
        self.assertEqual(len(result["suggestions"]), 3)
        self.assertEqual(result["suggestions"][0]["type"], "integrity")

    def test_entry_pending_forecast_can_use_distinct_fourth_direction(self):
        result = suggest_inquiries(self.scenario("GI-03"))
        self.assertFalse(result["suppressed"])
        self.assertEqual(len(result["suggestions"]), 4)
        keys = [
            (row["type"], row["domain"], row["target_scope"])
            for row in result["suggestions"]
        ]
        self.assertEqual(len(keys), len(set(keys)))

    def test_warn_entry_with_pending_forecast_reserves_fourth_for_validation(self):
        payload = self.scenario("GI-02")
        payload["pending_forecast_available"] = True
        result = suggest_inquiries(payload)
        self.assertFalse(result["suppressed"])
        self.assertEqual(len(result["suggestions"]), 4)
        self.assertEqual(result["suggestions"][0]["type"], "integrity")
        self.assertEqual(result["suggestions"][3]["type"], "validation")

    def test_post_answer_career_starts_with_deep_dive(self):
        result = suggest_inquiries(self.scenario("GI-04"))
        self.assertFalse(result["suppressed"])
        self.assertEqual(result["suggestions"][0]["type"], "deep_dive")
        self.assertEqual(result["suggestions"][0]["domain"], "career")

    def test_post_answer_with_real_options_includes_decision(self):
        result = suggest_inquiries(self.scenario("GI-05"))
        self.assertFalse(result["suppressed"])
        self.assertIn("decision", [row["type"] for row in result["suggestions"]])

    def test_falsifiable_forecast_includes_validation(self):
        result = suggest_inquiries(self.scenario("GI-06"))
        self.assertFalse(result["suppressed"])
        self.assertIn("validation", [row["type"] for row in result["suggestions"]])

    def test_post_answer_respects_specificity_time_and_related_domain_inputs(self):
        payload = self.scenario("GI-04")
        result = suggest_inquiries(payload)
        self.assertFalse(result["suppressed"])
        specificity_order = {"broad_domain": 0, "event_family": 1, "event_form": 2}
        ceiling = specificity_order[payload["current_answer"]["allowed_specificity"]]
        for row in result["suggestions"]:
            self.assertLessEqual(specificity_order[row["requested_specificity"]], ceiling)
            if row["type"] == "time_refine":
                self.assertIn(row["target_scope"], payload["current_answer"]["time_refinement_scopes"])
            if row["type"] == "related_domain":
                self.assertIn(row["domain"], payload["current_answer"]["related_domains"])

    def test_specificity_gate_filters_illegal_candidate_before_selection(self):
        payload = self.scenario("GI-04")
        injected = [
            {
                "type": "deep_dive",
                "domain": "career",
                "target_scope": "yearly",
                "requested_specificity": "event_family",
                "max_specificity": "event_family",
                "reason_code": "legal_one",
            },
            {
                "type": "deep_dive",
                "domain": "career",
                "target_scope": "yearly",
                "requested_specificity": "event_form",
                "max_specificity": "event_family",
                "reason_code": "illegal_inflation",
            },
            {
                "type": "related_domain",
                "domain": "finance",
                "target_scope": "yearly",
                "requested_specificity": "broad_domain",
                "max_specificity": "event_family",
                "reason_code": "legal_two",
            },
        ]
        with patch("engine.distribution.guided_inquiry._post_answer_candidates", return_value=injected):
            result = suggest_inquiries(payload)
        self.assertTrue(result["suppressed"])
        self.assertEqual(result["suppression_reason"], "insufficient_legal_suggestions")
        self.assertEqual(result["suggestions"], [])

    def test_hard_blocking_scenarios_are_suppressed(self):
        for scenario_id in ("GI-07", "GI-08", "GI-09", "GI-10"):
            with self.subTest(scenario_id=scenario_id):
                result = suggest_inquiries(self.scenario(scenario_id))
                self.assertTrue(result["suppressed"])
                self.assertEqual(result["suggestions"], [])
                self.assertEqual(result["policy_version"], "guided_inquiry_v1")

    def test_suppression_reason_precedence_is_deterministic(self):
        payload = self.scenario("GI-01")
        payload["user_opted_out"] = True
        payload["case_health"] = "BLOCKED"
        payload["blocking_state"] = "runtime_error"
        self.assertEqual(suppression_reason(payload), "user_opted_out")

        payload["user_opted_out"] = False
        self.assertEqual(suppression_reason(payload), "case_blocked")

        payload["case_health"] = "PASS"
        self.assertEqual(suppression_reason(payload), "runtime_error")

        for state in (
            "required_input",
            "historical_disclosure",
            "mutation_confirmation",
            "non_metaphysics_utility",
        ):
            with self.subTest(state=state):
                payload["blocking_state"] = state
                self.assertEqual(suppression_reason(payload), state)

        payload["blocking_state"] = "none"
        self.assertIsNone(suppression_reason(payload))

    def test_fewer_than_three_legal_candidates_suppresses_entire_block(self):
        result = suggest_inquiries(self.scenario("GI-11"))
        self.assertTrue(result["suppressed"])
        self.assertEqual(result["suppression_reason"], "insufficient_legal_suggestions")
        self.assertEqual(result["suggestions"], [])

    def test_mapping_insertion_order_does_not_change_output_bytes(self):
        variants = self.scenario("GI-12")
        left = suggest_inquiries(variants["payload_a"])
        right = suggest_inquiries(variants["payload_b"])
        canonical = lambda value: json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        self.assertEqual(canonical(left), canonical(right))

    def test_blindness_forbidden_fields_fail_closed(self):
        forbidden = {
            "verified_events": [],
            "historical_actuals": [],
            "ground_truth": {},
            "event_text": "not allowed",
        }
        for field, value in forbidden.items():
            with self.subTest(location="top_level", field=field):
                payload = self.scenario("GI-01")
                payload[field] = value
                with self.assertRaises(DistributionError) as caught:
                    suggest_inquiries(payload)
                self.assertEqual(caught.exception.code, "invalid_guided_inquiry_payload")

            with self.subTest(location="current_answer", field=field):
                payload = self.scenario("GI-04")
                payload["current_answer"][field] = value
                with self.assertRaises(DistributionError) as caught:
                    suggest_inquiries(payload)
                self.assertEqual(caught.exception.code, "invalid_guided_inquiry_payload")

    def test_unknown_top_level_field_fails_closed(self):
        payload = self.scenario("GI-01")
        payload["unknown_field"] = []
        with self.assertRaises(DistributionError) as caught:
            suggest_inquiries(payload)
        self.assertEqual(caught.exception.code, "invalid_guided_inquiry_payload")

    def test_unknown_enums_and_non_boolean_flags_fail_closed(self):
        mutations = [
            ("mode", "other"),
            ("case_health", "UNKNOWN"),
            ("blocking_state", "later"),
            ("user_opted_out", 1),
            ("case_integrity_action_available", "yes"),
            ("pending_forecast_available", None),
        ]
        for field, value in mutations:
            with self.subTest(field=field, value=value):
                payload = self.scenario("GI-01")
                payload[field] = value
                with self.assertRaises(DistributionError) as caught:
                    suggest_inquiries(payload)
                self.assertEqual(caught.exception.code, "invalid_guided_inquiry_payload")

    def test_post_answer_requires_complete_current_answer_contract(self):
        payload = self.scenario("GI-04")
        payload["current_answer"] = None
        with self.assertRaises(DistributionError) as caught:
            suggest_inquiries(payload)
        self.assertEqual(caught.exception.code, "invalid_guided_inquiry_payload")

    def test_current_answer_rejects_unknown_fields_duplicate_domains_and_bad_scopes(self):
        base = self.scenario("GI-04")
        mutations = []

        unknown = deepcopy(base)
        unknown["current_answer"]["other"] = "not allowed"
        mutations.append(unknown)

        duplicate_domain = deepcopy(base)
        duplicate_domain["current_answer"]["related_domains"] = ["finance", "finance"]
        mutations.append(duplicate_domain)

        bad_scope = deepcopy(base)
        bad_scope["current_answer"]["time_refinement_scopes"] = ["decadal"]
        mutations.append(bad_scope)

        for payload in mutations:
            with self.subTest(payload=payload):
                with self.assertRaises(DistributionError) as caught:
                    suggest_inquiries(payload)
                self.assertEqual(caught.exception.code, "invalid_guided_inquiry_payload")


if __name__ == "__main__":
    unittest.main()
