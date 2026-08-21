import unittest

from engine.ziwei.basis import build_palace_stem_index, build_star_location_index
from engine.ziwei.composition import ZiweiCompositeView, build_cycle_layer, build_layer_stack
from engine.ziwei.errors import ZiweiPhase2AError
from engine.ziwei.flying import build_natal_flying_graph, fly_transformations
from engine.ziwei.models import (
    AvailabilityRecord,
    ChartIdentity,
    CycleStemSource,
    LayerIdentity,
    NatalContext,
    TransformationType,
    ZiweiLayerStack,
)
from engine.ziwei.transformations import get_transformation_set
from tests.ziwei_phase2a_fixtures import CHART, PROVENANCE, SYNTHETIC_PALACE_STEM_RECORDS, SYNTHETIC_STAR_RECORDS


def _base_natal(birth_year_layer=None):
    stars = build_star_location_index(SYNTHETIC_STAR_RECORDS, CHART, PROVENANCE)
    stems = build_palace_stem_index(SYNTHETIC_PALACE_STEM_RECORDS, CHART, PROVENANCE)
    return NatalContext(stars, stems, build_natal_flying_graph(stems, stars), birth_year_layer)


def _components(scope, reference, stem, natal):
    source = CycleStemSource("cycle_stem", CHART, scope, reference, stem)
    transformations = get_transformation_set(stem)
    edges = fly_transformations(transformations, natal.star_locations, source)
    identity = LayerIdentity(CHART.chart_id, scope, reference, transformations.profile_id)
    return source, transformations, edges, identity


def _components_for_chart(chart, scope, reference, stem, star_locations):
    source = CycleStemSource("cycle_stem", chart, scope, reference, stem)
    transformations = get_transformation_set(stem)
    edges = fly_transformations(transformations, star_locations, source)
    identity = LayerIdentity(chart.chart_id, scope, reference, transformations.profile_id)
    return source, transformations, edges, identity


class ZiweiCompositionModelTests(unittest.TestCase):
    def test_availability_record_is_explicit(self):
        item = AvailabilityRecord("unavailable", "fine_cycle_stem_resolver_not_enabled")
        self.assertEqual(item.status, "unavailable")


