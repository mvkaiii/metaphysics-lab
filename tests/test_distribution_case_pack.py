import unittest

from engine.distribution.constants import PROJECT_CONTRACT_VERSION
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
BASE_SLOTS = [
    "00_專案索引.md", "01_命盤核心摘要.md", "02_命盤資料校驗紀錄.md",
    "03_八字結構化資料包.md", "04_紫微基礎資料包.md",
]
PROGRESSIVE_SLOTS = ["05_驗證事件紀錄.md", "06_流年追蹤紀錄.md", "07_問事追蹤紀錄.md", "08_重大決策紀錄.md"]
ALL_SLOTS = BASE_SLOTS + PROGRESSIVE_SLOTS
REQUIRED_META = {
    "case_schema_version", "project_contract_version", "record_type", "subject_id",
    "subject_display_name", "subject_short_id", "filename_label", "created_at",
    "last_updated_at", "last_modified_by", "runtime_version_if_applicable",
    "source_classification", "mutation_policy",
}


def actual(slot):
    return "Kai_7F3A2C_" + slot


class DistributionCasePackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        built = dispatch("build_natal", {"birth": BIRTH, "resolved_location": LOCATION})
        if not built.get("ok"):
            raise AssertionError(built)
        cls.normalized = built["data"]["normalized_natal"]
        cls.base_payload = {
            "normalized_natal": cls.normalized,
            "subject_id": "subj_7f3a2c91d4e8",
            "subject_display_name": "Kai",
            "subject_short_id": "7F3A2C",
            "filename_label": "Kai",
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
        result = {}
        for line in lines[1:]:
            if line == "---":
                return result
            key, value = line.split(": ", 1)
            result[key] = value
        raise AssertionError("unterminated front matter")

    def append(self, files, slot, entry, when="2026-08-23T01:00:00+08:00"):
        return dispatch("update_case_record", {
            "case_files": files, "filename": slot, "operation": "append",
            "updated_at": when, "last_modified_by": "ai", "entry": entry,
        })

    def test_new_case_exports_only_base_files_deterministically(self):
        first = self.export()
        second = self.export()
        self.assertTrue(first["ok"], first)
        self.assertEqual(list(first["data"]["files"]), [actual(slot) for slot in BASE_SLOTS])
        self.assertEqual(first["data"]["files"], second["data"]["files"])
        index = first["data"]["files"][actual("00_專案索引.md")]
        self.assertIn("Historical Calibration: `uncalibrated`", index)
        self.assertIn("Kai_7F3A2C_05_驗證事件紀錄.md", index)

    def test_base_files_use_schema_contract_and_subject_identity(self):
        result = self.export()
        self.assertTrue(result["ok"], result)
        for name, text in result["data"]["files"].items():
            meta = self.front_matter(text)
            self.assertTrue(REQUIRED_META.issubset(meta), name)
            self.assertEqual(meta["case_schema_version"], "1.1")
            self.assertEqual(meta["project_contract_version"], PROJECT_CONTRACT_VERSION)
            self.assertEqual(meta["subject_id"], "subj_7f3a2c91d4e8")
            self.assertEqual(meta["subject_display_name"], "Kai")
            self.assertEqual(meta["subject_short_id"], "7F3A2C")

    def test_base_case_validates_without_progressive_files(self):
        exported = self.export()
        result = dispatch("validate_case", {"case_files": exported["data"]["files"]})
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["data"]["canonical_slots"], BASE_SLOTS)

    def test_bazi_and_ziwei_files_contain_facts_not_interpretation(self):
        result = self.export(analysis_sections={"長期框架": "這是明確標示的 AI 分析文字。"})
        files = result["data"]["files"]
        self.assertIn("bazi.pillars", files[actual("03_八字結構化資料包.md")])
        self.assertIn("ziwei.ming_palace", files[actual("04_紫微基礎資料包.md")])
        self.assertNotIn("命理推論", files[actual("03_八字結構化資料包.md")])
        self.assertIn("## 命理推論", files[actual("01_命盤核心摘要.md")])

    def test_first_verified_event_materializes_subject_prefixed_05_and_updates_index(self):
        files = self.export()["data"]["files"]
        result = self.append(files, "05_驗證事件紀錄.md", {"record_id": "evt-001", "status": "verified", "summary": "開始帶實習生"})
        self.assertTrue(result["ok"], result)
        changed = result["data"]["changed_files"]
        self.assertEqual(set(changed), {actual("00_專案索引.md"), actual("05_驗證事件紀錄.md")})
        self.assertIn("evt-001", changed[actual("05_驗證事件紀錄.md")])
        self.assertIn("✓ 05", changed[actual("00_專案索引.md")])

    def test_subsequent_verified_event_changes_only_05(self):
        exported = self.export()
        first = self.append(exported["data"]["files"], "05_驗證事件紀錄.md", {"record_id": "evt-001", "status": "verified", "summary": "第一件事"})
        files = dict(exported["data"]["files"])
        files.update(first["data"]["changed_files"])
        second = self.append(files, "05_驗證事件紀錄.md", {"record_id": "evt-002", "status": "verified", "summary": "第二件事"}, "2026-08-23T02:00:00+08:00")
        self.assertTrue(second["ok"], second)
        self.assertEqual(list(second["data"]["changed_files"]), [actual("05_驗證事件紀錄.md")])
        text = second["data"]["changed_files"][actual("05_驗證事件紀錄.md")]
        self.assertEqual(text.count("<!-- Metaphysics Lab Case Template"), 1)

    def test_first_tracking_records_materialize_06_07_08_on_demand(self):
        samples = {
            "06_流年追蹤紀錄.md": {"record_id": "forecast-001", "blind_forecast": "第一版盲判"},
            "07_問事追蹤紀錄.md": {"record_id": "question-001", "blind_forecast": "第一版問事"},
            "08_重大決策紀錄.md": {"record_id": "decision-001", "decision": "是否轉職"},
        }
        for slot, entry in samples.items():
            with self.subTest(slot=slot):
                files = self.export()["data"]["files"]
                result = self.append(files, slot, entry)
                self.assertTrue(result["ok"], result)
                self.assertEqual(set(result["data"]["changed_files"]), {actual("00_專案索引.md"), actual(slot)})

    def test_case_1_1_round_trips_prospective_forecast_lock_without_schema_change(self):
        from engine.distribution.prospective import lock_prospective_forecast, resolve_query_anchor

        anchor = resolve_query_anchor({
            "query_anchor_at": "2026-08-26T17:00:00+08:00",
            "query_timezone": "Asia/Taipei",
            "target_start": "2026-08-01T00:00:00+08:00",
            "target_end": "2026-12-31T23:59:59+08:00",
            "question_reference": "case-1.1-prospective-roundtrip",
        })
        claim = {
            "claim_id": "claim-2026-09-work-001",
            "forecast_window": {"start": "2026-09-01T00:00:00+08:00", "end": "2026-09-30T23:59:59+08:00"},
            "primary_domain": "工作",
            "event_family": "職責變動",
            "prediction": "9 月內出現可被正式記錄的工作職責調整。",
            "matched_if": "正式職稱、管理範圍或書面職責至少一項在預測窗內改變。",
            "not_matched_if": "預測窗結束時，上述三項均未發生正式改變。",
            "evidence_layers": ["bazi.yearly", "ziwei.yearly"],
            "evidence_time_scales": ["yearly"],
            "capability_maturity": "stable",
            "confidence": "medium",
            "knowledge_cutoff_at": anchor["knowledge_cutoff_at"],
            "evaluation_eligibility": "clean_scorable",
            "contamination_state": "clean_prospective",
            "method_version": "lin_tianji_v1.5-exp",
        }
        locked = lock_prospective_forecast({"anchor": anchor, "claims": [claim]})

        exported = self.export()
        result = self.append(
            exported["data"]["files"],
            "06_流年追蹤紀錄.md",
            {"record_id": "prospective-lock-001", "prospective_forecast_lock": locked},
        )
        self.assertTrue(result["ok"], result)
        files = dict(exported["data"]["files"])
        files.update(result["data"]["changed_files"])

        validated = dispatch("validate_case", {"case_files": files})
        self.assertTrue(validated["ok"], validated)
        self.assertEqual(validated["data"]["case_schema_version"], "1.1")
        tracking = files[actual("06_流年追蹤紀錄.md")]
        self.assertIn(locked["canonical_digest"], tracking)
        self.assertIn("lin_tianji_v1.5-exp", tracking)

    def test_blind_forecast_replacement_is_rejected(self):
        exported = self.export()
        appended = self.append(exported["data"]["files"], "06_流年追蹤紀錄.md", {"record_id": "forecast-001", "blind_forecast": "第一版"})
        files = dict(exported["data"]["files"])
        files.update(appended["data"]["changed_files"])
        result = dispatch("update_case_record", {
            "case_files": files, "filename": actual("06_流年追蹤紀錄.md"), "operation": "replace_blind_forecast",
            "updated_at": "2026-08-23T02:00:00+08:00", "last_modified_by": "ai",
            "entry": {"record_id": "forecast-001", "blind_forecast": "偷偷改掉"},
        })
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "immutable_blind_forecast")

    def test_validate_case_detects_subject_mismatch(self):
        exported = self.export()
        first = self.append(exported["data"]["files"], "08_重大決策紀錄.md", {"record_id": "decision-001", "decision": "是否轉職"})
        files = dict(exported["data"]["files"])
        files.update(first["data"]["changed_files"])
        target = actual("08_重大決策紀錄.md")
        files[target] = files[target].replace("subject_id: subj_7f3a2c91d4e8", "subject_id: subj_aaaaaaaaaaaa", 1)
        result = dispatch("validate_case", {"case_files": files})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "case_subject_mismatch")

    def test_legacy_1_0_nine_file_case_remains_readable(self):
        exported = self.export()
        files = dict(exported["data"]["files"])
        for slot in PROGRESSIVE_SLOTS:
            entry = {"record_id": "legacy-" + slot[:2]}
            if slot == "05_驗證事件紀錄.md":
                entry.update({"status": "verified", "summary": "legacy event"})
            elif slot in ("06_流年追蹤紀錄.md", "07_問事追蹤紀錄.md"):
                entry["blind_forecast"] = "legacy forecast"
            else:
                entry["decision"] = "legacy decision"
            result = self.append(files, slot, entry)
            self.assertTrue(result["ok"], result)
            files.update(result["data"]["changed_files"])
        legacy = {}
        for slot in ALL_SLOTS:
            text = files[actual(slot)]
            text = text.replace("case_schema_version: 1.1", "case_schema_version: 1.0", 1)
            text = text.replace("project_contract_version: %s" % PROJECT_CONTRACT_VERSION, "project_contract_version: 1.0", 1)
            text = text.replace("subject_id: subj_7f3a2c91d4e8", "subject_id: case-legacy", 1)
            legacy[slot] = text
        result = dispatch("validate_case", {"case_files": legacy})
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["data"]["case_schema_version"], "1.0")
        self.assertEqual(result["data"]["validated_files"], ALL_SLOTS)


if __name__ == "__main__":
    unittest.main()
