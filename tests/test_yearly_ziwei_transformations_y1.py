import unittest

from engine.distribution.runtime import dispatch


BIRTH = {
    "sex": "male",
    "birth_date": "1984-03-13",
    "birth_time": "19:20",
    "birth_place": "台北市",
}

RESOLVED_TAIPEI = {
    "canonical_name": "Taipei City, Taiwan",
    "latitude": 25.033,
    "longitude": 121.5654,
    "timezone": "Asia/Taipei",
    "provider_name": "ai_host",
    "provider_version": "user-confirmed",
    "provider_reference": None,
}

SOURCE_ORACLE = {
    2025: [
        ("祿", "天機", "夫妻宮"),
        ("權", "天梁", "命宮"),
        ("科", "紫微", "兄弟宮"),
        ("忌", "太陰", "財帛宮"),
    ],
    2026: [
        ("祿", "天同", "遷移宮"),
        ("權", "天機", "夫妻宮"),
        ("科", "文昌", "疾厄宮"),
        ("忌", "廉貞", "田宅宮"),
    ],
    2027: [
        ("祿", "太陰", "財帛宮"),
        ("權", "天同", "遷移宮"),
        ("科", "天機", "夫妻宮"),
        ("忌", "巨門", "夫妻宮"),
    ],
}


class YearlyZiweiTransformationsY1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        natal = dispatch(
            "build_natal",
            {"birth": BIRTH, "resolved_location": RESOLVED_TAIPEI},
        )
        if not natal.get("ok"):
            raise AssertionError(natal)
        cls.normalized = natal["data"]["normalized_natal"]

    def yearly_edges(self, year):
        forecast = dispatch(
            "resolve_forecast_context",
            {
                "normalized_natal": self.normalized,
                "target": {
                    "civil_datetime": f"{year}-06-15T12:00:00",
                    "timezone": "Asia/Taipei",
                },
                "requested_scopes": ["yearly"],
            },
        )
        self.assertTrue(forecast["ok"], forecast)
        layer = forecast["data"]["ziwei"]["yearly"]
        transform = layer["transformation_layer"]
        flowing = layer["flowing_star_layer"]
        self.assertEqual(transform["identity"]["reference"], flowing["source"]["reference"])
        self.assertEqual(transform["source"]["heavenly_stem"], flowing["source"]["heavenly_stem"])
        return [
            (
                edge["transformation_type"],
                edge["star"],
                edge["target_palace"],
            )
            for edge in transform["flying_edges"]
        ]

    def test_2025_2027_match_available_astralium_yearly_oracle(self):
        for year, expected in SOURCE_ORACLE.items():
            with self.subTest(year=year):
                self.assertEqual(self.yearly_edges(year), expected)

    def test_repeated_forecast_is_deterministic(self):
        for year in sorted(SOURCE_ORACLE):
            with self.subTest(year=year):
                self.assertEqual(self.yearly_edges(year), self.yearly_edges(year))


if __name__ == "__main__":
    unittest.main()
