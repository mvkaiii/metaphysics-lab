import hashlib
import json
from pathlib import Path
import unittest

from tools.validate_bazi_decadal_clean_oracle_contract import validate_clean_oracle_contract
from tools.seal_bazi_decadal_reference_inputs import validate_preoracle_seal

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs/research/bazi-decadal-independent-oracle-contract.v2.1.md"
CASES = ROOT / "docs/research/bazi-decadal-oracle-case-inputs.v2.1.json"
SEAL = ROOT / "docs/research/bazi-decadal-preoracle-seal.v2.1.json"
V2_CASES = ROOT / "docs/research/bazi-decadal-oracle-case-inputs.v2.json"

SPEC_SHA = "b47de7809cadb82159c272b2d2d7fb3bbc7ffc99d9e8ed6c1fa60a1bf3c900e4"
CASE_SHA = "939f8e29123acabfc16366b05622d1d3598b6aa72c4cc54cf96db3ce6e35128e"
SEAL_SHA = "53f4e249f4f6e13fd26e9859101cceeaac31a1f186c155653a24e79f02dd4a27"


class BaziDecadalV21CleanOracleContractTests(unittest.TestCase):
    def test_clean_contract_has_no_prior_result_leakage(self):
        self.assertEqual(validate_clean_oracle_contract(SPEC), [])

    def test_clean_contract_exact_digest(self):
        self.assertEqual(hashlib.sha256(SPEC.read_bytes()).hexdigest(), SPEC_SHA)

    def test_case_bundle_is_byte_identical_to_v2_case_bundle(self):
        self.assertEqual(CASES.read_bytes(), V2_CASES.read_bytes())
        payload = json.loads(CASES.read_text(encoding="utf-8"))
        self.assertEqual(payload["bundle_sha256"], CASE_SHA)
        self.assertFalse(payload["expected_values_present"])
        self.assertEqual([c["case_id"] for c in payload["cases"]], [f"bdv2-{i:03d}" for i in range(1, 13)])

    def test_v21_seal_is_valid_and_bound_to_clean_contract(self):
        seal = json.loads(SEAL.read_text(encoding="utf-8"))
        self.assertEqual(validate_preoracle_seal(seal), [])
        self.assertEqual(seal["seal_sha256"], SEAL_SHA)
        self.assertEqual(seal["profile"]["specification_sha256"], SPEC_SHA)
        self.assertFalse(seal["independence_boundary"]["expected_values_present"])


if __name__ == "__main__":
    unittest.main()
