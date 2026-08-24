import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
QUICK = ROOT / "docs" / "快速開始.md"
INSTALL = ROOT / "docs" / "安裝到ChatGPT-Project.md"
DATA_GUIDE = ROOT / "docs" / "命盤資料準備指南.md"
UPDATE = ROOT / "docs" / "更新與版本同步.md"
CHANGELOG = ROOT / "CHANGELOG.md"
RELEASE_NOTES = ROOT / "docs" / "發布說明-v1.3.0.md"

USER_ARTIFACTS = (
    "metaphysics_lab.py",
    "METAPHYSICS_CORE.md",
    "PROJECT_INSTRUCTIONS.md",
)
USER_LABELS = (
    "命理計算程式",
    "命理分析核心規則",
    "Project 設定指令",
)
STARTUP = "開始建立我的命理專案。"


class AIDistributionDocsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readme = README.read_text(encoding="utf-8")
        cls.quick = QUICK.read_text(encoding="utf-8")
        cls.install = INSTALL.read_text(encoding="utf-8")
        cls.data_guide = DATA_GUIDE.read_text(encoding="utf-8")
        cls.update = UPDATE.read_text(encoding="utf-8")
        cls.changelog = CHANGELOG.read_text(encoding="utf-8")

    def test_readme_first_use_is_plain_language_download_flow(self):
        head = self.readme[:5000]
        for name in USER_ARTIFACTS:
            self.assertIn(name, head)
        for label in USER_LABELS:
            self.assertIn(label, head)
        self.assertIn("下載區", head)
        self.assertIn("GitHub 顯示為 Assets", head)
        self.assertIn("不需要下載 Source code", head)
        self.assertIn("不需要解壓縮", head)
        self.assertIn(STARTUP, head)
        self.assertIn("較高推理", head)
        self.assertNotIn("Draft PR #160", head)
        self.assertNotIn("implementation / maturity / routing", head)

    def test_quick_start_is_ai_first_and_no_repo_module_install(self):
        for name in USER_ARTIFACTS:
            self.assertIn(name, self.quick)
        for label in USER_LABELS:
            self.assertIn(label, self.quick)
        self.assertIn(STARTUP, self.quick)
        self.assertIn("較高推理", self.quick)
        self.assertNotIn("requirements.txt", self.quick)
        self.assertNotIn("engine/", self.quick)

    def test_project_install_is_two_uploads_plus_one_copy(self):
        self.assertIn("上傳 `metaphysics_lab.py`", self.install)
        self.assertIn("上傳 `METAPHYSICS_CORE.md`", self.install)
        self.assertIn("`PROJECT_INSTRUCTIONS.md`", self.install)
        self.assertIn("Project Instructions", self.install)
        for label in USER_LABELS:
            self.assertIn(label, self.install)
        self.assertIn(STARTUP, self.install)
        self.assertNotIn("requirements.txt", self.install)
        self.assertNotIn("engine/", self.install)

    def test_public_docs_offer_three_chart_source_paths(self):
        combined = self.readme + self.quick + self.data_guide
        self.assertIn("只有出生資料", combined)
        self.assertIn("出生資料 + Astralium", combined)
        self.assertIn("只有第三方排盤", combined)
        self.assertIn("Astralium", combined)
        self.assertIn("可選", combined)

    def test_user_facing_examples_are_fictional_and_not_private_kai_examples(self):
        for path in (README, QUICK, INSTALL, DATA_GUIDE):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("Kai", text, str(path))
            self.assertNotIn("1984年3月13日19:20", text, str(path))
        combined = self.quick + self.install + self.data_guide
        self.assertIn("虛構", combined)
        self.assertTrue("Alex" in combined or "Mina" in combined)

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

    def test_changelog_has_plain_language_v1_3_0_summary_before_technical_history(self):
        head = self.changelog[:9000]
        self.assertIn("## v1.3.0｜2026-08-23", head)
        self.assertIn("一般使用者摘要", head)
        self.assertIn("Astralium", head)
        self.assertIn("metaphysics_lab.py", head)
        self.assertIn("GitHub Release", head)

    def test_repo_has_canonical_plain_language_v1_3_0_release_note_source(self):
        self.assertTrue(RELEASE_NOTES.exists())
        text = RELEASE_NOTES.read_text(encoding="utf-8")
        self.assertIn("Metaphysics Lab v1.3.0", text)
        self.assertIn("下載區", text)
        for name in USER_ARTIFACTS:
            self.assertIn(name, text)
        for label in USER_LABELS:
            self.assertIn(label, text)
        self.assertIn("只有出生資料", text)
        self.assertIn("出生資料 + Astralium", text)
        self.assertIn("只有第三方排盤", text)


if __name__ == "__main__":
    unittest.main()
