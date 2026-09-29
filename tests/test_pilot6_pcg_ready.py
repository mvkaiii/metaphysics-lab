import json
from pathlib import Path
import unittest
from tools.validate_pilot6_pre_candidate_gate import candidate_case_processing_allowed,validate_pilot6_pre_candidate_gate
ROOT=Path(__file__).resolve().parents[1]
BLOCKED=ROOT/"docs/research/pilot6-pre-candidate-gate.template.json"
READY=ROOT/"docs/research/pilot6-pre-candidate-gate.ready.v1.json"
CP=ROOT/"docs/research/pilot6-pcg-ready-checkpoint.v1.json"
class Pilot6PcgReadyTests(unittest.TestCase):
 def setUp(self):
  self.blocked=json.loads(BLOCKED.read_text(encoding="utf-8"));self.ready=json.loads(READY.read_text(encoding="utf-8"));self.cp=json.loads(CP.read_text(encoding="utf-8"))
 def test_start_template_remains_blocked(self):
  self.assertEqual(validate_pilot6_pre_candidate_gate(self.blocked),[]);self.assertFalse(candidate_case_processing_allowed(self.blocked))
 def test_ready_receipt_validates_and_opens_gate(self):
  self.assertEqual(validate_pilot6_pre_candidate_gate(self.ready),[]);self.assertTrue(all(self.ready["prerequisites"].values()));self.assertTrue(candidate_case_processing_allowed(self.ready));self.assertFalse(self.ready["private_material_disclosed"]);self.assertFalse(self.ready["manual_override_allowed"])
 def test_ready_preserves_start_bindings_including_manifest01(self):
  self.assertEqual(self.ready["public_bindings"],self.blocked["public_bindings"])
  b=self.ready["public_bindings"];self.assertIsNotNone(b["manifest_decision_sha256"]);self.assertIsNotNone(b["manifest_gate_profile"]);self.assertIsNotNone(b["manifest_gate_rule"])
 def test_public_ready_artifacts_exclude_private_material(self):
  s=json.dumps({"ready":self.ready,"checkpoint":self.cp},ensure_ascii=False).lower()
  for forbidden in ('"opaque_case_id":','"birth_data":','"source_census_digest":','"source_manifest_digest":','"private_provenance_digest":','"prediction_text":','"outcome_text":'):
   self.assertNotIn(forbidden,s)
 def test_checkpoint_records_ready_before_candidate_processing(self):
  self.assertEqual(self.cp["checkpoint_status"],"PCG_READY");self.assertEqual(self.cp["governance"]["canonical_manifest_decision_status"],"MANIFEST-01_APPROVED");self.assertEqual(self.cp["governance"]["intake_status"],"ELIGIBLE_FOR_S1_SOURCE");self.assertEqual(self.cp["execution_state"]["candidate_processing"],"NOT_STARTED_AT_CHECKPOINT");self.assertEqual(self.cp["execution_state"]["manifest01_receipt"],"NOT_CREATED")
 def test_fresh_prediction_context_is_required(self):
  h=self.cp["prediction_context_hygiene"];self.assertTrue(h["governance_search_returned_blind_side_snippet"]);self.assertFalse(h["frozen_candidate_runtime_executed"]);self.assertFalse(h["candidate_case_processing_started"]);self.assertTrue(h["fresh_isolated_prediction_context_required_before_candidate_processing"])
if __name__=="__main__":unittest.main()
