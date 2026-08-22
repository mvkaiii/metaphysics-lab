import unittest

from engine.calendar.sexagenary import (
    GAN,
    ZHI,
    is_valid_sexagenary_pair,
    lunar_year_branch,
)


class Phase2CSexagenaryTests(unittest.TestCase):
    def test_lunar_year_branch(self):
        self.assertEqual(lunar_year_branch(1984), "子")
        self.assertEqual(lunar_year_branch(1996), "子")
        self.assertEqual(lunar_year_branch(2026), "午")

    def test_lunar_year_branch_rejects_non_integer_input(self):
        for value in (True, 2026.0, "2026", None):
            with self.assertRaises(ValueError):
                lunar_year_branch(value)

    def test_exactly_sixty_pairs_are_legal(self):
        legal = [(stem, branch) for stem in GAN for branch in ZHI if is_valid_sexagenary_pair(stem, branch)]
        self.assertEqual(len(legal), 60)
        self.assertTrue(is_valid_sexagenary_pair("甲", "子"))
        self.assertFalse(is_valid_sexagenary_pair("甲", "丑"))
        self.assertTrue(is_valid_sexagenary_pair("癸", "亥"))

    def test_invalid_stem_or_branch_is_not_a_legal_pair(self):
        self.assertFalse(is_valid_sexagenary_pair("不存在", "子"))
        self.assertFalse(is_valid_sexagenary_pair("甲", "不存在"))


if __name__ == "__main__":
    unittest.main()
