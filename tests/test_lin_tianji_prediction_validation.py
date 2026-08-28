import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "lin_tianji_prediction_validation.v1.json"
RUNNER = ROOT / "tools" / "run_lin_tianji_prediction_validation.py"
EXPECTED_IDS = [
    "C01-decadal-strong-yearly-weak",
    "C02-yearly-strong-monthly-weak",
    "C03-yearly-weak-monthly-strong",
    "C04-experimental-day-hour-spike",
    "C05-correlated-ziwei-derivatives",
    "C06-independent-bazi-ziwei-convergence",
    "C07-historical-repeated-support",
    "C08-historical-unsupported-domain",
    "C09-known-before-cutoff-plan",
    "C10-algorithm-weight-request",
    "C11-user-language-lexical-audit",
    "C12-progressive-case-stage1-isolation",
]


def load_runner():
    if not RUNNER.is_file():
        raise AssertionError("prediction-validation runner is missing")
    spec = importlib.util.spec_from_file_location("lin_tianji_prediction_validation_test_runner", RUNNER)
    if spec is None or spec.loader is None:
        raise AssertionError("prediction-validation runner cannot be imported")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LinTianJiPredictionValidationTests(unittest.TestCase):
    def test_fixture_contains_exact_required_scenario_classes(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(payload["fixture_version"], "lin_tianji_prediction_validation.v1")
        self.assertEqual([row["id"] for row in payload["scenarios"]], EXPECTED_IDS)
        self.assertEqual(len(payload["scenarios"]), 12)
        serialized = json.dumps(payload, ensure_ascii=False).lower()
        self.assertNotIn("kai", serialized)
        self.assertNotIn("2026-09-17", serialized)

    def test_all_scenarios_pass_with_deterministic_evidence(self):
        runner = load_runner()
        first = runner.run_scenarios(FIXTURE)
        second = runner.run_scenarios(FIXTURE)
        self.assertEqual(first, second)
        self.assertEqual([row["scenario_id"] for row in first], EXPECTED_IDS)
        self.assertTrue(all(row["status"] == "PASS" for row in first), first)
        for row in first:
            self.assertTrue(row["reason"])
            self.assertTrue(row["policy_or_method_version"])
            self.assertRegex(row["input_digest"], r"^[0-9a-f]{64}$")
            self.assertRegex(row["output_digest"], r"^[0-9a-f]{64}$")

    def test_cli_returns_nonzero_on_failure_and_json_report_on_success(self):
        completed = subprocess.run(
            [sys.executable, str(RUNNER), "--fixture", str(FIXTURE), "--json"],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["fixture_version"], "lin_tianji_prediction_validation.v1")
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["scenario_count"], 12)
        self.assertEqual(report["failed_count"], 0)
        self.assertEqual([row["scenario_id"] for row in report["results"]], EXPECTED_IDS)


if __name__ == "__main__":
    unittest.main()
