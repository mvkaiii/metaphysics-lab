import re
import unittest
from pathlib import Path

from engine.distribution.constants import (
    CASE_SCHEMA_VERSION,
    DISTRIBUTION_RUNTIME_VERSION,
    PROJECT_CONTRACT_VERSION,
    RUNTIME_SCHEMA_VERSION,
)
from engine.distribution.runtime import dispatch
from tools import build_ai_distribution


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist" / "ai"
EXPECTED_ARTIFACTS = {
    "metaphysics_lab.py",
    "metaphysics_core.md",
    "project_instructions.txt",
}


class AIDistributionAcceptanceTests(unittest.TestCase):
    def test_distribution_has_exactly_three_public_artifacts(self):
        files = {path.name for path in DIST.iterdir() if path.is_file()}
        self.assertEqual(files, EXPECTED_ARTIFACTS)
        self.assertFalse(any(path.suffix.lower() in {".pdf", ".png", ".jpg", ".jpeg", ".webp"} for path in DIST.iterdir()))

    def test_committed_artifacts_equal_deterministic_rebuild(self):
        expected = build_ai_distribution.render_distribution(ROOT)
        self.assertEqual(set(expected), EXPECTED_ARTIFACTS)
        for name, content in expected.items():
            self.assertEqual((DIST / name).read_bytes(), content, name)

    def test_generated_bundle_has_contract_versions_and_source_digest(self):
        text = (DIST / "metaphysics_lab.py").read_text(encoding="utf-8")
        self.assertIn("GENERATED FILE - DO NOT EDIT", text)
        self.assertRegex(text, r'SOURCE_DIGEST = [\'\"][0-9a-f]{64}[\'\"]')
        normalized = text.replace("'", '"')
        self.assertIn('PROJECT_CONTRACT_VERSION = "%s"' % PROJECT_CONTRACT_VERSION, normalized)
        self.assertIn('RUNTIME_SCHEMA_VERSION = "%s"' % RUNTIME_SCHEMA_VERSION, normalized)
        self.assertIn('CASE_SCHEMA_VERSION = "%s"' % CASE_SCHEMA_VERSION, normalized)
        self.assertIn('DISTRIBUTION_RUNTIME_VERSION = "%s"' % DISTRIBUTION_RUNTIME_VERSION, normalized)
        self.assertNotIn("tests/", text)
        self.assertNotIn("qualification/", text)
        self.assertNotIn("/mnt/data/", text)

    def test_fixed_markdown_has_no_dynamic_capability_snapshot(self):
        fixed = (
            (DIST / "metaphysics_core.md").read_text(encoding="utf-8")
            + (DIST / "project_instructions.txt").read_text(encoding="utf-8")
        )
        for forbidden in (
            "600/600",
            "814b77e6",
            "ziwei.flowing_stars =",
            "Phase 2C Ziwei Flowing Stars",
        ):
            self.assertNotIn(forbidden, fixed)
        self.assertIn("runtime_info", fixed)
        self.assertIn("Historical Blind Calibration", fixed)
        self.assertIn("00～04", fixed)
        self.assertIn("05～08", fixed)

    def test_runtime_capabilities_remain_unpromoted(self):
        result = dispatch("runtime_info", {})
        self.assertTrue(result["ok"], result)
        caps = result["data"]["capabilities"]
        self.assertEqual(caps["ziwei.flowing_stars"]["maturity"], "experimental")
        self.assertEqual(caps["ziwei.flowing_stars"]["routing"], "on_demand")
        self.assertEqual(caps["bazi.natal_chart"]["maturity"], "experimental")
        self.assertEqual(caps["ziwei.natal_chart"]["maturity"], "experimental")
        self.assertEqual(caps["natal.reconciliation"]["maturity"], "stable")
        self.assertEqual(caps["natal.markdown_export"]["maturity"], "stable")
        self.assertEqual(caps["historical.activation_selector"]["maturity"], "experimental")
        self.assertEqual(caps["historical.activation_selector"]["routing"], "on_demand")

    def test_formal_release_is_v1_6_0_without_capability_promotion(self):
        text = (ROOT / "VERSION.md").read_text(encoding="utf-8")
        formal = text.split("## 歷史版本", 1)[0]
        self.assertIn("Metaphysics Lab Core：**v1.6.0**", formal)
        self.assertIn("發布日期：**2026-09-05**", formal)
        self.assertIn("正式 release commit：`c325d754112df71c6747e17262d2e781d2864441`", formal)
        self.assertNotIn("PENDING_FINAL_QUALIFICATION", formal)
        self.assertIn("AI Distribution Pack", text)
        self.assertIn("AI Distribution Runtime：v1.1-exp", text)
        self.assertIn("release 本身不改變 capability maturity", text)
        self.assertNotRegex(formal, r"最新正式發布[\s\S]{0,100}v1\.4\.0")

    def test_distribution_contains_no_private_case_payload_files(self):
        self.assertEqual({path.name for path in DIST.iterdir()}, EXPECTED_ARTIFACTS)
        bundle = (DIST / "metaphysics_lab.py").read_text(encoding="utf-8")
        self.assertNotIn("raw Astralium chart payload", bundle)
        self.assertNotIn("private qualification evidence payload", bundle)
        self.assertNotIn("免費八字命盤_Kai.pdf", bundle)


if __name__ == "__main__":
    unittest.main()
