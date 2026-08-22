import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from engine.bazi.natal import compare_bazi_time_views
from engine.birth.models import ResolvedBirthPlace
from engine.birth.time_views import BirthTimeViews, TimeView, build_birth_time_views
from engine.calendar import resolve_calendar


TAIPEI = ZoneInfo("Asia/Taipei")
TAIPEI_PLACE = ResolvedBirthPlace(
    canonical_name="Taipei, Taiwan",
    latitude=25.0375,
    longitude=121.5637,
    timezone="Asia/Taipei",
    provider_name="fixture",
    provider_version="1",
    resolution_status="resolved",
    provider_reference="fixture:taipei",
)


def _view(kind, dt):
    return TimeView(
        kind=kind,
        local_datetime=dt,
        adjustment_minutes=0.0,
        profile_id="fixture",
        rule_version="1",
        calculation_basis="fixture",
        boundary_effect={},
        provenance={},
    )


def _views(civil, solar):
    return BirthTimeViews(
        reported_civil=_view("reported_civil", civil),
        normalized_civil=_view("normalized_civil", civil),
        true_solar=_view("true_solar", solar),
    )


class BaziTimeProfileComparisonTests(unittest.TestCase):
    def test_taipei_1984_is_equivalent(self):
        resolution = resolve_calendar("1984-03-13T19:20:00", "Asia/Taipei")
        self.assertTrue(resolution.ok)
        self.assertIsNotNone(resolution.context)
        comparison = compare_bazi_time_views(
            build_birth_time_views(resolution.context, TAIPEI_PLACE)
        )
        self.assertEqual(comparison.status, "EQUIVALENT")
        self.assertEqual(comparison.affected_components, ())
        self.assertEqual(comparison.severity, "INFO")
        self.assertIsNone(comparison.error_code)
        self.assertEqual(comparison.default_pillars, comparison.true_solar_pillars)

    def test_hour_only_material_conflict_is_blocking(self):
        comparison = compare_bazi_time_views(
            _views(
                datetime(1984, 3, 13, 19, 2, tzinfo=TAIPEI),
                datetime(1984, 3, 13, 18, 56, tzinfo=TAIPEI),
            )
        )
        self.assertEqual(comparison.status, "CONFLICT")
        self.assertEqual(comparison.error_code, "bazi_time_profile_conflict")
        self.assertEqual(comparison.severity, "BLOCKING")
        self.assertEqual(comparison.affected_components, ("hour",))

    def test_23_boundary_lists_day_and_hour_components(self):
        comparison = compare_bazi_time_views(
            _views(
                datetime(2026, 8, 20, 22, 58, tzinfo=TAIPEI),
                datetime(2026, 8, 20, 23, 2, tzinfo=TAIPEI),
            )
        )
        self.assertEqual(comparison.status, "CONFLICT")
        self.assertEqual(comparison.severity, "BLOCKING")
        self.assertEqual(comparison.error_code, "bazi_time_profile_conflict")
        self.assertIn("day", comparison.affected_components)
        self.assertIn("hour", comparison.affected_components)


if __name__ == "__main__":
    unittest.main()
