import json
import unittest
from pathlib import Path

from tools.qualify_birth_location_provider import PUBLIC_CASES, build_summary


SUMMARY_PATH = Path("qualification/birth/location-provider-summary.json")
FORBIDDEN_KEYS = {"full_address", "birth_datetime", "person_name", "raw_response"}


def walk_keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from walk_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk_keys(item)


class BirthLocationQualificationTests(unittest.TestCase):
    def test_public_cases_contain_no_private_birth_records(self):
        self.assertEqual(
            PUBLIC_CASES,
            (
                "台北市, 台灣",
                "高雄市, 台灣",
                "Tokyo, Japan",
                "New York, NY, USA",
                "London, UK",
            ),
        )

    def test_committed_summary_schema_is_privacy_safe(self):
        payload = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], "1.0")
        self.assertEqual(payload["classification"], "public_location_qualification")
        self.assertEqual(set(payload["queries"]), set(PUBLIC_CASES))
        self.assertTrue(FORBIDDEN_KEYS.isdisjoint(set(walk_keys(payload))))

    def test_summary_builder_rounds_coordinates_and_counts_results(self):
        records = [
            {
                "query": "台北市, 台灣",
                "status": "PASS",
                "latitude": 25.0375199,
                "longitude": 121.5636799,
                "timezone": "Asia/Taipei",
            },
            {
                "query": "London, UK",
                "status": "FAIL",
                "latitude": None,
                "longitude": None,
                "timezone": None,
            },
        ]
        summary = build_summary(records, provider_name="fixture", provider_version="1", generated_at="2026-08-22T00:00:00Z")
        self.assertEqual(summary["pass_count"], 1)
        self.assertEqual(summary["fail_count"], 1)
        self.assertEqual(summary["results"][0]["latitude"], 25.0375)
        self.assertEqual(summary["results"][0]["longitude"], 121.5637)
        self.assertTrue(FORBIDDEN_KEYS.isdisjoint(set(walk_keys(summary))))


if __name__ == "__main__":
    unittest.main()
