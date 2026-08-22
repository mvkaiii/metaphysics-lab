import unittest
from dataclasses import FrozenInstanceError

from engine.ziwei.errors import ZiweiFlowingStarError
from engine.ziwei.flowing_star_models import (
    FlowingStarLayer,
    FlowingStarPlacement,
    FlowingStarProfile,
    FlowingStarSource,
    ScopePalaceMapping,
)
from engine.ziwei.models import ChartIdentity, LayerIdentity, LayerProvenance


PROFILE_ID = "ziwei-flowing-stars-common-v1"
RULE_VERSION = "1.0-exp"


def provenance():
    return LayerProvenance(
        "project_derived",
        "Metaphysics Lab",
        None,
        PROFILE_ID,
        RULE_VERSION,
        "tests.test_ziwei_flowing_star_models",
    )


def chart_identity():
    return ChartIdentity("chart-test", "project_natal", "ziwei-natal-true-solar-common-v1")


def source(scope="daily", stem="甲", branch="子", reference="ref:1", validation="validated"):
    return FlowingStarSource(
        chart_identity(),
        scope,
        reference,
        stem,
        branch,
        "test-cycle-source-v1",
        RULE_VERSION,
        validation,
        provenance(),
    )


def placements(scope="daily", count=10):
    stars = ("天魁", "天鉞", "文昌", "文曲", "祿存", "擎羊", "陀羅", "天馬", "紅鸞", "天喜", "年解")
    categories = {
        "天魁": "soft", "天鉞": "soft", "文昌": "soft", "文曲": "soft",
        "祿存": "lucun", "擎羊": "tough", "陀羅": "tough", "天馬": "tianma",
        "紅鸞": "flower", "天喜": "flower", "年解": "helper",
    }
    return tuple(
        FlowingStarPlacement(star, categories[star], scope, "子", index + 1, provenance())
        for index, star in enumerate(stars[:count])
    )


