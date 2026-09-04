import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RELEASE_VERSION = "v1.6.0"
RELEASE_DATE = "2026-09-05"
RELEASE_COMMIT = "c325d754112df71c6747e17262d2e781d2864441"
USER_PACKAGE = "Metaphysics-Lab-v1.6.0-User-Package.zip"


class V16PostReleaseDocsTests(unittest.TestCase):
    def test_current_user_docs_point_to_v160_release(self):
        for relative in (
            "README.md",
            "docs/快速開始.md",
            "docs/安裝到ChatGPT-Project.md",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(RELEASE_VERSION, text, relative)
            self.assertIn(USER_PACKAGE, text, relative)

    def test_current_state_docs_record_v160_as_published(self):
        version = (ROOT / "VERSION.md").read_text(encoding="utf-8")
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        update = (ROOT / "docs" / "更新與版本同步.md").read_text(encoding="utf-8")
        architecture = (ROOT / "docs" / "架構說明.md").read_text(encoding="utf-8")

        self.assertIn("Metaphysics Lab Core：**v1.6.0**", version)
        self.assertIn(f"發布日期：**{RELEASE_DATE}**", version)
        self.assertIn(f"正式 release commit：`{RELEASE_COMMIT}`", version)
        self.assertIn("## v1.6.0｜2026-09-05", changelog)
        self.assertIn("目前正式版本為 **v1.6.0｜2026-09-05**", update)
        self.assertIn("v1.5.0 → v1.6.0", update)
        self.assertIn("目前正式版本為 **v1.6.0｜2026-09-05**", architecture)


if __name__ == "__main__":
    unittest.main()
