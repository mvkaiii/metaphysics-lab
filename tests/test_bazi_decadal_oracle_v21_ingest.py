import json
from pathlib import Path
import unittest

from tools.ingest_bazi_decadal_oracle_v21 import validate_and_normalize

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/research/evidence/bazi-decadal-v2.1-independent-oracle"


class BaziDecadalOracleV21IngestTests(unittest.TestCase):
    def test_uploaded_independent_oracle_artifacts_validate(self):
        normalized, receipt = validate_and_normalize(
            oracle_source=EVIDENCE / "oracle.cjs",
            source_record=EVIDENCE / "oracle-source.sha256",
            oracle_output=EVIDENCE / "oracle-output.json",
            sealing_receipt=EVIDENCE / "sealing-receipt.json",
            case_bundle_path=ROOT / "docs/research/bazi-decadal-oracle-case-inputs.v2.1.json",
            preoracle_seal_path=ROOT / "docs/research/bazi-decadal-preoracle-seal.v2.1.json",
        )
        self.assertEqual(receipt["status"], "ORACLE_ARTIFACTS_VALIDATED")
        self.assertEqual(receipt["case_count"], 12)
        self.assertEqual(receipt["expected_value_count"], 60)
        self.assertEqual(len(normalized["cases"]), 12)
        self.assertFalse(normalized["production_code_access"])
        self.assertFalse(normalized["production_output_access"])
        self.assertFalse(normalized["comparison_result_access_before_seal"])


if __name__ == "__main__":
    unittest.main()
