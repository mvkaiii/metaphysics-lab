import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
CP=ROOT/"docs/research/pilot5-structural-snapshot-checkpoint.v1.json"
class Pilot5StructuralSnapshotCheckpointTests(unittest.TestCase):
 def setUp(self): self.cp=json.loads(CP.read_text(encoding="utf-8"))
 def test_manifest_is_frozen_before_efa(self):
  self.assertEqual(self.cp["checkpoint_status"],"STRUCTURAL_SNAPSHOT_MANIFEST_FROZEN")
  self.assertEqual(self.cp["process_stage"],"STRUCTURAL_SNAPSHOT_MANIFEST")
  self.assertEqual(self.cp["governance"]["pcg_status"],"READY_BEFORE_CANDIDATE_PROCESSING")
  self.assertTrue(self.cp["candidate_execution"]["processing_started_only_after_pcg_ready"])
  self.assertTrue(self.cp["manifest_contract"]["complete_ordered_snapshot_manifest_created"])
  self.assertTrue(self.cp["manifest_contract"]["frozen_before_efa_materialization"])
  self.assertEqual(self.cp["execution_state"]["efa_census"],"NOT_STARTED_AT_CHECKPOINT")
 def test_enum01_cannot_be_rewritten_after_exposure(self):
  e=self.cp["enumeration_contract"]
  self.assertFalse(e["post_exposure_segment_merge_allowed"]);self.assertFalse(e["post_exposure_segment_split_allowed"]);self.assertFalse(e["post_exposure_segment_substitution_allowed"])
  self.assertFalse(self.cp["manifest_contract"]["efa_content_used_to_define_snapshot_census"])
 def test_auth01_is_already_start_bound_but_not_executed(self):
  self.assertEqual(self.cp["governance"]["downstream_authority_decision_status"],"AUTH-01_APPROVED_AND_START_BOUND")
  self.assertEqual(self.cp["execution_state"]["segment_aware_window_authority"],"NOT_CREATED")
  self.assertEqual(self.cp["execution_state"]["prediction_lock"],"NOT_CREATED")
 def test_public_checkpoint_excludes_private_observations(self):
  self.assertTrue(all(v is False for v in self.cp["privacy"].values()))
  s=json.dumps(self.cp,ensure_ascii=False).lower()
  for forbidden in ('"snapshot_count":','"snapshot_id":','"snapshot_manifest_digest":','"enumeration_digest":','"structural_state_digest":','"birth_date":','"opaque_case_id":'):
   self.assertNotIn(forbidden,s)
 def test_blind_side_and_outcome_remain_closed(self):
  self.assertFalse(self.cp["candidate_execution"]["blind_side_material_read"])
  self.assertEqual(self.cp["execution_state"]["outcome_collection"],"NOT_STARTED")
  self.assertFalse(self.cp["interpretation"]["predictive_validity_evidence_created"])
if __name__=="__main__":unittest.main()
