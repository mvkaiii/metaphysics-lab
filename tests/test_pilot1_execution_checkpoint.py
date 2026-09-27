import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_PATH = (
    ROOT / "docs" / "research" / "pilot1-execution-checkpoint.v1.json"
)


class Pilot1ExecutionCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.checkpoint = json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))

    def test_checkpoint_records_fail_closed_s1_result(self):
        self.assertEqual(
            self.checkpoint["checkpoint_status"],
            "HALTED_NON_QUALIFYING",
        )
        self.assertEqual(
            self.checkpoint["deviation_code"],
            "S1_SOURCE_MANIFEST_NOT_FROZEN_BEFORE_CANDIDATE_EXPOSURE",
        )
        self.assertEqual(
            self.checkpoint["intake"]["eligibility_status"],
            "INELIGIBLE_PREVIOUSLY_EXPOSED",
        )
        self.assertEqual(
            self.checkpoint["s1"]["frame_status"],
            "EXCLUDE_PREVIOUSLY_EXPOSED",
        )
        self.assertEqual(self.checkpoint["s1"]["receipt_status"], "INELIGIBLE")
        self.assertEqual(self.checkpoint["s1"]["included_case_count"], 0)
        self.assertEqual(self.checkpoint["s1"]["locked_claim_count"], 0)

    def test_checkpoint_does_not_fabricate_downstream_execution(self):
        state = self.checkpoint["execution_state"]
        self.assertEqual(state["prediction_lock"], "NOT_CREATED")
        self.assertEqual(state["outcome_collection"], "NOT_STARTED")
        self.assertEqual(state["adjudication"], "NOT_STARTED")
        self.assertEqual(state["scoring"], "NOT_STARTED")
        self.assertEqual(state["verified_event_calibration"], "NOT_STARTED")

    def test_pilot1_cannot_replace_failed_case(self):
        next_action = self.checkpoint["next_action"]
        self.assertEqual(next_action["pilot1_replacement_case"], "PROHIBITED")
        self.assertEqual(
            next_action["retry_requires"],
            "NEW_PILOT_ID_AND_NEW_PROTOCOL_VERSION",
        )

    def test_public_checkpoint_contains_no_private_case_payload(self):
        serialized = json.dumps(
            self.checkpoint,
            ensure_ascii=False,
            sort_keys=True,
        ).lower()
        forbidden = (
            "opaque_case_id",
            "source_record_digest",
            "private_digest",
            "birth_input",
            "birth_data",
            "prediction_text",
            "outcome_text",
            "claim_ids",
        )
        for token in forbidden:
            self.assertNotIn(token, serialized)

    def test_process_failure_creates_no_predictive_or_promotion_evidence(self):
        interpretation = self.checkpoint["interpretation"]
        self.assertFalse(interpretation["pilot1_process_conformance_met"])
        self.assertFalse(interpretation["predictive_validity_evidence_created"])
        self.assertFalse(interpretation["qualification_evidence_created"])
        self.assertFalse(interpretation["stable_promotion_effect"])


if __name__ == "__main__":
    unittest.main()
