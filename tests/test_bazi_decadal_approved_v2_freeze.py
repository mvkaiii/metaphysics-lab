import hashlib
import json
from pathlib import Path
import unittest

from tools.materialize_bazi_decadal_case_inputs import validate_case_input_bundle
from tools.materialize_bazi_decadal_case_inputs_v2 import materialize_case_inputs_v2
from tools.seal_bazi_decadal_reference_inputs import validate_preoracle_seal

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs/research/bazi-decadal-independent-profile-spec.v2.md"
REVIEW = ROOT / "docs/research/bazi-decadal-preoracle-review-packet.v2.json"
BUNDLE = ROOT / "docs/research/bazi-decadal-oracle-case-inputs.v2.json"
SEAL = ROOT / "docs/research/bazi-decadal-preoracle-seal.v2.json"
CHECKPOINT = ROOT / "docs/research/bazi-decadal-domain-review-checkpoint.v2.json"

SPEC_SHA = "24825b1c2c850873f54e117c53c13932a8a730dc3a245a1c5e7e2599259c3305"
BUNDLE_SHA = "939f8e29123acabfc16366b05622d1d3598b6aa72c4cc54cf96db3ce6e35128e"
SEAL_SHA = "56f63fbe9561a9216e2f6e597d0f76ca4006af0ffd09a775f4da0d980e13ae0c"


class BaziDecadalApprovedV2FreezeTests(unittest.TestCase):
    def test_approved_spec_exact_digest(self):
        self.assertEqual(hashlib.sha256(SPEC.read_bytes()).hexdigest(), SPEC_SHA)

    def test_committed_case_bundle_is_reproducible_and_valid(self):
        review = json.loads(REVIEW.read_text(encoding="utf-8"))
        committed = json.loads(BUNDLE.read_text(encoding="utf-8"))
        rebuilt = materialize_case_inputs_v2(review, timezone="Asia/Taipei")
        self.assertEqual(committed, rebuilt)
        self.assertEqual(validate_case_input_bundle(committed), [])
        self.assertEqual(committed["bundle_sha256"], BUNDLE_SHA)
        text = json.dumps(committed, ensure_ascii=False).lower()
        for forbidden in ("forward", "reverse", "yin_year", "yang_year", "expected_from_contract"):
            self.assertNotIn(forbidden, text)

    def test_v2_seal_is_valid_and_exactly_bound(self):
        seal = json.loads(SEAL.read_text(encoding="utf-8"))
        self.assertEqual(validate_preoracle_seal(seal), [])
        self.assertEqual(seal["seal_sha256"], SEAL_SHA)
        self.assertEqual(seal["profile"]["specification_sha256"], SPEC_SHA)
        self.assertEqual(
            [case["case_id"] for case in seal["case_census"]],
            [f"bdv2-{i:03d}" for i in range(1, 13)],
        )
        self.assertTrue(all(case["production_results_consulted_for_selection"] is False for case in seal["case_census"]))
        self.assertFalse(seal["independence_boundary"]["expected_values_present"])

    def test_checkpoint_freezes_preapproval_production_candidate(self):
        checkpoint = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
        self.assertEqual(checkpoint["state"], "V2_PRE_ORACLE_SEALED")
        self.assertEqual(checkpoint["production_candidate"]["sha"], "6280c29b0a493e4b27379948c8cc82ba94bfa04f")
        self.assertEqual(checkpoint["case_inputs"]["bundle_sha256"], BUNDLE_SHA)
        self.assertEqual(checkpoint["preoracle_seal"]["seal_sha256"], SEAL_SHA)
        self.assertFalse(checkpoint["oracle_execution_started"])
        self.assertFalse(checkpoint["expected_values_present"])
        self.assertFalse(checkpoint["maturity_promotion"])


if __name__ == "__main__":
    unittest.main()
