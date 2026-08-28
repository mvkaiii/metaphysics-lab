from pathlib import Path
import unittest

from engine.historical.selector import completed_flow_year_periods


ROOT = Path(__file__).resolve().parents[1]
PROJECT_PROMPT = ROOT / "core" / "核心提示詞.md"
ANALYSIS_RULES = ROOT / "core" / "命理分析作業規範.md"
AI_WORKFLOW = ROOT / "core" / "AI工作流程.md"
DATA_GUIDE = ROOT / "docs" / "命盤資料準備指南.md"


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

    def test_first_natal_onboarding_requires_subject_display_name_for_files(self):
        combined = self._read(PROJECT_PROMPT) + "\n" + self._read(AI_WORKFLOW) + "\n" + self._read(ANALYSIS_RULES)
        for phrase in (
            "命主稱呼",
            "必填",
            "用於檔名",
            "暱稱／代號",
            "不一定要真名",
            "不得使用 Project 擁有者",
            "不得使用目前聊天者",
        ):
            self.assertIn(phrase, combined)
        self.assertIn("命主稱呼、性別、出生年月日、出生時間、出生地", combined)

    def test_post_natal_flow_recommends_previous_ten_years_and_materializes_markdown_when_used(self):
        combined = self._read(ANALYSIS_RULES) + "\n" + self._read(AI_WORKFLOW)
        for phrase in (
            "本命盤建立完成後",
            "過去 10 年",
            "排除今年",
            "從去年往前",
            "建議但非強制",
            "05_驗證事件紀錄.md",
            "實際產生",
            "下載",
        ):
            self.assertIn(phrase, combined)

    def test_astralium_optional_supplement_files_keep_subject_identity(self):
        combined = self._read(PROJECT_PROMPT) + "\n" + self._read(AI_WORKFLOW) + "\n" + self._read(ANALYSIS_RULES) + "\n" + self._read(DATA_GUIDE)
        for phrase in (
            "03-1_Astralium八字資料包.md",
            "04-1_Astralium紫微資料包.md",
            "非 canonical",
            "可選外部參考附件",
            "subject_display_name",
            "大小寫差異",
            "Case 的正式命主稱呼",
            "Amy",
            "amy",
            "Allie",
            "不得生成",
        ):
            self.assertIn(phrase, combined)

    def test_historical_calibration_is_recommended_not_required_for_future_analysis(self):
        combined = self._read(PROJECT_PROMPT) + "\n" + self._read(AI_WORKFLOW) + "\n" + self._read(ANALYSIS_RULES) + "\n" + self._read(DATA_GUIDE)
        for phrase in (
            "建議但非強制",
            "未校準仍可直接進入",
            "uncalibrated",
            "不影響排盤本身的正確性",
            "個人化落地形式與信心校準會少一層證據",
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

    def test_user_facing_calibration_status_hides_engineering_terms(self):
        combined = self._read(PROJECT_PROMPT) + "\n" + self._read(AI_WORKFLOW) + "\n" + self._read(ANALYSIS_RULES)
        for phrase in (
            "內部校準狀態碼不得直接當成使用者結論",
            "`uncalibrated` →「尚未完成歷史事件校準」",
            "`basic` →「已完成初步校準」",
            "`calibrated` →「已完成較完整校準」",
            "`scorable` →「可正式評估」",
            "`unscorable` →「目前資料不足以正式評估」",
            "runtime validator",
            "schema",
            "migration",
            "除非使用者明確要求技術檢查",
            "不影響資料使用的純內部欄位名稱差異",
            "正常回答省略",
            "目前已完成初步校準",
        ):
            self.assertIn(phrase, combined)

    def test_user_facing_prose_uses_taiwan_traditional_chinese_without_unnecessary_english(self):
        combined = self._read(PROJECT_PROMPT) + "\n" + self._read(AI_WORKFLOW) + "\n" + self._read(ANALYSIS_RULES)
        for phrase in (
            "一般對使用者的敘述以台灣繁體中文完整表達",
            "不必要的英文",
            "英文副詞、形容詞、連接詞或一般動詞",
            "有自然中文說法",
            "一律改用中文",
            "專有名詞、產品名稱、檔名、程式識別字",
            "回答送出前",
            "檢查一般敘述",
            "individually",
            "單獨看",
        ):
            self.assertIn(phrase, combined)

    def test_phase5_known_reality_changes_strategy_not_forecast(self):
        combined = self._read(PROJECT_PROMPT) + "\n" + self._read(AI_WORKFLOW) + "\n" + self._read(ANALYSIS_RULES)
        for phrase in (
            "Interpretation Contract",
            "現實背景可以讓策略更具體",
            "不得改變 ranking",
            "不得提高 specificity",
            "不得把已知事實改寫成預測命中",
            "Stage 2 不得改寫 Stage 1",
        ):
            self.assertIn(phrase, combined)

    def test_phase5_disclosure_and_branding_boundary(self):
        combined = self._read(PROJECT_PROMPT) + "\n" + self._read(AI_WORKFLOW) + "\n" + self._read(ANALYSIS_RULES)
        for phrase in (
            "user_safe",
            "technical_rationale",
            "internal_only",
            "台灣繁體中文",
            "高層可稽核理由",
            "不公開精確 weight",
            "不公開精確 threshold",
            "Historical Personalization 不等於機率",
            "林氏天機",
            "method identity",
            "不作每句話的權威前綴",
        ):
            self.assertIn(phrase, combined)

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

    def test_case_delivery_offers_verified_zip_and_individual_markdown_without_claiming_download_success(self):
        combined = self._read(PROJECT_PROMPT) + "\n" + self._read(AI_WORKFLOW) + "\n" + self._read(ANALYSIS_RULES)
        for phrase in (
            "可驗證資料包交付",
            "ZIP",
            "完整性檢查",
            "Markdown 是正式資料",
            "ZIP 與單獨 `.md`",
            "同時提供",
            "個別下載",
            "同一份 canonical Markdown bytes",
            "逐 byte 完全相同",
            "不得宣稱下載成功",
            "重新產生新的附件",
            "檔案傳輸失敗",
            "只包含新增或真正變動的 Markdown",
        ):
            self.assertIn(phrase, combined)

    def test_case_delivery_treats_zip_as_cross_client_primary_and_markdown_as_best_effort(self):
        combined = self._read(PROJECT_PROMPT) + "\n" + self._read(AI_WORKFLOW) + "\n" + self._read(ANALYSIS_RULES)
        for phrase in (
            "跨 client 主要交付方式",
            "best-effort",
            "client route unavailable",
            "不要重新 render",
            "不要改成 `.txt`",
            "不要改副檔名",
            "不視為檔案生成失敗",
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
