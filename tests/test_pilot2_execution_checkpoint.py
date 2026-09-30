import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_PATH = ROOT / "docs" / "research" / "pilot2-execution-checkpoint.v1.json"


class Pilot2ExecutionCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.checkpoint = json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))

    def test_halts_at_claim_universe_lock(self):
        self.assertEqual(self.checkpoint["checkpoint_status"], "HALTED_NON_QUALIFYING")
        self.assertEqual(self.checkpoint["process_stage"], "CLAIM_UNIVERSE_LOCK")
        self.assertEqual(
            self.checkpoint["deviation_code"],
            "MULTI_SEGMENT_YEARLY_EFA_UNIVERSE_UNRESOLVED",
        )

    def test_pcg01_and_source_governance_succeeded_before_halt(self):
        governance = self.checkpoint["governance"]
        self.assertEqual(governance["pcg01_status"], "READY_BEFORE_CANDIDATE_PROCESSING")
        self.assertEqual(governance["intake_status"], "ELIGIBLE_FOR_S1_SOURCE")
        self.assertEqual(
            governance["source_manifest_status"],
            "FROZEN_BEFORE_CANDIDATE_PROCESSING",
        )
        self.assertEqual(
            governance["exposure_status"],
            "UNEXPOSED_BEFORE_CANDIDATE_PROCESSING",
        )

    def test_observation_does_not_choose_an_unapproved_aggregation(self):
        observation = self.checkpoint["structural_observation"]
        self.assertEqual(observation["snapshot_count"], 5)
        self.assertEqual(observation["child_count_per_snapshot"], [28, 28, 28, 28, 28])
        self.assertFalse(observation["child_sets_identical"])
        self.assertEqual(observation["union_child_count"], 45)
        self.assertEqual(observation["intersection_child_count"], 11)
        self.assertFalse(observation["approved_multi_snapshot_selector_exists"])
        self.assertFalse(observation["approved_union_or_intersection_rule_exists"])

    def test_no_prediction_or_outcome_execution_is_fabricated(self):
        state = self.checkpoint["execution_state"]
        self.assertEqual(state["claim_universe_lock"], "NOT_CREATED")
        self.assertEqual(state["prediction_lock"], "NOT_CREATED")
        self.assertEqual(state["outcome_collection"], "NOT_STARTED")
        self.assertEqual(state["adjudication"], "NOT_STARTED")
        self.assertEqual(state["scoring"], "NOT_STARTED")

    def test_retry_requires_new_pilot_and_pre_registered_contract_delta(self):
        next_action = self.checkpoint["next_action"]
        self.assertEqual(next_action["pilot2_resume"], "PROHIBITED")
        self.assertEqual(
            next_action["retry_requires"],
            "NEW_PILOT_ID_AND_NEW_PROTOCOL_VERSION",
        )
        self.assertIn(
            "PRE_REGISTER",
            next_action["required_contract_delta"],
        )


if __name__ == "__main__":
    unittest.main()
