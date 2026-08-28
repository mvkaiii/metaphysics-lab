import hashlib
import importlib.util
import io
import unittest
import zipfile
from pathlib import Path

from tools import build_ai_distribution


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_ASSETS = (
    "metaphysics_core.md",
    "metaphysics_lab.py",
    "project_instructions.txt",
)
EXPECTED_ZIP_MEMBERS = sorted(EXPECTED_ASSETS)


class V15ReleaseContractTests(unittest.TestCase):
    def test_distribution_surface_is_exactly_three_copy_ready_assets(self):
        self.assertEqual(build_ai_distribution.ARTIFACT_NAMES, EXPECTED_ASSETS)
        rendered = build_ai_distribution.render_distribution(ROOT)
        self.assertEqual(tuple(rendered), EXPECTED_ASSETS)
        instructions = rendered["project_instructions.txt"].decode("utf-8")
        self.assertIn("Project Instructions", instructions)
        self.assertNotIn("project_instructions.md", EXPECTED_ASSETS)

    def test_distribution_directory_has_no_old_project_instructions_md(self):
        dist = ROOT / "dist" / "ai"
        self.assertTrue((dist / "project_instructions.txt").is_file())
        self.assertFalse((dist / "project_instructions.md").exists())

    def test_claim_contract_is_falsifiable_and_bounded(self):
        contract = ROOT / "core" / "林氏天機預測驗證契約.md"
        self.assertTrue(contract.is_file(), "v1.5 claim contract source is missing")
        text = contract.read_text(encoding="utf-8")
        for required in (
            "claim_id",
            "priority",
            "domain",
            "event_family",
            "forecast_window",
            "matched_if",
            "partial_if",
            "not_matched_if",
            "confidence",
            "contamination_state",
            "domain_result",
            "event_family_result",
            "timing_result",
            "Primary Claims",
            "Secondary Claims",
        ):
            self.assertIn(required, text)
        self.assertIn("最多 3", text)
        self.assertIn("最多 2", text)
        self.assertIn("不得", text)
        self.assertIn("擴張", text)
        self.assertIn("matched_if", text)

    def test_tracking_templates_carry_claim_and_contamination_contract(self):
        question = (ROOT / "templates" / "問事追蹤紀錄_TEMPLATE.md").read_text(encoding="utf-8")
        annual = (ROOT / "templates" / "流年追蹤紀錄_TEMPLATE.md").read_text(encoding="utf-8")
        for required in (
            "claim_id",
            "priority",
            "event_family",
            "forecast_window",
            "matched_if",
            "partial_if",
            "not_matched_if",
            "domain_result",
            "event_family_result",
            "timing_result",
            "failure_mode",
        ):
            self.assertIn(required, question)
        for required in (
            "contamination_state",
            "clean_prospective",
            "partially_known",
            "known_before_lock",
        ):
            self.assertIn(required, annual)

    def test_release_package_builder_exists_and_is_deterministic_three_file_zip(self):
        module_path = ROOT / "tools" / "build_release_package.py"
        self.assertTrue(module_path.is_file(), "release package builder is missing")
        spec = importlib.util.spec_from_file_location("build_release_package_test", module_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        first = module.render_user_package(ROOT / "dist" / "ai")
        second = module.render_user_package(ROOT / "dist" / "ai")
        self.assertEqual(first, second)
        self.assertEqual(hashlib.sha256(first).hexdigest(), hashlib.sha256(second).hexdigest())
        with zipfile.ZipFile(io.BytesIO(first), "r") as archive:
            self.assertEqual(sorted(archive.namelist()), EXPECTED_ZIP_MEMBERS)
            self.assertTrue(all("/" not in name for name in archive.namelist()))
            for name in EXPECTED_ZIP_MEMBERS:
                self.assertEqual(archive.read(name), (ROOT / "dist" / "ai" / name).read_bytes())
        verified = module.verify_user_package(first, ROOT / "dist" / "ai")
        self.assertTrue(verified["integrity_verified"])
        self.assertEqual(sorted(verified["members"]), EXPECTED_ZIP_MEMBERS)

    def test_release_package_rejects_extra_or_missing_distribution_asset(self):
        module_path = ROOT / "tools" / "build_release_package.py"
        self.assertTrue(module_path.is_file(), "release package builder is missing")
        spec = importlib.util.spec_from_file_location("build_release_package_validation_test", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for name in EXPECTED_ASSETS:
                (root / name).write_bytes(b"x")
            (root / "extra.txt").write_text("no", encoding="utf-8")
            with self.assertRaises(ValueError):
                module.render_user_package(root)
            (root / "extra.txt").unlink()
            (root / "metaphysics_core.md").unlink()
            with self.assertRaises(ValueError):
                module.render_user_package(root)

    def test_release_workflow_publishes_only_after_v15_gates(self):
        workflow = ROOT / ".github" / "workflows" / "release-v1.5.yml"
        self.assertTrue(workflow.is_file(), "v1.5 release workflow is missing")
        text = workflow.read_text(encoding="utf-8")
        self.assertIn("contents: write", text)
        self.assertIn("v1.5.0", text)
        self.assertIn("run_lin_tianji_cat_eye.py", text)
        self.assertIn("build_release_package.py", text)
        self.assertIn("project_instructions.txt", text)
        self.assertIn("Metaphysics-Lab-v1.5.0-User-Package.zip", text)
        self.assertIn("gh release create", text)


if __name__ == "__main__":
    unittest.main()
