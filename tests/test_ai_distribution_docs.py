import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
QUICK = ROOT / "docs" / "快速開始.md"
INSTALL = ROOT / "docs" / "安裝到ChatGPT-Project.md"
DATA_GUIDE = ROOT / "docs" / "命盤資料準備指南.md"
ASTRALIUM_GUIDE = ROOT / "docs" / "Astralium資料取得指南.md"
UPDATE = ROOT / "docs" / "更新與版本同步.md"
GOVERNANCE = ROOT / "docs" / "資料治理.md"
ARCHITECTURE = ROOT / "docs" / "架構說明.md"
CHANGELOG = ROOT / "CHANGELOG.md"
RELEASE_NOTES = ROOT / "docs" / "發布說明-v1.4.0.md"
HISTORICAL_V130_RELEASE_NOTES = ROOT / "docs" / "發布說明-v1.3.0.md"
PROJECT_INSTRUCTIONS = ROOT / "dist" / "ai" / "project_instructions.txt"
CORE_WORKFLOW = ROOT / "core" / "AI工作流程.md"
PROJECT_INSTRUCTIONS_SOURCE = ROOT / "core" / "核心提示詞.md"

USER_ARTIFACTS = (
    "metaphysics_lab.py",
    "metaphysics_core.md",
    "project_instructions.txt",
)
V140_USER_ARTIFACTS = (
    "metaphysics_lab.py",
    "metaphysics_core.md",
    "project_instructions.md",
)
USER_LABELS = (
    "命理計算程式",
    "命理分析核心規則",
    "Project 設定指令",
)
STARTUP = "開始建立我的命理專案。"
PUBLIC_GUIDES = (
    README,
    QUICK,
    INSTALL,
    DATA_GUIDE,
    ASTRALIUM_GUIDE,
    UPDATE,
    GOVERNANCE,
    ARCHITECTURE,
    RELEASE_NOTES,
)


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
        self.assertIn("Metaphysics-Lab-v1.7.1-User-Package.zip", head)
        self.assertIn("解壓縮", head)
        self.assertIn("不要下載 GitHub 自動產生的 Source code", head)
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
        self.assertIn("上傳 `metaphysics_core.md`", self.install)
        self.assertIn("`project_instructions.txt`", self.install)
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

    def test_portable_onboarding_is_birth_data_first_not_astralium_first(self):
        readme = self.readme
        project_instructions = PROJECT_INSTRUCTIONS.read_text(encoding="utf-8")
        for text in (readme, project_instructions):
            self.assertIn("出生資料", text)
            self.assertIn("offline registry", text)
            self.assertIn("不需要網路", text)
            self.assertIn("不需要額外 Python 套件", text)
            self.assertIn("Astralium", text)
            self.assertIn("可選", text)
        for forbidden in (
            "AI 應先請你開啟 Astralium",
            "先請使用者開啟 Astralium",
            "過渡期首次建立流程",
            "Portable Offline Natal Pipeline 完成前",
        ):
            self.assertNotIn(forbidden, readme)
            self.assertNotIn(forbidden, project_instructions)

    def test_public_examples_are_fictional_and_do_not_use_private_kai_name(self):
        for path in PUBLIC_GUIDES:
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
        self.assertIn("project_instructions.txt", self.update)
        self.assertIn("metaphysics_core.md", self.update)
        self.assertIn("schema migration", self.update)
        self.assertIn("runtime_info", self.update)
        self.assertNotIn("ziwei.flowing_stars` 仍 planned", self.update)
        self.assertNotIn("ziwei.flowing_stars       planned", self.update)

    def test_changelog_has_plain_language_v1_4_0_summary_before_technical_history(self):
        head = self.changelog[:10000]
        self.assertIn("## v1.4.0｜2026-08-26", head)
        self.assertIn("一般使用者摘要", head)
        self.assertIn("Astralium", head)
        self.assertIn("metaphysics_lab.py", RELEASE_NOTES.read_text(encoding="utf-8"))
        self.assertIn("GitHub Release", self.changelog)
        self.assertIn("## v1.3.0｜2026-08-23", self.changelog)

    def test_repo_has_canonical_plain_language_v1_4_0_release_note_source(self):
        self.assertTrue(RELEASE_NOTES.exists())
        text = RELEASE_NOTES.read_text(encoding="utf-8")
        self.assertIn("Metaphysics Lab v1.4.0", text)
        self.assertIn("下載區", text)
        for name in V140_USER_ARTIFACTS:
            self.assertIn(name, text)
        self.assertNotIn("project_instructions.txt", text)
        for label in USER_LABELS:
            self.assertIn(label, text)
        self.assertIn("Birth Data first", text)
        self.assertIn("Astralium", text)
        self.assertIn("可選", text)
        self.assertTrue(HISTORICAL_V130_RELEASE_NOTES.exists())

    def test_guided_inquiry_contract_lives_in_distribution_source_docs(self):
        combined = (
            CORE_WORKFLOW.read_text(encoding="utf-8")
            + "\n"
            + PROJECT_INSTRUCTIONS_SOURCE.read_text(encoding="utf-8")
        )
        for phrase in (
            "主動顯示",
            "3～4 個",
            "預設 3 個",
            "不足 3 個合法建議就不顯示",
            "不得提高 specificity",
            "使用者可以直接自由輸入、不必選建議",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, combined)


if __name__ == "__main__":
    unittest.main()
