import unittest
from engine.calendar.models import CalendarResolverException
from engine.calendar.timezone import normalize_local_time


class CalendarTimezoneTests(unittest.TestCase):
    def test_taipei_ordinary_normalization(self):
        result = normalize_local_time("2026-09-18T14:00:00", "Asia/Taipei")
        self.assertEqual(result.utc_offset, "+08:00")
        self.assertEqual(result.utc_datetime.isoformat(), "2026-09-18T06:00:00+00:00")
        self.assertEqual(result.gregorian_date.isoformat(), "2026-09-18")
        self.assertEqual(result.hour_branch, "未")

    def test_embedded_offset_is_invalid_datetime(self):
        with self.assertRaises(CalendarResolverException) as ctx:
            normalize_local_time("2026-09-18T14:00:00+08:00", "Asia/Taipei")
        self.assertEqual(ctx.exception.error.code, "invalid_datetime")

    def test_date_only_is_invalid_datetime(self):
        with self.assertRaises(CalendarResolverException) as ctx:
            normalize_local_time("2026-09-18", "Asia/Taipei")
        self.assertEqual(ctx.exception.error.code, "invalid_datetime")

    def test_invalid_iana_timezone(self):
        with self.assertRaises(CalendarResolverException) as ctx:
            normalize_local_time("2026-09-18T14:00:00", "Mars/Olympus")
        self.assertEqual(ctx.exception.error.code, "invalid_timezone")

    def test_hour_branch_does_not_change_civil_date_at_23(self):
        cases = (
            ("2026-09-18T22:59:00", "2026-09-18", "亥"),
            ("2026-09-18T23:00:00", "2026-09-18", "子"),
            ("2026-09-18T23:59:00", "2026-09-18", "子"),
            ("2026-09-19T00:00:00", "2026-09-19", "子"),
            ("2026-09-19T00:59:00", "2026-09-19", "子"),
            ("2026-09-19T01:00:00", "2026-09-19", "丑"),
        )
        for value, expected_date, expected_branch in cases:
            result = normalize_local_time(value, "Asia/Taipei")
            self.assertEqual(result.gregorian_date.isoformat(), expected_date)
            self.assertEqual(result.hour_branch, expected_branch)

    def test_new_york_spring_forward_gap_is_error(self):
        with self.assertRaises(CalendarResolverException) as ctx:
            normalize_local_time("2026-03-08T02:30:00", "America/New_York")
        self.assertEqual(ctx.exception.error.code, "nonexistent_local_time")

    def test_new_york_fall_back_lists_two_candidates(self):
        with self.assertRaises(CalendarResolverException) as ctx:
            normalize_local_time("2026-11-01T01:30:00", "America/New_York")
        self.assertEqual(ctx.exception.error.code, "ambiguous_local_time")
        self.assertEqual(
            ctx.exception.error.details["candidates"],
            [
                {"utc_offset": "-04:00", "utc_datetime": "2026-11-01T05:30:00+00:00"},
                {"utc_offset": "-05:00", "utc_datetime": "2026-11-01T06:30:00+00:00"},
            ],
        )

    def test_valid_offset_hints_choose_exact_candidate(self):
        first = normalize_local_time("2026-11-01T01:30:00", "America/New_York", "-04:00")
        second = normalize_local_time("2026-11-01T01:30:00", "America/New_York", "-05:00")
        self.assertEqual(first.utc_datetime.isoformat(), "2026-11-01T05:30:00+00:00")
        self.assertEqual(second.utc_datetime.isoformat(), "2026-11-01T06:30:00+00:00")

    def test_invalid_offset_hint_is_rejected(self):
        with self.assertRaises(CalendarResolverException) as ctx:
            normalize_local_time("2026-11-01T01:30:00", "America/New_York", "-06:00")
        self.assertEqual(ctx.exception.error.code, "invalid_utc_offset_hint")

    def test_unique_time_cannot_be_overridden_by_wrong_hint(self):
        with self.assertRaises(CalendarResolverException) as ctx:
            normalize_local_time("2026-07-15T12:00:00", "America/New_York", "-05:00")
        self.assertEqual(ctx.exception.error.code, "invalid_utc_offset_hint")

    def test_cross_zone_roundtrips(self):
        cases = (
            ("2026-01-15T12:00:00", "America/New_York", "-05:00"),
            ("2026-07-15T12:00:00", "America/New_York", "-04:00"),
            ("2026-01-15T12:00:00", "Europe/London", "+00:00"),
            ("2026-07-15T12:00:00", "Europe/London", "+01:00"),
            ("2026-07-15T12:00:00", "Asia/Tokyo", "+09:00"),
            ("2026-01-15T12:00:00", "Australia/Sydney", "+11:00"),
            ("2026-07-15T12:00:00", "Australia/Sydney", "+10:00"),
        )
        for value, zone, offset in cases:
            result = normalize_local_time(value, zone)
            self.assertEqual(result.utc_offset, offset)
            self.assertEqual(
                result.utc_datetime.astimezone(result.local_datetime.tzinfo).replace(tzinfo=None),
                result.local_datetime.replace(tzinfo=None),
            )

    def test_historical_taipei_offsets(self):
        cases = (
            ("1937-09-30T12:00:00", "+08:00"),
            ("1937-10-01T12:00:00", "+09:00"),
            ("1945-09-20T12:00:00", "+09:00"),
            ("1945-09-21T12:00:00", "+08:00"),
            ("1946-06-01T12:00:00", "+09:00"),
            ("1946-11-01T12:00:00", "+08:00"),
            ("1979-08-01T12:00:00", "+09:00"),
            ("1979-11-01T12:00:00", "+08:00"),
        )
        for value, offset in cases:
            self.assertEqual(normalize_local_time(value, "Asia/Taipei").utc_offset, offset)


if __name__ == "__main__":
    unittest.main()
