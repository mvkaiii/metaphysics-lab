"""Validate and normalize the Task3 v2.1 independent-oracle artifacts.

This adapter does not calculate or alter expected values.  It validates exact
artifact bindings and maps the clean-room executor's output schema into the
existing finalizer input schema.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from typing import Any, Mapping, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.finalize_bazi_decadal_reference_packet import _validate_oracle_bundle
from tools.materialize_bazi_decadal_case_inputs import validate_case_input_bundle
from tools.seal_bazi_decadal_reference_inputs import validate_preoracle_seal

ORACLE_SOURCE_SHA256 = "d4a4fdff95abb64e700ae9ebe966332546b373096aac6af56af8e2933fa815ac"
ORACLE_OUTPUT_FILE_SHA256 = "1743703e63183a5a76e710578d8548e26b03849c917de2fb7f107f3f25906362"
SEALING_RECEIPT_FILE_SHA256 = "40edf01200096a16d47221efe2458fec8e7a52ad39b86fa146d54be0e02b6dc3"
SOURCE_RECORD_FILE_SHA256 = "bc56d8d54c3e1ea78c844bbe68d21bc6de7fc70146e6e0d729ec887b696135a5"
CONTRACT_SHA256 = "b47de7809cadb82159c272b2d2d7fb3bbc7ffc99d9e8ed6c1fa60a1bf3c900e4"
CASE_BUNDLE_SHA256 = "939f8e29123acabfc16366b05622d1d3598b6aa72c4cc54cf96db3ce6e35128e"
PREORACLE_SEAL_SHA256 = "53f4e249f4f6e13fd26e9859101cceeaac31a1f186c155653a24e79f02dd4a27"
EXPECTED_PATHS = [
    "/decadal_direction",
    "/periods/0/pillar",
    "/periods/0/start_age_years",
    "/periods/0/start_datetime",
    "/periods/1/end_datetime",
]
EXPECTED_CASE_IDS = [f"bdv2-{i:03d}" for i in range(1, 13)]


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _aware_datetime(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("expected ISO-8601 datetime string")
    match = re.fullmatch(
        r"(\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2})(?:\\.(\\d{1,9}))?([+-]\\d{2}:\\d{2})",
        value,
    )
    if match is None:
        raise ValueError("invalid offset ISO-8601 datetime")
    fraction = match.group(2)
    normalized = match.group(1)
    if fraction:
        normalized += "." + fraction[:6].ljust(6, "0")
    normalized += match.group(3)
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("datetime must contain explicit offset")
    return parsed


def _finite(value: Any) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
    )


def validate_and_normalize(
    *,
    oracle_source: Path,
    source_record: Path,
    oracle_output: Path,
    sealing_receipt: Path,
    case_bundle_path: Path,
    preoracle_seal_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    errors: list[str] = []

    observed_files = {
        "oracle_source_sha256": file_sha256(oracle_source),
        "source_record_file_sha256": file_sha256(source_record),
        "oracle_output_file_sha256": file_sha256(oracle_output),
        "sealing_receipt_file_sha256": file_sha256(sealing_receipt),
    }
    expected_files = {
        "oracle_source_sha256": ORACLE_SOURCE_SHA256,
        "source_record_file_sha256": SOURCE_RECORD_FILE_SHA256,
        "oracle_output_file_sha256": ORACLE_OUTPUT_FILE_SHA256,
        "sealing_receipt_file_sha256": SEALING_RECEIPT_FILE_SHA256,
    }
    for key, expected in expected_files.items():
        if observed_files[key] != expected:
            errors.append(f"{key}: digest mismatch")

    record = source_record.read_text(encoding="utf-8")
    if record != f"{ORACLE_SOURCE_SHA256}  oracle.cjs\n":
        errors.append("source record: exact content mismatch")

    output = _load(oracle_output)
    receipt = _load(sealing_receipt)
    cases = _load(case_bundle_path)
    seal = _load(preoracle_seal_path)

    case_errors = validate_case_input_bundle(cases)
    if case_errors:
        errors.extend("case_bundle: " + item for item in case_errors)
    seal_errors = validate_preoracle_seal(seal)
    if seal_errors:
        errors.extend("preoracle_seal: " + item for item in seal_errors)

    if cases.get("bundle_sha256") != CASE_BUNDLE_SHA256:
        errors.append("case bundle canonical binding mismatch")
    if seal.get("seal_sha256") != PREORACLE_SEAL_SHA256:
        errors.append("pre-oracle canonical binding mismatch")
    if seal.get("profile", {}).get("specification_sha256") != CONTRACT_SHA256:
        errors.append("contract binding mismatch in pre-oracle seal")

    expected_output_top = {
        "schema_version", "bundle_type", "execution_contract_sha256",
        "case_bundle_sha256", "preoracle_seal_sha256", "oracle_source_sha256",
        "comparison_paths", "source_precision_seconds",
        "source_precision_policy", "cases",
    }
    if set(output) != expected_output_top:
        errors.append("oracle output top-level field census mismatch")
    if output.get("schema_version") != "1.0":
        errors.append("oracle output schema_version")
    if output.get("bundle_type") != "bazi_decadal_independent_oracle_output":
        errors.append("oracle output bundle_type")
    if output.get("execution_contract_sha256") != CONTRACT_SHA256:
        errors.append("oracle output contract binding")
    if output.get("case_bundle_sha256") != CASE_BUNDLE_SHA256:
        errors.append("oracle output case-bundle binding")
    if output.get("preoracle_seal_sha256") != PREORACLE_SEAL_SHA256:
        errors.append("oracle output pre-oracle binding")
    if output.get("oracle_source_sha256") != ORACLE_SOURCE_SHA256:
        errors.append("oracle output source binding")
    if output.get("comparison_paths") != EXPECTED_PATHS:
        errors.append("oracle output comparison path census")
    if output.get("source_precision_seconds") != 60:
        errors.append("oracle output source precision")
    if output.get("source_precision_policy") != "conservative +/-60 seconds":
        errors.append("oracle output source precision policy")

    output_cases = output.get("cases")
    if not isinstance(output_cases, list) or len(output_cases) != 12:
        errors.append("oracle output case count")
        output_cases = []
    sealed_cases = {case["case_id"]: case for case in cases.get("cases", [])}
    if [case.get("case_id") for case in output_cases] != EXPECTED_CASE_IDS:
        errors.append("oracle output case IDs/order")
    for index, result in enumerate(output_cases):
        case_id = result.get("case_id")
        if set(result) != {"case_id", "input_sha256", "expected_values"}:
            errors.append(f"{case_id or index}: oracle result field census")
            continue
        sealed = sealed_cases.get(case_id)
        if sealed is None:
            errors.append(f"{case_id}: unknown case")
            continue
        if result.get("input_sha256") != sealed.get("input_sha256"):
            errors.append(f"{case_id}: input digest mismatch")
        expected_values = result.get("expected_values")
        if not isinstance(expected_values, Mapping):
            errors.append(f"{case_id}: expected_values must be object")
            continue
        if list(expected_values) != EXPECTED_PATHS:
            errors.append(f"{case_id}: expected path census/order")
            continue
        if expected_values["/decadal_direction"] not in {"forward", "reverse"}:
            errors.append(f"{case_id}: direction value")
        pillar = expected_values["/periods/0/pillar"]
        if not isinstance(pillar, str) or len(pillar) != 2:
            errors.append(f"{case_id}: first pillar value")
        if not _finite(expected_values["/periods/0/start_age_years"]):
            errors.append(f"{case_id}: start_age_years not finite")
        for pointer in (
            "/periods/0/start_datetime",
            "/periods/1/end_datetime",
        ):
            try:
                _aware_datetime(expected_values[pointer])
            except (TypeError, ValueError):
                errors.append(f"{case_id}: {pointer} invalid datetime")

    required_receipt = {
        "pre_execution_gate": "PASS",
        "pre_execution_gate_confirmed_by_user": True,
        "oracle_source_frozen_before_expected_value_generation": True,
        "oracle_source_sha256": ORACLE_SOURCE_SHA256,
        "oracle_source_sha256_after_generation": ORACLE_SOURCE_SHA256,
        "oracle_source_unmodified_after_expected_value_generation": True,
        "sealed_case_count": 12,
        "executed_case_count": 12,
        "production_code_accessed": False,
        "production_output_accessed": False,
        "production_code_output_accessed": False,
        "production_comparison_performed": False,
        "prior_comparison_outcomes_accessed": False,
        "prior_qualification_outcomes_accessed": False,
        "inputs_unmodified_after_execution": True,
        "execution_contract_sha256": CONTRACT_SHA256,
        "case_bundle_sha256": CASE_BUNDLE_SHA256,
        "preoracle_seal_sha256": PREORACLE_SEAL_SHA256,
        "oracle_output_sha256": ORACLE_OUTPUT_FILE_SHA256,
        "source_precision_seconds": 60,
        "source_precision_policy": "conservative +/-60 seconds",
    }
    for key, expected in required_receipt.items():
        if receipt.get(key) != expected:
            errors.append(f"receipt.{key}: binding/attestation mismatch")
    if receipt.get("comparison_paths") != EXPECTED_PATHS:
        errors.append("receipt.comparison_paths")
    if receipt.get("executed_case_ids") != EXPECTED_CASE_IDS:
        errors.append("receipt.executed_case_ids")
    if receipt.get("runtime") != "v24.15.0":
        errors.append("receipt.runtime")

    try:
        frozen = _aware_datetime(receipt.get("freeze_recorded_at"))
        started = _aware_datetime(receipt.get("expected_value_generation_started_at"))
        completed = _aware_datetime(receipt.get("execution_completed_at"))
        if not (frozen < started <= completed):
            errors.append("receipt chronology: expected freeze < generation <= completion")
    except (TypeError, ValueError):
        errors.append("receipt chronology: invalid datetime")

    source_text = oracle_source.read_text(encoding="utf-8")
    requires = re.findall(r"require\((?:'|\")(.*?)(?:'|\")\)", source_text)
    if sorted(requires) != sorted(["node:fs", "node:path", "node:crypto", "node:assert/strict"]):
        errors.append("oracle source imports: unexpected dependency")
    forbidden_runtime_markers = (
        "child_process", "execSync", "spawnSync", "node:http", "node:https",
        "node:net", "node:tls", "fetch(", "github.com", "api.github.com",
    )
    if any(marker in source_text for marker in forbidden_runtime_markers):
        errors.append("oracle source static scan: external access primitive detected")

    if errors:
        raise ValueError("; ".join(sorted(set(errors))))

    normalized_cases = []
    for result in output_cases:
        normalized_cases.append({
            "case_id": result["case_id"],
            "input_sha256": result["input_sha256"],
            "comparisons": [
                {
                    "path": pointer,
                    "status": "provided",
                    "expected": result["expected_values"][pointer],
                }
                for pointer in EXPECTED_PATHS
            ],
        })

    oracle_bundle = {
        "schema_version": "1.0",
        "preoracle_seal_sha256": PREORACLE_SEAL_SHA256,
        "oracle_builder_id": "codex-cleanroom-node-v24.15.0",
        "oracle_code_sha256": ORACLE_SOURCE_SHA256,
        "production_code_access": False,
        "production_output_access": False,
        "comparison_result_access_before_seal": False,
        "attestation": (
            "PRE-EXECUTION GATE PASS; oracle source frozen before expected-value "
            "generation; 12 sealed cases executed; production code/output not "
            "accessed; prior comparison/qualification outcomes not accessed; "
            "production comparison not performed; source unchanged after generation."
        ),
        "sealed_at": receipt["execution_completed_at"],
        "sealed_by": "independent_cleanroom_executor",
        "cases": normalized_cases,
    }
    oracle_bundle_errors = _validate_oracle_bundle(oracle_bundle)
    if oracle_bundle_errors:
        raise ValueError("normalized oracle bundle invalid: " + "; ".join(oracle_bundle_errors))

    intake_receipt = {
        "schema_version": "1.0",
        "status": "ORACLE_ARTIFACTS_VALIDATED",
        "artifact_file_sha256": observed_files,
        "bindings": {
            "execution_contract_sha256": CONTRACT_SHA256,
            "case_bundle_sha256": CASE_BUNDLE_SHA256,
            "preoracle_seal_sha256": PREORACLE_SEAL_SHA256,
            "oracle_source_sha256": ORACLE_SOURCE_SHA256,
            "oracle_output_file_sha256": ORACLE_OUTPUT_FILE_SHA256,
        },
        "case_count": 12,
        "comparison_path_count_per_case": 5,
        "expected_value_count": 60,
        "static_source_scan": {
            "external_runtime_imports_detected": False,
            "network_or_process_primitives_detected": False,
            "note": "Static scan is supporting evidence only; executor receipt remains an attestation.",
        },
        "independence_assessment": "DECLARED_NOT_VERIFIED",
        "next_gate": "FINALIZE_REFERENCE_AND_COMPARE_FROZEN_PRODUCTION_CANDIDATE",
    }
    return oracle_bundle, intake_receipt


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--oracle-source", required=True, type=Path)
    parser.add_argument("--source-record", required=True, type=Path)
    parser.add_argument("--oracle-output", required=True, type=Path)
    parser.add_argument("--sealing-receipt", required=True, type=Path)
    parser.add_argument("--case-bundle", required=True, type=Path)
    parser.add_argument("--preoracle-seal", required=True, type=Path)
    parser.add_argument("--normalized-output", required=True, type=Path)
    parser.add_argument("--intake-receipt", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        normalized, receipt = validate_and_normalize(
            oracle_source=args.oracle_source,
            source_record=args.source_record,
            oracle_output=args.oracle_output,
            sealing_receipt=args.sealing_receipt,
            case_bundle_path=args.case_bundle,
            preoracle_seal_path=args.preoracle_seal,
        )
        for path, payload in (
            (args.normalized_output, normalized),
            (args.intake_receipt, receipt),
        ):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
        print(json.dumps({
            "status": receipt["status"],
            "case_count": receipt["case_count"],
            "expected_value_count": receipt["expected_value_count"],
            "normalized_output": str(args.normalized_output),
            "intake_receipt": str(args.intake_receipt),
        }, ensure_ascii=False, sort_keys=True))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ingest_bazi_decadal_oracle_v21: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
