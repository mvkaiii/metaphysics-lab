import unittest

from engine.calendar.sexagenary import GAN, ZHI, is_valid_sexagenary_pair
from engine.ziwei.errors import ZiweiFlowingStarError
from engine.ziwei.flowing_star_models import FlowingStarSource
from engine.ziwei.flowing_stars import (
    FLOWING_STAR_PROFILE_ID,
    FLOWING_STAR_RULE_VERSION,
    build_flowing_star_layer,
    get_flowing_star_profile,
    place_chang_qu_by_stem,
    place_flowing_stars_for_pair,
    place_luan_xi,
    place_nianjie,
)
from engine.ziwei.models import ChartIdentity, LayerProvenance
from engine.ziwei.natal_stars import place_kui_yue, place_lucun_yang_tuo, place_tianma


PROFILE_ID = "ziwei-flowing-stars-common-v1"
RULE_VERSION = "1.0-exp"
SCOPES = ("decadal", "yearly", "monthly", "daily", "hourly")
BASE_CATALOG = ("天魁", "天鉞", "文昌", "文曲", "祿存", "擎羊", "陀羅", "天馬", "紅鸞", "天喜")


def provenance():
    return LayerProvenance(
        "project_derived",
        "Metaphysics Lab",
        None,
        PROFILE_ID,
        RULE_VERSION,
        "tests.test_ziwei_flowing_stars",
    )


def chart_identity():
    return ChartIdentity("chart-phase2c-core", "project_natal", "ziwei-natal-true-solar-common-v1")


def formal_source(scope, stem, branch, reference):
    return FlowingStarSource(
        chart_identity(),
        scope,
        reference,
        stem,
        branch,
        "test-cycle-source-v1",
        RULE_VERSION,
        "validated",
        provenance(),
    )


