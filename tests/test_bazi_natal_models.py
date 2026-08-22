import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime
from zoneinfo import ZoneInfo

from engine.bazi.natal_models import (
    BaziDecadalPeriod,
    BaziNatalChart,
    BaziNatalProfile,
    HiddenStem,
    Pillar,
    PillarDetail,
)


class BaziNatalModelTests(unittest.TestCase):
    def test_profile_contract_is_explicit_and_experimental_versioned(self):
        profile = BaziNatalProfile()
        self.assertEqual(profile.profile_id, "bazi-natal-project-v1")
        self.assertEqual(profile.rule_version, "1.0-exp")
        self.assertEqual(profile.effective_time_basis, "normalized_civil")
        self.assertEqual(profile.day_boundary, "23:00")
        self.assertEqual(profile.decadal_rule, "three-days-one-year-v1")

    def test_pillar_text_is_deterministic_and_validated(self):
        pillar = Pillar("甲", "子")
        self.assertEqual(pillar.text, "甲子")
        with self.assertRaises(ValueError):
            Pillar("X", "子")
        with self.assertRaises(ValueError):
            Pillar("甲", "X")

    def test_models_are_frozen_and_hidden_rank_is_positive(self):
        pillar = Pillar("甲", "子")
        with self.assertRaises(FrozenInstanceError):
            pillar.stem = "乙"  # type: ignore[misc]
        with self.assertRaises(ValueError):
            HiddenStem("癸", 0)

    def test_chart_allows_pending_downstream_facts_without_fake_values(self):
        dt = datetime(1984, 3, 13, 19, 20, tzinfo=ZoneInfo("Asia/Taipei"))
        pillars = (
            Pillar("甲", "子"),
            Pillar("丁", "卯"),
            Pillar("丙", "午"),
            Pillar("戊", "戌"),
        )
        chart = BaziNatalChart(
            profile=BaziNatalProfile(),
            effective_datetime=dt,
            pillars=pillars,
            day_master="丙",
            pillar_details=(),
            element_counts=None,
            decadal_direction=None,
            decadal_start=None,
            decadal_periods=(),
            validation={"status": "candidate"},
            provenance={"classification": "Project 原生盤面"},
        )
        self.assertEqual(chart.pillar_details, ())
        self.assertIsNone(chart.element_counts)
        self.assertIsNone(chart.decadal_direction)
        self.assertEqual(chart.decadal_periods, ())

    def test_chart_rejects_negative_or_incomplete_element_counts(self):
        dt = datetime(1984, 3, 13, 19, 20, tzinfo=ZoneInfo("Asia/Taipei"))
        pillars = (
            Pillar("甲", "子"),
            Pillar("丁", "卯"),
            Pillar("丙", "午"),
            Pillar("戊", "戌"),
        )
        details = tuple(
            PillarDetail(pillar, (), "比肩", ()) for pillar in pillars
        )
        period = BaziDecadalPeriod(1, Pillar("戊", "辰"), 1.0, 11.0, dt, dt)
        kwargs = dict(
            profile=BaziNatalProfile(),
            effective_datetime=dt,
            pillars=pillars,
            day_master="丙",
            pillar_details=details,
            decadal_direction="forward",
            decadal_start=dt,
            decadal_periods=(period,),
            validation={"status": "candidate"},
            provenance={"classification": "Project 原生盤面"},
        )
        with self.assertRaises(ValueError):
            BaziNatalChart(element_counts={"木": 1, "火": 1}, **kwargs)
        with self.assertRaises(ValueError):
            BaziNatalChart(
                element_counts={"木": 1, "火": 1, "土": 1, "金": 1, "水": -1},
                **kwargs,
            )


if __name__ == "__main__":
    unittest.main()
