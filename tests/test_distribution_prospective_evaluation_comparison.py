import copy
import importlib
import unittest

from engine.distribution.errors import DistributionError


class DistributionProspectiveEvaluationComparisonTests(unittest.TestCase):
    @staticmethod
    def _evaluation():
        return importlib.import_module("engine.distribution.prospective_evaluation")

    @staticmethod
    def _record(method_version, verification_state, scorable=True):
        return {
            "status": "evaluated",
            "locked_forecast_digest": "a" * 64,
            "claim": {
                "claim_id": f"{method_version}-{verification_state}",
                "method_version": method_version,
            },
            "evaluation": {
                "verification_state": verification_state,
                "scorable": scorable,
            },
        }

    def test_comparison_keeps_legacy_and_v15_denominators_separate(self):
        evaluation = self._evaluation()
        records = [
            self._record("legacy-method-label", "matched"),
            self._record("legacy-method-label", "not_matched"),
            self._record("legacy-method-label", "cannot_recall", scorable=False),
            self._record("lin_tianji_v1.5-exp", "matched"),
            self._record("lin_tianji_v1.5-exp", "partial"),
            self._record("lin_tianji_v1.5-exp", "matched", scorable=False),
        ]

        result = evaluation.build_method_comparison(records)
        methods = {item["method_version"]: item for item in result["methods"]}

        self.assertEqual(methods["legacy-method-label"]["clean_scorable_count"], 2)
        self.assertEqual(methods["legacy-method-label"]["matched_count"], 1)
        self.assertEqual(methods["legacy-method-label"]["not_matched_count"], 1)
        self.assertEqual(methods["lin_tianji_v1.5-exp"]["clean_scorable_count"], 2)
        self.assertEqual(methods["lin_tianji_v1.5-exp"]["matched_count"], 1)
        self.assertEqual(methods["lin_tianji_v1.5-exp"]["partial_count"], 1)

    def test_unscorable_records_do_not_enter_method_denominator(self):
        evaluation = self._evaluation()
        records = [
            self._record("lin_tianji_v1.5-exp", "matched", scorable=True),
            self._record("lin_tianji_v1.5-exp", "matched", scorable=False),
            self._record("lin_tianji_v1.5-exp", "cannot_recall", scorable=False),
        ]

        result = evaluation.build_method_comparison(records)
        method = result["methods"][0]

        self.assertEqual(method["clean_scorable_count"], 1)
        self.assertEqual(method["matched_count"], 1)
        self.assertEqual(method["partial_count"], 0)
        self.assertEqual(method["not_matched_count"], 0)

    def test_comparison_preserves_method_version_labels_exactly(self):
        evaluation = self._evaluation()
        labels = ["legacy-method-label", "lin_tianji_v1.5-exp", "research-shadow-v0"]
        records = [self._record(label, "matched") for label in labels]

        result = evaluation.build_method_comparison(records)

        self.assertEqual([item["method_version"] for item in result["methods"]], labels)

    def test_comparison_does_not_mutate_legacy_or_v15_records(self):
        evaluation = self._evaluation()
        records = [
            self._record("legacy-method-label", "not_matched"),
            self._record("lin_tianji_v1.5-exp", "matched"),
        ]
        original = copy.deepcopy(records)

        evaluation.build_method_comparison(records)

        self.assertEqual(records, original)

    def test_comparison_exposes_no_pooled_accuracy_or_superiority_claim(self):
        evaluation = self._evaluation()
        records = [
            self._record("legacy-method-label", "not_matched"),
            self._record("lin_tianji_v1.5-exp", "matched"),
        ]

        result = evaluation.build_method_comparison(records)

        self.assertEqual(result["status"], "comparison_metadata")
        self.assertEqual(result["comparison_boundary"], "separate_method_denominators")
        self.assertIsNone(result["pooled_accuracy_denominator"])
        self.assertEqual(result["superiority_claim_status"], "not_established")
        self.assertNotIn("accuracy", result)
        for method in result["methods"]:
            self.assertNotIn("accuracy", method)
            self.assertNotIn("accuracy_rate", method)

    def test_comparison_rejects_malformed_records_fail_closed(self):
        evaluation = self._evaluation()
        invalid_records = (
            [],
            [{"claim": {}, "evaluation": {"verification_state": "matched", "scorable": True}}],
            [self._record("lin_tianji_v1.5-exp", "unsupported")],
            [self._record("lin_tianji_v1.5-exp", "matched", scorable="yes")],
            [None],
        )

        for records in invalid_records:
            with self.subTest(records=records):
                with self.assertRaises(DistributionError) as caught:
                    evaluation.build_method_comparison(records)
                self.assertEqual(caught.exception.code, "invalid_prospective_evaluation")


if __name__ == "__main__":
    unittest.main()
