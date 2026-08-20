import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from engine.project_bazi_calendar import bazi_pillars as legacy_bazi_pillars
from engine.project_ziwei_month import project_derived_ziwei_month as legacy_ziwei_month
from engine.bazi.calendar import bazi_pillars as modular_bazi_pillars
from engine.ziwei.common import ZHI, PALACE_NAMES
from engine.ziwei.month import project_derived_ziwei_month as modular_ziwei_month


class EngineModuleLayoutTests(unittest.TestCase):
    def test_bazi_modular_path_matches_legacy_path(self):
        dt = datetime(2026, 8, 20, 17, 12, tzinfo=ZoneInfo("Asia/Taipei"))
        self.assertEqual(modular_bazi_pillars(dt), legacy_bazi_pillars(dt))

    def test_ziwei_modular_path_matches_legacy_path(self):
        kwargs = dict(
            birth_lunar_month=5,
            birth_hour_branch="戌",
            flow_year_branch="酉",
            lunar_month=2,
            lunar_day=1,
            is_leap_month=False,
        )
        self.assertEqual(modular_ziwei_month(**kwargs), legacy_ziwei_month(**kwargs))

    def test_ziwei_common_owns_shared_constants(self):
        self.assertEqual(ZHI, tuple("子丑寅卯辰巳午未申酉戌亥"))
        self.assertEqual(PALACE_NAMES[0], "命宮")
        self.assertEqual(PALACE_NAMES[-1], "父母宮")


if __name__ == "__main__":
    unittest.main()
