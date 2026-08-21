import unittest
import engine.calendar as calendar


class CalendarPackageExportTests(unittest.TestCase):
    def test_public_exports_exist(self):
        for name in (
            "TimePrecision",
            "PrecisionAssessment",
            "assess_precision",
            "CalendarContext",
            "CalendarResolution",
            "resolve_calendar",
        ):
            self.assertTrue(hasattr(calendar, name), name)


if __name__ == "__main__":
    unittest.main()
