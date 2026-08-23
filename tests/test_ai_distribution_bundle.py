import json
import subprocess
import sys
import unittest
from pathlib import Path

from engine.distribution.runtime import dispatch


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "dist" / "ai" / "metaphysics_lab.py"

BIRTH = {
    "sex": "male",
    "birth_date": "1984-03-13",
    "birth_time": "19:20",
    "birth_place": "台北市",
}

LOCATION = {
    "canonical_name": "Taipei City, Taiwan",
    "latitude": 25.033,
    "longitude": 121.5654,
    "timezone": "Asia/Taipei",
    "provider_name": "ai_host",
    "provider_version": "user-confirmed",
    "provider_reference": None,
}


class AIDistributionBundleTests(unittest.TestCase):
    @staticmethod
    def bundled_request(action, payload=None, python_flags=()):
        request = json.dumps(
            {"action": action, "payload": {} if payload is None else payload},
            ensure_ascii=False,
        )
        completed = subprocess.run(
            [sys.executable, *python_flags, str(BUNDLE), "request", "--input", "-"],
            cwd=str(ROOT),
            input=request,
            text=True,
            capture_output=True,
        )
        if completed.returncode != 0:
            raise AssertionError(completed.stdout + completed.stderr)
        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise AssertionError(completed.stdout + completed.stderr) from exc
        return completed, result

    @classmethod
    def setUpClass(cls):
        if not BUNDLE.exists():
            raise AssertionError("generated bundle is missing: %s" % BUNDLE)
        built = dispatch(
            "build_natal",
            {"birth": BIRTH, "resolved_location": LOCATION},
        )
        if not built.get("ok"):
            raise AssertionError(built)
        cls.normalized = built["data"]["normalized_natal"]

    def test_runtime_info_matches_modular_runtime(self):
        modular = dispatch("runtime_info", {})
        completed = subprocess.run(
            [sys.executable, str(BUNDLE), "runtime-info"],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        bundled = json.loads(completed.stdout)
        self.assertEqual(bundled, modular)

    def test_natal_request_matches_modular_runtime(self):
        payload = {"birth": BIRTH, "resolved_location": LOCATION}
        modular = dispatch("build_natal", payload)
        _, bundled = self.bundled_request("build_natal", payload)
        self.assertEqual(bundled, modular)

    def test_forecast_request_matches_modular_runtime(self):
        payload = {
            "normalized_natal": self.normalized,
            "target": {
                "civil_datetime": "2026-09-15T23:30:00",
                "timezone": "Asia/Taipei",
            },
            "requested_scopes": ["monthly", "daily"],
        }
        modular = dispatch("resolve_forecast_context", payload)
        _, bundled = self.bundled_request("resolve_forecast_context", payload)
        self.assertEqual(bundled, modular)

    def test_case_export_matches_modular_runtime(self):
        payload = {
            "normalized_natal": self.normalized,
            "subject_id": "case-bundle-parity-a1b2c3",
            "generated_at": "2026-08-23T00:00:00+08:00",
            "last_modified_by": "ai",
        }
        modular = dispatch("export_case_markdown", payload)
        _, bundled = self.bundled_request("export_case_markdown", payload)
        self.assertEqual(bundled, modular)
        self.assertEqual(len(bundled["data"]["files"]), 5)
        self.assertEqual(
            list(bundled["data"]["files"]),
            [
                "00_專案索引.md",
                "01_命盤核心摘要.md",
                "02_命盤資料校驗紀錄.md",
                "03_八字結構化資料包.md",
                "04_紫微基礎資料包.md",
            ],
        )

    def test_historical_selector_request_matches_modular_runtime(self):
        payload = {
            "normalized_natal": self.normalized,
            "as_of_datetime": "2026-08-23T10:27:00+08:00",
            "timezone": "Asia/Taipei",
        }
        modular = dispatch("prepare_historical_calibration", payload)
        _, bundled = self.bundled_request("prepare_historical_calibration", payload)
        self.assertEqual(bundled, modular)
        self.assertTrue(bundled["ok"], bundled)
        self.assertEqual(len(bundled["data"]["high_years"]), 4)
        self.assertIn("control_year", bundled["data"])
        support = bundled["data"]["ziwei_support"]
        self.assertEqual(support["status"], "available")
        self.assertEqual(support["role"], "support_only")
        self.assertFalse(support["ranking_authority"])
        self.assertEqual(len(support["years"]), 5)

    def test_request_cli_reads_json_stdin_and_returns_one_json_object(self):
        completed, result = self.bundled_request("runtime_info", {})
        self.assertEqual(completed.returncode, 0)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["action"], "runtime_info")
        self.assertEqual(len([line for line in completed.stdout.splitlines() if line.strip()]), 1)

    def test_unknown_action_is_structured_and_non_crashing(self):
        completed, result = self.bundled_request("not_a_real_action", {})
        self.assertEqual(completed.returncode, 0)
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "unsupported_action")

    def test_runtime_info_survives_without_site_packages(self):
        completed = subprocess.run(
            [sys.executable, "-S", str(BUNDLE), "runtime-info"],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        result = json.loads(completed.stdout)
        self.assertTrue(result["ok"], result)
        deps = result["data"]["external_dependencies"]
        self.assertFalse(deps["geopy"]["installed"])
        self.assertFalse(deps["timezonefinder"]["installed"])

    def test_missing_core_dependency_returns_machine_readable_error(self):
        payload = {"birth": BIRTH, "resolved_location": LOCATION}
        completed, result = self.bundled_request(
            "build_natal",
            payload,
            python_flags=("-S",),
        )
        self.assertEqual(completed.returncode, 0)
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "dependency_unavailable")
        self.assertTrue(result["error"]["details"]["missing_module"])
        self.assertNotIn("Traceback", completed.stderr)


if __name__ == "__main__":
    unittest.main()
