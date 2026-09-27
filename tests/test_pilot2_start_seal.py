import hashlib
import json
from pathlib import Path
import unittest

from engine.distribution.manifest import capability_manifest_digest
from tools.validate_prospective_pilot_decision import (
    pilot_start_allowed,
    validate_decision_receipt,
)
from tools.validate_pilot2_pre_candidate_gate import (
    candidate_case_processing_allowed,
    validate_pilot2_pre_candidate_gate,
)


ROOT = Path(__file__).resolve().parents[1]
SEAL_PATH = ROOT / "docs" / "research" / "pilot2-start-seal.v1.json"
RECEIPT_PATH = ROOT / "docs" / "research" / "pilot2-decision-receipt.template.json"
GATE_PATH = ROOT / "docs" / "research" / "pilot2-pre-candidate-gate.template.json"
PROTOCOL_PATH = ROOT / "docs" / "research" / "pilot2-protocol.md"
WINDOW_PATH = ROOT / "docs" / "research" / "pilot2-window-policy.v1.json"


class Pilot2StartSealTests(unittest.TestCase):
    def setUp(self):
        self.seal = json.loads(SEAL_PATH.read_text(encoding="utf-8"))
        self.receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
        self.gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))

    def test_seal_binds_exact_frozen_candidate_and_package(self):
        frozen = self.seal["frozen_candidate"]
        self.assertEqual(
            frozen["candidate_commit"],
            "4cf324a851204b2d278dc044acf2b0561304d2b0",
        )
        self.assertEqual(
            frozen["package_sha256"],
            "cb175e2d482fe9ca8e2d46d6c55c4b0237f1cbb9a631e0d3c50aef75f8e1e0c4",
        )

    def test_manifest_digest_recomputes_from_registry_truth(self):
        self.assertEqual(
            capability_manifest_digest(),
            "d11a63ec5194fb49939f4b02583a8bddf7bcfb0e9e7bbd9f547af1047837e7b0",
        )
        self.assertEqual(
            capability_manifest_digest(),
            self.seal["frozen_candidate"]["capability_manifest_sha256"],
        )

    def test_protocol_digest_recomputes_from_raw_approved_bytes(self):
        digest = hashlib.sha256(PROTOCOL_PATH.read_bytes()).hexdigest()
        self.assertEqual(
            digest,
            "840b9f8accf4bc1bd3289703ca6179847ac22766cd66f2d71ba3a8f355869352",
        )
        self.assertEqual(
            digest,
            self.seal["frozen_candidate"]["protocol_sha256"],
        )

    def test_window_policy_digest_recomputes_from_raw_bytes(self):
        digest = hashlib.sha256(WINDOW_PATH.read_bytes()).hexdigest()
        self.assertEqual(
            digest,
            "fae6cb56e722a7e427d3b21e29c7355e6d39baf5bdac9ecde39766832736c445",
        )
        self.assertEqual(
            digest,
            self.seal["frozen_candidate"]["window_policy_sha256"],
        )

    def test_start_receipt_is_authorized(self):
        self.assertEqual(validate_decision_receipt(self.receipt), [])
        self.assertTrue(pilot_start_allowed(self.receipt))
        self.assertEqual(self.receipt["pilot_status"], "AUTHORIZED_NOT_STARTED")

    def test_pcg01_remains_blocked_after_start_authorization(self):
        self.assertEqual(validate_pilot2_pre_candidate_gate(self.gate), [])
        self.assertTrue(self.gate["prerequisites"]["protocol_decisions_approved"])
        self.assertTrue(self.gate["prerequisites"]["start_authorization_bound"])
        for key in (
            "source_census_frozen",
            "intake_registry_valid",
            "intake_eligible_for_s1",
            "s1_source_manifest_frozen",
            "s1_candidate_exposure_unexposed",
            "s1_manifest_predates_candidate_processing",
        ):
            self.assertFalse(self.gate["prerequisites"][key], key)
        self.assertEqual(self.gate["gate_status"], "BLOCKED")
        self.assertFalse(candidate_case_processing_allowed(self.gate))

    def test_start_seal_does_not_fabricate_real_execution(self):
        state = self.seal["execution_state"]
        self.assertEqual(state["source_census"], "NOT_FROZEN")
        self.assertEqual(state["intake_registry"], "NOT_CREATED")
        self.assertEqual(state["s1_source_manifest"], "NOT_CREATED")
        self.assertEqual(state["candidate_processing"], "NOT_STARTED")
        self.assertEqual(state["prediction_lock"], "NOT_CREATED")
        self.assertEqual(state["outcome_collection"], "NOT_STARTED")


if __name__ == "__main__":
    unittest.main()
