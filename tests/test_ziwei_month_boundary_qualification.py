import json
import subprocess
import sys
import unittest
from pathlib import Path
from zoneinfo import ZoneInfo

from lunar_python import Lunar, LunarMonth

from engine.calendar.models import CalendarResolverException
from engine.calendar.resolver import resolve_calendar
from engine.calendar.timezone import normalize_local_time
from engine.distribution.runtime import dispatch
from engine.ziwei.fine_cycle_stems import resolve_month_stem
from tools import build_ziwei_month_boundary_qualification as qualifier


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "tools" / "build_ziwei_month_boundary_qualification.py"
REPORT = ROOT / "qualification" / "ziwei" / "month_boundary" / "public-lunar-python-1.4.8.json"
README = ROOT / "qualification" / "ziwei" / "month_boundary" / "README.md"
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


def _solar_date(lunar_year, lunar_month, lunar_day):
    return Lunar.fromYmdHms(lunar_year, lunar_month, lunar_day, 12, 0, 0).getSolar().toYmd()


def _resolved_month(civil_date, hour="12:00:00", timezone="Asia/Taipei", offset_hint=None):
    result = resolve_calendar("%sT%s" % (civil_date, hour), timezone, offset_hint)
    if not result.ok or result.context is None:
        raise AssertionError(result)
    return result.context, resolve_month_stem(result.context)


