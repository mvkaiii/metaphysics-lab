import unittest

from engine.distribution.constants import PROJECT_CONTRACT_VERSION
from engine.distribution.runtime import dispatch


BIRTH = {
    "sex": "female",
    "birth_date": "1992-08-17",
    "birth_time": "14:30",
    "birth_place": "高雄市",
}
LOCATION = {
    "canonical_name": "Kaohsiung City, Taiwan",
    "latitude": 22.6273,
    "longitude": 120.3014,
    "timezone": "Asia/Taipei",
    "provider_name": "ai_host",
    "provider_version": "synthetic-test",
    "provider_reference": None,
}
BASE_SLOTS = [
    "00_專案索引.md",
    "01_命盤核心摘要.md",
    "02_命盤資料校驗紀錄.md",
    "03_八字結構化資料包.md",
    "04_紫微基礎資料包.md",
]
TRACKING_SLOTS = [
    "05_驗證事件紀錄.md",
    "06_流年追蹤紀錄.md",
    "07_問事追蹤紀錄.md",
    "08_重大決策紀錄.md",
]
ALL_SLOTS = BASE_SLOTS + TRACKING_SLOTS


class FifthRoundLegacyRecordIdCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        natal = dispatch("build_natal", {"birth": BIRTH, "resolved_location": LOCATION})
        if not natal.get("ok"):
            raise AssertionError(natal)
        exported = dispatch(
            "export_case_markdown",
            {
                "normalized_natal": natal["data"]["normalized_natal"],
                "subject_id": "subj_a1b2c3d4e5f6",
                "subject_display_name": "Example",
                "subject_short_id": "A1B2C3",
                "filename_label": "Example",
                "generated_at": "2026-08-24T03:00:00+08:00",
                "last_modified_by": "ai",
            },
        )
        if not exported.get("ok"):
            raise AssertionError(exported)
        cls.current_files = dict(exported["data"]["files"])
        entries = {
            "05_驗證事件紀錄.md": {"record_id": "legacy-05", "status": "verified", "summary": "synthetic legacy event"},
            "06_流年追蹤紀錄.md": {"record_id": "legacy-06", "blind_forecast": "synthetic legacy forecast"},
            "07_問事追蹤紀錄.md": {"record_id": "legacy-07", "blind_forecast": "synthetic legacy question"},
            "08_重大決策紀錄.md": {"record_id": "legacy-08", "decision": "synthetic legacy decision"},
        }
        for index, slot in enumerate(TRACKING_SLOTS, start=1):
            updated = dispatch(
                "update_case_record",
                {
                    "case_files": cls.current_files,
                    "filename": slot,
                    "operation": "append",
                    "updated_at": "2026-08-24T03:%02d:00+08:00" % index,
                    "last_modified_by": "ai",
                    "entry": entries[slot],
                },
            )
            if not updated.get("ok"):
                raise AssertionError(updated)
            cls.current_files.update(updated["data"]["changed_files"])

    @classmethod
    def _actual_name(cls, slot):
        return next(name for name in cls.current_files if name.endswith(slot))

    @classmethod
    def legacy_case(cls, *, record_id="年度 預測 1", nonfinite=False, mismatch=False):
        legacy = {}
        for slot in ALL_SLOTS:
            text = cls.current_files[cls._actual_name(slot)]
            text = text.replace("case_schema_version: 1.1", "case_schema_version: 1.0", 1)
            text = text.replace("project_contract_version: %s" % PROJECT_CONTRACT_VERSION, "project_contract_version: 1.0", 1)
            text = text.replace("subject_id: subj_a1b2c3d4e5f6", "subject_id: case-legacy", 1)
            if slot == "07_問事追蹤紀錄.md":
                text = text.replace("### legacy-07", "### %s" % record_id, 1)
                payload_id = "other id" if mismatch else record_id
                text = text.replace('"record_id": "legacy-07"', '"record_id": "%s"' % payload_id, 1)
                if nonfinite:
                    text = text.replace('"blind_forecast": "synthetic legacy question"', '"blind_forecast": "synthetic legacy question",\n  "value": NaN', 1)
            legacy[slot] = text
        return legacy

    def _migrate(self, case_files):
        return dispatch(
            "migrate_case",
            {
                "case_files": case_files,
                "subject_display_name": "Legacy Example",
                "updated_at": "2026-08-24T04:00:00+08:00",
            },
        )

    def test_legacy_1_0_unicode_space_record_id_remains_readable(self):
        result = dispatch("validate_case", {"case_files": self.legacy_case()})
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["data"]["case_schema_version"], "1.0")

    def test_legacy_1_0_unicode_space_record_id_migrates_to_valid_1_1(self):
        migrated = self._migrate(self.legacy_case())
        self.assertTrue(migrated["ok"], migrated)
        changed = migrated["data"]["changed_files"]
        validated = dispatch("validate_case", {"case_files": changed})
        self.assertTrue(validated["ok"], validated)
        self.assertEqual(validated["data"]["case_schema_version"], "1.1")
        question_text = next(text for name, text in changed.items() if name.endswith("07_問事追蹤紀錄.md"))
        self.assertNotIn("年度 預測 1", question_text)
        self.assertIn("legacy-07-", question_text)

    def test_long_legacy_1_0_record_id_migrates_within_1_1_length_limit(self):
        legacy_id = "舊年度預測 " + ("甲乙丙丁" * 80)
        legacy = self.legacy_case(record_id=legacy_id)
        readable = dispatch("validate_case", {"case_files": legacy})
        self.assertTrue(readable["ok"], readable)
        migrated = self._migrate(legacy)
        self.assertTrue(migrated["ok"], migrated)
        changed = migrated["data"]["changed_files"]
        validated = dispatch("validate_case", {"case_files": changed})
        self.assertTrue(validated["ok"], validated)
        question_text = next(text for name, text in changed.items() if name.endswith("07_問事追蹤紀錄.md"))
        heading = next(line[4:] for line in question_text.splitlines() if line.startswith("### legacy-07-"))
        self.assertLessEqual(len(heading), 128)
        self.assertNotIn(legacy_id, question_text)

    def test_legacy_1_0_nonfinite_json_is_still_rejected(self):
        result = dispatch("validate_case", {"case_files": self.legacy_case(nonfinite=True)})
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error"]["code"], "invalid_case_markdown")

    def test_legacy_1_0_heading_payload_record_id_mismatch_is_still_rejected(self):
        result = dispatch("validate_case", {"case_files": self.legacy_case(mismatch=True)})
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error"]["code"], "invalid_case_markdown")


if __name__ == "__main__":
    unittest.main()
