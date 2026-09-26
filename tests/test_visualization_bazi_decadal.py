import copy
import json
import unittest
from pathlib import Path

from engine.distribution.manifest import capability_manifest_digest, load_capability_manifest
from engine.visualization.bazi_decadal import canonical_json_bytes, project_bazi_decadal
from engine.visualization.contract import validate_chart


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "visualization" / "bazi-decadal-engine-view.v1.json"


def _fixture():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


class BaziDecadalVisualizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load_capability_manifest()

    def test_projection_preserves_engine_period_values(self):
        fixture = _fixture()
        chart = project_bazi_decadal(
            fixture, self.manifest,
            as_of="2005-01-01T00:00:00+08:00",
            timezone="Asia/Taipei",
            visibility_mode="blind",
        )
        self.assertEqual(chart["status"], "ready")
        self.assertEqual(validate_chart(chart), [])
        source = fixture["project_natal"]["bazi"]["decadal_periods"]
        actual = chart["data"]["periods"]
        self.assertEqual([row["pillar"] for row in actual], [row["pillar"] for row in source])
        self.assertEqual([row["start_at"] for row in actual], [row["start_datetime"] for row in source])
        self.assertEqual([row["age_start_years"] for row in actual], [row["start_age_years"] for row in source])

    def test_as_of_at_boundary_selects_next_period_once(self):
        fixture = _fixture()
        boundary = fixture["project_natal"]["bazi"]["decadal_periods"][0]["end_datetime"]
        chart = project_bazi_decadal(
            fixture, self.manifest, as_of=boundary, timezone="Asia/Taipei", visibility_mode="blind"
        )
        self.assertEqual(chart["data"]["current_period_id"], "period-2")
        self.assertEqual(
            sum(period["id"] == chart["data"]["current_period_id"] for period in chart["data"]["periods"]),
            1,
        )

    def test_outside_range_has_no_current_period(self):
        fixture = _fixture()
        chart = project_bazi_decadal(
            fixture, self.manifest, as_of="2030-01-01T00:00:00+08:00", timezone="Asia/Taipei", visibility_mode="blind"
        )
        self.assertEqual(chart["status"], "ready")
        self.assertIsNone(chart["data"]["current_period_id"])

    def test_equivalent_offset_is_stable_at_boundary(self):
        fixture = _fixture()
        chart = project_bazi_decadal(
            fixture,
            self.manifest,
            as_of="2001-07-29T05:41:19.800000+00:00",
            timezone="Asia/Taipei",
            visibility_mode="blind",
        )
        self.assertEqual(chart["data"]["current_period_id"], "period-2")

    def test_source_timezone_mismatch_is_unsupported(self):
        fixture = _fixture()
        chart = project_bazi_decadal(
            fixture,
            self.manifest,
            as_of="2005-01-01T00:00:00+00:00",
            timezone="UTC",
            visibility_mode="blind",
        )
        self.assertEqual(chart["status"], "unsupported")
        self.assertIn("SOURCE_TIMEZONE_MISMATCH", chart["reason_codes"])

    def test_unknown_interval_semantics_is_unsupported(self):
        fixture = _fixture()
        fixture["project_natal"]["bazi"]["profile"]["interval_semantics"] = "needs_confirmation"
        fixture["provenance"]["source_payload_sha256"] = __import__("hashlib").sha256(
            canonical_json_bytes(fixture["project_natal"])
        ).hexdigest()
        chart = project_bazi_decadal(
            fixture, self.manifest, as_of="2005-01-01T00:00:00+08:00", timezone="Asia/Taipei", visibility_mode="blind"
        )
        self.assertEqual(chart["status"], "unsupported")
        self.assertIn("UNKNOWN_INTERVAL_SEMANTICS", chart["reason_codes"])
        self.assertEqual(validate_chart(chart), [])

    def test_ambiguous_candidate_is_unsupported(self):
        fixture = _fixture()
        fixture["resolved_candidate_count"] = 2
        chart = project_bazi_decadal(
            fixture, self.manifest, as_of="2005-01-01T00:00:00+08:00", timezone="Asia/Taipei", visibility_mode="blind"
        )
        self.assertEqual(chart["status"], "unsupported")
        self.assertIn("AMBIGUOUS_NATAL_CANDIDATE", chart["reason_codes"])

    def test_missing_optional_ten_god_is_null_not_calculated(self):
        fixture = _fixture()
        chart = project_bazi_decadal(
            fixture, self.manifest, as_of="2005-01-01T00:00:00+08:00", timezone="Asia/Taipei", visibility_mode="blind"
        )
        period = chart["data"]["periods"][0]
        self.assertIsNone(period["ten_god"])
        self.assertIsNone(period["elements"])
        self.assertEqual(period["optional_reasons"]["ten_god"], "NO_QUALIFIED_SOURCE")

    def test_source_maturity_matches_manifest(self):
        fixture = _fixture()
        fixture["source_capabilities"][0]["maturity"] = "stable"
        chart = project_bazi_decadal(
            fixture, self.manifest, as_of="2005-01-01T00:00:00+08:00", timezone="Asia/Taipei", visibility_mode="blind"
        )
        self.assertEqual(chart["status"], "unsupported")
        self.assertIn("SOURCE_MATURITY_MISMATCH", chart["reason_codes"])

    def test_no_case_or_event_payload_leaks(self):
        fixture = _fixture()
        fixture["known_reality_context"] = {"event": "secret"}
        with self.assertRaises(ValueError):
            project_bazi_decadal(
                fixture, self.manifest, as_of="2005-01-01T00:00:00+08:00", timezone="Asia/Taipei", visibility_mode="blind"
            )

    def test_same_input_same_canonical_bytes(self):
        fixture = _fixture()
        first = project_bazi_decadal(
            fixture, self.manifest, as_of="2005-01-01T00:00:00+08:00", timezone="Asia/Taipei", visibility_mode="blind"
        )
        second = project_bazi_decadal(
            copy.deepcopy(fixture), copy.deepcopy(self.manifest), as_of="2005-01-01T00:00:00+08:00", timezone="Asia/Taipei", visibility_mode="blind"
        )
        self.assertEqual(canonical_json_bytes(first), canonical_json_bytes(second))
        self.assertEqual(first["provenance"]["manifest_sha256"], capability_manifest_digest(self.manifest))


if __name__ == "__main__":
    unittest.main()
