import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class V15TerminologyContractTests(unittest.TestCase):
    def test_active_release_paths_use_current_validation_names(self):
        expected = (
            ".github/workflows/lin-tianji-v1.5-validation.yml",
            "tools/run_lin_tianji_prediction_validation.py",
            "tools/run_v15_release_surface_validation.py",
            "tests/fixtures/lin_tianji_prediction_validation.v1.json",
            "tests/test_lin_tianji_prediction_validation.py",
            "tests/test_lin_tianji_prediction_validation_progressive.py",
            "tests/test_v15_release_surface_validation.py",
        )
        removed = (
            ".github/workflows/feature-historical-calibration-validation.yml",
            "tools/run_lin_tianji_cat_eye.py",
            "tools/run_v15_sandbox_black_box.py",
            "tests/fixtures/lin_tianji_cat_eye.v1.json",
            "tests/test_lin_tianji_cat_eye.py",
            "tests/test_lin_tianji_cat_eye_progressive.py",
            "tests/test_v15_sandbox_black_box.py",
        )
        for relative in expected:
            self.assertTrue((ROOT / relative).is_file(), relative)
        for relative in removed:
            self.assertFalse((ROOT / relative).exists(), relative)

    def test_active_release_surface_has_no_retired_labels(self):
        active_files = (
            "README.md",
            "VERSION.md",
            "docs/發布說明-v1.5.0.md",
            "docs/release/v1.5.0-qualification.md",
            ".github/workflows/release-v1.5.yml",
            ".github/workflows/lin-tianji-v1.5-validation.yml",
            "tools/run_lin_tianji_prediction_validation.py",
            "tools/run_v15_release_surface_validation.py",
            "tests/test_v15_release_contract.py",
            "tests/test_v15_release_surface_validation.py",
            "docs/superpowers/plans/2026-08-26-林氏天機-v1.5-Implementation-Plan.md",
            "docs/superpowers/specs/2026-08-28-林氏天機-v1.5-Phase5-Interpretation-Contract-設計.md",
        )
        retired = (
            "cat-eye",
            "cat_eye",
            "CatEye",
            "貓眼",
            "sandbox_black_box",
            "sandbox black-box",
            "three-asset black-box",
            "Feature Historical Calibration Validation",
            "phase6-rebuilt-ai-distribution",
            "progressive-case-ai-distribution",
        )
        for relative in active_files:
            text = (ROOT / relative).read_text(encoding="utf-8")
            for token in retired:
                self.assertNotIn(token, text, "%s still contains %r" % (relative, token))

    def test_release_surface_validator_does_not_reuse_sandbox_black_box_symbols(self):
        for relative in (
            "tools/run_v15_release_surface_validation.py",
            "tests/test_v15_release_surface_validation.py",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("black_box", text, relative)
            self.assertNotIn("black-box", text, relative)
        runner = (ROOT / "tools" / "run_v15_release_surface_validation.py").read_text(encoding="utf-8")
        test = (ROOT / "tests" / "test_v15_release_surface_validation.py").read_text(encoding="utf-8")
        self.assertNotIn('"rubric"', runner)
        self.assertIn('"checks"', runner)
        self.assertIn('report["checks"]', test)
        self.assertIn("test_all_release_surface_checks_pass", test)

    def test_current_user_docs_prefer_user_package_and_current_terms(self):
        for relative in ("README.md", "docs/快速開始.md", "docs/安裝到ChatGPT-Project.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("Metaphysics-Lab-v1.5.0-User-Package.zip", text, relative)
            self.assertIn("project_instructions.txt", text, relative)
        for relative in ("README.md", "docs/快速開始.md", "docs/安裝到ChatGPT-Project.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("Historical Blind Calibration", text, relative)

    def test_active_current_state_docs_reflect_published_v15(self):
        active_files = (
            "README.md",
            "VERSION.md",
            "CHANGELOG.md",
            "docs/快速開始.md",
            "docs/安裝到ChatGPT-Project.md",
            "docs/更新與版本同步.md",
            "docs/架構說明.md",
            "docs/release/v1.5.0-qualification.md",
            "docs/release/v1.5.0-terminology-audit.md",
        )
        forbidden = (
            "v1.5.0 Release Candidate",
            "PENDING_FINAL_QUALIFICATION",
            "PENDING_FINAL_EVIDENCE",
            "ACTIVE_TERMINOLOGY_CLEAN_PENDING_FULL_CI",
            "v1.5.0 正式發布後",
        )
        for relative in active_files:
            text = (ROOT / relative).read_text(encoding="utf-8")
            for token in forbidden:
                self.assertNotIn(token, text, "%s still contains %r" % (relative, token))

    def test_version_and_changelog_reflect_published_v15_without_rewriting_history(self):
        version = (ROOT / "VERSION.md").read_text(encoding="utf-8")
        formal = version.split("## 歷史版本", 1)[0]
        self.assertIn("Metaphysics Lab Core：**v1.5.0**", formal)
        self.assertIn("發布日期：**2026-08-29**", formal)
        self.assertIn("正式 release commit：`66f604222caadac0209125a78674c3f4491c4b99`", formal)
        self.assertIn("林氏天機預測驗證", formal)
        self.assertIn("發行面驗證", formal)
        self.assertIn("隔離沙盒對話驗證", formal)
        self.assertNotIn("PENDING_FINAL_QUALIFICATION", formal)

        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        current = changelog.split("## v1.4.0｜", 1)[0]
        self.assertIn("## v1.5.0｜2026-08-29", current)
        self.assertNotIn("v1.5.0｜Release Candidate", current)
        self.assertIn("林氏天機預測驗證", current)
        self.assertIn("發行面驗證", current)

    def test_update_and_architecture_docs_have_published_status_without_rewriting_v14_history(self):
        update = (ROOT / "docs/更新與版本同步.md").read_text(encoding="utf-8")
        self.assertIn("目前正式版本為 **v1.5.0｜2026-08-29**", update)
        self.assertIn("v1.4.0 → v1.5.0", update)
        self.assertIn("Metaphysics-Lab-v1.5.0-User-Package.zip", update)
        self.assertIn("project_instructions.txt", update)
        historical = update.split("## 三、v1.3.0 → v1.4.0", 1)[1].split("## 四、", 1)[0]
        self.assertIn("project_instructions.md", historical)

        architecture = (ROOT / "docs/架構說明.md").read_text(encoding="utf-8")
        self.assertIn("目前正式版本為 **v1.5.0｜2026-08-29**", architecture[:800])
        self.assertNotIn("v1.5.0 Release Candidate", architecture[:1000])
        self.assertNotIn("目前正式版本為 **v1.4.0", architecture[:800])


if __name__ == "__main__":
    unittest.main()
