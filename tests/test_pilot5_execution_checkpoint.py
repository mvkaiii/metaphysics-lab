import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
CP=ROOT/"docs/research/pilot5-execution-checkpoint.v1.json"
class Pilot5ExecutionCheckpointTests(unittest.TestCase):
 def setUp(self): self.cp=json.loads(CP.read_text(encoding="utf-8"))
 def test_halt_is_before_agg_auth_and_prediction(self):
  self.assertEqual(self.cp["checkpoint_status"],"HALTED_NON_QUALIFYING")
  self.assertEqual(self.cp["process_stage"],"SNAPSHOT_MANIFEST_CANONICAL_VALIDATION_BEFORE_AGGREGATION")
  self.assertEqual(self.cp["deviation_code"],"PRE_EFA_SNAPSHOT_MANIFEST_SCHEMA_INVALID")
  s=self.cp["execution_state"]
  self.assertEqual(s["structural_snapshot_rows"],"FROZEN_BEFORE_EFA_PRIVATE")
  self.assertEqual(s["canonical_snapshot_manifest_validation"],"FAILED_CLOSED")
  self.assertEqual(s["claim_universe_lock"],"NOT_CREATED")
  self.assertEqual(s["segment_aware_window_authority"],"NOT_CREATED")
  self.assertEqual(s["prediction_lock"],"NOT_CREATED")
 def test_no_retrospective_manifest_rebuild_is_allowed(self):
  d=self.cp["deviation_boundary"]
  self.assertFalse(d["snapshot_membership_or_order_changed_after_efa"])
  self.assertFalse(d["private_structural_digests_changed_after_efa"])
  self.assertFalse(d["invalid_serialization_used_efa_content_for_selection"])
  self.assertFalse(d["canonical_manifest_digest_frozen_before_efa"])
  self.assertFalse(d["retrospective_manifest_rebuild_allowed"])
  self.assertFalse(d["agg01_execution_allowed"])
  self.assertFalse(d["auth01_execution_allowed"])
  self.assertFalse(d["prediction_lock_allowed"])
 def test_blind_side_and_outcomes_remain_unread(self):
  self.assertTrue(all(v is False for v in self.cp["blindness"].values()))
  self.assertFalse(self.cp["interpretation"]["predictive_validity_evidence_created"])
  self.assertFalse(self.cp["interpretation"]["qualification_evidence_created"])
 def test_public_checkpoint_contains_no_private_observations(self):
  self.assertTrue(all(v is False for v in self.cp["privacy"].values()))
  s=json.dumps(self.cp,ensure_ascii=False).lower()
  for forbidden in ('"opaque_case_id":','"snapshot_count":','"snapshot_id":','"structural_state_digest":','"claim_id":','"event_family_attribution_digest":','"birth_date":','"birth_time":'):
   self.assertNotIn(forbidden,s)
 def test_retry_requires_new_pilot(self):
  n=self.cp["next_action"]
  self.assertEqual(n["pilot5_resume"],"PROHIBITED")
  self.assertEqual(n["replacement_case_under_pilot5"],"PROHIBITED")
  self.assertEqual(n["retry_requires"],"NEW_PILOT_ID_OR_PROTOCOL_VERSION")
if __name__=="__main__":unittest.main()
