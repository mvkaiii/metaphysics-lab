import json
from pathlib import Path
import unittest

from tools.validate_prospective_pilot_decision import (
    pilot_start_allowed,
    validate_decision_receipt,
)
from tools.validate_pilot2_pre_candidate_gate import (
    candidate_case_processing_allowed,
    validate_pilot2_pre_candidate_gate,
)


ROOT = Path(__file__).resolve().parents[1]
RECEIPT_PATH = ROOT / "docs" / "research" / "pilot2-decision-receipt.template.json"
PCG_DECISION_PATH = ROOT / "docs" / "research" / "pilot2-pcg01-decision.v1.json"
GATE_PATH = ROOT / "docs" / "research" / "pilot2-pre-candidate-gate.template.json"


class Pilot2ApprovalStateTests(unittest.TestCase):
    def setUp(self):
        self.receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
        self.pcg = json.loads(PCG_DECISION_PATH.read_text(encoding="utf-8"))
        self.gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))

    def test_d01_to_d12_are_approved_but_start_is_not_authorized(self):
        self.assertEqual(validate_decision_receipt(self.receipt), [])
        self.assertEqual(self.receipt["protocol_decision_status"], "ALL_ITEMS_APPROVED")
        self.assertEqual(self.receipt["pilot_status"], "READY_FOR_START_AUTHORIZATION")
        self.assertTrue(all(row["status"] == "APPROVED" for row in self.receipt["decisions"]))
        self.assertFalse(self.receipt["pilot_start_authorization"]["authorized"])
        self.assertFalse(pilot_start_allowed(self.receipt))

    def test_pcg01_is_mandatory_and_has_no_bypass(self):
        self.assertEqual(self.pcg["pilot_id"], "Pilot-2")
        self.assertEqual(self.pcg["decision_id"], "PCG-01")
        self.assertEqual(self.pcg["status"], "APPROVED")
        self.assertTrue(self.pcg["mandatory"])
        self.assertFalse(self.pcg["manual_override_allowed"])
        self.assertFalse(self.pcg["start_authorization_effect"])

    def test_public_gate_reflects_approval_but_remains_blocked(self):
        self.assertEqual(validate_pilot2_pre_candidate_gate(self.gate), [])
        self.assertTrue(self.gate["prerequisites"]["protocol_decisions_approved"])
        for key, value in self.gate["prerequisites"].items():
            if key != "protocol_decisions_approved":
                self.assertFalse(value, key)
        self.assertEqual(self.gate["gate_status"], "BLOCKED")
        self.assertFalse(self.gate["candidate_case_processing_allowed"])
        self.assertFalse(candidate_case_processing_allowed(self.gate))

    def test_no_real_start_bindings_exist_yet(self):
        self.assertFalse(self.gate["prerequisites"]["start_authorization_bound"])
        self.assertTrue(all(value is None for value in self.gate["public_bindings"].values()))


if __name__ == "__main__":
    unittest.main()
