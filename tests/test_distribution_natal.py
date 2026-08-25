import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from engine.birth.errors import BirthFoundationError
from engine.birth.models import GeocodeCandidate, ResolvedBirthPlace
from engine.distribution.runtime import dispatch


ROOT = Path(__file__).resolve().parents[1]

RESOLVED_TAIPEI = {
    "canonical_name": "Taipei City, Taiwan",
    "latitude": 25.033,
    "longitude": 121.5654,
    "timezone": "Asia/Taipei",
    "provider_name": "ai_host",
    "provider_version": "user-confirmed",
    "provider_reference": None,
}

COMPLETE_BIRTH = {
    "sex": "male",
    "birth_date": "1984-03-13",
    "birth_time": "19:20",
    "birth_place": "台北市",
}


def offline_taipei():
    return ResolvedBirthPlace(
        canonical_name="Taipei City, Taiwan",
        latitude=25.033,
        longitude=121.5654,
        timezone="Asia/Taipei",
        provider_name="metaphysics_lab_offline_registry",
        provider_version="1.0",
        resolution_status="resolved_offline_registry",
        provider_reference="tw-tpe|geonames:1668341",
    )


class _SyntheticNetworkProvider:
    name = "synthetic-network"
    version = "test-1"

    def geocode(self, query):
        return (
            GeocodeCandidate(
                name="Synthetic Taipei, Taiwan",
                latitude=25.033,
                longitude=121.5654,
                country_code="tw",
                raw_id="synthetic:1",
            ),
        )


