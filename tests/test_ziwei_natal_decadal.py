import json
import unittest
from pathlib import Path

from engine.birth.models import Sex
from engine.ziwei.natal_decadal import (
    build_ziwei_decadal_periods,
    resolve_decadal_direction,
    resolve_life_body_master,
)
from engine.ziwei.natal_palaces import resolve_palace_stems


FIXTURE = Path("qualification/ziwei/natal/public-iztro-decadal-vectors.json")
EXPECTED_REVISION = "814b77e6371e1050cac31bbf674db3c3138fcfde"


class ZiweiNatalDecadalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_fixture_is_pinned_public_oracle(self):
        self.assertEqual(self.fixture["oracle"]["engine"], "iztro")
        self.assertEqual(self.fixture["oracle"]["version"], "2.6.0")
        self.assertEqual(self.fixture["oracle"]["revision"], EXPECTED_REVISION)
        self.assertEqual(len(self.fixture["oracle"]["rule_contract_sha256"]), 64)
        self.assertEqual(len(self.fixture["masters"]), 12)
        self.assertEqual(len(self.fixture["directions"]), 10)
        self.assertEqual(len(self.fixture["bureau_age_start"]), 5)

    def test_all_144_ming_and_birth_year_branch_master_combinations(self):
        rows = self.fixture["masters"]
        checked = 0
        for ming in rows:
            for birth in rows:
                self.assertEqual(
                    resolve_life_body_master(ming["branch"], birth["branch"]),
                    (ming["life_master"], birth["body_master"]),
                )
                checked += 1
        self.assertEqual(checked, 144)

    def test_all_20_stem_sex_direction_combinations(self):
        checked = 0
        for row in self.fixture["directions"]:
            self.assertEqual(resolve_decadal_direction(row["stem"], Sex.MALE), row["male"])
            self.assertEqual(resolve_decadal_direction(row["stem"], Sex.FEMALE), row["female"])
            checked += 2
        self.assertEqual(checked, 20)

    def test_all_five_bureau_age_starts_and_both_directions(self):
        palaces = resolve_palace_stems("甲", "寅")
        by_name = {palace.name: palace for palace in palaces}
        for row in self.fixture["bureau_age_start"]:
            for direction in ("forward", "reverse"):
                periods = build_ziwei_decadal_periods(palaces, row["bureau"], direction)
                self.assertIsInstance(periods, tuple)
                self.assertEqual(len(periods), 12)
                self.assertEqual(periods[0].palace, "命宮")
                self.assertEqual(periods[0].age_start, row["age_start"])
                self.assertEqual(periods[-1].age_start, row["age_start"] + 110)
                for index, period in enumerate(periods):
                    self.assertEqual(period.index, index + 1)
                    self.assertEqual(period.age_start, row["age_start"] + 10 * index)
                    self.assertEqual(period.age_end, period.age_start + 9)
                    self.assertEqual(period.direction, direction)
                    self.assertEqual(period.stem_branch, by_name[period.palace].stem_branch)
                    if index:
                        self.assertGreater(period.age_start, periods[index - 1].age_end)

    def test_forward_and_reverse_palace_orientation_matches_pinned_rule(self):
        palaces = resolve_palace_stems("甲", "寅")
        forward = build_ziwei_decadal_periods(palaces, "木三局", "forward")
        reverse = build_ziwei_decadal_periods(palaces, "木三局", "reverse")
        self.assertEqual(tuple(period.palace for period in forward[:4]), ("命宮", "父母宮", "福德宮", "田宅宮"))
        self.assertEqual(tuple(period.palace for period in reverse[:4]), ("命宮", "兄弟宮", "夫妻宮", "子女宮"))

    def test_count_is_explicit_and_cannot_exceed_twelve(self):
        palaces = resolve_palace_stems("甲", "寅")
        periods = build_ziwei_decadal_periods(palaces, "水二局", "forward", count=3)
        self.assertEqual(len(periods), 3)
        self.assertEqual(tuple(period.index for period in periods), (1, 2, 3))
        for count in (0, 13, True):
            with self.assertRaises(ValueError):
                build_ziwei_decadal_periods(palaces, "水二局", "forward", count=count)

    def test_invalid_inputs_fail_closed(self):
        with self.assertRaises(ValueError):
            resolve_life_body_master("不存在", "子")
        with self.assertRaises(ValueError):
            resolve_life_body_master("子", "不存在")
        with self.assertRaises(ValueError):
            resolve_decadal_direction("不存在", Sex.MALE)
        with self.assertRaises(ValueError):
            resolve_decadal_direction("甲", "male")
        palaces = resolve_palace_stems("甲", "寅")
        with self.assertRaises(ValueError):
            build_ziwei_decadal_periods(palaces, "不存在", "forward")
        with self.assertRaises(ValueError):
            build_ziwei_decadal_periods(palaces, "水二局", "sideways")
        with self.assertRaises(ValueError):
            build_ziwei_decadal_periods(palaces[:-1], "水二局", "forward")


if __name__ == "__main__":
    unittest.main()
