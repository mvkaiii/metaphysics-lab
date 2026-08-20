import unittest

from engine.ziwei import flow_day_ming_branch, project_derived_ziwei_day, get_capability


class ZiweiPackageExportsTests(unittest.TestCase):
    def test_flow_day_exports(self):
        self.assertEqual(flow_day_ming_branch(5, "戌", "酉", 1, 2, False), "辰")
        self.assertEqual(project_derived_ziwei_day(5, "戌", "酉", 1, 2, False)["scope"], "紫微流日")
        self.assertEqual(get_capability("ziwei.flow_day_palaces")["routing"], "on_demand")


if __name__ == "__main__":
    unittest.main()
