import json
import unittest
from pathlib import Path

from engine.ziwei.common import PALACE_NAMES, ZHI, palaces_from_ming_branch
from engine.ziwei.natal_palaces import (
    resolve_five_element_bureau,
    resolve_ming_body_branches,
    resolve_palace_stems,
)
from engine.ziwei.transformation_profiles import LEGAL_STEMS


FIXTURE = Path("qualification/ziwei/natal/public-iztro-palace-vectors.json")
EXPECTED_REVISION = "814b77e6371e1050cac31bbf674db3c3138fcfde"


class ZiweiNatalPalaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_fixture_is_pinned_public_oracle_with_full_matrix_counts(self):
        oracle = self.fixture["oracle"]
        self.assertEqual(oracle["engine"], "iztro")
        self.assertEqual(oracle["version"], "2.6.0")
        self.assertEqual(oracle["revision"], EXPECTED_REVISION)
        self.assertEqual(len(oracle["contract_sha256"]), 64)
        self.assertEqual(self.fixture["notes"]["month_hour_case_count"], 144)
        self.assertEqual(self.fixture["notes"]["palace_stem_year_case_count"], 10)
        self.assertEqual(self.fixture["notes"]["legal_bureau_combination_count"], 60)

    def test_all_12_months_by_12_hour_branches_match_pinned_ming_body_vectors(self):
        checked = 0
        for row in self.fixture["month_hour_matrix"]:
            self.assertEqual(row["hour_branches"], "".join(ZHI))
            self.assertEqual(len(row["ming_branches"]), 12)
            self.assertEqual(len(row["body_branches"]), 12)
            for index, hour_branch in enumerate(ZHI):
                self.assertEqual(
                    resolve_ming_body_branches(row["lunar_month"], hour_branch),
                    (row["ming_branches"][index], row["body_branches"][index]),
                )
                checked += 1
        self.assertEqual(checked, 144)

    def test_palace_records_follow_existing_canonical_palace_mapping_for_every_ming_branch(self):
        for ming_branch in ZHI:
            records = resolve_palace_stems("甲", ming_branch)
            self.assertEqual(len(records), 12)
            self.assertEqual(tuple(record.name for record in records), PALACE_NAMES)
            expected_branches = palaces_from_ming_branch(ming_branch)
            self.assertEqual(
                {record.name: record.branch for record in records},
                expected_branches,
            )
            self.assertEqual(len({record.branch for record in records}), 12)

    def test_all_ten_year_stem_palace_stems_match_pinned_vectors(self):
        self.assertEqual(
            {row["birth_year_stem"] for row in self.fixture["palace_stem_matrix"]},
            set(LEGAL_STEMS),
        )
        for row in self.fixture["palace_stem_matrix"]:
            expected = dict(zip(row["branches"], row["heavenly_stems"]))
            records = resolve_palace_stems(row["birth_year_stem"], "寅")
            actual = {record.branch: record.heavenly_stem for record in records}
            self.assertEqual(actual, expected)
            for record in records:
                self.assertEqual(record.stem_branch, record.heavenly_stem + record.branch)

    def test_all_60_legal_ming_stem_branch_combinations_match_bureau_vectors(self):
        legend = self.fixture["bureau_legend"]
        checked = set()
        for row in self.fixture["bureau_matrix"]:
            self.assertEqual(len(row["branches"]), 12)
            self.assertEqual(len(row["heavenly_stems"]), 12)
            self.assertEqual(len(row["bureau_codes"]), 12)
            for stem, branch, code in zip(
                row["heavenly_stems"], row["branches"], row["bureau_codes"]
            ):
                stem_branch = stem + branch
                self.assertNotIn(stem_branch, checked)
                checked.add(stem_branch)
                self.assertEqual(resolve_five_element_bureau(stem, branch), legend[code])
        self.assertEqual(len(checked), 60)
        self.assertEqual(
            {resolve_five_element_bureau(item[0], item[1]) for item in checked},
            {"水二局", "木三局", "金四局", "土五局", "火六局"},
        )

    def test_invalid_inputs_fail_closed(self):
        with self.assertRaises(ValueError):
            resolve_ming_body_branches(0, "子")
        with self.assertRaises(ValueError):
            resolve_ming_body_branches(1, "不存在")
        with self.assertRaises(ValueError):
            resolve_palace_stems("不存在", "寅")
        with self.assertRaises(ValueError):
            resolve_palace_stems("甲", "不存在")
        with self.assertRaises(ValueError):
            resolve_five_element_bureau("不存在", "寅")
        with self.assertRaises(ValueError):
            resolve_five_element_bureau("甲", "不存在")


if __name__ == "__main__":
    unittest.main()
