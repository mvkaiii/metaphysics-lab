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

    def test_current_user_docs_keep_three_file_surface_and_current_terms(self):
        for relative in ("README.md", "docs/快速開始.md", "docs/安裝到ChatGPT-Project.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("project_instructions.txt", text, relative)
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

    def test_v15_release_history_remains_preserved_after_newer_releases(self):
        version = (ROOT / "VERSION.md").read_text(encoding="utf-8")
        self.assertIn("## v1.5.0 Capability Snapshot", version)
        self.assertIn("### v1.5.0｜2026-08-29", version)
        self.assertIn("66f604222caadac0209125a78674c3f4491c4b99", version)

        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        v15 = changelog.split("## v1.5.0｜2026-08-29", 1)[1].split("## v1.4.0｜", 1)[0]
        self.assertNotIn("v1.5.0｜Release Candidate", v15)
        self.assertIn("林氏天機預測驗證", v15)
        self.assertIn("發行面驗證", v15)
        self.assertIn("66f604222caadac0209125a78674c3f4491c4b99", v15)

    def test_v15_upgrade_history_remains_without_rewriting_v14_history(self):
        update = (ROOT / "docs/更新與版本同步.md").read_text(encoding="utf-8")
        self.assertIn("v1.4.0 → v1.5.0", update)
        v15_upgrade = update.split("## 四、v1.4.0 → v1.5.0", 1)[1].split("## 五、", 1)[0]
        self.assertIn("Metaphysics-Lab-v1.5.0-User-Package.zip", v15_upgrade)
        self.assertIn("project_instructions.txt", v15_upgrade)
        historical = update.split("## 三、v1.3.0 → v1.4.0", 1)[1].split("## 四、", 1)[0]
        self.assertIn("project_instructions.md", historical)

        architecture = (ROOT / "docs/架構說明.md").read_text(encoding="utf-8")
        self.assertNotIn("v1.5.0 Release Candidate", architecture[:1200])
        self.assertNotIn("目前正式版本為 **v1.4.0", architecture[:800])


if __name__ == "__main__":
    unittest.main()
