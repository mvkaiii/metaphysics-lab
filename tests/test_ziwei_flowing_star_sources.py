import unittest
from datetime import date
from types import SimpleNamespace

from engine.ziwei.errors import ZiweiFlowingStarError
from engine.ziwei.fine_cycle_stems import resolve_day_stem, resolve_hour_stem, resolve_month_stem
from engine.ziwei.flowing_star_sources import (
    source_from_daily,
    source_from_decadal,
    source_from_hourly,
    source_from_monthly,
    source_from_resolved_cycle,
    source_from_yearly,
)
from engine.ziwei.models import ChartIdentity
from engine.ziwei.natal_models import ZiweiDecadalPeriod
from engine.ziwei.common import PALACE_NAMES
from tests.ziwei_phase2b_fixtures import calendar_context


def chart_identity():
    return ChartIdentity("chart-phase2c", "project_natal", "ziwei-natal-true-solar-common-v1")


class FlowingStarSourceTests(unittest.TestCase):
    def test_month_day_hour_reuse_phase2b_resolution_exactly(self):
        context = calendar_context(
            gregorian_date=date(1987, 12, 6),
            local_hour=21,
            local_minute=30,
            hour_branch="亥",
        )
        cases = (
            (resolve_month_stem(context), source_from_monthly),
            (resolve_day_stem(context), source_from_daily),
            (resolve_hour_stem(context), source_from_hourly),
        )
        for resolution, adapter in cases:
            result = adapter(resolution, chart_identity())
            self.assertEqual(result.scope, resolution.scope)
            self.assertEqual(result.reference, resolution.reference)
            self.assertEqual(result.heavenly_stem, resolution.heavenly_stem)
            self.assertEqual(result.earthly_branch, resolution.earthly_branch)
            self.assertEqual(result.source_profile, resolution.profile_id)
            self.assertEqual(result.rule_version, resolution.rule_version)
            self.assertEqual(result.validation_status, resolution.calendar_validation_status)
            self.assertEqual(result.provenance, resolution.provenance)

    def test_resolution_scope_mismatch_fails_closed(self):
        daily = resolve_day_stem(calendar_context())
        with self.assertRaises(ZiweiFlowingStarError) as caught:
            source_from_resolved_cycle(daily, chart_identity(), "monthly")
        self.assertEqual(caught.exception.code, "cycle_scope_mismatch")

    def test_yearly_source_uses_lunar_year_not_gregorian_year(self):
        before = calendar_context(
            gregorian_date=date(2026, 2, 16),
            lunar_year=2025,
            lunar_month=12,
            lunar_day=29,
        )
        after = calendar_context(
            gregorian_date=date(2026, 2, 17),
            lunar_year=2026,
            lunar_month=1,
            lunar_day=1,
        )
        before_source = source_from_yearly(before, chart_identity())
        after_source = source_from_yearly(after, chart_identity())
        self.assertEqual((before_source.heavenly_stem, before_source.earthly_branch), ("乙", "巳"))
        self.assertEqual(before_source.reference, "lunar-year:2025")
        self.assertEqual((after_source.heavenly_stem, after_source.earthly_branch), ("丙", "午"))
        self.assertEqual(after_source.reference, "lunar-year:2026")

    def test_decadal_source_reuses_period_stem_branch(self):
        period = ZiweiDecadalPeriod(1, 2, 11, PALACE_NAMES[0], "庚辰", "forward")
        result = source_from_decadal(period, chart_identity())
        self.assertEqual((result.heavenly_stem, result.earthly_branch), ("庚", "辰"))
        self.assertIn("1", result.reference)
        self.assertIn("2-11", result.reference)
        self.assertIn("庚辰", result.reference)

    def test_decadal_invalid_pair_and_malformed_source_fail_closed(self):
        invalid_pair = ZiweiDecadalPeriod(1, 2, 11, PALACE_NAMES[0], "甲丑", "forward")
        with self.assertRaises(ZiweiFlowingStarError) as caught:
            source_from_decadal(invalid_pair, chart_identity())
        self.assertEqual(caught.exception.code, "decadal_source_not_resolved")
        malformed = SimpleNamespace(index=1, age_start=2, age_end=11, stem_branch="甲", palace=PALACE_NAMES[0], direction="forward")
        with self.assertRaises(ZiweiFlowingStarError) as caught2:
            source_from_decadal(malformed, chart_identity())
        self.assertEqual(caught2.exception.code, "decadal_source_not_resolved")

    def test_boundary_caution_is_preserved(self):
        resolution = resolve_day_stem(calendar_context(calendar_status="boundary_caution"))
        result = source_from_daily(resolution, chart_identity())
        self.assertEqual(result.validation_status, "boundary_caution")

    def test_boundary_conflict_fails_closed_for_fine_cycle_source(self):
        resolution = SimpleNamespace(
            scope="daily",
            reference="ziwei-day:2026-08-22@late_zi_forward-v1",
            heavenly_stem="戊",
            earthly_branch="午",
            profile_id="ziwei-fine-cycle-lunar-late-zi-v1",
            rule_version="1.0-exp",
            calendar_validation_status="boundary_conflict",
            provenance=resolve_day_stem(calendar_context()).provenance,
        )
        with self.assertRaises(ZiweiFlowingStarError) as caught:
            source_from_daily(resolution, chart_identity())
        self.assertEqual(caught.exception.code, "calendar_boundary_conflict")

    def test_out_of_validated_range_fails_closed(self):
        resolution = SimpleNamespace(
            scope="daily",
            reference="ziwei-day:2101-01-01@late_zi_forward-v1",
            heavenly_stem="己",
            earthly_branch="未",
            profile_id="ziwei-fine-cycle-lunar-late-zi-v1",
            rule_version="1.0-exp",
            calendar_validation_status="out_of_validated_range",
            provenance=resolve_day_stem(calendar_context()).provenance,
        )
        with self.assertRaises(ZiweiFlowingStarError) as caught:
            source_from_daily(resolution, chart_identity())
        self.assertEqual(caught.exception.code, "calendar_out_of_validated_range")

    def test_yearly_boundary_conflict_and_out_of_range_fail_closed(self):
        for status, code in (
            ("boundary_conflict", "calendar_boundary_conflict"),
            ("out_of_validated_range", "calendar_out_of_validated_range"),
        ):
            with self.assertRaises(ZiweiFlowingStarError) as caught:
                source_from_yearly(calendar_context(calendar_status=status), chart_identity())
            self.assertEqual(caught.exception.code, code)


if __name__ == "__main__":
    unittest.main()
