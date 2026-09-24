import unittest
from pathlib import Path

from engine.distribution.guided_inquiry import suggest_inquiries


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "docs" / "release" / "v1.7.0-isolated-sandbox-script.md"
AI_WORKFLOW = ROOT / "core" / "AI工作流程.md"
PROJECT_INSTRUCTIONS = ROOT / "core" / "核心提示詞.md"
DIST_CORE = ROOT / "dist" / "ai" / "metaphysics_core.md"
DIST_INSTRUCTIONS = ROOT / "dist" / "ai" / "project_instructions.txt"


class V17SandboxFollowupRegressionTests(unittest.TestCase):
    def test_s03_contract_does_not_use_opt_out_language(self):
        script = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("script_version: v1.7.0-isolated-sandbox-script.v3", script)
        self.assertIn("User prompt: `好，接著還能看什麼？`", script)
        s03 = script.split("### S03", 1)[1].split("### S04", 1)[0]
        self.assertNotIn("User prompt: `先到這裡。`", s03)

    def test_post_answer_can_use_distinct_fourth_direction(self):
        payload = {
            "mode": "post_answer",
            "case_health": "PASS",
            "user_opted_out": False,
            "blocking_state": "none",
            "case_integrity_action_available": False,
            "pending_forecast_available": True,
            "current_answer": {
                "primary_domain": "career",
                "target_scope": "yearly",
                "allowed_specificity": "event_family",
                "time_refinement_scopes": ["monthly"],
                "actionable_options_present": True,
                "forecast_lock_eligible": False,
                "related_domains": [],
            },
        }
        result = suggest_inquiries(payload)
        self.assertFalse(result["suppressed"])
        self.assertEqual(len(result["suggestions"]), 4)
        self.assertEqual(
            [row["type"] for row in result["suggestions"]],
            ["deep_dive", "decision", "validation", "time_refine"],
        )
        self.assertEqual(result["suggestions"][2]["reason_code"], "pending_forecast_tracking")

    def test_entry_presentation_has_one_visible_batch_and_never_more_than_four(self):
        required = "入口只顯示一組，最多4個。"
        for path in (AI_WORKFLOW, PROJECT_INSTRUCTIONS, DIST_CORE, DIST_INSTRUCTIONS):
            with self.subTest(path=path.name):
                self.assertIn(required, path.read_text(encoding="utf-8"))

    def test_four_policy_suggestions_must_all_be_rendered(self):
        required = (
            "顯示前必須先呼叫 runtime `suggest_inquiries`",
            "不得自行新增第四個",
            "不得自行省略第四個",
        )
        for path in (AI_WORKFLOW, PROJECT_INSTRUCTIONS, DIST_CORE, DIST_INSTRUCTIONS):
            text = path.read_text(encoding="utf-8")
            for phrase in required:
                with self.subTest(path=path.name, phrase=phrase):
                    self.assertIn(phrase, text)

    def test_case_blocked_presentation_is_recovery_only(self):
        required = "BLOCKED 狀態下只提供解除 blocking conflict 的 recovery guidance；不得列出『衝突解除後可以問』的一般命理問題清單。"
        for path in (AI_WORKFLOW, PROJECT_INSTRUCTIONS, DIST_CORE, DIST_INSTRUCTIONS):
            with self.subTest(path=path.name):
                self.assertIn(required, path.read_text(encoding="utf-8"))

    def test_suggestion_wording_cannot_exceed_specificity_ceiling(self):
        required = "建議問題的文字本身也不得超過 specificity ceiling；不得把 event_family 改寫成升職、加薪或其他 event_form 故事。"
        for path in (AI_WORKFLOW, PROJECT_INSTRUCTIONS, DIST_CORE, DIST_INSTRUCTIONS):
            with self.subTest(path=path.name):
                self.assertIn(required, path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
