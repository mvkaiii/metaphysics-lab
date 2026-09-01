from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone
from typing import Mapping

PROTOCOL_SCHEMA = "v1.6-claim-consumption-sampling-protocol.v1"
SOURCE_MANIFEST_SCHEMA = "v1.6-claim-consumption-sampling-source-manifest.v1"
CLAIM_UNIVERSE_SCHEMA = "v1.6-claim-consumption-sampling-claim-universe-lock.v1"
FRAME_SCHEMA = "v1.6-claim-consumption-sampling-frame.v1"
RECEIPT_SCHEMA = "v1.6-claim-consumption-sampling-eligibility-receipt.v1"
ORACLE_SCHEMA = "v1.6-claim-consumption-oracle.v1"
ORACLE_ID_VERIFICATION_SCHEMA = "v1.6-claim-consumption-sampling-oracle-identity-verification.v1"

SAMPLING_PROFILE = "lin_tianji_claim_consumption_complete_census_v1"
REQUIRED_T1_POLICY_PROFILE = "lin_tianji_claim_consumption_private_strict_zero_v1"
REQUIRED_T1_POLICY_DIGEST = "65a072b2de63d6f509cc79139442263695589feca28ee99da0ab976ba0c3118a"

ALLOWED_CASE_STATUSES = (
    "EXCLUDE_AFTER_CUTOFF",
    "EXCLUDE_INPUT_INVALID",
    "EXCLUDE_NON_CONFIRMATION",
    "EXCLUDE_OUT_OF_SCOPE",
    "EXCLUDE_PREVIOUSLY_EXPOSED",
    "INCLUDE",
)
ALLOWED_EXCLUSION_REASON_CODES = (
    "after_cutoff",
    "input_invalid",
    "non_confirmation",
    "out_of_scope",
    "previously_exposed",
)

_PROTOCOL_FIELDS = frozenset((
    "schema_version",
    "sampling_profile",
    "required_t1_policy_profile",
    "required_t1_policy_digest",
    "protocol_frozen_at",
    "allowed_case_statuses",
    "allowed_exclusion_reason_codes",
    "complete_census_required",
    "candidate_exposure_must_be_unexposed",
    "claim_universe_must_be_outcome_free",
    "minimum_case_count_rule",
    "minimum_claim_count_rule",
    "protocol_digest",
    "promotion_allowed",
))
_SOURCE_FIELDS = frozenset((
    "schema_version",
    "sampling_profile",
    "sampling_protocol_digest",
    "required_t1_policy_digest",
    "cutoff_timestamp",
    "source_locked_at",
    "records",
    "source_manifest_digest",
))
_SOURCE_RECORD_FIELDS = frozenset((
    "opaque_case_id",
    "source_record_digest",
    "within_cutoff",
    "candidate_exposure_status",
    "confirmation_status",
    "input_validity_status",
    "scope_status",
    "eligibility_facts_digest",
    "record_digest",
))
_CLAIM_UNIVERSE_FIELDS = frozenset((
    "schema_version",
    "sampling_profile",
    "sampling_protocol_digest",
    "source_manifest_digest",
    "claim_authority_profile",
    "claim_authority_digest",
    "locked_at",
    "cases",
    "claim_universe_digest",
))
_CLAIM_CASE_FIELDS = frozenset(("opaque_case_id", "locked_claim_ids", "claim_case_digest"))
_FRAME_FIELDS = frozenset((
    "schema_version",
    "sampling_profile",
    "sampling_protocol_digest",
    "required_t1_policy_digest",
    "cutoff_timestamp",
    "source_manifest_digest",
    "claim_universe_digest",
    "claim_authority_profile",
    "claim_authority_digest",
    "locked_at",
    "cases",
    "frame_digest",
))
_FRAME_CASE_FIELDS = frozenset((
    "opaque_case_id",
    "source_record_digest",
    "status",
    "exclusion_reason_code",
    "locked_claim_ids",
    "case_digest",
))
_RECEIPT_FIELDS = frozenset((
    "schema_version",
    "sampling_profile",
    "status",
    "case_count",
    "claim_count",
    "sampling_protocol_digest",
    "sealed_at",
    "receipt_digest",
    "promotion_allowed",
))
_ORACLE_ROOT_FIELDS = frozenset(("schema_version", "oracle_profile", "rubric_digest", "cases"))
_ORACLE_CASE_FIELDS = frozenset(("case_id", "expectations", "cutoff_contamination", "oracle_case_digest"))
_ORACLE_EXPECTATION_FIELDS = frozenset((
    "claim_id",
    "expected_authorization",
    "minimum_acceptable_specificity",
    "maximum_specificity",
    "caveat_required",
))


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
        raise ValueError("sampling eligibility input must be canonical JSON") from exc


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


