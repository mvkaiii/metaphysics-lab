import unittest
from datetime import date
from unittest.mock import patch
from engine.calendar.lunar import (
    LunarProviderFailure,
    LunarProviderUnsupportedDate,
    LunarPythonProvider,
    calendar_validation_for,
)
from engine.calendar.models import LunarDate


class CalendarLunarTests(unittest.TestCase):
    def test_known_lunar_new_year(self):
        self.assertEqual(
            LunarPythonProvider().convert(date(2025, 1, 29)),
            LunarDate(2025, 1, 1, False),
        )

    def test_known_2025_leap_sixth_month(self):
        self.assertEqual(
            LunarPythonProvider().convert(date(2025, 7, 25)),
            LunarDate(2025, 6, 1, True),
        )

    def test_validated_edges(self):
        self.assertEqual(calendar_validation_for(date(1901, 1, 1)).check.status, "validated")
        self.assertEqual(calendar_validation_for(date(2100, 12, 31)).check.status, "validated")

    def test_2057_conflict_window(self):
        for value in (date(2057, 9, 28), date(2057, 10, 10), date(2057, 10, 27)):
            decision = calendar_validation_for(value)
            self.assertEqual(decision.check.status, "boundary_conflict")
            self.assertEqual(decision.boundary_id, "hko-new-moon-2057-09-28-conflict")
        self.assertEqual(calendar_validation_for(date(2057, 10, 28)).check.status, "validated")

    def test_caution_dates(self):
        self.assertEqual(calendar_validation_for(date(2089, 9, 4)).check.status, "boundary_caution")
        self.assertEqual(calendar_validation_for(date(2097, 8, 7)).check.status, "boundary_caution")

    def test_out_of_validated_range(self):
        self.assertEqual(
            calendar_validation_for(date(2150, 3, 1)).check.status,
            "out_of_validated_range",
        )

    @patch("engine.calendar.lunar.Solar.fromYmd", side_effect=IndexError("unsupported"))
    def test_provider_unsupported_date(self, _mock):
        with self.assertRaises(LunarProviderUnsupportedDate):
            LunarPythonProvider().convert(date(2150, 3, 1))

    @patch("engine.calendar.lunar.Solar.fromYmd", side_effect=RuntimeError("boom"))
    def test_provider_failure(self, _mock):
        with self.assertRaises(LunarProviderFailure):
            LunarPythonProvider().convert(date(2026, 8, 21))


if __name__ == "__main__":
    unittest.main()
