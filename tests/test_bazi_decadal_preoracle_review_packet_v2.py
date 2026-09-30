import json
from pathlib import Path
import unittest

from tools.validate_bazi_decadal_preoracle_review_packet_v2 import (
    ready_for_preoracle_seal_v2,
    validate_review_packet_v2,
)

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "docs/research/bazi-decadal-preoracle-review-packet.v2.json"
V1_CASES = ROOT / "docs/research/bazi-decadal-oracle-case-inputs.v1.json"


class BaziDecadalPreOracleReviewPacketV2Tests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads(PACKET.read_text(encoding="utf-8"))

    def test_v2_review_packet_is_valid_but_not_sealable(self):
        self.assertEqual(validate_review_packet_v2(self.payload), [])
        self.assertFalse(ready_for_preoracle_seal_v2(self.payload))
        self.assertFalse(self.payload["seal_allowed"])
        self.assertEqual(self.payload["task3_status"], "NEEDS_EVIDENCE")

    def test_case_inputs_are_exactly_the_same_pre_result_v1_inputs(self):
        v1 = json.loads(V1_CASES.read_text(encoding="utf-8"))
        old_inputs = sorted(
            (case["input"]["birth_datetime"], case["input"]["sex"])
            for case in v1["cases"]
        )
        new_inputs = sorted(
            (case["birth_datetime"], case["sex"])
            for case in self.payload["case_selection"]["cases"]
        )
        self.assertEqual(new_inputs, old_inputs)
        self.assertEqual(self.payload["case_selection"]["post_result_case_additions"], 0)
        self.assertEqual(self.payload["case_selection"]["post_result_case_removals"], 0)
        self.assertEqual(self.payload["case_selection"]["post_result_case_replacements"], 0)

    def test_case_metadata_has_no_direction_or_year_polarity_answers(self):
        cases = self.payload["case_selection"]["cases"]
        self.assertEqual([case["case_id"] for case in cases], [f"bdv2-{i:03d}" for i in range(1, 13)])
        serialized = json.dumps(cases, ensure_ascii=False).lower()
        for forbidden in (
            "forward",
            "reverse",
            "yin_year",
            "yang_year",
            "expected_from_contract",
        ):
            self.assertNotIn(forbidden, serialized)

    def test_independent_source_is_hko_and_production_provider_is_separate(self):
        oracle = self.payload["independent_oracle_source_plan"]
        production = self.payload["production_timing_evidence"]
        self.assertEqual(oracle["provider"], "Hong Kong Observatory")
        self.assertEqual(oracle["published_precision_seconds"], 60)
        self.assertEqual(production["provider"], "bundled lunar-python==1.4.8")
        self.assertEqual(production["benchmark_result"], "PASS")
        self.assertEqual(production["within_60_seconds"], 48)

    def test_equality_gap_is_explicit_not_fabricated(self):
        equality = self.payload["equality_coverage"]
        self.assertFalse(equality["exact_subminute_hko_equality_case_present"])
        self.assertTrue(equality["project_unit_test_present"])
        self.assertTrue(equality["domain_acceptance_required"])

    def test_no_oracle_output_or_qualification_claim_is_present(self):
        text = json.dumps(self.payload, ensure_ascii=False).lower()
        self.assertNotIn('"expected":', text)
        self.assertFalse(self.payload["independence_boundary"]["oracle_execution_started"])
        self.assertFalse(self.payload["independence_boundary"]["oracle_expected_values_present"])
        self.assertFalse(self.payload["seal_allowed"])


if __name__ == "__main__":
    unittest.main()
