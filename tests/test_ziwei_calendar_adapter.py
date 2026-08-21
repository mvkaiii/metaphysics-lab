import unittest
from engine.calendar.resolver import resolve_calendar
from engine.ziwei.calendar_adapter import (
    ZiweiCalendarAdapterError,
    ziwei_day_from_calendar,
    ziwei_hour_from_calendar,
    ziwei_month_from_calendar,
)
from engine.ziwei.day import project_derived_ziwei_day
from engine.ziwei.hour import project_derived_ziwei_hour
from engine.ziwei.month import project_derived_ziwei_month


class ZiweiCalendarAdapterTests(unittest.TestCase):
    def test_month_adapter_passes_resolved_lunar_fields(self):
        context = resolve_calendar("2025-01-29T12:00:00", "Asia/Taipei").context
        assert context is not None
        adapted = ziwei_month_from_calendar(context, 5, "戌", "巳")
        expected = project_derived_ziwei_month(
            5,
            "戌",
            "巳",
            context.lunar.month,
            context.lunar.day,
            context.lunar.is_leap_month,
        )
        self.assertEqual(adapted["ziwei"], expected)

    def test_day_adapter_passes_resolved_lunar_fields(self):
        context = resolve_calendar("2025-01-29T12:00:00", "Asia/Taipei").context
        assert context is not None
        adapted = ziwei_day_from_calendar(context, 5, "戌", "巳")
        expected = project_derived_ziwei_day(
            5,
            "戌",
            "巳",
            context.lunar.month,
            context.lunar.day,
            context.lunar.is_leap_month,
        )
        self.assertEqual(adapted["ziwei"], expected)

    def test_hour_adapter_uses_resolver_hour_branch_without_day_rollover(self):
        context = resolve_calendar("2026-09-18T23:30:00", "Asia/Taipei").context
        assert context is not None
        adapted = ziwei_hour_from_calendar(context, 5, "戌", "午")
        expected = project_derived_ziwei_hour(
            5,
            "戌",
            "午",
            context.lunar.month,
            context.lunar.day,
            context.lunar.is_leap_month,
            "子",
        )
        self.assertEqual(adapted["ziwei"], expected)
        self.assertEqual(adapted["calendar"]["gregorian_date"], "2026-09-18")
        self.assertFalse(adapted["calendar"]["metaphysics_day_boundary_applied"])

    def test_boundary_conflict_is_rejected(self):
        context = resolve_calendar("2057-09-28T12:00:00", "Asia/Taipei").context
        assert context is not None
        with self.assertRaises(ZiweiCalendarAdapterError) as ctx:
            ziwei_day_from_calendar(context, 5, "戌", "巳")
        self.assertEqual(ctx.exception.code, "boundary_conflict")


if __name__ == "__main__":
    unittest.main()
