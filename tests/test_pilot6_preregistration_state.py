import json
from pathlib import Path
import unittest
from tools.validate_prospective_pilot_decision import validate_decision_receipt,pilot_start_allowed
from tools.validate_pilot6_pre_candidate_gate import validate_pilot6_pre_candidate_gate,candidate_case_processing_allowed
ROOT=Path(__file__).resolve().parents[1]
class Pilot6ApprovalStateTests(unittest.TestCase):
 def load(self,name): return json.loads((ROOT/"docs/research"/name).read_text(encoding="utf-8"))
 def test_d01_d12_approved_and_start_authorized(self):
  r=self.load("pilot6-decision-receipt.template.json");self.assertEqual(validate_decision_receipt(r),[]);self.assertEqual(r["protocol_decision_status"],"ALL_ITEMS_APPROVED");self.assertEqual(r["pilot_status"],"AUTHORIZED_NOT_STARTED");self.assertTrue(all(x["status"]=="APPROVED" for x in r["decisions"]));self.assertTrue(all(x["approver_role"]=="human_decision_owner" for x in r["decisions"]));self.assertTrue(pilot_start_allowed(r));self.assertTrue(r["pilot_start_authorization"]["authorized"]);self.assertEqual(r["pilot_start_authorization"]["authorized_at"],"2026-09-29T14:21:43+08:00")
 def test_special_decisions_approved_without_start_effect(self):
  rows=[self.load(n) for n in ("pilot6-enumeration-decision.v1.json","pilot6-manifest-decision.v1.json","pilot6-aggregation-decision.v1.json","pilot6-downstream-authority-decision.v1.json")]
  for d in rows:
   self.assertEqual(d["pilot_id"],"Pilot-6");self.assertEqual(d["status"],"APPROVED");self.assertEqual(d["approved_by_role"],"human_decision_owner");self.assertEqual(d["approved_at"],"2026-09-29T12:39:46+08:00");self.assertFalse(d["start_authorization_effect"]);self.assertFalse(d["manual_override_allowed"]);self.assertFalse(d["promotion_allowed"])
  self.assertFalse(rows[1]["retrospective_repair_after_efa_allowed"])
  self.assertFalse(rows[2]["inherited_approval_from_prior_pilots"])
  self.assertFalse(rows[3]["best_snapshot_selection_allowed"])
  self.assertFalse(rows[3]["synthetic_single_source_authority_allowed"])
 def test_window_approved_and_start_authorized(self):
  w=self.load("pilot6-window-policy.v1.json");self.assertEqual(w["status"],"APPROVED_START_AUTHORIZED");self.assertEqual(w["approved_by_role"],"human_decision_owner");self.assertEqual(w["approved_at"],"2026-09-29T12:39:46+08:00");self.assertTrue(w["start_authorized"]);self.assertEqual(w["start_authorized_at"],"2026-09-29T14:21:43+08:00");self.assertFalse(w["promotion_allowed"])
 def test_pcg_records_start_binding_but_remains_blocked(self):
  g=self.load("pilot6-pre-candidate-gate.template.json");self.assertEqual(validate_pilot6_pre_candidate_gate(g),[]);self.assertTrue(all(g["prerequisites"][k] for k in ("protocol_decisions_approved","enum01_approved","manifest01_approved","agg01_approved","auth01_approved")));self.assertTrue(g["prerequisites"]["start_authorization_bound"]);self.assertEqual(g["gate_status"],"BLOCKED");self.assertFalse(candidate_case_processing_allowed(g));self.assertFalse(g["candidate_case_processing_allowed"])
 def test_approval_timestamps_consistent(self):
  r=self.load("pilot6-decision-receipt.template.json");stamp="2026-09-29T12:39:46+08:00";self.assertEqual({x["approved_at"] for x in r["decisions"]},{stamp});self.assertEqual(self.load("pilot6-window-policy.v1.json")["approved_at"],stamp)
if __name__=="__main__":unittest.main()
