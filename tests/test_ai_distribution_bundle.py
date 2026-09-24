import base64
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest import mock

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
IDENTITY = {
    "subject_id": "subj_7f3a2c91d4e8",
    "subject_display_name": "Kai",
    "subject_short_id": "7F3A2C",
    "filename_label": "Kai",
}


class AIDistributionBundleTests(unittest.TestCase):
    @staticmethod
    def bundled_request(action, payload=None, python_flags=()):
        request = json.dumps({"action": action, "payload": {} if payload is None else payload}, ensure_ascii=False)
        completed = subprocess.run(
            [sys.executable, *python_flags, str(BUNDLE), "request", "--input", "-"],
            cwd=str(ROOT), input=request, text=True, capture_output=True,
        )
        if completed.returncode != 0:
            raise AssertionError(completed.stdout + completed.stderr)
        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise AssertionError(completed.stdout + completed.stderr) from exc
        return completed, result

    @staticmethod
    def _load_fresh_generated_bundle():
        from tools import build_ai_distribution as builder

        temp_dir = tempfile.TemporaryDirectory()
        output = Path(temp_dir.name)
        builder.build_distribution(ROOT, output)
        path = output / "metaphysics_lab.py"
        spec = importlib.util.spec_from_file_location("metaphysics_lab_test_bundle", path)
        if spec is None or spec.loader is None:
            temp_dir.cleanup()
            raise AssertionError("generated bundle could not be imported")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return temp_dir, module

    @staticmethod
    def _set_embedded_records(module, records):
        payload = {"build_format_version": "1.1", "files": records}
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        module._PAYLOAD_B64 = base64.b64encode(zlib.compress(raw, level=9)).decode("ascii")
        module.SOURCE_DIGEST = hashlib.sha256(raw).hexdigest()
        module._SOURCE_FILES = {record["path"]: record["sha256"] for record in records}
        module._RUNTIME_ROOT = None

    @classmethod
    def setUpClass(cls):
        if not BUNDLE.exists():
            raise AssertionError("generated bundle is missing: %s" % BUNDLE)
        built = dispatch("build_natal", {"birth": BIRTH, "resolved_location": LOCATION})
        if not built.get("ok"):
            raise AssertionError(built)
        cls.normalized = built["data"]["normalized_natal"]

    def test_runtime_info_matches_modular_runtime(self):
        modular = dispatch("runtime_info", {})
        completed = subprocess.run([sys.executable, str(BUNDLE), "runtime-info"], cwd=str(ROOT), text=True, capture_output=True)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        bundled = json.loads(completed.stdout)
        self.assertEqual(bundled, modular)
        self.assertEqual(
            bundled["data"]["bundled_dependencies"],
            modular["data"]["bundled_dependencies"],
        )
        self.assertEqual(
            bundled["data"]["offline_location_registry"],
            modular["data"]["offline_location_registry"],
        )
        self.assertTrue(bundled["data"]["bundled_dependencies"]["lunar-python"]["available"])
        self.assertTrue(bundled["data"]["bundled_dependencies"]["tzdata"]["available"])

    def test_guided_inquiry_request_matches_modular_runtime(self):
        payload = {
            "mode": "entry",
            "case_health": "PASS",
            "user_opted_out": False,
            "blocking_state": "none",
            "case_integrity_action_available": False,
            "pending_forecast_available": False,
            "current_answer": None,
        }
        modular = dispatch("suggest_inquiries", payload)
        self.assertTrue(modular["ok"], modular)
        _, bundled = self.bundled_request("suggest_inquiries", payload)
        self.assertEqual(bundled, modular)

    def test_natal_request_matches_modular_runtime(self):
        payload = {"birth": BIRTH, "resolved_location": LOCATION}
        modular = dispatch("build_natal", payload)
        _, bundled = self.bundled_request("build_natal", payload)
        self.assertEqual(bundled, modular)

    def test_birth_only_taipei_matches_modular_runtime_under_python_s(self):
        payload = {"birth": BIRTH}
        modular = dispatch("build_natal", payload)
        completed, bundled = self.bundled_request("build_natal", payload, python_flags=("-S",))
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(bundled, modular)
        self.assertTrue(bundled["ok"], bundled)
        self.assertEqual(
            bundled["data"]["resolved_location"]["provider_name"],
            "metaphysics_lab_offline_registry",
        )
        self.assertEqual(bundled["data"]["resolved_location"]["timezone"], "Asia/Taipei")
        self.assertEqual(len(bundled["data"]["project_natal"]["ziwei"]["palaces"]), 12)

    def test_candidate_envelope_request_matches_modular_runtime_for_bounded_range(self):
        payload = {
            "birth": {
                "sex": "male",
                "birth_date": "1984-03-13",
                "birth_time_range": ["18:58", "19:02"],
                "birth_place": "台北市",
            },
            "resolved_location": LOCATION,
        }
        modular = dispatch("natal.candidate_envelope", payload)
        _, bundled = self.bundled_request("natal.candidate_envelope", payload)
        self.assertEqual(bundled, modular)
        self.assertTrue(bundled["ok"], bundled)
        self.assertFalse(bundled["data"]["candidate_envelope"]["provenance"]["midpoint_used"])

    def test_forecast_request_matches_modular_runtime(self):
        payload = {
            "normalized_natal": self.normalized,
            "target": {"civil_datetime": "2026-09-15T23:30:00", "timezone": "Asia/Taipei"},
            "requested_scopes": ["monthly", "daily"],
        }
        modular = dispatch("resolve_forecast_context", payload)
        _, bundled = self.bundled_request("resolve_forecast_context", payload)
        self.assertEqual(bundled, modular)

    def test_query_anchor_request_matches_modular_runtime(self):
        payload = {
            "query_anchor_at": "2026-08-26T17:00:00+08:00",
            "query_timezone": "Asia/Taipei",
            "target_start": "2026-08-01T00:00:00+08:00",
            "target_end": "2026-12-31T23:59:59+08:00",
            "question_reference": "bundle-prospective-anchor",
        }
        modular = dispatch("resolve_query_anchor", payload)
        self.assertTrue(modular["ok"], modular)
        _, bundled = self.bundled_request("resolve_query_anchor", payload)
        self.assertEqual(bundled, modular)

    def test_prospective_forecast_lock_matches_modular_runtime(self):
        anchor_payload = {
            "query_anchor_at": "2026-08-26T17:00:00+08:00",
            "query_timezone": "Asia/Taipei",
            "target_start": "2026-08-01T00:00:00+08:00",
            "target_end": "2026-12-31T23:59:59+08:00",
            "question_reference": "bundle-prospective-lock",
        }
        anchor = dispatch("resolve_query_anchor", anchor_payload)["data"]
        claim = {
            "claim_id": "claim-2026-09-work-001",
            "forecast_window": {"start": "2026-09-01T00:00:00+08:00", "end": "2026-09-30T23:59:59+08:00"},
            "primary_domain": "工作",
            "event_family": "職責變動",
            "prediction": "9 月內出現可被正式記錄的工作職責調整。",
            "matched_if": "正式職稱、管理範圍或書面職責至少一項在預測窗內改變。",
            "not_matched_if": "預測窗結束時，上述三項均未發生正式改變。",
            "evidence_layers": ["bazi.yearly", "ziwei.yearly"],
            "evidence_time_scales": ["yearly"],
            "capability_maturity": "stable",
            "confidence": "medium",
            "knowledge_cutoff_at": anchor["knowledge_cutoff_at"],
            "evaluation_eligibility": "clean_scorable",
            "contamination_state": "clean_prospective",
            "method_version": "lin_tianji_v1.5-exp",
        }
        payload = {"anchor": anchor, "claims": [claim]}
        modular = dispatch("lock_prospective_forecast", payload)
        self.assertTrue(modular["ok"], modular)
        _, bundled = self.bundled_request("lock_prospective_forecast", payload)
        self.assertEqual(bundled, modular)
        self.assertEqual(len(modular["data"]["canonical_digest"]), 64)

    def test_case_export_matches_modular_runtime(self):
        payload = {
            "normalized_natal": self.normalized,
            **IDENTITY,
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
                "Kai_7F3A2C_00_專案索引.md",
                "Kai_7F3A2C_01_命盤核心摘要.md",
                "Kai_7F3A2C_02_命盤資料校驗紀錄.md",
                "Kai_7F3A2C_03_八字結構化資料包.md",
                "Kai_7F3A2C_04_紫微基礎資料包.md",
            ],
        )

    def test_subject_registry_validation_matches_modular_runtime(self):
        registry = """---\nregistry_schema_version: 1.0\n---\n# 命主索引\n\n<!-- subjects:start -->\n```json\n{\"subjects\":[{\"filename_label\":\"Kai\",\"status\":\"active\",\"subject_display_name\":\"Kai\",\"subject_id\":\"subj_7f3a2c91d4e8\",\"subject_short_id\":\"7F3A2C\"}]}\n```\n<!-- subjects:end -->\n"""
        payload = {"registry_markdown": registry}
        modular = dispatch("subject.registry_validate", payload)
        _, bundled = self.bundled_request("subject.registry_validate", payload)
        self.assertEqual(bundled, modular)

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
        completed = subprocess.run([sys.executable, "-S", str(BUNDLE), "runtime-info"], cwd=str(ROOT), text=True, capture_output=True)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        result = json.loads(completed.stdout)
        self.assertTrue(result["ok"], result)
        deps = result["data"]["external_dependencies"]
        self.assertFalse(deps["geopy"]["installed"])
        self.assertFalse(deps["timezonefinder"]["installed"])

    def test_bundled_core_dependencies_work_under_python_s(self):
        payload = {"birth": BIRTH, "resolved_location": LOCATION}
        modular = dispatch("build_natal", payload)
        completed, result = self.bundled_request("build_natal", payload, python_flags=("-S",))
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(result, modular)
        self.assertTrue(result["ok"], result)
        self.assertNotIn("Traceback", completed.stderr)

    def test_unsafe_or_corrupt_records_are_rejected_before_runtime_root_creation(self):
        safe_bytes = b"print('safe')\n"
        safe_digest = hashlib.sha256(safe_bytes).hexdigest()
        safe_content = base64.b64encode(safe_bytes).decode("ascii")
        cases = [
            [
                {"path": "/tmp/escape.py", "sha256": safe_digest, "encoding": "base64", "content": safe_content}
            ],
            [
                {"path": "../escape.py", "sha256": safe_digest, "encoding": "base64", "content": safe_content}
            ],
            [
                {"path": "engine/a.py", "sha256": safe_digest, "encoding": "base64", "content": safe_content},
                {"path": "engine/a.py", "sha256": safe_digest, "encoding": "base64", "content": safe_content},
            ],
            [
                {"path": "engine/a.py", "sha256": "0" * 64, "encoding": "base64", "content": safe_content}
            ],
        ]
        for records in cases:
            with self.subTest(records=records):
                temp_dir, module = self._load_fresh_generated_bundle()
                try:
                    self._set_embedded_records(module, records)
                    with mock.patch.object(module.tempfile, "mkdtemp", side_effect=AssertionError("must validate before writes")):
                        with self.assertRaises(RuntimeError):
                            module._ensure_runtime_root()
                finally:
                    temp_dir.cleanup()


if __name__ == "__main__":
    unittest.main()
