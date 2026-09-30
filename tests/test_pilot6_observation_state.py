import json
from datetime import datetime
from pathlib import Path
import unittest

from tools.validate_pilot6_observation_state import (
    adjudication_allowed_at,
    engineering_development_allowed,
    outcome_collection_window_open,
    validate_pilot6_observation_state,
)

ROOT = Path(__file__).resolve().parents[1]
OBSERVATION = ROOT / "docs/research/pilot6-observation-state.v1.json"


class Pilot6ObservationStateTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads(OBSERVATION.read_text(encoding="utf-8"))

    def test_observation_state_validates(self):
        self.assertEqual(validate_pilot6_observation_state(self.payload), [])
        self.assertEqual(self.payload["lifecycle_state"], "OBSERVATION_PENDING")
        self.assertEqual(self.payload["prediction_side_status"], "PREDICTION_LOCKED")

    def test_observation_does_not_block_v18_engineering(self):
        self.assertTrue(engineering_development_allowed(self.payload))
        permissions = self.payload["permissions"]
        self.assertTrue(permissions["engineering_development_continuation_allowed"])
        self.assertFalse(permissions["frozen_candidate_mutation_allowed"])
        self.assertFalse(permissions["replacement_case_allowed"])
        self.assertFalse(permissions["retrospective_prediction_repair_allowed"])

    def test_outcome_collection_opens_only_inside_approved_window(self):
        self.assertFalse(outcome_collection_window_open(
            self.payload, datetime.fromisoformat("2026-09-29T18:33:00+08:00")
        ))
        self.assertTrue(outcome_collection_window_open(
            self.payload, datetime.fromisoformat("2027-09-01T00:00:00+08:00")
        ))
        self.assertTrue(outcome_collection_window_open(
            self.payload, datetime.fromisoformat("2027-10-31T23:59:59+08:00")
        ))
        self.assertFalse(outcome_collection_window_open(
            self.payload, datetime.fromisoformat("2027-11-01T00:00:00+08:00")
        ))

    def test_adjudication_waits_for_full_window_plus_72_hours(self):
        self.assertFalse(adjudication_allowed_at(
            self.payload, datetime.fromisoformat("2027-10-31T23:59:59+08:00")
        ))
        self.assertFalse(adjudication_allowed_at(
            self.payload, datetime.fromisoformat("2027-11-03T23:59:58+08:00")
        ))
        self.assertTrue(adjudication_allowed_at(
            self.payload, datetime.fromisoformat("2027-11-03T23:59:59+08:00")
        ))

    def test_public_observation_artifact_discloses_no_private_lock_material(self):
        serialized = json.dumps(self.payload, ensure_ascii=False).lower()
        for forbidden_key in (
            "prediction_lock_digest",
            "execution_artifact_zip_sha256",
            "private_case_id",
            "birth_data",
            "prediction_text",
            "outcome_text",
        ):
            self.assertNotIn(f'"{forbidden_key}":', serialized)
        self.assertTrue(all(value is False for value in self.payload["privacy"].values()))

    def test_pilot_specific_stable_promotion_remains_blocked(self):
        self.assertFalse(
            self.payload["permissions"]["pilot_capability_stable_promotion_allowed"]
        )


if __name__ == "__main__":
    unittest.main()
