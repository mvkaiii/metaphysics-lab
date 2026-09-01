from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime
from typing import Mapping

from engine.distribution.claim_consumption_qualification import (
    INPUT_SCHEMA,
    validate_claim_consumption_qualification_input,
)

ORACLE_SCHEMA = "v1.6-claim-consumption-oracle.v1"
SEAL_SCHEMA = "v1.6-claim-consumption-oracle-seal.v1"
RECEIPT_SCHEMA = "v1.6-claim-consumption-oracle-seal-receipt.v1"
CANDIDATE_OUTPUT_SCHEMA = "v1.6-claim-consumption-candidate-output.v1"
VERIFICATION_SCHEMA = "v1.6-claim-consumption-oracle-seal-verification.v1"

_AUTHORIZATIONS = frozenset(("render", "render_with_caveat", "abstain_claim"))
_SPECIFICITY_ORDER = {
    "domain": 0,
    "event_family": 1,
    "concrete_event": 2,
    "highly_specific_event": 3,
}

_ORACLE_FIELDS = frozenset(("schema_version", "oracle_profile", "rubric_digest", "cases"))
_ORACLE_CASE_FIELDS = frozenset((
    "case_id",
    "expectations",
    "cutoff_contamination",
    "oracle_case_digest",
))
_EXPECTATION_FIELDS = frozenset((
    "claim_id",
    "expected_authorization",
    "minimum_acceptable_specificity",
    "maximum_specificity",
    "caveat_required",
))
_SEAL_FIELDS = frozenset((
    "schema_version",
    "oracle_profile",
    "case_count",
    "claim_count",
    "rubric_digest",
    "oracle_expectation_digest",
    "case_set_digest",
    "cutoff_contamination_count",
    "sealed_at",
    "seal_digest",
))
_RECEIPT_FIELDS = frozenset((
    "schema_version",
    "status",
    "oracle_profile",
    "case_count",
    "claim_count",
    "rubric_digest",
    "case_set_digest",
    "oracle_expectation_digest",
    "cutoff_contamination_count",
    "sealed_at",
    "seal_digest",
    "promotion_allowed",
))
_VERIFICATION_FIELDS = frozenset(("schema_version", "status", "seal_digest"))
_CANDIDATE_FIELDS = frozenset(("schema_version", "candidate_sha", "cases"))
_CANDIDATE_CASE_FIELDS = frozenset(("case_id", "claim_consumption_bundle", "candidate_case_digest"))


def _canonical_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("oracle seal input must be canonical JSON") from exc


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be a mapping")
    return value


def _list(value: object, label: str) -> list:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be non-empty text")
    return value


def _bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{label} must be boolean")
    return value