class ZiweiMonthBoundaryQualificationTests(unittest.TestCase):
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

    def _forecast(self, target, scopes=("monthly",)):
        return dispatch(
            "resolve_forecast_context",
            {
                "normalized_natal": self.normalized,
                "target": {"civil_datetime": target, "timezone": "Asia/Taipei"},
                "requested_scopes": list(scopes),
            },
        )

    def test_reproducible_month_boundary_qualification_deliverables_exist(self):
        self.assertTrue(BUILDER.is_file(), "missing reproducible Ziwei month-boundary qualification builder")
        self.assertTrue(REPORT.is_file(), "missing committed Ziwei month-boundary qualification evidence")
        self.assertTrue(README.is_file(), "missing Ziwei month-boundary qualification scope document")

    def test_committed_evidence_matches_fresh_pinned_oracle_run(self):
        committed = json.loads(REPORT.read_text(encoding="utf-8"))
        fresh = qualifier.build_report()
        self.assertEqual(committed, fresh)
        self.assertEqual(fresh["result"], "PASS")
        self.assertEqual(fresh["mismatch_count"], 0)
        self.assertEqual(fresh["mismatches"], [])
        self.assertFalse(fresh["maturity_promotion"])
        self.assertEqual(fresh["oracle"]["package"], "lunar-python")
        self.assertEqual(fresh["oracle"]["version"], "1.4.8")
        self.assertFalse(fresh["oracle"]["runtime_authority"])
        self.assertEqual(fresh["phase2b_lunar_lite_anchor"]["status"], "PASS")
        self.assertFalse(
            fresh["phase2b_lunar_lite_anchor"]["direct_runtime_limit"]["direct_oracle_usable"]
        )

    def test_evidence_closes_leap_twelfth_with_explicit_oracle_limit(self):
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        coverage = report["coverage"]
        self.assertEqual(coverage["ordinary_months"]["cases"], 72)
        self.assertEqual(coverage["leap_month_boundaries"]["cases"], 14)
        self.assertEqual(coverage["ordinal_13_to_next_year_month_1_property"]["cases"], 10)
        self.assertTrue(coverage["ordinal_13_to_next_year_month_1_property"]["passed"])
        leap12 = coverage["leap_twelfth_month_second_half"]
        self.assertEqual(leap12["historical_lunar_year"], 1574)
        self.assertEqual(leap12["oracle_leap_month"], -12)
        self.assertEqual(leap12["oracle_following_year"], 1575)
        self.assertEqual(leap12["oracle_following_month"], 1)
        self.assertEqual(leap12["project_day16_effective_month"], 1)
        self.assertEqual(leap12["project_day16_ganzhi"], leap12["oracle_following_ganzhi"])
        self.assertTrue(leap12["qualified"])

    def test_check_mode_accepts_committed_evidence_without_mutation(self):
        before = REPORT.read_bytes()
        completed = subprocess.run(
            [sys.executable, str(BUILDER), "--check"],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("Ziwei month-boundary qualification evidence is up to date", completed.stdout)
        self.assertEqual(REPORT.read_bytes(), before)

    def test_real_leap_month_day15_day16_changes_month_source_once(self):
        day15 = _solar_date(2023, -2, 15)
        day16 = _solar_date(2023, -2, 16)
        context15, resolved15 = _resolved_month(day15)
        context16, resolved16 = _resolved_month(day16)
        self.assertTrue(context15.lunar.is_leap_month)
        self.assertTrue(context16.lunar.is_leap_month)
        self.assertEqual((context15.lunar.month, context15.lunar.day), (2, 15))
        self.assertEqual((context16.lunar.month, context16.lunar.day), (2, 16))
        self.assertEqual(resolved15.reference, "lunar:2023-L02-A")
        self.assertEqual(resolved16.reference, "lunar:2023-L02-B")
        leap = LunarMonth.fromYm(2023, -2)
        following = leap.next(1)
        self.assertEqual(
            resolved15.heavenly_stem + resolved15.earthly_branch,
            leap.getGanZhi(),
        )
        self.assertEqual(
            resolved16.heavenly_stem + resolved16.earthly_branch,
            following.getGanZhi(),
        )

    def test_ordinary_month_and_lunar_year_boundaries_follow_neutral_calendar_conversion(self):
        month = LunarMonth.fromYm(2023, 6)
        last_day = _solar_date(2023, 6, month.getDayCount())
        next_day = _solar_date(2023, 7, 1)
        context_last, resolved_last = _resolved_month(last_day)
        context_next, resolved_next = _resolved_month(next_day)
        self.assertEqual((context_last.lunar.month, context_last.lunar.day), (6, month.getDayCount()))
        self.assertEqual((context_next.lunar.month, context_next.lunar.day), (7, 1))
        self.assertNotEqual(resolved_last.reference, resolved_next.reference)

        month12 = LunarMonth.fromYm(2023, 12)
        year_last = _solar_date(2023, 12, month12.getDayCount())
        year_next = _solar_date(2024, 1, 1)
        year_last_context, year_last_resolved = _resolved_month(year_last)
        year_next_context, year_next_resolved = _resolved_month(year_next)
        self.assertEqual(year_last_context.lunar.year, 2023)
        self.assertEqual(year_last_context.lunar.month, 12)
        self.assertEqual(year_next_context.lunar.year, 2024)
        self.assertEqual(year_next_context.lunar.month, 1)
        self.assertNotEqual(year_last_resolved.reference, year_next_resolved.reference)
        self.assertEqual(
            year_next_resolved.heavenly_stem + year_next_resolved.earthly_branch,
            LunarMonth.fromYm(2024, 1).getGanZhi(),
        )

    def test_2300_does_not_independently_advance_month_layer(self):
        before_context, before = _resolved_month("2026-09-15", "22:59:00")
        after_context, after = _resolved_month("2026-09-15", "23:00:00")
        self.assertEqual(before_context.normalized_time.gregorian_date, after_context.normalized_time.gregorian_date)
        self.assertEqual(before_context.lunar, after_context.lunar)
        self.assertEqual(before.reference, after.reference)
        self.assertEqual(
            before.heavenly_stem + before.earthly_branch,
            after.heavenly_stem + after.earthly_branch,
        )

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

    def test_dst_offset_resolution_does_not_fork_month_result(self):
        first = resolve_calendar("2026-11-01T01:30:00", "America/New_York", "-04:00")
        second = resolve_calendar("2026-11-01T01:30:00", "America/New_York", "-05:00")
        self.assertTrue(first.ok, first)
        self.assertTrue(second.ok, second)
        self.assertIsNotNone(first.context)
        self.assertIsNotNone(second.context)
        self.assertNotEqual(first.context.normalized_time.utc_datetime, second.context.normalized_time.utc_datetime)
        first_month = resolve_month_stem(first.context)
        second_month = resolve_month_stem(second.context)
        self.assertEqual(first_month.reference, second_month.reference)
        self.assertEqual(
            first_month.heavenly_stem + first_month.earthly_branch,
            second_month.heavenly_stem + second_month.earthly_branch,
        )

    def test_monthly_downstream_layers_reuse_one_resolved_source(self):
        target = _solar_date(2023, -2, 16) + "T14:30:00"
        result = self._forecast(target)
        self.assertTrue(result["ok"], result)
        layer = result["data"]["ziwei"]["monthly"]
        resolved = layer["resolved_cycle"]
        transform = layer["transformation_layer"]
        flowing = layer["flowing_star_layer"]
        self.assertEqual(transform["identity"]["reference"], resolved["reference"])
        self.assertEqual(flowing["source"]["reference"], resolved["reference"])
        self.assertEqual(transform["source"]["heavenly_stem"], resolved["heavenly_stem"])
        self.assertEqual(flowing["source"]["heavenly_stem"], resolved["heavenly_stem"])
        self.assertEqual(flowing["source"]["earthly_branch"], resolved["earthly_branch"])
        self.assertEqual(layer["source_resolution_count"], 1)

    def test_generated_runtime_matches_modular_month_boundaries(self):
        leap15 = _solar_date(2023, -2, 15) + "T14:30:00"
        leap16 = _solar_date(2023, -2, 16) + "T14:30:00"
        month12 = LunarMonth.fromYm(2023, 12)
        lunar_year_last = _solar_date(2023, 12, month12.getDayCount()) + "T14:30:00"
        lunar_year_next = _solar_date(2024, 1, 1) + "T14:30:00"
        targets = (
            "2026-09-15T14:30:00",
            "2026-09-15T23:30:00",
            leap15,
            leap16,
            lunar_year_last,
            lunar_year_next,
        )
        for target in targets:
            with self.subTest(target=target):
                payload = {
                    "normalized_natal": self.normalized,
                    "target": {"civil_datetime": target, "timezone": "Asia/Taipei"},
                    "requested_scopes": ["monthly"],
                }
                modular = dispatch("resolve_forecast_context", payload)
                bundled = self._bundled_request("resolve_forecast_context", payload)
                self.assertTrue(modular["ok"], modular)
                self.assertEqual(bundled, modular)


if __name__ == "__main__":
    unittest.main()
