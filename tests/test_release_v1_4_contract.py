from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
VERSION = ROOT / "VERSION.md"
CHANGELOG = ROOT / "CHANGELOG.md"
RULES = ROOT / "core" / "命理推導計算規則.md"
RELEASE_NOTES = ROOT / "docs" / "發布說明-v1.4.0.md"


class ReleaseV14ContractTests(unittest.TestCase):
    @staticmethod
    def _read(path):
        return path.read_text(encoding="utf-8")

    def test_v1_4_release_surface_is_consistent_without_maturity_promotion(self):
        readme = self._read(README)
        version = self._read(VERSION)
        changelog = self._read(CHANGELOG)
        rules = self._read(RULES)

        self.assertTrue(RELEASE_NOTES.exists(), "v1.4.0 user-facing release notes are missing")
        notes = self._read(RELEASE_NOTES)

        self.assertIn("目前正式版本為 **v1.4.0（2026-08-26）**", readme)
        self.assertIn("Metaphysics Lab Core：**v1.4.0**", version)
        self.assertIn("發布日期：**2026-08-26**", version)
        self.assertIn("docs/發布說明-v1.4.0.md", version)
        self.assertIn("## v1.4.0｜2026-08-26", changelog)
        self.assertNotIn("## Unreleased｜Project Contract 1.1 + Case Schema 1.1 + Portable Offline Natal", changelog)

        self.assertIn("# Metaphysics Lab v1.4.0", notes)
        self.assertIn("發布日期：**2026-08-26**", notes)
        for asset in ("metaphysics_lab.py", "metaphysics_core.md", "project_instructions.md"):
            self.assertIn(asset, notes)

        self.assertIn("正式 release identity 為 v1.4.0", rules)
        self.assertNotIn(
            "`leap_twelfth_month_second_half` 目前只有 synthetic internal coverage，屬 **not externally qualified**。",
            rules,
        )
        self.assertIn("86", rules)
        self.assertIn("0 mismatch", rules)
        self.assertIn("implemented / experimental / on_demand", rules)

        combined = version + "\n" + changelog + "\n" + notes + "\n" + rules
        self.assertIn("不提升", combined)
        self.assertIn("maturity", combined)


if __name__ == "__main__":
    unittest.main()
