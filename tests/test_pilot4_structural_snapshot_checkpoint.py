import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
CP=ROOT/"docs/research/pilot4-structural-snapshot-checkpoint.v1.json"

class Pilot4StructuralSnapshotCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.cp=json.loads(CP.read_text(encoding="utf-8"))

    def test_manifest_is_frozen_before_efa(self):
        self.assertEqual(self.cp["checkpoint_status"],"STRUCTURAL_SNAPSHOT_MANIFEST_FROZEN")
        self.assertEqual(self.cp["process_stage"],"STRUCTURAL_SNAPSHOT_MANIFEST")
        self.assertTrue(self.cp["governance"]["pcg_status"].startswith("READY_BEFORE_"))
        self.assertTrue(self.cp["candidate_execution"]["processing_started_only_after_pcg_ready"])
        self.assertTrue(self.cp["manifest_contract"]["complete_ordered_snapshot_manifest_created"])
        self.assertTrue(self.cp["manifest_contract"]["frozen_before_efa_materialization"])
        self.assertEqual(self.cp["execution_state"]["efa_census"],"NOT_STARTED_AT_CHECKPOINT")

    def test_enum01_cannot_be_rewritten_after_exposure(self):
        enum=self.cp["enumeration_contract"]
        self.assertEqual(enum["profile"],"lin_tianji_complete_structural_snapshot_enumerator_v1")
        self.assertEqual(enum["rule"],"complete_union_of_authoritative_yearly_monthly_time_boundaries_no_post_exposure_merge")
        self.assertFalse(enum["post_exposure_segment_merge_allowed"])
        self.assertFalse(enum["post_exposure_segment_split_allowed"])
        self.assertFalse(enum["post_exposure_segment_substitution_allowed"])
        self.assertFalse(self.cp["manifest_contract"]["efa_content_used_to_define_snapshot_census"])

    def test_structural_digest_uses_existing_runtime_authority(self):
        self.assertEqual(
            self.cp["manifest_contract"]["structural_state_digest_authority"],
            "CANONICAL_STRUCTURAL_INTERPRETATION_INTERPRETATION_DIGEST",
        )
        self.assertEqual(
            self.cp["manifest_contract"]["structural_state_digest_profile_source"],
            "FROZEN_CANDIDATE_RUNTIME",
        )

    def test_public_checkpoint_contains_no_private_snapshot_observations(self):
        privacy=self.cp["privacy"]
        self.assertTrue(all(value is False for value in privacy.values()))
        serialized=json.dumps(self.cp,ensure_ascii=False).lower()
        for forbidden in (
            '"opaque_case_id":','"snapshot_count":','"snapshot_id":',
            '"snapshot_manifest_digest":','"enumeration_digest":',
            '"structural_state_digest":','"birth_date":','"birth_time":'
        ):
            self.assertNotIn(forbidden,serialized)

    def test_no_prediction_or_outcome_evidence_created(self):
        state=self.cp["execution_state"]
        self.assertEqual(state["claim_universe_lock"],"NOT_CREATED")
        self.assertEqual(state["prediction_lock"],"NOT_CREATED")
        self.assertEqual(state["outcome_collection"],"NOT_STARTED")
        self.assertFalse(self.cp["interpretation"]["predictive_validity_evidence_created"])
        self.assertFalse(self.cp["interpretation"]["qualification_evidence_created"])

if __name__=="__main__":
    unittest.main()
