import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class V18CompactPresentationPolicyTests(unittest.TestCase):
    def test_project_instructions_define_progressive_disclosure_without_authority_change(self):
        text = (ROOT / "core" / "核心提示詞.md").read_text(encoding="utf-8")
        for required in (
            "compact（預設）",
            "explain",
            "audit",
            "收斂的是呈現，不是分析",
            "最多 3 個主要判斷",
            "render_bazi_decadal_timeline",
            "原始 SVG bytes",
            "不得改變任何 deterministic truth、ranking、claim consumption、specificity ceiling、confidence、盲判內容或事件校準結果",
        ):
            self.assertIn(required, text)

    def test_core_spec_keeps_compact_as_presentation_only(self):
        text = (ROOT / "core" / "命理分析作業規範.md").read_text(encoding="utf-8")
        for required in (
            "v1.8 Presentation Contract：Compact by default",
            "compact / explain / audit",
            "Presentation profile **不得**修改或重新排序 Python authority",
            "source_commit",
            "Visualization為Experimental presentation surface",
        ):
            self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
