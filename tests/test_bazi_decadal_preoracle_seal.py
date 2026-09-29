import copy
import hashlib
import json
import unittest

from tools.seal_bazi_decadal_reference_inputs import (
    build_preoracle_seal,
    validate_preoracle_seal,
)


def _sha(label):
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _draft():
    return {
        "schema_version": "1.0",
        "status": "DRAFT",
        "profile": {
            "profile_id": "bazi-natal-project-v1",
            "rule_version": "1.0-exp",
            "decadal_rule": "three-days-one-year-v1",
            "age_basis": "continuous_years_from_jie_interval",
            "specification_sha256": _sha("reviewed-written-profile"),
        },
        "source_bindings": [
            {
                "provider": "Hong Kong Observatory",
                "role": "astronomical_input",
                "source_url": "https://www.hko.gov.hk/example/almanac.pdf",
                "source_file_label": "hko-almanac-example.pdf",
                "source_sha256": _sha("exact-source-bytes"),
                "timezone": "UTC+08:00",
                "published_precision_seconds": 60,
            }
        ],
        "case_census": [
            {
                "case_id": "case-forward-before-jie-001",
                "input_sha256": _sha("case-input-001"),
                "coverage_tags": ["forward", "before_jie", "cross_year"],
                "production_results_consulted_for_selection": False,
                "comparisons": [
                    {"path": "/decadal_direction", "kind": "exact"},
                    {"path": "/periods/0/pillar", "kind": "exact"},
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


class BaziDecadalPreOracleSealTests(unittest.TestCase):
    def test_build_seal_is_valid_and_deterministic(self):
        first = build_preoracle_seal(_draft())
        second = build_preoracle_seal(json.loads(json.dumps(_draft(), ensure_ascii=False)))
        self.assertEqual(first, second)
        self.assertEqual(validate_preoracle_seal(first), [])
        self.assertEqual(first["status"], "PRE_ORACLE_SEALED")
        self.assertRegex(first["seal_sha256"], r"^[0-9a-f]{64}$")

    def test_expected_values_are_not_allowed_in_preoracle_contract(self):
        draft = _draft()
        draft["case_census"][0]["comparisons"][0]["expected"] = "forward"
        with self.assertRaisesRegex(ValueError, "unknown field 'expected'"):
            build_preoracle_seal(draft)

    def test_case_selection_cannot_claim_production_consultation(self):
        draft = _draft()
        draft["case_census"][0]["production_results_consulted_for_selection"] = True
        with self.assertRaisesRegex(ValueError, "expected false"):
            build_preoracle_seal(draft)

    def test_tolerance_must_be_frozen_before_oracle(self):
        draft = _draft()
        del draft["case_census"][0]["comparisons"][2]["tolerance"]
        with self.assertRaisesRegex(ValueError, "tolerance"):
            build_preoracle_seal(draft)

    def test_source_bytes_digest_is_required(self):
        draft = _draft()
        draft["source_bindings"][0]["source_sha256"] = "not-a-digest"
        with self.assertRaisesRegex(ValueError, "source_sha256"):
            build_preoracle_seal(draft)

    def test_duplicate_case_and_comparison_paths_fail_closed(self):
        draft = _draft()
        duplicate = copy.deepcopy(draft["case_census"][0])
        draft["case_census"].append(duplicate)
        with self.assertRaisesRegex(ValueError, "duplicate case_id"):
            build_preoracle_seal(draft)

        draft = _draft()
        draft["case_census"][0]["comparisons"].append(
            copy.deepcopy(draft["case_census"][0]["comparisons"][0])
        )
        with self.assertRaisesRegex(ValueError, "duplicate comparison path"):
            build_preoracle_seal(draft)

    def test_independence_boundary_rejects_oracle_exposure(self):
        draft = _draft()
        draft["independence_boundary"]["oracle_may_receive_production_output"] = True
        with self.assertRaisesRegex(ValueError, "oracle_may_receive_production_output"):
            build_preoracle_seal(draft)

    def test_seal_digest_detects_post_seal_mutation(self):
        sealed = build_preoracle_seal(_draft())
        sealed["case_census"][0]["coverage_tags"].append("leap_year")
        errors = validate_preoracle_seal(sealed)
        self.assertTrue(any("digest mismatch" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
