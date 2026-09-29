"""Build and validate a pre-oracle seal for Bazi decadal reference qualification.

The seal freezes only inputs that must predate an independent oracle:
written-profile identity, external source bytes, case census, comparison paths,
and tolerances. It never calculates Bazi values or stores expected values.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from typing import Any, Mapping, Optional, Sequence


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_TOP_FIELDS = {
    "schema_version",
    "status",
    "profile",
    "source_bindings",
    "case_census",
    "independence_boundary",
    "sealed_at",
    "sealed_by",
    "seal_sha256",
}
_PROFILE_FIELDS = {
    "profile_id",
    "rule_version",
    "decadal_rule",
    "age_basis",
    "specification_sha256",
}
_SOURCE_FIELDS = {
    "provider",
    "role",
    "source_url",
    "source_file_label",
    "source_sha256",
    "timezone",
    "published_precision_seconds",
}
_CASE_FIELDS = {
    "case_id",
    "input_sha256",
    "coverage_tags",
    "production_results_consulted_for_selection",
    "comparisons",
}
_COMPARISON_FIELDS = {"path", "kind", "tolerance", "reason"}
_INDEPENDENCE_FIELDS = {
    "expected_values_present",
    "oracle_may_receive_production_code",
    "oracle_may_receive_production_output",
    "oracle_may_receive_comparison_results_before_reference_seal",
}
_KINDS = {"exact", "number_abs", "datetime_abs_seconds", "not_comparable"}


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _string(value: Any, path: str, errors: list[str]) -> bool:
    if not isinstance(value, str) or not value:
        errors.append(f"{path}: expected a non-empty string")
        return False
    return True


def _sha(value: Any, path: str, errors: list[str]) -> bool:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        errors.append(f"{path}: expected a lowercase SHA256")
        return False
    return True


def _offset_datetime(value: Any, path: str, errors: list[str]) -> bool:
    if not isinstance(value, str) or not value:
        errors.append(f"{path}: expected an ISO-8601 datetime string")
        return False
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        errors.append(f"{path}: invalid ISO-8601 datetime")
        return False
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        errors.append(f"{path}: datetime requires an explicit offset")
        return False
    return True


def _finite_nonnegative(value: Any) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
        and value >= 0
    )


def _unknown_fields(value: Mapping[str, Any], allowed: set[str], path: str, errors: list[str]) -> None:
    for key in sorted(set(value) - allowed):
        errors.append(f"{path}: unknown field {key!r}")


def _seal_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    material = deepcopy(dict(payload))
    material.pop("seal_sha256", None)
    return material


def validate_preoracle_seal(payload: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, Mapping):
        return ["seal: expected an object"]
    _unknown_fields(payload, _TOP_FIELDS, "seal", errors)
    for key in sorted(_TOP_FIELDS):
        if key not in payload:
            errors.append(f"seal: missing field {key}")
    if payload.get("schema_version") != "1.0":
        errors.append("seal.schema_version: expected '1.0'")
    if payload.get("status") != "PRE_ORACLE_SEALED":
        errors.append("seal.status: expected PRE_ORACLE_SEALED")
    _offset_datetime(payload.get("sealed_at"), "seal.sealed_at", errors)
    _string(payload.get("sealed_by"), "seal.sealed_by", errors)

    profile = payload.get("profile")
    if not isinstance(profile, Mapping):
        errors.append("seal.profile: expected an object")
    else:
        _unknown_fields(profile, _PROFILE_FIELDS, "seal.profile", errors)
        expected = {
            "profile_id": "bazi-natal-project-v1",
            "rule_version": "1.0-exp",
            "decadal_rule": "three-days-one-year-v1",
            "age_basis": "continuous_years_from_jie_interval",
        }
        for key, value in expected.items():
            if profile.get(key) != value:
                errors.append(f"seal.profile.{key}: expected {value!r}")
        _sha(profile.get("specification_sha256"), "seal.profile.specification_sha256", errors)

    sources = payload.get("source_bindings")
    if not isinstance(sources, list) or not sources:
        errors.append("seal.source_bindings: expected a non-empty list")
    else:
        seen_source_digests = set()
        for index, source in enumerate(sources):
            path = f"seal.source_bindings[{index}]"
            if not isinstance(source, Mapping):
                errors.append(f"{path}: expected an object")
                continue
            _unknown_fields(source, _SOURCE_FIELDS, path, errors)
            for key in ("provider", "source_url", "source_file_label", "timezone"):
                _string(source.get(key), f"{path}.{key}", errors)
            if source.get("role") != "astronomical_input":
                errors.append(f"{path}.role: expected astronomical_input")
            if _sha(source.get("source_sha256"), f"{path}.source_sha256", errors):
                if source["source_sha256"] in seen_source_digests:
                    errors.append(f"{path}.source_sha256: duplicate source digest")
                seen_source_digests.add(source["source_sha256"])
            precision = source.get("published_precision_seconds")
            if isinstance(precision, bool) or not isinstance(precision, int) or precision <= 0:
                errors.append(f"{path}.published_precision_seconds: expected a positive integer")

    cases = payload.get("case_census")
    if not isinstance(cases, list) or not cases:
        errors.append("seal.case_census: expected a non-empty list")
    else:
        seen_case_ids = set()
        for index, case in enumerate(cases):
            path = f"seal.case_census[{index}]"
            if not isinstance(case, Mapping):
                errors.append(f"{path}: expected an object")
                continue
            _unknown_fields(case, _CASE_FIELDS, path, errors)
            case_id = case.get("case_id")
            if _string(case_id, f"{path}.case_id", errors):
                if case_id in seen_case_ids:
                    errors.append(f"{path}.case_id: duplicate case_id {case_id!r}")
                seen_case_ids.add(case_id)
            _sha(case.get("input_sha256"), f"{path}.input_sha256", errors)
            tags = case.get("coverage_tags")
            if (
                not isinstance(tags, list)
                or not tags
                or any(not isinstance(tag, str) or not tag for tag in tags)
                or len(tags) != len(set(tags))
            ):
                errors.append(f"{path}.coverage_tags: expected unique non-empty strings")
            if case.get("production_results_consulted_for_selection") is not False:
                errors.append(f"{path}.production_results_consulted_for_selection: expected false")
            comparisons = case.get("comparisons")
            if not isinstance(comparisons, list) or not comparisons:
                errors.append(f"{path}.comparisons: expected a non-empty list")
                continue
            seen_paths = set()
            for row_index, row in enumerate(comparisons):
                row_path = f"{path}.comparisons[{row_index}]"
                if not isinstance(row, Mapping):
                    errors.append(f"{row_path}: expected an object")
                    continue
                _unknown_fields(row, _COMPARISON_FIELDS, row_path, errors)
                pointer = row.get("path")
                if _string(pointer, f"{row_path}.path", errors):
                    if not pointer.startswith("/"):
                        errors.append(f"{row_path}.path: expected a JSON Pointer")
                    if pointer in seen_paths:
                        errors.append(f"{row_path}.path: duplicate comparison path {pointer!r}")
                    seen_paths.add(pointer)
                kind = row.get("kind")
                if kind not in _KINDS:
                    errors.append(f"{row_path}.kind: unsupported comparison kind")
                    continue
                if kind == "exact":
                    if "tolerance" in row:
                        errors.append(f"{row_path}.tolerance: must be omitted for exact")
                    if "reason" in row:
                        errors.append(f"{row_path}.reason: must be omitted for exact")
                elif kind in {"number_abs", "datetime_abs_seconds"}:
                    if not _finite_nonnegative(row.get("tolerance")):
                        errors.append(f"{row_path}.tolerance: expected a non-negative finite number")
                    if "reason" in row:
                        errors.append(f"{row_path}.reason: must be omitted for {kind}")
                elif kind == "not_comparable":
                    _string(row.get("reason"), f"{row_path}.reason", errors)
                    if "tolerance" in row:
                        errors.append(f"{row_path}.tolerance: must be omitted for not_comparable")

    boundary = payload.get("independence_boundary")
    if not isinstance(boundary, Mapping):
        errors.append("seal.independence_boundary: expected an object")
    else:
        _unknown_fields(boundary, _INDEPENDENCE_FIELDS, "seal.independence_boundary", errors)
        expected_flags = {
            "expected_values_present": False,
            "oracle_may_receive_production_code": False,
            "oracle_may_receive_production_output": False,
            "oracle_may_receive_comparison_results_before_reference_seal": False,
        }
        for key, expected in expected_flags.items():
            if boundary.get(key) is not expected:
                errors.append(f"seal.independence_boundary.{key}: expected {expected}")

    seal_sha = payload.get("seal_sha256")
    if _sha(seal_sha, "seal.seal_sha256", errors):
        expected_sha = _digest(_seal_payload(payload))
        if seal_sha != expected_sha:
            errors.append("seal.seal_sha256: digest mismatch")
    return sorted(set(errors))


def build_preoracle_seal(draft: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(draft, Mapping):
        raise ValueError("draft must be an object")
    sealed = deepcopy(dict(draft))
    sealed["status"] = "PRE_ORACLE_SEALED"
    sealed["seal_sha256"] = "0" * 64
    sealed["seal_sha256"] = _digest(_seal_payload(sealed))
    errors = validate_preoracle_seal(sealed)
    if errors:
        raise ValueError("invalid pre-oracle seal: " + "; ".join(errors))
    return sealed


def _write_output(path: Path, payload: Mapping[str, Any], overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(f"output exists; pass --overwrite to replace it: {path}")
    if not path.parent.exists():
        raise FileNotFoundError(f"output directory does not exist: {path.parent}")
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draft", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    try:
        draft = json.loads(args.draft.read_text(encoding="utf-8"))
        sealed = build_preoracle_seal(draft)
        rendered = json.dumps(sealed, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        if args.output is None:
            sys.stdout.write(rendered)
        else:
            _write_output(args.output, sealed, args.overwrite)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"seal_bazi_decadal_reference_inputs: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
