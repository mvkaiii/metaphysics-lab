import json
from pathlib import Path
import unittest

from tools.validate_pilot2_pre_candidate_gate import (
    candidate_case_processing_allowed,
    validate_pilot2_pre_candidate_gate,
)


ROOT = Path(__file__).resolve().parents[1]
READY_PATH = ROOT / "docs" / "research" / "pilot2-pcg01-ready-receipt.v1.json"
BLOCKED_PATH = ROOT / "docs" / "research" / "pilot2-pre-candidate-gate.template.json"


class Pilot2Pcg01ReadinessTests(unittest.TestCase):
    def test_ready_receipt_opens_candidate_processing_gate(self):
        ready = json.loads(READY_PATH.read_text(encoding="utf-8"))
        self.assertEqual(validate_pilot2_pre_candidate_gate(ready), [])
        self.assertTrue(all(ready["prerequisites"].values()))
        self.assertEqual(ready["gate_status"], "READY")
        self.assertTrue(candidate_case_processing_allowed(ready))

    def test_after_start_template_preserves_prior_blocked_state(self):
        blocked = json.loads(BLOCKED_PATH.read_text(encoding="utf-8"))
        self.assertEqual(validate_pilot2_pre_candidate_gate(blocked), [])
        self.assertEqual(blocked["gate_status"], "BLOCKED")
        self.assertFalse(candidate_case_processing_allowed(blocked))


if __name__ == "__main__":
    unittest.main()
