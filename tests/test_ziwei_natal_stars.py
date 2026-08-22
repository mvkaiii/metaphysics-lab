import json
import unittest
from pathlib import Path

from engine.ziwei.common import ZHI
from engine.ziwei.natal_palaces import resolve_palace_stems
from engine.ziwei.natal_profiles import ZiweiNatalProfile
from engine.ziwei.natal_stars import materialize_star_records, place_major_stars
from engine.ziwei.star_catalog import MAJOR_STARS


FIXTURE = Path("qualification/ziwei/natal/public-iztro-major-star-vectors.json")
EXPECTED_REVISION = "814b77e6371e1050cac31bbf674db3c3138fcfde"
BUREAU_VALUES = {"水二局": 2, "木三局": 3, "金四局": 4, "土五局": 5, "火六局": 6}


class ZiweiNatalMajorStarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

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


if __name__ == "__main__":
    unittest.main()
