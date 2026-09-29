import json
from pathlib import Path
import unittest
from tools.validate_prospective_pilot_decision import validate_decision_receipt,pilot_start_allowed
from tools.validate_pilot6_pre_candidate_gate import validate_pilot6_pre_candidate_gate,candidate_case_processing_allowed
from tools.pilot6_canonical_snapshot_manifest_gate import CANONICAL_PRE_EFA_MANIFEST_GATE_PROFILE,CANONICAL_PRE_EFA_MANIFEST_GATE_RULE
ROOT=Path(__file__).resolve().parents[1]
class Pilot6PreregistrationStateTests(unittest.TestCase):
 def load(self,name): return json.loads((ROOT/"docs/research"/name).read_text(encoding="utf-8"))
 def test_d01_d12_pending_and_start_closed(self):
  r=self.load("pilot6-decision-receipt.template.json");self.assertEqual(validate_decision_receipt(r),[]);self.assertEqual(r["protocol_decision_status"],"PENDING_ITEM_APPROVAL");self.assertEqual(r["pilot_status"],"NOT_STARTED");self.assertTrue(all(x["status"]=="PENDING" for x in r["decisions"]));self.assertFalse(pilot_start_allowed(r))
 def test_all_special_decisions_are_fresh_pending(self):
  for name in ("pilot6-enumeration-decision.v1.json","pilot6-manifest-decision.v1.json","pilot6-aggregation-decision.v1.json","pilot6-downstream-authority-decision.v1.json"):
   d=self.load(name);self.assertEqual(d["pilot_id"],"Pilot-6");self.assertIn("PENDING",d["status"]);self.assertFalse(d["start_authorization_effect"]);self.assertFalse(d["manual_override_allowed"]);self.assertFalse(d["promotion_allowed"])
  m=self.load("pilot6-manifest-decision.v1.json");self.assertEqual(m["proposed_profile"],CANONICAL_PRE_EFA_MANIFEST_GATE_PROFILE);self.assertEqual(m["proposed_rule"],CANONICAL_PRE_EFA_MANIFEST_GATE_RULE);self.assertFalse(m["retrospective_repair_after_efa_allowed"])
 def test_window_is_new_and_unapproved(self):
  w=self.load("pilot6-window-policy.proposed.v1.json");self.assertEqual(w["status"],"PROPOSED_PENDING_HUMAN_APPROVAL");self.assertEqual(w["outcome_window_start"],"2027-09-01T00:00:00+08:00");self.assertEqual(w["outcome_window_end"],"2027-10-31T23:59:59+08:00");self.assertFalse(w["prior_pilot_private_case_observations_used_for_window_selection"]);self.assertFalse(w["promotion_allowed"])
 def test_pcg_defaults_blocked_and_binds_manifest_decision_later(self):
  g=self.load("pilot6-pre-candidate-gate.template.json");self.assertEqual(validate_pilot6_pre_candidate_gate(g),[]);self.assertEqual(g["gate_status"],"BLOCKED");self.assertFalse(candidate_case_processing_allowed(g));self.assertFalse(g["prerequisites"]["manifest01_approved"]);self.assertIsNone(g["public_bindings"]["manifest_decision_sha256"]);self.assertFalse(g["private_material_disclosed"]);self.assertFalse(g["manual_override_allowed"])
if __name__=="__main__":unittest.main()
