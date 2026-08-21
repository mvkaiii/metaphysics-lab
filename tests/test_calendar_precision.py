import unittest

from engine.calendar.precision import TimePrecision, assess_precision


class CalendarPrecisionTests(unittest.TestCase):
    def test_year_question_does_not_require_fake_datetime(self):
        result = assess_precision(TimePrecision.YEAR, TimePrecision.YEAR)
        self.assertTrue(result.can_execute)
        self.assertEqual(result.allowed_actions, ())

    def test_month_input_cannot_route_to_day_capability(self):
        result = assess_precision(TimePrecision.DAY, TimePrecision.MONTH)
        self.assertFalse(result.can_execute)
        self.assertEqual(result.reason, "insufficient_precision")
        self.assertEqual(result.allowed_actions, ("ask", "keep_candidates", "downgrade"))

    def test_non_unique_hour_input_cannot_execute(self):
        result = assess_precision(TimePrecision.HOUR, TimePrecision.HOUR, is_unique=False)
        self.assertFalse(result.can_execute)
        self.assertEqual(result.reason, "ambiguous_input")

    def test_exact_day_can_route_to_day_capability(self):
        result = assess_precision(TimePrecision.DAY, TimePrecision.DAY, is_unique=True)
        self.assertTrue(result.can_execute)

    def test_finer_input_can_satisfy_coarser_capability(self):
        result = assess_precision(TimePrecision.MONTH, TimePrecision.DAY)
        self.assertTrue(result.can_execute)


if __name__ == "__main__":
    unittest.main()
