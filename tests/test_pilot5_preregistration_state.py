import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class Pilot5ApprovalStateTests(unittest.TestCase):
    def load(self,name):
        return json.loads((ROOT/"docs/research"/name).read_text(encoding="utf-8"))

    def test_all_human_decisions_are_approved_but_start_is_closed(self):
        r=self.load("pilot5-decision-receipt.template.json")
        self.assertEqual(r["protocol_decision_status"],"ALL_ITEMS_APPROVED")
        self.assertEqual(r["pilot_status"],"READY_FOR_START_AUTHORIZATION")
        self.assertTrue(all(row["status"]=="APPROVED" for row in r["decisions"]))
        self.assertTrue(all(row["approver_role"]=="human_decision_owner" for row in r["decisions"]))
        self.assertFalse(r["pilot_start_authorization"]["authorized"])
        self.assertIsNone(r["pilot_start_authorization"]["candidate_commit"])

    def test_enum_agg_auth_are_fresh_approved_without_start_effect(self):
        enum=self.load("pilot5-enumeration-decision.v1.json")
        agg=self.load("pilot5-aggregation-decision.v1.json")
        auth=self.load("pilot5-downstream-authority-decision.v1.json")
        for row in (enum,agg,auth):
            self.assertEqual(row["pilot_id"],"Pilot-5")
            self.assertEqual(row["status"],"APPROVED")
            self.assertEqual(row["approved_by_role"],"human_decision_owner")
            self.assertFalse(row["start_authorization_effect"])
            self.assertFalse(row["manual_override_allowed"])
            self.assertFalse(row["promotion_allowed"])
        self.assertFalse(agg["inherited_approval_from_prior_pilots"])
        self.assertFalse(auth["best_snapshot_selection_allowed"])
        self.assertFalse(auth["confidence_repetition_uplift_allowed"])
        self.assertFalse(auth["specificity_repetition_uplift_allowed"])
        self.assertFalse(auth["synthetic_single_source_authority_allowed"])

    def test_window_is_approved_pending_start_only(self):
        w=self.load("pilot5-window-policy.v1.json")
        self.assertEqual(w["status"],"APPROVED_PENDING_START_AUTHORIZATION")
        self.assertEqual(w["approved_by_role"],"human_decision_owner")
        self.assertEqual(w["approved_at"],"2026-09-29T11:43:28+08:00")
        self.assertFalse(w["start_authorized"])
        self.assertFalse(w["promotion_allowed"])

    def test_approval_timestamps_are_consistent(self):
        r=self.load("pilot5-decision-receipt.template.json")
        enum=self.load("pilot5-enumeration-decision.v1.json")
        agg=self.load("pilot5-aggregation-decision.v1.json")
        auth=self.load("pilot5-downstream-authority-decision.v1.json")
        w=self.load("pilot5-window-policy.v1.json")
        stamp="2026-09-29T11:43:28+08:00"
        self.assertEqual({row["approved_at"] for row in r["decisions"]},{stamp})
        self.assertEqual(enum["approved_at"],stamp)
        self.assertEqual(agg["approved_at"],stamp)
        self.assertEqual(auth["approved_at"],stamp)
        self.assertEqual(w["approved_at"],stamp)

    def test_no_approval_file_authorizes_candidate_processing(self):
        gate=self.load("pilot5-pre-candidate-gate.template.json")
        self.assertEqual(gate["gate_status"],"BLOCKED")
        self.assertFalse(gate["candidate_case_processing_allowed"])
        self.assertFalse(gate["prerequisites"]["start_authorization_bound"])
        self.assertFalse(gate["private_material_disclosed"])
        self.assertFalse(gate["manual_override_allowed"])

if __name__=="__main__":
    unittest.main()
