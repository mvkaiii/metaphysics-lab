import unittest

from engine.distribution.calibration import _selector_point_map


V2_PROFILE_ID = "historical-activation-bazi-v2"


def _row(year):
    return {"label_year": year}


def _selector(rule_version):
    return {
        "profile_id": V2_PROFILE_ID,
        "rule_version": rule_version,
        "high_years": [_row(2021), _row(2020), _row(2018), _row(2024)],
        "control_year": None,
        "control_selection": "abstain",
    }


class SelectorCalibrationCompatibilityTests(unittest.TestCase):
    def test_v2_21_abstention_is_accepted_by_historical_calibration(self):
        order, rows = _selector_point_map(_selector("2.1-exp"))
        self.assertEqual(order, [2021, 2020, 2018, 2024])
        self.assertEqual(sorted(rows), [2018, 2020, 2021, 2024])

    def test_v2_20_remains_readable_for_existing_locks(self):
        order, rows = _selector_point_map(_selector("2.0-exp"))
        self.assertEqual(order, [2021, 2020, 2018, 2024])
        self.assertEqual(sorted(rows), [2018, 2020, 2021, 2024])


if __name__ == "__main__":
    unittest.main()