def _exact_fields(value: Mapping[str, object], allowed: frozenset, label: str) -> None:
    unknown = set(value) - allowed
    missing = allowed - set(value)
    if unknown:
        raise ValueError(f"{label} contains unknown fields: {sorted(unknown)}")
    if missing:
        raise ValueError(f"{label} is missing required fields: {sorted(missing)}")


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be non-empty text")
    return value


def _sha256_text(value: object, label: str) -> str:
    text = _text(value, label)
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise ValueError(f"{label} must be lowercase sha256 hex")
    return text


def _bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{label} must be boolean")
    return value


def _false(value: object, label: str) -> bool:
    if value is not False:
        raise ValueError(f"{label} must be false")
    return False


def _nonnegative_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    return value


def _timestamp(value: object, label: str) -> str:
    text = _text(value, label)
    if not text.endswith("Z"):
        raise ValueError(f"{label} must be UTC RFC3339 Z timestamp")
    try:
        parsed = datetime.fromisoformat(text[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError(f"{label} must be UTC RFC3339 Z timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError(f"{label} must be UTC RFC3339 Z timestamp")
    return text


def _timestamp_value(value: str) -> datetime:
    return datetime.fromisoformat(value[:-1] + "+00:00")


def _unique_text_list(value: object, label: str, *, allow_empty: bool) -> list[str]:
    rows = _list(value, label)
    result = [_text(row, label) for row in rows]
    if not allow_empty and not result:
        raise ValueError(f"{label} must be non-empty")
    if len(result) != len(set(result)):
        raise ValueError(f"{label} values must be unique; duplicate values are forbidden")
    return result


def _derive_case_status(record: Mapping[str, object]) -> tuple[str, str | None]:
    if record["within_cutoff"] is False:
        return "EXCLUDE_AFTER_CUTOFF", "after_cutoff"
    if record["candidate_exposure_status"] == "PREVIOUSLY_EXPOSED":
        return "EXCLUDE_PREVIOUSLY_EXPOSED", "previously_exposed"
    if record["confirmation_status"] == "NON_CONFIRMATION":
        return "EXCLUDE_NON_CONFIRMATION", "non_confirmation"
    if record["input_validity_status"] == "INVALID":
        return "EXCLUDE_INPUT_INVALID", "input_invalid"
    if record["scope_status"] == "OUT_OF_SCOPE":
        return "EXCLUDE_OUT_OF_SCOPE", "out_of_scope"
    return "INCLUDE", None


def validate_sampling_protocol(payload: object) -> dict:
    protocol = _mapping(payload, "sampling protocol")
    _exact_fields(protocol, _PROTOCOL_FIELDS, "sampling protocol")
    if protocol["schema_version"] != PROTOCOL_SCHEMA:
        raise ValueError("unsupported sampling protocol schema_version")
    if protocol["sampling_profile"] != SAMPLING_PROFILE:
        raise ValueError("unsupported sampling_profile")
    if protocol["required_t1_policy_profile"] != REQUIRED_T1_POLICY_PROFILE:
        raise ValueError("sampling protocol requires unexpected T1 policy profile")
    if protocol["required_t1_policy_digest"] != REQUIRED_T1_POLICY_DIGEST:
        raise ValueError("sampling protocol requires unexpected T1 policy digest")
    _timestamp(protocol["protocol_frozen_at"], "protocol_frozen_at")
    statuses = _unique_text_list(protocol["allowed_case_statuses"], "allowed_case_statuses", allow_empty=False)
    reasons = _unique_text_list(protocol["allowed_exclusion_reason_codes"], "allowed_exclusion_reason_codes", allow_empty=False)
    if statuses != list(ALLOWED_CASE_STATUSES):
        raise ValueError("allowed_case_statuses must equal the frozen S1 status list")
    if reasons != list(ALLOWED_EXCLUSION_REASON_CODES):
        raise ValueError("allowed_exclusion_reason_codes must equal the frozen S1 reason list")
    if _bool(protocol["complete_census_required"], "complete_census_required") is not True:
        raise ValueError("complete_census_required must be true")
    if _bool(protocol["candidate_exposure_must_be_unexposed"], "candidate_exposure_must_be_unexposed") is not True:
        raise ValueError("candidate_exposure_must_be_unexposed must be true")
    if _bool(protocol["claim_universe_must_be_outcome_free"], "claim_universe_must_be_outcome_free") is not True:
        raise ValueError("claim_universe_must_be_outcome_free must be true")
    if protocol["minimum_case_count_rule"] != "at_least_one_if_eligible":
        raise ValueError("unsupported minimum_case_count_rule")
    if protocol["minimum_claim_count_rule"] != "at_least_one_if_eligible":
        raise ValueError("unsupported minimum_claim_count_rule")
    _false(protocol["promotion_allowed"], "promotion_allowed")
    supplied = _sha256_text(protocol["protocol_digest"], "protocol_digest")
    normalized = copy.deepcopy(dict(protocol))
    normalized.pop("protocol_digest")
    if supplied != _digest(normalized):
        raise ValueError("protocol_digest does not match sampling protocol payload")
    return copy.deepcopy(dict(protocol))


def _validate_source_record(raw: object) -> dict:
    record = _mapping(raw, "source manifest record")
    _exact_fields(record, _SOURCE_RECORD_FIELDS, "source manifest record")
    case_id = _text(record["opaque_case_id"], "opaque_case_id")
    source_record_digest = _sha256_text(record["source_record_digest"], "source_record_digest")
    within_cutoff = _bool(record["within_cutoff"], "within_cutoff")
    exposure = record["candidate_exposure_status"]
    confirmation = record["confirmation_status"]
    validity = record["input_validity_status"]
    scope = record["scope_status"]
    if exposure not in {"UNEXPOSED", "PREVIOUSLY_EXPOSED"}:
        raise ValueError("unsupported candidate_exposure_status")
    if confirmation not in {"CONFIRMED", "NON_CONFIRMATION"}:
        raise ValueError("unsupported confirmation_status")
    if validity not in {"VALID", "INVALID"}:
        raise ValueError("unsupported input_validity_status")
    if scope not in {"IN_SCOPE", "OUT_OF_SCOPE"}:
        raise ValueError("unsupported scope_status")
    facts = {
        "within_cutoff": within_cutoff,
        "candidate_exposure_status": exposure,
        "confirmation_status": confirmation,
        "input_validity_status": validity,
        "scope_status": scope,
    }
    facts_digest = _sha256_text(record["eligibility_facts_digest"], "eligibility_facts_digest")
    if facts_digest != _digest(facts):
        raise ValueError("eligibility_facts_digest does not match eligibility facts")
    record_digest = _sha256_text(record["record_digest"], "record_digest")
    expected_record_digest = _digest({
        "opaque_case_id": case_id,
        "source_record_digest": source_record_digest,
        "eligibility_facts_digest": facts_digest,
    })
    if record_digest != expected_record_digest:
        raise ValueError("record_digest does not match source record identity")
    return copy.deepcopy(dict(record))


def _normalized_source_payload(source: Mapping[str, object]) -> dict:
    records = [_validate_source_record(row) for row in _list(source["records"], "records")]
    case_ids = [row["opaque_case_id"] for row in records]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("source manifest opaque_case_id values must be unique; duplicate case IDs are forbidden")
    return {
        "schema_version": SOURCE_MANIFEST_SCHEMA,
        "sampling_profile": str(source["sampling_profile"]),
        "sampling_protocol_digest": str(source["sampling_protocol_digest"]),
        "required_t1_policy_digest": str(source["required_t1_policy_digest"]),
        "cutoff_timestamp": str(source["cutoff_timestamp"]),
        "source_locked_at": str(source["source_locked_at"]),
        "records": sorted(records, key=lambda row: row["opaque_case_id"]),
    }


def validate_sampling_source_manifest(payload: object, protocol: object) -> dict:
    validated_protocol = validate_sampling_protocol(protocol)
    source = _mapping(payload, "sampling source manifest")
    _exact_fields(source, _SOURCE_FIELDS, "sampling source manifest")
    if source["schema_version"] != SOURCE_MANIFEST_SCHEMA:
        raise ValueError("unsupported sampling source manifest schema_version")
    if source["sampling_profile"] != SAMPLING_PROFILE:
        raise ValueError("source manifest sampling_profile mismatch")
    if source["sampling_protocol_digest"] != validated_protocol["protocol_digest"]:
        raise ValueError("source manifest sampling protocol digest mismatch")
    if source["required_t1_policy_digest"] != REQUIRED_T1_POLICY_DIGEST:
        raise ValueError("source manifest T1 policy digest mismatch")
    cutoff = _timestamp(source["cutoff_timestamp"], "cutoff_timestamp")
    locked = _timestamp(source["source_locked_at"], "source_locked_at")
    if _timestamp_value(locked) < _timestamp_value(str(validated_protocol["protocol_frozen_at"])):
        raise ValueError("source manifest cannot be locked before S1 protocol freeze")
    _normalized_source_payload(source)
    supplied = _sha256_text(source["source_manifest_digest"], "source_manifest_digest")
    normalized = _normalized_source_payload(source)
    normalized["cutoff_timestamp"] = cutoff
    normalized["source_locked_at"] = locked
    if supplied != _digest(normalized):
        raise ValueError("source_manifest_digest does not match canonical source manifest")
    return copy.deepcopy(dict(source))


def _validate_claim_case(raw: object) -> dict:
    row = _mapping(raw, "claim universe case")
    _exact_fields(row, _CLAIM_CASE_FIELDS, "claim universe case")
    case_id = _text(row["opaque_case_id"], "opaque_case_id")
    claims = _unique_text_list(row["locked_claim_ids"], "locked_claim_ids", allow_empty=True)
    supplied = _sha256_text(row["claim_case_digest"], "claim_case_digest")
    expected = _digest({"opaque_case_id": case_id, "locked_claim_ids": sorted(claims)})
    if supplied != expected:
        raise ValueError("claim_case_digest does not match canonical claim identity")
    return {"opaque_case_id": case_id, "locked_claim_ids": sorted(claims), "claim_case_digest": supplied}


def _normalized_claim_universe_payload(lock: Mapping[str, object]) -> dict:
    cases = [_validate_claim_case(row) for row in _list(lock["cases"], "cases")]
    case_ids = [row["opaque_case_id"] for row in cases]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("claim universe opaque_case_id values must be unique; duplicate case IDs are forbidden")
    return {
        "schema_version": CLAIM_UNIVERSE_SCHEMA,
        "sampling_profile": str(lock["sampling_profile"]),
        "sampling_protocol_digest": str(lock["sampling_protocol_digest"]),
        "source_manifest_digest": str(lock["source_manifest_digest"]),
        "claim_authority_profile": str(lock["claim_authority_profile"]),
        "claim_authority_digest": str(lock["claim_authority_digest"]),
        "locked_at": str(lock["locked_at"]),
        "cases": sorted(cases, key=lambda row: row["opaque_case_id"]),
    }


def validate_claim_universe_lock(payload: object, source_manifest: object, protocol: object) -> dict:
    validated_protocol = validate_sampling_protocol(protocol)
    validated_source = validate_sampling_source_manifest(source_manifest, validated_protocol)
    lock = _mapping(payload, "claim universe lock")
    _exact_fields(lock, _CLAIM_UNIVERSE_FIELDS, "claim universe lock")
    if lock["schema_version"] != CLAIM_UNIVERSE_SCHEMA:
        raise ValueError("unsupported claim universe schema_version")
    if lock["sampling_profile"] != SAMPLING_PROFILE:
        raise ValueError("claim universe sampling_profile mismatch")
    if lock["sampling_protocol_digest"] != validated_protocol["protocol_digest"]:
        raise ValueError("claim universe sampling protocol digest mismatch")
    if lock["source_manifest_digest"] != validated_source["source_manifest_digest"]:
        raise ValueError("claim universe source manifest digest mismatch")
    _text(lock["claim_authority_profile"], "claim_authority_profile")
    _sha256_text(lock["claim_authority_digest"], "claim_authority_digest")
    locked = _timestamp(lock["locked_at"], "claim universe locked_at")
    if _timestamp_value(locked) < _timestamp_value(str(validated_source["source_locked_at"])):
        raise ValueError("claim universe cannot be locked before source manifest")

    normalized = _normalized_claim_universe_payload(lock)
    include_ids = {
        row["opaque_case_id"]
        for row in validated_source["records"]
        if _derive_case_status(row)[0] == "INCLUDE"
    }
    actual_ids = {row["opaque_case_id"] for row in normalized["cases"]}
    if actual_ids != include_ids:
        raise ValueError("claim universe case set must exactly equal deterministic INCLUDE case set; excluded or missing cases are forbidden")
    for row in normalized["cases"]:
        if not row["locked_claim_ids"]:
            raise ValueError("every INCLUDE case requires a non-empty outcome-free locked claim set")

    supplied = _sha256_text(lock["claim_universe_digest"], "claim_universe_digest")
    if supplied != _digest(normalized):
        raise ValueError("claim_universe_digest does not match canonical claim universe")
    return copy.deepcopy(dict(lock))


def _frame_case_digest_payload(row: Mapping[str, object]) -> dict:
    return {
        "opaque_case_id": str(row["opaque_case_id"]),
        "source_record_digest": str(row["source_record_digest"]),
        "status": str(row["status"]),
        "exclusion_reason_code": row["exclusion_reason_code"],
        "locked_claim_ids": sorted(list(row["locked_claim_ids"])),
    }


def _normalized_frame_payload(frame: Mapping[str, object]) -> dict:
    normalized_cases = []
    for raw in _list(frame["cases"], "frame cases"):
        row = _mapping(raw, "sampling frame case")
        _exact_fields(row, _FRAME_CASE_FIELDS, "sampling frame case")
        case_id = _text(row["opaque_case_id"], "opaque_case_id")
        source_record_digest = _sha256_text(row["source_record_digest"], "source_record_digest")
        status = _text(row["status"], "status")
        if status not in ALLOWED_CASE_STATUSES:
            raise ValueError("sampling frame case contains unsupported status")
        reason = row["exclusion_reason_code"]
        if reason is not None and reason not in ALLOWED_EXCLUSION_REASON_CODES:
            raise ValueError("sampling frame case contains unsupported or free-text exclusion reason")
        claims = _unique_text_list(row["locked_claim_ids"], "locked_claim_ids", allow_empty=True)
        normalized_row = {
            "opaque_case_id": case_id,
            "source_record_digest": source_record_digest,
            "status": status,
            "exclusion_reason_code": reason,
            "locked_claim_ids": sorted(claims),
        }
        supplied = _sha256_text(row["case_digest"], "case_digest")
        if supplied != _digest(normalized_row):
            raise ValueError("case_digest does not match sampling frame case payload")
        normalized_cases.append({**normalized_row, "case_digest": supplied})
    ids = [row["opaque_case_id"] for row in normalized_cases]
    if len(ids) != len(set(ids)):
        raise ValueError("sampling frame opaque_case_id values must be unique")
    return {
        "schema_version": FRAME_SCHEMA,
        "sampling_profile": str(frame["sampling_profile"]),
        "sampling_protocol_digest": str(frame["sampling_protocol_digest"]),
        "required_t1_policy_digest": str(frame["required_t1_policy_digest"]),
        "cutoff_timestamp": str(frame["cutoff_timestamp"]),
        "source_manifest_digest": str(frame["source_manifest_digest"]),
        "claim_universe_digest": str(frame["claim_universe_digest"]),
        "claim_authority_profile": str(frame["claim_authority_profile"]),
        "claim_authority_digest": str(frame["claim_authority_digest"]),
        "locked_at": str(frame["locked_at"]),
        "cases": sorted(normalized_cases, key=lambda row: row["opaque_case_id"]),
    }


def build_sampling_frame(source_manifest: object, claim_universe_lock: object, protocol: object, locked_at: str) -> dict:
    validated_protocol = validate_sampling_protocol(protocol)
    validated_source = validate_sampling_source_manifest(source_manifest, validated_protocol)
    validated_claims = validate_claim_universe_lock(claim_universe_lock, validated_source, validated_protocol)
    frame_time = _timestamp(locked_at, "sampling frame locked_at")
    if _timestamp_value(frame_time) < _timestamp_value(str(validated_claims["locked_at"])):
        raise ValueError("sampling frame cannot be locked before claim universe")
    claim_map = {
        row["opaque_case_id"]: sorted(list(row["locked_claim_ids"]))
        for row in validated_claims["cases"]
    }
    cases = []
    for source_row in sorted(validated_source["records"], key=lambda row: row["opaque_case_id"]):
        status, reason = _derive_case_status(source_row)
        claims = claim_map[source_row["opaque_case_id"]] if status == "INCLUDE" else []
        row = {
            "opaque_case_id": source_row["opaque_case_id"],
            "source_record_digest": source_row["source_record_digest"],
            "status": status,
            "exclusion_reason_code": reason,
            "locked_claim_ids": claims,
        }
        row["case_digest"] = _digest(row)
        cases.append(row)
    frame = {
        "schema_version": FRAME_SCHEMA,
        "sampling_profile": SAMPLING_PROFILE,
        "sampling_protocol_digest": validated_protocol["protocol_digest"],
        "required_t1_policy_digest": REQUIRED_T1_POLICY_DIGEST,
        "cutoff_timestamp": validated_source["cutoff_timestamp"],
        "source_manifest_digest": validated_source["source_manifest_digest"],
        "claim_universe_digest": validated_claims["claim_universe_digest"],
        "claim_authority_profile": validated_claims["claim_authority_profile"],
        "claim_authority_digest": validated_claims["claim_authority_digest"],
        "locked_at": frame_time,
        "cases": cases,
    }
    frame["frame_digest"] = _digest(frame)
    return frame


def validate_sampling_frame(payload: object, source_manifest: object, claim_universe_lock: object, protocol: object) -> dict:
    validated_protocol = validate_sampling_protocol(protocol)
    validated_source = validate_sampling_source_manifest(source_manifest, validated_protocol)
    validated_claims = validate_claim_universe_lock(claim_universe_lock, validated_source, validated_protocol)
    frame = _mapping(payload, "sampling frame")
    _exact_fields(frame, _FRAME_FIELDS, "sampling frame")
    if frame["schema_version"] != FRAME_SCHEMA:
        raise ValueError("unsupported sampling frame schema_version")
    bindings = {
        "sampling_profile": SAMPLING_PROFILE,
        "sampling_protocol_digest": validated_protocol["protocol_digest"],
        "required_t1_policy_digest": REQUIRED_T1_POLICY_DIGEST,
        "cutoff_timestamp": validated_source["cutoff_timestamp"],
        "source_manifest_digest": validated_source["source_manifest_digest"],
        "claim_universe_digest": validated_claims["claim_universe_digest"],
        "claim_authority_profile": validated_claims["claim_authority_profile"],
        "claim_authority_digest": validated_claims["claim_authority_digest"],
    }
    for key, expected in bindings.items():
        if frame[key] != expected:
            raise ValueError(f"sampling frame {key} binding mismatch")
    frame_time = _timestamp(frame["locked_at"], "sampling frame locked_at")
    if _timestamp_value(frame_time) < _timestamp_value(str(validated_claims["locked_at"])):
        raise ValueError("sampling frame cannot be locked before claim universe")

    normalized = _normalized_frame_payload(frame)
    source_map = {row["opaque_case_id"]: row for row in validated_source["records"]}
    claim_map = {row["opaque_case_id"]: sorted(list(row["locked_claim_ids"])) for row in validated_claims["cases"]}
    frame_map = {row["opaque_case_id"]: row for row in normalized["cases"]}
    if set(frame_map) != set(source_map):
        raise ValueError("sampling frame case set must exactly equal source manifest case set for complete census")
    for case_id, source_row in source_map.items():
        row = frame_map[case_id]
        if row["source_record_digest"] != source_row["source_record_digest"]:
            raise ValueError("sampling frame source_record_digest mismatch")
        expected_status, expected_reason = _derive_case_status(source_row)
        if row["status"] != expected_status or row["exclusion_reason_code"] != expected_reason:
            raise ValueError("sampling frame status/reason contradicts deterministic exposure/exclusion precedence")
        expected_claims = claim_map[case_id] if expected_status == "INCLUDE" else []
        if row["locked_claim_ids"] != expected_claims:
            raise ValueError("sampling frame claim set must exactly match outcome-free claim universe for INCLUDE cases")

    supplied = _sha256_text(frame["frame_digest"], "frame_digest")
    if supplied != _digest(normalized):
        raise ValueError("frame_digest does not match canonical sampling frame")
    return copy.deepcopy(dict(frame))


def build_sampling_eligibility_receipt(
    frame: object,
    source_manifest: object,
    claim_universe_lock: object,
    protocol: object,
    sealed_at: str,
) -> dict:
    validated_protocol = validate_sampling_protocol(protocol)
    validated_source = validate_sampling_source_manifest(source_manifest, validated_protocol)
    validated_claims = validate_claim_universe_lock(claim_universe_lock, validated_source, validated_protocol)
    validated_frame = validate_sampling_frame(frame, validated_source, validated_claims, validated_protocol)
    timestamp = _timestamp(sealed_at, "sampling receipt sealed_at")
    if _timestamp_value(timestamp) < _timestamp_value(str(validated_frame["locked_at"])):
        raise ValueError("sampling receipt cannot be sealed before sampling frame")
    included = [row for row in validated_frame["cases"] if row["status"] == "INCLUDE"]
    case_count = len(included)
    claim_count = sum(len(row["locked_claim_ids"]) for row in included)
    status = "ELIGIBLE" if case_count > 0 and claim_count > 0 else "INELIGIBLE"
    receipt = {
        "schema_version": RECEIPT_SCHEMA,
        "sampling_profile": SAMPLING_PROFILE,
        "status": status,
        "case_count": case_count,
        "claim_count": claim_count,
        "sampling_protocol_digest": validated_protocol["protocol_digest"],
        "sealed_at": timestamp,
        "promotion_allowed": False,
    }
    receipt["receipt_digest"] = _digest(receipt)
    return receipt


def verify_sampling_eligibility_receipt(payload: object) -> dict:
    receipt = _mapping(payload, "sampling eligibility receipt")
    _exact_fields(receipt, _RECEIPT_FIELDS, "sampling eligibility receipt")
    if receipt["schema_version"] != RECEIPT_SCHEMA:
        raise ValueError("unsupported sampling eligibility receipt schema_version")
    if receipt["sampling_profile"] != SAMPLING_PROFILE:
        raise ValueError("sampling eligibility receipt profile mismatch")
    status = receipt["status"]
    if status not in {"ELIGIBLE", "INELIGIBLE"}:
        raise ValueError("sampling eligibility receipt status must be ELIGIBLE or INELIGIBLE")
    case_count = _nonnegative_int(receipt["case_count"], "case_count")
    claim_count = _nonnegative_int(receipt["claim_count"], "claim_count")
    if status == "ELIGIBLE" and (case_count < 1 or claim_count < 1):
        raise ValueError("ELIGIBLE sampling receipt requires positive case and claim counts")
    if status == "INELIGIBLE" and case_count > 0 and claim_count > 0:
        raise ValueError("INELIGIBLE S1 receipt cannot contain positive case and claim counts")
    _sha256_text(receipt["sampling_protocol_digest"], "sampling_protocol_digest")
    _timestamp(receipt["sealed_at"], "sampling receipt sealed_at")
    _false(receipt["promotion_allowed"], "promotion_allowed")
    supplied = _sha256_text(receipt["receipt_digest"], "receipt_digest")
    normalized = copy.deepcopy(dict(receipt))
    normalized.pop("receipt_digest")
    if supplied != _digest(normalized):
        raise ValueError("receipt_digest does not match sampling eligibility receipt")
    return copy.deepcopy(dict(receipt))


def _validate_frame_identity_shape(frame: object) -> dict:
    root = _mapping(frame, "sampling frame")
    _exact_fields(root, _FRAME_FIELDS, "sampling frame")
    if root["schema_version"] != FRAME_SCHEMA:
        raise ValueError("unsupported sampling frame schema_version")
    normalized = _normalized_frame_payload(root)
    supplied = _sha256_text(root["frame_digest"], "frame_digest")
    if supplied != _digest(normalized):
        raise ValueError("frame_digest does not match canonical sampling frame")
    return copy.deepcopy(dict(root))


def _oracle_identity_payload(oracle: object) -> list[dict]:
    root = _mapping(oracle, "oracle")
    _exact_fields(root, _ORACLE_ROOT_FIELDS, "oracle")
    if root["schema_version"] != ORACLE_SCHEMA:
        raise ValueError("unsupported oracle schema_version")
    _text(root["oracle_profile"], "oracle_profile")
    _sha256_text(root["rubric_digest"], "rubric_digest")
    identities = []
    seen_cases = set()
    for raw_case in _list(root["cases"], "oracle cases"):
        case = _mapping(raw_case, "oracle case")
        _exact_fields(case, _ORACLE_CASE_FIELDS, "oracle case")
        case_id = _text(case["case_id"], "oracle case_id")
        if case_id in seen_cases:
            raise ValueError("oracle case identity values must be unique")
        seen_cases.add(case_id)
        claims = []
        for raw_expected in _list(case["expectations"], "oracle expectations"):
            expected = _mapping(raw_expected, "oracle expectation")
            _exact_fields(expected, _ORACLE_EXPECTATION_FIELDS, "oracle expectation")
            claims.append(_text(expected["claim_id"], "oracle claim_id"))
        if len(claims) != len(set(claims)):
            raise ValueError("oracle claim identity values must be unique")
        identities.append({"case_id": case_id, "claim_ids": sorted(claims)})
    return sorted(identities, key=lambda row: row["case_id"])


def verify_oracle_identity_against_sampling_frame(frame: object, oracle: object) -> dict:
    validated_frame = _validate_frame_identity_shape(frame)
    included = {
        row["opaque_case_id"]: sorted(list(row["locked_claim_ids"]))
        for row in validated_frame["cases"]
        if row["status"] == "INCLUDE"
    }
    oracle_identities = _oracle_identity_payload(oracle)
    oracle_map = {row["case_id"]: row["claim_ids"] for row in oracle_identities}
    if set(oracle_map) != set(included):
        raise ValueError("oracle case identity set must exactly equal sampling INCLUDE case set")
    for case_id, expected_claims in included.items():
        if oracle_map[case_id] != expected_claims:
            raise ValueError("oracle claim identity set must exactly equal sampling locked claim set")
    oracle_identity_digest = _digest(oracle_identities)
    report = {
        "schema_version": ORACLE_ID_VERIFICATION_SCHEMA,
        "status": "VALID",
        "case_count": len(included),
        "claim_count": sum(len(claims) for claims in included.values()),
        "sampling_frame_digest": validated_frame["frame_digest"],
        "oracle_identity_digest": oracle_identity_digest,
        "promotion_allowed": False,
    }
    report["verification_digest"] = _digest(report)
    return report
