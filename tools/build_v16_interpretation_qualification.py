#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Mapping

INPUT_SCHEMA = "v1.6-private-qualification-input.v1"
SUMMARY_SCHEMA = "v1.6-private-qualification-summary.v1"
RESULTS = ("matched", "partial", "missed")
ANNUAL_ROLES = (
    "sustained_high",
    "localized_spike",
    "relative_low",
    "true_control",
    "uncertain",
)
CONTROL_RESULTS = ("false_negative", "not_false_negative")
CONTROL_SELECTIONS = ("selected", "abstain")

_TOP_LEVEL_FIELDS = frozenset(("schema_version", "cases"))
_CASE_FIELDS = frozenset((
    "case_id", "selector_v1", "selector_v2", "interpretation_v1",
    "interpretation_v2", "cutoff_contamination", "input_digest",
))
_SELECTOR_V1_FIELDS = frozenset(("control_result",))
_SELECTOR_V2_FIELDS = frozenset(("annual_role", "control_eligible", "control_selection"))
_INTERPRETATION_FIELDS = frozenset(("domain_result", "event_family_result", "false_positive", "abstained"))


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


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be a mapping")
    return value


def _exact_fields(value: Mapping[str, object], allowed: frozenset[str], field: str) -> None:
    unknown = sorted(set(value) - allowed)
    missing = sorted(allowed - set(value))
    if unknown:
        raise ValueError(f"{field} has unknown fields: {', '.join(unknown)}")
    if missing:
        raise ValueError(f"{field} is missing fields: {', '.join(missing)}")


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be non-empty text")
    return value


def _bool(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be boolean")
    return value


def _enum(value: object, allowed: tuple[str, ...], field: str) -> str:
    text = _text(value, field)
    if text not in allowed:
        raise ValueError(f"{field} has unsupported value: {text}")
    return text


def _sha256_text(value: object, field: str) -> str:
    text = _text(value, field)
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise ValueError(f"{field} must be lowercase sha256 hex")
    return text


def _normalize_interpretation(value: object, field: str) -> dict:
    raw = _mapping(value, field)
    _exact_fields(raw, _INTERPRETATION_FIELDS, field)
    return {
        "domain_result": _enum(raw["domain_result"], RESULTS, f"{field}.domain_result"),
        "event_family_result": _enum(raw["event_family_result"], RESULTS, f"{field}.event_family_result"),
        "false_positive": _bool(raw["false_positive"], f"{field}.false_positive"),
        "abstained": _bool(raw["abstained"], f"{field}.abstained"),
    }


def _normalize_case(value: object, index: int) -> dict:
    field = f"cases[{index}]"
    raw = _mapping(value, field)
    _exact_fields(raw, _CASE_FIELDS, field)

    selector_v1 = _mapping(raw["selector_v1"], f"{field}.selector_v1")
    _exact_fields(selector_v1, _SELECTOR_V1_FIELDS, f"{field}.selector_v1")

    selector_v2 = _mapping(raw["selector_v2"], f"{field}.selector_v2")
    _exact_fields(selector_v2, _SELECTOR_V2_FIELDS, f"{field}.selector_v2")

    return {
        "case_id": _text(raw["case_id"], f"{field}.case_id"),
        "selector_v1": {
            "control_result": _enum(
                selector_v1["control_result"], CONTROL_RESULTS, f"{field}.selector_v1.control_result"
            ),
        },
        "selector_v2": {
            "annual_role": _enum(selector_v2["annual_role"], ANNUAL_ROLES, f"{field}.selector_v2.annual_role"),
            "control_eligible": _bool(selector_v2["control_eligible"], f"{field}.selector_v2.control_eligible"),
            "control_selection": _enum(
                selector_v2["control_selection"], CONTROL_SELECTIONS, f"{field}.selector_v2.control_selection"
            ),
        },
        "interpretation_v1": _normalize_interpretation(raw["interpretation_v1"], f"{field}.interpretation_v1"),
        "interpretation_v2": _normalize_interpretation(raw["interpretation_v2"], f"{field}.interpretation_v2"),
        "cutoff_contamination": _bool(raw["cutoff_contamination"], f"{field}.cutoff_contamination"),
        "input_digest": _sha256_text(raw["input_digest"], f"{field}.input_digest"),
    }


def validate_private_qualification_input(payload: Mapping[str, object]) -> tuple[dict, ...]:
    raw = _mapping(payload, "payload")
    _exact_fields(raw, _TOP_LEVEL_FIELDS, "payload")
    if raw["schema_version"] != INPUT_SCHEMA:
        raise ValueError("unsupported private qualification schema_version")
    cases = raw["cases"]
    if not isinstance(cases, list):
        raise ValueError("cases must be a list")
    if not cases:
        raise ValueError("private qualification requires at least one case")
    normalized = tuple(_normalize_case(case, index) for index, case in enumerate(cases))
    case_ids = [case["case_id"] for case in normalized]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("case_id values must be unique")
    return normalized


def _counter() -> dict:
    return {result: 0 for result in RESULTS}


def aggregate_private_qualification(payload: Mapping[str, object]) -> dict:
    cases = validate_private_qualification_input(payload)

    selector = {
        "v1_control_false_negative_count": 0,
        "v2_not_true_control_count": 0,
        "v2_true_control_count": 0,
        "v2_abstention_count": 0,
    }
    interpretation = {
        "v1_domain": _counter(),
        "v2_domain": _counter(),
        "v1_event_family": _counter(),
        "v2_event_family": _counter(),
        "v1_false_positive_count": 0,
        "v2_false_positive_count": 0,
        "v2_abstention_count": 0,
    }
    contamination_count = 0

    for case in cases:
        if case["selector_v1"]["control_result"] == "false_negative":
            selector["v1_control_false_negative_count"] += 1

        if case["selector_v2"]["annual_role"] == "true_control":
            selector["v2_true_control_count"] += 1
        else:
            selector["v2_not_true_control_count"] += 1

        if case["selector_v2"]["control_selection"] == "abstain":
            selector["v2_abstention_count"] += 1

        v1 = case["interpretation_v1"]
        v2 = case["interpretation_v2"]
        interpretation["v1_domain"][v1["domain_result"]] += 1
        interpretation["v2_domain"][v2["domain_result"]] += 1
        interpretation["v1_event_family"][v1["event_family_result"]] += 1
        interpretation["v2_event_family"][v2["event_family_result"]] += 1
        interpretation["v1_false_positive_count"] += int(v1["false_positive"])
        interpretation["v2_false_positive_count"] += int(v2["false_positive"])
        interpretation["v2_abstention_count"] += int(v2["abstained"])
        contamination_count += int(case["cutoff_contamination"])

    input_digests = sorted(case["input_digest"] for case in cases)
    report = {
        "schema_version": SUMMARY_SCHEMA,
        "status": "FAIL" if contamination_count else "PASS",
        "case_count": len(cases),
        "selector": selector,
        "interpretation": interpretation,
        "cutoff_contamination_count": contamination_count,
        "input_set_digest": _digest(input_digests),
        "promotion_allowed": False,
    }
    report["summary_digest"] = _digest(report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Build private-safe v1.6 interpretation qualification aggregate")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    source = json.loads(Path(args.input).read_text(encoding="utf-8"))
    report = aggregate_private_qualification(source)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
