import unittest

from engine.calendar.sexagenary import GAN, ZHI
from engine.ziwei.basis import build_star_location_index
from engine.ziwei.common import PALACE_NAMES
from engine.ziwei.composition import build_cycle_layer
from engine.ziwei.errors import ZiweiFlowingStarError
from engine.ziwei.flying import fly_transformations
from engine.ziwei.flowing_star_models import FlowingStarSource, ScopePalaceMapping
from engine.ziwei.flowing_star_view import join_dynamic_cycle, materialize_flowing_star_layer
from engine.ziwei.flowing_stars import build_flowing_star_layer
from engine.ziwei.models import ChartIdentity, CycleStemSource, LayerIdentity, LayerProvenance
from engine.ziwei.natal_models import ZiweiPalaceRecord
from engine.ziwei.transformations import get_transformation_set
from tests.ziwei_phase2a_fixtures import CHART, PROVENANCE, SYNTHETIC_STAR_RECORDS


FLOW_PROFILE = "ziwei-flowing-stars-common-v1"
RULE_VERSION = "1.0-exp"


def flow_provenance():
    return LayerProvenance(
        "project_derived",
        "Metaphysics Lab",
        None,
        FLOW_PROFILE,
        RULE_VERSION,
        "tests.test_ziwei_flowing_star_view",
    )


def flow_layer(chart=CHART, scope="yearly", reference="lunar-year:2026", stem="丙", branch="午"):
    source = FlowingStarSource(
        chart,
        scope,
        reference,
        stem,
        branch,
        "test-cycle-source-v1",
        RULE_VERSION,
        "validated",
        flow_provenance(),
    )
    return build_flowing_star_layer(source)


def natal_palaces():
    records = []
    for index, (name, branch) in enumerate(zip(PALACE_NAMES, ZHI)):
        stem = GAN[index % len(GAN)]
        records.append(ZiweiPalaceRecord(name, branch, stem, stem + branch))
    return tuple(records)


def scope_mapping(chart_id=CHART.chart_id, scope="yearly", reference="lunar-year:2026"):
    mapping = {branch: PALACE_NAMES[(index + 3) % 12] for index, branch in enumerate(ZHI)}
    return ScopePalaceMapping(chart_id, scope, reference, mapping)


def transformation_layer(scope="yearly", reference="lunar-year:2026", stem="丙", chart=CHART):
    star_locations = build_star_location_index(SYNTHETIC_STAR_RECORDS, chart, PROVENANCE)
    source = CycleStemSource("cycle_stem", chart, scope, reference, stem)
    transformations = get_transformation_set(stem)
    edges = fly_transformations(transformations, star_locations, source)
    identity = LayerIdentity(chart.chart_id, scope, reference, transformations.profile_id)
    return build_cycle_layer(identity, source, transformations, edges, PROVENANCE)


class FlowingStarViewTests(unittest.TestCase):
    def test_natal_materialization_preserves_target_branch(self):
        layer = flow_layer()
        palaces = natal_palaces()
        by_branch = {palace.branch: palace.name for palace in palaces}
        records = materialize_flowing_star_layer(layer, palaces)
        self.assertEqual(len(records), 11)
        for placement, record in zip(layer.placements, records):
            self.assertEqual(record.base_star, placement.base_star)
            self.assertEqual(record.target_branch, placement.target_branch)
            self.assertEqual(record.natal_palace, by_branch[placement.target_branch])
            self.assertIsNone(record.scope_palace)
            self.assertEqual(record.scope, layer.source.scope)
            self.assertEqual(record.source_reference, layer.source.reference)

    def test_missing_or_duplicate_natal_branch_map_fails_closed(self):
        layer = flow_layer()
        palaces = natal_palaces()
        with self.assertRaises(ZiweiFlowingStarError) as caught:
            materialize_flowing_star_layer(layer, palaces[:-1])
        self.assertEqual(caught.exception.code, "flowing_star_materialization_mismatch")

        first = palaces[0]
        second = palaces[1]
        duplicate = ZiweiPalaceRecord(second.name, first.branch, second.heavenly_stem, second.heavenly_stem + first.branch)
        malformed = (first, duplicate) + palaces[2:]
        with self.assertRaises(ZiweiFlowingStarError) as caught2:
            materialize_flowing_star_layer(layer, malformed)
        self.assertEqual(caught2.exception.code, "flowing_star_materialization_mismatch")

    def test_optional_scope_mapping_populates_scope_palace(self):
        layer = flow_layer()
        mapping = scope_mapping()
        records = materialize_flowing_star_layer(layer, natal_palaces(), mapping)
        for record in records:
            self.assertEqual(record.scope_palace, mapping.palaces[record.target_branch])

    def test_scope_mapping_identity_mismatch_fails_closed(self):
        layer = flow_layer()
        cases = (
            scope_mapping(chart_id="other-chart"),
            scope_mapping(scope="daily"),
            scope_mapping(reference="other-reference"),
        )
        for mapping in cases:
            with self.assertRaises(ZiweiFlowingStarError) as caught:
                materialize_flowing_star_layer(layer, natal_palaces(), mapping)
            self.assertEqual(caught.exception.code, "flowing_star_materialization_mismatch")
            self.assertTrue(caught.exception.details)

    def test_display_name_mapping_is_exact(self):
        suffix = {
            "天魁": "魁", "天鉞": "鉞", "文昌": "昌", "文曲": "曲",
            "祿存": "祿", "擎羊": "羊", "陀羅": "陀", "天馬": "馬",
            "紅鸞": "鸞", "天喜": "喜", "年解": "年解",
        }
        prefix = {"decadal": "運", "yearly": "流", "monthly": "月", "daily": "日", "hourly": "時"}
        pair_by_scope = {
            "decadal": ("甲", "子"),
            "yearly": ("丙", "午"),
            "monthly": ("戊", "辰"),
            "daily": ("庚", "申"),
            "hourly": ("壬", "戌"),
        }
        for scope, scope_prefix in prefix.items():
            stem, branch = pair_by_scope[scope]
            layer = flow_layer(scope=scope, reference="ref:%s" % scope, stem=stem, branch=branch)
            records = materialize_flowing_star_layer(layer, natal_palaces())
            for record in records:
                expected = "年解" if record.base_star == "年解" else scope_prefix + suffix[record.base_star]
                self.assertEqual(record.display_name, expected)

    def test_dynamic_join_allows_different_rule_profiles_for_same_cycle_key(self):
        transform = transformation_layer()
        flowing = flow_layer()
        self.assertNotEqual(transform.identity.rule_profile, flowing.identity.rule_profile)
        records = materialize_flowing_star_layer(flowing, natal_palaces())
        view = join_dynamic_cycle(transform, flowing, records)
        self.assertIs(view.transformation_layer, transform)
        self.assertIs(view.flowing_star_layer, flowing)
        self.assertEqual(view.materialized_records, records)

    def test_dynamic_join_rejects_chart_scope_or_reference_mismatch(self):
        transform = transformation_layer()
        cases = (
            flow_layer(chart=ChartIdentity("other-chart", CHART.chart_basis, CHART.source_profile)),
            flow_layer(scope="daily", reference="lunar-year:2026", stem="丙", branch="午"),
            flow_layer(reference="lunar-year:2027"),
        )
        for flowing in cases:
            with self.assertRaises(ZiweiFlowingStarError) as caught:
                join_dynamic_cycle(transform, flowing)
            self.assertEqual(caught.exception.code, "flowing_star_materialization_mismatch")
            self.assertTrue(caught.exception.details)


if __name__ == "__main__":
    unittest.main()
