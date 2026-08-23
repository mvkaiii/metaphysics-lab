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

BASE_FILES = [
    "00_專案索引.md",
    "01_命盤核心摘要.md",
    "02_命盤資料校驗紀錄.md",
    "03_八字結構化資料包.md",
    "04_紫微基礎資料包.md",
]

PROGRESSIVE_FILES = [
    "05_驗證事件紀錄.md",
    "06_流年追蹤紀錄.md",
    "07_問事追蹤紀錄.md",
    "08_重大決策紀錄.md",
]

ALL_FILES = BASE_FILES + PROGRESSIVE_FILES

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

    def append(self, files, filename, entry, when="2026-08-23T01:00:00+08:00"):
        return dispatch(
            "update_case_record",
            {
                "case_files": files,
                "filename": filename,
                "operation": "append",
                "updated_at": when,
                "last_modified_by": "ai",
                "entry": entry,
            },
        )

    def test_new_case_exports_only_base_files_deterministically(self):
        first = self.export()
        second = self.export()
        self.assertTrue(first["ok"], first)
        self.assertTrue(second["ok"], second)
        self.assertEqual(list(first["data"]["files"]), BASE_FILES)
        self.assertEqual(first["data"]["files"], second["data"]["files"])
        index = first["data"]["files"]["00_專案索引.md"]
        self.assertIn("Historical Calibration: `uncalibrated`", index)
        for name in BASE_FILES:
            self.assertIn("✓", index)
        for name in PROGRESSIVE_FILES:
            self.assertNotIn(name, first["data"]["files"])

    def test_base_files_use_schema_and_contract_1_1(self):
        result = self.export()
        self.assertTrue(result["ok"], result)
        for name, text in result["data"]["files"].items():
            meta = self.front_matter(text)
            self.assertTrue(REQUIRED_META.issubset(meta), name)
            self.assertEqual(meta["case_schema_version"], "1.1")
            self.assertEqual(meta["project_contract_version"], "1.1")
            self.assertEqual(meta["subject_id"], "case-19840313-a1b2c3")

    def test_base_case_validates_without_progressive_files(self):
        exported = self.export()
        result = dispatch("validate_case", {"case_files": exported["data"]["files"]})
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["data"]["case_schema_version"], "1.1")
        self.assertEqual(result["data"]["validated_files"], BASE_FILES)

    def test_bazi_and_ziwei_files_contain_deterministic_facts_not_interpretation(self):
        result = self.export(analysis_sections={"長期框架": "這是明確標示的 AI 分析文字。"})
        self.assertTrue(result["ok"], result)
        files = result["data"]["files"]
        self.assertIn("bazi.pillars", files["03_八字結構化資料包.md"])
        self.assertIn("ziwei.ming_palace", files["04_紫微基礎資料包.md"])
        self.assertNotIn("命理推論", files["03_八字結構化資料包.md"])
        self.assertNotIn("命理推論", files["04_紫微基礎資料包.md"])
        self.assertIn("## 命理推論", files["01_命盤核心摘要.md"])

    def test_first_verified_event_materializes_05_and_updates_index(self):
        exported = self.export()
        files = exported["data"]["files"]
        result = self.append(
            files,
            "05_驗證事件紀錄.md",
            {
                "record_id": "evt-001",
                "occurred_at": "2026-08-01",
                "status": "verified",
                "summary": "開始帶實習生進行資料分析訓練",
            },
        )
        self.assertTrue(result["ok"], result)
        changed = result["data"]["changed_files"]
        self.assertEqual(set(changed), {"00_專案索引.md", "05_驗證事件紀錄.md"})
        self.assertIn("evt-001", changed["05_驗證事件紀錄.md"])
        self.assertIn("✓ 05", changed["00_專案索引.md"])

    def test_subsequent_verified_event_changes_only_05(self):
        exported = self.export()
        first = self.append(
            exported["data"]["files"],
            "05_驗證事件紀錄.md",
            {"record_id": "evt-001", "status": "verified", "summary": "第一件事"},
        )
        files = dict(exported["data"]["files"])
        files.update(first["data"]["changed_files"])
        second = self.append(
            files,
            "05_驗證事件紀錄.md",
            {"record_id": "evt-002", "status": "verified", "summary": "第二件事"},
            "2026-08-23T02:00:00+08:00",
        )
        self.assertTrue(second["ok"], second)
        self.assertEqual(list(second["data"]["changed_files"]), ["05_驗證事件紀錄.md"])
        self.assertIn("evt-001", second["data"]["changed_files"]["05_驗證事件紀錄.md"])
        self.assertIn("evt-002", second["data"]["changed_files"]["05_驗證事件紀錄.md"])

    def test_first_tracking_records_materialize_06_07_08_on_demand(self):
        samples = {
            "06_流年追蹤紀錄.md": {"record_id": "forecast-001", "blind_forecast": "第一版盲判"},
            "07_問事追蹤紀錄.md": {"record_id": "question-001", "blind_forecast": "第一版問事"},
            "08_重大決策紀錄.md": {"record_id": "decision-001", "decision": "是否轉職"},
        }
        for filename, entry in samples.items():
            with self.subTest(filename=filename):
                exported = self.export()
                result = self.append(exported["data"]["files"], filename, entry)
                self.assertTrue(result["ok"], result)
                self.assertEqual(set(result["data"]["changed_files"]), {"00_專案索引.md", filename})

    def test_blind_forecast_replacement_is_rejected_after_materialization(self):
        exported = self.export()
        appended = self.append(
            exported["data"]["files"],
            "06_流年追蹤紀錄.md",
            {"record_id": "forecast-001", "blind_forecast": "第一版盲判內容，不得覆寫。"},
        )
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
                "entry": {"record_id": "forecast-001", "blind_forecast": "偷偷改掉的新版。"},
            },
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "immutable_blind_forecast")

    def test_validate_case_detects_subject_mismatch_in_materialized_file(self):
        exported = self.export()
        first = self.append(
            exported["data"]["files"],
            "08_重大決策紀錄.md",
            {"record_id": "decision-001", "decision": "是否轉職"},
        )
        files = dict(exported["data"]["files"])
        files.update(first["data"]["changed_files"])
        files["08_重大決策紀錄.md"] = files["08_重大決策紀錄.md"].replace(
            "subject_id: case-19840313-a1b2c3", "subject_id: case-other", 1
        )
        result = dispatch("validate_case", {"case_files": files})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "case_subject_mismatch")

    def test_legacy_1_0_nine_file_case_remains_readable(self):
        exported = self.export()
        files = dict(exported["data"]["files"])
        for filename in PROGRESSIVE_FILES:
            entry = {"record_id": "legacy-" + filename[:2]}
            if filename == "05_驗證事件紀錄.md":
                entry.update({"status": "verified", "summary": "legacy event"})
            elif filename in ("06_流年追蹤紀錄.md", "07_問事追蹤紀錄.md"):
                entry["blind_forecast"] = "legacy forecast"
            else:
                entry["decision"] = "legacy decision"
            result = self.append(files, filename, entry)
            self.assertTrue(result["ok"], result)
            files.update(result["data"]["changed_files"])
        legacy = {
            name: text.replace("case_schema_version: 1.1", "case_schema_version: 1.0", 1).replace(
                "project_contract_version: 1.1", "project_contract_version: 1.0", 1
            )
            for name, text in files.items()
        }
        result = dispatch("validate_case", {"case_files": legacy})
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["data"]["case_schema_version"], "1.0")
        self.assertEqual(result["data"]["validated_files"], ALL_FILES)


if __name__ == "__main__":
    unittest.main()
