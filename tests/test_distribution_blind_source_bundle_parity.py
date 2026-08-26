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
IDENTITY = {
    "subject_id": "subj_7f3a2c91d4e8",
    "subject_display_name": "Kai",
    "subject_short_id": "7F3A2C",
    "filename_label": "Kai",
}
BASE_SLOTS = (
    "00_專案索引.md",
    "01_命盤核心摘要.md",
    "02_命盤資料校驗紀錄.md",
    "03_八字結構化資料包.md",
    "04_紫微基礎資料包.md",
)
PROGRESSIVE_SLOT = "05_驗證事件紀錄.md"


def _actual(slot):
    return "Kai_7F3A2C_" + slot


class DistributionBlindSourceBundleParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not BUNDLE.exists():
            raise AssertionError("generated bundle is missing: %s" % BUNDLE)
        built = dispatch("build_natal", {"birth": BIRTH, "resolved_location": LOCATION})
        if not built.get("ok"):
            raise AssertionError(built)
        exported = dispatch(
            "export_case_markdown",
            {
                "normalized_natal": built["data"]["normalized_natal"],
                **IDENTITY,
                "generated_at": "2026-08-26T22:10:00+08:00",
                "last_modified_by": "ai",
            },
        )
        if not exported.get("ok"):
            raise AssertionError(exported)
        files = dict(exported["data"]["files"])
        appended = dispatch(
            "update_case_record",
            {
                "case_files": files,
                "filename": PROGRESSIVE_SLOT,
                "operation": "append",
                "updated_at": "2026-08-26T22:11:00+08:00",
                "last_modified_by": "ai",
                "entry": {
                    "record_id": "evt-phase0-bundle-001",
                    "status": "verified",
                    "summary": "synthetic parity event",
                },
            },
        )
        if not appended.get("ok"):
            raise AssertionError(appended)
        files.update(appended["data"]["changed_files"])
        cls.case_files = files
        cls.base_files = {_actual(slot): files[_actual(slot)] for slot in BASE_SLOTS}

    @staticmethod
    def _bundled_request(action, payload):
        request = json.dumps({"action": action, "payload": payload}, ensure_ascii=False)
        completed = subprocess.run(
            [sys.executable, str(BUNDLE), "request", "--input", "-"],
            cwd=str(ROOT),
            input=request,
            text=True,
            capture_output=True,
        )
        if completed.returncode != 0:
            raise AssertionError(completed.stdout + completed.stderr)
        try:
            return json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise AssertionError(completed.stdout + completed.stderr) from exc

    @staticmethod
    def _payload(source_files, source_case_files):
        return {
            "blind_forecast_id": "bf-phase0-bundle-001",
            "subject_id": IDENTITY["subject_id"],
            "question_type": "流年問事",
            "question_reference": "2027-work",
            "locked_at": "2026-08-26T22:12:00+08:00",
            "source_files_used": list(source_files),
            "source_case_files": source_case_files,
            "blind_forecast_payload": {"核心結論": "synthetic bundle parity forecast"},
        }

    def test_progressive_manifest_base_only_lock_matches_generated_bundle(self):
        payload = self._payload(self.base_files, self.base_files)
        modular = dispatch("lock_blind_forecast", payload)
        bundled = self._bundled_request("lock_blind_forecast", payload)
        self.assertTrue(modular["ok"], modular)
        self.assertEqual(bundled, modular)

    def test_progressive_content_rejection_matches_generated_bundle(self):
        stage1_with_05 = dict(self.base_files)
        stage1_with_05[_actual(PROGRESSIVE_SLOT)] = self.case_files[_actual(PROGRESSIVE_SLOT)]
        payload = self._payload(stage1_with_05, stage1_with_05)
        modular = dispatch("lock_blind_forecast", payload)
        bundled = self._bundled_request("lock_blind_forecast", payload)
        self.assertFalse(modular["ok"])
        self.assertEqual(modular["error"]["code"], "blind_source_violation")
        self.assertEqual(bundled, modular)


if __name__ == "__main__":
    unittest.main()
