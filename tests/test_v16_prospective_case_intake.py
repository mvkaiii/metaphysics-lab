from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from engine.distribution.claim_consumption_case_intake import (
    ELIGIBLE_STATUS,
    INELIGIBLE_EXPOSED_STATUS,
    INELIGIBLE_PROVENANCE_STATUS,
    build_intake_registry,
    validate_intake_registry,
    validate_intake_registry_successor,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "v1.6-prospective-case-intake.synthetic.v1.json"
TEMPLATE = ROOT / "qualification" / "claim_consumption" / "v1.6" / "prospective-case-intake-registry.template.v1.json"
SCHEMA = ROOT / "qualification" / "claim_consumption" / "v1.6" / "prospective-case-intake-registry.schema.v1.json"
RUNBOOK = ROOT / "docs" / "research" / "2026-09-02-v1.6-prospective-case-intake-runbook.md"
CLI = ROOT / "tools" / "validate_v16_prospective_case_intake.py"
PYTHON = Path(sys.executable)


def _load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _records_by_id(registry: dict) -> dict[str, dict]:
    return {row["opaque_case_id"]: row for row in registry["records"]}


class ProspectiveCaseIntakeTests(unittest.TestCase):
    def test_future_and_historical_unexposed_are_eligible(self):
        fixture = _load_fixture()
        registry = build_intake_registry(
            [fixture["future_unexposed"], fixture["historical_unexposed"]],
            "2026-09-02T00:30:00Z",
            previous_registry_digest=None,
        )
        rows = _records_by_id(registry)
        self.assertEqual(rows["case-future-a"]["eligibility_status"], ELIGIBLE_STATUS)
        self.assertEqual(rows["case-historical-a"]["eligibility_status"], ELIGIBLE_STATUS)
        self.assertEqual(rows["case-future-a"]["eligibility_reason_code"], "eligible")
        self.assertEqual(rows["case-historical-a"]["eligibility_reason_code"], "eligible")
        self.assertEqual(validate_intake_registry(registry), registry)

    def test_missing_provenance_is_ineligible_source_provenance(self):
        base = _load_fixture()["historical_unexposed"]
        mutations = (
            ("source_provenance_status", "UNVERIFIABLE", "source_provenance_digest", None),
            ("first_intake_status", "UNVERIFIABLE", "first_intake_provenance_digest", None),
            ("candidate_exposure_status", "UNKNOWN", "candidate_exposure_provenance_digest", None),
        )
        for status_key, status_value, digest_key, digest_value in mutations:
            with self.subTest(status_key=status_key):
                row = copy.deepcopy(base)
                row[status_key] = status_value
                row[digest_key] = digest_value
                registry = build_intake_registry([row], "2026-09-02T00:30:00Z", previous_registry_digest=None)
                built = registry["records"][0]
                self.assertEqual(built["eligibility_status"], INELIGIBLE_PROVENANCE_STATUS)
                self.assertNotEqual(built["eligibility_reason_code"], "eligible")

    def test_previously_exposed_is_ineligible(self):
        row = _load_fixture()["previously_exposed"]
        registry = build_intake_registry([row], "2026-09-02T00:30:00Z", previous_registry_digest=None)
        built = registry["records"][0]
        self.assertEqual(built["eligibility_status"], INELIGIBLE_EXPOSED_STATUS)
        self.assertEqual(built["eligibility_reason_code"], "previously_exposed")

    def test_origin_outcome_contract_fails_closed(self):
        fixture = _load_fixture()
        future = copy.deepcopy(fixture["future_unexposed"])
        future["outcome_availability_at_intake"] = "KNOWN"
        historical = copy.deepcopy(fixture["historical_unexposed"])
        historical["outcome_availability_at_intake"] = "PENDING"
        for row in (future, historical):
            with self.subTest(origin=row["case_origin"]):
                with self.assertRaises(ValueError):
                    build_intake_registry([row], "2026-09-02T00:30:00Z", previous_registry_digest=None)

    def test_source_and_intake_timestamps_fail_closed(self):
        row = copy.deepcopy(_load_fixture()["future_unexposed"])
        row["source_timestamp"] = "2026-09-02T00:22:00Z"
        row["intake_timestamp"] = "2026-09-02T00:21:00Z"
        with self.assertRaises(ValueError):
            build_intake_registry([row], "2026-09-02T00:30:00Z", previous_registry_digest=None)
        row = copy.deepcopy(_load_fixture()["future_unexposed"])
        row["intake_timestamp"] = "2026-09-02T00:31:00Z"
        with self.assertRaises(ValueError):
            build_intake_registry([row], "2026-09-02T00:30:00Z", previous_registry_digest=None)

    def test_duplicate_unknown_and_digest_tamper_fail_closed(self):
        row = _load_fixture()["future_unexposed"]
        with self.assertRaises(ValueError):
            build_intake_registry([row, copy.deepcopy(row)], "2026-09-02T00:30:00Z", previous_registry_digest=None)
        mutated = copy.deepcopy(row)
        mutated["unexpected"] = True
        with self.assertRaises(ValueError):
            build_intake_registry([mutated], "2026-09-02T00:30:00Z", previous_registry_digest=None)
        registry = build_intake_registry([row], "2026-09-02T00:30:00Z", previous_registry_digest=None)
        tampered = copy.deepcopy(registry)
        tampered["records"][0]["opaque_case_id"] = "tampered"
        with self.assertRaises(ValueError):
            validate_intake_registry(tampered)
        tampered = copy.deepcopy(registry)
        tampered["registry_digest"] = "0" * 64
        with self.assertRaises(ValueError):
            validate_intake_registry(tampered)

    def test_registry_digest_is_order_independent(self):
        fixture = _load_fixture()
        a = build_intake_registry(
            [fixture["future_unexposed"], fixture["historical_unexposed"]],
            "2026-09-02T00:30:00Z",
            previous_registry_digest=None,
        )
        b = build_intake_registry(
            [fixture["historical_unexposed"], fixture["future_unexposed"]],
            "2026-09-02T00:30:00Z",
            previous_registry_digest=None,
        )
        self.assertEqual(a, b)

    def test_successor_is_append_only(self):
        fixture = _load_fixture()
        blank = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        first = build_intake_registry(
            [fixture["future_unexposed"]],
            "2026-09-02T00:30:00Z",
            previous_registry_digest=blank["registry_digest"],
        )
        validate_intake_registry_successor(first, blank)
        second = build_intake_registry(
            [fixture["future_unexposed"], fixture["historical_unexposed"]],
            "2026-09-02T00:40:00Z",
            previous_registry_digest=first["registry_digest"],
        )
        validate_intake_registry_successor(second, first)
        deleted = build_intake_registry(
            [fixture["historical_unexposed"]],
            "2026-09-02T00:40:00Z",
            previous_registry_digest=first["registry_digest"],
        )
        with self.assertRaises(ValueError):
            validate_intake_registry_successor(deleted, first)
        changed = copy.deepcopy(fixture["future_unexposed"])
        changed["source_record_digest"] = "f" * 64
        mutated = build_intake_registry(
            [changed, fixture["historical_unexposed"]],
            "2026-09-02T00:40:00Z",
            previous_registry_digest=first["registry_digest"],
        )
        with self.assertRaises(ValueError):
            validate_intake_registry_successor(mutated, first)

    def test_public_template_schema_and_runbook_are_safe(self):
        template = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        self.assertEqual(template["records"], [])
        self.assertFalse(template["promotion_allowed"])
        self.assertEqual(validate_intake_registry(template), template)
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(schema["additionalProperties"], False)
        text = RUNBOOK.read_text(encoding="utf-8")
        for marker in (
            "FUTURE_EVENT",
            "HISTORICAL_UNEXPOSED",
            "INELIGIBLE_SOURCE_PROVENANCE",
            "PREVIOUSLY_EXPOSED",
            "S1",
            "git 外",
        ):
            self.assertIn(marker, text)

    def test_cli_build_requires_explicit_output_and_validate_is_aggregate_only(self):
        fixture = _load_fixture()
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            records_path = td / "records.json"
            records_path.write_text(json.dumps([fixture["future_unexposed"]]), encoding="utf-8")
            proc = subprocess.run(
                [str(PYTHON), str(CLI), "build", "--records", str(records_path), "--locked-at", "2026-09-02T00:30:00Z"],
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertNotEqual(proc.returncode, 0)
            output = td / "registry.json"
            subprocess.run(
                [str(PYTHON), str(CLI), "build", "--records", str(records_path), "--locked-at", "2026-09-02T00:30:00Z", "--output", str(output)],
                cwd=ROOT,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertTrue(output.exists())
            proc = subprocess.run(
                [str(PYTHON), str(CLI), "validate", "--registry", str(output)],
                cwd=ROOT,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            summary = json.loads(proc.stdout.decode("utf-8"))
            self.assertEqual(summary["status"], "VALID")
            self.assertEqual(summary["record_count"], 1)
            rendered = proc.stdout.decode("utf-8")
            self.assertNotIn("case-future-a", rendered)
            self.assertNotIn("source_record_digest", rendered)

    def test_intake_authority_does_not_import_scoring_or_private_case_data(self):
        files = [
            ROOT / "engine" / "distribution" / "claim_consumption_case_intake.py",
            ROOT / "tools" / "validate_v16_prospective_case_intake.py",
            RUNBOOK,
        ]
        text = "\n".join(path.read_text(encoding="utf-8") for path in files)
        for forbidden in (
            "evaluate_claim_consumption_qualification",
            "evaluate_claim_consumption_private_threshold",
            "build_claim_consumption_contract",
            "render_with_caveat",
            "expected_authorization",
            "actual_event",
            "birth_date",
            "subject_name",
        ):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
