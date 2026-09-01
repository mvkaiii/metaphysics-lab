import unittest
from pathlib import Path


def read(path):
    return Path(path).read_text(encoding="utf-8")


class HybridAICoordinationContractTests(unittest.TestCase):
    def test_ai_workflow_declares_python_coordination_authority(self):
        text = read("core/AI工作流程.md")
        self.assertIn("Python 算 coordination，AI 讀 coordination。", text)
        self.assertIn("coordination_relation", text)
        self.assertIn("parallel_signals", text)
        self.assertIn("legacy_cross_system_relation", text)
        self.assertIn("coordination_specificity_cap", text)

    def test_core_prompt_prevents_ai_recomputation_and_conflict_rewrite(self):
        text = read("core/核心提示詞.md")
        self.assertIn("coordination metadata", text)
        self.assertIn("不得自行重算", text)
        self.assertIn("parallel_signals", text)
        self.assertIn("legacy relation", text)
        self.assertIn("specificity", text)

    def test_architecture_keeps_single_prompt_authority_and_coordination_layer(self):
        text = read("docs/架構說明.md")
        self.assertIn("Claim Evidence -> Coordination v2 -> AI interpretation", text)
        self.assertIn("不重新計算 coordination", text)
        self.assertIn("不得建立第二套 prompt authority", text)


if __name__ == "__main__":
    unittest.main()
