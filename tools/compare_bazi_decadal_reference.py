"""Compare sealed independent Bazi decadal reference packets with engine-view data.

This module deliberately does not calculate Bazi values, select cases, create
oracle expected values, or decide qualification/promotion. It validates a
sealed reference packet and performs deterministic field comparisons only.
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


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_REFERENCE_TOP = {
    "schema_version", "status", "profile", "independence", "source_bindings",
    "sealed_at", "sealed_by", "cases",
}
_PROFILE_FIELDS = {"profile_id", "rule_version", "decadal_rule", "age_basis"}
_INDEPENDENCE_FIELDS = {
    "oracle_builder_id", "oracle_code_sha256", "production_code_access",
    "production_output_access", "comparison_result_access_before_seal",
    "attestation",
}
_SOURCE_FIELDS = {
    "provider", "role", "source_url", "source_sha256", "timezone",
    "published_precision_seconds",
}
_CASE_FIELDS = {"case_id", "input_sha256", "comparisons"}
_COMPARISON_FIELDS = {"path", "kind", "expected", "tolerance", "reason"}
_ACTUAL_TOP = {"schema_version", "cases"}
_ACTUAL_CASE_FIELDS = {"case_id", "input_sha256", "engine_view"}
_KINDS = {
    "exact", "number_abs", "datetime_abs_seconds", "not_comparable",
    "missing_reference",
}
_MISSING = object()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _unknown_fields(value, allowed, path, errors):
    for key in sorted(set(value) - allowed):
        errors.append(f"{path}: unknown field {key!r}")


def _string(value, path, errors):
    if not isinstance(value, str) or not value:
        errors.append(f"{path}: expected a non-empty string")
        return False
    return True


def _sha(value, path, errors):
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        errors.append(f"{path}: expected a lowercase SHA256")
        return False
    return True


def _finite_number(value):
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
    )


def _offset_datetime(value, path, errors):
    if not isinstance(value, str) or not value:
        errors.append(f"{path}: expected an ISO-8601 datetime string")
        return None
    match = re.fullmatch(
        r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d{1,9}))?([+-]\d{2}:\d{2})",
        value,
    )
    if match is None:
        errors.append(f"{path}: invalid ISO-8601 datetime")
        return None
    fraction = match.group(2)
    normalized = match.group(1)
    if fraction:
        normalized += "." + fraction[:6].ljust(6, "0")
    normalized += match.group(3)
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        errors.append(f"{path}: invalid ISO-8601 datetime")
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        errors.append(f"{path}: datetime requires an explicit offset")
        return None
    return parsed


def validate_reference_packet(packet: Mapping[str, Any]) -> list[str]:
    errors = []
    if not isinstance(packet, Mapping):
        return ["packet: expected an object"]
    _unknown_fields(packet, _REFERENCE_TOP, "packet", errors)
    for key in sorted(_REFERENCE_TOP):
        if key not in packet:
            errors.append(f"packet: missing field {key}")
    if packet.get("schema_version") != "1.0":
        errors.append("packet.schema_version: expected '1.0'")
    if packet.get("status") != "SEALED":
        errors.append("packet.status: expected SEALED")
    _offset_datetime(packet.get("sealed_at"), "packet.sealed_at", errors)
    _string(packet.get("sealed_by"), "packet.sealed_by", errors)

    profile = packet.get("profile")
    if not isinstance(profile, Mapping):
        errors.append("packet.profile: expected an object")
    else:
        _unknown_fields(profile, _PROFILE_FIELDS, "packet.profile", errors)
        expected_profile = {
            "profile_id": "bazi-natal-project-v1",
            "rule_version": "1.0-exp",
            "decadal_rule": "three-days-one-year-v1",
            "age_basis": "continuous_years_from_jie_interval",
        }
        for key, expected in expected_profile.items():
            if profile.get(key) != expected:
                errors.append(f"packet.profile.{key}: expected {expected!r}")

    independence = packet.get("independence")
    if not isinstance(independence, Mapping):
        errors.append("packet.independence: expected an object")
    else:
        _unknown_fields(independence, _INDEPENDENCE_FIELDS, "packet.independence", errors)
        _string(independence.get("oracle_builder_id"), "packet.independence.oracle_builder_id", errors)
        _sha(independence.get("oracle_code_sha256"), "packet.independence.oracle_code_sha256", errors)
        for key in ("production_code_access", "production_output_access", "comparison_result_access_before_seal"):
            if independence.get(key) is not False:
                errors.append(f"packet.independence.{key}: independent oracle requires false")
        _string(independence.get("attestation"), "packet.independence.attestation", errors)

    sources = packet.get("source_bindings")
    if not isinstance(sources, list) or not sources:
        errors.append("packet.source_bindings: expected a non-empty list")
    else:
        for index, source in enumerate(sources):
            path = f"packet.source_bindings[{index}]"
            if not isinstance(source, Mapping):
                errors.append(f"{path}: expected an object")
                continue
            _unknown_fields(source, _SOURCE_FIELDS, path, errors)
            for key in ("provider", "source_url", "timezone"):
                _string(source.get(key), f"{path}.{key}", errors)
            if source.get("role") != "astronomical_input":
                errors.append(f"{path}.role: expected astronomical_input")
            _sha(source.get("source_sha256"), f"{path}.source_sha256", errors)
            precision = source.get("published_precision_seconds")
            if isinstance(precision, bool) or not isinstance(precision, int) or precision <= 0:
                errors.append(f"{path}.published_precision_seconds: expected a positive integer")

    cases = packet.get("cases")
    case_ids = set()
    if not isinstance(cases, list) or not cases:
        errors.append("packet.cases: expected a non-empty list")
    else:
        for case_index, case in enumerate(cases):
            path = f"packet.cases[{case_index}]"
            if not isinstance(case, Mapping):
                errors.append(f"{path}: expected an object")
                continue
            _unknown_fields(case, _CASE_FIELDS, path, errors)
            case_id = case.get("case_id")
            if _string(case_id, f"{path}.case_id", errors):
                if case_id in case_ids:
                    errors.append(f"{path}.case_id: duplicate case_id {case_id!r}")
                case_ids.add(case_id)
            _sha(case.get("input_sha256"), f"{path}.input_sha256", errors)
            comparisons = case.get("comparisons")
            seen_paths = set()
            if not isinstance(comparisons, list) or not comparisons:
                errors.append(f"{path}.comparisons: expected a non-empty list")
                continue
            for row_index, row in enumerate(comparisons):
                row_path = f"{path}.comparisons[{row_index}]"
                if not isinstance(row, Mapping):
                    errors.append(f"{row_path}: expected an object")
                    continue
                _unknown_fields(row, _COMPARISON_FIELDS, row_path, errors)
                pointer = row.get("path")
                if not _string(pointer, f"{row_path}.path", errors):
                    continue
                if not pointer.startswith("/"):
                    errors.append(f"{row_path}.path: expected a JSON Pointer")
                if pointer in seen_paths:
                    errors.append(f"{row_path}.path: duplicate comparison path {pointer!r}")
                seen_paths.add(pointer)
                kind = row.get("kind")
                if kind not in _KINDS:
                    errors.append(f"{row_path}.kind: unsupported comparison kind")
                    continue
                if kind in {"not_comparable", "missing_reference"}:
                    _string(row.get("reason"), f"{row_path}.reason", errors)
                    if "expected" in row:
                        errors.append(f"{row_path}.expected: must be omitted for {kind}")
                    if "tolerance" in row:
                        errors.append(f"{row_path}.tolerance: must be omitted for {kind}")
                    continue
                if "expected" not in row:
                    errors.append(f"{row_path}.expected: required for {kind}")
                if kind == "exact":
                    if "tolerance" in row:
                        errors.append(f"{row_path}.tolerance: must be omitted for exact")
                elif kind == "number_abs":
                    if not _finite_number(row.get("expected")):
                        errors.append(f"{row_path}.expected: number_abs requires a finite number")
                    tolerance = row.get("tolerance")
                    if not _finite_number(tolerance) or tolerance < 0:
                        errors.append(f"{row_path}.tolerance: number_abs requires a non-negative finite tolerance")
                elif kind == "datetime_abs_seconds":
                    _offset_datetime(row.get("expected"), f"{row_path}.expected", errors)
                    tolerance = row.get("tolerance")
                    if not _finite_number(tolerance) or tolerance < 0:
                        errors.append(f"{row_path}.tolerance: datetime_abs_seconds requires a non-negative finite tolerance")
    return sorted(set(errors))


def _validate_actual_bundle(bundle):
    errors = []
    if not isinstance(bundle, Mapping):
        return ["actual: expected an object"]
    _unknown_fields(bundle, _ACTUAL_TOP, "actual", errors)
    if bundle.get("schema_version") != "1.0":
        errors.append("actual.schema_version: expected '1.0'")
    cases = bundle.get("cases")
    seen = set()
    if not isinstance(cases, list) or not cases:
        errors.append("actual.cases: expected a non-empty list")
        return sorted(set(errors))
    for index, case in enumerate(cases):
        path = f"actual.cases[{index}]"
        if not isinstance(case, Mapping):
            errors.append(f"{path}: expected an object")
            continue
        _unknown_fields(case, _ACTUAL_CASE_FIELDS, path, errors)
        case_id = case.get("case_id")
        if _string(case_id, f"{path}.case_id", errors):
            if case_id in seen:
                errors.append(f"{path}.case_id: duplicate case_id {case_id!r}")
            seen.add(case_id)
        _sha(case.get("input_sha256"), f"{path}.input_sha256", errors)
        if not isinstance(case.get("engine_view"), Mapping):
            errors.append(f"{path}.engine_view: expected an object")
    return sorted(set(errors))


def _pointer(value, pointer):
    current = value
    for token in pointer.split("/")[1:]:
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, Mapping):
            if token not in current:
                return _MISSING
            current = current[token]
        elif isinstance(current, list):
            if not token.isdigit():
                return _MISSING
            index = int(token)
            if index < 0 or index >= len(current):
                return _MISSING
            current = current[index]
        else:
            return _MISSING
    return current


def _compare_row(row, actual_value):
    kind = row["kind"]
    result = {
        "path": row["path"], "kind": kind, "status": None,
        "expected": row.get("expected"),
        "actual": None if actual_value is _MISSING else actual_value,
        "tolerance": row.get("tolerance"), "difference": None,
        "reason": row.get("reason"),
    }
    if kind == "missing_reference":
        result["status"] = "MISSING_REFERENCE"
        return result
    if kind == "not_comparable":
        result["status"] = "NOT_COMPARABLE"
        return result
    if actual_value is _MISSING:
        result["status"] = "MISMATCH"
        result["reason"] = "ACTUAL_FIELD_MISSING"
        return result
    if kind == "exact":
        result["status"] = "MATCH" if actual_value == row["expected"] else "MISMATCH"
        return result
    if kind == "number_abs":
        if not _finite_number(actual_value):
            result["status"] = "MISMATCH"
            result["reason"] = "ACTUAL_NOT_FINITE_NUMBER"
            return result
        difference = abs(float(actual_value) - float(row["expected"]))
        result["difference"] = difference
        result["status"] = "MATCH" if difference <= float(row["tolerance"]) else "MISMATCH"
        return result
    if kind == "datetime_abs_seconds":
        actual_errors = []
        actual_dt = _offset_datetime(actual_value, "actual_value", actual_errors)
        if actual_dt is None:
            result["status"] = "MISMATCH"
            result["reason"] = "ACTUAL_NOT_OFFSET_DATETIME"
            return result
        expected_errors = []
        expected_dt = _offset_datetime(row["expected"], "expected_value", expected_errors)
        if expected_dt is None:
            raise ValueError("validated reference datetime could not be parsed")
        difference = abs((actual_dt - expected_dt).total_seconds())
        result["difference"] = difference
        result["status"] = "MATCH" if difference <= float(row["tolerance"]) else "MISMATCH"
        return result
    raise ValueError(f"unsupported comparison kind: {kind}")


def compare_reference_packet(reference, actual_bundle):
    reference_errors = validate_reference_packet(reference)
    if reference_errors:
        raise ValueError("invalid reference packet: " + "; ".join(reference_errors))
    actual_errors = _validate_actual_bundle(actual_bundle)
    if actual_errors:
        raise ValueError("invalid actual bundle: " + "; ".join(actual_errors))
    reference_cases = {case["case_id"]: case for case in reference["cases"]}
    actual_cases = {case["case_id"]: case for case in actual_bundle["cases"]}
    if set(reference_cases) != set(actual_cases):
        missing = sorted(set(reference_cases) - set(actual_cases))
        extra = sorted(set(actual_cases) - set(reference_cases))
        raise ValueError("case census mismatch: missing=%s extra=%s" % (missing, extra))
    field_results = []
    counts = {"MATCH": 0, "MISMATCH": 0, "NOT_COMPARABLE": 0, "MISSING_REFERENCE": 0}
    for case_id in sorted(reference_cases):
        ref_case = reference_cases[case_id]
        actual_case = actual_cases[case_id]
        if ref_case["input_sha256"] != actual_case["input_sha256"]:
            raise ValueError(f"{case_id}: input digest mismatch")
        for row in ref_case["comparisons"]:
            compared = _compare_row(row, _pointer(actual_case["engine_view"], row["path"]))
            compared["case_id"] = case_id
            counts[compared["status"]] += 1
            field_results.append(compared)
    if counts["MISMATCH"]:
        comparison_result = "MISMATCH"
    elif counts["MISSING_REFERENCE"] or counts["NOT_COMPARABLE"]:
        comparison_result = "PARTIAL"
    else:
        comparison_result = "MATCH"
    field_results.sort(key=lambda item: (item["case_id"], item["path"]))
    return {
        "schema_version": "1.0",
        "comparison_result": comparison_result,
        "qualification_decision": "HUMAN_REVIEW_REQUIRED",
        "maturity_promotion": False,
        "independence_assessment": "DECLARED_NOT_VERIFIED",
        "reference_packet_sha256": _digest(reference),
        "actual_bundle_sha256": _digest(actual_bundle),
        "case_count": len(reference_cases),
        "counts": counts,
        "field_results": field_results,
    }


def _write_output(path, payload, overwrite):
    if path.exists() and not overwrite:
        raise FileExistsError("output exists; pass --overwrite to replace it: %s" % path)
    if not path.parent.exists():
        raise FileNotFoundError("output directory does not exist: %s" % path.parent)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8", newline="\n",
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--actual", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    try:
        reference = json.loads(args.reference.read_text(encoding="utf-8"))
        actual = json.loads(args.actual.read_text(encoding="utf-8"))
        report = compare_reference_packet(reference, actual)
        rendered = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        if args.output is None:
            sys.stdout.write(rendered)
        else:
            _write_output(args.output, report, args.overwrite)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("compare_bazi_decadal_reference: %s" % exc, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
