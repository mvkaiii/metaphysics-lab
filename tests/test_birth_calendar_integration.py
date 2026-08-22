import unittest
from datetime import date, time

from engine.birth.calendar_adapter import resolve_birth_calendar
from engine.birth.models import (
    BirthDateInput,
    BirthInput,
    BirthPlaceInput,
    BirthTimeInput,
    ResolvedBirthPlace,
    Sex,
)
from engine.calendar.precision import TimePrecision


def make_birth(year, month, day, hour, minute, place_label="台北市"):
    return BirthInput(
        sex=Sex.MALE,
        birth_date=BirthDateInput(date(year, month, day), TimePrecision.DAY),
        birth_time=BirthTimeInput(time(hour, minute), None, TimePrecision.HOUR, "%02d:%02d" % (hour, minute)),
        birth_place=BirthPlaceInput(place_label),
    )


def make_location(timezone="Asia/Taipei"):
    return ResolvedBirthPlace(
        canonical_name="Taipei City, Taiwan" if timezone == "Asia/Taipei" else "New York, USA",
        latitude=25.0375 if timezone == "Asia/Taipei" else 40.7128,
        longitude=121.5637 if timezone == "Asia/Taipei" else -74.0060,
        timezone=timezone,
        provider_name="fixture",
        provider_version="1",
        resolution_status="resolved",
        provider_reference="fixture:1",
    )


class BirthCalendarIntegrationTests(unittest.TestCase):
    def test_taipei_birth_input_reaches_existing_calendar_resolver(self):
        resolution = resolve_birth_calendar(make_birth(1984, 3, 13, 19, 20), make_location())
        self.assertTrue(resolution.ok)
        self.assertEqual(resolution.context.input.timezone, "Asia/Taipei")
        self.assertEqual(resolution.context.input.civil_datetime, "1984-03-13T19:20:00")
        self.assertEqual(resolution.context.normalized_time.utc_offset, "+08:00")
        self.assertFalse(resolution.context.policies.metaphysics_day_boundary_applied)

    def test_dst_nonexistent_time_preserves_calendar_error_code(self):
        resolution = resolve_birth_calendar(
            make_birth(2026, 3, 8, 2, 30, "New York"),
            make_location("America/New_York"),
        )
        self.assertFalse(resolution.ok)
        self.assertEqual(resolution.error.code, "nonexistent_local_time")

    def test_calendar_boundary_conflict_is_not_renamed_to_success(self):
        resolution = resolve_birth_calendar(make_birth(2057, 9, 28, 12, 0), make_location())
        self.assertTrue(resolution.ok)
        self.assertEqual(resolution.context.validation.overall_status, "boundary_conflict")


if __name__ == "__main__":
    unittest.main()
