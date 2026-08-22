from pathlib import Path
import unittest


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

    def test_core_prompt_requires_precision_and_resolved_source(self):
        text = _read("core/核心提示詞.md")
        for needle in (
            "Phase 2C Ziwei Flowing Stars",
            "ziwei-flowing-stars-common-v1",
            "implemented / experimental / on_demand",
            "Project 推導盤面",
            "輸入精度",
            "已解析來源",
        ):
            self.assertIn(needle, text)

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

    def test_readme_locks_capability_maturity_privacy_and_scope(self):
        text = _read("README.md")
        for needle in (
            "Phase 2C Ziwei Flowing Stars",
            "ziwei.flowing_stars",
            "implemented / experimental / on_demand",
            "Project 推導盤面",
            "Astralium flowing-stars",
            "PENDING",
            "歲前十二神",
            "將前十二神",
        ):
            self.assertIn(needle, text)

    def test_changelog_records_unreleased_phase2c_without_promotion(self):
        text = _read("CHANGELOG.md")
        for needle in (
            "## Unreleased｜Phase 2C Ziwei Flowing Stars",
            "ziwei-flowing-stars-common-v1",
            "implemented / experimental / on_demand",
            "Project 推導盤面",
            "Astralium flowing-stars",
            "PENDING",
            "歲前十二神",
            "將前十二神",
        ):
            self.assertIn(needle, text)

    def test_release_identity_remains_v120(self):
        text = _read("VERSION.md")
        self.assertIn("Metaphysics Lab Core：**v1.2.0**", text)
        self.assertNotIn("Phase 2C Ziwei Flowing Stars", text)


if __name__ == "__main__":
    unittest.main()
