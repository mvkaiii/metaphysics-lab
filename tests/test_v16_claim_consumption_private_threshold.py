from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from engine.distribution.claim_consumption_private_threshold import (
    evaluate_claim_consumption_private_threshold,
    validate_oracle_seal_receipt,
    validate_private_evaluation_identity_receipt,
    validate_private_release_policy,
    validate_q1_private_report,
    validate_sampling_eligibility_receipt,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "v1.6-claim-consumption-private-threshold.synthetic.v1.json"


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text())


def refresh_policy(policy: dict) -> None:
    policy.pop("policy_digest", None)
    policy["policy_digest"] = digest(policy)


def refresh_receipt(receipt: dict) -> None:
    receipt.pop("receipt_digest", None)
    receipt["receipt_digest"] = digest(receipt)


def refresh_oracle_receipt(receipt: dict) -> None:
    payload = {
        "schema_version": "v1.6-claim-consumption-oracle-seal.v1",
        "oracle_profile": receipt["oracle_profile"],
        "case_count": receipt["case_count"],
        "claim_count": receipt["claim_count"],
        "rubric_digest": receipt["rubric_digest"],
        "oracle_expectation_digest": receipt["oracle_expectation_digest"],
        "case_set_digest": receipt["case_set_digest"],
        "cutoff_contamination_count": receipt["cutoff_contamination_count"],
        "sealed_at": receipt["sealed_at"],
    }
    receipt["seal_digest"] = digest(payload)


def refresh_q1_report(report: dict) -> None:
    report.pop("report_digest", None)
    report["report_digest"] = digest(report)


def evaluate(payload: dict) -> dict:
    return evaluate_claim_consumption_private_threshold(
        payload["policy"],
        payload["sampling_receipt"],
        payload["oracle_receipt"],
        payload["evaluation_identity_receipt"],
        payload["q1_report"],
    )


