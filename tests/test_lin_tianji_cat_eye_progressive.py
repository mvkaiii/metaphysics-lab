import unittest

from engine.distribution.blind_sources import validate_blind_source_case
from engine.distribution.runtime import dispatch


BIRTH = {"sex": "male", "birth_date": "1984-03-13", "birth_time": "19:20", "birth_place": "台北市"}
LOCATION = {
    "canonical_name": "Taipei City, Taiwan", "latitude": 25.033, "longitude": 121.5654,
    "timezone": "Asia/Taipei", "provider_name": "ai_host", "provider_version": "synthetic-cat-eye",
    "provider_reference": None,
}


class CatEyeProgressiveIsolationTests(unittest.TestCase):
    def test_05_and_06_materialized_but_stage1_reads_base_only(self):
        built = dispatch("build_natal", {"birth": BIRTH, "resolved_location": LOCATION})
        self.assertTrue(built["ok"], built)
        exported = dispatch("export_case_markdown", {
            "normalized_natal": built["data"]["normalized_natal"],
            "subject_id": "subj_ca7e1e000001", "subject_display_name": "Synthetic", "subject_short_id": "CA7E1E",
            "filename_label": "Synthetic", "generated_at": "2026-08-29T00:00:00+08:00", "last_modified_by": "ai",
        })
        self.assertTrue(exported["ok"], exported)
        files = dict(exported["data"]["files"])
        first = dispatch("update_case_record", {
            "case_files": files, "filename": "05_驗證事件紀錄.md", "operation": "append",
            "updated_at": "2026-08-29T00:01:00+08:00", "last_modified_by": "ai",
            "entry": {"record_id": "evt-cat-eye", "status": "verified", "summary": "synthetic verified history"},
        })
        self.assertTrue(first["ok"], first)
        files.update(first["data"]["changed_files"])
        second = dispatch("update_case_record", {
            "case_files": files, "filename": "06_流年追蹤紀錄.md", "operation": "append",
            "updated_at": "2026-08-29T00:02:00+08:00", "last_modified_by": "ai",
            "entry": {"record_id": "forecast-cat-eye", "blind_forecast": "synthetic locked note"},
        })
        self.assertTrue(second["ok"], second)
        files.update(second["data"]["changed_files"])

        base = {name: text for name, text in files.items() if any(token in name for token in ("_00_", "_01_", "_02_", "_03_", "_04_"))}
        self.assertEqual(len(base), 5)
        result = validate_blind_source_case(base)
        self.assertEqual(result["status"], "validated")
        state = result["manifest_progressive_state"]
        self.assertTrue(state["05_驗證事件紀錄.md"])
        self.assertTrue(state["06_流年追蹤紀錄.md"])
        self.assertFalse(any("synthetic verified history" in text for text in base.values()))
        self.assertFalse(any("synthetic locked note" in text for text in base.values()))


if __name__ == "__main__":
    unittest.main()
