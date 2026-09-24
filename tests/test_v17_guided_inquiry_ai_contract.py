import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "core" / "AI工作流程.md"
PROJECT_INSTRUCTIONS_SOURCE = ROOT / "core" / "核心提示詞.md"


class GuidedInquiryAIContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.instructions = PROJECT_INSTRUCTIONS_SOURCE.read_text(encoding="utf-8")
        cls.combined = cls.workflow + "\n" + cls.instructions

    def test_source_docs_define_user_facing_guided_inquiry_contract(self):
        required = (
            "主動顯示",
            "3～4 個",
            "預設 3 個",
            "已有 substantive 問題先回答",
            "不足 3 個合法建議就不顯示",
            "不得提高 specificity",
            "不得在盲判前用驗證事件產生建議",
            "使用者可以直接自由輸入、不必選建議",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.combined)

    def test_workflow_defines_session_entry_and_rendering_boundary(self):
        for phrase in (
            "第一次 assistant 回覆",
            "不是背景推播",
            "structured intents",
            "台灣繁體中文",
            "reason_code",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.workflow)
        self.assertIn("使用者可以直接自由輸入、不必選建議", self.workflow)

    def test_runtime_suggestion_count_is_mandatory_render_authority(self):
        workflow_required = (
            "顯示前必須先呼叫 runtime `suggest_inquiries`",
            "suggestions 陣列長度為 3 時，使用者可見輸出必須剛好 3 個",
            "suggestions 陣列長度為 4 時，使用者可見輸出必須剛好 4 個",
            "不得自行新增第四個",
            "不得自行省略第四個",
        )
        for phrase in workflow_required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.workflow)

        instructions_required = (
            "必須先呼叫 runtime `suggest_inquiries`",
            "不得自行決定顯示 3 個或 4 個",
            "不得自行新增第四個",
            "不得自行省略第四個",
        )
        for phrase in instructions_required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.instructions)

    def test_workflow_contains_conditional_career_rendering_examples(self):
        examples = (
            "把今年工作拆成月份，看哪些時段較適合主動推進",
            "進一步區分目前訊號偏責任、專案角色、職稱或雇主變動",
            "如果你手上已有兩個工作選項，可以直接做決策比較",
        )
        for example in examples:
            with self.subTest(example=example):
                self.assertIn(example, self.workflow)
        self.assertIn("specificity ceiling", self.workflow)
        self.assertIn("只有在", self.workflow)

    def test_project_instructions_preserve_blindness_and_free_form_input(self):
        for phrase in (
            "主動顯示",
            "預設 3 個",
            "不得在盲判前用驗證事件產生建議",
            "使用者可以直接自由輸入、不必選建議",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.instructions)


if __name__ == "__main__":
    unittest.main()
