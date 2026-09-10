import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CURRENT_VERSION = "v1.7.0"
USER_PACKAGE = "Metaphysics-Lab-v1.7.0-User-Package.zip"
CURRENT_DOCS = (
    ROOT / "README.md",
    ROOT / "docs" / "快速開始.md",
    ROOT / "docs" / "安裝到ChatGPT-Project.md",
    ROOT / "docs" / "更新與版本同步.md",
)
RELEASE_NOTES = ROOT / "docs" / "發布說明-v1.7.0.md"


class V17DocsTests(unittest.TestCase):
    def test_current_user_docs_identify_v170_and_case_schema_1_1(self):
        for path in CURRENT_DOCS:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertIn(CURRENT_VERSION, text)
                self.assertIn("Case Schema 1.1", text)
                self.assertTrue(
                    "不需要重建" in text or "不要求重建" in text or "不要重建" in text,
                    f"{path}: must explicitly preserve existing Case data without destructive rebuild",
                )

    def test_install_surfaces_point_to_v170_three_file_user_package(self):
        for relative in (
            "README.md",
            "docs/快速開始.md",
            "docs/安裝到ChatGPT-Project.md",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(relative=relative):
                self.assertIn(USER_PACKAGE, text)
                self.assertIn("metaphysics_lab.py", text)
                self.assertIn("metaphysics_core.md", text)
                self.assertIn("project_instructions.txt", text)

    def test_v16_to_v17_upgrade_replaces_all_three_distribution_files_together(self):
        text = (ROOT / "docs" / "更新與版本同步.md").read_text(encoding="utf-8")
        self.assertIn("v1.6.0 → v1.7.0", text)
        self.assertIn("三個檔案一起", text)
        self.assertIn("Metaphysics-Lab-v1.7.0-User-Package.zip", text)
        self.assertIn("替換 Project 中的 `metaphysics_lab.py`", text)
        self.assertIn("替換 `metaphysics_core.md`", text)
        self.assertIn("`project_instructions.txt`", text)
        self.assertIn("保留", text)
        self.assertIn("Case Schema 1.1", text)

    def test_v170_release_notes_state_reliability_and_governance_boundaries(self):
        self.assertTrue(RELEASE_NOTES.exists())
        text = RELEASE_NOTES.read_text(encoding="utf-8")
        for phrase in (
            "Metaphysics Lab v1.7.0",
            "3～4 個",
            "預設 3 個",
            "Case Doctor",
            "不自動刪除",
            "conditional_prospective",
            "hidden_existing_reality",
            "clean prospective denominator",
            "Case Schema 1.1",
            "Experimental",
            "不因 v1.7 發布而自動升級",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
