import unittest
from dataclasses import replace
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from engine.birth.calendar_adapter import resolve_birth_calendar
from engine.birth.models import (
    BirthDateInput,
    BirthInput,
    BirthPlaceInput,
    BirthTimeInput,
    ResolvedBirthPlace,
    Sex,
)
from engine.birth.time_views import BirthTimeViews, TimeView, build_birth_time_views
from engine.calendar.precision import TimePrecision
from engine.ziwei.natal_profiles import ZiweiNatalProfile
from engine.ziwei.natal_time import ZiweiNatalTimeError, build_ziwei_birth_basis


TZ = ZoneInfo("Asia/Taipei")


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


def view(kind, value, boundary_effect=None):
    return TimeView(
        kind=kind,
        local_datetime=value,
        adjustment_minutes=0.0,
        profile_id="fixture",
        rule_version="1",
        calculation_basis="synthetic fixture",
        boundary_effect=boundary_effect or {
            "date_changed": False,
            "hour_branch_changed": False,
            "from_hour_branch": "戌",
            "to_hour_branch": "戌",
        },
        provenance={"timezone": "Asia/Taipei"},
    )


class ZiweiNatalTimeTests(unittest.TestCase):
    def test_taipei_true_solar_is_preserved_and_selected_as_effective_basis(self):
        calendar = resolve_birth_calendar(birth_input(), place()).context
        views = build_birth_time_views(calendar, place())
        basis = build_ziwei_birth_basis(calendar, views, ZiweiNatalProfile())

        self.assertEqual(basis.reported_datetime.strftime("%Y-%m-%d %H:%M"), "1984-03-13 19:20")
        self.assertEqual(basis.normalized_datetime.strftime("%Y-%m-%d %H:%M"), "1984-03-13 19:20")
        self.assertEqual(basis.true_solar_datetime.strftime("%Y-%m-%d %H:%M:%S"), "1984-03-13 19:16:25")
        self.assertEqual(basis.effective_datetime, basis.true_solar_datetime)
        self.assertEqual(basis.effective_hour_branch, "戌")
        self.assertEqual((basis.lunar_year, basis.lunar_month, basis.lunar_day), (1984, 2, 11))
        self.assertFalse(basis.is_leap_month)
        self.assertEqual(basis.validation["calendar_status"], "validated")
        self.assertEqual(basis.validation["time_profile_status"], "EQUIVALENT")
        self.assertEqual(basis.provenance["profile_id"], "ziwei-natal-true-solar-common-v1")
        self.assertEqual(basis.provenance["effective_time_basis"], "true_solar")

    def test_cross_hour_true_solar_is_material_without_overwriting_reported_time(self):
        calendar = resolve_birth_calendar(birth_input(19, 2), place()).context
        civil = datetime(1984, 3, 13, 19, 2, tzinfo=TZ)
        solar = datetime(1984, 3, 13, 18, 56, tzinfo=TZ)
        views = BirthTimeViews(
            reported_civil=view("reported_civil", civil),
            normalized_civil=view("normalized_civil", civil),
            true_solar=view(
                "true_solar",
                solar,
                {
                    "date_changed": False,
                    "hour_branch_changed": True,
                    "from_hour_branch": "戌",
                    "to_hour_branch": "酉",
                },
            ),
        )
        basis = build_ziwei_birth_basis(calendar, views, ZiweiNatalProfile())
        self.assertEqual(basis.reported_datetime, civil)
        self.assertEqual(basis.effective_datetime, solar)
        self.assertEqual(basis.effective_hour_branch, "酉")
        self.assertEqual(basis.validation["time_profile_status"], "CONFLICT")
        self.assertEqual(basis.validation["error_code"], "ziwei_time_profile_conflict")
        self.assertEqual(basis.validation["severity"], "BLOCKING")
        self.assertEqual(basis.validation["affected_components"], ("hour",))

    def test_true_solar_date_change_re_resolves_lunar_date_through_calendar_resolver(self):
        calendar = resolve_birth_calendar(birth_input(0, 5), place()).context
        reported = datetime(1984, 3, 13, 0, 5, tzinfo=TZ)
        corrected = datetime(1984, 3, 12, 23, 55, tzinfo=TZ)
        views = BirthTimeViews(
            reported_civil=view("reported_civil", reported),
            normalized_civil=view("normalized_civil", reported),
            true_solar=view(
                "true_solar",
                corrected,
                {
                    "date_changed": True,
                    "hour_branch_changed": False,
                    "from_hour_branch": "子",
                    "to_hour_branch": "子",
                },
            ),
        )
        basis = build_ziwei_birth_basis(calendar, views, ZiweiNatalProfile())
        self.assertEqual(basis.effective_datetime, corrected)
        self.assertEqual((basis.lunar_year, basis.lunar_month, basis.lunar_day), (1984, 2, 10))
        self.assertTrue(basis.validation["effective_calendar_re_resolved"])
        self.assertEqual(basis.validation["affected_components"], ("date",))

    def test_calendar_boundary_conflict_fails_closed(self):
        calendar = resolve_birth_calendar(birth_input(), place()).context
        conflict_validation = replace(calendar.validation, overall_status="boundary_conflict")
        conflict_calendar = replace(calendar, validation=conflict_validation)
        views = build_birth_time_views(calendar, place())
        with self.assertRaises(ZiweiNatalTimeError) as caught:
            build_ziwei_birth_basis(conflict_calendar, views, ZiweiNatalProfile())
        self.assertEqual(caught.exception.code, "calendar_boundary_conflict")

    def test_out_of_validated_range_is_explicit_unqualified_candidate(self):
        calendar = resolve_birth_calendar(birth_input(), place()).context
        out_validation = replace(calendar.validation, overall_status="out_of_validated_range")
        out_calendar = replace(calendar, validation=out_validation)
        views = build_birth_time_views(calendar, place())
        basis = build_ziwei_birth_basis(out_calendar, views, ZiweiNatalProfile())
        self.assertEqual(basis.validation["calendar_status"], "out_of_validated_range")
        self.assertEqual(basis.validation["qualification_status"], "unqualified_candidate")

    def test_non_true_solar_profile_fails_closed(self):
        calendar = resolve_birth_calendar(birth_input(), place()).context
        views = build_birth_time_views(calendar, place())
        profile = replace(ZiweiNatalProfile(), time_basis="normalized_civil")
        with self.assertRaises(ZiweiNatalTimeError) as caught:
            build_ziwei_birth_basis(calendar, views, profile)
        self.assertEqual(caught.exception.code, "unsupported_ziwei_time_basis")


if __name__ == "__main__":
    unittest.main()
