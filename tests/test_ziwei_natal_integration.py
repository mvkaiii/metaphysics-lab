import unittest
from datetime import datetime
from types import MappingProxyType
from unittest.mock import patch
from zoneinfo import ZoneInfo

from engine.birth.models import Sex
from engine.ziwei.errors import ZiweiPhase2AError
from engine.ziwei.models import ChartIdentity, StarLocationIndex
from engine.ziwei.natal import build_ziwei_natal
from engine.ziwei.natal_time import ZiweiBirthBasis
from engine.ziwei.star_catalog import MAJOR_STARS
from engine.ziwei.transformation_profiles import PROFILE


class ZiweiNatalIntegrationTests(unittest.TestCase):
    def _basis(self):
        tz = ZoneInfo("Asia/Taipei")
        return ZiweiBirthBasis(
            reported_datetime=datetime(1984, 3, 13, 19, 20, tzinfo=tz),
            normalized_datetime=datetime(1984, 3, 13, 19, 20, tzinfo=tz),
            true_solar_datetime=datetime(1984, 3, 13, 19, 16, 25, tzinfo=tz),
            effective_datetime=datetime(1984, 3, 13, 19, 16, 25, tzinfo=tz),
            effective_hour_branch="戌",
            lunar_year=1984,
            lunar_month=2,
            lunar_day=11,
            is_leap_month=False,
            validation={
                "calendar_status": "validated",
                "qualification_status": "qualified_candidate",
                "time_profile_status": "EQUIVALENT",
                "severity": "INFO",
                "affected_components": (),
            },
            provenance={
                "classification": "Project 原生盤面",
                "profile_id": "ziwei-natal-true-solar-common-v1",
                "rule_version": "1.0-exp",
                "effective_time_basis": "true_solar",
            },
        )

    def test_end_to_end_builder_materializes_complete_v1_core(self):
        chart = build_ziwei_natal(self._basis(), Sex.MALE)
        self.assertEqual(len(chart.palaces), 12)
        self.assertEqual(len(chart.decadal_periods), 12)
        self.assertEqual(chart.classification, "Project 原生盤面")
        self.assertEqual(chart.maturity, "experimental")
        self.assertIsNotNone(chart.chart_identity)
        self.assertEqual(chart.chart_identity.chart_basis, "project_native_ziwei_natal")

        major = tuple(record.star for record in chart.stars if record.star in MAJOR_STARS)
        self.assertEqual(major, MAJOR_STARS)
        self.assertEqual(len(set(major)), 14)

        required = {star for stars in PROFILE.values() for star in stars}
        self.assertTrue(required.issubset({record.star for record in chart.stars}))
        self.assertEqual(len(chart.birth_transformations.transformations), 4)
        self.assertEqual(chart.birth_transformations.heavenly_stem, "甲")
        self.assertEqual(len(chart.natal_flying_graph.edges), 48)
        self.assertEqual(chart.natal_flying_graph.chart_identity, chart.chart_identity)
        self.assertIsNotNone(chart.life_master)
        self.assertIsNotNone(chart.body_master)
        self.assertIsNotNone(chart.five_element_bureau)
        self.assertEqual(chart.ming_palace, "命宮")
        self.assertIn(chart.body_palace, {record.name for record in chart.palaces})

    def test_builder_applies_versioned_brightness_without_guessing_undefined_rows(self):
        chart = build_ziwei_natal(self._basis(), Sex.MALE)
        by_star = {record.star: record for record in chart.stars}
        self.assertIsNotNone(by_star["紫微"].brightness)
        self.assertIsNotNone(by_star["文昌"].brightness)
        self.assertIsNone(by_star["左輔"].brightness)
        self.assertIsNone(by_star["天魁"].brightness)

    def test_same_input_is_deterministic_including_chart_identity(self):
        first = build_ziwei_natal(self._basis(), Sex.MALE)
        second = build_ziwei_natal(self._basis(), Sex.MALE)
        self.assertEqual(first, second)
        self.assertEqual(first.chart_identity, second.chart_identity)

    def test_chart_identity_mismatch_from_phase2a_adapter_fails_closed(self):
        original = __import__("engine.ziwei.natal", fromlist=["build_star_location_index"]).build_star_location_index

        def wrong_identity(records, chart_identity, provenance):
            index = original(records, chart_identity, provenance)
            return StarLocationIndex(
                ChartIdentity("wrong-chart", chart_identity.chart_basis, chart_identity.source_profile),
                MappingProxyType(dict(index.locations)),
                index.validation_status,
                index.provenance,
            )

        with patch("engine.ziwei.natal.build_star_location_index", side_effect=wrong_identity):
            with self.assertRaises(ZiweiPhase2AError) as caught:
                build_ziwei_natal(self._basis(), Sex.MALE)
        self.assertEqual(caught.exception.code, "chart_basis_mismatch")

    def test_invalid_sex_and_unqualified_calendar_fail_closed(self):
        with self.assertRaises(ValueError):
            build_ziwei_natal(self._basis(), "male")

        basis = self._basis()
        invalid = ZiweiBirthBasis(
            reported_datetime=basis.reported_datetime,
            normalized_datetime=basis.normalized_datetime,
            true_solar_datetime=basis.true_solar_datetime,
            effective_datetime=basis.effective_datetime,
            effective_hour_branch=basis.effective_hour_branch,
            lunar_year=basis.lunar_year,
            lunar_month=basis.lunar_month,
            lunar_day=basis.lunar_day,
            is_leap_month=basis.is_leap_month,
            validation={"calendar_status": "boundary_conflict"},
            provenance=basis.provenance,
        )
        with self.assertRaises(ValueError):
            build_ziwei_natal(invalid, Sex.MALE)


if __name__ == "__main__":
    unittest.main()
