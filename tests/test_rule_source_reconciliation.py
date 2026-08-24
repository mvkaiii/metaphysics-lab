import unittest
from pathlib import Path

from engine.distribution.runtime import dispatch


ROOT = Path(__file__).resolve().parents[1]
CORE_FILES = (
    "core/命理分析作業規範.md",
    "core/命理推導計算規則.md",
    "core/核心提示詞.md",
    "core/紫微流月推導規則.md",
    "core/紫微流日推導規則.md",
    "core/紫微流時推導規則.md",
)
USER_DOCS = (
    "README.md",
    "docs/快速開始.md",
    "docs/安裝到ChatGPT-Project.md",
    "docs/更新與版本同步.md",
)


class RuleSourceReconciliationTests(unittest.TestCase):
    def _combined(self, files):
        return "\n".join((ROOT / p).read_text(encoding="utf-8") for p in files)

    def test_current_runtime_capabilities_are_registry_driven_not_documented_as_missing(self):
        combined = self._combined(CORE_FILES)
        self.assertNotIn("Project 紫微流月定位層", combined)
        self.assertNotIn("Project 紫微流日定位層", combined)
        self.assertNotIn("Project 紫微流時定位層", combined)
        self.assertNotIn("紫微流時：`planned / on_demand`", combined)
        self.assertIn("runtime_info", combined)

        result = dispatch("runtime_info", {})
        self.assertTrue(result["ok"], result)
        caps = result["data"]["capabilities"]
        self.assertEqual(caps["ziwei.transformations"]["implementation"], "implemented")
        self.assertEqual(caps["ziwei.transformations"]["maturity"], "stable")
        self.assertEqual(caps["ziwei.flying"]["implementation"], "implemented")
        self.assertEqual(caps["ziwei.flying"]["maturity"], "stable")
        self.assertEqual(caps["ziwei.flow_hour_palaces"]["implementation"], "implemented")

    def test_phase2b_historical_rules_match_runtime_without_user_doc_snapshot(self):
        historical = self._combined((
            "core/命理推導計算規則.md",
            "docs/架構說明.md",
            "CHANGELOG.md",
        ))
        for required in (
            "ziwei-fine-cycle-lunar-late-zi-v1",
            "late_zi_forward-v1",
            "lunar-lite",
            "18/18 PASS",
            "iztro",
            "Astralium",
            "PENDING",
        ):
            self.assertIn(required, historical)

        caps = dispatch("runtime_info", {})["data"]["capabilities"]
        for capability_id in (
            "ziwei.flow_month_stem",
            "ziwei.flow_day_stem",
            "ziwei.flow_hour_stem",
            "ziwei.flow_month_transformations",
            "ziwei.flow_day_transformations",
            "ziwei.flow_hour_transformations",
            "ziwei.flow_month_flying",
            "ziwei.flow_day_flying",
            "ziwei.flow_hour_flying",
        ):
            cap = caps[capability_id]
            self.assertEqual(cap["implementation"], "implemented")
            self.assertEqual(cap["maturity"], "experimental")
            self.assertEqual(cap["routing"], "on_demand")

    def test_current_user_guidance_delegates_capability_state_to_runtime(self):
        current_guidance = self._combined((
            "README.md",
            "docs/快速開始.md",
            "docs/安裝到ChatGPT-Project.md",
        ))
        self.assertNotIn("Fine Cycle Stem Resolver 尚未固定", current_guidance)
        self.assertNotIn("Fine Cycle Stem Resolver = implemented / stable", current_guidance)
        self.assertNotIn("Fine Cycle Stem Resolver = implemented / stable / default", current_guidance)
        self.assertIn("runtime_info", current_guidance)
        self.assertIn("metaphysics_lab.py", current_guidance)
        self.assertIn("較高推理", current_guidance)
        self.assertNotIn("High reasoning", current_guidance)

    def test_release_baseline_and_runtime_contract_are_explicitly_distinct(self):
        sync = (ROOT / "docs/更新與版本同步.md").read_text(encoding="utf-8")
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        version = (ROOT / "VERSION.md").read_text(encoding="utf-8")

        self.assertIn("Project Contract", sync)
        self.assertIn("Runtime", sync)
        self.assertIn("Case Schema", sync)
        self.assertIn("只替換 `metaphysics_lab.py`", sync)
        self.assertIn("## v1.3.0｜2026-08-23", changelog)
        self.assertIn("### Phase 2B｜Ziwei Fine Cycle Stem Resolver v1", changelog)
        self.assertIn("### Phase 2C｜Ziwei Flowing Stars", changelog)
        self.assertIn("Metaphysics Lab Core：**v1.3.0**", version)
        self.assertIn("AI Distribution Pack", version)
        self.assertIn("runtime_info", version)
        self.assertNotIn("## Unreleased｜Phase 2B", changelog)
        self.assertNotIn("## Unreleased｜Phase 2C Ziwei Flowing Stars", changelog)

    def test_user_docs_do_not_overclaim_dynamic_capability_state(self):
        docs = self._combined(USER_DOCS)
        self.assertNotIn("Fine Cycle Stem Resolver = implemented / stable", docs)
        self.assertNotIn("Fine Cycle Stem Resolver = implemented / stable / default", docs)
        self.assertIn("runtime_info", docs)
        self.assertIn("正式版本", docs)


if __name__ == "__main__":
    unittest.main()