class ZiweiCompositionTests(unittest.TestCase):
    def test_fine_cycle_scope_is_rejected(self):
        natal = _base_natal()
        source, trans, edges, identity = _components("monthly", "2026-L07", "丙", natal)
        with self.assertRaises(ZiweiPhase2AError) as cm:
            build_cycle_layer(identity, source, trans, edges, PROVENANCE)
        self.assertEqual(cm.exception.code, "unsupported_scope")

    def test_cycle_layer_rejects_identity_source_scope_reference_mismatch(self):
        natal = _base_natal()
        source, trans, edges, identity = _components("yearly", "2026", "丙", natal)
        wrong_identity = LayerIdentity(
            identity.chart_id,
            "decadal",
            "43-52-virtual-age",
            identity.rule_profile,
        )
        with self.assertRaises(ZiweiPhase2AError) as cm:
            build_cycle_layer(wrong_identity, source, trans, edges, PROVENANCE)
        self.assertEqual(cm.exception.code, "layer_component_mismatch")

    def test_cycle_layer_rejects_source_transformation_stem_mismatch(self):
        natal = _base_natal()
        source, unused_trans, edges, identity = _components("yearly", "2026", "丙", natal)
        wrong_trans = get_transformation_set("丁")
        with self.assertRaises(ZiweiPhase2AError) as cm:
            build_cycle_layer(identity, source, wrong_trans, edges, PROVENANCE)
        self.assertEqual(cm.exception.code, "layer_component_mismatch")

    def test_cycle_layer_rejects_flying_edges_from_different_source(self):
        natal = _base_natal()
        source, trans, unused_edges, identity = _components("yearly", "2026", "丙", natal)
        other_source = CycleStemSource(
            "cycle_stem",
            CHART,
            "yearly",
            "2027",
            "丙",
        )
        wrong_edges = fly_transformations(trans, natal.star_locations, other_source)
        with self.assertRaises(ZiweiPhase2AError) as cm:
            build_cycle_layer(identity, source, trans, wrong_edges, PROVENANCE)
        self.assertEqual(cm.exception.code, "layer_component_mismatch")

    def test_birth_year_layer_from_different_chart_is_rejected(self):
        other = ChartIdentity("chart-other", "natal", "synthetic-v1")
        other_stars = build_star_location_index(SYNTHETIC_STAR_RECORDS, other, PROVENANCE)
        other_source, other_trans, other_edges, other_id = _components_for_chart(
            other,
            "birth_year",
            "natal",
            "乙",
            other_stars,
        )
        foreign_birth = build_cycle_layer(
            other_id,
            other_source,
            other_trans,
            other_edges,
            PROVENANCE,
        )
        natal = _base_natal(foreign_birth)
        with self.assertRaises(ZiweiPhase2AError) as cm:
            build_layer_stack(CHART, natal)
        self.assertEqual(cm.exception.code, "chart_basis_mismatch")

    def test_birth_year_slot_rejects_non_birth_year_layer(self):
        natal0 = _base_natal()
        source, trans, edges, identity = _components("yearly", "2026", "丙", natal0)
        yearly_layer = build_cycle_layer(identity, source, trans, edges, PROVENANCE)
        natal = _base_natal(yearly_layer)
        with self.assertRaises(ZiweiPhase2AError) as cm:
            build_layer_stack(CHART, natal)
        self.assertEqual(cm.exception.code, "layer_component_mismatch")

    def test_duplicate_layer_identity_is_rejected(self):
        natal = _base_natal()
        source, trans, edges, identity = _components("yearly", "2026", "丙", natal)
        layer = build_cycle_layer(identity, source, trans, edges, PROVENANCE)
        with self.assertRaises(ZiweiPhase2AError) as cm:
            build_layer_stack(CHART, natal, (layer, layer))
        self.assertEqual(cm.exception.code, "duplicate_layer_identity")

    def test_conflicting_same_identity_is_layer_conflict(self):
        natal = _base_natal()
        source_a, trans_a, edges_a, identity = _components("yearly", "2026", "丙", natal)
        layer_a = build_cycle_layer(identity, source_a, trans_a, edges_a, PROVENANCE)
        source_b, trans_b, edges_b, unused_identity = _components("yearly", "2026", "丁", natal)
        layer_b = build_cycle_layer(identity, source_b, trans_b, edges_b, PROVENANCE)
        with self.assertRaises(ZiweiPhase2AError) as cm:
            build_layer_stack(CHART, natal, (layer_a, layer_b))
        self.assertEqual(cm.exception.code, "layer_conflict")

    def test_birth_year_decadal_yearly_are_preserved_without_overwrite(self):
        natal0 = _base_natal()
        birth_source, birth_trans, birth_edges, birth_id = _components("birth_year", "natal", "乙", natal0)
        birth_layer = build_cycle_layer(birth_id, birth_source, birth_trans, birth_edges, PROVENANCE)
        natal = _base_natal(birth_layer)
        dec_source, dec_trans, dec_edges, dec_id = _components("decadal", "43-52-virtual-age", "丙", natal)
        year_source, year_trans, year_edges, year_id = _components("yearly", "2026", "丁", natal)
        dec_layer = build_cycle_layer(dec_id, dec_source, dec_trans, dec_edges, PROVENANCE)
        year_layer = build_cycle_layer(year_id, year_source, year_trans, year_edges, PROVENANCE)
        stack = build_layer_stack(CHART, natal, (dec_layer, year_layer))
        rows = ZiweiCompositeView(stack).for_transformation(TransformationType.JI)
        self.assertEqual(tuple(row.scope for row in rows), ("birth_year", "decadal", "yearly"))

    def test_fine_cycle_availability_remains_unavailable(self):
        stack = build_layer_stack(CHART, _base_natal())
        self.assertEqual(stack.availability["monthly_transformations"].status, "unavailable")
        self.assertEqual(stack.availability["monthly_transformations"].reason, "fine_cycle_stem_resolver_not_enabled")
        self.assertEqual(stack.availability["daily_transformations"].status, "unavailable")
        self.assertEqual(stack.availability["hourly_transformations"].status, "unavailable")


if __name__ == "__main__":
    unittest.main()
