import unittest
from datetime import date, time

from engine.birth.calendar_adapter import resolve_birth_calendar
from engine.birth.errors import BirthFoundationError
from engine.birth.models import (
    BirthDateInput,
    BirthInput,
    BirthPlaceInput,
    BirthTimeInput,
    ResolvedBirthPlace,
    Sex,
)
from engine.birth.time_views import (
    TRUE_SOLAR_NOAA_GAMMA_V1,
    build_birth_time_views,
    equation_of_time_minutes,
    true_solar_adjustment_minutes,
)
from engine.calendar.precision import TimePrecision


def birth_input(hour=19, minute=20):
    return BirthInput(
        sex=Sex.MALE,
        birth_date=BirthDateInput(date(1984, 3, 13), TimePrecision.DAY),
        birth_time=BirthTimeInput(time(hour, minute), None, TimePrecision.HOUR, "%02d:%02d" % (hour, minute)),
        birth_place=BirthPlaceInput("台北市"),
    )


def place(longitude=121.5637):
    return ResolvedBirthPlace(
        canonical_name="Taipei City, Taiwan",
        latitude=25.0375,
        longitude=longitude,
        timezone="Asia/Taipei",
        provider_name="fixture",
        provider_version="1",
        resolution_status="resolved",
        provider_reference="fixture:1",
    )


class BirthTimeViewTests(unittest.TestCase):
    def test_taipei_1984_true_solar_vector_is_formula_frozen(self):
        calendar = resolve_birth_calendar(birth_input(), place()).context
        views = build_birth_time_views(calendar, place())
        self.assertEqual(views.true_solar.profile_id, "true-solar-noaa-gamma-v1")
        self.assertEqual(views.true_solar.rule_version, "1.0-exp")
        self.assertAlmostEqual(views.true_solar.adjustment_minutes, -3.5750772239, places=6)
        self.assertEqual(views.true_solar.local_datetime.strftime("%Y-%m-%d %H:%M:%S"), "1984-03-13 19:16:25")
        self.assertFalse(views.true_solar.boundary_effect["date_changed"])
        self.assertFalse(views.true_solar.boundary_effect["hour_branch_changed"])
        self.assertEqual(views.true_solar.boundary_effect["from_hour_branch"], "戌")
        self.assertEqual(views.true_solar.boundary_effect["to_hour_branch"], "戌")

    def test_synthetic_longitude_can_cross_hour_branch_without_selecting_policy(self):
        synthetic = place(longitude=117.0)
        calendar = resolve_birth_calendar(birth_input(19, 10), synthetic).context
        views = build_birth_time_views(calendar, synthetic)
        self.assertEqual(calendar.normalized_time.hour_branch, "戌")
        self.assertEqual(views.normalized_civil.local_datetime.hour, 19)
        self.assertEqual(views.true_solar.boundary_effect["from_hour_branch"], "戌")
        self.assertEqual(views.true_solar.boundary_effect["to_hour_branch"], "酉")
        self.assertTrue(views.true_solar.boundary_effect["hour_branch_changed"])
        self.assertEqual(views.true_solar.kind, "true_solar")

    def test_reported_and_normalized_civil_views_are_preserved(self):
        calendar = resolve_birth_calendar(birth_input(), place()).context
        views = build_birth_time_views(calendar, place())
        self.assertEqual(views.reported_civil.kind, "reported_civil")
        self.assertEqual(views.normalized_civil.kind, "normalized_civil")
        self.assertEqual(views.reported_civil.local_datetime.strftime("%H:%M"), "19:20")
        self.assertEqual(views.normalized_civil.local_datetime.strftime("%H:%M"), "19:20")
        self.assertEqual(views.reported_civil.adjustment_minutes, 0.0)
        self.assertEqual(views.normalized_civil.adjustment_minutes, 0.0)

    def test_formula_helpers_require_timezone_aware_datetime(self):
        from datetime import datetime
        naive = datetime(1984, 3, 13, 19, 20)
        with self.assertRaises(BirthFoundationError) as caught:
            equation_of_time_minutes(naive)
        self.assertEqual(caught.exception.code, "true_solar_profile_unavailable")
        with self.assertRaises(BirthFoundationError):
            true_solar_adjustment_minutes(naive, 121.5637)

    def test_default_profile_explicitly_enables_both_corrections(self):
        self.assertTrue(TRUE_SOLAR_NOAA_GAMMA_V1.longitude_correction)
        self.assertTrue(TRUE_SOLAR_NOAA_GAMMA_V1.equation_of_time)


if __name__ == "__main__":
    unittest.main()
