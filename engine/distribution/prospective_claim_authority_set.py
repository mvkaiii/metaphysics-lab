"""Outcome-blind composite authority for multi-case prospective S1 batches."""

from __future__ import annotations

import hashlib
import json
from typing import Mapping

from .claim_authority_manifest import (
    CLAIM_AUTHORITY_MANIFEST_PROFILE,
    validate_claim_authority_manifest,
)
from .claim_consumption_sampling_eligibility import (
    _derive_case_status,
    validate_sampling_protocol,
    validate_sampling_source_manifest,
)
from .errors import DistributionError


PROSPECTIVE_CLAIM_AUTHORITY_SET_SCHEMA = "v1.6-prospective-claim-authority-set.v1"
PROSPECTIVE_CLAIM_AUTHORITY_SET_PROFILE = "lin_tianji_prospective_claim_authority_set_v1"

_INPUT_MEMBER_FIELDS = frozenset((
    "opaque_case_id",
    "source_record_digest",
    "claim_authority_manifest",
))
_OUTPUT_MEMBER_FIELDS = frozenset((
    "opaque_case_id",
    "source_record_digest",
    "claim_authority_profile",
    "claim_authority_digest",
))
_OUTPUT_FIELDS = frozenset((
    "schema_version",
    "claim_authority_profile",
    "source_manifest_digest",
    "case_authorities",
    "promotion_allowed",
    "claim_authority_digest",
))


def _raise(message: str, details=None) -> None:
    raise DistributionError(
        "invalid_prospective_claim_authority_set",
        message,
        {} if details is None else dict(details),
    )


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        _raise("%s must be a mapping" % field, {"field": field})
    return value


def _list(value: object, field: str) -> list:
    if not isinstance(value, list):
        _raise("%s must be a list" % field, {"field": field})
    return value


def _exact_fields(value: Mapping[str, object], allowed: frozenset, field: str) -> None:
    missing = sorted(allowed - set(value))
    unknown = sorted(set(value) - allowed)
    if missing or unknown:
        _raise(
            "%s fields do not match the fixed contract" % field,
            {"field": field, "missing_fields": missing, "unknown_fields": unknown},
        )


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _raise("%s must be non-empty text" % field, {"field": field})
    return value.strip()


def _sha256(value: object, field: str) -> str:
    text = _text(value, field)
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        _raise("%s must be lowercase SHA-256 hex" % field, {"field": field})
    return text


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
        _raise("claim-authority set must contain canonical JSON values")
        raise AssertionError("unreachable") from exc


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _promotion_false(value: object) -> bool:
    if value is not False:
        _raise("promotion_allowed must be false")
    return False


def _validated_source(sampling_protocol: object, source_manifest: object) -> tuple[dict, dict]:
    validated_protocol = validate_sampling_protocol(sampling_protocol)
    validated_source = validate_sampling_source_manifest(source_manifest, validated_protocol)
    return validated_protocol, validated_source


def _include_ids(validated_source: Mapping[str, object]) -> set[str]:
    result = {
        str(row["opaque_case_id"])
        for row in validated_source["records"]
        if _derive_case_status(row)[0] == "INCLUDE"
    }
    if not result:
        _raise("claim-authority set requires at least one deterministic INCLUDE case")
    return result


