import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from engine.distribution.event_family_paired_oracle import (
    ORACLE_SCHEMA,
    ORACLE_SEAL_PROFILE_VERSION,
    seal_event_family_paired_oracle,
    verify_event_family_paired_oracle,
)


FIXTURE = Path("tests/fixtures/v1.6-event-family-paired-oracle.synthetic.v1.json")
CLI = Path("tools/seal_v16_event_family_paired_oracle.py")


def load_oracle():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def shared_child_universe():
    return [
        {
            "child_claim_id": "child:yearly:career:leadership_change",
            "primary_domain": "career",
            "event_family": "leadership_change",
        },
        {
            "child_claim_id": "child:yearly:career:role_change",
            "primary_domain": "career",
            "event_family": "role_change",
        },
    ]


def rendered_bytes(value):
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


class EventFamilyPairedOracleTests(unittest.TestCase):
    def test_synthetic_oracle_seals_to_aggregate_only_receipt(self):
        oracle = load_oracle()
        receipt = seal_event_family_paired_oracle(
            oracle=oracle,
            shared_child_universe=shared_child_universe(),
        )

        self.assertEqual(oracle["schema_version"], ORACLE_SCHEMA)
        self.assertEqual(receipt["profile_version"], ORACLE_SEAL_PROFILE_VERSION)
        self.assertEqual(
            set(receipt),
            {
                "profile_version",
                "schema_version",
                "classification",
                "oracle_frozen_at",
                "case_count",
                "child_count",
                "oracle_digest",
                "seal_digest",
                "promotion_allowed",
            },
        )
        self.assertEqual(receipt["case_count"], 1)
        self.assertEqual(receipt["child_count"], 2)
        self.assertFalse(receipt["promotion_allowed"])
        serialized = json.dumps(receipt, ensure_ascii=False)
        for forbidden in (
            "child:yearly:career:role_change",
            "career",
            "role_change",
            "supported",
            "unsupported",
        ):
            self.assertNotIn(forbidden, serialized)

    def test_case_and_child_order_permutations_seal_identically(self):
        oracle = load_oracle()
        first = seal_event_family_paired_oracle(
            oracle=oracle,
            shared_child_universe=shared_child_universe(),
        )

        permuted = copy.deepcopy(oracle)
        permuted["cases"].reverse()
        for case in permuted["cases"]:
            case["child_outcomes"].reverse()
        second = seal_event_family_paired_oracle(
            oracle=permuted,
            shared_child_universe=list(reversed(shared_child_universe())),
        )

        self.assertEqual(first, second)
        self.assertEqual(first["oracle_digest"], second["oracle_digest"])
        self.assertEqual(first["seal_digest"], second["seal_digest"])

    def test_shared_child_universe_must_exactly_match_every_oracle_case(self):
        oracle = load_oracle()

        missing = shared_child_universe()[:-1]
        with self.assertRaises(ValueError):
            seal_event_family_paired_oracle(oracle=oracle, shared_child_universe=missing)

        extra = shared_child_universe() + [
            {
                "child_claim_id": "child:yearly:career:transfer",
                "primary_domain": "career",
                "event_family": "transfer",
            }
        ]
        with self.assertRaises(ValueError):
            seal_event_family_paired_oracle(oracle=oracle, shared_child_universe=extra)

        relabeled = copy.deepcopy(shared_child_universe())
        relabeled[0]["event_family"] = "promotion"
        with self.assertRaises(ValueError):
            seal_event_family_paired_oracle(oracle=oracle, shared_child_universe=relabeled)

    def test_case_digest_and_outcome_specificity_rules_fail_closed(self):
        oracle = load_oracle()

        tampered_digest = copy.deepcopy(oracle)
        tampered_digest["cases"][0]["child_outcomes"][0]["caveat_required"] = True
        with self.assertRaises(ValueError):
            seal_event_family_paired_oracle(
                oracle=tampered_digest,
                shared_child_universe=shared_child_universe(),
            )

        unsupported_with_specificity = copy.deepcopy(oracle)
        unsupported_with_specificity["cases"][0]["child_outcomes"][0][
            "maximum_supported_specificity"
        ] = "event_family"
        with self.assertRaises(ValueError):
            seal_event_family_paired_oracle(
                oracle=unsupported_with_specificity,
                shared_child_universe=shared_child_universe(),
            )

        supported_without_specificity = copy.deepcopy(oracle)
        supported_without_specificity["cases"][0]["child_outcomes"][1][
            "maximum_supported_specificity"
        ] = None
        with self.assertRaises(ValueError):
            seal_event_family_paired_oracle(
                oracle=supported_without_specificity,
                shared_child_universe=shared_child_universe(),
            )

    def test_unknown_private_or_narrative_fields_are_rejected_at_all_levels(self):
        mutations = []

        top = load_oracle()
        top["subject_name"] = "private"
        mutations.append(top)

        case = load_oracle()
        case["cases"][0]["notes"] = "private"
        mutations.append(case)

        outcome = load_oracle()
        outcome["cases"][0]["child_outcomes"][0]["raw_event_text"] = "private"
        mutations.append(outcome)

        narrative = load_oracle()
        narrative["cases"][0]["child_outcomes"][0]["narrative"] = "private"
        mutations.append(narrative)

        birth = load_oracle()
        birth["cases"][0]["birth_date"] = "1984-03-13"
        mutations.append(birth)

        for payload in mutations:
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    seal_event_family_paired_oracle(
                        oracle=payload,
                        shared_child_universe=shared_child_universe(),
                    )

    def test_verify_recomputes_identity_and_returns_only_aggregate_receipt(self):
        oracle = load_oracle()
        receipt = seal_event_family_paired_oracle(
            oracle=oracle,
            shared_child_universe=shared_child_universe(),
        )
        verified = verify_event_family_paired_oracle(
            oracle=oracle,
            seal_receipt=receipt,
            shared_child_universe=shared_child_universe(),
        )
        self.assertEqual(verified, receipt)

        tampered = copy.deepcopy(receipt)
        tampered["child_count"] += 1
        with self.assertRaises(ValueError):
            verify_event_family_paired_oracle(
                oracle=oracle,
                seal_receipt=tampered,
                shared_child_universe=shared_child_universe(),
            )

    def test_seal_and_verify_cli_match_direct_api_bytes(self):
        oracle = load_oracle()
        expected = seal_event_family_paired_oracle(
            oracle=oracle,
            shared_child_universe=shared_child_universe(),
        )
        expected_bytes = rendered_bytes(expected)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            universe_path = root / "universe.json"
            receipt_path = root / "receipt.json"
            universe_path.write_text(
                json.dumps(shared_child_universe(), ensure_ascii=False),
                encoding="utf-8",
            )

            seal = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "seal",
                    "--oracle",
                    str(FIXTURE),
                    "--child-universe",
                    str(universe_path),
                    "--receipt",
                    str(receipt_path),
                ],
                check=False,
                capture_output=True,
            )
            self.assertEqual(seal.returncode, 0, seal.stderr.decode("utf-8"))
            self.assertEqual(seal.stdout, b"")
            self.assertEqual(receipt_path.read_bytes(), expected_bytes)

            verify = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "verify",
                    "--oracle",
                    str(FIXTURE),
                    "--child-universe",
                    str(universe_path),
                    "--receipt",
                    str(receipt_path),
                ],
                check=False,
                capture_output=True,
            )
            self.assertEqual(verify.returncode, 0, verify.stderr.decode("utf-8"))
            self.assertEqual(verify.stdout, expected_bytes)


if __name__ == "__main__":
    unittest.main()
