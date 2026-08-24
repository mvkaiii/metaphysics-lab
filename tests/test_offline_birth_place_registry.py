import json
import unittest
from pathlib import Path

from engine.birth.errors import BirthFoundationError


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "data" / "birth_places" / "registry.v1.json"

TAIWAN_CANONICAL = {
    "Taipei City", "New Taipei City", "Taoyuan City", "Taichung City",
    "Tainan City", "Kaohsiung City", "Keelung City", "Hsinchu City",
    "Chiayi City", "Hsinchu County", "Miaoli County", "Changhua County",
    "Nantou County", "Yunlin County", "Chiayi County", "Pingtung County",
    "Yilan County", "Hualien County", "Taitung County", "Penghu County",
    "Kinmen County", "Lienchiang County",
}

INTERNATIONAL_CANONICAL = {
    "Tokyo", "Osaka", "Seoul", "Hong Kong", "Singapore", "Kuala Lumpur",
    "Bangkok", "Beijing", "Shanghai", "New York City", "Los Angeles",
    "San Francisco", "Vancouver", "Toronto", "London", "Paris", "Sydney",
    "Melbourne",
}


def _load_registry_json():
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


class OfflineBirthPlaceRegistryTests(unittest.TestCase):
    def test_committed_registry_has_exact_v1_coverage(self):
        raw = _load_registry_json()
        self.assertEqual(raw["version"], "1.0")
        self.assertEqual(raw["coverage_profile"], "taiwan-admin1-plus-explicit-major-cities-v1")
        records = raw["records"]
        self.assertEqual(len(records), 40)
        taiwan = {row["canonical_name"] for row in records if row["country_code"] == "TW"}
        international = {row["canonical_name"] for row in records if row["country_code"] != "TW"}
        self.assertEqual(taiwan, TAIWAN_CANONICAL)
        self.assertEqual(international, INTERNATIONAL_CANONICAL)

    def test_registry_records_have_valid_required_fields_and_geonames_provenance(self):
        raw = _load_registry_json()
        record_ids = set()
        for row in raw["records"]:
            self.assertIsInstance(row["record_id"], str)
            self.assertTrue(row["record_id"].strip())
            self.assertNotIn(row["record_id"], record_ids)
            record_ids.add(row["record_id"])
            self.assertTrue(str(row["canonical_name"]).strip())
            self.assertRegex(row["country_code"], r"^[A-Z]{2}$")
            self.assertIn("admin_area", row)
            self.assertIsInstance(row["latitude"], (int, float))
            self.assertIsInstance(row["longitude"], (int, float))
            self.assertGreaterEqual(row["latitude"], -90)
            self.assertLessEqual(row["latitude"], 90)
            self.assertGreaterEqual(row["longitude"], -180)
            self.assertLessEqual(row["longitude"], 180)
            self.assertTrue(str(row["timezone"]).strip())
            self.assertIsInstance(row["aliases"], list)
            self.assertTrue(row["aliases"])
            self.assertEqual(row["source"], "geonames-curated")
            self.assertEqual(row["source_version"], "2026-08-24")
            self.assertRegex(row["source_reference"], r"^geonames:\d+$")

    def test_all_taiwan_records_use_asia_taipei(self):
        for row in _load_registry_json()["records"]:
            if row["country_code"] == "TW":
                self.assertEqual(row["timezone"], "Asia/Taipei", row["canonical_name"])

    def test_taipei_explicit_aliases_resolve_to_same_record_with_stable_provenance(self):
        from engine.birth.offline_registry import resolve_offline_birth_place

        values = ["台北", "臺北", "台北市", "臺北市", "Taipei", "Taipei City"]
        results = [resolve_offline_birth_place(value) for value in values]
        self.assertTrue(all(result is not None for result in results))
        first = results[0]
        self.assertTrue(all(result.canonical_name == first.canonical_name for result in results))
        self.assertEqual(first.canonical_name, "Taipei City")
        self.assertEqual(first.timezone, "Asia/Taipei")
        self.assertEqual(first.provider_name, "metaphysics_lab_offline_registry")
        self.assertEqual(first.provider_version, "1.0")
        self.assertEqual(first.resolution_status, "resolved")
        self.assertEqual(
            first.provider_reference,
            "tw-geonames-1668338|geonames:1668338",
        )

    def test_registry_metadata_is_exact_and_does_not_expose_alias_payload(self):
        from engine.birth.offline_registry import offline_birth_place_registry_metadata

        metadata = offline_birth_place_registry_metadata()
        self.assertEqual(metadata["version"], "1.0")
        self.assertEqual(metadata["record_count"], 40)
        self.assertEqual(
            metadata["coverage_profile"],
            "taiwan-admin1-plus-explicit-major-cities-v1",
        )
        self.assertEqual(metadata["source_profiles"], ["geonames-curated-2026-08-24"])
        self.assertNotIn("records", metadata)
        self.assertNotIn("aliases", metadata)

    def test_normalization_is_conservative_and_deterministic(self):
        from engine.birth.offline_registry import normalize_birth_place_alias

        self.assertEqual(normalize_birth_place_alias("  Ｔａｉｐｅｉ－Ｃｉｔｙ  "), "taipei city")
        self.assertEqual(normalize_birth_place_alias("Taipei_City"), "taipei city")
        self.assertEqual(normalize_birth_place_alias("Taipei   City"), "taipei city")
        self.assertNotEqual(normalize_birth_place_alias("Taipie"), "taipei")
        self.assertNotEqual(normalize_birth_place_alias("東京"), normalize_birth_place_alias("Tokyo"))

    def test_unlisted_fuzzy_or_implicit_translation_does_not_match(self):
        from engine.birth.offline_registry import resolve_offline_birth_place

        self.assertIsNone(resolve_offline_birth_place("Taipie"))
        self.assertIsNone(resolve_offline_birth_place("Taipei-ish"))

    def test_committed_short_chiayi_and_hsinchu_aliases_fail_closed(self):
        from engine.birth.offline_registry import resolve_offline_birth_place

        expected = {
            "Chiayi": {"Chiayi City", "Chiayi County"},
            "嘉義": {"Chiayi City", "Chiayi County"},
            "Hsinchu": {"Hsinchu City", "Hsinchu County"},
            "新竹": {"Hsinchu City", "Hsinchu County"},
        }
        for alias, names in expected.items():
            with self.subTest(alias=alias):
                with self.assertRaises(BirthFoundationError) as caught:
                    resolve_offline_birth_place(alias)
                self.assertEqual(caught.exception.code, "ambiguous_birth_place")
                self.assertEqual(caught.exception.details["candidate_count"], 2)
                self.assertEqual(
                    {row["canonical_name"] for row in caught.exception.details["candidates"]},
                    names,
                )

    def test_synthetic_duplicate_alias_fails_closed_with_all_candidates(self):
        from engine.birth.offline_registry import OfflineBirthPlaceRegistry

        records = [
            {
                "record_id": "test-a",
                "canonical_name": "Alpha",
                "country_code": "AA",
                "admin_area": "A",
                "latitude": 1.0,
                "longitude": 2.0,
                "timezone": "Etc/UTC",
                "aliases": ["shared"],
                "source": "synthetic-test",
                "source_version": "1",
                "source_reference": "a",
            },
            {
                "record_id": "test-b",
                "canonical_name": "Beta",
                "country_code": "BB",
                "admin_area": "B",
                "latitude": 3.0,
                "longitude": 4.0,
                "timezone": "Etc/UTC",
                "aliases": ["shared"],
                "source": "synthetic-test",
                "source_version": "1",
                "source_reference": "b",
            },
        ]
        registry = OfflineBirthPlaceRegistry(
            version="test",
            coverage_profile="synthetic",
            records=records,
        )
        with self.assertRaises(BirthFoundationError) as caught:
            registry.resolve("shared")
        self.assertEqual(caught.exception.code, "ambiguous_birth_place")
        self.assertEqual(caught.exception.details["candidate_count"], 2)
        self.assertEqual(
            {row["record_id"] for row in caught.exception.details["candidates"]},
            {"test-a", "test-b"},
        )

    def test_duplicate_normalized_alias_within_one_record_is_rejected(self):
        from engine.birth.offline_registry import OfflineBirthPlaceRegistry

        record = {
            "record_id": "dup",
            "canonical_name": "Duplicate",
            "country_code": "AA",
            "admin_area": "A",
            "latitude": 1.0,
            "longitude": 2.0,
            "timezone": "Etc/UTC",
            "aliases": ["Foo-Bar", "foo bar"],
            "source": "synthetic-test",
            "source_version": "1",
            "source_reference": "dup",
        }
        with self.assertRaises(ValueError):
            OfflineBirthPlaceRegistry(version="test", coverage_profile="synthetic", records=[record])


if __name__ == "__main__":
    unittest.main()
