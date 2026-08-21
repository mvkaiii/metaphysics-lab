import unittest
from dataclasses import replace
from unittest.mock import patch

from engine.ziwei.basis import build_star_location_index
from engine.ziwei.errors import ZiweiFineCycleError, ZiweiPhase2AError
from engine.ziwei.fine_cycle import build_fine_cycle_layer
from engine.ziwei.fine_cycle_stems import (
    resolve_day_stem,
    resolve_hour_stem,
    resolve_month_stem,
)
from engine.ziwei.models import ChartIdentity
from engine.ziwei.transformations import get_transformation_set as real_get_transformation_set
from tests.ziwei_phase2b_fixtures import (
    CHART,
    PROVENANCE,
    SYNTHETIC_STAR_RECORDS,
    calendar_context,
)


def _stars(chart=CHART):
    return build_star_location_index(SYNTHETIC_STAR_RECORDS, chart, PROVENANCE)


class FineCycleTransformationIntegrationTests(unittest.TestCase):
    def test_each_fine_scope_builds_exactly_four_transformations_and_edges(self):
        for resolution in (
            resolve_month_stem(calendar_context(lunar_year=2023, lunar_month=6, lunar_day=13)),
            resolve_day_stem(calendar_context()),
            resolve_hour_stem(calendar_context()),
        ):
            layer = build_fine_cycle_layer(resolution, CHART, _stars())
            self.assertEqual(layer.identity.scope, resolution.scope)
            self.assertEqual(layer.identity.reference, resolution.reference)
            self.assertEqual(layer.heavenly_stem, resolution.heavenly_stem)
            self.assertEqual(layer.earthly_branch, resolution.earthly_branch)
            self.assertEqual(len(layer.transformations.transformations), 4)
            self.assertEqual(len(layer.flying_edges), 4)

    def test_chart_mismatch_uses_existing_phase2a_contract(self):
        other = ChartIdentity("other", "natal", "synthetic-v1")
        with self.assertRaises(ZiweiPhase2AError) as cm:
            build_fine_cycle_layer(resolve_day_stem(calendar_context()), CHART, _stars(other))
        self.assertEqual(cm.exception.code, "chart_basis_mismatch")

    def test_non_fine_scope_is_rejected_before_downstream_calls(self):
        resolution = replace(resolve_day_stem(calendar_context()), scope="weekly")
        with self.assertRaises(ZiweiFineCycleError) as cm:
            build_fine_cycle_layer(resolution, CHART, _stars())
        self.assertEqual(cm.exception.code, "invalid_fine_cycle_scope")

    def test_reference_scope_mismatch_is_rejected(self):
        resolution = replace(
            resolve_day_stem(calendar_context()),
            reference="lunar:2023-06",
        )
        with self.assertRaises(ZiweiFineCycleError) as cm:
            build_fine_cycle_layer(resolution, CHART, _stars())
        self.assertEqual(cm.exception.code, "fine_cycle_reference_conflict")

    def test_hour_branch_and_reference_must_match_resolution(self):
        resolution = replace(
            resolve_hour_stem(calendar_context()),
            hour_branch="子",
        )
        with self.assertRaises(ZiweiFineCycleError) as cm:
            build_fine_cycle_layer(resolution, CHART, _stars())
        self.assertEqual(cm.exception.code, "fine_cycle_reference_conflict")

    def test_downstream_transformation_stem_mismatch_is_rejected(self):
        resolution = resolve_month_stem(calendar_context(lunar_year=2023, lunar_month=6, lunar_day=13))
        wrong = real_get_transformation_set("丁")
        with patch("engine.ziwei.fine_cycle.get_transformation_set", return_value=wrong):
            with self.assertRaises(ZiweiFineCycleError) as cm:
                build_fine_cycle_layer(resolution, CHART, _stars())
        self.assertEqual(cm.exception.code, "fine_cycle_stem_mismatch")

    def test_unknown_fine_cycle_profile_is_rejected(self):
        resolution = replace(resolve_day_stem(calendar_context()), profile_id="unknown")
        with self.assertRaises(ZiweiFineCycleError) as cm:
            build_fine_cycle_layer(resolution, CHART, _stars())
        self.assertEqual(cm.exception.code, "invalid_fine_cycle_profile")


if __name__ == "__main__":
    unittest.main()
