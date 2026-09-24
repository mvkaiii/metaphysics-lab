import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RELEASE_VERSION = "v1.7.0"
RELEASE_DATE = "2026-09-24"
RELEASE_COMMIT = "24760aa8766eb2691c8878f2cd8b97f0b37f8964"
CANDIDATE_SHA = "3153d5a49909094e16151c2cbbc487c2579dbff4"
USER_PACKAGE = "Metaphysics-Lab-v1.7.0-User-Package.zip"
USER_PACKAGE_SHA256 = "7de4285c0e7c79e2d4a311ec8a16b0866ac0820a303eb9a288dd63d50798cdd7"


class V17PostReleaseDocsTests(unittest.TestCase):
    def test_current_user_docs_identify_published_v170(self):
        for relative in (
            "README.md",
            "docs/快速開始.md",
            "docs/安裝到ChatGPT-Project.md",
            "docs/更新與版本同步.md",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(relative=relative):
                self.assertIn(f"{RELEASE_VERSION}｜{RELEASE_DATE}", text)
                self.assertNotIn("v1.7.0**（release candidate）", text)

    def test_v170_published_snapshot_identity_is_recorded(self):
        version = (ROOT / "VERSION.md").read_text(encoding="utf-8")
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        notes = (ROOT / "docs" / "發布說明-v1.7.0.md").read_text(encoding="utf-8")
        qualification = (ROOT / "docs" / "release" / "v1.7.0-qualification.md").read_text(encoding="utf-8")

        self.assertIn("Metaphysics Lab Core：**v1.7.0**", version)
        self.assertIn(f"發布日期：**{RELEASE_DATE}**", version)
        self.assertIn(f"正式 release commit：`{RELEASE_COMMIT}`", version)
        self.assertIn(f"## v1.7.0｜{RELEASE_DATE}", changelog)
        self.assertIn(RELEASE_COMMIT, notes)
        self.assertIn(CANDIDATE_SHA, notes)
        self.assertIn(USER_PACKAGE, changelog)
        self.assertIn(USER_PACKAGE_SHA256, changelog)
        self.assertIn("PASS and published", qualification)

    def test_v16_historical_release_identity_remains_present(self):
        version = (ROOT / "VERSION.md").read_text(encoding="utf-8")
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("Metaphysics Lab Core：**v1.6.0**", version)
        self.assertIn("發布日期：**2026-09-05**", version)
        self.assertIn("正式 release commit：`c325d754112df71c6747e17262d2e781d2864441`", version)
        self.assertIn("## v1.6.0｜2026-09-05", changelog)


if __name__ == "__main__":
    unittest.main()
