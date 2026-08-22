import copy
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

EXPECTED_FILES = [
    "00_專案索引.md",
    "01_命盤核心摘要.md",
    "02_命盤資料校驗紀錄.md",
    "03_八字結構化資料包.md",
    "04_紫微基礎資料包.md",
    "05_驗證事件紀錄.md",
    "06_流年追蹤紀錄.md",
    "07_問事追蹤紀錄.md",
    "08_重大決策紀錄.md",
]

REQUIRED_META = {
    "case_schema_version",
    "project_contract_version",
    "record_type",
    "subject_id",
    "created_at",
    "last_updated_at",
    "last_modified_by",
    "runtime_version_if_applicable",
    "source_classification",
    "mutation_policy",
}


class DistributionCasePackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        built = dispatch(
            "build_natal",
            {"birth": BIRTH, "resolved_location": LOCATION},
        )
        if not built.get("ok"):
            raise AssertionError(built)
        cls.normalized = built["data"]["normalized_natal"]
        cls.base_payload = {
            "normalized_natal": cls.normalized,
            "subject_id": "case-19840313-a1b2c3",
            "generated_at": "2026-08-23T00:00:00+08:00",
            "last_modified_by": "ai",
        }

    def export(self, **extra):
        payload = dict(self.base_payload)
        payload.update(extra)
        return dispatch("export_case_markdown", payload)

    @staticmethod
    def front_matter(text):
        lines = text.splitlines()
        if not lines or lines[0] != "---":
            raise AssertionError("missing front matter")
        result = {}
        for line in lines[1:]:
            if line == "---":
                return result
            key, value = line.split(": ", 1)
            result[key] = value
        raise AssertionError("unterminated front matter")

    def test_fixed_input_produces_exact_nine_byte_identical_markdown_files(self):
        first = self.export()
        second = self.export()
        self.assertTrue(first["ok"], first)
        self.assertTrue(second["ok"], second)
        self.assertEqual(list(first["data"]["files"]), EXPECTED_FILES)
        self.assertEqual(first["data"]["files"], second["data"]["files"])
        for name, text in first["data"]["files"].items():
            self.assertIsInstance(text, str)
            self.assertTrue(text.endswith("\n"), name)

    def test_all_files_have_required_front_matter_and_opaque_subject_id(self):
        result = self.export()
        self.assertTrue(result["ok"], result)
        for name, text in result["data"]["files"].items():
            meta = self.front_matter(text)
            self.assertTrue(REQUIRED_META.issubset(meta), name)
            self.assertEqual(meta["case_schema_version"], "1.0")
            self.assertEqual(meta["project_contract_version"], "1.0")
            self.assertEqual(meta["subject_id"], "case-19840313-a1b2c3")
            self.assertNotIn("name", meta)

    def test_bazi_and_ziwei_files_contain_deterministic_facts_not_interpretation(self):
        result = self.export(
            analysis_sections={"長期框架": "這是明確標示的 AI 分析文字。"}
        )
        self.assertTrue(result["ok"], result)
        files = result["data"]["files"]
        self.assertIn("bazi.pillars", files["03_八字結構化資料包.md"])
        self.assertIn("ziwei.ming_palace", files["04_紫微基礎資料包.md"])
        self.assertIn("Metaphysics Lab", files["03_八字結構化資料包.md"])
        self.assertIn("Metaphysics Lab", files["04_紫微基礎資料包.md"])
        self.assertNotIn("命理推論", files["03_八字結構化資料包.md"])
        self.assertNotIn("命理推論", files["04_紫微基礎資料包.md"])
        self.assertNotIn("這是明確標示的 AI 分析文字", files["03_八字結構化資料包.md"])
        self.assertNotIn("這是明確標示的 AI 分析文字", files["04_紫微基礎資料包.md"])
        self.assertIn("## 命理推論", files["01_命盤核心摘要.md"])
        self.assertIn("這是明確標示的 AI 分析文字", files["01_命盤核心摘要.md"])

    def test_initial_tracking_files_are_empty_and_do_not_fabricate_records(self):
        result = self.export()
        self.assertTrue(result["ok"], result)
        files = result["data"]["files"]
        for name in EXPECTED_FILES[5:]:
            text = files[name]
            self.assertIn("目前沒有已記錄項目", text)
            self.assertNotIn("evt-", text)
            self.assertNotIn("forecast-", text)
            self.assertNotIn("decision-", text)

    def test_append_verified_event_returns_only_changed_event_file(self):
        exported = self.export()
        files = exported["data"]["files"]
        before_core = {name: files[name] for name in EXPECTED_FILES[:5]}
        result = dispatch(
            "update_case_record",
            {
                "case_files": files,
                "filename": "05_驗證事件紀錄.md",
                "operation": "append",
                "updated_at": "2026-08-23T01:00:00+08:00",
                "last_modified_by": "ai",
                "entry": {
                    "record_id": "evt-001",
                    "occurred_at": "2026-08-01",
                    "status": "verified",
                    "summary": "開始帶實習生進行資料分析訓練",
                },
            },
        )
        self.assertTrue(result["ok"], result)
        changed = result["data"]["changed_files"]
        self.assertEqual(list(changed), ["05_驗證事件紀錄.md"])
        self.assertIn("evt-001", changed["05_驗證事件紀錄.md"])
        self.assertIn("開始帶實習生", changed["05_驗證事件紀錄.md"])
        for name, text in before_core.items():
            self.assertNotIn(name, changed)
            self.assertEqual(files[name], text)

    def test_blind_forecast_replacement_is_rejected(self):
        exported = self.export()
        appended = dispatch(
            "update_case_record",
            {
                "case_files": exported["data"]["files"],
                "filename": "06_流年追蹤紀錄.md",
                "operation": "append",
                "updated_at": "2026-08-23T01:00:00+08:00",
                "last_modified_by": "ai",
                "entry": {
                    "record_id": "forecast-001",
                    "blind_forecast": "第一版盲判內容，不得覆寫。",
                },
            },
        )
        self.assertTrue(appended["ok"], appended)
        files = dict(exported["data"]["files"])
        files.update(appended["data"]["changed_files"])
        result = dispatch(
            "update_case_record",
            {
                "case_files": files,
                "filename": "06_流年追蹤紀錄.md",
                "operation": "replace_blind_forecast",
                "updated_at": "2026-08-23T02:00:00+08:00",
                "last_modified_by": "ai",
                "entry": {
                    "record_id": "forecast-001",
                    "blind_forecast": "偷偷改掉的新版。",
                },
            },
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "immutable_blind_forecast")

    def test_validate_case_detects_subject_mismatch(self):
        exported = self.export()
        files = copy.deepcopy(exported["data"]["files"])
        files["08_重大決策紀錄.md"] = files["08_重大決策紀錄.md"].replace(
            "subject_id: case-19840313-a1b2c3",
            "subject_id: case-other",
            1,
        )
        result = dispatch("validate_case", {"case_files": files})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "case_subject_mismatch")

    def test_current_schema_migration_is_compatible_no_change(self):
        exported = self.export()
        result = dispatch(
            "migrate_case",
            {"case_files": exported["data"]["files"]},
        )
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["data"]["status"], "compatible")
        self.assertEqual(result["data"]["migration"], "no_change")
        self.assertEqual(result["data"]["changed_files"], {})


if __name__ == "__main__":
    unittest.main()