def _nonnegative_int(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    return value


def _exact_fields(value: Mapping[str, object], allowed: frozenset, label: str) -> None:
    unknown = set(value) - allowed
    missing = allowed - set(value)
    if unknown:
        raise ValueError(f"{label} contains unknown fields: {sorted(unknown)}")
    if missing:
        raise ValueError(f"{label} is missing required fields: {sorted(missing)}")


def _sha256_text(value: object, label: str) -> str:
    text = _text(value, label)
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise ValueError(f"{label} must be lowercase sha256 hex")
    return text


def _specificity(value: object, label: str) -> str:
    if value not in _SPECIFICITY_ORDER:
        raise ValueError(f"{label} contains unsupported specificity")
    return str(value)


def _sealed_at(value: object) -> str:
    text = _text(value, "sealed_at")
    try:
        parsed = datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise ValueError("sealed_at must be UTC RFC3339 with Z suffix") from exc
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != text:
        raise ValueError("sealed_at must be UTC RFC3339 with Z suffix")
    return text


def _validate_expectation(raw: object) -> dict:
    expected = _mapping(raw, "oracle expectation")
    _exact_fields(expected, _EXPECTATION_FIELDS, "oracle expectation")
    claim_id = _text(expected["claim_id"], "expectation.claim_id")
    authorization = expected["expected_authorization"]
    if authorization not in _AUTHORIZATIONS:
        raise ValueError("expected_authorization contains unsupported value")
    caveat_required = _bool(expected["caveat_required"], "caveat_required")
    if caveat_required != (authorization == "render_with_caveat"):
        raise ValueError("caveat_required contradicts expected_authorization")

    minimum = expected["minimum_acceptable_specificity"]
    maximum = expected["maximum_specificity"]
    if authorization == "abstain_claim":
        if minimum is not None or maximum is not None:
            raise ValueError("abstain_claim expectation requires null specificity bounds")
        normalized_minimum = None
        normalized_maximum = None
    else:
        normalized_minimum = _specificity(minimum, "minimum_acceptable_specificity")
        normalized_maximum = _specificity(maximum, "maximum_specificity")
        if _SPECIFICITY_ORDER[normalized_minimum] > _SPECIFICITY_ORDER[normalized_maximum]:
            raise ValueError("minimum_acceptable_specificity cannot exceed maximum_specificity")

    return {
        "claim_id": claim_id,
        "expected_authorization": str(authorization),
        "minimum_acceptable_specificity": normalized_minimum,
        "maximum_specificity": normalized_maximum,
        "caveat_required": caveat_required,
    }


def _normalized_case_payload(case: Mapping[str, object]) -> dict:
    expectations = [
        _validate_expectation(row)
        for row in _list(case["expectations"], "expectations")
    ]
    claim_ids = [row["claim_id"] for row in expectations]
    if len(claim_ids) != len(set(claim_ids)):
        raise ValueError("expectation claim_id values must be unique")
    return {
        "case_id": _text(case["case_id"], "case_id"),
        "expectations": sorted(expectations, key=lambda row: row["claim_id"]),
        "cutoff_contamination": _bool(
            case["cutoff_contamination"],
            "cutoff_contamination",
        ),
    }


def _validate_oracle_case(raw: object) -> dict:
    case = _mapping(raw, "oracle case")
    _exact_fields(case, _ORACLE_CASE_FIELDS, "oracle case")
    normalized_payload = _normalized_case_payload(case)
    supplied_digest = _sha256_text(case["oracle_case_digest"], "oracle_case_digest")
    if supplied_digest != _digest(normalized_payload):
        raise ValueError("oracle_case_digest does not match canonical case payload")
    return {
        **normalized_payload,
        "oracle_case_digest": supplied_digest,
    }


def validate_claim_consumption_oracle(payload: object) -> dict:
    root = _mapping(payload, "claim consumption oracle")
    _exact_fields(root, _ORACLE_FIELDS, "claim consumption oracle")
    if root["schema_version"] != ORACLE_SCHEMA:
        raise ValueError("unsupported oracle schema_version")
    _text(root["oracle_profile"], "oracle_profile")
    _sha256_text(root["rubric_digest"], "rubric_digest")
    cases = [_validate_oracle_case(row) for row in _list(root["cases"], "cases")]
    if not cases:
        raise ValueError("oracle must contain at least one case")
    case_ids = [row["case_id"] for row in cases]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("case_id values must be unique")
    return copy.deepcopy(payload)


def _normalized_oracle_cases(oracle: Mapping[str, object]) -> list[dict]:
    cases = [_validate_oracle_case(row) for row in _list(oracle["cases"], "cases")]
    return sorted(cases, key=lambda row: row["case_id"])


def seal_claim_consumption_oracle(oracle: object, sealed_at: str) -> dict:
    validate_claim_consumption_oracle(oracle)
    root = _mapping(oracle, "claim consumption oracle")
    timestamp = _sealed_at(sealed_at)
    cases = _normalized_oracle_cases(root)
    normalized_case_payloads = [
        {
            "case_id": row["case_id"],
            "expectations": copy.deepcopy(row["expectations"]),
            "cutoff_contamination": row["cutoff_contamination"],
        }
        for row in cases
    ]
    case_digests = sorted(row["oracle_case_digest"] for row in cases)
    seal = {
        "schema_version": SEAL_SCHEMA,
        "oracle_profile": str(root["oracle_profile"]),
        "case_count": len(cases),
        "claim_count": sum(len(row["expectations"]) for row in cases),
        "rubric_digest": str(root["rubric_digest"]),
        "oracle_expectation_digest": _digest(normalized_case_payloads),
        "case_set_digest": _digest(case_digests),
        "cutoff_contamination_count": sum(
            int(row["cutoff_contamination"]) for row in cases
        ),
        "sealed_at": timestamp,
    }
    seal["seal_digest"] = _digest(seal)
    return seal


def _validate_seal_shape(raw: object) -> dict:
    seal = _mapping(raw, "oracle seal")
    _exact_fields(seal, _SEAL_FIELDS, "oracle seal")
    if seal["schema_version"] != SEAL_SCHEMA:
        raise ValueError("unsupported oracle seal schema_version")
    normalized = {
        "schema_version": SEAL_SCHEMA,
        "oracle_profile": _text(seal["oracle_profile"], "oracle_profile"),
        "case_count": _nonnegative_int(seal["case_count"], "case_count"),
        "claim_count": _nonnegative_int(seal["claim_count"], "claim_count"),
        "rubric_digest": _sha256_text(seal["rubric_digest"], "rubric_digest"),
        "oracle_expectation_digest": _sha256_text(
            seal["oracle_expectation_digest"],
            "oracle_expectation_digest",
        ),
        "case_set_digest": _sha256_text(seal["case_set_digest"], "case_set_digest"),
        "cutoff_contamination_count": _nonnegative_int(
            seal["cutoff_contamination_count"],
            "cutoff_contamination_count",
        ),
        "sealed_at": _sealed_at(seal["sealed_at"]),
        "seal_digest": _sha256_text(seal["seal_digest"], "seal_digest"),
    }
    digest_payload = dict(normalized)
    supplied = digest_payload.pop("seal_digest")
    if supplied != _digest(digest_payload):
        raise ValueError("seal_digest does not match seal payload")
    return normalized


def verify_oracle_seal(oracle: object, seal: object) -> dict:
    validated_seal = _validate_seal_shape(seal)
    expected = seal_claim_consumption_oracle(oracle, validated_seal["sealed_at"])
    if validated_seal != expected:
        raise ValueError("oracle does not match sealed oracle identity")
    result = {
        "schema_version": VERIFICATION_SCHEMA,
        "status": "VALID",
        "seal_digest": validated_seal["seal_digest"],
    }
    _exact_fields(result, _VERIFICATION_FIELDS, "verification report")
    return result


def build_public_oracle_seal_receipt(seal: object) -> dict:
    validated = _validate_seal_shape(seal)
    receipt = {
        "schema_version": RECEIPT_SCHEMA,
        "status": "SEALED",
        "oracle_profile": validated["oracle_profile"],
        "case_count": validated["case_count"],
        "claim_count": validated["claim_count"],
        "rubric_digest": validated["rubric_digest"],
        "case_set_digest": validated["case_set_digest"],
        "oracle_expectation_digest": validated["oracle_expectation_digest"],
        "cutoff_contamination_count": validated["cutoff_contamination_count"],
        "sealed_at": validated["sealed_at"],
        "seal_digest": validated["seal_digest"],
        "promotion_allowed": False,
    }
    _exact_fields(receipt, _RECEIPT_FIELDS, "public seal receipt")
    return receipt



def _git_sha(value: object, label: str) -> str:
    text = _text(value, label)
    if len(text) != 40 or any(ch not in "0123456789abcdef" for ch in text):
        raise ValueError(f"{label} must be 40-character lowercase git sha")
    return text


def _validate_candidate_bundle_with_q1_validator(raw: object) -> dict:
    bundle = _mapping(raw, "claim_consumption_bundle")
    decisions = _list(bundle.get("decisions"), "claim_consumption_bundle.decisions")
    expectations = []
    for raw_decision in decisions:
        decision = _mapping(raw_decision, "claim consumption decision")
        claim_id = decision.get("claim_id")
        authorization = decision.get("decision")
        authorized_specificity = decision.get("authorized_specificity")
        if authorization == "abstain_claim":
            minimum = None
            maximum = None
        else:
            minimum = authorized_specificity
            maximum = authorized_specificity
        expectations.append({
            "claim_id": claim_id,
            "expected_authorization": authorization,
            "minimum_acceptable_specificity": minimum,
            "maximum_specificity": maximum,
            "caveat_required": authorization == "render_with_caveat",
        })

    case = {
        "case_id": "candidate-bundle-schema-validation",
        "claim_consumption_bundle": copy.deepcopy(bundle),
        "expectations": expectations,
        "cutoff_contamination": False,
    }
    case["input_digest"] = _digest(case)
    wrapper = {
        "schema_version": INPUT_SCHEMA,
        "classification": "synthetic_validation",
        "cases": [case],
    }
    validate_claim_consumption_qualification_input(wrapper)
    return copy.deepcopy(bundle)


def _validate_candidate_case(raw: object) -> dict:
    case = _mapping(raw, "candidate output case")
    _exact_fields(case, _CANDIDATE_CASE_FIELDS, "candidate output case")
    case_id = _text(case["case_id"], "candidate case_id")
    bundle = _validate_candidate_bundle_with_q1_validator(case["claim_consumption_bundle"])
    supplied = _sha256_text(case["candidate_case_digest"], "candidate_case_digest")
    payload = {
        "case_id": case_id,
        "claim_consumption_bundle": copy.deepcopy(bundle),
    }
    if supplied != _digest(payload):
        raise ValueError("candidate_case_digest does not match candidate case payload")
    return {
        **payload,
        "candidate_case_digest": supplied,
    }


def validate_claim_consumption_candidate_output(payload: object) -> dict:
    root = _mapping(payload, "candidate output package")
    _exact_fields(root, _CANDIDATE_FIELDS, "candidate output package")
    if root["schema_version"] != CANDIDATE_OUTPUT_SCHEMA:
        raise ValueError("unsupported candidate output schema_version")
    _git_sha(root["candidate_sha"], "candidate_sha")
    cases = [_validate_candidate_case(row) for row in _list(root["cases"], "candidate cases")]
    if not cases:
        raise ValueError("candidate output must contain at least one case")
    case_ids = [row["case_id"] for row in cases]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("candidate case_id values must be unique")
    return copy.deepcopy(payload)


def _normalized_candidate_cases(candidate_output: Mapping[str, object]) -> list[dict]:
    cases = [
        _validate_candidate_case(row)
        for row in _list(candidate_output["cases"], "candidate cases")
    ]
    return sorted(cases, key=lambda row: row["case_id"])


def join_sealed_oracle_with_candidate(
    oracle: object,
    seal: object,
    candidate_output: object,
) -> dict:
    verified = verify_oracle_seal(oracle, seal)
    if verified["status"] != "VALID":
        raise ValueError("oracle seal is not valid")
    validated_seal = _validate_seal_shape(seal)
    if validated_seal["cutoff_contamination_count"] != 0:
        raise ValueError("cutoff contamination prevents oracle join")

    validate_claim_consumption_oracle(oracle)
    validate_claim_consumption_candidate_output(candidate_output)
    oracle_root = _mapping(oracle, "claim consumption oracle")
    candidate_root = _mapping(candidate_output, "candidate output package")

    oracle_cases = _normalized_oracle_cases(oracle_root)
    candidate_cases = _normalized_candidate_cases(candidate_root)
    oracle_by_id = {row["case_id"]: row for row in oracle_cases}
    candidate_by_id = {row["case_id"]: row for row in candidate_cases}
    if set(oracle_by_id) != set(candidate_by_id):
        raise ValueError("oracle and candidate case sets must match exactly")

    joined_cases = []
    for case_id in sorted(oracle_by_id):
        oracle_case = oracle_by_id[case_id]
        candidate_case = candidate_by_id[case_id]
        expected_ids = {row["claim_id"] for row in oracle_case["expectations"]}
        actual_ids = {
            str(row["claim_id"])
            for row in candidate_case["claim_consumption_bundle"]["decisions"]
        }
        if expected_ids != actual_ids:
            raise ValueError(f"oracle and candidate claim sets must match exactly for {case_id}")

        joined_case = {
            "case_id": case_id,
            "claim_consumption_bundle": copy.deepcopy(
                candidate_case["claim_consumption_bundle"]
            ),
            "expectations": copy.deepcopy(oracle_case["expectations"]),
            "cutoff_contamination": oracle_case["cutoff_contamination"],
        }
        joined_case["input_digest"] = _digest(joined_case)
        joined_cases.append(joined_case)

    joined = {
        "schema_version": INPUT_SCHEMA,
        "classification": "private_external_evaluation",
        "cases": joined_cases,
    }
    validate_claim_consumption_qualification_input(joined)
    return copy.deepcopy(joined)
