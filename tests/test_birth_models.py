import unittest
from datetime import date, time

from engine.birth.errors import BirthFoundationError
from engine.birth.models import (
    BirthDateInput,
    BirthInput,
    BirthPlaceInput,
    BirthTimeInput,
    Sex,
)
from engine.calendar.precision import TimePrecision


class BirthModelTests(unittest.TestCase):
    def test_birth_input_preserves_reported_values(self):
        birth = BirthInput(
            sex=Sex.MALE,
            birth_date=BirthDateInput(date(1984, 3, 13), TimePrecision.DAY),
            birth_time=BirthTimeInput(time(19, 20), None, TimePrecision.HOUR, "19:20"),
            birth_place=BirthPlaceInput("台北市"),
        )
        payload = birth.to_dict()
        self.assertEqual(payload["sex"], "male")
        self.assertEqual(payload["birth_date"]["value"], "1984-03-13")
        self.assertEqual(payload["birth_time"]["label"], "19:20")
        self.assertEqual(payload["birth_place"]["label"], "台北市")
        self.assertEqual(payload["calendar_kind"], "gregorian")

    def test_birth_time_range_must_not_run_backwards(self):
        with self.assertRaises(BirthFoundationError) as caught:
            BirthTimeInput(time(22, 0), time(20, 0), TimePrecision.HOUR, "20:00-22:00")
        self.assertEqual(caught.exception.code, "invalid_birth_time_range")

    def test_birth_place_must_not_be_blank(self):
        with self.assertRaises(BirthFoundationError) as caught:
            BirthPlaceInput("   ")
        self.assertEqual(caught.exception.code, "invalid_birth_place")

    def test_mode_a_only_accepts_gregorian_calendar_in_v1(self):
        with self.assertRaises(BirthFoundationError) as caught:
            BirthInput(
                sex=Sex.FEMALE,
                birth_date=BirthDateInput(date(1990, 5, 6), TimePrecision.DAY),
                birth_time=BirthTimeInput(time(15, 20), None, TimePrecision.HOUR, "15:20"),
                birth_place=BirthPlaceInput("高雄市"),
                calendar_kind="lunar",
            )
        self.assertEqual(caught.exception.code, "unsupported_birth_calendar")


if __name__ == "__main__":
    unittest.main()
