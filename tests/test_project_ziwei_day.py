import unittest

from engine.ziwei.day import flow_day_ming_branch, flow_day_palaces, project_derived_ziwei_day


class ZiweiDayTests(unittest.TestCase):
    def test_first_day_starts_at_flow_month_ming(self):
        self.assertEqual(flow_day_ming_branch(5, "戌", "酉", 1, 1, False), "卯")

    def test_second_day_moves_forward_one_palace(self):
        self.assertEqual(flow_day_ming_branch(5, "戌", "酉", 1, 2, False), "辰")

    def test_thirteenth_day_wraps_to_same_palace(self):
        self.assertEqual(flow_day_ming_branch(5, "戌", "酉", 1, 13, False), "卯")

    def test_leap_month_second_half_uses_next_effective_month_without_day_reset(self):
        self.assertEqual(flow_day_ming_branch(5, "戌", "酉", 5, 15, True), "酉")
        self.assertEqual(flow_day_ming_branch(5, "戌", "酉", 5, 16, True), "亥")

    def test_palace_map_anchors_at_flow_day_ming(self):
        palaces = flow_day_palaces("辰")
        self.assertEqual(palaces["命宮"], "辰")
        self.assertEqual(palaces["兄弟宮"], "卯")
        self.assertEqual(palaces["父母宮"], "巳")

    def test_structured_output_marks_experimental_on_demand(self):
        result = project_derived_ziwei_day(5, "戌", "酉", 1, 2, False)
        self.assertEqual(result["classification"], "Project 推導盤面")
        self.assertEqual(result["scope"], "紫微流日")
        self.assertEqual(result["capability"]["implementation"], "implemented")
        self.assertEqual(result["capability"]["maturity"], "experimental")
        self.assertEqual(result["capability"]["routing"], "on_demand")
        self.assertEqual(result["flow_month_ming_branch"], "卯")
        self.assertEqual(result["flow_day_ming_branch"], "辰")
        self.assertTrue(result["features"]["flow_hour_implemented"])
        self.assertFalse(result["features"]["flow_hour_default_routing"])
        self.assertFalse(result["features"]["daily_four_transformations_implemented"])
        self.assertFalse(result["features"]["daily_flowing_stars_implemented"])

    def test_invalid_day_is_rejected(self):
        with self.assertRaises(ValueError):
            flow_day_ming_branch(5, "戌", "酉", 1, 0, False)
        with self.assertRaises(ValueError):
            flow_day_ming_branch(5, "戌", "酉", 1, 31, False)

    def test_invalid_branch_is_rejected(self):
        with self.assertRaises(ValueError):
            flow_day_ming_branch(5, "A", "酉", 1, 1, False)


if __name__ == "__main__":
    unittest.main()
