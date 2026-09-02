"""Immutable outcome-blind authority manifest for prospective child universes."""

from __future__ import annotations

import hashlib
import json
from typing import Mapping

from .errors import DistributionError
from .event_family_attribution import EVENT_FAMILY_ATTRIBUTION_PROFILE_VERSION
from .prospective_window_scope import (
    PROSPECTIVE_WINDOW_SCOPE_PROFILE,
    resolve_prospective_window_scope,
)
from .structural_policy import MAPPING_PROFILE


CLAIM_AUTHORITY_MANIFEST_SCHEMA = "v1.6-prospective-claim-authority-manifest.v1"
CLAIM_AUTHORITY_MANIFEST_PROFILE = "lin_tianji_prospective_claim_authority_manifest_v1"

_INPUT_FIELDS = frozenset((
    "scope_policy",
    "structural_candidate_authority",
    "mapping_profile",
    "phase3_authority",
    "efa_authority",
    "resolved_target_scope",
    "promotion_allowed",
))
_MANIFEST_FIELDS = frozenset((
    "schema_version",
    "claim_authority_profile",
    "scope_policy",
    "structural_candidate_authority",
    "mapping_profile",
    "phase3_authority",
    "efa_authority",
    "resolved_target_scope",
    "promotion_allowed",
    "claim_authority_digest",
))
_SCOPE_SUMMARY_FIELDS = frozenset(("policy_profile", "policy_digest"))
_STRUCTURAL_AUTHORITY_FIELDS = frozenset(("authority_profile", "authority_digest"))
_PHASE3_AUTHORITY_FIELDS = frozenset(("policy_profile", "policy_digest"))
_EFA_AUTHORITY_FIELDS = frozenset(("profile_version", "authority_digest"))


def _raise(message: str, details=None) -> None:
    raise DistributionError(
        "invalid_claim_authority_manifest",
        message,
        {} if details is None else dict(details),
    )


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        _raise("%s must be a mapping" % field, {"field": field})
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
        _raise("claim-authority manifest must contain canonical JSON values")
        raise AssertionError("unreachable") from exc


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _validated_scope_policy(value: object) -> dict:
    scope = _mapping(value, "scope_policy")
    try:
        expected = resolve_prospective_window_scope(
            {
                "window_start": scope.get("window_start"),
                "window_end": scope.get("window_end"),
                "timezone": scope.get("timezone"),
            }
        )
    except DistributionError as exc:
        _raise("scope_policy is not a valid resolved prospective window scope", {"scope_error": exc.code})
    if dict(scope) != expected:
        _raise("scope_policy does not match canonical resolver output")
    return expected


def _validated_scope_summary(value: object) -> dict:
    scope = _mapping(value, "scope_policy")
    _exact_fields(scope, _SCOPE_SUMMARY_FIELDS, "scope_policy")
    profile = _text(scope.get("policy_profile"), "scope_policy.policy_profile")
    if profile != PROSPECTIVE_WINDOW_SCOPE_PROFILE:
        _raise("scope policy profile is unsupported")
    return {
        "policy_profile": profile,
        "policy_digest": _sha256(scope.get("policy_digest"), "scope_policy.policy_digest"),
    }


def _validated_structural_authority(value: object) -> dict:
    authority = _mapping(value, "structural_candidate_authority")
    _exact_fields(authority, _STRUCTURAL_AUTHORITY_FIELDS, "structural_candidate_authority")
    return {
        "authority_profile": _text(
            authority.get("authority_profile"),
            "structural_candidate_authority.authority_profile",
        ),
        "authority_digest": _sha256(
            authority.get("authority_digest"),
            "structural_candidate_authority.authority_digest",
        ),
    }


def _validated_phase3_authority(value: object) -> dict:
    authority = _mapping(value, "phase3_authority")
    _exact_fields(authority, _PHASE3_AUTHORITY_FIELDS, "phase3_authority")
    return {
        "policy_profile": _text(authority.get("policy_profile"), "phase3_authority.policy_profile"),
        "policy_digest": _sha256(authority.get("policy_digest"), "phase3_authority.policy_digest"),
    }


