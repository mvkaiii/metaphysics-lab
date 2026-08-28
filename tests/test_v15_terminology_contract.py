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

    def test_current_user_docs_prefer_user_package_and_current_terms(self):
        for relative in ("README.md", "docs/快速開始.md", "docs/安裝到ChatGPT-Project.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("Metaphysics-Lab-v1.5.0-User-Package.zip", text, relative)
            self.assertIn("project_instructions.txt", text, relative)
        for relative in ("README.md", "docs/快速開始.md", "docs/安裝到ChatGPT-Project.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("Historical Blind Calibration", text, relative)

    def test_version_and_changelog_distinguish_release_candidate_from_history(self):
        version = (ROOT / "VERSION.md").read_text(encoding="utf-8")
        self.assertIn("v1.5.0 Release Candidate", version)
        self.assertIn("林氏天機預測驗證", version)
        self.assertIn("發行面驗證", version)
        self.assertIn("隔離沙盒對話驗證", version)
        self.assertNotIn("deterministic cat-eye", version)
        self.assertNotIn("black-box distribution gate", version)

        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        current = changelog.split("## v1.4.0｜", 1)[0]
        self.assertIn("v1.5.0｜Release Candidate", current)
        self.assertNotIn("## Unreleased｜林氏天機", current)
        self.assertIn("林氏天機預測驗證", current)
        self.assertIn("發行面驗證", current)

    def test_update_and_architecture_docs_have_current_status_without_rewriting_v14_history(self):
        update = (ROOT / "docs/更新與版本同步.md").read_text(encoding="utf-8")
        self.assertIn("v1.4.0 → v1.5.0", update)
        self.assertIn("Metaphysics-Lab-v1.5.0-User-Package.zip", update)
        self.assertIn("project_instructions.txt", update)
        historical = update.split("## 三、v1.3.0 → v1.4.0", 1)[1].split("## 四、", 1)[0]
        self.assertIn("project_instructions.md", historical)

        architecture = (ROOT / "docs/架構說明.md").read_text(encoding="utf-8")
        self.assertIn("v1.4.0", architecture[:600])
        self.assertIn("v1.5.0 Release Candidate", architecture[:1000])
        self.assertNotIn("目前正式版本為 **v1.3.0", architecture[:600])


if __name__ == "__main__":
    unittest.main()
