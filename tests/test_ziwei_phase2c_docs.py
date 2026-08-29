from pathlib import Path
import unittest

from engine.distribution.runtime import dispatch


ROOT = Path(__file__).resolve().parents[1]


def _read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class ZiweiPhase2CDocsTests(unittest.TestCase):
    def test_rules_document_five_sources_and_no_recalculation(self):
        text = _read("core/命理推導計算規則.md")
        for needle in (
            "Phase 2C Ziwei Flowing Stars",
            "ziwei-flowing-stars-common-v1",
            "Project 推導盤面",
            "decadal",
            "yearly",
            "monthly",
            "daily",
            "hourly",
            "ResolvedCycleStem",
            "ZiweiDecadalPeriod.stem_branch",
        ):
            self.assertIn(needle, text)
        self.assertIn("不得重新推", text)

    def test_core_prompt_requires_precision_resolved_source_and_runtime_manifest(self):
        text = _read("core/核心提示詞.md")
        for needle in (
            "Precision must be earned by input",
            "External / Project / Resolved",
            "Project 推導盤面",
            "runtime_info",
            "runtime manifest",
        ):
            self.assertIn(needle, text)
        self.assertNotIn("Phase 2C Ziwei Flowing Stars", text)
        self.assertNotIn("ziwei-flowing-stars-common-v1", text)
        self.assertNotIn("600 source cases", text)

    def test_runtime_locks_flowing_star_capability_maturity_and_scope(self):
        result = dispatch("runtime_info", {})
        self.assertTrue(result["ok"], result)
        cap = result["data"]["capabilities"]["ziwei.flowing_stars"]
        self.assertEqual(cap["implementation"], "implemented")
        self.assertEqual(cap["maturity"], "experimental")
        self.assertEqual(cap["routing"], "on_demand")
        self.assertEqual(cap["rule_version"], "1.0-exp")
        self.assertEqual(cap["module"], "engine.ziwei.flowing_stars")
        self.assertEqual(cap["conditional_dependencies"]["monthly"], ["ziwei.flow_month_stem"])
        self.assertEqual(cap["conditional_dependencies"]["daily"], ["ziwei.flow_day_stem"])
        self.assertEqual(cap["conditional_dependencies"]["hourly"], ["ziwei.flow_hour_stem"])

    def test_architecture_keeps_flowing_stars_independent(self):
        text = _read("docs/架構說明.md")
        for needle in (
            "Phase 2C Ziwei Flowing Stars",
            "FlowingStarLayer",
            "CycleTransformationLayer",
            "chart_id + scope + reference",
            "ziwei-flowing-stars-common-v1",
        ):
            self.assertIn(needle, text)

    def test_readme_delegates_dynamic_phase2c_state_and_keeps_privacy_boundary(self):
        text = _read("README.md")
        for needle in (
            "runtime_info",
            "Project 推導盤面",
            "CHANGELOG.md",
            "私人 Astralium raw chart",
        ):
            self.assertIn(needle, text)
        self.assertNotIn("Phase 2C Ziwei Flowing Stars", text)
        self.assertNotIn("ziwei-flowing-stars-common-v1", text)
        self.assertNotIn("600/600", text)

    def test_changelog_records_phase2c_in_v130_without_promotion(self):
        text = _read("CHANGELOG.md")
        for needle in (
            "## v1.3.0｜2026-08-23",
            "### Phase 2C｜Ziwei Flowing Stars",
            "ziwei-flowing-stars-common-v1",
            "implemented / experimental / on_demand",
            "Project 推導盤面",
            "Astralium flowing-stars",
            "PENDING",
            "歲前十二神",
            "將前十二神",
        ):
            self.assertIn(needle, text)
        self.assertNotIn("## Unreleased｜Phase 2C Ziwei Flowing Stars", text)
        self.assertNotIn("ziwei.flowing_stars = implemented / stable", text)

    def test_current_release_is_v150_without_flowing_star_promotion(self):
        text = _read("VERSION.md")
        self.assertIn("Metaphysics Lab Core：**v1.5.0**", text)
        self.assertIn("Ziwei Flowing Stars：v1.0-exp", text)
        self.assertIn("`ziwei.flowing_stars` | implemented | experimental | on_demand", text)
        self.assertIn("Astralium flowing-stars            PENDING", text)
        self.assertNotIn("`ziwei.flowing_stars` | implemented | stable", text)
        self.assertIn("### v1.4.0｜2026-08-26", text)


if __name__ == "__main__":
    unittest.main()
