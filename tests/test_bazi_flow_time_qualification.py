import json
import subprocess
import sys
import unittest
from pathlib import Path
from zoneinfo import ZoneInfo

from engine.bazi.calendar import day_pillar, time_pillar
from engine.calendar.models import CalendarResolverException
from engine.calendar.timezone import normalize_local_time
from engine.distribution.runtime import dispatch
from tools import build_bazi_flow_time_qualification as qualifier


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "tools" / "build_bazi_flow_time_qualification.py"
REPORT = ROOT / "qualification" / "bazi" / "flow_time" / "public-lunar-python-1.4.8.json"
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


class _SystemZoneProviderForTest:
    def zone(self, timezone_name):
        try:
            return ZoneInfo(timezone_name)
        except Exception as exc:
            raise CalendarResolverException(
                "invalid_timezone",
                "unknown IANA timezone: %r" % timezone_name,
                {"timezone": timezone_name},
            ) from exc


TEST_ZONE_PROVIDER = _SystemZoneProviderForTest()


class BaziFlowTimeQualificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        built = dispatch("build_natal", {"birth": BIRTH, "resolved_location": LOCATION})
        if not built.get("ok"):
            raise AssertionError(built)
        cls.normalized = built["data"]["normalized_natal"]

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
        return json.loads(completed.stdout)

    def test_reproducible_public_qualification_deliverables_exist(self):
        self.assertTrue(BUILDER.is_file(), "missing reproducible flow-time qualification builder")
        self.assertTrue(REPORT.is_file(), "missing committed public flow-time qualification evidence")

    def test_committed_public_evidence_matches_fresh_pinned_oracle_run(self):
        committed = json.loads(REPORT.read_text(encoding="utf-8"))
        fresh = qualifier.build_report()
        self.assertEqual(committed, fresh)
        self.assertEqual(fresh["result"], "PASS")
        self.assertEqual(fresh["mismatch_count"], 0)
        self.assertEqual(fresh["mismatches"], [])
        self.assertFalse(fresh["maturity_promotion"])
        self.assertEqual(fresh["oracle"]["package"], "lunar-python")
        self.assertEqual(fresh["oracle"]["version"], "1.4.8")
        self.assertEqual(fresh["oracle"]["eight_char_sect"], 1)

    def test_public_evidence_covers_required_ranges_and_matrices(self):
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        coverage = report["coverage"]
        self.assertEqual(
            coverage["day_samples"],
            {"start": "1980-01-01", "end": "2050-12-31", "step_days": 97, "cases": 268},
        )
        self.assertEqual(coverage["early_zi_boundary"]["cases"], 16)
        self.assertEqual(
            coverage["early_zi_boundary"]["zones"],
            ["Asia/Taipei", "Asia/Tokyo", "America/New_York", "Europe/London"],
        )
        self.assertEqual(coverage["gregorian_transitions"]["cases"], 13)
        self.assertEqual(
            coverage["five_rat_matrix"],
            {"day_stems": 10, "hour_branches": 12, "cases": 120},
        )
        self.assertEqual(coverage["consecutive_day_property"]["pairs"], 730)

    def test_check_mode_accepts_committed_evidence_without_mutation(self):
        before = REPORT.read_bytes()
        completed = subprocess.run(
            [sys.executable, str(BUILDER), "--check"],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("qualification evidence is up to date", completed.stdout)
        self.assertEqual(REPORT.read_bytes(), before)

    def test_dst_nonexistent_and_ambiguous_times_are_resolver_owned(self):
        with self.assertRaises(CalendarResolverException) as spring:
            normalize_local_time(
                "2026-03-08T02:30:00",
                "America/New_York",
                provider=TEST_ZONE_PROVIDER,
            )
        self.assertEqual(spring.exception.error.code, "nonexistent_local_time")

        with self.assertRaises(CalendarResolverException) as fall:
            normalize_local_time(
                "2026-11-01T01:30:00",
                "America/New_York",
                provider=TEST_ZONE_PROVIDER,
            )
        self.assertEqual(fall.exception.error.code, "ambiguous_local_time")
        self.assertEqual(len(fall.exception.error.details["candidates"]), 2)

    def test_dst_offset_resolution_does_not_create_two_bazi_results_for_same_local_civil_time(self):
        first = normalize_local_time(
            "2026-11-01T01:30:00",
            "America/New_York",
            "-04:00",
            provider=TEST_ZONE_PROVIDER,
        )
        second = normalize_local_time(
            "2026-11-01T01:30:00",
            "America/New_York",
            "-05:00",
            provider=TEST_ZONE_PROVIDER,
        )
        self.assertNotEqual(first.utc_datetime, second.utc_datetime)
        self.assertEqual(day_pillar(first.local_datetime), day_pillar(second.local_datetime))
        self.assertEqual(time_pillar(first.local_datetime), time_pillar(second.local_datetime))

    def test_generated_runtime_matches_modular_daily_hourly_context_at_ordinary_and_late_zi_times(self):
        for target in ("2026-09-15T14:30:00", "2026-09-15T23:30:00"):
            with self.subTest(target=target):
                payload = {
                    "normalized_natal": self.normalized,
                    "target": {"civil_datetime": target, "timezone": "Asia/Taipei"},
                    "requested_scopes": ["daily", "hourly"],
                }
                modular = dispatch("resolve_forecast_context", payload)
                bundled = self._bundled_request("resolve_forecast_context", payload)
                self.assertTrue(modular["ok"], modular)
                self.assertEqual(bundled, modular)


if __name__ == "__main__":
    unittest.main()
