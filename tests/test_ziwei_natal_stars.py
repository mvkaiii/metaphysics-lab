import json
import unittest
from pathlib import Path
from types import SimpleNamespace

from engine.ziwei.common import ZHI
from engine.ziwei.errors import ZiweiPhase2AError
from engine.ziwei.natal_palaces import resolve_palace_stems
from engine.ziwei.natal_profiles import ZiweiNatalProfile
from engine.ziwei.natal_stars import (
    materialize_star_records,
    place_auxiliary_stars,
    place_chang_qu,
    place_fire_bell,
    place_kui_yue,
    place_left_right_assistants,
    place_lucun_yang_tuo,
    place_major_stars,
    place_tianma,
    validate_transformation_star_locations,
)
from engine.ziwei.star_catalog import AUXILIARY_STARS, MAJOR_STARS, STAR_CATALOG
from engine.ziwei.transformation_profiles import PROFILE


MAJOR_FIXTURE = Path("qualification/ziwei/natal/public-iztro-major-star-vectors.json")
AUX_FIXTURE = Path("qualification/ziwei/natal/public-iztro-aux-star-vectors.json")
EXPECTED_REVISION = "814b77e6371e1050cac31bbf674db3c3138fcfde"
BUREAU_VALUES = {"水二局": 2, "木三局": 3, "金四局": 4, "土五局": 5, "火六局": 6}


class ZiweiNatalMajorStarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(MAJOR_FIXTURE.read_text(encoding="utf-8"))

    def test_catalog_order_is_exact_and_immutable(self):
        self.assertEqual(
            MAJOR_STARS,
            (
                "紫微", "天機", "太陽", "武曲", "天同", "廉貞",
                "天府", "太陰", "貪狼", "巨門", "天相", "天梁", "七殺", "破軍",
            ),
        )
        self.assertIsInstance(MAJOR_STARS, tuple)

    def test_fixture_is_pinned_and_covers_all_150_day_bureau_cases(self):
        self.assertEqual(self.fixture["oracle"]["revision"], EXPECTED_REVISION)
        self.assertEqual(self.fixture["oracle"]["engine"], "iztro")
        self.assertEqual(self.fixture["oracle"]["version"], "2.6.0")
        self.assertEqual(len(self.fixture["oracle"]["rule_contract_sha256"]), 64)
        self.assertEqual(self.fixture["case_count"], 150)
        self.assertEqual({row["bureau"] for row in self.fixture["matrices"]}, set(BUREAU_VALUES))
        self.assertTrue(all(len(row["placements"]) == 30 for row in self.fixture["matrices"]))

    def test_source_comment_sanity_vectors_are_frozen(self):
        by_key = {(item["bureau"], item["lunar_day"]): item for item in self.fixture["sanity_vectors"]}
        for bureau, day, branch in (("木三局", 27, "戌"), ("火六局", 13, "亥"), ("土五局", 6, "未")):
            placements = dict(place_major_stars(day, bureau))
            self.assertEqual(placements["紫微"], branch)
            self.assertEqual(by_key[(bureau, day)]["ziwei_branch"], branch)

    def test_all_150_cases_match_pinned_major_star_vectors_exactly(self):
        checked = 0
        for row in self.fixture["matrices"]:
            self.assertEqual(row["bureau_value"], BUREAU_VALUES[row["bureau"]])
            for day, encoded in enumerate(row["placements"], start=1):
                actual = place_major_stars(day, row["bureau"])
                self.assertIsInstance(actual, tuple)
                self.assertEqual(tuple(star for star, _ in actual), MAJOR_STARS)
                self.assertEqual(len(actual), 14)
                self.assertEqual(len({star for star, _ in actual}), 14)
                self.assertTrue(all(branch in ZHI for _, branch in actual))
                self.assertEqual("".join(branch for _, branch in actual), encoded)
                self.assertEqual(actual, place_major_stars(day, row["bureau"]))
                checked += 1
        self.assertEqual(checked, 150)

    def test_materialization_maps_branches_to_existing_palace_records_without_brightness_guess(self):
        palaces = resolve_palace_stems("甲", "寅")
        profile = ZiweiNatalProfile()
        placements = place_major_stars(11, "水二局")
        records = materialize_star_records(placements, palaces, profile)
        palace_by_branch = {palace.branch: palace.name for palace in palaces}
        self.assertEqual(len(records), 14)
        for record, (star, branch) in zip(records, placements):
            self.assertEqual(record.star, star)
            self.assertEqual(record.branch, branch)
            self.assertEqual(record.palace, palace_by_branch[branch])
            self.assertEqual(record.category, "major")
            self.assertIsNone(record.brightness)
            self.assertEqual(record.catalog_profile, profile.star_catalog)

    def test_invalid_day_bureau_and_materialization_inputs_fail_closed(self):
        for day in (0, 31, True):
            with self.assertRaises(ValueError):
                place_major_stars(day, "水二局")
        with self.assertRaises(ValueError):
            place_major_stars(1, "不存在")
        with self.assertRaises(ValueError):
            materialize_star_records((('紫微', '不存在'),), resolve_palace_stems("甲", "寅"), ZiweiNatalProfile())
        with self.assertRaises(ValueError):
            materialize_star_records((('紫微', '寅'), ('紫微', '卯')), resolve_palace_stems("甲", "寅"), ZiweiNatalProfile())


class ZiweiNatalAuxiliaryStarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(AUX_FIXTURE.read_text(encoding="utf-8"))

    def test_fixture_is_pinned_and_covers_each_rule_dependency_dimension(self):
        self.assertEqual(self.fixture["oracle"]["revision"], EXPECTED_REVISION)
        self.assertEqual(self.fixture["oracle"]["engine"], "iztro")
        self.assertEqual(self.fixture["coverage"], {
            "lunar_months": 12,
            "hour_branches": 12,
            "year_stems": 10,
            "year_branches": 12,
            "fire_bell_year_branch_hour_cases": 144,
        })

    def test_all_transformation_required_stars_exist_in_natal_catalog(self):
        required = {star for stars in PROFILE.values() for star in stars}
        self.assertTrue(required.issubset(STAR_CATALOG))
        self.assertTrue({"左輔", "右弼", "文昌", "文曲"}.issubset(AUXILIARY_STARS))

    def test_all_month_vectors_match_left_right_assistants(self):
        for row in self.fixture["left_right"]:
            self.assertEqual(
                place_left_right_assistants(row["month"]),
                {"左輔": row["left"], "右弼": row["right"]},
            )

    def test_all_hour_vectors_match_chang_qu(self):
        for row in self.fixture["chang_qu"]:
            self.assertEqual(
                place_chang_qu(row["hour"]),
                {"文昌": row["chang"], "文曲": row["qu"]},
            )

    def test_all_ten_stems_match_kui_yue_and_lucun_yang_tuo(self):
        for row in self.fixture["kui_yue"]:
            self.assertEqual(place_kui_yue(row["stem"]), {"天魁": row["kui"], "天鉞": row["yue"]})
        for row in self.fixture["lu_yang_tuo"]:
            self.assertEqual(
                place_lucun_yang_tuo(row["stem"]),
                {"祿存": row["lu"], "擎羊": row["yang"], "陀羅": row["tuo"]},
            )

    def test_all_year_branches_match_tianma(self):
        for row in self.fixture["tianma"]:
            self.assertEqual(place_tianma(row["branch"]), {"天馬": row["ma"]})

    def test_all_144_year_branch_hour_cases_match_fire_bell(self):
        hours = self.fixture["hour_branch_order"]
        checked = 0
        for row in self.fixture["fire_bell"]:
            self.assertEqual(len(row["fire"]), 12)
            self.assertEqual(len(row["bell"]), 12)
            for index, hour in enumerate(hours):
                self.assertEqual(
                    place_fire_bell(row["year_branch"], hour),
                    {"火星": row["fire"][index], "鈴星": row["bell"][index]},
                )
                checked += 1
        self.assertEqual(checked, 144)

    def test_combined_auxiliary_placement_has_exact_selected_catalog_order(self):
        basis = SimpleNamespace(lunar_month=2, effective_hour_branch="戌", lunar_year=1984)
        placements = place_auxiliary_stars(basis, "甲", ZiweiNatalProfile())
        self.assertEqual(tuple(star for star, _ in placements), AUXILIARY_STARS)
        self.assertEqual(len(placements), 12)
        self.assertEqual(len({star for star, _ in placements}), 12)
        self.assertTrue(all(branch in ZHI for _, branch in placements))

    def test_missing_transformation_star_location_fails_closed_before_flying(self):
        complete = place_major_stars(11, "水二局") + place_auxiliary_stars(
            SimpleNamespace(lunar_month=2, effective_hour_branch="戌", lunar_year=1984),
            "甲",
            ZiweiNatalProfile(),
        )
        validate_transformation_star_locations(complete)
        missing_wenchang = tuple(item for item in complete if item[0] != "文昌")
        with self.assertRaises(ZiweiPhase2AError) as caught:
            validate_transformation_star_locations(missing_wenchang)
        self.assertEqual(caught.exception.code, "missing_transformation_star_location")
        self.assertIn("文昌", caught.exception.details["missing_stars"])

    def test_invalid_auxiliary_inputs_fail_closed(self):
        for month in (0, 13, True):
            with self.assertRaises(ValueError):
                place_left_right_assistants(month)
        with self.assertRaises(ValueError):
            place_chang_qu("不存在")
        with self.assertRaises(ValueError):
            place_kui_yue("不存在")
        with self.assertRaises(ValueError):
            place_lucun_yang_tuo("不存在")
        with self.assertRaises(ValueError):
            place_tianma("不存在")
        with self.assertRaises(ValueError):
            place_fire_bell("子", "不存在")


if __name__ == "__main__":
    unittest.main()
