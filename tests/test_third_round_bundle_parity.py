import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

from engine.distribution.runtime import dispatch
from tests.test_distribution_case_pack import IDENTITY as _UNUSED_IDENTITY  # keep import surface explicit
from tests.test_distribution_partial_case import ENVELOPE, IDENTITY
from tests.test_third_round_adversarial_regressions import LOCATION, ThirdRoundCaseRecordTests


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "dist" / "ai" / "metaphysics_lab.py"


def _bundled_request(action, payload):
    request = json.dumps({"action": action, "payload": payload}, ensure_ascii=False)
    completed = subprocess.run(
        [sys.executable, str(BUNDLE), "request", "--input", "-"],
        cwd=str(ROOT), input=request, text=True, capture_output=True,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stdout + completed.stderr)
    return json.loads(completed.stdout)


class ThirdRoundBundleParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ThirdRoundCaseRecordTests.setUpClass()
        cls.base_files = ThirdRoundCaseRecordTests.base_files

    def test_bundle_matches_modular_known_fact_control_character_rejection(self):
        envelope = copy.deepcopy(ENVELOPE)
        envelope["known_facts"]["birth_place"] = "Taipei\nFORGED"
        payload = {
            "candidate_envelope": envelope,
            "resolved_location": LOCATION,
            **IDENTITY,
            "generated_at": "2026-08-23T00:00:00+08:00",
            "last_modified_by": "test",
        }
        modular = dispatch("export_case_markdown", payload)
        bundled = _bundled_request("export_case_markdown", payload)
        self.assertEqual(bundled, modular)
        self.assertFalse(modular["ok"], modular)
        self.assertEqual(modular["error"]["code"], "invalid_candidate_envelope")

    def test_bundle_matches_modular_cross_subject_tracking_rejection(self):
        payload = {
            "case_files": self.base_files,
            "filename": "07_問事追蹤紀錄.md",
            "operation": "append",
            "updated_at": "2026-08-23T01:00:00+08:00",
            "last_modified_by": "test",
            "entry": {
                "record_id": "bundle-cross-subject",
                "subject_id": "subj_aaaaaaaaaaaa",
                "question": "other subject",
            },
        }
        modular = dispatch("update_case_record", payload)
        bundled = _bundled_request("update_case_record", payload)
        self.assertEqual(bundled, modular)
        self.assertFalse(modular["ok"], modular)
        self.assertEqual(modular["error"]["code"], "case_subject_mismatch")


if __name__ == "__main__":
    unittest.main()
