from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone
from typing import Mapping

REGISTRY_SCHEMA = "v1.6-claim-consumption-prospective-case-intake-registry.v1"
INTAKE_PROFILE = "lin_tianji_claim_consumption_prospective_case_intake_v1"

ELIGIBLE_STATUS = "ELIGIBLE_FOR_S1_SOURCE"
INELIGIBLE_PROVENANCE_STATUS = "INELIGIBLE_SOURCE_PROVENANCE"
INELIGIBLE_EXPOSED_STATUS = "INELIGIBLE_PREVIOUSLY_EXPOSED"

_CASE_ORIGINS = frozenset(("FUTURE_EVENT", "HISTORICAL_UNEXPOSED"))
_OUTCOME_AVAILABILITY = frozenset(("PENDING", "KNOWN"))
_PROVENANCE_STATUSES = frozenset(("VERIFIABLE", "UNVERIFIABLE"))
_EXPOSURE_STATUSES = frozenset(("UNEXPOSED", "PREVIOUSLY_EXPOSED", "UNKNOWN"))

_RAW_RECORD_FIELDS = frozenset((
    "opaque_case_id",
    "case_origin",
    "source_timestamp",
    "intake_timestamp",
    "outcome_availability_at_intake",
    "source_record_digest",
    "source_provenance_status",
    "source_provenance_digest",
    "first_intake_status",
    "first_intake_provenance_digest",
    "candidate_exposure_status",
    "candidate_exposure_provenance_digest",
))
_RECORD_FIELDS = frozenset((*_RAW_RECORD_FIELDS, "eligibility_status", "eligibility_reason_code", "intake_record_digest"))
_REGISTRY_FIELDS = frozenset((
    "schema_version",
    "intake_profile",
    "registry_locked_at",
    "previous_registry_digest",
    "records",
    "registry_digest",
    "promotion_allowed",
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
        raise ValueError("intake input must be canonical JSON") from exc


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


def _false(value: object, label: str) -> bool:
    if value is not False:
        raise ValueError(f"{label} must be false")
    return False


def _sha256_text(value: object, label: str) -> str:
    text = _text(value, label)
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise ValueError(f"{label} must be lowercase sha256 hex")
    return text


def _optional_sha256(value: object, label: str) -> str | None:
    if value is None:
        return None
    return _sha256_text(value, label)


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


def _enum(value: object, allowed: frozenset, label: str) -> str:
    text = _text(value, label)
    if text not in allowed:
        raise ValueError(f"{label} contains unsupported value")
    return text


def _validate_provenance_pair(status: str, digest: object, label: str) -> str | None:
    normalized = _optional_sha256(digest, f"{label}_digest")
    if status == "VERIFIABLE" and normalized is None:
        raise ValueError(f"{label} VERIFIABLE requires provenance digest")
    if status == "UNVERIFIABLE" and normalized is not None:
        raise ValueError(f"{label} UNVERIFIABLE requires null provenance digest")
    return normalized


def _normalize_raw_record(payload: object) -> dict:
    row = _mapping(payload, "intake record")
    _exact_fields(row, _RAW_RECORD_FIELDS, "intake record")
    case_origin = _enum(row["case_origin"], _CASE_ORIGINS, "case_origin")
    outcome = _enum(row["outcome_availability_at_intake"], _OUTCOME_AVAILABILITY, "outcome_availability_at_intake")
    if case_origin == "FUTURE_EVENT" and outcome != "PENDING":
        raise ValueError("FUTURE_EVENT requires PENDING outcome at intake")
    if case_origin == "HISTORICAL_UNEXPOSED" and outcome != "KNOWN":
        raise ValueError("HISTORICAL_UNEXPOSED requires KNOWN outcome at intake")

    source_timestamp = _timestamp(row["source_timestamp"], "source_timestamp")
    intake_timestamp = _timestamp(row["intake_timestamp"], "intake_timestamp")
    if _timestamp_value(source_timestamp) > _timestamp_value(intake_timestamp):
        raise ValueError("source_timestamp cannot be after intake_timestamp")

    source_status = _enum(row["source_provenance_status"], _PROVENANCE_STATUSES, "source_provenance_status")
    first_status = _enum(row["first_intake_status"], _PROVENANCE_STATUSES, "first_intake_status")
    exposure_status = _enum(row["candidate_exposure_status"], _EXPOSURE_STATUSES, "candidate_exposure_status")

    source_provenance_digest = _validate_provenance_pair(
        source_status, row["source_provenance_digest"], "source_provenance"
    )
    first_intake_provenance_digest = _validate_provenance_pair(
        first_status, row["first_intake_provenance_digest"], "first_intake_provenance"
    )
    exposure_digest = _optional_sha256(
        row["candidate_exposure_provenance_digest"], "candidate_exposure_provenance_digest"
    )
    if exposure_status == "UNKNOWN" and exposure_digest is not None:
        raise ValueError("UNKNOWN exposure requires null provenance digest")
    if exposure_status != "UNKNOWN" and exposure_digest is None:
        raise ValueError("known exposure status requires provenance digest")

    return {
        "opaque_case_id": _text(row["opaque_case_id"], "opaque_case_id"),
        "case_origin": case_origin,
        "source_timestamp": source_timestamp,
        "intake_timestamp": intake_timestamp,
        "outcome_availability_at_intake": outcome,
        "source_record_digest": _sha256_text(row["source_record_digest"], "source_record_digest"),
        "source_provenance_status": source_status,
        "source_provenance_digest": source_provenance_digest,
        "first_intake_status": first_status,
        "first_intake_provenance_digest": first_intake_provenance_digest,
        "candidate_exposure_status": exposure_status,
        "candidate_exposure_provenance_digest": exposure_digest,
    }


def _classify(raw: Mapping[str, object]) -> tuple[str, str]:
    if raw["source_provenance_status"] != "VERIFIABLE":
        return INELIGIBLE_PROVENANCE_STATUS, "source_provenance_unverifiable"
    if raw["first_intake_status"] != "VERIFIABLE":
        return INELIGIBLE_PROVENANCE_STATUS, "first_intake_unverifiable"
    if raw["candidate_exposure_status"] == "UNKNOWN":
        return INELIGIBLE_PROVENANCE_STATUS, "exposure_provenance_unverifiable"
    if raw["candidate_exposure_status"] == "PREVIOUSLY_EXPOSED":
        return INELIGIBLE_EXPOSED_STATUS, "previously_exposed"
    return ELIGIBLE_STATUS, "eligible"


def _build_record(payload: object, registry_locked_at: str) -> dict:
    raw = _normalize_raw_record(payload)
    if _timestamp_value(raw["intake_timestamp"]) > _timestamp_value(registry_locked_at):
        raise ValueError("intake_timestamp cannot be after registry_locked_at")
    status, reason = _classify(raw)
    record_payload = {**raw, "eligibility_status": status, "eligibility_reason_code": reason}
    return {**record_payload, "intake_record_digest": _digest(record_payload)}


def build_intake_registry(
    records: object,
    registry_locked_at: str,
    *,
    previous_registry_digest: str | None,
) -> dict:
    locked_at = _timestamp(registry_locked_at, "registry_locked_at")
    previous = _optional_sha256(previous_registry_digest, "previous_registry_digest")
    built = [_build_record(row, locked_at) for row in _list(records, "records")]
    case_ids = [row["opaque_case_id"] for row in built]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("opaque_case_id values must be unique")
    built.sort(key=lambda row: row["opaque_case_id"])
    payload = {
        "schema_version": REGISTRY_SCHEMA,
        "intake_profile": INTAKE_PROFILE,
        "registry_locked_at": locked_at,
        "previous_registry_digest": previous,
        "records": built,
        "promotion_allowed": False,
    }
    return {**payload, "registry_digest": _digest(payload)}


def _validate_full_record(payload: object, registry_locked_at: str) -> dict:
    row = _mapping(payload, "intake registry record")
    _exact_fields(row, _RECORD_FIELDS, "intake registry record")
    raw = {key: row[key] for key in _RAW_RECORD_FIELDS}
    expected = _build_record(raw, registry_locked_at)
    if row["eligibility_status"] != expected["eligibility_status"]:
        raise ValueError("eligibility_status does not match intake facts")
    if row["eligibility_reason_code"] != expected["eligibility_reason_code"]:
        raise ValueError("eligibility_reason_code does not match intake facts")
    supplied = _sha256_text(row["intake_record_digest"], "intake_record_digest")
    if supplied != expected["intake_record_digest"]:
        raise ValueError("intake_record_digest does not match record payload")
    return copy.deepcopy(dict(row))


def validate_intake_registry(payload: object) -> dict:
    registry = _mapping(payload, "intake registry")
    _exact_fields(registry, _REGISTRY_FIELDS, "intake registry")
    if registry["schema_version"] != REGISTRY_SCHEMA:
        raise ValueError("unsupported intake registry schema_version")
    if registry["intake_profile"] != INTAKE_PROFILE:
        raise ValueError("unsupported intake_profile")
    locked_at = _timestamp(registry["registry_locked_at"], "registry_locked_at")
    _optional_sha256(registry["previous_registry_digest"], "previous_registry_digest")
    _false(registry["promotion_allowed"], "promotion_allowed")
    records = [_validate_full_record(row, locked_at) for row in _list(registry["records"], "records")]
    case_ids = [row["opaque_case_id"] for row in records]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("opaque_case_id values must be unique")
    if case_ids != sorted(case_ids):
        raise ValueError("intake registry records must use canonical opaque_case_id order")
    supplied = _sha256_text(registry["registry_digest"], "registry_digest")
    digest_payload = dict(registry)
    digest_payload.pop("registry_digest")
    if supplied != _digest(digest_payload):
        raise ValueError("registry_digest does not match registry payload")
    return copy.deepcopy(dict(registry))


def validate_intake_registry_successor(current: object, previous: object) -> dict:
    current_registry = validate_intake_registry(current)
    previous_registry = validate_intake_registry(previous)
    if current_registry["previous_registry_digest"] != previous_registry["registry_digest"]:
        raise ValueError("successor previous_registry_digest does not match previous registry")
    if _timestamp_value(current_registry["registry_locked_at"]) < _timestamp_value(previous_registry["registry_locked_at"]):
        raise ValueError("successor registry_locked_at cannot move backward")

    previous_rows = {row["opaque_case_id"]: row for row in previous_registry["records"]}
    current_rows = {row["opaque_case_id"]: row for row in current_registry["records"]}
    if not set(previous_rows).issubset(current_rows):
        raise ValueError("successor cannot delete prior intake records")
    for case_id, prior in previous_rows.items():
        if current_rows[case_id] != prior:
            raise ValueError("successor cannot mutate prior intake records")
    if len(current_rows) <= len(previous_rows):
        raise ValueError("successor must append at least one new intake record")
    return copy.deepcopy(current_registry)
