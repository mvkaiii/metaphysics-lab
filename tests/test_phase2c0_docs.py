import unittest
from pathlib import Path

from engine.bazi.capabilities import get_capability as get_bazi_capability
from engine.ziwei.capabilities import get_capability as get_ziwei_capability


PATHS = {
    "work_rules": Path("core/命理分析作業規範.md"),
    "calc_rules": Path("core/命理推導計算規則.md"),
    "prompt": Path("core/核心提示詞.md"),
    "architecture": Path("docs/架構說明.md"),
    "quickstart": Path("docs/快速開始.md"),
    "install": Path("docs/安裝到ChatGPT-Project.md"),
    "update": Path("docs/更新與版本同步.md"),
    "readme": Path("README.md"),
    "changelog": Path("CHANGELOG.md"),
}


def read(name):
    return PATHS[name].read_text(encoding="utf-8")


class Phase2C0DocumentationTests(unittest.TestCase):
    def test_authoritative_rules_define_project_native_chart_as_eighth_data_class(self):
        rules = read("work_rules")
        self.assertIn("Project 原生盤面", rules)
        self.assertIn("八種資料類型", rules)
        self.assertIn("原始盤面事實", rules)
        self.assertIn("Project 推導盤面", rules)
        self.assertIn("命理推論", rules)

    def test_precision_and_missing_input_rules_are_explicit(self):
        combined = "\n".join((read("work_rules"), read("prompt"), read("architecture")))
        self.assertIn("Precision must be earned by input", combined)
        self.assertIn("不得自行補值", combined)
        self.assertIn("只追問缺少欄位", combined)
        self.assertIn("保留候選", combined)
        self.assertIn("降級分析", combined)

    def test_time_basis_and_calendar_boundary_are_documented(self):
        architecture = read("architecture")
        calc_rules = read("calc_rules")
        self.assertIn("reported_civil_time", architecture)
        self.assertIn("normalized_civil_time", architecture)
        self.assertIn("bazi_effective_time", architecture)
        self.assertIn("ziwei_effective_time", architecture)
        self.assertIn("Calendar Resolver 不負責真太陽時", architecture)
        self.assertIn("真太陽時＝經度校正＋均時差", calc_rules)
        self.assertIn("八字", calc_rules)
        self.assertIn("紫微", calc_rules)
        self.assertIn("獨立", calc_rules)

    def test_external_project_resolved_and_authority_policy_are_explicit(self):
        combined = "\n".join((read("work_rules"), read("architecture"), read("prompt")))
        self.assertIn("Astralium 為可選 external qualification source", combined)
        self.assertIn("External / Project / Resolved", combined)
        self.assertIn("MATCH / EQUIVALENT / CONFLICT / NOT_COMPARABLE", combined)
        self.assertIn("Experimental", combined)
        self.assertIn("Stable", combined)
        self.assertIn("不得覆寫", combined)

    def test_user_guidance_supports_mode_a_and_ambiguity_without_fake_precision(self):
        combined = "\n".join((read("quickstart"), read("install"), read("readme")))
        self.assertIn("男，1984年3月13日19:20，台北市出生", combined)
        self.assertIn("出生日期", combined)
        self.assertIn("出生時間", combined)
        self.assertIn("出生地", combined)
        self.assertIn("性別", combined)
        self.assertIn("只追問", combined)
        self.assertIn("候選", combined)
        self.assertIn("大概晚上7、8點", combined)

    def test_natal_capabilities_remain_experimental_after_phase2c_activation(self):
        self.assertEqual(get_bazi_capability("bazi.natal_chart")["maturity"], "experimental")
        ziwei_natal = get_ziwei_capability("ziwei.natal_chart")
        self.assertEqual(ziwei_natal["maturity"], "experimental")

        flowing = get_ziwei_capability("ziwei.flowing_stars")
        self.assertEqual(flowing["implementation"], "implemented")
        self.assertEqual(flowing["maturity"], "experimental")
        self.assertEqual(flowing["routing"], "on_demand")
        self.assertEqual(flowing["rule_version"], "1.0-exp")

        current_docs = "\n".join((read("readme"), read("changelog")))
        self.assertIn("ziwei.flowing_stars", current_docs)
        self.assertIn("implemented / experimental / on_demand", current_docs)
        self.assertIn("Phase 2C Ziwei Flowing Stars", current_docs)

        historical_docs = "\n".join((read("readme"), read("changelog"), read("update")))
        self.assertIn("Phase 2C0", historical_docs)
        self.assertIn("Experimental", historical_docs)


if __name__ == "__main__":
    unittest.main()
