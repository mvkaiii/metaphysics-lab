import copy
import unittest

from engine.distribution.runtime import dispatch
from engine.historical.selector import select_historical_activation


BIRTH = {
    "sex": "male",
    "birth_date": "1984-03-13",
    "birth_time": "19:20",
    "birth_place": "台北市",
}

LOCATION = {
    "canonical_name": "Taipei City, Taiwan",
    "latitude": 25.033,
    "longitude": 121.5654,
    "timezone": "Asia/Taipei",
    "provider_name": "ai_host",
    "provider_version": "user-confirmed",
    "provider_reference": None,
}


class HistoricalZiweiSupportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        built = dispatch(
            "build_natal",
            {"birth": BIRTH, "resolved_location": LOCATION},
        )
        if not built.get("ok"):
            raise AssertionError(built)
        cls.normalized = built["data"]["normalized_natal"]
        cls.payload = {
            "normalized_natal": cls.normalized,
            "as_of_datetime": "2026-08-23T10:55:00+08:00",
            "timezone": "Asia/Taipei",
        }

    def test_prepare_attaches_support_only_for_canonical_five_without_changing_digest(self):
        canonical = select_historical_activation(self.payload)
        prepared = dispatch("prepare_historical_calibration", self.payload)
        self.assertTrue(prepared["ok"], prepared)
        data = prepared["data"]

        self.assertEqual(data["selection_digest"], canonical["selection_digest"])
        self.assertEqual(
            [row["label_year"] for row in data["high_years"]],
            [row["label_year"] for row in canonical["high_years"]],
        )
        self.assertEqual(data["control_year"]["label_year"], canonical["control_year"]["label_year"])

        support = data["ziwei_support"]
        self.assertEqual(support["status"], "available")
        self.assertEqual(support["role"], "support_only")
        self.assertFalse(support["ranking_authority"])
        expected_years = [row["label_year"] for row in canonical["high_years"]]
        expected_years.append(canonical["control_year"]["label_year"])
        self.assertEqual([row["label_year"] for row in support["years"]], expected_years)
        for row in support["years"]:
            self.assertEqual(row["scope"], "yearly")
            self.assertEqual(row["classification"], "Project 推導盤面")
            self.assertEqual(row["maturity"], "experimental")
            self.assertTrue(row["reference"])
            self.assertIn("flowing_star_layer", row)

    def test_missing_ziwei_downgrades_support_without_changing_bazi_selection(self):
        normal = dispatch("prepare_historical_calibration", self.payload)
        self.assertTrue(normal["ok"], normal)

        bazi_only = copy.deepcopy(self.normalized)
        bazi_only["project"]["ziwei"] = {}
        degraded_payload = dict(self.payload)
        degraded_payload["normalized_natal"] = bazi_only
        degraded = dispatch("prepare_historical_calibration", degraded_payload)
        self.assertTrue(degraded["ok"], degraded)

        self.assertEqual(
            degraded["data"]["selection_digest"],
            normal["data"]["selection_digest"],
        )
        self.assertEqual(
            [row["label_year"] for row in degraded["data"]["high_years"]],
            [row["label_year"] for row in normal["data"]["high_years"]],
        )
        self.assertEqual(
            degraded["data"]["control_year"]["label_year"],
            normal["data"]["control_year"]["label_year"],
        )
        support = degraded["data"]["ziwei_support"]
        self.assertEqual(support["status"], "unavailable")
        self.assertEqual(support["role"], "support_only")
        self.assertFalse(support["ranking_authority"])
        self.assertTrue(support["reason"])


if __name__ == "__main__":
    unittest.main()
