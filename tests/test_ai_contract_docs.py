from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CORE_PROMPT = ROOT / "core" / "核心提示詞.md"
ANALYSIS_RULES = ROOT / "core" / "命理分析作業規範.md"
AI_WORKFLOW = ROOT / "core" / "AI工作流程.md"


class AIContractDocsTests(unittest.TestCase):
    def _read(self, path):
        self.assertTrue(path.exists(), "%s must exist" % path.relative_to(ROOT))
        return path.read_text(encoding="utf-8")

    def test_fixed_contract_preserves_long_lived_governance(self):
        prompt = self._read(CORE_PROMPT)
        rules = self._read(ANALYSIS_RULES)
        combined = prompt + "\n" + rules

        for phrase in (
            "Precision must be earned by input",
            "External / Project / Resolved",
            "Project 原生盤面",
            "Project 推導盤面",
            "已驗證事件",
            "研究假說",
            "當次現實背景",
            "第一階段",
            "第二階段",
            "Experimental",
            "高風險",
            "多人",
        ):
            self.assertIn(phrase, combined)

    def test_fixed_contract_delegates_current_capability_state_to_runtime(self):
        prompt = self._read(CORE_PROMPT)
        rules = self._read(ANALYSIS_RULES)
        workflow = self._read(AI_WORKFLOW)
        combined = "\n".join((prompt, rules, workflow))

        self.assertIn("runtime_info", combined)
        self.assertIn("runtime manifest", combined.lower())
        self.assertIn("maturity", combined)
        self.assertIn("不得假裝已執行", combined)

    def test_fixed_contract_does_not_embed_fast_changing_runtime_snapshot(self):
        prompt = self._read(CORE_PROMPT)
        rules = self._read(ANALYSIS_RULES)
        workflow = self._read(AI_WORKFLOW)
        combined = "\n".join((prompt, rules, workflow))

        forbidden = (
            "Phase 2B",
            "Phase 2C",
            "Phase 2C0",
            "ziwei.flowing_stars =",
            "ziwei.flowing_stars` =",
            "600/600",
            "6120",
            "814b77e",
            "Astralium flowing-stars private qualification",
        )
        for phrase in forbidden:
            self.assertNotIn(phrase, combined, "fixed contract contains dynamic snapshot: %s" % phrase)

    def test_workflow_requires_real_file_update_for_persistent_case_changes(self):
        workflow = self._read(AI_WORKFLOW)
        self.assertIn("永久", workflow)
        self.assertIn("新版", workflow)
        self.assertIn(".md", workflow)
        self.assertIn("替換", workflow)
        self.assertIn("不能執行 Python", workflow)

    def test_phase5_user_safe_disclosure_translates_internal_engineering_terms(self):
        combined = "\n".join((
            self._read(CORE_PROMPT),
            self._read(ANALYSIS_RULES),
            self._read(AI_WORKFLOW),
        ))
        for phrase in (
            "activation high",
            "maturity experimental",
            "specificity ceiling",
            "eligibility gate",
            "dependency family",
            "ordinal score",
            "historical_modifier_scaled",
            "ranking_digest",
            "repo 維護",
            "technical audit",
            "內部術語",
        ):
            self.assertIn(phrase, combined)

    def test_phase5_technical_governance_preserves_ranking_authority(self):
        rules = (ROOT / "core" / "命理推導計算規則.md").read_text(encoding="utf-8")
        for phrase in (
            "lin_tianji_interpretation_contract_v1-exp",
            "Phase 3",
            "唯一 base ranking authority",
            "ranking_authority=false",
            "PRIMARY_DOMAIN_DISPLAY_LIMIT = 3",
            "不得建立第二套 maturity / specificity",
            "known reality",
            "不得改寫 prospective hit",
        ):
            self.assertIn(phrase, rules)


if __name__ == "__main__":
    unittest.main()