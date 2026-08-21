import unittest
from pathlib import Path

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
    "docs/架構說明.md",
    "docs/快速開始.md",
    "docs/安裝到ChatGPT-Project.md",
    "docs/更新與版本同步.md",
)


class RuleSourceReconciliationTests(unittest.TestCase):
    def _combined(self, files):
        return "\n".join((ROOT / p).read_text(encoding="utf-8") for p in files)

    def test_current_runtime_capabilities_are_not_documented_as_missing(self):
        combined = self._combined(CORE_FILES)
        self.assertNotIn("Project 紫微流月定位層", combined)
        self.assertNotIn("Project 紫微流日定位層", combined)
        self.assertNotIn("Project 紫微流時定位層", combined)
        self.assertNotIn("Project Bazi Calendar Engine", combined)
        self.assertNotIn("- Calendar / Input Resolver", combined)
        self.assertNotIn("紫微流時：`planned / on_demand`", combined)
        self.assertIn("Calendar Resolver v1", combined)
        self.assertIn("Ziwei Transformation Core", combined)
        self.assertIn("Ziwei Flying Core", combined)

    def test_phase2b_documented_state_matches_runtime(self):
        combined = self._combined(CORE_FILES + USER_DOCS)
        for required in (
            "ziwei-fine-cycle-lunar-late-zi-v1",
            "late_zi_forward-v1",
            "implemented / experimental / on_demand",
            "lunar-lite",
            "18/18 PASS",
            "iztro",
            "Astralium",
            "PENDING",
        ):
            self.assertIn(required, combined)
        self.assertIn("流曜", combined)
        self.assertIn("planned", combined.lower())

    def test_current_user_guidance_does_not_present_phase2b_as_missing_or_stable(self):
        quick = (ROOT / "docs/快速開始.md").read_text(encoding="utf-8")
        install = (ROOT / "docs/安裝到ChatGPT-Project.md").read_text(encoding="utf-8")
        current_guidance = quick + "\n" + install
        self.assertNotIn("Fine Cycle Stem Resolver 尚未固定", current_guidance)
        self.assertNotIn("流月／流日／流時四化與飛化 = planned / on_demand", current_guidance)
        self.assertNotIn("Fine Cycle Stem Resolver = implemented / stable", current_guidance)
        self.assertNotIn("Fine Cycle Stem Resolver = implemented / stable / default", current_guidance)
        self.assertIn("fine-cycle profile", current_guidance)

    def test_release_baseline_and_unreleased_overlay_are_explicitly_distinct(self):
        sync = (ROOT / "docs/更新與版本同步.md").read_text(encoding="utf-8")
        overlay_marker = "## 四點五、Unreleased Phase 2B 同步 overlay"
        baseline_marker = "## 五、v1.2.0 Capability 狀態"
        self.assertIn(overlay_marker, sync)
        self.assertIn(baseline_marker, sync)
        overlay = sync.split(overlay_marker, 1)[1].split(baseline_marker, 1)[0]
        baseline = sync.split(baseline_marker, 1)[1].split("## 六、", 1)[0]
        self.assertIn("implemented / experimental / on_demand / 1.0-exp", overlay)
        self.assertIn("流月／流日／流時四化與飛化 = planned / on_demand", baseline)
        self.assertIn("v1.2.0", baseline_marker)

    def test_user_docs_do_not_overclaim_as_stable_default(self):
        docs = self._combined(USER_DOCS)
        self.assertNotIn("Fine Cycle Stem Resolver = implemented / stable", docs)
        self.assertNotIn("Fine Cycle Stem Resolver = implemented / stable / default", docs)
        self.assertIn("Calendar Resolver", docs)
        self.assertIn("fine-cycle profile", docs)


if __name__ == "__main__":
    unittest.main()
