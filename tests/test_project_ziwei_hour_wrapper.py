import unittest

from engine.project_ziwei_hour import project_derived_ziwei_hour as legacy_hour
from engine.ziwei.hour import project_derived_ziwei_hour as modular_hour


class ZiweiHourWrapperTests(unittest.TestCase):
    def test_wrapper_matches_modular_hour(self):
        kwargs = dict(
            birth_lunar_month=5,
            birth_hour_branch="戌",
            flow_year_branch="酉",
            lunar_month=1,
            lunar_day=2,
            is_leap_month=False,
            hour_branch="丑",
        )
        self.assertEqual(legacy_hour(**kwargs), modular_hour(**kwargs))


if __name__ == "__main__":
    unittest.main()
