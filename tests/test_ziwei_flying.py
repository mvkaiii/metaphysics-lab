import unittest

from engine.ziwei.basis import build_palace_stem_index, build_star_location_index
from engine.ziwei.common import PALACE_NAMES, opposite_palace
from engine.ziwei.errors import ZiweiPhase2AError
from engine.ziwei.flying import classify_geometric_relation, fly_transformations
from engine.ziwei.models import ChartIdentity, CycleStemSource, GeometricRelation, PalaceStemSource
from engine.ziwei.transformations import get_transformation_set
from tests.ziwei_phase2a_fixtures import CHART, PROVENANCE, SYNTHETIC_PALACE_STEM_RECORDS, SYNTHETIC_STAR_RECORDS


class ZiweiFlyingTests(unittest.TestCase):
    def test_all_144_palace_pairs_classify_exactly(self):
        counts = {item: 0 for item in GeometricRelation}
        for source_palace in PALACE_NAMES:
            source = PalaceStemSource("palace_stem", CHART, source_palace, "甲")
            for target in PALACE_NAMES:
                counts[classify_geometric_relation(source, target)] += 1
        self.assertEqual(counts[GeometricRelation.SAME_PALACE], 12)
        self.assertEqual(counts[GeometricRelation.OPPOSITE_PALACE_INCOMING], 12)
        self.assertEqual(counts[GeometricRelation.NORMAL], 120)

    def test_opposite_palace_is_symmetric(self):
        for palace in PALACE_NAMES:
            self.assertEqual(opposite_palace(opposite_palace(palace)), palace)

    def test_cycle_source_never_has_self_relation(self):
        source = CycleStemSource("cycle_stem", CHART, "yearly", "2026", "丙")
        self.assertIsNone(classify_geometric_relation(source, "田宅宮"))

    def test_cycle_transformation_set_creates_exactly_four_edges(self):
        stars = build_star_location_index(SYNTHETIC_STAR_RECORDS, CHART, PROVENANCE)
        source = CycleStemSource("cycle_stem", CHART, "yearly", "2026", "丙")
        edges = fly_transformations(get_transformation_set("丙"), stars, source)
        self.assertEqual(len(edges), 4)
        self.assertTrue(all(edge.target_basis == "natal_star_location" for edge in edges))
        self.assertTrue(all(edge.geometric_relation is None for edge in edges))

    def test_missing_star_location_fails_closed(self):
        stars = build_star_location_index(SYNTHETIC_STAR_RECORDS[:1], CHART, PROVENANCE)
        source = CycleStemSource("cycle_stem", CHART, "yearly", "2026", "丙")
        with self.assertRaises(ZiweiPhase2AError) as cm:
            fly_transformations(get_transformation_set("丙"), stars, source)
        self.assertEqual(cm.exception.code, "missing_star_location")

    def test_chart_basis_mismatch_fails_closed(self):
        stars = build_star_location_index(SYNTHETIC_STAR_RECORDS, CHART, PROVENANCE)
        other = ChartIdentity("chart-other", "natal", "synthetic-v1")
        source = CycleStemSource("cycle_stem", other, "yearly", "2026", "丙")
        with self.assertRaises(ZiweiPhase2AError) as cm:
            fly_transformations(get_transformation_set("丙"), stars, source)
        self.assertEqual(cm.exception.code, "chart_basis_mismatch")


if __name__ == "__main__":
    unittest.main()
