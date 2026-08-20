import unittest

import engine.ziwei as ziwei
from engine.ziwei import get_capability, flow_month_ming_branch
from engine.ziwei.day import flow_day_ming_branch
from engine.ziwei.hour import flow_hour_ming_branch


class ZiweiPackageExportsTests(unittest.TestCase):
    def test_package_keeps_stable_root_exports_and_fine_timing_uses_explicit_modules(self):
        self.assertEqual(flow_month_ming_branch(5, "戌", "酉", 1, 1, False), "卯")
        self.assertEqual(flow_day_ming_branch(5, "戌", "酉", 1, 2, False), "辰")
        self.assertEqual(flow_hour_ming_branch(5, "戌", "酉", 1, 2, False, "丑"), "巳")
        self.assertEqual(get_capability("ziwei.flow_hour_palaces")["routing"], "on_demand")
        self.assertFalse(hasattr(ziwei, "flow_hour_ming_branch"))


if __name__ == "__main__":
    unittest.main()
