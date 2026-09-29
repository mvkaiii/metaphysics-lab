import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
CP=ROOT/"docs/research/pilot4-execution-checkpoint.v1.json"

class Pilot4ExecutionCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.cp=json.loads(CP.read_text(encoding="utf-8"))

    def test_halt_occurs_after_efa_union_and_exact_s1_but_before_prediction(self):
        self.assertEqual(self.cp["checkpoint_status"],"HALTED_NON_QUALIFYING")
        self.assertEqual(self.cp["process_stage"],"DOWNSTREAM_AUTHORITY_COMPATIBILITY")
        self.assertEqual(self.cp["deviation_code"],"MULTI_SEGMENT_DOWNSTREAM_AUTHORITY_PATH_UNAVAILABLE")
        state=self.cp["execution_state"]
        self.assertEqual(state["efa_census"],"COMPLETE_PRIVATE")
        self.assertEqual(state["claim_universe_lock"],"CREATED_PRIVATE")
        self.assertEqual(state["s1_claim_membership_lock"],"VALIDATED_EXACT_PRIVATE")
        self.assertEqual(state["downstream_authority_compatibility"],"FAILED_CLOSED")
        self.assertEqual(state["prediction_lock"],"NOT_CREATED")
        self.assertEqual(state["outcome_collection"],"NOT_STARTED")

    def test_frozen_downstream_is_single_source_and_aggregate_is_membership_only(self):
        c=self.cp["contract_boundary"]
        self.assertEqual(c["aggregation_scope"],"MEMBERSHIP_ONLY")
        self.assertTrue(c["aggregate_may_not_impersonate_single_snapshot_authority"])
        self.assertTrue(c["frozen_claim_evidence_requires_single_ranking_and_structural_provenance"])
        self.assertTrue(c["frozen_claim_consumption_requires_matching_single_ranking_and_structural_provenance"])
        self.assertTrue(c["frozen_hierarchical_authority_requires_single_efa_bundle"])
        self.assertTrue(c["frozen_hybrid_composer_requires_single_efa_bundle"])
        self.assertTrue(c["frozen_hybrid_output_contract_consumes_single_hcc_source"])

    def test_no_retrospective_adapter_or_snapshot_selection_is_allowed(self):
        c=self.cp["contract_boundary"]
        self.assertFalse(c["segment_aware_downstream_adapter_preregistered"])
        self.assertFalse(c["best_snapshot_selection_preregistered"])
        self.assertFalse(c["synthetic_multi_source_authority_preregistered"])
        self.assertFalse(c["retrospective_adapter_invention_allowed"])
        self.assertEqual(self.cp["next_action"]["pilot4_resume"],"PROHIBITED")
        self.assertEqual(self.cp["next_action"]["replacement_case_under_pilot4"],"PROHIBITED")
        self.assertEqual(self.cp["next_action"]["retry_requires"],"NEW_PILOT_ID_OR_PROTOCOL_VERSION")

    def test_blind_side_and_outcomes_remain_unread(self):
        self.assertFalse(self.cp["blindness"]["validation_event_history_read"])
        self.assertFalse(self.cp["blindness"]["outcome_material_read"])
        self.assertFalse(self.cp["interpretation"]["predictive_validity_evidence_created"])
        self.assertFalse(self.cp["interpretation"]["qualification_evidence_created"])

    def test_public_checkpoint_contains_no_private_observation_details(self):
        self.assertTrue(all(value is False for value in self.cp["privacy"].values()))
        s=json.dumps(self.cp,ensure_ascii=False).lower()
        for forbidden in (
            '"opaque_case_id":','"snapshot_count":','"snapshot_id":','"claim_count":',
            '"claim_id":','"snapshot_manifest_digest":','"claim_universe_digest":',
            '"structural_state_digest":','"ranking_digest":','"event_family_attribution_digest":',
            '"birth_date":','"birth_time":'
        ):
            self.assertNotIn(forbidden,s)

if __name__=="__main__":
    unittest.main()
