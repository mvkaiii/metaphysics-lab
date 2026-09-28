import json
from pathlib import Path
import unittest

from tools.validate_prospective_pilot_decision import (
    pilot_start_allowed,
    validate_decision_receipt,
)
from tools.pilot4_structural_snapshot_enumerator import (
    STRUCTURAL_SNAPSHOT_ENUMERATION_PROFILE,
    STRUCTURAL_SNAPSHOT_ENUMERATION_RULE,
)
from tools.pilot3_yearly_claim_universe import (
    MULTI_SEGMENT_YEARLY_UNIVERSE_PROFILE,
    MULTI_SEGMENT_YEARLY_UNIVERSE_RULE,
)


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "docs" / "research" / "pilot4-decision-receipt.template.json"
ENUM = ROOT / "docs" / "research" / "pilot4-enumeration-decision.v1.json"
AGG = ROOT / "docs" / "research" / "pilot4-aggregation-decision.v1.json"
WINDOW = ROOT / "docs" / "research" / "pilot4-window-policy.v1.json"


class Pilot4ApprovalStateTests(unittest.TestCase):
    def setUp(self):
        self.receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
        self.enum = json.loads(ENUM.read_text(encoding="utf-8"))
        self.agg = json.loads(AGG.read_text(encoding="utf-8"))
        self.window = json.loads(WINDOW.read_text(encoding="utf-8"))

    def test_d01_to_d12_are_approved_but_start_remains_closed(self):
        self.assertEqual(validate_decision_receipt(self.receipt), [])
        self.assertEqual(self.receipt["protocol_decision_status"], "ALL_ITEMS_APPROVED")
        self.assertEqual(self.receipt["pilot_status"], "READY_FOR_START_AUTHORIZATION")
        self.assertTrue(all(row["status"] == "APPROVED" for row in self.receipt["decisions"]))
        self.assertFalse(self.receipt["pilot_start_authorization"]["authorized"])
        self.assertFalse(pilot_start_allowed(self.receipt))

    def test_enum01_is_approved_mandatory_and_has_no_start_effect(self):
        self.assertEqual(self.enum["pilot_id"], "Pilot-4")
        self.assertEqual(self.enum["decision_id"], "ENUM-01")
        self.assertEqual(self.enum["status"], "APPROVED")
        self.assertEqual(self.enum["approved_profile"], STRUCTURAL_SNAPSHOT_ENUMERATION_PROFILE)
        self.assertEqual(self.enum["approved_rule"], STRUCTURAL_SNAPSHOT_ENUMERATION_RULE)
        self.assertTrue(self.enum["mandatory"])
        self.assertFalse(self.enum["manual_override_allowed"])
        self.assertFalse(self.enum["start_authorization_effect"])
        self.assertFalse(self.enum["pilot2_observed_case_results_used_for_rule_selection"])
        self.assertFalse(self.enum["pilot3_observed_case_results_used_for_rule_selection"])
        self.assertFalse(self.enum["candidate_case_exposure_used_for_rule_selection"])

    def test_agg01_is_fresh_approved_and_not_inherited(self):
        self.assertEqual(self.agg["pilot_id"], "Pilot-4")
        self.assertEqual(self.agg["decision_id"], "AGG-01")
        self.assertEqual(self.agg["status"], "APPROVED")
        self.assertEqual(self.agg["approved_profile"], MULTI_SEGMENT_YEARLY_UNIVERSE_PROFILE)
        self.assertEqual(self.agg["approved_rule"], MULTI_SEGMENT_YEARLY_UNIVERSE_RULE)
        self.assertFalse(self.agg["inherited_approval_from_pilot3"])
        self.assertFalse(self.agg["pilot2_claim_set_observations_used_for_rule_selection"])
        self.assertFalse(self.agg["pilot3_claim_set_observations_used_for_rule_selection"])
        self.assertFalse(self.agg["start_authorization_effect"])

    def test_window_is_approved_but_not_start_authorized(self):
        self.assertEqual(self.window["status"], "APPROVED_PENDING_START_AUTHORIZATION")
        self.assertEqual(self.window["approved_at"], "2026-09-28T21:41:06+08:00")
        self.assertEqual(self.window["timezone"], "Asia/Taipei")
        self.assertEqual(self.window["outcome_window_start"], "2027-05-01T00:00:00+08:00")
        self.assertEqual(self.window["outcome_window_end"], "2027-06-30T23:59:59+08:00")
        self.assertEqual(self.window["requested_scopes"], ["yearly", "monthly"])
        self.assertFalse(self.window["start_authorized"])
        self.assertFalse(self.window["promotion_allowed"])

    def test_all_approval_timestamps_are_consistent(self):
        approval = "2026-09-28T21:41:06+08:00"
        self.assertEqual({row["approved_at"] for row in self.receipt["decisions"]}, {approval})
        self.assertEqual(self.enum["approved_at"], approval)
        self.assertEqual(self.agg["approved_at"], approval)
        self.assertEqual(self.window["approved_at"], approval)


if __name__ == "__main__":
    unittest.main()
