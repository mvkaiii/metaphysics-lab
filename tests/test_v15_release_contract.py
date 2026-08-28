import hashlib
import importlib.util
import io
import json
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
SANDBOX_SCRIPT = ROOT / "docs" / "release" / "v1.5.0-isolated-sandbox-script.md"
SANDBOX_FIXTURE = ROOT / "tests" / "fixtures" / "v1.5.0-isolated-sandbox-fixture.v1.json"
SANDBOX_EVIDENCE = ROOT / "docs" / "release" / "v1.5.0-isolated-sandbox-conversation-validation.md"
SANDBOX_VALIDATOR = ROOT / "tools" / "validate_v15_sandbox_evidence.py"
SANDBOX_RUBRICS = (
    "temporal_ownership_pass",
    "specificity_pass",
    "calibration_narrowing_pass",
    "cutoff_contamination_pass",
    "experimental_ceiling_pass",
    "natural_language_pass",
    "algorithm_disclosure_pass",
    "strategy_forecast_separation_pass",
)


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

    def test_isolated_sandbox_test_kit_is_versioned_fixed_and_private_free(self):
        self.assertTrue(SANDBOX_SCRIPT.is_file(), "fixed C.2 prompt script is missing")
        self.assertTrue(SANDBOX_FIXTURE.is_file(), "synthetic C.2 fixture is missing")
        script = SANDBOX_SCRIPT.read_text(encoding="utf-8")
        fixture_text = SANDBOX_FIXTURE.read_text(encoding="utf-8")
        fixture = json.loads(fixture_text)

        self.assertEqual(fixture["fixture_version"], "v1.5.0-isolated-sandbox-fixture.v1")
        self.assertEqual(fixture["classification"], "synthetic_test_case")
        self.assertEqual(fixture["subject"]["display_name"], "Mina")
        self.assertEqual(fixture["target_year"], 2027)
        self.assertEqual(len(fixture["historical_event_ledger"]), 10)
        self.assertEqual([row["year"] for row in fixture["historical_event_ledger"]], list(range(2016, 2026)))

        for required in (
            "script_version: v1.5.0-isolated-sandbox-script.v1",
            "年度總覽",
            "月份拆解",
            "某日",
            "某時",
            "已知現實背景",
            "Historical Calibration",
            "精確權重",
            "一定會發生",
        ) + SANDBOX_RUBRICS:
            self.assertIn(required, script)

        combined = script + "\n" + fixture_text
        self.assertNotIn("Kai", combined)
        self.assertNotIn("1984-03-13", combined)
        self.assertIn("fictional", combined.lower())

    def test_isolated_sandbox_evidence_template_is_fail_closed_until_real_run(self):
        self.assertTrue(SANDBOX_EVIDENCE.is_file())
        text = SANDBOX_EVIDENCE.read_text(encoding="utf-8")
        self.assertIn("schema_version: v1.5.0-isolated-sandbox-evidence.v1", text)
        self.assertIn("status: PENDING", text)
        self.assertNotIn("status: PASS", text)
        for key in (
            "tested_release_candidate_sha",
            "tested_distribution_digest",
            "tested_user_package_sha256",
            "script_sha256",
            "fixture_sha256",
            "sandbox_run_id",
            "sandbox_environment",
            "executed_at",
        ):
            self.assertIn(f"{key}: PENDING", text)
        for rubric in SANDBOX_RUBRICS:
            self.assertIn(f"- {rubric}: PENDING", text)

    def test_sandbox_evidence_validator_rejects_pending_template(self):
        self.assertTrue(SANDBOX_VALIDATOR.is_file(), "sandbox evidence validator is missing")
        spec = importlib.util.spec_from_file_location("validate_v15_sandbox_evidence_test", SANDBOX_VALIDATOR)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        report = module.validate_evidence(
            root=ROOT,
            evidence_path=SANDBOX_EVIDENCE,
            current_sha="f" * 40,
        )
        self.assertEqual(report["status"], "PENDING", report)
        self.assertFalse(report["release_allowed"], report)
        self.assertIn("evidence_status_not_pass", report["errors"])

    def test_release_workflow_uses_structured_sandbox_evidence_validator(self):
        workflow = ROOT / ".github" / "workflows" / "release-v1.5.yml"
        self.assertTrue(workflow.is_file(), "v1.5 release workflow is missing")
        text = workflow.read_text(encoding="utf-8")
        self.assertIn("contents: write", text)
        self.assertIn("v1.5.0", text)
        self.assertIn("run_lin_tianji_prediction_validation.py", text)
        self.assertIn("build_release_package.py", text)
        self.assertIn("project_instructions.txt", text)
        self.assertIn("Metaphysics-Lab-v1.5.0-User-Package.zip", text)
        self.assertIn("validate_v15_sandbox_evidence.py", text)
        self.assertIn("--current-sha \"$GITHUB_SHA\"", text)
        self.assertNotIn("grep -q 'status: PASS'", text)
        self.assertIn("gh release create", text)


if __name__ == "__main__":
    unittest.main()
