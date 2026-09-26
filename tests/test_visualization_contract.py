import copy
import json
import math
import unittest
from pathlib import Path

from engine.visualization.contract import validate_chart


ROOT = Path(__file__).resolve().parents[1]


def _provenance():
    return {
        "repo": "mvkaiii/metaphysics-lab",
        "source_commit": "8" * 40,
        "release_version": "1.7.1",
        "distribution_runtime_version": "1.2-exp",
        "manifest_sha256": "1" * 64,
        "source_payload_sha256": "2" * 64,
        "projection_version": "1.0-exp",
    }


def _ready_chart():
    return {
        "chart_type": "bazi_decadal_timeline",
        "schema_version": "1.0",
        "status": "ready",
        "reason_codes": [],
        "view_context": {
            "as_of": "2026-09-26T12:00:00+08:00",
            "timezone": "Asia/Taipei",
            "visibility_mode": "blind",
            "locale": "zh-TW",
        },
        "source_capabilities": [
            {
                "capability_id": "bazi.natal_chart",
                "scope": "decadal_periods",
                "profile_id": "bazi-natal-project-v1",
                "rule_version": "1.0-exp",
                "maturity": "experimental",
                "routing": "on_demand",
            }
        ],
        "data": {
            "age_basis": {
                "id": "continuous_years_from_jie_interval",
                "description": "Continuous years from the jie interval.",
                "rounding_policy": "preserve_source_precision",
            },
            "time_basis": {
                "calendar": "gregorian",
                "boundary_policy": "source_interval_only",
                "interval_convention": "[start_at,end_at)",
                "source_timezone": "Asia/Taipei",
            },
            "direction": "forward",
            "periods": [
                {
                    "id": "period-1",
                    "index": 1,
                    "pillar": "戊辰",
                    "age_start_years": 7.376851851851852,
                    "age_end_years": 17.376851851851853,
                    "start_at": "1991-07-30T03:29:19.800000+08:00",
                    "end_at": "2001-07-29T13:41:19.800000+08:00",
                    "ten_god": None,
                    "elements": None,
                    "optional_reasons": {
                        "ten_god": "NO_QUALIFIED_SOURCE",
                        "elements": "NO_QUALIFIED_SOURCE",
                    },
                    "authority_refs": {
                        "/pillar": ["period-1-derived"],
                        "/start_at": ["period-1-derived"],
                        "/end_at": ["period-1-derived"],
                    },
                }
            ],
            "current_period_id": "period-1",
            "year_overlays": [],
        },
        "annotations": [],
        "authorities": {
            "period-1-derived": {
                "classification": "project_derived",
                "source_refs": ["/provenance/source_payload_sha256"],
                "transformation": "serialized_engine_value",
                "confidence": None,
            }
        },
        "provenance": _provenance(),
        "limitations": [
            {
                "code": "EXPERIMENTAL_CAPABILITY",
                "message": "E：大運圖表維持Experimental，未代表Stable qualification。",
                "scope": "chart",
            },
            {
                "code": "OPTIONAL_FIELDS_UNAVAILABLE",
                "message": "十神與五行沒有合格的大運專屬來源。",
                "scope": "periods",
            },
        ],
    }


def _unsupported_chart():
    chart = _ready_chart()
    chart.update(
        {
            "status": "unsupported",
            "reason_codes": ["AMBIGUOUS_NATAL_CANDIDATE"],
            "source_capabilities": [],
            "data": None,
            "authorities": {},
            "provenance": {
                **_provenance(),
                "source_commit": None,
                "release_version": None,
                "distribution_runtime_version": None,
                "manifest_sha256": None,
                "source_payload_sha256": None,
            },
        }
    )
    return chart


class VisualizationContractTests(unittest.TestCase):
    def test_valid_ready_chart_is_accepted(self):
        self.assertEqual(validate_chart(_ready_chart()), [])

    def test_unknown_schema_rejected(self):
        chart = _ready_chart()
        chart["schema_version"] = "9.9"
        errors = validate_chart(chart)
        self.assertTrue(any("schema_version" in error for error in errors))

    def test_ready_requires_provenance_and_field_authority(self):
        chart = _ready_chart()
        del chart["provenance"]["manifest_sha256"]
        del chart["data"]["periods"][0]["authority_refs"]
        errors = validate_chart(chart)
        self.assertTrue(any("provenance" in error for error in errors))
        self.assertTrue(any("authority_refs" in error for error in errors))

    def test_inference_cannot_claim_verified_event(self):
        chart = _ready_chart()
        chart["authorities"]["period-1-derived"]["classification"] = "verified_event"
        errors = validate_chart(chart)
        self.assertTrue(any("verified_event" in error for error in errors))

    def test_experimental_badge_cannot_be_dropped(self):
        chart = _ready_chart()
        chart["limitations"] = [item for item in chart["limitations"] if item["code"] != "EXPERIMENTAL_CAPABILITY"]
        errors = validate_chart(chart)
        self.assertTrue(any("Experimental" in error or "EXPERIMENTAL" in error for error in errors))

    def test_nonfinite_numbers_rejected(self):
        chart = _ready_chart()
        chart["data"]["periods"][0]["age_start_years"] = math.nan
        errors = validate_chart(chart)
        self.assertTrue(any("finite" in error for error in errors))

    def test_unsupported_has_no_data(self):
        chart = _unsupported_chart()
        self.assertEqual(validate_chart(chart), [])
        chart["data"] = {}
        errors = validate_chart(chart)
        self.assertTrue(any("data" in error for error in errors))

    def test_unknown_fields_and_authority_rejected(self):
        chart = _ready_chart()
        chart["unexpected"] = True
        chart["authorities"]["bad"] = {
            "classification": "made_up",
            "source_refs": [],
            "transformation": "none",
            "confidence": None,
        }
        errors = validate_chart(chart)
        self.assertTrue(any("unknown field" in error for error in errors))
        self.assertTrue(any("authority" in error for error in errors))

    def test_blind_fixture_rejects_known_reality_ledger_and_event(self):
        chart = _ready_chart()
        chart["annotations"] = [
            {
                "target_id": "period-1",
                "text": "known reality",
                "authority_refs": ["period-1-derived"],
                "visibility": "blind",
                "evidence_refs": ["historical_event_ledger"],
            }
        ]
        chart["data"]["known_reality_context"] = {"secret": True}
        errors = validate_chart(chart)
        self.assertTrue(any("blind" in error or "contamination" in error for error in errors))

    def test_schema_is_json_schema_2020_12_with_ready_and_unsupported_branches(self):
        schema = json.loads(
            (ROOT / "schemas" / "visualization" / "chart.v1.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["properties"]["schema_version"]["const"], "1.0")
        self.assertEqual(len(schema["oneOf"]), 2)


if __name__ == "__main__":
    unittest.main()
