import hashlib
import json
from pathlib import Path
import unittest

from tools.seal_bazi_decadal_reference_inputs import validate_preoracle_seal


ROOT = Path(__file__).resolve().parents[1]
SEAL = ROOT / "docs/research/bazi-decadal-preoracle-seal.v1.json"
CASE_INPUTS = ROOT / "docs/research/bazi-decadal-oracle-case-inputs.v1.json"
CHECKPOINT = ROOT / "docs/research/bazi-decadal-domain-review-checkpoint.v1.json"
SPEC = ROOT / "docs/research/bazi-decadal-independent-profile-spec.v1.md"


class BaziDecadalApprovedPreOracleSealTests(unittest.TestCase):
    def setUp(self):
        self.seal = json.loads(SEAL.read_text(encoding="utf-8"))
        self.case_inputs = json.loads(CASE_INPUTS.read_text(encoding="utf-8"))
        self.checkpoint = json.loads(CHECKPOINT.read_text(encoding="utf-8"))

    def test_preoracle_seal_validates(self):
        self.assertEqual(validate_preoracle_seal(self.seal), [])
        self.assertEqual(self.seal["status"], "PRE_ORACLE_SEALED")
        self.assertEqual(
            self.seal["seal_sha256"],
            "db32a95bc41a54531907e7e059655c094b1b1234a533770a88f2e3a52712874e",
        )

    def test_spec_digest_is_exact(self):
        digest = hashlib.sha256(SPEC.read_bytes()).hexdigest()
        self.assertEqual(
            digest,
            "0757d1275e55b84e2424d6131e9dbdc73e029e1b619f900147be928cc7e5e01d",
        )
        self.assertEqual(self.seal["profile"]["specification_sha256"], digest)

    def test_case_input_digests_bind_exact_seal_census(self):
        by_id = {case["case_id"]: case for case in self.case_inputs["cases"]}
        self.assertEqual(len(by_id), 12)
        self.assertEqual(len(self.seal["case_census"]), 12)
        for sealed in self.seal["case_census"]:
            self.assertEqual(sealed["input_sha256"], by_id[sealed["case_id"]]["input_sha256"])

    def test_source_bindings_are_exact_acquired_bytes(self):
        by_year = {
            2015: "60a45ab889ef436936571a04a49387c6f9ce8d43243fb21c64e3fcb0331c8320",
            2016: "84beb01553646b807a7c15d6efebdd7550af1ac6d7f06e07bfdd124dab9e443b",
        }
        self.assertEqual(
            [source["source_sha256"] for source in self.seal["source_bindings"]],
            [by_year[2015], by_year[2016]],
        )

    def test_no_oracle_values_or_comparison_results_exist(self):
        text = json.dumps(
            {"seal": self.seal, "case_inputs": self.case_inputs, "checkpoint": self.checkpoint},
            ensure_ascii=False,
        ).lower()
        self.assertNotIn('"expected":', text)
        self.assertFalse(self.seal["independence_boundary"]["expected_values_present"])
        self.assertFalse(self.checkpoint["oracle_execution_started"])
        self.assertFalse(self.checkpoint["comparison_started"])
        self.assertTrue(self.checkpoint["oracle_handoff_allowed"])

    def test_approved_tolerances_and_endpoint_are_frozen(self):
        for case in self.seal["case_census"]:
            rows = {row["path"]: row for row in case["comparisons"]}
            self.assertEqual(rows["/periods/0/start_age_years"]["tolerance"], 0.0002314814814814815)
            self.assertEqual(rows["/periods/0/start_datetime"]["tolerance"], 7304.85)
            self.assertEqual(rows["/periods/1/end_datetime"]["tolerance"], 7304.85)
            self.assertEqual(rows["/periods/1/end_datetime"]["kind"], "datetime_abs_seconds")


if __name__ == "__main__":
    unittest.main()