class FlowingStarModelTests(unittest.TestCase):
    def test_error_contract_matches_existing_ziwei_errors(self):
        err = ZiweiFlowingStarError("cycle_scope_mismatch", "x", {"scope": "daily"})
        self.assertEqual(err.code, "cycle_scope_mismatch")
        self.assertEqual(err.details, {"scope": "daily"})

    def test_profile_is_frozen_and_versioned(self):
        profile = FlowingStarProfile(PROFILE_ID, RULE_VERSION, "earthly_branch", "iztro-2.6.0-814b77e6")
        with self.assertRaises(FrozenInstanceError):
            profile.rule_version = "2"

    def test_source_is_frozen_and_requires_legal_sexagenary_pair(self):
        item = source()
        with self.assertRaises(FrozenInstanceError):
            item.scope = "monthly"
        with self.assertRaises(ZiweiFlowingStarError) as caught:
            source(stem="甲", branch="丑")
        self.assertEqual(caught.exception.code, "invalid_sexagenary_pair")

    def test_source_rejects_invalid_scope_blank_reference_and_invalid_branch(self):
        for kwargs, code in (
            ({"scope": "weekly"}, "unsupported_flowing_star_scope"),
            ({"reference": "  "}, "missing_cycle_stem_source"),
            ({"branch": "不存在"}, "invalid_flowing_star_branch"),
        ):
            with self.assertRaises(ZiweiFlowingStarError) as caught:
                source(**kwargs)
            self.assertEqual(caught.exception.code, code)

    def test_placement_rejects_unknown_category_scope_branch_and_sequence(self):
        for args, code in (
            (("天魁", "unknown", "daily", "子", 1, provenance()), "invalid_flowing_star_layer"),
            (("天魁", "soft", "weekly", "子", 1, provenance()), "unsupported_flowing_star_scope"),
            (("天魁", "soft", "daily", "不存在", 1, provenance()), "invalid_flowing_star_branch"),
            (("天魁", "soft", "daily", "子", 0, provenance()), "invalid_flowing_star_layer"),
        ):
            with self.assertRaises(ZiweiFlowingStarError) as caught:
                FlowingStarPlacement(*args)
            self.assertEqual(caught.exception.code, code)

    def test_non_yearly_layer_requires_exactly_ten_unique_stars(self):
        src = source()
        identity = LayerIdentity(src.chart_identity.chart_id, src.scope, src.reference, PROFILE_ID)
        layer = FlowingStarLayer(
            identity, src, placements(), PROFILE_ID, RULE_VERSION,
            "Project 推導盤面", "experimental", "validated", provenance(),
        )
        self.assertEqual(len(layer.placements), 10)
        with self.assertRaises(FrozenInstanceError):
            layer.maturity = "stable"
        with self.assertRaises(ZiweiFlowingStarError) as caught:
            FlowingStarLayer(
                identity, src, placements(count=9), PROFILE_ID, RULE_VERSION,
                "Project 推導盤面", "experimental", "validated", provenance(),
            )
        self.assertEqual(caught.exception.code, "incomplete_flowing_star_catalog")

    def test_yearly_layer_requires_exactly_eleven_and_nianjie(self):
        src = source(scope="yearly", stem="丙", branch="寅", reference="lunar-year:2026")
        identity = LayerIdentity(src.chart_identity.chart_id, src.scope, src.reference, PROFILE_ID)
        yearly = placements(scope="yearly", count=11)
        layer = FlowingStarLayer(
            identity, src, yearly, PROFILE_ID, RULE_VERSION,
            "Project 推導盤面", "experimental", "validated", provenance(),
        )
        self.assertEqual(layer.placements[-1].base_star, "年解")
        with self.assertRaises(ZiweiFlowingStarError):
            FlowingStarLayer(
                identity, src, yearly[:-1], PROFILE_ID, RULE_VERSION,
                "Project 推導盤面", "experimental", "validated", provenance(),
            )

    def test_layer_rejects_duplicate_identity_and_identity_source_mismatch(self):
        src = source()
        identity = LayerIdentity(src.chart_identity.chart_id, src.scope, src.reference, PROFILE_ID)
        duplicated = placements()[:-1] + (placements()[0],)
        with self.assertRaises(ZiweiFlowingStarError) as caught:
            FlowingStarLayer(
                identity, src, duplicated, PROFILE_ID, RULE_VERSION,
                "Project 推導盤面", "experimental", "validated", provenance(),
            )
        self.assertEqual(caught.exception.code, "duplicate_flowing_star_identity")
        bad_identity = LayerIdentity("other-chart", src.scope, src.reference, PROFILE_ID)
        with self.assertRaises(ZiweiFlowingStarError) as caught2:
            FlowingStarLayer(
                bad_identity, src, placements(), PROFILE_ID, RULE_VERSION,
                "Project 推導盤面", "experimental", "validated", provenance(),
            )
        self.assertEqual(caught2.exception.code, "chart_basis_mismatch")

    def test_layer_rejects_nonexperimental_maturity_and_blocked_source(self):
        src = source()
        identity = LayerIdentity(src.chart_identity.chart_id, src.scope, src.reference, PROFILE_ID)
        with self.assertRaises(ZiweiFlowingStarError):
            FlowingStarLayer(
                identity, src, placements(), PROFILE_ID, RULE_VERSION,
                "Project 推導盤面", "stable", "validated", provenance(),
            )
        blocked = source(validation="boundary_conflict")
        blocked_identity = LayerIdentity(blocked.chart_identity.chart_id, blocked.scope, blocked.reference, PROFILE_ID)
        with self.assertRaises(ZiweiFlowingStarError):
            FlowingStarLayer(
                blocked_identity, blocked, placements(), PROFILE_ID, RULE_VERSION,
                "Project 推導盤面", "experimental", "boundary_conflict", provenance(),
            )

    def test_scope_palace_mapping_freezes_input_mapping(self):
        mapping = {branch: "宮-%s" % branch for branch in "子丑寅卯辰巳午未申酉戌亥"}
        item = ScopePalaceMapping("chart-test", "daily", "ref:1", mapping)
        mapping["子"] = "changed"
        self.assertEqual(item.palaces["子"], "宮-子")
        with self.assertRaises(TypeError):
            item.palaces["子"] = "changed"


if __name__ == "__main__":
    unittest.main()
