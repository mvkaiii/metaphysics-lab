import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROMPT = ROOT / "core" / "核心提示詞.md"
WORKFLOW = ROOT / "core" / "AI工作流程.md"
RULES = ROOT / "core" / "命理分析作業規範.md"
DIST_PROMPT = ROOT / "dist" / "ai" / "project_instructions.txt"
DIST_CORE = ROOT / "dist" / "ai" / "metaphysics_core.md"


class V19InstructionsCoreIntegrationTests(unittest.TestCase):
    @staticmethod
    def read(path):
        return path.read_text(encoding="utf-8")

    @classmethod
    def setUpClass(cls):
        cls.prompt = cls.read(PROMPT)
        cls.workflow = cls.read(WORKFLOW)
        cls.rules = cls.read(RULES)
        cls.combined = cls.prompt + "\n" + cls.workflow + "\n" + cls.rules

    def test_project_instructions_fit_limit_and_delegate_guided_natal_state(self):
        self.assertLessEqual(len(self.prompt), 8000)
        for phrase in (
            "natal.guided_build_state",
            "不得以聊天記憶",
            "next.action",
            "state_digest",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.prompt)

    def test_onboarding_uses_birth_time_state_not_mandatory_exact_clock_time(self):
        for phrase in (
            "birth_time_precision",
            "exact",
            "bounded",
            "unknown_time",
            "不知道出生時間",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.combined)

        obsolete = "命主稱呼、性別、出生年月日、出生時間、出生地"
        self.assertNotIn(obsolete, self.prompt)
        self.assertNotIn(obsolete, self.workflow)

    def test_runtime_state_owns_routing_and_ai_does_not_pick_fold_or_midpoint(self):
        for phrase in (
            "只執行 runtime 回傳的 \`next.action\`",
            "ambiguous_fold",
            "nonexistent",
            "不得自行選 fold occurrence",
            "不得自行取中點",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.combined)

    def test_case_revision_upgrade_is_explicit_and_preserves_history(self):
        for phrase in (
            "case_revision_upgrade_required",
            "case.replace_natal_base",
            "natal_revision_id",
            "base_case_digest",
            "保留 05～08",
            "不得回填",
            "舊 lock",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.combined)

    def test_new_blind_locks_bind_current_revision_without_rewriting_legacy_locks(self):
        for phrase in (
            "lock_provenance",
            "目前 Case revision",
            "新 Stage 1",
            "舊 lock 保持 immutable",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.combined)

    def test_candidate_envelope_profile_is_runtime_authority_not_ai_memory(self):
        for phrase in (
            "Candidate Envelope profile",
            "runtime validator",
            "不得以舊版 profile 記憶",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.combined)

    def test_generated_distribution_contains_same_v19_workflow_contract(self):
        dist_prompt = self.read(DIST_PROMPT)
        dist_core = self.read(DIST_CORE)
        for phrase in (
            "natal.guided_build_state",
            "birth_time_precision",
            "case.replace_natal_base",
        ):
            with self.subTest(prompt_phrase=phrase):
                self.assertIn(phrase, dist_prompt)
            with self.subTest(core_phrase=phrase):
                self.assertIn(phrase, dist_core)

        self.assertEqual(dist_prompt, self.prompt.rstrip() + "\n")

    def test_integration_does_not_promote_capabilities_or_redefine_prediction_method(self):
        self.assertIn("Experimental", self.combined)
        self.assertIn("maturity", self.combined)
        self.assertIn("routing", self.combined)
        self.assertIn("版本切換不得改 prediction method identity", self.combined)
        self.assertIn("不構成 Stable promotion", self.combined)
        self.assertNotIn("lin_tianji_v1.5-exp", self.combined)


if __name__ == "__main__":
    unittest.main()
