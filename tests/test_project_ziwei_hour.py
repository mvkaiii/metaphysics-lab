import unittest

from engine.ziwei.hour import (
    flow_hour_ming_branch,
    flow_hour_palaces,
    project_derived_ziwei_hour,
)


class ZiweiHourTests(unittest.TestCase):
    def test_zi_hour_starts_at_flow_day_ming(self):
        self.assertEqual(flow_hour_ming_branch(5, "戌", "酉", 1, 2, False, "子"), "辰")

    def test_chou_hour_moves_forward_one_palace(self):
        self.assertEqual(flow_hour_ming_branch(5, "戌", "酉", 1, 2, False, "丑"), "巳")

    def test_noon_hour_moves_forward_six_palaces(self):
        self.assertEqual(flow_hour_ming_branch(5, "戌", "酉", 1, 2, False, "午"), "戌")

    def test_hai_hour_moves_forward_eleven_palaces(self):
        self.assertEqual(flow_hour_ming_branch(5, "戌", "酉", 1, 2, False, "亥"), "卯")

    def test_palace_map_anchors_at_flow_hour_ming(self):
        palaces = flow_hour_palaces("巳")
        self.assertEqual(palaces["命宮"], "巳")
        self.assertEqual(palaces["兄弟宮"], "辰")
        self.assertEqual(palaces["父母宮"], "午")

    def test_civil_time_strings_are_rejected(self):
        for value in ("14:00", "下午兩點", "2pm", ""):
            with self.assertRaises(ValueError):
                flow_hour_ming_branch(5, "戌", "酉", 1, 2, False, value)

    def test_leap_month_hour_inherits_day_without_resetting_day_count(self):
        self.assertEqual(flow_hour_ming_branch(5, "戌", "酉", 5, 15, True, "子"), "酉")
        self.assertEqual(flow_hour_ming_branch(5, "戌", "酉", 5, 16, True, "子"), "亥")

    def test_structured_output_marks_project_derived_hour_scope(self):
        result = project_derived_ziwei_hour(5, "戌", "酉", 1, 2, False, "丑")
        self.assertEqual(result["classification"], "Project 推導盤面")
        self.assertEqual(result["scope"], "紫微流時")
        self.assertEqual(result["flow_month_ming_branch"], "卯")
        self.assertEqual(result["flow_day_ming_branch"], "辰")
        self.assertEqual(result["flow_hour_ming_branch"], "巳")
        self.assertTrue(result["features"]["flow_hour_implemented"])
        self.assertFalse(result["features"]["flow_hour_default_routing"])
        self.assertFalse(result["features"]["hourly_four_transformations_implemented"])
        self.assertFalse(result["features"]["hourly_flowing_stars_implemented"])
        self.assertFalse(result["features"]["fine_flying_implemented"])
        self.assertTrue(result["features"]["calendar_resolver_implemented"])


if __name__ == "__main__":
    unittest.main()
