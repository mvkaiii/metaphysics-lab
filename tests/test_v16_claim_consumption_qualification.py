import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from engine.distribution.claim_consumption_qualification import (
    INPUT_SCHEMA,
    REPORT_SCHEMA,
    evaluate_claim_consumption_qualification,
    validate_claim_consumption_qualification_input,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "v1.6-claim-consumption-qualification.synthetic.v1.json"


def canonical_bytes(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def load_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def refresh_bundle(bundle):
    bundle.pop("claim_consumption_digest", None)
    bundle["claim_consumption_digest"] = digest(bundle)


def refresh_case(case):
    case.pop("input_digest", None)
    case["input_digest"] = digest(case)


class ClaimConsumptionQualificationTests(unittest.TestCase):
    def test_baseline_synthetic_oracle_passes_and_report_is_aggregate_only(self):
        payload = load_fixture()
        self.assertEqual(payload["schema_version"], INPUT_SCHEMA)
        validated = validate_claim_consumption_qualification_input(payload)
        self.assertEqual(validated, payload)

        report = evaluate_claim_consumption_qualification(payload)
        self.assertEqual(report["schema_version"], REPORT_SCHEMA)
        self.assertEqual(report["classification"], "synthetic_validation")
        self.assertEqual(report["case_count"], 3)
        self.assertEqual(report["claim_count"], 3)
        self.assertEqual(
            report["decision_alignment"],
            {"matched": 3, "partial": 0, "missed": 0},
        )
        self.assertEqual(report["over_render_count"], 0)
        self.assertEqual(report["under_render_count"], 0)
        self.assertEqual(report["caveat_omission_count"], 0)
        self.assertEqual(report["unnecessary_caveat_count"], 0)
        self.assertEqual(report["specificity_overreach_count"], 0)
        self.assertEqual(report["specificity_excessive_downgrade_count"], 0)
        self.assertEqual(report["cutoff_contamination_count"], 0)
        self.assertEqual(report["general_conformance_status"], "PASS")
        self.assertFalse(report["promotion_allowed"])
        self.assertEqual(len(report["input_set_digest"]), 64)
        self.assertEqual(len(report["report_digest"]), 64)
        rendered = json.dumps(report, sort_keys=True)
        self.assertNotIn("Q-SYN-", rendered)
        self.assertNotIn("claim:yearly:", rendered)
        self.assertNotIn("career", rendered)

    def test_over_render_is_missed_and_fails_general_conformance(self):
        payload = load_fixture()
        case = payload["cases"][2]
        actual = case["claim_consumption_bundle"]["decisions"][0]
        actual["decision"] = "render_with_caveat"
        actual["reason_codes"] = ["single_system_support"]
        refresh_bundle(case["claim_consumption_bundle"])
        refresh_case(case)
        report = evaluate_claim_consumption_qualification(payload)
        self.assertEqual(report["over_render_count"], 1)
        self.assertEqual(report["decision_alignment"]["missed"], 1)
        self.assertEqual(report["general_conformance_status"], "FAIL")

    def test_under_render_is_missed(self):
        payload = load_fixture()
        case = payload["cases"][0]
        actual = case["claim_consumption_bundle"]["decisions"][0]
        actual["decision"] = "abstain_claim"
        actual["reason_codes"] = ["no_same_scope_target_support"]
        refresh_bundle(case["claim_consumption_bundle"])
        refresh_case(case)
        report = evaluate_claim_consumption_qualification(payload)
        self.assertEqual(report["under_render_count"], 1)
        self.assertEqual(report["decision_alignment"]["missed"], 1)
        self.assertEqual(report["general_conformance_status"], "FAIL")

    def test_caveat_omission_is_partial(self):
        payload = load_fixture()
        case = payload["cases"][1]
        actual = case["claim_consumption_bundle"]["decisions"][0]
        actual["decision"] = "render"
        actual["reason_codes"] = []
        refresh_bundle(case["claim_consumption_bundle"])
        refresh_case(case)
        report = evaluate_claim_consumption_qualification(payload)
        self.assertEqual(report["caveat_omission_count"], 1)
        self.assertEqual(report["decision_alignment"]["partial"], 1)
        self.assertEqual(report["general_conformance_status"], "FAIL")

    def test_unnecessary_caveat_is_partial(self):
        payload = load_fixture()
        case = payload["cases"][0]
        actual = case["claim_consumption_bundle"]["decisions"][0]
        actual["decision"] = "render_with_caveat"
        actual["reason_codes"] = ["single_system_support"]
        refresh_bundle(case["claim_consumption_bundle"])
        refresh_case(case)
        report = evaluate_claim_consumption_qualification(payload)
        self.assertEqual(report["unnecessary_caveat_count"], 1)
        self.assertEqual(report["decision_alignment"]["partial"], 1)
        self.assertEqual(report["general_conformance_status"], "FAIL")

    def test_specificity_overreach_and_excessive_downgrade_are_counted(self):
        over = load_fixture()
        case = over["cases"][0]
        case["claim_consumption_bundle"]["decisions"][0]["original_effective_specificity"] = "highly_specific_event"
        case["claim_consumption_bundle"]["decisions"][0]["authorized_specificity"] = "highly_specific_event"
        refresh_bundle(case["claim_consumption_bundle"])
        refresh_case(case)
        report = evaluate_claim_consumption_qualification(over)
        self.assertEqual(report["specificity_overreach_count"], 1)
        self.assertEqual(report["decision_alignment"]["partial"], 1)
        self.assertEqual(report["general_conformance_status"], "FAIL")

        low = load_fixture()
        case = low["cases"][0]
        case["claim_consumption_bundle"]["decisions"][0]["authorized_specificity"] = "domain"
        refresh_bundle(case["claim_consumption_bundle"])
        refresh_case(case)
        report = evaluate_claim_consumption_qualification(low)
        self.assertEqual(report["specificity_excessive_downgrade_count"], 1)
        self.assertEqual(report["decision_alignment"]["partial"], 1)
        self.assertEqual(report["general_conformance_status"], "FAIL")

    def test_cutoff_contamination_fails_general_conformance(self):
        payload = load_fixture()
        payload["cases"][0]["cutoff_contamination"] = True
        refresh_case(payload["cases"][0])
        report = evaluate_claim_consumption_qualification(payload)
        self.assertEqual(report["cutoff_contamination_count"], 1)
        self.assertEqual(report["general_conformance_status"], "FAIL")

    def test_malformed_bundle_or_case_digest_fails_closed(self):
        payload = load_fixture()
        payload["cases"][0]["claim_consumption_bundle"]["decisions"][0]["decision"] = "abstain_claim"
        with self.assertRaisesRegex(ValueError, "claim_consumption_digest"):
            evaluate_claim_consumption_qualification(payload)

        payload = load_fixture()
        payload["cases"][0]["expectations"][0]["caveat_required"] = True
        with self.assertRaisesRegex(ValueError, "input_digest"):
            evaluate_claim_consumption_qualification(payload)

    def test_unknown_or_private_fields_are_rejected(self):
        for field in ("subject_name", "birth_date", "actual_event", "event_text", "notes"):
            payload = load_fixture()
            payload["cases"][0][field] = "private"
            refresh_case(payload["cases"][0])
            with self.assertRaisesRegex(ValueError, "unknown"):
                evaluate_claim_consumption_qualification(payload)

        payload = load_fixture()
        payload["unexpected"] = 1
        with self.assertRaisesRegex(ValueError, "unknown"):
            evaluate_claim_consumption_qualification(payload)

    def test_duplicate_missing_and_extra_claim_ids_fail_closed(self):
        payload = load_fixture()
        case = payload["cases"][0]
        case["claim_consumption_bundle"]["decisions"].append(
            copy.deepcopy(case["claim_consumption_bundle"]["decisions"][0])
        )
        refresh_bundle(case["claim_consumption_bundle"])
        refresh_case(case)
        with self.assertRaisesRegex(ValueError, "claim_id.*unique|unique.*claim_id"):
            evaluate_claim_consumption_qualification(payload)

        payload = load_fixture()
        case = payload["cases"][0]
        case["claim_consumption_bundle"]["decisions"] = []
        refresh_bundle(case["claim_consumption_bundle"])
        refresh_case(case)
        with self.assertRaisesRegex(ValueError, "claim.*sets|expected.*actual"):
            evaluate_claim_consumption_qualification(payload)

        payload = load_fixture()
        case = payload["cases"][0]
        extra = copy.deepcopy(case["claim_consumption_bundle"]["decisions"][0])
        extra["claim_id"] = "claim:yearly:extra"
        extra["primary_domain"] = "extra"
        case["claim_consumption_bundle"]["decisions"].append(extra)
        refresh_bundle(case["claim_consumption_bundle"])
        refresh_case(case)
        with self.assertRaisesRegex(ValueError, "claim.*sets|expected.*actual"):
            evaluate_claim_consumption_qualification(payload)

    def test_case_order_permutation_has_identical_report(self):
        payload = load_fixture()
        first = evaluate_claim_consumption_qualification(payload)
        payload["cases"].reverse()
        second = evaluate_claim_consumption_qualification(payload)
        self.assertEqual(first, second)

    def test_private_classification_is_metrics_only_and_never_promotable(self):
        payload = load_fixture()
        payload["classification"] = "private_external_evaluation"
        report = evaluate_claim_consumption_qualification(payload)
        self.assertEqual(report["general_conformance_status"], "METRICS_ONLY")
        self.assertFalse(report["promotion_allowed"])

    def test_cli_stdout_is_byte_identical_and_matches_direct_evaluator(self):
        command = [
            sys.executable,
            str(ROOT / "tools" / "evaluate_v16_claim_consumption_qualification.py"),
            "--input",
            str(FIXTURE),
        ]
        first = subprocess.run(command, cwd=ROOT, check=True, capture_output=True).stdout
        second = subprocess.run(command, cwd=ROOT, check=True, capture_output=True).stdout
        self.assertEqual(first, second)
        self.assertTrue(first.endswith(b"\n"))
        self.assertEqual(json.loads(first.decode("utf-8")), evaluate_claim_consumption_qualification(load_fixture()))

    def test_cli_output_file_writes_same_bytes_and_keeps_stdout_empty(self):
        command = [
            sys.executable,
            str(ROOT / "tools" / "evaluate_v16_claim_consumption_qualification.py"),
            "--input",
            str(FIXTURE),
        ]
        expected = subprocess.run(command, cwd=ROOT, check=True, capture_output=True).stdout
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "report.json"
            completed = subprocess.run(
                command + ["--output", str(output)],
                cwd=ROOT,
                check=True,
                capture_output=True,
            )
            self.assertEqual(completed.stdout, b"")
            self.assertEqual(output.read_bytes(), expected)

    def test_method_doc_locks_q1_governance_boundaries(self):
        text = (ROOT / "docs" / "research" / "2026-09-01-v1.6-claim-consumption-qualification-q1.md").read_text(encoding="utf-8")
        lowered = text.lower()
        self.assertIn("does not tune c1", lowered)
        self.assertIn("prior private", lowered)
        self.assertIn("aggregate-only", lowered)
        self.assertIn("promotion_allowed", text)
        self.assertIn("private_external_evaluation", text)
        self.assertIn("sealed", lowered)
        self.assertIn("minimum_acceptable_specificity", text)


if __name__ == "__main__":
    unittest.main()
