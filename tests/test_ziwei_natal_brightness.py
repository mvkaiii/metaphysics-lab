import json
import unittest
from pathlib import Path

from engine.ziwei.brightness_profiles import BRIGHTNESS_PROFILE_ID, brightness_for
from engine.ziwei.common import ZHI
from engine.ziwei.star_catalog import STAR_CATALOG, brightness_optional_for


FIXTURE = Path("qualification/ziwei/natal/public-iztro-brightness-vectors.json")
EXPECTED_REVISION = "814b77e6371e1050cac31bbf674db3c3138fcfde"
ALLOWED = {"廟", "旺", "得", "利", "平", "不", "陷"}


class ZiweiNatalBrightnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_profile_and_fixture_are_pinned(self):
        self.assertEqual(BRIGHTNESS_PROFILE_ID, "ziwei-brightness-common-v1")
        self.assertEqual(self.fixture["profile_id"], BRIGHTNESS_PROFILE_ID)
        self.assertEqual(self.fixture["oracle"]["revision"], EXPECTED_REVISION)
        self.assertEqual(self.fixture["oracle"]["engine"], "iztro")
        self.assertEqual(self.fixture["oracle"]["version"], "2.6.0")
        self.assertEqual(len(self.fixture["oracle"]["rule_contract_sha256"]), 64)
        self.assertEqual(self.fixture["branch_order"], "寅卯辰巳午未申酉戌亥子丑")
        self.assertEqual(set(self.fixture["allowed_labels"]), ALLOWED)
        self.assertEqual(self.fixture["defined_star_count"], 20)

    def test_every_committed_defined_pair_matches_pinned_source(self):
        checked = 0
        branches = tuple(self.fixture["branch_order"])
        for row in self.fixture["vectors"]:
            self.assertEqual(len(row["brightness"]), 12)
            self.assertIn(row["star"], STAR_CATALOG)
            for branch, expected in zip(branches, row["brightness"]):
                actual = brightness_for(row["star"], branch)
                self.assertEqual(actual, expected)
                if actual is not None:
                    self.assertIn(actual, ALLOWED)
                checked += 1
        self.assertEqual(checked, 240)

    def test_source_undefined_selected_stars_are_explicitly_optional(self):
        optional = tuple(self.fixture["undefined_optional_stars"])
        self.assertEqual(optional, ("左輔", "右弼", "天魁", "天鉞", "祿存", "天馬"))
        for star in optional:
            self.assertTrue(brightness_optional_for(star))
            for branch in ZHI:
                self.assertIsNone(brightness_for(star, branch))

    def test_partial_source_rows_are_optional_only_where_source_is_blank(self):
        vectors = {row["star"]: row["brightness"] for row in self.fixture["vectors"]}
        branches = tuple(self.fixture["branch_order"])
        for star in ("擎羊", "陀羅"):
            self.assertTrue(brightness_optional_for(star))
            self.assertIn(None, vectors[star])
            for branch, expected in zip(branches, vectors[star]):
                self.assertEqual(brightness_for(star, branch), expected)

    def test_complete_rows_are_not_marked_optional(self):
        for star in ("紫微", "天機", "太陽", "武曲", "天同", "廉貞", "天府", "太陰", "貪狼", "巨門", "天相", "天梁", "七殺", "破軍", "文昌", "文曲", "火星", "鈴星"):
            self.assertFalse(brightness_optional_for(star))

    def test_unknown_star_branch_and_profile_fail_closed(self):
        with self.assertRaises(ValueError):
            brightness_for("不存在", "寅")
        with self.assertRaises(ValueError):
            brightness_for("紫微", "不存在")
        with self.assertRaises(ValueError):
            brightness_for("紫微", "寅", profile_id="unknown")
        with self.assertRaises(ValueError):
            brightness_optional_for("不存在")


if __name__ == "__main__":
    unittest.main()
