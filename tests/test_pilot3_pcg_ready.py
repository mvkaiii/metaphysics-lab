import json
from pathlib import Path
import unittest

from tools.validate_pilot3_pre_candidate_gate import (
    candidate_case_processing_allowed,
    validate_pilot3_pre_candidate_gate,
)


ROOT = Path(__file__).resolve().parents[1]
BLOCKED_PATH = ROOT / "docs" / "research" / "pilot3-pre-candidate-gate.template.json"
READY_PATH = ROOT / "docs" / "research" / "pilot3-pre-candidate-gate.ready.v1.json"
CHECKPOINT_PATH = ROOT / "docs" / "research" / "pilot3-pcg-ready-checkpoint.v1.json"


class Pilot3PcgReadyTests(unittest.TestCase):
    def setUp(self):
        self.blocked = json.loads(BLOCKED_PATH.read_text(encoding="utf-8"))
        self.ready = json.loads(READY_PATH.read_text(encoding="utf-8"))
        self.checkpoint = json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))

    def test_start_time_template_remains_blocked(self):
        self.assertEqual(validate_pilot3_pre_candidate_gate(self.blocked), [])
        self.assertEqual(self.blocked["gate_status"], "BLOCKED")
        self.assertFalse(candidate_case_processing_allowed(self.blocked))

    def test_ready_receipt_validates_and_opens_candidate_processing(self):
        self.assertEqual(validate_pilot3_pre_candidate_gate(self.ready), [])
        self.assertEqual(self.ready["gate_status"], "READY")
        self.assertTrue(all(self.ready["prerequisites"].values()))
        self.assertTrue(candidate_case_processing_allowed(self.ready))
        self.assertFalse(self.ready["manual_override_allowed"])
        self.assertFalse(self.ready["private_material_disclosed"])

    def test_ready_receipt_preserves_start_bindings(self):
        self.assertEqual(
            self.ready["public_bindings"],
            self.blocked["public_bindings"],
        )

    def test_public_ready_artifacts_do_not_disclose_private_case_material(self):
        serialized = json.dumps(
            {"ready": self.ready, "checkpoint": self.checkpoint},
            ensure_ascii=False,
        ).lower()
        for forbidden in (
            "opaque_case_id",
            "birth_data",
            "source_manifest_digest",
            "private_provenance_digest",
            "prediction_text",
            "outcome_text",
        ):
            self.assertNotIn(f'"{forbidden}":', serialized)

    def test_checkpoint_records_ready_before_candidate_processing(self):
        self.assertEqual(self.checkpoint["checkpoint_status"], "PCG_READY")
        self.assertEqual(self.checkpoint["governance"]["intake_status"], "ELIGIBLE_FOR_S1_SOURCE")
        self.assertEqual(
            self.checkpoint["governance"]["s1_source_manifest_status"],
            "FROZEN_BEFORE_CANDIDATE_PROCESSING",
        )
        self.assertEqual(
            self.checkpoint["governance"]["exposure_status"],
            "UNEXPOSED_BEFORE_CANDIDATE_PROCESSING",
        )
        self.assertEqual(
            self.checkpoint["execution_state"]["candidate_processing"],
            "NOT_STARTED_AT_CHECKPOINT",
        )


if __name__ == "__main__":
    unittest.main()
