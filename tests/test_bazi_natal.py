import unittest
from dataclasses import replace

from engine.bazi.calendar import bazi_pillars, ten_god
from engine.bazi.natal import BaziNatalError, build_bazi_natal, hidden_stems
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

    def test_all_twelve_hidden_stem_tables_are_exact_and_ordered(self):
        expected = {
            "子": ("癸",),
            "丑": ("己", "癸", "辛"),
            "寅": ("甲", "丙", "戊"),
            "卯": ("乙",),
            "辰": ("戊", "乙", "癸"),
            "巳": ("丙", "戊", "庚"),
            "午": ("丁", "己"),
            "未": ("己", "丁", "乙"),
            "申": ("庚", "壬", "戊"),
            "酉": ("辛",),
            "戌": ("戊", "辛", "丁"),
            "亥": ("壬", "甲"),
        }
        self.assertEqual({branch: hidden_stems(branch) for branch in expected}, expected)

    def test_pillar_details_ten_gods_and_visible_element_counts_are_raw_facts(self):
        context, views = context_and_views("1984-03-13T19:20:00")
        chart = build_bazi_natal(context, views, Sex.MALE)
        self.assertEqual(len(chart.pillar_details), 4)
        for detail in chart.pillar_details:
            self.assertEqual(detail.stem_ten_god, ten_god(chart.day_master, detail.pillar.stem))
            self.assertEqual(
                tuple(hidden.stem for hidden in detail.hidden_stems),
                hidden_stems(detail.pillar.branch),
            )
            self.assertEqual(
                detail.hidden_ten_gods,
                tuple(ten_god(chart.day_master, hidden.stem) for hidden in detail.hidden_stems),
            )
            self.assertEqual(
                tuple(hidden.weight_rank for hidden in detail.hidden_stems),
                tuple(range(1, len(detail.hidden_stems) + 1)),
            )
        self.assertEqual(set(chart.element_counts), {"木", "火", "土", "金", "水"})
        self.assertEqual(sum(chart.element_counts.values()), 8)
        self.assertEqual(chart.provenance["element_count_basis"], "visible_stems_plus_branch_primary_elements")
        self.assertNotIn("strength", chart.provenance)

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
