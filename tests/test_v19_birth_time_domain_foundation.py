import unittest
from datetime import date, time, timedelta
from zoneinfo import ZoneInfo

from engine.birth.calendar_adapter import resolve_birth_calendar
from engine.birth.input_resolution import resolve_birth_input
from engine.birth.models import (
    BirthDateInput,
    BirthInput,
    BirthPlaceInput,
    BirthTimeInput,
    ResolvedBirthPlace,
    Sex,
)
from engine.birth.time_views import TRUE_SOLAR_NOAA_GAMMA_V1, build_birth_time_views
from engine.calendar.models import CalendarResolverException
from engine.calendar.precision import TimePrecision
from engine.calendar.timezone import enumerate_local_time_occurrences
from engine.distribution.runtime import dispatch


class _SystemZoneProviderForTest:
    def zone(self, timezone_name):
        try:
            return ZoneInfo(timezone_name)
        except Exception as exc:
            raise CalendarResolverException(
                "invalid_timezone",
                "unknown IANA timezone: %r" % timezone_name,
                {"timezone": timezone_name},
            ) from exc


TEST_PROVIDER = _SystemZoneProviderForTest()


def _new_york_place():
    return ResolvedBirthPlace(
        canonical_name="New York City, USA",
        latitude=40.7128,
        longitude=-74.0060,
        timezone="America/New_York",
        provider_name="fixture",
        provider_version="1",
        resolution_status="resolved",
        provider_reference="fixture:nyc",
    )


def _birth_input(year, month, day, hour, minute):
    return BirthInput(
        sex=Sex.MALE,
        birth_date=BirthDateInput(date(year, month, day), TimePrecision.DAY),
        birth_time=BirthTimeInput(
            time(hour, minute),
            None,
            TimePrecision.HOUR,
            "%02d:%02d" % (hour, minute),
        ),
        birth_place=BirthPlaceInput("New York City"),
    )


