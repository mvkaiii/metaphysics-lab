import copy
import json
from pathlib import Path
import unittest

from tools.materialize_bazi_decadal_case_inputs import (
    materialize_case_inputs,
    validate_case_input_bundle,
)


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "docs/research/bazi-decadal-preoracle-review-packet.v1.json"


class BaziDecadalCaseInputBundleTests(unittest.TestCase):
    def setUp(self):
        self.review = json.loads(PACKET.read_text(encoding="utf-8"))

    def test_materializes_all_and_only_predeclared_cases(self):
        bundle = materialize_case_inputs(self.review, timezone="Asia/Taipei")
        self.assertEqual(validate_case_input_bundle(bundle), [])
        expected_ids = [case["case_id"] for case in self.review["case_selection"]["cases"]]
        actual_ids = [case["case_id"] for case in bundle["cases"]]
        self.assertEqual(actual_ids, expected_ids)
        self.assertEqual(len(actual_ids), 12)

    def test_bundle_contains_no_expected_values_or_production_results(self):
        bundle = materialize_case_inputs(self.review, timezone="Asia/Taipei")
        serialized = json.dumps(bundle, ensure_ascii=False).lower()
        self.assertNotIn('"expected":', serialized)
        self.assertFalse(bundle["expected_values_present"])
        self.assertFalse(bundle["production_results_consulted_for_selection"])

    def test_case_input_digests_are_deterministic(self):
        first = materialize_case_inputs(self.review, timezone="Asia/Taipei")
        second = materialize_case_inputs(
            json.loads(json.dumps(self.review, ensure_ascii=False)),
            timezone="Asia/Taipei",
        )
        self.assertEqual(first, second)

    def test_post_materialization_mutation_breaks_digest(self):
        bundle = materialize_case_inputs(self.review, timezone="Asia/Taipei")
        mutated = copy.deepcopy(bundle)
        mutated["cases"][0]["input"]["birth_datetime"] = "2015-04-05T10:35:00+08:00"
        errors = validate_case_input_bundle(mutated)
        self.assertTrue(any("input_sha256" in error for error in errors), errors)
        self.assertTrue(any("bundle_sha256" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
