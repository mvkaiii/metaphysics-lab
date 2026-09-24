import unittest

from engine.distribution.prospective import (
    METHOD_VERSION,
    lock_prospective_forecast,
    resolve_query_anchor,
)
from engine.distribution.prospective_validation import classify_validation_context
from engine.distribution.runtime import dispatch


FROZEN_V15_DIGEST = "b9b465c43fe1e903601cb9b726ef0c691810a674b2c074146a1b30c7ee9d1524"

BIRTH = {
    "sex": "male",
    "birth_date": "1984-03-13",
    "birth_time": "19:20",
    "birth_place": "台北市",
}
LOCATION = {
    "canonical_name": "Taipei City, Taiwan",
    "latitude": 25.033,
    "longitude": 121.5654,
    "timezone": "Asia/Taipei",
    "provider_name": "ai_host",
    "provider_version": "user-confirmed",
    "provider_reference": None,
}


class ProspectiveValidationCompatibilityTests(unittest.TestCase):
    @staticmethod
    def _anchor():
        return resolve_query_anchor({
            "query_anchor_at": "2026-08-29T00:10:00+08:00",
            "query_timezone": "Asia/Taipei",
            "target_start": "2026-09-01T00:00:00+08:00",
            "target_end": "2026-12-31T23:59:59+08:00",
            "question_reference": "synthetic-v15-claim-contract",
        })

    @classmethod
    def _legacy_lock(cls):
        anchor = cls._anchor()
        claim = {
            "claim_id": "C1",
            "priority": "primary",
            "forecast_window": {
                "start": "2026-09-01T00:00:00+08:00",
                "end": "2026-09-30T23:59:59+08:00",
            },
            "primary_domain": "career",
            "event_family": "role_change",
            "prediction": "synthetic bounded event-family forecast",
            "matched_if": "formal responsibility or role changes inside the window",
            "partial_if": "responsibility changes materially but without formal title change",
            "not_matched_if": "no material responsibility or role change occurs inside the window",
            "evidence_layers": ["bazi"],
            "evidence_time_scales": ["yearly", "monthly"],
            "capability_maturity": "stable",
            "confidence": "medium",
            "knowledge_cutoff_at": anchor["knowledge_cutoff_at"],
            "evaluation_eligibility": "clean_scorable",
            "contamination_state": "clean_prospective",
            "method_version": METHOD_VERSION,
        }
        return anchor, lock_prospective_forecast({"anchor": anchor, "claims": [claim]})

    def test_v15_lock_digest_remains_bit_compatible(self):
        _, locked = self._legacy_lock()
        self.assertEqual(locked["canonical_digest"], FROZEN_V15_DIGEST)

    def test_case_1_1_round_trips_v15_lock_with_v2_validation_sidecar(self):
        anchor, locked = self._legacy_lock()
        self.assertEqual(locked["canonical_digest"], FROZEN_V15_DIGEST)

        built = dispatch("build_natal", {"birth": BIRTH, "resolved_location": LOCATION})
        self.assertTrue(built["ok"], built)
        exported = dispatch("export_case_markdown", {
            "normalized_natal": built["data"]["normalized_natal"],
            "subject_id": "subj_7f3a2c91d4e8",
            "subject_display_name": "Kai",
            "subject_short_id": "7F3A2C",
            "filename_label": "Kai",
            "generated_at": "2026-08-29T00:20:00+08:00",
            "last_modified_by": "ai",
        })
        self.assertTrue(exported["ok"], exported)

        sidecar = classify_validation_context({
            "forecast_id": "pv2-sidecar-001",
            "locked_at": "2026-08-29T00:20:00+08:00",
            "knowledge_cutoff_at": anchor["knowledge_cutoff_at"],
            "question_mode": "future_forecast",
            "knowledge_state_at_lock": "unknown",
            "prediction_window": {
                "start": "2026-09-01T00:00:00+08:00",
                "end": "2026-09-30T23:59:59+08:00",
            },
        })
        appended = dispatch("update_case_record", {
            "case_files": exported["data"]["files"],
            "filename": "06_流年追蹤紀錄.md",
            "operation": "append",
            "updated_at": "2026-08-29T00:20:00+08:00",
            "last_modified_by": "ai",
            "entry": {
                "record_id": "pv2-sidecar-001",
                "prospective_forecast_lock": locked,
                "validation_context": sidecar,
            },
        })
        self.assertTrue(appended["ok"], appended)

        files = dict(exported["data"]["files"])
        files.update(appended["data"]["changed_files"])
        validated = dispatch("validate_case", {"case_files": files})
        self.assertTrue(validated["ok"], validated)
        self.assertEqual(validated["data"]["case_schema_version"], "1.1")

        tracking_names = [name for name in files if name.endswith("_06_流年追蹤紀錄.md")]
        self.assertEqual(len(tracking_names), 1)
        tracking = files[tracking_names[0]]
        self.assertIn(FROZEN_V15_DIGEST, tracking)
        self.assertIn("prospective-validation-v2-exp", tracking)


if __name__ == "__main__":
    unittest.main()
