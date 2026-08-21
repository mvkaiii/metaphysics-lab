import unittest

from engine.ziwei.errors import ZiweiPhase2AError
from engine.ziwei.transformation_profiles import validate_transformation_profile
from engine.ziwei.transformations import get_transformation_set

EXPECTED = {
    "甲": ("廉貞", "破軍", "武曲", "太陽"),
    "乙": ("天機", "天梁", "紫微", "太陰"),
    "丙": ("天同", "天機", "文昌", "廉貞"),
    "丁": ("太陰", "天同", "天機", "巨門"),
    "戊": ("貪狼", "太陰", "右弼", "天機"),
    "己": ("武曲", "貪狼", "天梁", "文曲"),
    "庚": ("太陽", "武曲", "太陰", "天同"),
    "辛": ("巨門", "太陽", "文曲", "文昌"),
    "壬": ("天梁", "紫微", "左輔", "武曲"),
    "癸": ("破軍", "巨門", "太陰", "貪狼"),
}


class ZiweiTransformationTests(unittest.TestCase):
    def test_all_ten_stems_match_exact_four_transformations(self):
        checked = 0
        for stem, expected_stars in EXPECTED.items():
            result = get_transformation_set(stem)
            self.assertEqual(tuple(item.star for item in result.transformations), expected_stars)
            self.assertEqual(tuple(item.type.value for item in result.transformations), ("祿", "權", "科", "忌"))
            self.assertEqual(tuple(item.sequence for item in result.transformations), (0, 1, 2, 3))
            self.assertEqual(result.provenance.classification, "project_derived")
            checked += 4
        self.assertEqual(checked, 40)

    def test_invalid_stem_fails_closed(self):
        with self.assertRaises(ZiweiPhase2AError) as cm:
            get_transformation_set("A")
        self.assertEqual(cm.exception.code, "invalid_heavenly_stem")

    def test_unknown_profile_has_no_fallback(self):
        with self.assertRaises(ZiweiPhase2AError) as cm:
            get_transformation_set("甲", "unknown-v1")
        self.assertEqual(cm.exception.code, "unknown_profile")

    def test_incomplete_profile_is_invalid_transformation_profile(self):
        with self.assertRaises(ZiweiPhase2AError) as cm:
            validate_transformation_profile("x", "1", {"甲": ("廉貞", "破軍", "武曲", "太陽")})
        self.assertEqual(cm.exception.code, "invalid_transformation_profile")


if __name__ == "__main__":
    unittest.main()