def _validated_efa_authority(value: object) -> dict:
    authority = _mapping(value, "efa_authority")
    _exact_fields(authority, _EFA_AUTHORITY_FIELDS, "efa_authority")
    profile = _text(authority.get("profile_version"), "efa_authority.profile_version")
    if profile != EVENT_FAMILY_ATTRIBUTION_PROFILE_VERSION:
        _raise("EFA profile does not match the frozen EFA authority")
    return {
        "profile_version": profile,
        "authority_digest": _sha256(authority.get("authority_digest"), "efa_authority.authority_digest"),
    }


def _validated_mapping_profile(value: object) -> str:
    profile = _text(value, "mapping_profile")
    if profile != MAPPING_PROFILE:
        _raise("mapping_profile does not match the frozen structural mapping profile")
    return profile


def _validated_target_scope(value: object) -> str:
    target_scope = _text(value, "resolved_target_scope")
    if target_scope != "yearly":
        _raise("v1 claim authority requires resolved_target_scope=yearly")
    return target_scope


def _promotion_false(value: object) -> bool:
    if value is not False:
        _raise("promotion_allowed must be false")
    return False


def build_claim_authority_manifest(payload: Mapping[str, object]) -> dict:
    """Bind exact pre-outcome semantic authorities into one immutable digest."""

    source = _mapping(payload, "claim authority input")
    _exact_fields(source, _INPUT_FIELDS, "claim authority input")

    resolved_scope = _validated_scope_policy(source.get("scope_policy"))
    target_scope = _validated_target_scope(source.get("resolved_target_scope"))
    if resolved_scope["claim_target_scope"] != target_scope:
        _raise("resolved_target_scope does not match scope-policy authority")

    body = {
        "schema_version": CLAIM_AUTHORITY_MANIFEST_SCHEMA,
        "claim_authority_profile": CLAIM_AUTHORITY_MANIFEST_PROFILE,
        "scope_policy": {
            "policy_profile": resolved_scope["policy_profile"],
            "policy_digest": resolved_scope["policy_digest"],
        },
        "structural_candidate_authority": _validated_structural_authority(
            source.get("structural_candidate_authority")
        ),
        "mapping_profile": _validated_mapping_profile(source.get("mapping_profile")),
        "phase3_authority": _validated_phase3_authority(source.get("phase3_authority")),
        "efa_authority": _validated_efa_authority(source.get("efa_authority")),
        "resolved_target_scope": target_scope,
        "promotion_allowed": _promotion_false(source.get("promotion_allowed")),
    }
    return {**body, "claim_authority_digest": _digest(body)}


def validate_claim_authority_manifest(payload: Mapping[str, object]) -> dict:
    """Validate a serialized claim-authority manifest without outcome access."""

    manifest = _mapping(payload, "claim authority manifest")
    _exact_fields(manifest, _MANIFEST_FIELDS, "claim authority manifest")
    if manifest.get("schema_version") != CLAIM_AUTHORITY_MANIFEST_SCHEMA:
        _raise("claim authority manifest schema is unsupported")
    if manifest.get("claim_authority_profile") != CLAIM_AUTHORITY_MANIFEST_PROFILE:
        _raise("claim authority manifest profile is unsupported")

    body = {
        "schema_version": CLAIM_AUTHORITY_MANIFEST_SCHEMA,
        "claim_authority_profile": CLAIM_AUTHORITY_MANIFEST_PROFILE,
        "scope_policy": _validated_scope_summary(manifest.get("scope_policy")),
        "structural_candidate_authority": _validated_structural_authority(
            manifest.get("structural_candidate_authority")
        ),
        "mapping_profile": _validated_mapping_profile(manifest.get("mapping_profile")),
        "phase3_authority": _validated_phase3_authority(manifest.get("phase3_authority")),
        "efa_authority": _validated_efa_authority(manifest.get("efa_authority")),
        "resolved_target_scope": _validated_target_scope(manifest.get("resolved_target_scope")),
        "promotion_allowed": _promotion_false(manifest.get("promotion_allowed")),
    }
    supplied = _sha256(manifest.get("claim_authority_digest"), "claim_authority_digest")
    if supplied != _digest(body):
        _raise("claim_authority_digest does not match canonical manifest")
    return {**body, "claim_authority_digest": supplied}