class V19BirthTimeDomainFoundationTests(unittest.TestCase):
    def test_unknown_time_is_explicit_supported_precision_state(self):
        result = resolve_birth_input(
            {
                "sex": "male",
                "birth_date": "1984-03-13",
                "birth_place": "台北市",
                "birth_time_precision": "unknown_time",
            },
            target="ziwei_natal",
        )
        self.assertTrue(result.ok, result.to_dict())
        self.assertEqual(result.birth_time_precision, "unknown_time")
        self.assertIsNone(result.input.birth_time)
        self.assertEqual(result.to_dict()["birth_time_precision"], "unknown_time")
        self.assertIsNone(result.to_dict()["input"]["birth_time"])

    def test_missing_time_without_explicit_unknown_state_still_fails_closed(self):
        result = resolve_birth_input(
            {
                "sex": "male",
                "birth_date": "1984-03-13",
                "birth_place": "台北市",
            },
            target="ziwei_natal",
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, "missing_required_birth_field")
        self.assertEqual(result.missing_fields, ("birth_time_precision",))

    def test_bounded_time_is_supported_without_midpoint_collapse(self):
        result = resolve_birth_input(
            {
                "sex": "female",
                "birth_date": "1990-05-06",
                "birth_place": "高雄市",
                "birth_time_precision": "bounded",
                "birth_time_range": ["20:00", "22:00"],
            },
            target="ziwei_natal",
        )
        self.assertTrue(result.ok, result.to_dict())
        self.assertEqual(result.birth_time_precision, "bounded")
        self.assertEqual(result.input.birth_time.start.strftime("%H:%M"), "20:00")
        self.assertEqual(result.input.birth_time.end.strftime("%H:%M"), "22:00")
        self.assertFalse(result.input.birth_time.is_exact)

    def test_precision_state_must_match_supplied_time_fields(self):
        result = resolve_birth_input(
            {
                "sex": "male",
                "birth_date": "1984-03-13",
                "birth_place": "台北市",
                "birth_time_precision": "unknown_time",
                "birth_time": "19:20",
            },
            target="ziwei_natal",
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, "invalid_birth_time_precision_state")

    def test_full_build_does_not_treat_unknown_time_as_exact(self):
        result = dispatch(
            "build_natal",
            {
                "birth": {
                    "sex": "male",
                    "birth_date": "1984-03-13",
                    "birth_place": "台北市",
                    "birth_time_precision": "unknown_time",
                }
            },
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "ambiguous_birth_time")
        self.assertEqual(result["error"]["details"]["birth_time_precision"], "unknown_time")

    def test_public_location_resolution_is_time_independent(self):
        result = dispatch("birth.resolve_location", {"birth_place": "台北市"})
        self.assertTrue(result["ok"], result)
        location = result["data"]["resolved_location"]
        self.assertEqual(location["canonical_name"], "Taipei City")
        self.assertEqual(location["timezone"], "Asia/Taipei")
        self.assertEqual(location["provider_name"], "metaphysics_lab_offline_registry")

    def test_runtime_info_advertises_public_location_resolution(self):
        result = dispatch("runtime_info", {})
        self.assertTrue(result["ok"], result)
        self.assertIn("birth.resolve_location", result["data"]["supported_actions"])

    def test_fall_back_label_enumerates_two_legal_occurrences(self):
        occurrences = enumerate_local_time_occurrences(
            "2026-11-01T01:30:00",
            "America/New_York",
            provider=TEST_PROVIDER,
        )
        self.assertEqual(len(occurrences), 2)
        self.assertEqual([item.utc_offset for item in occurrences], ["-04:00", "-05:00"])
        self.assertEqual([item.fold for item in occurrences], [0, 1])
        self.assertEqual(
            [item.utc_datetime.isoformat() for item in occurrences],
            ["2026-11-01T05:30:00+00:00", "2026-11-01T06:30:00+00:00"],
        )

    def test_spring_gap_has_zero_legal_occurrences(self):
        occurrences = enumerate_local_time_occurrences(
            "2026-03-08T02:30:00",
            "America/New_York",
            provider=TEST_PROVIDER,
        )
        self.assertEqual(occurrences, ())

    def test_lord_howe_half_hour_fold_is_not_assumed_to_be_one_hour(self):
        occurrences = enumerate_local_time_occurrences(
            "2026-04-05T01:45:00",
            "Australia/Lord_Howe",
            provider=TEST_PROVIDER,
        )
        self.assertEqual(len(occurrences), 2)
        offsets = [item.local_datetime.utcoffset() for item in occurrences]
        self.assertEqual(offsets[0] - offsets[1], timedelta(minutes=30))

    def test_calendar_adapter_can_materialize_a_selected_fold_occurrence(self):
        resolution = resolve_birth_calendar(
            _birth_input(2026, 11, 1, 1, 30),
            _new_york_place(),
            utc_offset_hint="-05:00",
        )
        self.assertTrue(resolution.ok, resolution.error)
        self.assertEqual(resolution.context.normalized_time.utc_offset, "-05:00")
        self.assertEqual(resolution.context.normalized_time.local_datetime.fold, 1)

    def test_true_solar_adjustment_preserves_second_fold_occurrence_identity(self):
        resolution = resolve_birth_calendar(
            _birth_input(2026, 11, 1, 1, 30),
            _new_york_place(),
            utc_offset_hint="-05:00",
        )
        self.assertTrue(resolution.ok, resolution.error)
        views = build_birth_time_views(resolution.context, _new_york_place())
        self.assertEqual(TRUE_SOLAR_NOAA_GAMMA_V1.rule_version, "1.1-exp")
        self.assertEqual(views.normalized_civil.local_datetime.utcoffset(), timedelta(hours=-5))
        self.assertEqual(views.normalized_civil.local_datetime.fold, 1)
        self.assertEqual(views.true_solar.local_datetime.utcoffset(), timedelta(hours=-5))
        self.assertEqual(views.true_solar.local_datetime.fold, 1)
        self.assertEqual(views.true_solar.local_datetime.strftime("%Y-%m-%d %H:%M"), "2026-11-01 01:50")


if __name__ == "__main__":
    unittest.main()
