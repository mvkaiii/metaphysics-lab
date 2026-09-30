"""Finalize an independent Bazi decadal reference packet from a pre-oracle seal.

This module does not calculate Bazi values. It binds independently produced
expected values back to the exact pre-oracle case/path/tolerance census and
emits the reference-packet schema consumed by compare_bazi_decadal_reference.
"""

from __future__ import annotations

from copy import deepcopy
import math
from typing import Any, Mapping

from tools.compare_bazi_decadal_reference import validate_reference_packet
from tools.seal_bazi_decadal_reference_inputs import validate_preoracle_seal


_ORACLE_TOP = {
    "schema_version",
    "preoracle_seal_sha256",
    "oracle_builder_id",
    "oracle_code_sha256",
    "production_code_access",
    "production_output_access",
    "comparison_result_access_before_seal",
    "attestation",
    "sealed_at",
    "sealed_by",
    "cases",
}
_ORACLE_CASE_FIELDS = {"case_id", "input_sha256", "comparisons"}
_ORACLE_ROW_FIELDS = {"path", "status", "expected", "reason"}
_ORACLE_STATUSES = {"provided", "missing_reference"}


def _finite_number(value: Any) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
    )


def _validate_oracle_bundle(oracle: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(oracle, Mapping):
        return ["oracle: expected an object"]
    for key in sorted(set(oracle) - _ORACLE_TOP):
        errors.append(f"oracle: unknown field {key!r}")
    for key in sorted(_ORACLE_TOP):
        if key not in oracle:
            errors.append(f"oracle: missing field {key}")
    if oracle.get("schema_version") != "1.0":
        errors.append("oracle.schema_version: expected '1.0'")
    for key in (
        "preoracle_seal_sha256",
        "oracle_builder_id",
        "oracle_code_sha256",
        "attestation",
        "sealed_at",
        "sealed_by",
    ):
        if not isinstance(oracle.get(key), str) or not oracle[key]:
            errors.append(f"oracle.{key}: expected a non-empty string")
    for key in (
        "production_code_access",
        "production_output_access",
        "comparison_result_access_before_seal",
    ):
        if oracle.get(key) is not False:
            errors.append(f"oracle.{key}: independent oracle requires false")

    cases = oracle.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("oracle.cases: expected a non-empty list")
        return sorted(set(errors))
    seen_case_ids = set()
    for case_index, case in enumerate(cases):
        path = f"oracle.cases[{case_index}]"
        if not isinstance(case, Mapping):
            errors.append(f"{path}: expected an object")
            continue
        for key in sorted(set(case) - _ORACLE_CASE_FIELDS):
            errors.append(f"{path}: unknown field {key!r}")
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            errors.append(f"{path}.case_id: expected a non-empty string")
        elif case_id in seen_case_ids:
            errors.append(f"{path}.case_id: duplicate case_id {case_id!r}")
        else:
            seen_case_ids.add(case_id)
        if not isinstance(case.get("input_sha256"), str) or not case["input_sha256"]:
            errors.append(f"{path}.input_sha256: expected a non-empty string")
        rows = case.get("comparisons")
        if not isinstance(rows, list):
            errors.append(f"{path}.comparisons: expected a list")
            continue
        seen_paths = set()
        for row_index, row in enumerate(rows):
            row_path = f"{path}.comparisons[{row_index}]"
            if not isinstance(row, Mapping):
                errors.append(f"{row_path}: expected an object")
                continue
            for key in sorted(set(row) - _ORACLE_ROW_FIELDS):
                errors.append(f"{row_path}: unknown field {key!r}")
            pointer = row.get("path")
            if not isinstance(pointer, str) or not pointer.startswith("/"):
                errors.append(f"{row_path}.path: expected a JSON Pointer")
            elif pointer in seen_paths:
                errors.append(f"{row_path}.path: duplicate path {pointer!r}")
            else:
                seen_paths.add(pointer)
            status = row.get("status")
            if status not in _ORACLE_STATUSES:
                errors.append(f"{row_path}.status: expected provided or missing_reference")
                continue
            if status == "provided":
                if "expected" not in row:
                    errors.append(f"{row_path}.expected: required when status=provided")
                if "reason" in row:
                    errors.append(f"{row_path}.reason: must be omitted when status=provided")
            else:
                if "expected" in row:
                    errors.append(f"{row_path}.expected: must be omitted when status=missing_reference")
                if not isinstance(row.get("reason"), str) or not row["reason"]:
                    errors.append(f"{row_path}.reason: required when status=missing_reference")
    return sorted(set(errors))


def finalize_reference_packet(preoracle: Mapping[str, Any], oracle: Mapping[str, Any]) -> dict[str, Any]:
    pre_errors = validate_preoracle_seal(preoracle)
    if pre_errors:
        raise ValueError("invalid pre-oracle seal: " + "; ".join(pre_errors))
    oracle_errors = _validate_oracle_bundle(oracle)
    if oracle_errors:
        raise ValueError("invalid oracle bundle: " + "; ".join(oracle_errors))
    if oracle["preoracle_seal_sha256"] != preoracle["seal_sha256"]:
        raise ValueError("oracle bundle does not bind the supplied pre-oracle seal")

    pre_cases = {case["case_id"]: case for case in preoracle["case_census"]}
    oracle_cases = {case["case_id"]: case for case in oracle["cases"]}
    if set(pre_cases) != set(oracle_cases):
        missing = sorted(set(pre_cases) - set(oracle_cases))
        extra = sorted(set(oracle_cases) - set(pre_cases))
        raise ValueError(f"oracle case census mismatch: missing={missing} extra={extra}")

    cases = []
    for case_id in sorted(pre_cases):
        pre_case = pre_cases[case_id]
        oracle_case = oracle_cases[case_id]
        if oracle_case["input_sha256"] != pre_case["input_sha256"]:
            raise ValueError(f"{case_id}: oracle input digest mismatch")
        planned = {row["path"]: row for row in pre_case["comparisons"]}
        supplied = {row["path"]: row for row in oracle_case["comparisons"]}
        required_oracle_paths = {
            path for path, row in planned.items() if row["kind"] != "not_comparable"
        }
        if set(supplied) != required_oracle_paths:
            missing = sorted(required_oracle_paths - set(supplied))
            extra = sorted(set(supplied) - required_oracle_paths)
            raise ValueError(
                f"{case_id}: oracle comparison census mismatch: missing={missing} extra={extra}"
            )

        output_rows = []
        for pointer in sorted(planned):
            plan = planned[pointer]
            if plan["kind"] == "not_comparable":
                output_rows.append(
                    {"path": pointer, "kind": "not_comparable", "reason": plan["reason"]}
                )
                continue
            result = supplied[pointer]
            if result["status"] == "missing_reference":
                output_rows.append(
                    {"path": pointer, "kind": "missing_reference", "reason": result["reason"]}
                )
                continue
            expected = result["expected"]
            if plan["kind"] == "number_abs" and not _finite_number(expected):
                raise ValueError(f"{case_id}{pointer}: expected must be a finite number")
            row = {"path": pointer, "kind": plan["kind"], "expected": deepcopy(expected)}
            if "tolerance" in plan:
                row["tolerance"] = plan["tolerance"]
            output_rows.append(row)
        cases.append(
            {
                "case_id": case_id,
                "input_sha256": pre_case["input_sha256"],
                "comparisons": output_rows,
            }
        )

    profile = preoracle["profile"]
    source_bindings = [
        {
            "provider": source["provider"],
            "role": source["role"],
            "source_url": source["source_url"],
            "source_sha256": source["source_sha256"],
            "timezone": source["timezone"],
            "published_precision_seconds": source["published_precision_seconds"],
        }
        for source in preoracle["source_bindings"]
    ]
    reference = {
        "schema_version": "1.0",
        "status": "SEALED",
        "profile": {
            "profile_id": profile["profile_id"],
            "rule_version": profile["rule_version"],
            "decadal_rule": profile["decadal_rule"],
            "age_basis": profile["age_basis"],
        },
        "independence": {
            "oracle_builder_id": oracle["oracle_builder_id"],
            "oracle_code_sha256": oracle["oracle_code_sha256"],
            "production_code_access": oracle["production_code_access"],
            "production_output_access": oracle["production_output_access"],
            "comparison_result_access_before_seal": oracle["comparison_result_access_before_seal"],
            "attestation": oracle["attestation"],
        },
        "source_bindings": source_bindings,
        "sealed_at": oracle["sealed_at"],
        "sealed_by": oracle["sealed_by"],
        "cases": cases,
    }
    errors = validate_reference_packet(reference)
    if errors:
        raise ValueError("final reference packet is invalid: " + "; ".join(errors))
    return reference
