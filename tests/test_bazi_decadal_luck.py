import unittest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from engine.bazi.calendar import GAN, STEM_INFO, solar_term_time
from engine.bazi.natal import (
    build_bazi_natal,
    build_decadal_periods,
    decadal_direction,
    decadal_start_delta,
)
from engine.bazi.natal_models import Pillar
from engine.birth.models import ResolvedBirthPlace, Sex
from engine.birth.time_views import build_birth_time_views
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


def _sexagenary_cycle():
    return tuple(GAN[index % 10] + "子丑寅卯辰巳午未申酉戌亥"[index % 12] for index in range(60))


class BaziDecadalLuckTests(unittest.TestCase):
    def test_all_ten_stems_by_both_sexes_follow_direction_matrix(self):
        for stem in GAN:
            is_yang = STEM_INFO[stem][1]
            self.assertEqual(
                decadal_direction(stem, Sex.MALE),
                "forward" if is_yang else "reverse",
            )
            self.assertEqual(
                decadal_direction(stem, Sex.FEMALE),
                "reverse" if is_yang else "forward",
            )

    def test_forward_start_delta_uses_next_jie_with_three_days_one_year(self):
        birth = datetime(1984, 3, 13, 19, 20, tzinfo=TAIPEI)
        next_jie = solar_term_time(1984, "清明", TAIPEI)
        interval = next_jie - birth
        expected_age_years = interval.total_seconds() / (3 * 86400.0)
        expected_delta = timedelta(days=expected_age_years * 365.2425)
        actual = decadal_start_delta(birth, "forward")
        self.assertAlmostEqual(actual.total_seconds(), expected_delta.total_seconds(), places=6)

    def test_reverse_start_delta_uses_previous_jie_with_three_days_one_year(self):
        birth = datetime(1984, 3, 13, 19, 20, tzinfo=TAIPEI)
        previous_jie = solar_term_time(1984, "驚蟄", TAIPEI)
        interval = birth - previous_jie
        expected_age_years = interval.total_seconds() / (3 * 86400.0)
        expected_delta = timedelta(days=expected_age_years * 365.2425)
        actual = decadal_start_delta(birth, "reverse")
        self.assertAlmostEqual(actual.total_seconds(), expected_delta.total_seconds(), places=6)

    def test_invalid_direction_is_rejected(self):
        birth = datetime(1984, 3, 13, 19, 20, tzinfo=TAIPEI)
        with self.assertRaises(ValueError):
            decadal_start_delta(birth, "sideways")

    def test_month_pillar_sequence_moves_one_sexagenary_step_and_has_ten_periods(self):
        birth = datetime(1984, 3, 13, 19, 20, tzinfo=TAIPEI)
        month = Pillar("丁", "卯")
        cycle = _sexagenary_cycle()
        month_index = cycle.index(month.text)

        forward = build_decadal_periods(month, birth, "forward")
        reverse = build_decadal_periods(month, birth, "reverse")

        self.assertEqual(len(forward), 10)
        self.assertEqual(len(reverse), 10)
        self.assertEqual(
            tuple(period.pillar.text for period in forward),
            tuple(cycle[(month_index + step) % 60] for step in range(1, 11)),
        )
        self.assertEqual(
            tuple(period.pillar.text for period in reverse),
            tuple(cycle[(month_index - step) % 60] for step in range(1, 11)),
        )
        for periods in (forward, reverse):
            for index, period in enumerate(periods, start=1):
                self.assertEqual(period.index, index)
                self.assertAlmostEqual(period.end_age_years - period.start_age_years, 10.0, places=9)

    def test_natal_builder_materializes_direction_start_and_auditable_interval(self):
        resolution = resolve_calendar("1984-03-13T19:20:00", "Asia/Taipei")
        self.assertTrue(resolution.ok)
        self.assertIsNotNone(resolution.context)
        views = build_birth_time_views(resolution.context, TAIPEI_PLACE)
        chart = build_bazi_natal(resolution.context, views, Sex.MALE)

        self.assertIn(chart.decadal_direction, ("forward", "reverse"))
        self.assertIsNotNone(chart.decadal_start)
        self.assertEqual(len(chart.decadal_periods), 10)
        self.assertEqual(chart.decadal_periods[0].start_datetime, chart.decadal_start)
        self.assertEqual(chart.provenance["decadal_profile"], "three-days-one-year-v1")
        self.assertGreater(chart.provenance["decadal_jie_interval_seconds"], 0)
        self.assertGreater(chart.provenance["decadal_start_age_years"], 0)
        self.assertEqual(chart.provenance["pending_sections"], ())


if __name__ == "__main__":
    unittest.main()
