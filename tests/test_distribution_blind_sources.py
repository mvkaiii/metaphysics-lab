import unittest

from engine.distribution.runtime import dispatch


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
BASE_SLOTS = (
    "00_專案索引.md",
    "01_命盤核心摘要.md",
    "02_命盤資料校驗紀錄.md",
    "03_八字結構化資料包.md",
    "04_紫微基礎資料包.md",
)
PROGRESSIVE_SLOT = "05_驗證事件紀錄.md"


def _actual(slot):
    return "Kai_7F3A2C_" + slot


class DistributionBlindSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        built = dispatch("build_natal", {"birth": BIRTH, "resolved_location": LOCATION})
        if not built.get("ok"):
            raise AssertionError(built)
        exported = dispatch(
            "export_case_markdown",
            {
                "normalized_natal": built["data"]["normalized_natal"],
                "subject_id": "subj_7f3a2c91d4e8",
                "subject_display_name": "Kai",
                "subject_short_id": "7F3A2C",
                "filename_label": "Kai",
                "generated_at": "2026-08-26T22:00:00+08:00",
                "last_modified_by": "ai",
            },
        )
        if not exported.get("ok"):
            raise AssertionError(exported)
        files = dict(exported["data"]["files"])
        appended = dispatch(
            "update_case_record",
            {
                "case_files": files,
                "filename": PROGRESSIVE_SLOT,
                "operation": "append",
                "updated_at": "2026-08-26T22:01:00+08:00",
                "last_modified_by": "ai",
                "entry": {
                    "record_id": "evt-phase0-001",
                    "status": "verified",
                    "summary": "synthetic verified event for blind-source validation",
                },
            },
        )
        if not appended.get("ok"):
            raise AssertionError(appended)
        files.update(appended["data"]["changed_files"])
        cls.case_files = files
        cls.base_files = {_actual(slot): files[_actual(slot)] for slot in BASE_SLOTS}

    def _payload(self, source_files, source_case_files):
        return {
            "blind_forecast_id": "bf-phase0-001",
            "subject_id": "subj_7f3a2c91d4e8",
            "question_type": "流年問事",
            "question_reference": "2027-work",
            "locked_at": "2026-08-26T22:02:00+08:00",
            "source_files_used": list(source_files),
            "source_case_files": source_case_files,
            "blind_forecast_payload": {"核心結論": "synthetic blind forecast"},
        }

    def test_blind_lock_accepts_base_only_input_when_manifest_tracks_progressive_files(self):
        """00 may truthfully say 05 exists while Stage 1 still receives only 00-04."""
        result = dispatch(
            "lock_blind_forecast",
            self._payload(self.base_files, self.base_files),
        )
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["data"]["locked_payload"]["source_slots_used"], list(BASE_SLOTS))
        self.assertEqual(result["data"]["locked_payload"]["forbidden_source_slots"][0], PROGRESSIVE_SLOT)

    def test_blind_lock_rejects_progressive_file_content_in_stage1_sources(self):
        stage1_with_05 = dict(self.base_files)
        stage1_with_05[_actual(PROGRESSIVE_SLOT)] = self.case_files[_actual(PROGRESSIVE_SLOT)]
        result = dispatch(
            "lock_blind_forecast",
            self._payload(stage1_with_05, stage1_with_05),
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "blind_source_violation")

    def test_blind_lock_still_rejects_subject_mismatch_in_base_files(self):
        mismatched = dict(self.base_files)
        target = _actual("04_紫微基礎資料包.md")
        mismatched[target] = mismatched[target].replace(
            "subject_id: subj_7f3a2c91d4e8",
            "subject_id: subj_aaaaaaaaaaaa",
            1,
        )
        result = dispatch(
            "lock_blind_forecast",
            self._payload(mismatched, mismatched),
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "case_subject_mismatch")

    def test_full_case_validation_remains_strict_and_accepts_materialized_05(self):
        result = dispatch("validate_case", {"case_files": self.case_files})
        self.assertTrue(result["ok"], result)
        self.assertEqual(
            result["data"]["canonical_slots"],
            list(BASE_SLOTS) + [PROGRESSIVE_SLOT],
        )


if __name__ == "__main__":
    unittest.main()