def _source_map(validated_source: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    return {str(row["opaque_case_id"]): row for row in validated_source["records"]}


def _validated_input_member(
    raw: object,
    source_rows: Mapping[str, Mapping[str, object]],
) -> dict:
    member = _mapping(raw, "case authority member")
    _exact_fields(member, _INPUT_MEMBER_FIELDS, "case authority member")
    case_id = _text(member.get("opaque_case_id"), "opaque_case_id")
    source_digest = _sha256(member.get("source_record_digest"), "source_record_digest")
    source_row = source_rows.get(case_id)
    if source_row is None:
        _raise("case authority member does not exist in validated source manifest", {"opaque_case_id": case_id})
    if source_digest != source_row["source_record_digest"]:
        _raise("source_record_digest does not match validated source manifest", {"opaque_case_id": case_id})

    manifest = validate_claim_authority_manifest(
        _mapping(member.get("claim_authority_manifest"), "claim_authority_manifest")
    )
    if manifest["claim_authority_profile"] != CLAIM_AUTHORITY_MANIFEST_PROFILE:
        _raise("per-case claim-authority profile is unsupported", {"opaque_case_id": case_id})

    return {
        "opaque_case_id": case_id,
        "source_record_digest": source_digest,
        "claim_authority_profile": manifest["claim_authority_profile"],
        "claim_authority_digest": manifest["claim_authority_digest"],
    }


def build_claim_authority_set(
    sampling_protocol: object,
    source_manifest: object,
    case_authorities: object,
    promotion_allowed: bool = False,
) -> dict:
    """Build one deterministic composite authority for the S1 INCLUDE census."""

    _promotion_false(promotion_allowed)
    _, validated_source = _validated_source(sampling_protocol, source_manifest)
    expected_ids = _include_ids(validated_source)
    source_rows = _source_map(validated_source)

    members = [
        _validated_input_member(raw, source_rows)
        for raw in _list(case_authorities, "case_authorities")
    ]
    ids = [row["opaque_case_id"] for row in members]
    if len(ids) != len(set(ids)):
        _raise("case_authorities contains duplicate opaque_case_id values")
    if set(ids) != expected_ids:
        _raise(
            "case_authorities must exactly equal deterministic S1 INCLUDE case set",
            {
                "missing_case_ids": sorted(expected_ids - set(ids)),
                "extra_case_ids": sorted(set(ids) - expected_ids),
            },
        )

    body = {
        "schema_version": PROSPECTIVE_CLAIM_AUTHORITY_SET_SCHEMA,
        "claim_authority_profile": PROSPECTIVE_CLAIM_AUTHORITY_SET_PROFILE,
        "source_manifest_digest": validated_source["source_manifest_digest"],
        "case_authorities": sorted(members, key=lambda row: row["opaque_case_id"]),
        "promotion_allowed": False,
    }
    return {**body, "claim_authority_digest": _digest(body)}


def _validated_output_member(
    raw: object,
    source_rows: Mapping[str, Mapping[str, object]],
) -> dict:
    member = _mapping(raw, "serialized case authority member")
    _exact_fields(member, _OUTPUT_MEMBER_FIELDS, "serialized case authority member")
    case_id = _text(member.get("opaque_case_id"), "opaque_case_id")
    source_digest = _sha256(member.get("source_record_digest"), "source_record_digest")
    source_row = source_rows.get(case_id)
    if source_row is None:
        _raise("serialized case authority member does not exist in validated source manifest", {"opaque_case_id": case_id})
    if source_digest != source_row["source_record_digest"]:
        _raise("serialized source_record_digest does not match validated source manifest", {"opaque_case_id": case_id})
    profile = _text(member.get("claim_authority_profile"), "claim_authority_profile")
    if profile != CLAIM_AUTHORITY_MANIFEST_PROFILE:
        _raise("serialized per-case claim-authority profile is unsupported", {"opaque_case_id": case_id})
    return {
        "opaque_case_id": case_id,
        "source_record_digest": source_digest,
        "claim_authority_profile": profile,
        "claim_authority_digest": _sha256(member.get("claim_authority_digest"), "claim_authority_digest"),
    }


def validate_claim_authority_set(
    payload: object,
    sampling_protocol: object,
    source_manifest: object,
) -> dict:
    """Validate a serialized composite authority against the frozen S1 census."""

    _, validated_source = _validated_source(sampling_protocol, source_manifest)
    expected_ids = _include_ids(validated_source)
    source_rows = _source_map(validated_source)

    authority = _mapping(payload, "claim authority set")
    _exact_fields(authority, _OUTPUT_FIELDS, "claim authority set")
    if authority.get("schema_version") != PROSPECTIVE_CLAIM_AUTHORITY_SET_SCHEMA:
        _raise("claim-authority set schema is unsupported")
    if authority.get("claim_authority_profile") != PROSPECTIVE_CLAIM_AUTHORITY_SET_PROFILE:
        _raise("claim-authority set profile is unsupported")
    if authority.get("source_manifest_digest") != validated_source["source_manifest_digest"]:
        _raise("claim-authority set source_manifest_digest mismatch")
    _promotion_false(authority.get("promotion_allowed"))

    members = [
        _validated_output_member(raw, source_rows)
        for raw in _list(authority.get("case_authorities"), "case_authorities")
    ]
    ids = [row["opaque_case_id"] for row in members]
    if len(ids) != len(set(ids)):
        _raise("serialized case_authorities contains duplicate opaque_case_id values")
    if set(ids) != expected_ids:
        _raise(
            "serialized case_authorities must exactly equal deterministic S1 INCLUDE case set",
            {
                "missing_case_ids": sorted(expected_ids - set(ids)),
                "extra_case_ids": sorted(set(ids) - expected_ids),
            },
        )

    body = {
        "schema_version": PROSPECTIVE_CLAIM_AUTHORITY_SET_SCHEMA,
        "claim_authority_profile": PROSPECTIVE_CLAIM_AUTHORITY_SET_PROFILE,
        "source_manifest_digest": validated_source["source_manifest_digest"],
        "case_authorities": sorted(members, key=lambda row: row["opaque_case_id"]),
        "promotion_allowed": False,
    }
    supplied = _sha256(authority.get("claim_authority_digest"), "claim_authority_digest")
    if supplied != _digest(body):
        _raise("claim_authority_digest does not match canonical composite authority")
    return {**body, "claim_authority_digest": supplied}
