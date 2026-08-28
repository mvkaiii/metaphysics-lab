from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
RELEASE_NOTES = ROOT / "docs" / "發布說明-v1.4.0.md"
CHANGELOG = ROOT / "CHANGELOG.md"
RULES = ROOT / "core" / "命理推導計算規則.md"


class ReleaseV14HistoricalSnapshotTests(unittest.TestCase):
    def test_v1_4_historical_release_snapshot_is_preserved(self):
        self.assertTrue(RELEASE_NOTES.exists())
        notes = RELEASE_NOTES.read_text(encoding="utf-8")
        changelog = CHANGELOG.read_text(encoding="utf-8")
        rules = RULES.read_text(encoding="utf-8")
        self.assertIn("# Metaphysics Lab v1.4.0", notes)
        self.assertIn("發布日期：**2026-08-26**", notes)
        for asset in ("metaphysics_lab.py", "metaphysics_core.md", "project_instructions.md"):
            self.assertIn(asset, notes)
        self.assertIn("## v1.4.0｜2026-08-26", changelog)
        self.assertIn("86", rules)
        self.assertIn("0 mismatch", rules)


if __name__ == "__main__":
    unittest.main()
