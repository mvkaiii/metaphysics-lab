import copy
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from engine.distribution.errors import DistributionError
from engine.distribution.forecast import _select_bazi_current_decadal
from engine.distribution.runtime import dispatch


BIRTH = {
    "sex": "female",
    "birth_date": "1990-05-17",
    "birth_time": "10:20",
    "birth_place": "台北市",
}

RESOLVED_TAIPEI = {
    "canonical_name": "Taipei City, Taiwan",
    "latitude": 25.033,
    "longitude": 121.5654,
    "timezone": "Asia/Taipei",
    "provider_name": "ai_host",
    "provider_version": "synthetic-test",
    "provider_reference": None,
}


class DistributionForecastStructuralContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        built = dispatch(
            "build_natal",
            {"birth": BIRTH, "resolved_location": RESOLVED_TAIPEI},
        )
        if not built.get("ok"):
            raise AssertionError(built)
        cls.normalized = built["data"]["normalized_natal"]

    def test_forecast_context_carries_read_only_bazi_structural_context(self):
        result = dispatch(
            "resolve_forecast_context",
            {
                "normalized_natal": self.normalized,
                "target": {
                    "civil_datetime": "2027-08-18T14:30:00",
                    "timezone": "Asia/Taipei",
                },
                "requested_scopes": ["yearly", "monthly"],
            },
        )
        self.assertTrue(result["ok"], result)
        bazi = result["data"]["bazi"]
        structural = bazi["structural_context"]
        stored = self.normalized["project"]["bazi"]
        self.assertEqual(structural["day_master"], stored["day_master"])
        self.assertEqual(structural["natal_pillars"], stored["pillars"])
        current = structural["current_decadal"]
        self.assertIsNotNone(current)
        target = datetime.fromisoformat(bazi["datetime"])
        self.assertLessEqual(datetime.fromisoformat(current["start_datetime"]), target)
        self.assertLess(target, datetime.fromisoformat(current["end_datetime"]))
        self.assertTrue(current["pillar"])
        self.assertTrue(current["ten_god"])
        self.assertEqual(
            structural["decadal_boundaries_in_flow_year"],
            sorted(set(structural["decadal_boundaries_in_flow_year"])),
        )

    def test_current_decadal_selection_is_half_open(self):
        bazi = {
            "day_master": "丙",
            "decadal_periods": [
                {
                    "index": 1,
                    "pillar": "甲子",
                    "start_datetime": "2020-01-01T00:00:00+08:00",
                    "end_datetime": "2030-01-01T00:00:00+08:00",
                },
                {
                    "index": 2,
                    "pillar": "乙丑",
                    "start_datetime": "2030-01-01T00:00:00+08:00",
                    "end_datetime": "2040-01-01T00:00:00+08:00",
                },
            ],
        }
        boundary = datetime(2030, 1, 1, tzinfo=ZoneInfo("Asia/Taipei"))
        selected = _select_bazi_current_decadal(bazi, boundary)
        self.assertEqual(selected["index"], 2)
        self.assertEqual(selected["pillar"], "乙丑")

    def test_overlapping_stored_decadal_periods_fail_closed(self):
        bazi = {
            "day_master": "丙",
            "decadal_periods": [
                {
                    "index": 1,
                    "pillar": "甲子",
                    "start_datetime": "2020-01-01T00:00:00+08:00",
                    "end_datetime": "2031-01-01T00:00:00+08:00",
                },
                {
                    "index": 2,
                    "pillar": "乙丑",
                    "start_datetime": "2030-01-01T00:00:00+08:00",
                    "end_datetime": "2040-01-01T00:00:00+08:00",
                },
            ],
        }
        target = datetime(2030, 6, 1, tzinfo=ZoneInfo("Asia/Taipei"))
        with self.assertRaises(DistributionError) as caught:
            _select_bazi_current_decadal(copy.deepcopy(bazi), target)
        self.assertEqual(caught.exception.code, "forecast_basis_blocked")
        self.assertEqual(
            caught.exception.details["reason"],
            "overlapping_bazi_decadal_periods",
        )


if __name__ == "__main__":
    unittest.main()
