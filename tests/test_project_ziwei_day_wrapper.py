import unittest

from engine.project_ziwei_day import project_derived_ziwei_day as legacy_day
from engine.ziwei.day import project_derived_ziwei_day as modular_day


class ZiweiDayWrapperTests(unittest.TestCase):
    def test_wrapper_matches_modular_day(self):
        kwargs = dict(
            birth_lunar_month=5,
            birth_hour_branch="戌",
            flow_year_branch="酉",
            lunar_month=1,
            lunar_day=2,
            is_leap_month=False,
        )
        self.assertEqual(legacy_day(**kwargs), modular_day(**kwargs))


if __name__ == "__main__":
    unittest.main()
