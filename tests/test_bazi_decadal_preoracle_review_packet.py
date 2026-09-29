import json
from pathlib import Path
import unittest

from tools.validate_bazi_decadal_preoracle_review_packet import (
    ready_for_preoracle_seal,
    validate_review_packet,
)


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "docs/research/bazi-decadal-preoracle-review-packet.v1.json"


class BaziDecadalPreOracleReviewPacketTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads(PACKET.read_text(encoding="utf-8"))

    def test_review_packet_is_valid_but_not_sealable(self):
        self.assertEqual(validate_review_packet(self.payload), [])
        self.assertFalse(ready_for_preoracle_seal(self.payload))
        self.assertFalse(self.payload["seal_allowed"])
        self.assertEqual(self.payload["task3_status"], "NEEDS_EVIDENCE")

    def test_expected_values_and_oracle_execution_are_absent(self):
        boundary = self.payload["independence_boundary"]
        self.assertFalse(boundary["oracle_expected_values_present"])
        self.assertFalse(boundary["oracle_execution_started"])
        text = json.dumps(self.payload, ensure_ascii=False).lower()
        self.assertNotIn('"expected":', text)

    def test_case_census_is_predeclared_and_balanced(self):
        cases = self.payload["case_selection"]["cases"]
        self.assertEqual(len(cases), 12)
        self.assertEqual(sum(case["sex"] == "male" for case in cases), 6)
        self.assertEqual(sum(case["sex"] == "female" for case in cases), 6)
        self.assertTrue(any("cross_year_jie_lookup" in case["coverage_tags"] for case in cases))
        self.assertTrue(any("leap_day" in case["coverage_tags"] for case in cases))
        self.assertTrue(any("before_jie" in case["coverage_tags"] for case in cases))
        self.assertTrue(any("after_jie" in case["coverage_tags"] for case in cases))

    def test_source_bytes_and_spec_digest_are_still_missing_by_design(self):
        self.assertIsNone(self.payload["profile_candidate"]["specification_sha256"])
        for source in self.payload["external_source_plan"]["sources"]:
            self.assertIsNone(source["source_bytes_sha256"])
            self.assertEqual(source["source_bytes_status"], "NOT_YET_CAPTURED")

    def test_blockers_include_domain_and_source_precision_decisions(self):
        blockers = set(self.payload["blocking_items"])
        self.assertIn("DOMAIN_REVIEW_OF_WRITTEN_PROFILE", blockers)
        self.assertIn("EQUALITY_AT_JIE_RULE_UNRESOLVED", blockers)
        self.assertIn("ENDPOINT_GENERATION_RULE_UNRESOLVED", blockers)
        self.assertIn("SOURCE_PRECISION_SEMANTICS_UNRESOLVED", blockers)

    def test_public_packet_does_not_claim_qualification_or_promotion(self):
        self.assertEqual(self.payload["status"], "DRAFT_PENDING_DOMAIN_REVIEW")
        self.assertEqual(self.payload["task3_status"], "NEEDS_EVIDENCE")
        self.assertFalse(self.payload["seal_allowed"])


if __name__ == "__main__":
    unittest.main()
