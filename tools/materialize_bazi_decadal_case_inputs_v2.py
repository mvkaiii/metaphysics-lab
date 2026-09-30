"""Materialize the approved Task 3 v2 clean-room case bundle.

The v2 review packet preserves the same 12 pre-result birth/sex inputs while
removing answer-leaking metadata.  This tool emits the existing case-input
schema so downstream seal/finalizer/comparator code stays unchanged.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping

from tools.materialize_bazi_decadal_case_inputs import validate_case_input_bundle
from tools.validate_bazi_decadal_preoracle_review_packet_v2 import validate_review_packet_v2


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def materialize_case_inputs_v2(review_packet: Mapping[str, Any], *, timezone: str) -> dict:
    errors = validate_review_packet_v2(review_packet)
    if errors:
        raise ValueError("invalid v2 review packet: " + "; ".join(errors))
    cases = []
    for case in review_packet["case_selection"]["cases"]:
        input_payload = {
            "birth_datetime": case["birth_datetime"],
            "sex": case["sex"],
            "timezone": timezone,
        }
        cases.append({
            "case_id": case["case_id"],
            "input": deepcopy(input_payload),
            "input_sha256": _digest(input_payload),
            "coverage_tags": list(case["coverage_tags"]),
        })
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
    bundle_errors = validate_case_input_bundle(bundle)
    if bundle_errors:
        raise ValueError("generated invalid case bundle: " + "; ".join(bundle_errors))
    return bundle
