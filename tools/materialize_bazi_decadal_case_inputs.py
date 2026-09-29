"""Materialize the predeclared Bazi decadal case inputs for an oracle handoff.

The output contains only the already preregistered synthetic case inputs and
their canonical digests. It does not call production Bazi code and does not
contain expected values or comparison results.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Optional, Sequence

from tools.validate_bazi_decadal_preoracle_review_packet import validate_review_packet


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


def materialize_case_inputs(review_packet: Mapping[str, Any], *, timezone: str) -> dict:
    errors = validate_review_packet(review_packet)
    if errors:
        raise ValueError("invalid review packet: " + "; ".join(errors))
    if review_packet["case_selection"]["production_results_consulted_for_selection"] is not False:
        raise ValueError("case selection must remain production-result-blind")
    if not isinstance(timezone, str) or not timezone:
        raise ValueError("timezone must be non-empty")

    cases = []
    for case in review_packet["case_selection"]["cases"]:
        input_payload = {
            "birth_datetime": case["birth_datetime"],
            "sex": case["sex"],
            "timezone": timezone,
        }
        cases.append(
            {
                "case_id": case["case_id"],
                "input": deepcopy(input_payload),
                "input_sha256": _digest(input_payload),
                "coverage_tags": list(case["coverage_tags"]),
            }
        )
    bundle = {
        "schema_version": "1.0",
        "bundle_type": "bazi_decadal_oracle_case_inputs",
        "profile_id": review_packet["profile_candidate"]["profile_id"],
        "rule_version": review_packet["profile_candidate"]["rule_version"],
        "timezone": timezone,
        "production_results_consulted_for_selection": False,
        "expected_values_present": False,
        "cases": cases,
    }
    bundle["bundle_sha256"] = _digest(bundle)
    return bundle


def validate_case_input_bundle(bundle: Mapping[str, Any]) -> list[str]:
    errors = []
    if not isinstance(bundle, Mapping):
        return ["case_inputs: expected object"]
    if bundle.get("schema_version") != "1.0":
        errors.append("case_inputs.schema_version")
    if bundle.get("bundle_type") != "bazi_decadal_oracle_case_inputs":
        errors.append("case_inputs.bundle_type")
    if bundle.get("profile_id") != "bazi-natal-project-v1":
        errors.append("case_inputs.profile_id")
    if bundle.get("rule_version") != "1.0-exp":
        errors.append("case_inputs.rule_version")
    if bundle.get("production_results_consulted_for_selection") is not False:
        errors.append("case_inputs.production_results_consulted_for_selection")
    if bundle.get("expected_values_present") is not False:
        errors.append("case_inputs.expected_values_present")
    cases = bundle.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("case_inputs.cases")
        cases = []
    ids = set()
    for index, case in enumerate(cases):
        if not isinstance(case, Mapping):
            errors.append(f"case_inputs.cases[{index}]")
            continue
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not case_id or case_id in ids:
            errors.append(f"case_inputs.cases[{index}].case_id")
        ids.add(case_id)
        input_payload = case.get("input")
        if not isinstance(input_payload, Mapping):
            errors.append(f"case_inputs.cases[{index}].input")
        elif case.get("input_sha256") != _digest(input_payload):
            errors.append(f"case_inputs.cases[{index}].input_sha256")
    claimed = bundle.get("bundle_sha256")
    material = deepcopy(dict(bundle))
    material.pop("bundle_sha256", None)
    if claimed != _digest(material):
        errors.append("case_inputs.bundle_sha256")
    return sorted(set(errors))


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-packet", required=True, type=Path)
    parser.add_argument("--timezone", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    try:
        review_packet = json.loads(args.review_packet.read_text(encoding="utf-8"))
        bundle = materialize_case_inputs(review_packet, timezone=args.timezone)
        errors = validate_case_input_bundle(bundle)
        if errors:
            raise ValueError("generated invalid case-input bundle: " + "; ".join(errors))
        rendered = json.dumps(bundle, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        if args.output is None:
            sys.stdout.write(rendered)
        else:
            if args.output.exists() and not args.overwrite:
                raise FileExistsError(
                    f"output exists; pass --overwrite to replace it: {args.output}"
                )
            if not args.output.parent.exists():
                raise FileNotFoundError(
                    f"output directory does not exist: {args.output.parent}"
                )
            args.output.write_text(rendered, encoding="utf-8", newline="\n")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"materialize_bazi_decadal_case_inputs: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
