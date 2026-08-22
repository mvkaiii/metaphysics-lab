import unittest
from dataclasses import replace

from engine.bazi.calendar import bazi_pillars
from engine.bazi.natal import BaziNatalError, build_bazi_natal
from engine.bazi.natal_models import BaziNatalProfile
from engine.birth.models import ResolvedBirthPlace, Sex
from engine.birth.time_views import build_birth_time_views
from engine.calendar import resolve_calendar


TAIPEI = ResolvedBirthPlace(
    canonical_name="Taipei, Taiwan",
    latitude=25.0375,
    longitude=121.5637,
    timezone="Asia/Taipei",
    provider_name="fixture",
    provider_version="1",
    resolution_status="resolved",
    provider_reference="fixture:taipei",
)


def context_and_views(value):
    resolution = resolve_calendar(value, "Asia/Taipei")
    if not resolution.ok or resolution.context is None:
        raise AssertionError("calendar fixture failed: %s" % value)
    context = resolution.context
    return context, build_birth_time_views(context, TAIPEI)


class BaziNatalBuilderTests(unittest.TestCase):
    def test_locked_four_pillar_vectors_match_existing_bazi_engine(self):
        for value in (
            "1984-03-13T19:20:00",
            "2026-08-20T17:12:00",
            "2026-08-20T23:30:00",
        ):
            context, views = context_and_views(value)
            chart = build_bazi_natal(context, views, Sex.MALE)
            expected = bazi_pillars(context.normalized_time.local_datetime)
            self.assertEqual(tuple(pillar.text for pillar in chart.pillars), expected)
            self.assertEqual(chart.day_master, chart.pillars[2].stem)
            self.assertEqual(chart.effective_datetime, views.normalized_civil.local_datetime)
            self.assertEqual(chart.provenance["classification"], "Project 原生盤面")

    def test_unsupported_time_profile_fails_closed(self):
        context, views = context_and_views("1984-03-13T19:20:00")
        profile = replace(BaziNatalProfile(), effective_time_basis="true_solar")
        with self.assertRaises(BaziNatalError) as caught:
            build_bazi_natal(context, views, Sex.MALE, profile)
        self.assertEqual(caught.exception.code, "unsupported_bazi_time_profile")

    def test_calendar_boundary_conflict_blocks_natal_materialization(self):
        context, views = context_and_views("1984-03-13T19:20:00")
        conflict_validation = replace(context.validation, overall_status="boundary_conflict")
        conflict_context = replace(context, validation=conflict_validation)
        with self.assertRaises(BaziNatalError) as caught:
            build_bazi_natal(conflict_context, views, Sex.MALE)
        self.assertEqual(caught.exception.code, "calendar_boundary_conflict")

    def test_out_of_validated_range_is_materialized_only_as_unqualified_candidate(self):
        context, views = context_and_views("1984-03-13T19:20:00")
        unqualified_validation = replace(
            context.validation,
            overall_status="out_of_validated_range",
        )
        unqualified_context = replace(context, validation=unqualified_validation)
        chart = build_bazi_natal(unqualified_context, views, Sex.FEMALE)
        self.assertEqual(chart.validation["status"], "unqualified_candidate")
        self.assertEqual(chart.validation["calendar_status"], "out_of_validated_range")


if __name__ == "__main__":
    unittest.main()
