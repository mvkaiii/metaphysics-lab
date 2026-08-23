from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]

CANONICAL_DOCS = [
    ROOT / "README.md",
    ROOT / "core" / "核心提示詞.md",
    ROOT / "core" / "AI工作流程.md",
    ROOT / "core" / "命理分析作業規範.md",
    ROOT / "docs" / "快速開始.md",
    ROOT / "docs" / "安裝到ChatGPT-Project.md",
    ROOT / "docs" / "更新與版本同步.md",
    ROOT / "docs" / "架構說明.md",
    ROOT / "docs" / "命盤資料準備指南.md",
    ROOT / "docs" / "Astralium資料取得指南.md",
    ROOT / "docs" / "資料治理.md",
]


class DocumentationContractConsistencyTests(unittest.TestCase):
    def test_canonical_docs_do_not_use_superseded_runtime_or_case_language(self):
        forbidden = (
            "兩支 Python 引擎",
            "Metaphysics Lab v1.1 已能自行建立",
            "Project 紫微流月目前只包含",
            "目前不自行建立：\n\n- 紫微流日\n- 紫微流時",
        )
        for path in CANONICAL_DOCS:
            text = path.read_text(encoding="utf-8")
            for phrase in forbidden:
                self.assertNotIn(phrase, text, "%s still contains superseded wording: %s" % (path, phrase))

    def test_user_facing_data_layer_docs_use_current_eight_layer_model(self):
        for relative in (
            "docs/命盤資料準備指南.md",
            "docs/資料治理.md",
            "docs/Astralium資料取得指南.md",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("Project 原生盤面", text, relative)
            self.assertIn("Project 推導盤面", text, relative)
            self.assertIn("已校驗資料", text, relative)
            self.assertIn("已驗證事件", text, relative)

    def test_user_facing_docs_delegate_dynamic_capability_truth_to_runtime_info(self):
        for relative in (
            "docs/命盤資料準備指南.md",
            "docs/Astralium資料取得指南.md",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("runtime_info", text, relative)
            self.assertNotIn("目前只包含", text, relative)

    def test_birth_time_guidance_matches_current_runtime_boundary(self):
        text = (ROOT / "docs" / "命盤資料準備指南.md").read_text(encoding="utf-8")
        self.assertIn("目前 runtime", text)
        self.assertIn("缺少出生時間", text)
        self.assertIn("不能建立單一完整 Project 本命", text)
        self.assertIn("不得自行補一個時辰", text)

    def test_progressive_case_names_are_used_in_user_facing_case_guidance(self):
        for relative in (
            "docs/命盤資料準備指南.md",
            "docs/Astralium資料取得指南.md",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("00_專案索引.md", text, relative)
            self.assertIn("01_命盤核心摘要.md", text, relative)
            self.assertIn("02_命盤資料校驗紀錄.md", text, relative)

    def test_future_guidance_does_not_skip_historical_calibration_gate(self):
        text = (ROOT / "docs" / "命盤資料準備指南.md").read_text(encoding="utf-8")
        self.assertIn("Historical Blind Calibration", text)
        self.assertIn("本命分析", text)
        self.assertIn("未來", text)
        self.assertNotIn("就可以開始本命與流年問事", text)


if __name__ == "__main__":
    unittest.main()
