from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from engine.distribution.claim_consumption_qualification import (
    evaluate_claim_consumption_qualification,
    validate_claim_consumption_qualification_input,
)

import engine.distribution.claim_consumption_oracle_seal as oracle_seal_module
from engine.distribution.claim_consumption_oracle_seal import (
    RECEIPT_SCHEMA,
    VERIFICATION_SCHEMA,
    build_public_oracle_seal_receipt,
    seal_claim_consumption_oracle,
    validate_claim_consumption_oracle,
    verify_oracle_seal,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "v1.6-claim-consumption-oracle.synthetic.v1.json"
CANDIDATE_FIXTURE = ROOT / "tests" / "fixtures" / "v1.6-claim-consumption-candidate-output.synthetic.v1.json"
SEALED_AT = "2026-09-01T12:00:00Z"
CLI = ROOT / "tools" / "seal_v16_claim_consumption_oracle.py"
METHOD_DOC = ROOT / "docs" / "research" / "2026-09-01-v1.6-claim-consumption-oracle-seal-o1.md"


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _load_oracle() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _load_candidate() -> dict:
    return json.loads(CANDIDATE_FIXTURE.read_text(encoding="utf-8"))


def _recompute_case_digest(case: dict) -> None:
    payload = copy.deepcopy(case)
    payload.pop("oracle_case_digest", None)
    payload["expectations"] = sorted(payload["expectations"], key=lambda row: row["claim_id"])
    case["oracle_case_digest"] = _digest(payload)


class ClaimConsumptionOracleSealTests(unittest.TestCase):
    def test_valid_oracle_seals_verifies_and_receipt_is_aggregate_only(self):
        oracle = _load_oracle()
        validated = validate_claim_consumption_oracle(oracle)
        self.assertEqual(validated, oracle)

        seal = seal_claim_consumption_oracle(oracle, SEALED_AT)
        verified = verify_oracle_seal(oracle, seal)
        self.assertEqual(
            verified,
            {
                "schema_version": VERIFICATION_SCHEMA,
                "status": "VALID",
                "seal_digest": seal["seal_digest"],
            },
        )

        receipt = build_public_oracle_seal_receipt(seal)
        self.assertEqual(receipt["schema_version"], RECEIPT_SCHEMA)
        self.assertEqual(receipt["status"], "SEALED")
        self.assertIs(receipt["promotion_allowed"], False)
        serialized = _canonical_bytes(receipt).decode("utf-8")
        for forbidden in (
            "case_id",
            "claim_id",
            "expected_authorization",
            "minimum_acceptable_specificity",
            "maximum_specificity",
            "career",
            "finance",
            "partnership",
        ):
            self.assertNotIn(forbidden, serialized)

    def test_case_and_expectation_order_do_not_change_semantic_digests(self):
        oracle = _load_oracle()
        seal_a = seal_claim_consumption_oracle(oracle, SEALED_AT)

        permuted = copy.deepcopy(oracle)
        permuted["cases"].reverse()
        for case in permuted["cases"]:
            case["expectations"].reverse()
        seal_b = seal_claim_consumption_oracle(permuted, SEALED_AT)

        self.assertEqual(seal_a["oracle_expectation_digest"], seal_b["oracle_expectation_digest"])
        self.assertEqual(seal_a["case_set_digest"], seal_b["case_set_digest"])
        self.assertEqual(seal_a["seal_digest"], seal_b["seal_digest"])

    def test_duplicate_case_id_fails_closed(self):
        oracle = _load_oracle()
        duplicate = copy.deepcopy(oracle["cases"][0])
        oracle["cases"].append(duplicate)
        with self.assertRaisesRegex(ValueError, "case_id"):
            validate_claim_consumption_oracle(oracle)

    def test_duplicate_claim_id_fails_closed(self):
        oracle = _load_oracle()
        case = oracle["cases"][0]
        case["expectations"].append(copy.deepcopy(case["expectations"][0]))
        _recompute_case_digest(case)
        with self.assertRaisesRegex(ValueError, "claim_id"):
            validate_claim_consumption_oracle(oracle)

    def test_unknown_and_private_fields_fail_closed(self):
        mutations = []
        top = _load_oracle()
        top["subject_name"] = "private"
        mutations.append(top)

        case = _load_oracle()
        case["cases"][0]["actual_event"] = "private"
        mutations.append(case)

        expectation = _load_oracle()
        expectation["cases"][0]["expectations"][0]["notes"] = "private"
        mutations.append(expectation)

        for payload in mutations:
            with self.subTest(payload=payload):
                with self.assertRaisesRegex(ValueError, "unknown fields"):
                    validate_claim_consumption_oracle(payload)

    def test_rubric_digest_must_be_lowercase_sha256(self):
        for bad in ("ABC", "A" * 64, "g" * 64, "0" * 63):
            oracle = _load_oracle()
            oracle["rubric_digest"] = bad
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValueError, "rubric_digest"):
                    validate_claim_consumption_oracle(oracle)

    def test_oracle_case_digest_tampering_fails_closed(self):
        oracle = _load_oracle()
        oracle["cases"][0]["cutoff_contamination"] = True
        with self.assertRaisesRegex(ValueError, "oracle_case_digest"):
            validate_claim_consumption_oracle(oracle)

    def test_sealed_at_requires_utc_rfc3339_z(self):
        oracle = _load_oracle()
        for bad in (
            "2026-09-01T12:00:00+00:00",
            "2026-09-01T20:00:00+08:00",
            "2026-09-01 12:00:00Z",
            "not-a-time",
        ):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValueError, "sealed_at"):
                    seal_claim_consumption_oracle(oracle, bad)

    def test_seal_digest_tampering_fails_closed(self):
        oracle = _load_oracle()
        seal = seal_claim_consumption_oracle(oracle, SEALED_AT)
        seal["claim_count"] += 1
        with self.assertRaises(ValueError):
            verify_oracle_seal(oracle, seal)

    def test_verification_output_never_contains_oracle_answers(self):
        oracle = _load_oracle()
        seal = seal_claim_consumption_oracle(oracle, SEALED_AT)
        verified = verify_oracle_seal(oracle, seal)
        self.assertEqual(set(verified), {"schema_version", "status", "seal_digest"})
        serialized = _canonical_bytes(verified).decode("utf-8")
        self.assertNotIn("case_id", serialized)
        self.assertNotIn("claim_id", serialized)
        self.assertNotIn("expected_authorization", serialized)


    def test_valid_join_builds_q1_private_input(self):
        oracle = _load_oracle()
        seal = seal_claim_consumption_oracle(oracle, SEALED_AT)
        candidate = _load_candidate()

        with patch(
            "engine.distribution.claim_consumption_qualification.evaluate_claim_consumption_qualification",
            side_effect=AssertionError("join must not score"),
        ):
            joined = oracle_seal_module.join_sealed_oracle_with_candidate(
                oracle,
                seal,
                candidate,
            )

        self.assertEqual(joined["schema_version"], "v1.6-claim-consumption-qualification-input.v1")
        self.assertEqual(joined["classification"], "private_external_evaluation")
        self.assertEqual([row["case_id"] for row in joined["cases"]], ["oracle-case-a", "oracle-case-b"])
        self.assertEqual(validate_claim_consumption_qualification_input(joined), joined)
        self.assertEqual(evaluate_claim_consumption_qualification(joined)["general_conformance_status"], "METRICS_ONLY")

        oracle_by_id = {row["case_id"]: row for row in oracle["cases"]}
        candidate_by_id = {row["case_id"]: row for row in candidate["cases"]}
        for row in joined["cases"]:
            expected = sorted(
                oracle_by_id[row["case_id"]]["expectations"],
                key=lambda item: item["claim_id"],
            )
            self.assertEqual(row["expectations"], expected)
            self.assertEqual(
                row["claim_consumption_bundle"],
                candidate_by_id[row["case_id"]]["claim_consumption_bundle"],
            )
            digest_payload = dict(row)
            supplied = digest_payload.pop("input_digest")
            self.assertEqual(supplied, _digest(digest_payload))

    def test_candidate_sha_and_candidate_case_digest_are_strict(self):
        candidate = _load_candidate()
        for bad in ("abc", "A" * 40, "g" * 40, "0" * 39):
            mutated = copy.deepcopy(candidate)
            mutated["candidate_sha"] = bad
            with self.subTest(candidate_sha=bad):
                with self.assertRaisesRegex(ValueError, "candidate_sha"):
                    oracle_seal_module.validate_claim_consumption_candidate_output(mutated)

        tampered = copy.deepcopy(candidate)
        tampered["cases"][0]["claim_consumption_bundle"]["target_scope"] = "monthly"
        with self.assertRaises(ValueError):
            oracle_seal_module.validate_claim_consumption_candidate_output(tampered)

    def test_candidate_unknown_fields_and_duplicate_case_ids_fail_closed(self):
        candidate = _load_candidate()
        candidate["subject_name"] = "private"
        with self.assertRaisesRegex(ValueError, "unknown fields"):
            oracle_seal_module.validate_claim_consumption_candidate_output(candidate)

        duplicate = _load_candidate()
        duplicate["cases"].append(copy.deepcopy(duplicate["cases"][0]))
        with self.assertRaisesRegex(ValueError, "case_id"):
            oracle_seal_module.validate_claim_consumption_candidate_output(duplicate)

    def test_join_rejects_case_set_mismatch(self):
        oracle = _load_oracle()
        seal = seal_claim_consumption_oracle(oracle, SEALED_AT)
        candidate = _load_candidate()
        candidate["cases"] = candidate["cases"][:-1]
        with self.assertRaisesRegex(ValueError, "case.*set"):
            oracle_seal_module.join_sealed_oracle_with_candidate(oracle, seal, candidate)

    def test_join_rejects_claim_set_mismatch(self):
        oracle = _load_oracle()
        seal = seal_claim_consumption_oracle(oracle, SEALED_AT)
        candidate = _load_candidate()
        target = candidate["cases"][0]
        target["claim_consumption_bundle"]["decisions"] = target["claim_consumption_bundle"]["decisions"][:-1]
        bundle = target["claim_consumption_bundle"]
        bundle_payload = dict(bundle)
        bundle_payload.pop("claim_consumption_digest", None)
        bundle["claim_consumption_digest"] = _digest(bundle_payload)
        target["candidate_case_digest"] = _digest({
            "case_id": target["case_id"],
            "claim_consumption_bundle": bundle,
        })
        with self.assertRaisesRegex(ValueError, "claim.*set"):
            oracle_seal_module.join_sealed_oracle_with_candidate(oracle, seal, candidate)

    def test_contaminated_or_tampered_oracle_cannot_join(self):
        contaminated = _load_oracle()
        contaminated["cases"][0]["cutoff_contamination"] = True
        _recompute_case_digest(contaminated["cases"][0])
        contaminated_seal = seal_claim_consumption_oracle(contaminated, SEALED_AT)
        with self.assertRaisesRegex(ValueError, "contamination"):
            oracle_seal_module.join_sealed_oracle_with_candidate(
                contaminated,
                contaminated_seal,
                _load_candidate(),
            )

        oracle = _load_oracle()
        seal = seal_claim_consumption_oracle(oracle, SEALED_AT)
        oracle["cases"][0]["expectations"][0]["expected_authorization"] = "render"
        with self.assertRaises(ValueError):
            oracle_seal_module.join_sealed_oracle_with_candidate(oracle, seal, _load_candidate())

    def test_join_is_order_independent_and_byte_deterministic(self):
        oracle = _load_oracle()
        seal = seal_claim_consumption_oracle(oracle, SEALED_AT)
        candidate = _load_candidate()
        joined_a = oracle_seal_module.join_sealed_oracle_with_candidate(oracle, seal, candidate)

        oracle_b = copy.deepcopy(oracle)
        oracle_b["cases"].reverse()
        for case in oracle_b["cases"]:
            case["expectations"].reverse()
        candidate_b = copy.deepcopy(candidate)
        candidate_b["cases"].reverse()
        joined_b = oracle_seal_module.join_sealed_oracle_with_candidate(oracle_b, seal, candidate_b)

        self.assertEqual(_canonical_bytes(joined_a), _canonical_bytes(joined_b))


    def test_cli_seal_verify_join_matches_direct_api(self):
        oracle = _load_oracle()
        candidate = _load_candidate()
        direct_seal = seal_claim_consumption_oracle(oracle, SEALED_AT)
        direct_receipt = build_public_oracle_seal_receipt(direct_seal)
        direct_join = oracle_seal_module.join_sealed_oracle_with_candidate(
            oracle,
            direct_seal,
            candidate,
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            oracle_path = root / "oracle.json"
            candidate_path = root / "candidate.json"
            seal_path = root / "oracle-seal.json"
            receipt_path = root / "receipt.json"
            verify_path = root / "verify.json"
            join_path = root / "joined.json"
            oracle_path.write_text(json.dumps(oracle), encoding="utf-8")
            candidate_path.write_text(json.dumps(candidate), encoding="utf-8")

            sealed = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "seal",
                    "--oracle",
                    str(oracle_path),
                    "--sealed-at",
                    SEALED_AT,
                    "--seal-out",
                    str(seal_path),
                    "--receipt-out",
                    str(receipt_path),
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=ROOT,
            )
            self.assertEqual(sealed.stdout, "")
            self.assertEqual(sealed.stderr, "")
            self.assertEqual(seal_path.read_bytes(), _canonical_bytes(direct_seal) + b"\n")
            self.assertEqual(receipt_path.read_bytes(), _canonical_bytes(direct_receipt) + b"\n")

            verified = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "verify",
                    "--oracle",
                    str(oracle_path),
                    "--seal",
                    str(seal_path),
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=ROOT,
            )
            direct_verified = verify_oracle_seal(oracle, direct_seal)
            self.assertEqual(verified.stdout.encode("utf-8"), _canonical_bytes(direct_verified) + b"\n")
            self.assertEqual(verified.stderr, "")

            verified_to_file = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "verify",
                    "--oracle",
                    str(oracle_path),
                    "--seal",
                    str(seal_path),
                    "--output",
                    str(verify_path),
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=ROOT,
            )
            self.assertEqual(verified_to_file.stdout, "")
            self.assertEqual(verify_path.read_bytes(), _canonical_bytes(direct_verified) + b"\n")

            joined = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "join",
                    "--oracle",
                    str(oracle_path),
                    "--seal",
                    str(seal_path),
                    "--candidate-output",
                    str(candidate_path),
                    "--output",
                    str(join_path),
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=ROOT,
            )
            self.assertEqual(joined.stdout, "")
            self.assertEqual(joined.stderr, "")
            self.assertEqual(join_path.read_bytes(), _canonical_bytes(direct_join) + b"\n")

    def test_cli_requires_explicit_private_output_paths_and_has_no_git_or_network_side_effects(self):
        oracle_path = str(FIXTURE)
        candidate_path = str(CANDIDATE_FIXTURE)
        for args in (
            ["seal", "--oracle", oracle_path, "--sealed-at", SEALED_AT],
            [
                "join",
                "--oracle",
                oracle_path,
                "--seal",
                oracle_path,
                "--candidate-output",
                candidate_path,
            ],
            ["unknown-mode"],
        ):
            with self.subTest(args=args):
                result = subprocess.run(
                    [sys.executable, str(CLI), *args],
                    capture_output=True,
                    text=True,
                    cwd=ROOT,
                )
                self.assertNotEqual(result.returncode, 0)

        source = CLI.read_text(encoding="utf-8")
        for forbidden in (
            "git commit",
            "git push",
            "requests.",
            "urllib.request",
            "http://",
            "https://",
        ):
            self.assertNotIn(forbidden, source)

    def test_method_doc_locks_oracle_seal_governance_boundaries(self):
        text = METHOD_DOC.read_text(encoding="utf-8")
        for required in (
            "PRIVATE_ORACLE_OUTSIDE_GIT",
            "CANDIDATE_OUTPUT_AFTER_FREEZE",
            "JOIN_DOES_NOT_SCORE",
            "PRIVATE_Q1_NOT_EXECUTED",
            "promotion_allowed=false",
        ):
            self.assertIn(required, text)
        self.assertIn("4c5df745554b1d14a08b58aae45f4212b0162132", text)
        self.assertNotIn("actual_event", text)
        self.assertNotIn("subject_name", text)


if __name__ == "__main__":
    unittest.main()
