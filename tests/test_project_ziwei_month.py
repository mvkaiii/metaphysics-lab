import unittest

from engine.project_ziwei_month import (
    effective_lunar_month,
    annual_doujun_branch,
    flow_month_ming_branch,
    flow_month_palaces,
    project_derived_ziwei_month,
)


class ZiweiMonthTests(unittest.TestCase):
    def test_public_doujun_example_1993_birth_2017(self):
        self.assertEqual(
            annual_doujun_branch(
                birth_lunar_month=5,
                birth_hour_branch='戌',
                flow_year_branch='酉',
            ),
            '卯',
        )

    def test_first_month_starts_at_doujun(self):
        self.assertEqual(
            flow_month_ming_branch(
                birth_lunar_month=5,
                birth_hour_branch='戌',
                flow_year_branch='酉',
                lunar_month=1,
                lunar_day=1,
                is_leap_month=False,
            ),
            '卯',
        )

    def test_second_month_moves_forward_one_palace(self):
        self.assertEqual(
            flow_month_ming_branch(
                birth_lunar_month=5,
                birth_hour_branch='戌',
                flow_year_branch='酉',
                lunar_month=2,
                lunar_day=1,
                is_leap_month=False,
            ),
            '辰',
        )

    def test_leap_month_first_half_uses_original_month(self):
        self.assertEqual(effective_lunar_month(5, 15, True), 5)

    def test_leap_month_second_half_uses_next_month(self):
        self.assertEqual(effective_lunar_month(5, 16, True), 6)

    def test_leap_twelfth_month_wraps_to_first_month(self):
        self.assertEqual(effective_lunar_month(12, 16, True), 1)

    def test_flow_month_palaces_follow_fixed_direction(self):
        palaces = flow_month_palaces('卯')
        self.assertEqual(palaces['命宮'], '卯')
        self.assertEqual(palaces['兄弟宮'], '寅')
        self.assertEqual(palaces['夫妻宮'], '丑')
        self.assertEqual(palaces['父母宮'], '辰')

    def test_structured_output_explains_boundary_difference(self):
        result = project_derived_ziwei_month(
            birth_lunar_month=5,
            birth_hour_branch='戌',
            flow_year_branch='酉',
            lunar_month=2,
            lunar_day=1,
            is_leap_month=False,
        )
        self.assertEqual(result['classification'], 'Project 推導盤面')
        self.assertEqual(result['scope'], '紫微流月')
        self.assertEqual(result['month_boundary'], '農曆初一；閏月採初一至十五歸原月、十六起歸下一月')
        self.assertIn('八字流月採節氣月', result['boundary_note'])
        self.assertIn('不是 bug', result['boundary_note'])
        self.assertFalse(result['features']['flow_day_enabled'])
        self.assertFalse(result['features']['flow_hour_enabled'])
        self.assertFalse(result['features']['monthly_four_transformations_enabled'])

    def test_invalid_lunar_day_is_rejected(self):
        with self.assertRaises(ValueError):
            effective_lunar_month(5, 0, False)

    def test_invalid_branch_is_rejected(self):
        with self.assertRaises(ValueError):
            annual_doujun_branch(5, 'A', '酉')


if __name__ == '__main__':
    unittest.main()
