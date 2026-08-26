from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROJECT_PROMPT = ROOT / "core" / "核心提示詞.md"
ANALYSIS_RULES = ROOT / "core" / "命理分析作業規範.md"
AI_WORKFLOW = ROOT / "core" / "AI工作流程.md"
DATA_GUIDE = ROOT / "docs" / "命盤資料準備指南.md"
ASTRALIUM_GUIDE = ROOT / "docs" / "Astralium資料取得指南.md"


class OptionalHistoricalCalibrationContractTests(unittest.TestCase):
    @staticmethod
    def read(path):
        return path.read_text(encoding="utf-8")

    def test_historical_calibration_is_recommended_but_not_required_for_use(self):
        combined = "\n".join(
            self.read(path)
            for path in (PROJECT_PROMPT, ANALYSIS_RULES, AI_WORKFLOW, DATA_GUIDE)
        )
        for phrase in (
            "建議做過去 10 年",
            "不是強制前置條件",
            "可以直接進入本命分析、流年、問事或決策分析",
            "Historical Calibration = uncalibrated",
            "尚未完成歷史事件校準",
            "個人化落地形式與信心校準",
        ):
            self.assertIn(phrase, combined)
        self.assertNotIn("不得跳過 Historical Calibration gate", combined)

    def test_astralium_guidance_documents_optional_supplement_slots_and_subject_name_rule(self):
        combined = self.read(PROJECT_PROMPT) + "\n" + self.read(AI_WORKFLOW) + "\n" + self.read(ASTRALIUM_GUIDE)
        for phrase in (
            "03-1_Astralium八字資料包.md",
            "04-1_Astralium紫微資料包.md",
            "外部命盤資料",
            "不取代 03",
            "不取代 04",
            "命主稱呼必須一致",
            "Amy",
            "amy",
            "Allie",
            "大小寫差異",
        ):
            self.assertIn(phrase, combined)


if __name__ == "__main__":
    unittest.main()
