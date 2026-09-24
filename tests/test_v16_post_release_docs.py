import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RELEASE_VERSION = "v1.6.0"
RELEASE_DATE = "2026-09-05"
RELEASE_COMMIT = "c325d754112df71c6747e17262d2e781d2864441"
USER_PACKAGE = "Metaphysics-Lab-v1.6.0-User-Package.zip"


class V16PostReleaseDocsTests(unittest.TestCase):
    def test_historical_v160_release_surface_remains_documented(self):
        update = (ROOT / "docs" / "更新與版本同步.md").read_text(encoding="utf-8")
        release_notes = (ROOT / "docs" / "發布說明-v1.6.0.md").read_text(encoding="utf-8")

        self.assertIn("v1.5.0 → v1.6.0", update)
        self.assertIn(USER_PACKAGE, update)
        self.assertIn("Metaphysics Lab v1.6.0", release_notes)
        self.assertIn("Experimental / Project-derived", release_notes)

    def test_v160_published_snapshot_identity_is_immutable(self):
        version = (ROOT / "VERSION.md").read_text(encoding="utf-8")
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

        self.assertIn("Metaphysics Lab Core：**v1.6.0**", version)
        self.assertIn(f"發布日期：**{RELEASE_DATE}**", version)
        self.assertIn(f"正式 release commit：`{RELEASE_COMMIT}`", version)
        self.assertIn("## v1.6.0｜2026-09-05", changelog)


if __name__ == "__main__":
    unittest.main()
