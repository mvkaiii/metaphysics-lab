"""Pre-arm exact-match governance for prospective EFA child universes."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence

from .errors import DistributionError
from .event_family_attribution import EVENT_FAMILY_ATTRIBUTION_PROFILE_VERSION
from .event_family_legacy_adapter import EVENT_FAMILY_LEGACY_ADAPTER_PROFILE_VERSION
from .hybrid_output_contract import HYBRID_OUTPUT_CONTRACT_PROFILE_VERSION


_ARM_TYPES = frozenset(("legacy", "candidate_hoc"))


def _raise(message: str, details=None) -> None:
    raise DistributionError(
        "invalid_prospective_claim_universe",
        message,
        {} if details is None else dict(details),
    )


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        _raise("%s must be a mapping" % field, {"field": field})
    return value


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        _raise("%s must be non-empty text" % field, {"field": field})
    return value


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
        _raise("claim-universe payload must contain canonical JSON values")
        raise AssertionError("unreachable") from exc


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _validated_bundle_digest(bundle: Mapping[str, object], field: str) -> str:
    supplied = _sha256(bundle.get(field), field)
    body = dict(bundle)
    body.pop(field, None)
    if supplied != _digest(body):
        _raise("%s does not match canonical bundle" % field)
    return supplied


def _ids_from_rows(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        _raise("%s must be a list" % field, {"field": field})
    ids = []
    for raw in value:
        row = _mapping(raw, "%s row" % field)
        ids.append(_text(row.get("child_claim_id"), "%s.child_claim_id" % field))
    if len(ids) != len(set(ids)):
        _raise("%s child IDs must be unique" % field, {"field": field})
    return tuple(sorted(ids))


def _locked_ids(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        _raise("locked_claim_ids must be a non-empty sequence")
    ids = [_text(item, "locked_claim_ids") for item in value]
    if not ids:
        _raise("locked_claim_ids must not be empty")
    if len(ids) != len(set(ids)):
        _raise("locked_claim_ids must be unique")
    return tuple(sorted(ids))


def _claim_set_digest(ids: tuple[str, ...]) -> str:
    return _digest({"locked_claim_ids": list(ids)})


def child_ids_from_efa_bundle(efa_bundle: Mapping[str, object]) -> tuple[str, ...]:
    """Return the complete EFA child inventory, independent of child_opened."""

    bundle = _mapping(efa_bundle, "efa_bundle")
    if bundle.get("profile_version") != EVENT_FAMILY_ATTRIBUTION_PROFILE_VERSION:
        _raise("EFA profile does not match frozen authority")
    _text(bundle.get("target_scope"), "EFA target_scope")
    _validated_bundle_digest(bundle, "event_family_attribution_digest")
    ids = _ids_from_rows(bundle.get("children"), "EFA children")
    if not ids:
        _raise("EFA child inventory must not be empty")
    return ids


def validate_s1_case_claims_against_efa(*, locked_claim_ids, efa_bundle) -> dict:
    """Fail closed unless one S1 case locks the complete pre-arm EFA inventory."""

    locked = _locked_ids(locked_claim_ids)
    efa = _mapping(efa_bundle, "efa_bundle")
    expected = child_ids_from_efa_bundle(efa)
    if locked != expected:
        _raise(
            "S1 locked claim IDs must exactly equal the complete EFA child inventory",
            {"locked_count": len(locked), "efa_count": len(expected)},
        )
    return {
        "status": "valid",
        "claim_count": len(locked),
        "claim_set_digest": _claim_set_digest(locked),
        "efa_digest": _sha256(
            efa.get("event_family_attribution_digest"),
            "event_family_attribution_digest",
        ),
        "target_scope": _text(efa.get("target_scope"), "EFA target_scope"),
        "promotion_allowed": False,
    }


def _legacy_universe(bundle: Mapping[str, object]) -> tuple[tuple[str, ...], str, str]:
    if bundle.get("profile_version") != EVENT_FAMILY_LEGACY_ADAPTER_PROFILE_VERSION:
        _raise("Legacy Adapter profile does not match frozen authority")
    target_scope = _text(bundle.get("target_scope"), "Legacy target_scope")
    digest = _validated_bundle_digest(bundle, "legacy_adapter_digest")
    ids = _ids_from_rows(bundle.get("children"), "Legacy children")
    if not ids:
        _raise("Legacy child universe must not be empty")
    return ids, digest, target_scope


def _hoc_universe(bundle: Mapping[str, object]) -> tuple[tuple[str, ...], str, str]:
    if bundle.get("profile_version") != HYBRID_OUTPUT_CONTRACT_PROFILE_VERSION:
        _raise("HOC profile does not match frozen authority")
    target_scope = _text(bundle.get("target_scope"), "HOC target_scope")
    digest = _validated_bundle_digest(bundle, "hybrid_output_contract_digest")
    ordinary = _ids_from_rows(bundle.get("children"), "HOC children")
    audit = _ids_from_rows(bundle.get("audit_only_children"), "HOC audit_only_children")
    if set(ordinary) & set(audit):
        _raise("HOC ordinary and audit-only child IDs must be disjoint")
    ids = tuple(sorted(ordinary + audit))
    if not ids:
        _raise("HOC child universe must not be empty")

    render_units = bundle.get("render_units")
    if not isinstance(render_units, list):
        _raise("HOC render_units must be a list")
    rendered = []
    for raw in render_units:
        unit = _mapping(raw, "HOC render unit")
        members = unit.get("member_child_claim_ids")
        if not isinstance(members, list) or not members:
            _raise("HOC render unit members must be a non-empty list")
        rendered.extend(_text(item, "HOC render unit child ID") for item in members)
    if len(rendered) != len(set(rendered)):
        _raise("HOC renderable child cannot be consumed twice")
    if set(rendered) != set(ordinary):
        _raise("HOC render-unit membership must exactly equal ordinary child set")
    return ids, digest, target_scope


def validate_downstream_arm_universe(*, locked_claim_ids, arm_type, arm_bundle) -> dict:
    """Verify that a frozen Legacy or HOC arm preserves the S1 child universe."""

    locked = _locked_ids(locked_claim_ids)
    if arm_type not in _ARM_TYPES:
        _raise("arm_type is unsupported", {"arm_type": arm_type})
    bundle = _mapping(arm_bundle, "arm_bundle")
    if arm_type == "legacy":
        actual, arm_digest, target_scope = _legacy_universe(bundle)
    else:
        actual, arm_digest, target_scope = _hoc_universe(bundle)

    if locked != actual:
        _raise(
            "downstream arm child universe must exactly equal S1 locked claims",
            {"locked_count": len(locked), "arm_count": len(actual), "arm_type": arm_type},
        )
    return {
        "status": "valid",
        "arm_type": arm_type,
        "claim_count": len(locked),
        "claim_set_digest": _claim_set_digest(locked),
        "arm_digest": arm_digest,
        "target_scope": target_scope,
        "promotion_allowed": False,
    }
