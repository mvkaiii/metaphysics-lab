import json
from pathlib import Path
import unittest

from tools.validate_prospective_pilot_decision import (
    pilot_start_allowed,
    validate_decision_receipt,
)
from tools.pilot3_yearly_claim_universe import (
    MULTI_SEGMENT_YEARLY_UNIVERSE_PROFILE,
    MULTI_SEGMENT_YEARLY_UNIVERSE_RULE,
)


ROOT = Path(__file__).resolve().parents[1]
RECEIPT_PATH = ROOT / "docs" / "research" / "pilot3-decision-receipt.template.json"
AGG_PATH = ROOT / "docs" / "research" / "pilot3-aggregation-decision.v1.json"
WINDOW_PATH = ROOT / "docs" / "research" / "pilot3-window-policy.v1.json"


class Pilot3ApprovalStateTests(unittest.TestCase):
    def setUp(self):
        self.receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
        self.agg = json.loads(AGG_PATH.read_text(encoding="utf-8"))
        self.window = json.loads(WINDOW_PATH.read_text(encoding="utf-8"))

    def test_d01_to_d12_and_start_are_authorized(self):
        self.assertEqual(validate_decision_receipt(self.receipt), [])
        self.assertEqual(self.receipt["protocol_decision_status"], "ALL_ITEMS_APPROVED")
        self.assertEqual(self.receipt["pilot_status"], "AUTHORIZED_NOT_STARTED")
        self.assertTrue(all(row["status"] == "APPROVED" for row in self.receipt["decisions"]))
        self.assertTrue(self.receipt["pilot_start_authorization"]["authorized"])
        self.assertTrue(pilot_start_allowed(self.receipt))

    def test_agg01_is_approved_mandatory_and_has_no_start_effect(self):
        self.assertEqual(self.agg["pilot_id"], "Pilot-3")
        self.assertEqual(self.agg["decision_id"], "AGG-01")
        self.assertEqual(self.agg["status"], "APPROVED")
        self.assertEqual(
            self.agg["approved_profile"],
            MULTI_SEGMENT_YEARLY_UNIVERSE_PROFILE,
        )
        self.assertEqual(
            self.agg["approved_rule"],
            MULTI_SEGMENT_YEARLY_UNIVERSE_RULE,
        )
        self.assertTrue(self.agg["mandatory"])
        self.assertFalse(self.agg["manual_override_allowed"])
        self.assertFalse(self.agg["start_authorization_effect"])
        self.assertFalse(
            self.agg["pilot2_claim_set_observations_used_for_rule_selection"]
        )

    def test_window_is_approved_and_start_bound_without_promotion(self):
        self.assertEqual(self.window["pilot_id"], "Pilot-3")
        self.assertEqual(self.window["status"], "APPROVED_START_AUTHORIZED")
        self.assertTrue(self.window["start_authorized"])
        self.assertEqual(self.window["timezone"], "Asia/Taipei")
        self.assertEqual(
            self.window["outcome_window_start"],
            "2027-03-01T00:00:00+08:00",
        )
        self.assertEqual(
            self.window["outcome_window_end"],
            "2027-04-30T23:59:59+08:00",
        )
        self.assertEqual(
            self.window["aggregation_profile"],
            MULTI_SEGMENT_YEARLY_UNIVERSE_PROFILE,
        )
        self.assertEqual(
            self.window["aggregation_rule"],
            MULTI_SEGMENT_YEARLY_UNIVERSE_RULE,
        )
        self.assertFalse(self.window["promotion_allowed"])

    def test_approval_and_start_timestamps_are_separate(self):
        approval = "2026-09-28T13:57:00+08:00"
        start = "2026-09-28T14:12:31+08:00"
        self.assertEqual(
            {row["approved_at"] for row in self.receipt["decisions"]},
            {approval},
        )
        self.assertEqual(self.agg["approved_at"], approval)
        self.assertEqual(self.window["approved_at"], approval)
        self.assertEqual(
            self.receipt["pilot_start_authorization"]["authorized_at"],
            start,
        )
        self.assertEqual(self.window["start_authorized_at"], start)


if __name__ == "__main__":
    unittest.main()
