import hashlib
import unittest

from tools.compare_bazi_decadal_reference import validate_reference_packet
from tools.finalize_bazi_decadal_reference_packet import finalize_reference_packet
from tools.seal_bazi_decadal_reference_inputs import build_preoracle_seal


def _sha(label):
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _preoracle():
    return build_preoracle_seal(
        {
            "schema_version": "1.0",
            "status": "DRAFT",
            "profile": {
                "profile_id": "bazi-natal-project-v1",
                "rule_version": "1.0-exp",
                "decadal_rule": "three-days-one-year-v1",
                "age_basis": "continuous_years_from_jie_interval",
                "specification_sha256": _sha("reviewed-profile"),
            },
            "source_bindings": [
                {
                    "provider": "Hong Kong Observatory",
                    "role": "astronomical_input",
                    "source_url": "https://www.hko.gov.hk/example/almanac.pdf",
                    "source_file_label": "hko-almanac.pdf",
                    "source_sha256": _sha("source-bytes"),
                    "timezone": "UTC+08:00",
                    "published_precision_seconds": 60,
                }
            ],
            "case_census": [
                {
                    "case_id": "case-001",
                    "input_sha256": _sha("input-001"),
                    "coverage_tags": ["forward", "before_jie"],
                    "production_results_consulted_for_selection": False,
                    "comparisons": [
                        {"path": "/decadal_direction", "kind": "exact"},
                        {
                            "path": "/periods/0/start_age_years",
                            "kind": "number_abs",
                            "tolerance": 0.001,
                        },
                        {
                            "path": "/periods/0/start_datetime",
                            "kind": "datetime_abs_seconds",
                            "tolerance": 60,
                        },
                        {
                            "path": "/periods/1/end_datetime",
                            "kind": "not_comparable",
                            "reason": "Outside the reviewed reference scope.",
                        },
                    ],
                }
            ],
            "independence_boundary": {
                "expected_values_present": False,
                "oracle_may_receive_production_code": False,
                "oracle_may_receive_production_output": False,
                "oracle_may_receive_comparison_results_before_reference_seal": False,
            },
            "sealed_at": "2026-09-29T19:00:00+08:00",
            "sealed_by": "qualification-coordinator",
        }
    )


def _oracle(preoracle=None):
    preoracle = preoracle or _preoracle()
    return {
        "schema_version": "1.0",
        "preoracle_seal_sha256": preoracle["seal_sha256"],
        "oracle_builder_id": "independent-oracle-A",
        "oracle_code_sha256": _sha("oracle-code"),
        "production_code_access": False,
        "production_output_access": False,
        "comparison_result_access_before_seal": False,
        "attestation": "Expected values were produced only from the reviewed written contract and sealed external inputs.",
        "sealed_at": "2026-09-30T12:00:00+08:00",
        "sealed_by": "independent-oracle-A",
        "cases": [
            {
                "case_id": "case-001",
                "input_sha256": _sha("input-001"),
                "comparisons": [
                    {"path": "/decadal_direction", "status": "provided", "expected": "forward"},
                    {
                        "path": "/periods/0/start_age_years",
                        "status": "provided",
                        "expected": 7.3768,
                    },
                    {
                        "path": "/periods/0/start_datetime",
                        "status": "provided",
                        "expected": "1991-07-30T03:29:20+08:00",
                    },
                ],
            }
        ],
    }


class BaziDecadalReferenceFinalizerTests(unittest.TestCase):
    def test_finalizer_emits_existing_reference_packet_contract(self):
        pre = _preoracle()
        packet = finalize_reference_packet(pre, _oracle(pre))
        self.assertEqual(validate_reference_packet(packet), [])
        self.assertEqual(packet["cases"][0]["comparisons"][1]["tolerance"], 0.001)
        self.assertEqual(packet["cases"][0]["comparisons"][2]["tolerance"], 60)
        self.assertEqual(packet["cases"][0]["comparisons"][3]["kind"], "not_comparable")

    def test_preoracle_binding_mismatch_fails_closed(self):
        pre = _preoracle()
        oracle = _oracle(pre)
        oracle["preoracle_seal_sha256"] = _sha("different-seal")
        with self.assertRaisesRegex(ValueError, "does not bind"):
            finalize_reference_packet(pre, oracle)

    def test_oracle_cannot_add_or_remove_cases(self):
        pre = _preoracle()
        oracle = _oracle(pre)
        oracle["cases"][0]["case_id"] = "case-other"
        with self.assertRaisesRegex(ValueError, "case census mismatch"):
            finalize_reference_packet(pre, oracle)

    def test_oracle_cannot_change_input_digest(self):
        pre = _preoracle()
        oracle = _oracle(pre)
        oracle["cases"][0]["input_sha256"] = _sha("different-input")
        with self.assertRaisesRegex(ValueError, "input digest mismatch"):
            finalize_reference_packet(pre, oracle)

    def test_oracle_cannot_change_comparison_path_census(self):
        pre = _preoracle()
        oracle = _oracle(pre)
        oracle["cases"][0]["comparisons"].pop()
        with self.assertRaisesRegex(ValueError, "comparison census mismatch"):
            finalize_reference_packet(pre, oracle)

    def test_missing_reference_is_preserved(self):
        pre = _preoracle()
        oracle = _oracle(pre)
        oracle["cases"][0]["comparisons"][1] = {
            "path": "/periods/0/start_age_years",
            "status": "missing_reference",
            "reason": "Independent reference could not resolve this field.",
        }
        packet = finalize_reference_packet(pre, oracle)
        row = next(
            row for row in packet["cases"][0]["comparisons"]
            if row["path"] == "/periods/0/start_age_years"
        )
        self.assertEqual(row["kind"], "missing_reference")
        self.assertNotIn("tolerance", row)
        self.assertNotIn("expected", row)

    def test_oracle_exposure_flags_fail_closed(self):
        pre = _preoracle()
        oracle = _oracle(pre)
        oracle["production_code_access"] = True
        with self.assertRaisesRegex(ValueError, "production_code_access"):
            finalize_reference_packet(pre, oracle)


if __name__ == "__main__":
    unittest.main()
