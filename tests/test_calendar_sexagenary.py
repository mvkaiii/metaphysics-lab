import unittest
from datetime import date

from engine.calendar.sexagenary import (
    five_mouse_hour,
    five_tiger_month,
    gregorian_jdn,
    lunar_year_stem,
    sexagenary_day,
)


class CalendarSexagenaryTests(unittest.TestCase):
    def test_known_public_days(self):
        self.assertEqual(sexagenary_day(date(2023, 3, 9)), ("丙", "寅"))
        self.assertEqual(sexagenary_day(date(2023, 4, 8)), ("丙", "申"))
        self.assertEqual(sexagenary_day(date(1987, 12, 6)), ("己", "丑"))

    def test_jdn_consecutive_dates_increment_once(self):
        self.assertEqual(
            gregorian_jdn(date(2023, 3, 10)) - gregorian_jdn(date(2023, 3, 9)),
            1,
        )

    def test_lunar_year_stem_cycles(self):
        self.assertEqual(lunar_year_stem(2023), "癸")
        self.assertEqual(lunar_year_stem(2083), "癸")

    def test_five_tiger_month_vectors(self):
        self.assertEqual(five_tiger_month("癸", 1), ("甲", "寅"))
        self.assertEqual(five_tiger_month("癸", 6), ("己", "未"))
        self.assertEqual(five_tiger_month("癸", 13), ("丙", "寅"))

    def test_five_mouse_vectors(self):
        self.assertEqual(five_mouse_hour("己", "丑"), ("乙", "丑"))
        self.assertEqual(five_mouse_hour("庚", "子"), ("丙", "子"))

    def test_invalid_inputs_fail_closed(self):
        with self.assertRaises(ValueError):
            five_tiger_month("X", 1)
        with self.assertRaises(ValueError):
            five_tiger_month("甲", 0)
        with self.assertRaises(ValueError):
            five_tiger_month("甲", 14)
        with self.assertRaises(ValueError):
            five_mouse_hour("X", "子")
        with self.assertRaises(ValueError):
            five_mouse_hour("甲", "X")
        with self.assertRaises(ValueError):
            lunar_year_stem("2023")


if __name__ == "__main__":
    unittest.main()