class DistributionNatalTests(unittest.TestCase):
    def test_incomplete_birth_returns_existing_resolution_details(self):
        result = dispatch(
            "build_natal",
            {
                "birth": {
                    "birth_date": "1984-03-13",
                    "birth_time": "19:20",
                    "birth_place": "台北市",
                },
                "resolved_location": RESOLVED_TAIPEI,
            },
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "missing_required_birth_field")
        self.assertEqual(result["error"]["details"]["missing_fields"], ["sex"])
        self.assertEqual(
            result["error"]["details"]["allowed_actions"],
            ["ask", "keep_candidates", "downgrade"],
        )

    def test_build_natal_uses_pre_resolved_location_and_returns_structured_facts(self):
        result = dispatch(
            "build_natal",
            {"birth": COMPLETE_BIRTH, "resolved_location": RESOLVED_TAIPEI},
        )
        self.assertTrue(result["ok"], result)
        data = result["data"]
        project = data["project_natal"]
        self.assertEqual(project["source"]["source_type"], "project")
        self.assertEqual(project["source"]["source_name"], "Metaphysics Lab")
        self.assertEqual(project["source"]["maturity"], "experimental")
        self.assertEqual(project["birth"]["resolved_place_label"], "Taipei City, Taiwan")
        self.assertEqual(project["time_basis"]["location_provider"], "ai_host")
        self.assertEqual(set(project["bazi"]["pillars"]), {"year", "month", "day", "hour"})
        self.assertEqual(len(project["ziwei"]["palaces"]), 12)
        self.assertEqual(data["resolved_location"]["timezone"], "Asia/Taipei")
        serialized = json.dumps(data, ensure_ascii=False).lower()
        self.assertNotIn("interpretation", serialized)
        self.assertNotIn("advice", serialized)

    def test_explicit_resolved_location_has_precedence_over_offline_registry(self):
        with patch(
            "engine.distribution.natal.resolve_offline_birth_place",
            side_effect=AssertionError("offline resolver must not run for explicit location"),
        ):
            result = dispatch(
                "build_natal",
                {"birth": COMPLETE_BIRTH, "resolved_location": RESOLVED_TAIPEI},
            )
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["data"]["resolved_location"]["provider_name"], "ai_host")

    def test_build_natal_uses_unique_offline_registry_match_before_network(self):
        with patch("engine.distribution.natal.resolve_offline_birth_place", return_value=offline_taipei()), patch(
            "engine.distribution.natal._network_provider",
            side_effect=AssertionError("network provider must not run after offline match"),
        ):
            result = dispatch("build_natal", {"birth": COMPLETE_BIRTH})
        self.assertTrue(result["ok"], result)
        location = result["data"]["resolved_location"]
        self.assertEqual(location["provider_name"], "metaphysics_lab_offline_registry")
        self.assertEqual(location["provider_version"], "1.0")
        self.assertEqual(location["timezone"], "Asia/Taipei")

    def test_birth_only_taipei_uses_committed_offline_registry_end_to_end(self):
        result = dispatch("build_natal", {"birth": COMPLETE_BIRTH})
        self.assertTrue(result["ok"], result)
        data = result["data"]
        location = data["resolved_location"]
        project = data["project_natal"]
        self.assertEqual(location["canonical_name"], "Taipei City")
        self.assertEqual(location["provider_name"], "metaphysics_lab_offline_registry")
        self.assertEqual(location["provider_version"], "1.0")
        self.assertEqual(location["timezone"], "Asia/Taipei")
        self.assertEqual(set(project["bazi"]["pillars"]), {"year", "month", "day", "hour"})
        self.assertEqual(len(project["ziwei"]["palaces"]), 12)
        self.assertIsNotNone(data["normalized_natal"]["project"])

    def test_offline_ambiguity_fails_without_network_fallback(self):
        ambiguity = BirthFoundationError(
            "ambiguous_birth_place",
            "offline birth-place alias matches multiple registry records",
            {"query": "Springfield", "candidate_count": 2, "candidates": []},
        )
        with patch("engine.distribution.natal.resolve_offline_birth_place", side_effect=ambiguity), patch(
            "engine.distribution.natal._network_provider",
            side_effect=AssertionError("ambiguous offline result must not fall through to network"),
        ):
            result = dispatch(
                "build_natal",
                {
                    "birth": dict(COMPLETE_BIRTH, birth_place="Springfield"),
                    "network_location": {"enabled": True, "user_agent": "portable-test"},
                },
            )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "ambiguous_birth_place")

    def test_offline_miss_without_network_returns_location_not_resolved(self):
        result = dispatch(
            "build_natal",
            {"birth": dict(COMPLETE_BIRTH, birth_place="Unsupported Place")},
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "location_not_resolved")
        self.assertEqual(result["error"]["details"]["query"], "Unsupported Place")

    def test_offline_miss_with_explicit_network_fallback_preserves_resolved_provenance(self):
        with patch("engine.distribution.natal._network_provider", return_value=_SyntheticNetworkProvider()):
            result = dispatch(
                "build_natal",
                {
                    "birth": dict(COMPLETE_BIRTH, birth_place="Unsupported Place"),
                    "network_location": {"enabled": True, "user_agent": "portable-test"},
                },
            )
        self.assertTrue(result["ok"], result)
        location = result["data"]["resolved_location"]
        self.assertEqual(location["canonical_name"], "Synthetic Taipei, Taiwan")
        self.assertEqual(location["latitude"], 25.033)
        self.assertEqual(location["longitude"], 121.5654)
        self.assertEqual(location["timezone"], "Asia/Taipei")
        self.assertEqual(location["provider_name"], "synthetic-network")
        self.assertEqual(location["provider_version"], "test-1")
        self.assertEqual(location["provider_reference"], "synthetic:1")
        self.assertEqual(location["resolution_status"], "resolved")

    def test_build_natal_pre_resolved_path_does_not_require_location_packages(self):
        script = r'''
import builtins
import json

real_import = builtins.__import__
def guarded(name, globals=None, locals=None, fromlist=(), level=0):
    if name == "geopy" or name.startswith("geopy.") or name == "timezonefinder" or name.startswith("timezonefinder."):
        raise ModuleNotFoundError("blocked optional location dependency: %s" % name)
    return real_import(name, globals, locals, fromlist, level)

builtins.__import__ = guarded
from engine.distribution.runtime import dispatch
payload = {
    "birth": {"sex": "male", "birth_date": "1984-03-13", "birth_time": "19:20", "birth_place": "台北市"},
    "resolved_location": {
        "canonical_name": "Taipei City, Taiwan",
        "latitude": 25.033,
        "longitude": 121.5654,
        "timezone": "Asia/Taipei",
        "provider_name": "ai_host",
        "provider_version": "user-confirmed",
        "provider_reference": None,
    },
}
result = dispatch("build_natal", payload)
if not result.get("ok"):
    raise AssertionError(json.dumps(result, ensure_ascii=False))
'''
        completed = subprocess.run(
            [sys.executable, "-c", script],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_invalid_pre_resolved_coordinates_are_rejected(self):
        invalid = dict(RESOLVED_TAIPEI)
        invalid["latitude"] = 91.0
        result = dispatch(
            "build_natal",
            {"birth": COMPLETE_BIRTH, "resolved_location": invalid},
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "invalid_resolved_location")

    def test_reconcile_natal_preserves_external_project_and_conflict(self):
        built = dispatch(
            "build_natal",
            {"birth": COMPLETE_BIRTH, "resolved_location": RESOLVED_TAIPEI},
        )
        self.assertTrue(built["ok"], built)
        project = built["data"]["project_natal"]
        pillars = copy.deepcopy(project["bazi"]["pillars"])
        pillars["day"] = "甲子" if pillars["day"] != "甲子" else "乙丑"
        external_chart = {
            "birth": {"reported_datetime": project["birth"]["reported_datetime"]},
            "bazi": {"pillars": pillars},
            "ziwei": {"ming_palace": project["ziwei"]["ming_palace"]},
        }
        external_source = {
            "source_type": "external",
            "source_name": "Synthetic External",
            "source_version": "public-test-v1",
            "rule_profile": "synthetic-imported",
            "rule_version": "1",
            "maturity": "external",
            "validation_status": "provided",
        }
        result = dispatch(
            "reconcile_natal",
            {
                "project_natal": project,
                "external_chart": external_chart,
                "external_source": external_source,
            },
        )
        self.assertTrue(result["ok"], result)
        normalized = result["data"]["normalized_natal"]
        self.assertIsNotNone(normalized["external"])
        self.assertIsNotNone(normalized["project"])
        conflicts = [
            field
            for field in normalized["resolved"]["fields"]
            if field["path"] == "bazi.pillars.day" and field["status"] == "CONFLICT"
        ]
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]["severity"], "BLOCKING")
        self.assertEqual(conflicts[0]["selected_source"], "external")
        self.assertEqual(normalized["external"]["source"]["source_name"], "Synthetic External")
        self.assertEqual(normalized["project"]["source"]["source_name"], "Metaphysics Lab")


if __name__ == "__main__":
    unittest.main()
