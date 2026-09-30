import copy
import hashlib
import json
import unittest

from tools.compare_bazi_decadal_reference import (
    compare_reference_packet,
    validate_reference_packet,
)


def _sha(label):
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _reference():
    return {
        "schema_version": "1.0",
        "status": "SEALED",
        "profile": {
            "profile_id": "bazi-natal-project-v1",
            "rule_version": "1.0-exp",
            "decadal_rule": "three-days-one-year-v1",
            "age_basis": "continuous_years_from_jie_interval",
        },
        "independence": {
            "oracle_builder_id": "independent-reviewer-A",
            "oracle_code_sha256": _sha("oracle-code"),
            "production_code_access": False,
            "production_output_access": False,
            "comparison_result_access_before_seal": False,
            "attestation": "Expected values were produced from the approved written contract and sealed external inputs.",
        },
        "source_bindings": [
            {
                "provider": "Hong Kong Observatory",
                "role": "astronomical_input",
                "source_url": "https://www.hko.gov.hk/en/gts/astronomy/Solar_Term.htm",
                "source_sha256": _sha("sealed-hko-source-bytes"),
                "timezone": "UTC+08:00",
                "published_precision_seconds": 60,
            }
        ],
        "sealed_at": "2026-09-27T12:00:00+08:00",
        "sealed_by": "independent-reviewer-A",
        "cases": [
            {
                "case_id": "case-forward-boundary-001",
                "input_sha256": _sha("case-input"),
                "comparisons": [
                    {"path": "/decadal_direction", "kind": "exact", "expected": "forward"},
                    {"path": "/periods/0/pillar", "kind": "exact", "expected": "戊辰"},
                    {
                        "path": "/periods/0/start_age_years",
                        "kind": "number_abs",
                        "expected": 7.3768,
                        "tolerance": 0.001,
                    },
                    {
                        "path": "/periods/0/start_datetime",
                        "kind": "datetime_abs_seconds",
                        "expected": "1991-07-30T03:29:20+08:00",
                        "tolerance": 60,
                    },
                    {
                        "path": "/periods/1/end_datetime",
                        "kind": "missing_reference",
                        "reason": "External oracle did not cover this endpoint.",
                    },
                ],
            }
        ],
    }


def _actual():
    return {
        "schema_version": "1.0",
        "cases": [
            {
                "case_id": "case-forward-boundary-001",
                "input_sha256": _sha("case-input"),
                "engine_view": {
                    "decadal_direction": "forward",
                    "periods": [
                        {
                            "pillar": "戊辰",
                            "start_age_years": 7.376851851851852,
                            "start_datetime": "1991-07-30T03:29:19.800000+08:00",
                            "end_datetime": "2001-07-29T13:41:19.800000+08:00",
                        },
                        {
                            "pillar": "己巳",
                            "start_age_years": 17.376851851851853,
                            "start_datetime": "2001-07-29T13:41:19.800000+08:00",
                            "end_datetime": "2011-07-29T23:53:19.800000+08:00",
                        },
                    ],
                },
            }
        ],
    }


class BaziDecadalReferenceComparisonTests(unittest.TestCase):
    def test_valid_sealed_packet_is_accepted(self):
        self.assertEqual(validate_reference_packet(_reference()), [])

    def test_independence_exposure_is_rejected(self):
        packet = _reference()
        packet["independence"]["production_code_access"] = True
        errors = validate_reference_packet(packet)
        self.assertTrue(any("production_code_access" in error for error in errors), errors)

    def test_digest_and_tolerance_contract_is_fail_closed(self):
        packet = _reference()
        packet["source_bindings"][0]["source_sha256"] = "not-a-digest"
        del packet["cases"][0]["comparisons"][2]["tolerance"]
        errors = validate_reference_packet(packet)
        self.assertTrue(any("source_sha256" in error for error in errors), errors)
        self.assertTrue(any("tolerance" in error for error in errors), errors)

    def test_duplicate_case_path_is_rejected(self):
        packet = _reference()
        packet["cases"][0]["comparisons"].append(
            copy.deepcopy(packet["cases"][0]["comparisons"][0])
        )
        errors = validate_reference_packet(packet)
        self.assertTrue(any("duplicate" in error.lower() for error in errors), errors)

    def test_comparison_matches_exact_number_and_datetime(self):
        report = compare_reference_packet(_reference(), _actual())
        self.assertEqual(report["comparison_result"], "PARTIAL")
        rows = {
            (row["case_id"], row["path"]): row["status"]
            for row in report["field_results"]
        }
        self.assertEqual(rows[("case-forward-boundary-001", "/decadal_direction")], "MATCH")
        self.assertEqual(rows[("case-forward-boundary-001", "/periods/0/pillar")], "MATCH")
        self.assertEqual(rows[("case-forward-boundary-001", "/periods/0/start_age_years")], "MATCH")
        self.assertEqual(rows[("case-forward-boundary-001", "/periods/0/start_datetime")], "MATCH")
        self.assertEqual(rows[("case-forward-boundary-001", "/periods/1/end_datetime")], "MISSING_REFERENCE")
        self.assertEqual(report["qualification_decision"], "HUMAN_REVIEW_REQUIRED")

    def test_mismatch_is_reported_without_qualification_promotion(self):
        actual = _actual()
        actual["cases"][0]["engine_view"]["periods"][0]["pillar"] = "己巳"
        report = compare_reference_packet(_reference(), actual)
        self.assertEqual(report["comparison_result"], "MISMATCH")
        self.assertEqual(report["qualification_decision"], "HUMAN_REVIEW_REQUIRED")
        self.assertFalse(report["maturity_promotion"])

    def test_case_input_digest_mismatch_fails_closed(self):
        actual = _actual()
        actual["cases"][0]["input_sha256"] = _sha("different-input")
        with self.assertRaisesRegex(ValueError, "input digest"):
            compare_reference_packet(_reference(), actual)

    def test_output_is_deterministic_and_binds_reference_digest(self):
        first = compare_reference_packet(_reference(), _actual())
        second = compare_reference_packet(
            json.loads(json.dumps(_reference(), ensure_ascii=False)),
            json.loads(json.dumps(_actual(), ensure_ascii=False)),
        )
        self.assertEqual(first, second)
        self.assertRegex(first["reference_packet_sha256"], r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
