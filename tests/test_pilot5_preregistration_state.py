import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class Pilot5PreregistrationStateTests(unittest.TestCase):
    def load(self,name):
        return json.loads((ROOT/"docs/research"/name).read_text(encoding="utf-8"))

    def test_d01_to_d12_are_fresh_pending_and_start_is_closed(self):
        r=self.load("pilot5-decision-receipt.template.json")
        self.assertEqual(r["protocol_decision_status"],"PENDING_ITEM_APPROVAL")
        self.assertEqual(r["pilot_status"],"NOT_STARTED")
        self.assertEqual([x["status"] for x in r["decisions"]],["PENDING"]*12)
        self.assertFalse(r["pilot_start_authorization"]["authorized"])

    def test_enum_agg_auth_are_fresh_pending(self):
        for name,decision in (
            ("pilot5-enumeration-decision.v1.json","ENUM-01"),
            ("pilot5-aggregation-decision.v1.json","AGG-01"),
            ("pilot5-downstream-authority-decision.v1.json","AUTH-01"),
        ):
            r=self.load(name)
            self.assertEqual(r["pilot_id"],"Pilot-5")
            self.assertEqual(r["decision_id"],decision)
            self.assertEqual(r["status"],"PENDING_HUMAN_APPROVAL")
            self.assertFalse(r["start_authorization_effect"])

    def test_auth01_selection_does_not_use_pilot4_private_results(self):
        r=self.load("pilot5-downstream-authority-decision.v1.json")
        self.assertTrue(r["pilot4_defect_class_used"])
        self.assertFalse(r["pilot4_observed_snapshot_or_claim_results_used_for_rule_selection"])
        self.assertFalse(r["best_snapshot_selection_allowed"])
        self.assertFalse(r["confidence_repetition_uplift_allowed"])
        self.assertFalse(r["specificity_repetition_uplift_allowed"])
        self.assertFalse(r["synthetic_single_source_authority_allowed"])

    def test_window_is_only_proposed_and_non_overlapping(self):
        r=self.load("pilot5-window-policy.proposed.v1.json")
        self.assertEqual(r["status"],"PROPOSED_NOT_APPROVED")
        self.assertFalse(r["start_authorized"])
        self.assertEqual(r["outcome_window_start"],"2027-07-01T00:00:00+08:00")
        self.assertEqual(r["outcome_window_end"],"2027-08-31T23:59:59+08:00")
        self.assertFalse(r["prior_pilot_private_case_observations_used_for_window_selection"])

    def test_pre_candidate_gate_is_fail_closed(self):
        r=self.load("pilot5-pre-candidate-gate.template.json")
        self.assertEqual(r["gate_status"],"BLOCKED")
        self.assertFalse(r["candidate_case_processing_allowed"])
        self.assertFalse(any(r["prerequisites"].values()))
        self.assertTrue(all(v is None for v in r["public_bindings"].values()))
        self.assertFalse(r["manual_override_allowed"])
        self.assertFalse(r["private_material_disclosed"])

if __name__=="__main__":
    unittest.main()
