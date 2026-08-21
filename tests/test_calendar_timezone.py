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


if __name__ == "__main__":
    unittest.main()
