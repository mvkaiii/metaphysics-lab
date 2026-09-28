import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_PATH = ROOT / "docs" / "research" / "pilot3-execution-checkpoint.v1.json"


class Pilot3ExecutionCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.checkpoint = json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))

    def test_halt_is_before_snapshot_manifest_and_efa(self):
        self.assertEqual(self.checkpoint["checkpoint_status"], "HALTED_NON_QUALIFYING")
        self.assertEqual(self.checkpoint["process_stage"], "STRUCTURAL_SNAPSHOT_MANIFEST")
        self.assertEqual(
            self.checkpoint["deviation_code"],
            "STRUCTURAL_SNAPSHOT_SEGMENTATION_RULE_UNRESOLVED",
        )
        state = self.checkpoint["execution_state"]
        self.assertEqual(state["structural_snapshot_manifest"], "NOT_CREATED")
        self.assertEqual(state["efa_census"], "NOT_STARTED")
        self.assertEqual(state["claim_universe_lock"], "NOT_CREATED")
        self.assertEqual(state["prediction_lock"], "NOT_CREATED")

    def test_pre_candidate_sequence_succeeded_before_halt(self):
        governance = self.checkpoint["governance"]
        self.assertEqual(governance["pcg_status"], "READY_BEFORE_CANDIDATE_PROCESSING")
        self.assertEqual(governance["intake_status"], "ELIGIBLE_FOR_S1_SOURCE")
        self.assertEqual(
            governance["source_manifest_status"],
            "FROZEN_BEFORE_CANDIDATE_PROCESSING",
        )
        self.assertTrue(
            self.checkpoint["candidate_execution"]["processing_started_only_after_pcg_ready"]
        )
        self.assertTrue(self.checkpoint["candidate_execution"]["frozen_candidate_used"])

    def test_missing_snapshot_enumerator_cannot_be_repaired_after_exposure(self):
        boundary = self.checkpoint["contract_boundary"]
        self.assertEqual(boundary["window_claim_scope"], "yearly")
        self.assertEqual(boundary["timing_scope"], "monthly")
        self.assertFalse(
            boundary["deterministic_window_to_snapshot_enumerator_preregistered"]
        )
        self.assertFalse(boundary["retrospective_segmentation_rule_invention_allowed"])
        self.assertFalse(
            boundary["pilot2_observed_snapshot_or_claim_set_results_used_for_resolution"]
        )
        next_action = self.checkpoint["next_action"]
        self.assertEqual(next_action["pilot3_resume"], "PROHIBITED")
        self.assertEqual(next_action["replacement_case_under_pilot3"], "PROHIBITED")
        self.assertEqual(next_action["retry_requires"], "NEW_PILOT_ID_OR_PROTOCOL_VERSION")

    def test_halt_created_no_prediction_or_outcome_evidence(self):
        self.assertFalse(self.checkpoint["blindness"]["validation_event_history_read"])
        self.assertFalse(self.checkpoint["blindness"]["outcome_material_read"])
        interpretation = self.checkpoint["interpretation"]
        self.assertFalse(interpretation["predictive_validity_evidence_created"])
        self.assertFalse(interpretation["qualification_evidence_created"])
        self.assertFalse(interpretation["stable_promotion_effect"])


if __name__ == "__main__":
    unittest.main()
