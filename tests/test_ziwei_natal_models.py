import unittest
from dataclasses import FrozenInstanceError

from engine.ziwei.common import PALACE_NAMES, ZHI
from engine.ziwei.natal_models import ZiweiNatalChart, ZiweiPalaceRecord, ZiweiStarRecord
from engine.ziwei.natal_profiles import ZiweiNatalProfile
from engine.ziwei.transformation_profiles import LEGAL_STEMS


class ZiweiNatalModelTests(unittest.TestCase):
    def _palaces(self):
        return tuple(
            ZiweiPalaceRecord(
                name=name,
                branch=ZHI[index],
                heavenly_stem=LEGAL_STEMS[index % len(LEGAL_STEMS)],
                stem_branch=LEGAL_STEMS[index % len(LEGAL_STEMS)] + ZHI[index],
            )
            for index, name in enumerate(PALACE_NAMES)
        )

    def test_profile_contract_is_explicit_versioned_and_frozen(self):
        profile = ZiweiNatalProfile()
        self.assertEqual(profile.profile_id, "ziwei-natal-true-solar-common-v1")
        self.assertEqual(profile.rule_version, "1.0-exp")
        self.assertEqual(profile.time_basis, "true_solar")
        self.assertEqual(profile.star_catalog, "ziwei-core-stars-v1")
        self.assertEqual(profile.brightness_profile, "ziwei-brightness-common-v1")
        self.assertEqual(profile.decadal_profile, "ziwei-decadal-common-v1")
        self.assertEqual(profile.leap_month_policy, "iztro-fix-leap-15-16-v1")
        self.assertEqual(profile.late_zi_day_policy, "iztro-forward-v1")
        with self.assertRaises(FrozenInstanceError):
            profile.rule_version = "changed"

    def test_palace_record_requires_canonical_name_branch_and_matching_stem_branch(self):
        with self.assertRaises(ValueError):
            ZiweiPalaceRecord("不存在", "子", "甲", "甲子")
        with self.assertRaises(ValueError):
            ZiweiPalaceRecord("命宮", "不存在", "甲", "甲子")
        with self.assertRaises(ValueError):
            ZiweiPalaceRecord("命宮", "子", "甲", "乙子")

    def test_chart_requires_exactly_twelve_unique_canonical_palace_names(self):
        palaces = self._palaces()
        chart = ZiweiNatalChart(
            profile=ZiweiNatalProfile(),
            palaces=palaces,
            stars=(),
            decadal_periods=(),
            validation={"status": "pending"},
            provenance={"classification": "Project 原生盤面"},
        )
        self.assertEqual(tuple(palace.name for palace in chart.palaces), PALACE_NAMES)

        with self.assertRaises(ValueError):
            ZiweiNatalChart(
                profile=ZiweiNatalProfile(),
                palaces=palaces[:-1],
                stars=(),
                decadal_periods=(),
                validation={},
                provenance={},
            )

        duplicated = list(palaces)
        duplicated[-1] = ZiweiPalaceRecord(
            name="命宮",
            branch=duplicated[-1].branch,
            heavenly_stem=duplicated[-1].heavenly_stem,
            stem_branch=duplicated[-1].stem_branch,
        )
        with self.assertRaises(ValueError):
            ZiweiNatalChart(
                profile=ZiweiNatalProfile(),
                palaces=tuple(duplicated),
                stars=(),
                decadal_periods=(),
                validation={},
                provenance={},
            )

    def test_duplicate_star_identity_is_rejected_inside_one_chart(self):
        star = ZiweiStarRecord(
            star="紫微",
            palace="命宮",
            branch="子",
            category="major",
            brightness=None,
            catalog_profile="ziwei-core-stars-v1",
        )
        with self.assertRaises(ValueError):
            ZiweiNatalChart(
                profile=ZiweiNatalProfile(),
                palaces=self._palaces(),
                stars=(star, star),
                decadal_periods=(),
                validation={},
                provenance={},
            )

    def test_chart_and_records_are_frozen(self):
        chart = ZiweiNatalChart(
            profile=ZiweiNatalProfile(),
            palaces=self._palaces(),
            stars=(),
            decadal_periods=(),
            validation={},
            provenance={},
        )
        with self.assertRaises(FrozenInstanceError):
            chart.maturity = "stable"
        with self.assertRaises(TypeError):
            chart.validation["status"] = "changed"


if __name__ == "__main__":
    unittest.main()
