import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / "core" / "AI工作流程.md"
PROMPT_PATH = ROOT / "core" / "核心提示詞.md"


class PredictionValidationAIContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        cls.prompt = PROMPT_PATH.read_text(encoding="utf-8")

    def _assert_governance(self, text):
        self.assertIn("已知的未來安排不能當成全新、未知前提下的預測", text)
        self.assertIn("已經存在但第一階段沒有告知模型的事實，不能算作乾淨的前向命中", text)
        self.assertIn("事件在鎖定前已經發生", text)
        self.assertIn("改走 Historical Calibration", text)
        self.assertIn("評估時必須分開計算，不得混成一個整體命中率", text)
        self.assertIn("先向使用者確認；不得猜測", text)

    def test_workflow_defines_all_validation_context_governance_in_natural_language(self):
        self._assert_governance(self.workflow)

    def test_core_prompt_defines_all_validation_context_governance_in_natural_language(self):
        self._assert_governance(self.prompt)

    def test_new_user_facing_governance_does_not_require_internal_v2_field_names(self):
        for text in (self.workflow, self.prompt):
            self.assertNotIn("validation_context_input", text)
            self.assertNotIn("clean_accuracy_eligible", text)
            self.assertNotIn("conditional_accuracy_eligible", text)
            self.assertNotIn("claim_contract_version", text)


if __name__ == "__main__":
    unittest.main()