class ClaimConsumptionPrivateThresholdTests(unittest.TestCase):
    def test_valid_strict_zero_private_gate_passes(self):
        payload = load_fixture()
        report = evaluate(payload)
        self.assertEqual(report["eligibility_status"], "ELIGIBLE")
        self.assertEqual(report["private_gate_status"], "PASS")
        self.assertFalse(report["promotion_allowed"])
        self.assertTrue(all(value == 0 for value in report["strict_zero_metrics"].values()))

    def test_each_nonzero_strict_metric_fails(self):
        direct = [
            "cutoff_contamination_count",
            "over_render_count",
            "under_render_count",
            "caveat_omission_count",
            "unnecessary_caveat_count",
            "specificity_overreach_count",
            "specificity_excessive_downgrade_count",
        ]
        for key in direct:
            with self.subTest(metric=key):
                payload = load_fixture()
                payload["q1_report"][key] = 1
                refresh_q1_report(payload["q1_report"])
                report = evaluate(payload)
                self.assertEqual(report["eligibility_status"], "ELIGIBLE")
                self.assertEqual(report["private_gate_status"], "FAIL")
                self.assertEqual(report["strict_zero_metrics"][key], 1)

        for alignment_key, report_key in (("partial", "partial_alignment_count"), ("missed", "missed_alignment_count")):
            with self.subTest(metric=alignment_key):
                payload = load_fixture()
                payload["q1_report"]["decision_alignment"]["matched"] = 11
                payload["q1_report"]["decision_alignment"][alignment_key] = 1
                refresh_q1_report(payload["q1_report"])
                report = evaluate(payload)
                self.assertEqual(report["private_gate_status"], "FAIL")
                self.assertEqual(report["strict_zero_metrics"][report_key], 1)

    def test_sampling_noneligible_and_sequencing_mismatch_are_ineligible(self):
        payload = load_fixture()
        payload["sampling_receipt"]["status"] = "INELIGIBLE"
        refresh_receipt(payload["sampling_receipt"])
        self.assertEqual(evaluate(payload)["private_gate_status"], "INELIGIBLE")

        payload = load_fixture()
        payload["policy"]["policy_frozen_at"] = payload["oracle_receipt"]["sealed_at"]
        refresh_policy(payload["policy"])
        self.assertEqual(evaluate(payload)["private_gate_status"], "INELIGIBLE")

        payload = load_fixture()
        payload["sampling_receipt"]["sealed_at"] = "2026-09-01T14:32:01Z"
        refresh_receipt(payload["sampling_receipt"])
        self.assertEqual(evaluate(payload)["private_gate_status"], "INELIGIBLE")

        payload = load_fixture()
        payload["evaluation_identity_receipt"]["bound_at"] = "2026-09-01T14:31:59Z"
        refresh_receipt(payload["evaluation_identity_receipt"])
        self.assertEqual(evaluate(payload)["private_gate_status"], "INELIGIBLE")

    def test_identity_and_count_mismatch_are_ineligible(self):
        for artifact_key, count_key in (
            ("sampling_receipt", "case_count"),
            ("evaluation_identity_receipt", "claim_count"),
            ("oracle_receipt", "case_count"),
            ("q1_report", "claim_count"),
        ):
            with self.subTest(artifact=artifact_key, count=count_key):
                payload = load_fixture()
                payload[artifact_key][count_key] += 1
                if artifact_key in {"sampling_receipt", "evaluation_identity_receipt"}:
                    refresh_receipt(payload[artifact_key])
                elif artifact_key == "oracle_receipt":
                    refresh_oracle_receipt(payload[artifact_key])
                else:
                    payload[artifact_key]["decision_alignment"]["matched"] += 1
                    refresh_q1_report(payload[artifact_key])
                self.assertEqual(evaluate(payload)["private_gate_status"], "INELIGIBLE")

        payload = load_fixture()
        payload["evaluation_identity_receipt"]["oracle_seal_digest"] = "a" * 64
        refresh_receipt(payload["evaluation_identity_receipt"])
        self.assertEqual(evaluate(payload)["private_gate_status"], "INELIGIBLE")

        payload = load_fixture()
        payload["evaluation_identity_receipt"]["qualification_input_set_digest"] = "b" * 64
        refresh_receipt(payload["evaluation_identity_receipt"])
        self.assertEqual(evaluate(payload)["private_gate_status"], "INELIGIBLE")

    def test_oracle_contamination_is_ineligible(self):
        payload = load_fixture()
        payload["oracle_receipt"]["cutoff_contamination_count"] = 1
        refresh_oracle_receipt(payload["oracle_receipt"])
        payload["evaluation_identity_receipt"]["oracle_seal_digest"] = payload["oracle_receipt"]["seal_digest"]
        refresh_receipt(payload["evaluation_identity_receipt"])
        self.assertEqual(evaluate(payload)["private_gate_status"], "INELIGIBLE")

    def test_tampered_artifacts_fail_closed(self):
        cases = (
            ("policy", "policy_digest"),
            ("sampling_receipt", "receipt_digest"),
            ("evaluation_identity_receipt", "receipt_digest"),
            ("oracle_receipt", "seal_digest"),
            ("q1_report", "report_digest"),
        )
        for artifact_key, digest_key in cases:
            with self.subTest(artifact=artifact_key):
                payload = load_fixture()
                payload[artifact_key][digest_key] = "0" * 64
                with self.assertRaisesRegex(ValueError, "digest|seal"):
                    evaluate(payload)

    def test_unknown_fields_fail_closed(self):
        for artifact_key in ("policy", "sampling_receipt", "evaluation_identity_receipt", "oracle_receipt", "q1_report"):
            with self.subTest(artifact=artifact_key):
                payload = load_fixture()
                payload[artifact_key]["private_text"] = "forbidden"
                with self.assertRaisesRegex(ValueError, "unknown"):
                    evaluate(payload)

    def test_q1_internal_alignment_must_match_claim_count(self):
        payload = load_fixture()
        payload["q1_report"]["decision_alignment"]["matched"] = 11
        refresh_q1_report(payload["q1_report"])
        with self.assertRaisesRegex(ValueError, "alignment|claim_count"):
            evaluate(payload)

    def test_individual_validators_accept_baseline(self):
        payload = load_fixture()
        self.assertEqual(validate_private_release_policy(payload["policy"]), payload["policy"])
        self.assertEqual(validate_sampling_eligibility_receipt(payload["sampling_receipt"]), payload["sampling_receipt"])
        self.assertEqual(validate_private_evaluation_identity_receipt(payload["evaluation_identity_receipt"]), payload["evaluation_identity_receipt"])
        self.assertEqual(validate_oracle_seal_receipt(payload["oracle_receipt"]), payload["oracle_receipt"])
        self.assertEqual(validate_q1_private_report(payload["q1_report"]), payload["q1_report"])

    def test_report_is_aggregate_only_and_deterministic(self):
        payload = load_fixture()
        first = evaluate(payload)
        second = evaluate(copy.deepcopy(payload))
        self.assertEqual(canonical_bytes(first), canonical_bytes(second))
        self.assertEqual(
            set(first),
            {
                "schema_version", "policy_profile", "policy_digest", "sampling_profile",
                "sampling_receipt_digest", "evaluation_identity_receipt_digest", "candidate_sha",
                "oracle_seal_digest", "qualification_input_set_digest", "q1_report_digest",
                "case_count", "claim_count", "eligibility_status", "private_gate_status",
                "strict_zero_metrics", "promotion_allowed", "report_digest",
            },
        )
        rendered = json.dumps(first, sort_keys=True)
        for forbidden in ("case_id", "claim_id", "expected_authorization", "actual_event", "birth_date", "domain"):
            self.assertNotIn(forbidden, rendered)

    def test_frozen_public_policy_artifact_validates(self):
        policy_path = ROOT / "qualification" / "claim_consumption" / "v1.6" / "private-release-policy.strict-zero.v1.json"
        policy = json.loads(policy_path.read_text())
        self.assertEqual(validate_private_release_policy(policy), policy)
        self.assertEqual(policy["policy_profile"], "lin_tianji_claim_consumption_private_strict_zero_v1")
        self.assertTrue(all(value == 0 for value in policy["thresholds"].values()))
        self.assertFalse(policy["promotion_allowed"])

    def test_cli_matches_direct_api_and_output_file_bytes(self):
        payload = load_fixture()
        policy_path = ROOT / "qualification" / "claim_consumption" / "v1.6" / "private-release-policy.strict-zero.v1.json"
        command_base = [
            sys.executable,
            str(ROOT / "tools" / "evaluate_v16_claim_consumption_private_threshold.py"),
            "--policy", str(policy_path),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            paths = {}
            for key, arg in (
                ("sampling_receipt", "--sampling-receipt"),
                ("oracle_receipt", "--oracle-receipt"),
                ("evaluation_identity_receipt", "--evaluation-identity-receipt"),
                ("q1_report", "--q1-report"),
            ):
                path = tmp_path / f"{key}.json"
                path.write_text(json.dumps(payload[key], ensure_ascii=False, sort_keys=True, indent=2) + "\n")
                paths[key] = (arg, path)
            command = command_base[:]
            for key in ("sampling_receipt", "oracle_receipt", "evaluation_identity_receipt", "q1_report"):
                arg, path = paths[key]
                command.extend([arg, str(path)])
            expected_policy = json.loads(policy_path.read_text())
            direct = evaluate_claim_consumption_private_threshold(
                expected_policy,
                payload["sampling_receipt"],
                payload["oracle_receipt"],
                payload["evaluation_identity_receipt"],
                payload["q1_report"],
            )
            first = subprocess.run(command, cwd=ROOT, check=True, capture_output=True).stdout
            second = subprocess.run(command, cwd=ROOT, check=True, capture_output=True).stdout
            self.assertEqual(first, second)
            self.assertTrue(first.endswith(b"\n"))
            self.assertEqual(json.loads(first.decode("utf-8")), direct)
            output = tmp_path / "t1-report.json"
            completed = subprocess.run(command + ["--output", str(output)], cwd=ROOT, check=True, capture_output=True)
            self.assertEqual(completed.stdout, b"")
            self.assertEqual(output.read_bytes(), first)

    def test_method_doc_and_source_lock_prospective_governance(self):
        method_path = ROOT / "docs" / "research" / "2026-09-01-v1.6-claim-consumption-private-threshold-t1.md"
        text = method_path.read_text()
        for marker in (
            "promotion_allowed=false",
            "current exposed pair",
            "permanently prospective-ineligible",
            "Q1 exactly once",
            "T1 gate",
            "不得",
        ):
            self.assertIn(marker, text)

        scan_paths = [
            ROOT / "engine" / "distribution" / "claim_consumption_private_threshold.py",
            ROOT / "tools" / "evaluate_v16_claim_consumption_private_threshold.py",
            method_path,
        ]
        forbidden = (
            "q1-" + "private-adjudication",
            "PRIVATE_Q1_" + "PRE_EVALUATION",
            "f66b" + "59cb",
            "76e25535" + "f58cbfa5",
        )
        for path in scan_paths:
            contents = path.read_text()
            for marker in forbidden:
                self.assertNotIn(marker, contents)



if __name__ == "__main__":
    unittest.main()
