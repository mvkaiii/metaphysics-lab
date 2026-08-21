import unittest
from datetime import date
from engine.calendar.models import LunarDate, LunarProviderMetadata
from engine.calendar.resolver import resolve_calendar


class StubFutureProvider:
    metadata = LunarProviderMetadata("stub", "1", "test-only")

    def convert(self, civil_date: date) -> LunarDate:
        return LunarDate(2150, 1, 1, False)


class CalendarResolverTests(unittest.TestCase):
    def test_success_context(self):
        result = resolve_calendar("2026-09-18T14:00:00", "Asia/Taipei")
        self.assertTrue(result.ok)
        context = result.context
        assert context is not None
        self.assertEqual(context.schema_version, "1.0")
        self.assertEqual(context.resolver_version, "1.0.0")
        self.assertEqual(context.normalized_time.hour_branch, "未")
        self.assertFalse(context.policies.metaphysics_day_boundary_applied)
        self.assertEqual(context.providers.lunar_calendar.version, "1.4.8")
        self.assertEqual(context.providers.timezone_database.tzdb_version, "2026c")

    def test_23xx_keeps_same_civil_date(self):
        result = resolve_calendar("2026-09-18T23:30:00", "Asia/Taipei")
        context = result.context
        assert context is not None
        self.assertEqual(context.normalized_time.gregorian_date.isoformat(), "2026-09-18")
        self.assertEqual(context.normalized_time.hour_branch, "子")
        self.assertFalse(context.policies.metaphysics_day_boundary_applied)

    def test_boundary_conflict_remains_success_with_conflict_metadata(self):
        result = resolve_calendar("2057-09-28T12:00:00", "Asia/Taipei")
        self.assertTrue(result.ok)
        context = result.context
        assert context is not None
        self.assertEqual(context.validation.calendar_conversion.status, "boundary_conflict")
        self.assertEqual(context.validation.overall_status, "boundary_conflict")

    def test_out_of_range_provider_success_is_not_error(self):
        result = resolve_calendar(
            "2150-03-01T12:00:00",
            "Asia/Taipei",
            lunar_provider=StubFutureProvider(),
        )
        self.assertTrue(result.ok)
        context = result.context
        assert context is not None
        self.assertEqual(context.validation.calendar_conversion.status, "out_of_validated_range")

    def test_invalid_timezone_returns_public_error(self):
        result = resolve_calendar("2026-09-18T14:00:00", "Mars/Olympus")
        self.assertFalse(result.ok)
        assert result.error is not None
        self.assertEqual(result.error.code, "invalid_timezone")


if __name__ == "__main__":
    unittest.main()
