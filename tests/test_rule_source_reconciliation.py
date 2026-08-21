import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "core/命理分析作業規範.md",
    "core/命理推導計算規則.md",
    "core/核心提示詞.md",
    "core/紫微流月推導規則.md",
    "core/紫微流日推導規則.md",
    "core/紫微流時推導規則.md",
)

class RuleSourceReconciliationTests(unittest.TestCase):
    def test_current_runtime_capabilities_are_not_documented_as_missing(self):
        combined = "\n".join((ROOT / p).read_text(encoding="utf-8") for p in FILES)
        self.assertNotIn("Project 紫微流月定位層", combined)
        self.assertNotIn("Project 紫微流日定位層", combined)
        self.assertNotIn("Project 紫微流時定位層", combined)
        self.assertNotIn("Project Bazi Calendar Engine", combined)
        self.assertNotIn("- Calendar / Input Resolver", combined)
        self.assertNotIn("紫微流時：`planned / on_demand`", combined)
        self.assertIn("Calendar Resolver v1", combined)
        self.assertIn("Ziwei Transformation Core", combined)
        self.assertIn("Ziwei Flying Core", combined)

    def test_fine_cycle_transformations_are_not_prematurely_marked_implemented(self):
        text = (ROOT / "core/命理推導計算規則.md").read_text(encoding="utf-8")
        self.assertIn("流月／流日／流時細部四化", text)
        self.assertIn("planned / on_demand", text)

if __name__ == "__main__":
    unittest.main()
