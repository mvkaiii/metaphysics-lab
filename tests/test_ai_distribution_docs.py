import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
QUICK = ROOT / "docs" / "快速開始.md"
INSTALL = ROOT / "docs" / "安裝到ChatGPT-Project.md"
UPDATE = ROOT / "docs" / "更新與版本同步.md"
CHANGELOG = ROOT / "CHANGELOG.md"

USER_ARTIFACTS = (
    "metaphysics_lab.py",
    "METAPHYSICS_CORE.md",
    "PROJECT_INSTRUCTIONS.md",
)
STARTUP = "開始建立我的命理專案。"


class AIDistributionDocsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readme = README.read_text(encoding="utf-8")
        cls.quick = QUICK.read_text(encoding="utf-8")
        cls.install = INSTALL.read_text(encoding="utf-8")
        cls.update = UPDATE.read_text(encoding="utf-8")
        cls.changelog = CHANGELOG.read_text(encoding="utf-8")

    def test_readme_first_use_names_two_uploads_one_instruction_artifact(self):
        head = self.readme[:5000]
        for name in USER_ARTIFACTS:
            self.assertIn(name, head)
        self.assertIn("上傳", head)
        self.assertIn("Project Instructions", head)
        self.assertIn(STARTUP, head)
        self.assertIn("High", head)

    def test_quick_start_is_ai_first_and_no_repo_module_install(self):
        for name in USER_ARTIFACTS:
            self.assertIn(name, self.quick)
        self.assertIn(STARTUP, self.quick)
        self.assertIn("High", self.quick)
        self.assertNotIn("requirements.txt", self.quick)
        self.assertNotIn("engine/", self.quick)
        self.assertNotIn("解壓", self.quick)

    def test_project_install_is_two_uploads_plus_one_copy(self):
        self.assertIn("上傳 `metaphysics_lab.py`", self.install)
        self.assertIn("上傳 `METAPHYSICS_CORE.md`", self.install)
        self.assertIn("`PROJECT_INSTRUCTIONS.md`", self.install)
        self.assertIn("Project Instructions", self.install)
        self.assertIn(STARTUP, self.install)
        self.assertNotIn("requirements.txt", self.install)
        self.assertNotIn("engine/", self.install)

    def test_docs_have_explicit_no_python_execution_fallback(self):
        combined = self.quick + self.install
        self.assertIn("無法執行 Python", combined)
        self.assertIn("python metaphysics_lab.py request --input", combined)
        self.assertIn("不得假裝", combined)

    def test_upgrade_is_runtime_only_by_default(self):
        self.assertIn("Project Contract", self.update)
        self.assertIn("Runtime", self.update)
        self.assertIn("Case Schema", self.update)
        self.assertIn("只替換 `metaphysics_lab.py`", self.update)
        self.assertIn("PROJECT_INSTRUCTIONS.md", self.update)
        self.assertIn("METAPHYSICS_CORE.md", self.update)
        self.assertIn("schema migration", self.update)
        self.assertIn("runtime_info", self.update)
        self.assertNotIn("ziwei.flowing_stars` 仍 planned", self.update)
        self.assertNotIn("ziwei.flowing_stars       planned", self.update)

    def test_changelog_has_ai_distribution_pack_unreleased_entry(self):
        head = self.changelog[:5000]
        self.assertIn("AI Distribution Pack", head)
        self.assertIn("metaphysics_lab.py", head)
        self.assertIn("九份", head)
        self.assertIn("VERSION.md", head)


if __name__ == "__main__":
    unittest.main()