class FlowingStarCoreTests(unittest.TestCase):
    def test_profile_and_catalog_order_are_fixed(self):
        self.assertEqual(FLOWING_STAR_PROFILE_ID, PROFILE_ID)
        self.assertEqual(FLOWING_STAR_RULE_VERSION, RULE_VERSION)
        profile = get_flowing_star_profile()
        self.assertEqual(profile.profile_id, PROFILE_ID)
        self.assertEqual(profile.rule_version, RULE_VERSION)
        self.assertEqual(profile.canonical_location, "earthly_branch")
        self.assertEqual(profile.qualification_target, "iztro-2.6.0-814b77e6")

        non_yearly = place_flowing_stars_for_pair("daily", "甲", "子")
        yearly = place_flowing_stars_for_pair("yearly", "甲", "子")
        self.assertEqual(tuple(item.base_star for item in non_yearly), BASE_CATALOG)
        self.assertEqual(tuple(item.base_star for item in yearly), BASE_CATALOG + ("年解",))

    def test_chang_qu_exact_approved_table(self):
        expected = {
            "甲": ("巳", "酉"), "乙": ("午", "申"), "丙": ("申", "午"), "丁": ("酉", "巳"),
            "戊": ("申", "午"), "己": ("酉", "巳"), "庚": ("亥", "卯"), "辛": ("子", "寅"),
            "壬": ("寅", "子"), "癸": ("卯", "亥"),
        }
        for stem, pair in expected.items():
            self.assertEqual(place_chang_qu_by_stem(stem), {"文昌": pair[0], "文曲": pair[1]})

    def test_luan_xi_exact_approved_table(self):
        expected = {
            "子": ("卯", "酉"), "丑": ("寅", "申"), "寅": ("丑", "未"), "卯": ("子", "午"),
            "辰": ("亥", "巳"), "巳": ("戌", "辰"), "午": ("酉", "卯"), "未": ("申", "寅"),
            "申": ("未", "丑"), "酉": ("午", "子"), "戌": ("巳", "亥"), "亥": ("辰", "戌"),
        }
        for branch, pair in expected.items():
            self.assertEqual(place_luan_xi(branch), {"紅鸞": pair[0], "天喜": pair[1]})

    def test_nianjie_exact_approved_table(self):
        expected = {
            "子": "戌", "丑": "酉", "寅": "申", "卯": "未", "辰": "午", "巳": "巳",
            "午": "辰", "未": "卯", "申": "寅", "酉": "丑", "戌": "子", "亥": "亥",
        }
        for branch, target in expected.items():
            self.assertEqual(place_nianjie(branch), {"年解": target})

    def test_existing_natal_helpers_are_reused_semantically(self):
        for stem in GAN:
            placements = {item.base_star: item.target_branch for item in place_flowing_stars_for_pair("daily", stem, "子")}
            for star, target in place_kui_yue(stem).items():
                self.assertEqual(placements[star], target)
            for star, target in place_lucun_yang_tuo(stem).items():
                self.assertEqual(placements[star], target)

        for branch in ZHI:
            placements = {item.base_star: item.target_branch for item in place_flowing_stars_for_pair("daily", "甲", branch)}
            self.assertEqual(placements["天馬"], place_tianma(branch)["天馬"])

    def test_all_600_pure_formula_combinations_hold_invariants(self):
        total = 0
        for scope in SCOPES:
            for stem in GAN:
                for branch in ZHI:
                    items = place_flowing_stars_for_pair(scope, stem, branch)
                    expected_count = 11 if scope == "yearly" else 10
                    self.assertEqual(len(items), expected_count)
                    self.assertEqual(tuple(item.sequence for item in items), tuple(range(1, expected_count + 1)))
                    self.assertEqual(len({item.base_star for item in items}), expected_count)
                    self.assertTrue(all(item.target_branch in ZHI for item in items))
                    by_star = {item.base_star: item.target_branch for item in items}

                    lu_index = ZHI.index(by_star["祿存"])
                    self.assertEqual(by_star["擎羊"], ZHI[(lu_index + 1) % 12])
                    self.assertEqual(by_star["陀羅"], ZHI[(lu_index - 1) % 12])
                    self.assertEqual(by_star["天喜"], ZHI[(ZHI.index(by_star["紅鸞"]) + 6) % 12])
                    self.assertIn(by_star["天馬"], ("寅", "申", "巳", "亥"))
                    total += 1
        self.assertEqual(total, 600)

    def test_all_300_formal_sources_build_and_invalid_pairs_fail_at_source(self):
        legal_pairs = tuple((stem, branch) for stem in GAN for branch in ZHI if is_valid_sexagenary_pair(stem, branch))
        invalid_pairs = tuple((stem, branch) for stem in GAN for branch in ZHI if not is_valid_sexagenary_pair(stem, branch))
        self.assertEqual(len(legal_pairs), 60)
        self.assertEqual(len(invalid_pairs), 60)

        built = 0
        for scope in SCOPES:
            for index, (stem, branch) in enumerate(legal_pairs):
                src = formal_source(scope, stem, branch, "%s:%d" % (scope, index))
                layer = build_flowing_star_layer(src)
                self.assertEqual(layer.source, src)
                self.assertEqual(layer.identity.chart_id, src.chart_identity.chart_id)
                self.assertEqual(layer.identity.scope, scope)
                self.assertEqual(layer.identity.reference, src.reference)
                built += 1
        self.assertEqual(built, 300)

        for scope in SCOPES:
            for index, (stem, branch) in enumerate(invalid_pairs):
                with self.assertRaises(ZiweiFlowingStarError) as caught:
                    formal_source(scope, stem, branch, "invalid:%s:%d" % (scope, index))
                self.assertEqual(caught.exception.code, "invalid_sexagenary_pair")

    def test_pure_formula_rejects_individually_invalid_stem_or_branch(self):
        with self.assertRaises(ZiweiFlowingStarError) as caught:
            place_flowing_stars_for_pair("daily", "不存在", "子")
        self.assertEqual(caught.exception.code, "invalid_flowing_star_stem")
        with self.assertRaises(ZiweiFlowingStarError) as caught2:
            place_flowing_stars_for_pair("daily", "甲", "不存在")
        self.assertEqual(caught2.exception.code, "invalid_flowing_star_branch")


if __name__ == "__main__":
    unittest.main()
