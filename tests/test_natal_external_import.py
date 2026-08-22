import unittest

from engine.natal.errors import NatalFoundationError
from engine.natal.external import import_external_natal
from engine.natal.models import NatalSource


class NatalExternalImportTests(unittest.TestCase):
    def setUp(self):
        self.source = NatalSource(
            source_type="external",
            source_name="Astralium",
            source_version="synthetic-public",
            rule_profile="astralium-imported",
            rule_version="unknown",
            maturity="external",
            validation_status="provided",
        )

    def full_payload(self):
        return {
            "birth": {
                "reported_datetime": "1984-03-13T19:20:00+08:00",
                "place_label": "Taipei City",
            },
            "bazi": {
                "pillars": {
                    "year": "甲子",
                    "month": "丁卯",
                    "day": "丙辰",
                    "hour": "戊戌",
                }
            },
            "ziwei": {
                "ming_palace": "夫妻",
                "body_palace": "命宮",
                "five_element_bureau": "水二局",
                "palaces": [
                    {"name": "命宮", "branch": "戌", "heavenly_stem": "甲"},
                    {"name": "夫妻", "branch": "辰", "heavenly_stem": "庚"},
                ],
                "stars": [
                    {"star": "紫微", "palace": "夫妻", "brightness": "旺"},
                    {"star": "天機", "palace": "命宮", "brightness": "平"},
                ],
                "birth_transformations": {
                    "祿": "廉貞",
                    "權": "破軍",
                    "科": "武曲",
                    "忌": "太陽",
                },
                "decadal_cycles": [
                    {"index": 1, "palace": "命宮", "start_age": 2, "end_age": 11}
                ],
            },
        }

    def test_imports_structured_astralium_shaped_payload_and_preserves_source(self):
        view = import_external_natal(self.full_payload(), self.source)
        self.assertEqual(view.source.source_name, "Astralium")
        self.assertEqual(view.source.source_version, "synthetic-public")
        self.assertEqual(view.source.source_type, "external")
        self.assertEqual(view.birth["reported_datetime"], "1984-03-13T19:20:00+08:00")
        self.assertEqual(view.bazi["pillars"]["day"], "丙辰")
        self.assertEqual(view.ziwei["ming_palace"], "夫妻")
        self.assertEqual(view.ziwei["stars"][0]["star"], "紫微")

    def test_partial_external_chart_does_not_synthesize_missing_fields(self):
        payload = {
            "birth": {"reported_datetime": "1984-03-13T19:20:00+08:00"},
            "ziwei": {"ming_palace": "夫妻"},
        }
        view = import_external_natal(payload, self.source)
        self.assertEqual(dict(view.bazi), {})
        self.assertEqual(dict(view.ziwei), {"ming_palace": "夫妻"})
        self.assertNotIn("stars", view.ziwei)
        self.assertNotIn("palaces", view.ziwei)

    def test_duplicate_palace_names_are_invalid_schema(self):
        payload = self.full_payload()
        payload["ziwei"]["palaces"] = [
            {"name": "命宮", "branch": "戌"},
            {"name": "命宮", "branch": "亥"},
        ]
        with self.assertRaises(NatalFoundationError) as caught:
            import_external_natal(payload, self.source)
        self.assertEqual(caught.exception.code, "invalid_natal_schema")

    def test_duplicate_unique_star_identities_are_invalid_schema(self):
        payload = self.full_payload()
        payload["ziwei"]["stars"] = [
            {"star": "紫微", "palace": "命宮"},
            {"star": "紫微", "palace": "夫妻"},
        ]
        with self.assertRaises(NatalFoundationError) as caught:
            import_external_natal(payload, self.source)
        self.assertEqual(caught.exception.code, "invalid_natal_schema")

    def test_malformed_four_pillars_are_invalid_schema(self):
        payload = self.full_payload()
        payload["bazi"]["pillars"]["hour"] = "XYZ"
        with self.assertRaises(NatalFoundationError) as caught:
            import_external_natal(payload, self.source)
        self.assertEqual(caught.exception.code, "invalid_natal_schema")

    def test_unknown_source_classification_is_invalid_schema(self):
        source = NatalSource(
            source_type="mystery",
            source_name="Unknown",
            source_version="1",
            rule_profile="unknown",
            rule_version="unknown",
            maturity="external",
            validation_status="provided",
        )
        with self.assertRaises(NatalFoundationError) as caught:
            import_external_natal(self.full_payload(), source)
        self.assertEqual(caught.exception.code, "invalid_natal_schema")

    def test_unstructured_payload_shapes_are_rejected_not_parsed(self):
        for payload in (
            "# Astralium chart markdown",
            {"birth": [], "bazi": {}, "ziwei": {}},
            {"birth": {}, "bazi": {"pillars": "甲子 丁卯 丙辰 戊戌"}, "ziwei": {}},
        ):
            with self.assertRaises(NatalFoundationError) as caught:
                import_external_natal(payload, self.source)
            self.assertEqual(caught.exception.code, "invalid_natal_schema")


if __name__ == "__main__":
    unittest.main()
