from pathlib import Path
import unittest

from engine.historical.selector import completed_flow_year_periods


ROOT = Path(__file__).resolve().parents[1]
PROJECT_PROMPT = ROOT / "core" / "核心提示詞.md"
ANALYSIS_RULES = ROOT / "core" / "命理分析作業規範.md"
AI_WORKFLOW = ROOT / "core" / "AI工作流程.md"


class ProjectUXContractTests(unittest.TestCase):
    @staticmethod
    def _read(path):
        return path.read_text(encoding="utf-8")

    def test_project_instructions_fit_chatgpt_project_limit_and_keep_bootstrap_contract(self):
        prompt = self._read(PROJECT_PROMPT)
        self.assertLessEqual(len(prompt), 8000)
        for phrase in (
            "metaphysics_core.md",
            "Python 算盤，AI 讀盤",
            "Birth Data first",
            "runtime_info",
            "offline registry",
            "Astralium",
            "可選",
            "不得假裝已執行",
            "白話為主",
            "過去事件校準",
        ):
            self.assertIn(phrase, prompt)

    def test_post_natal_flow_calibrates_previous_ten_years_and_materializes_markdown(self):
        combined = self._read(ANALYSIS_RULES) + "\n" + self._read(AI_WORKFLOW)
        for phrase in (
            "本命盤建立完成後",
            "過去 10 年",
            "排除今年",
            "從去年往前",
            "05_驗證事件紀錄.md",
            "實際產生",
            "下載",
        ):
            self.assertIn(phrase, combined)

    def test_user_facing_analysis_prefers_natural_language_over_internal_terms(self):
        rules = self._read(ANALYSIS_RULES)
        for phrase in (
            "自然語言",
            "本段結論",
            "白話＋命理邏輯",
            "盤面可能性",
            "現實拆解",
            "適合的方向",
            "宜",
            "忌",
            "方向建議",
            "內部術語",
        ):
            self.assertIn(phrase, rules)

    def test_user_facing_case_language_hides_internal_execution_terms(self):
        combined = self._read(PROJECT_PROMPT) + "\n" + self._read(AI_WORKFLOW) + "\n" + self._read(ANALYSIS_RULES)
        for phrase in (
            "本命基礎檔案",
            "內部執行預設靜默",
            "不要向使用者直播",
            "Base Case",
            "runtime_info",
            "subject_id",
            "materialize",
        ):
            self.assertIn(phrase, combined)
        self.assertIn("對外稱", combined)

    def test_progressive_records_are_never_precreated_and_tracking_needs_real_use(self):
        combined = self._read(AI_WORKFLOW) + "\n" + self._read(ANALYSIS_RULES)
        for phrase in (
            "不得在首次建盤時預先建立 05～08",
            "05_驗證事件紀錄.md",
            "完成過去事件校準",
            "06_流年追蹤紀錄.md",
            "07_問事追蹤紀錄.md",
            "08_重大決策紀錄.md",
            "使用者明確同意保存",
            "真正有對應紀錄時才建立",
        ):
            self.assertIn(phrase, combined)

    def test_existing_case_files_are_replaced_not_duplicated_with_suffixes(self):
        combined = self._read(PROJECT_PROMPT) + "\n" + self._read(AI_WORKFLOW) + "\n" + self._read(ANALYSIS_RULES)
        for phrase in (
            "更新既有檔案時要替換原檔",
            "命主索引1.md",
            "不得把副本檔名當正式檔案",
            "先移除舊版同名檔案再上傳新版",
        ):
            self.assertIn(phrase, combined)

    def test_annual_analysis_has_overview_then_capability_driven_time_breakdown(self):
        rules = self._read(ANALYSIS_RULES)
        for phrase in (
            "全年主軸",
            "時間節奏",
            "月份",
            "區間",
            "12 個月",
            "不得自行補造月級",
        ):
            self.assertIn(phrase, rules)

    def test_calibration_reference_year_window_excludes_current_gregorian_year_even_before_lichun(self):
        periods = completed_flow_year_periods("2026-01-15T12:00:00+08:00", "Asia/Taipei")
        self.assertEqual([item["label_year"] for item in periods], list(range(2016, 2026)))


if __name__ == "__main__":
    unittest.main()
