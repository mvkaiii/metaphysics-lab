import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

from engine.distribution.constants import RELEASE_VERSION


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "tools" / "run_v17_release_surface_validation.py"
EXPECTED_CHECKS = (
    "capability_manifest_v1",
    "case_doctor_contract",
    "case_reconciliation_dry_run",
    "prospective_v1_frozen_identity",
    "prospective_validation_v2",
    "guided_inquiry_contract",
    "project_instructions_size",
    "case_schema_1_1",
    "selector_v1_default",
    "interpretation_v1_default",
    "deterministic_user_package",
    "python39_compile",
    "distribution_parity",
)


class V17ReleaseSurfaceValidationTests(unittest.TestCase):
    @staticmethod
    def _load_validator():
        if not VALIDATOR.is_file():
            raise AssertionError("v1.7 release-surface validator is missing")
        spec = importlib.util.spec_from_file_location("run_v17_release_surface_validation_test", VALIDATOR)
        if spec is None or spec.loader is None:
            raise AssertionError("v1.7 release-surface validator cannot be imported")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_validator_reports_required_named_checks_and_passes(self):
        module = self._load_validator()
        report = module.run(ROOT / "dist" / "ai")
        self.assertEqual(report["release_version"], RELEASE_VERSION)
        self.assertEqual(tuple(row["check"] for row in report["checks"]), EXPECTED_CHECKS)
        for row in report["checks"]:
            self.assertIn(row["status"], {"PASS", "FAIL"})
        self.assertEqual(report["status"], "PASS", report)

    def test_json_cli_is_deterministic(self):
        first = subprocess.run(
            [sys.executable, str(VALIDATOR), "--json"],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
        )
        second = subprocess.run(
            [sys.executable, str(VALIDATOR), "--json"],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
        )
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertEqual(first.stdout, second.stdout)
        report = json.loads(first.stdout)
        self.assertEqual(tuple(row["check"] for row in report["checks"]), EXPECTED_CHECKS)
        self.assertEqual(report["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
