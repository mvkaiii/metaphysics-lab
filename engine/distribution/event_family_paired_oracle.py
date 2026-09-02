"""Deterministic child-outcome oracle sealing for paired v1.6 research.

The oracle stores structured child outcomes only.  Public seal receipts are
aggregate-only and never expose child identities, domains, event families, or
outcome rows.
"""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime
from typing import Mapping, Sequence


ORACLE_SCHEMA = "v1.6-event-family-paired-oracle.v1"
ORACLE_SEAL_PROFILE_VERSION = "lin_tianji_event_family_paired_oracle_seal_v1"
_ORACLE_SEAL_RECEIPT_SCHEMA = "v1.6-event-family-paired-oracle-seal-receipt.v1"

_ORACLE_FIELDS = frozenset(("schema_version", "classification", "oracle_frozen_at", "cases"))
_CASE_FIELDS = frozenset(("case_id", "target_scope", "child_outcomes", "case_digest"))
_CHILD_FIELDS = frozenset((
    "child_claim_id",
    "primary_domain",
    "event_family",
    "outcome_status",
    "maximum_supported_specificity",
    "caveat_required",
    "expected_cross_system_relation",
))
_UNIVERSE_FIELDS = frozenset(("child_claim_id", "primary_domain", "event_family"))
_RECEIPT_FIELDS = frozenset((
    "profile_version",
    "schema_version",
    "classification",
    "oracle_frozen_at",
    "case_count",
    "child_count",
    "oracle_digest",
    "seal_digest",
    "promotion_allowed",
))

_OUTCOME_STATUSES = frozenset(("supported", "unsupported", "indeterminate"))
_SUPPORTED_SPECIFICITIES = frozenset((
    "event_family",
    "concrete_event",
    "highly_specific_event",
))
_EXPECTED_RELATIONS = frozenset((
    "direct_convergence",
    "single_system_qualified",
    "layered_complement",
    "divergence",
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
        raise ValueError("paired oracle input must be canonical JSON") from exc


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


def _frozen_at(value: object) -> str:
    text = _text(value, "oracle_frozen_at")
    try:
        parsed = datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise ValueError("oracle_frozen_at must be UTC RFC3339 with Z suffix") from exc
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != text:
        raise ValueError("oracle_frozen_at must be UTC RFC3339 with Z suffix")
    return text


def _normalized_universe(value: object) -> list[dict]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("shared_child_universe must be a sequence")
    rows = []
    seen_ids = set()
    seen_pairs = set()
    for raw in value:
        row = _mapping(raw, "shared child universe row")
        _exact_fields(row, _UNIVERSE_FIELDS, "shared child universe row")
        normalized = {
            "child_claim_id": _text(row["child_claim_id"], "child_claim_id"),
            "primary_domain": _text(row["primary_domain"], "primary_domain"),
            "event_family": _text(row["event_family"], "event_family"),
        }
        child_id = normalized["child_claim_id"]
        pair = (normalized["primary_domain"], normalized["event_family"])
        if child_id in seen_ids:
            raise ValueError("shared child universe child_claim_id values must be unique")
        if pair in seen_pairs:
            raise ValueError("shared child universe domain/event-family pairs must be unique")
        seen_ids.add(child_id)
        seen_pairs.add(pair)
        rows.append(normalized)
    if not rows:
        raise ValueError("shared_child_universe must contain at least one child")
    return sorted(rows, key=lambda row: row["child_claim_id"])


def _normalized_child_outcome(raw: object) -> dict:
    row = _mapping(raw, "child outcome")
    _exact_fields(row, _CHILD_FIELDS, "child outcome")
    status = row["outcome_status"]
    if status not in _OUTCOME_STATUSES:
        raise ValueError("outcome_status contains unsupported value")

    maximum = row["maximum_supported_specificity"]
    if status == "supported":
        if maximum not in _SUPPORTED_SPECIFICITIES:
            raise ValueError("supported outcome requires supported specificity")
        normalized_maximum = str(maximum)
    else:
        if maximum is not None:
            raise ValueError("unsupported/indeterminate outcome requires null specificity")
        normalized_maximum = None

    relation = row["expected_cross_system_relation"]
    if relation not in _EXPECTED_RELATIONS:
        raise ValueError("expected_cross_system_relation contains unsupported value")

    return {
        "child_claim_id": _text(row["child_claim_id"], "child_claim_id"),
        "primary_domain": _text(row["primary_domain"], "primary_domain"),
        "event_family": _text(row["event_family"], "event_family"),
        "outcome_status": str(status),
        "maximum_supported_specificity": normalized_maximum,
        "caveat_required": _bool(row["caveat_required"], "caveat_required"),
        "expected_cross_system_relation": str(relation),
    }


def _normalized_case(raw: object, universe: list[dict]) -> dict:
    case = _mapping(raw, "oracle case")
    _exact_fields(case, _CASE_FIELDS, "oracle case")
    children = [
        _normalized_child_outcome(row)
        for row in _list(case["child_outcomes"], "child_outcomes")
    ]
    child_ids = [row["child_claim_id"] for row in children]
    if len(child_ids) != len(set(child_ids)):
        raise ValueError("oracle case child_claim_id values must be unique")
    children.sort(key=lambda row: row["child_claim_id"])

    child_identity = [
        {
            "child_claim_id": row["child_claim_id"],
            "primary_domain": row["primary_domain"],
            "event_family": row["event_family"],
        }
        for row in children
    ]
    if child_identity != universe:
        raise ValueError("oracle case child universe must exactly match shared child universe")

    body = {
        "case_id": _text(case["case_id"], "case_id"),
        "target_scope": _text(case["target_scope"], "target_scope"),
        "child_outcomes": children,
    }
    supplied = _sha256_text(case["case_digest"], "case_digest")
    actual = _digest(body)
    if supplied != actual:
        raise ValueError("case_digest does not match canonical case payload")
    return {**body, "case_digest": supplied}


def _normalized_oracle(oracle: object, universe: list[dict]) -> dict:
    root = _mapping(oracle, "paired event-family oracle")
    _exact_fields(root, _ORACLE_FIELDS, "paired event-family oracle")
    if root["schema_version"] != ORACLE_SCHEMA:
        raise ValueError("unsupported oracle schema_version")
    classification = _text(root["classification"], "classification")
    frozen_at = _frozen_at(root["oracle_frozen_at"])
    cases = [
        _normalized_case(row, universe)
        for row in _list(root["cases"], "cases")
    ]
    if not cases:
        raise ValueError("oracle must contain at least one case")
    case_ids = [row["case_id"] for row in cases]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("oracle case_id values must be unique")
    cases.sort(key=lambda row: row["case_id"])
    return {
        "schema_version": ORACLE_SCHEMA,
        "classification": classification,
        "oracle_frozen_at": frozen_at,
        "cases": cases,
    }


def _build_receipt(oracle: object, shared_child_universe: object) -> dict:
    universe = _normalized_universe(shared_child_universe)
    normalized = _normalized_oracle(oracle, universe)
    oracle_digest = _digest(normalized)
    receipt = {
        "profile_version": ORACLE_SEAL_PROFILE_VERSION,
        "schema_version": _ORACLE_SEAL_RECEIPT_SCHEMA,
        "classification": normalized["classification"],
        "oracle_frozen_at": normalized["oracle_frozen_at"],
        "case_count": len(normalized["cases"]),
        "child_count": sum(len(case["child_outcomes"]) for case in normalized["cases"]),
        "oracle_digest": oracle_digest,
        "promotion_allowed": False,
    }
    receipt["seal_digest"] = _digest(receipt)
    return receipt


def _validated_receipt(raw: object) -> dict:
    receipt = _mapping(raw, "paired oracle seal receipt")
    _exact_fields(receipt, _RECEIPT_FIELDS, "paired oracle seal receipt")
    if receipt["profile_version"] != ORACLE_SEAL_PROFILE_VERSION:
        raise ValueError("unsupported paired oracle seal profile")
    if receipt["schema_version"] != _ORACLE_SEAL_RECEIPT_SCHEMA:
        raise ValueError("unsupported paired oracle seal receipt schema")
    classification = _text(receipt["classification"], "classification")
    frozen_at = _frozen_at(receipt["oracle_frozen_at"])
    for field in ("case_count", "child_count"):
        value = receipt[field]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{field} must be a non-negative integer")
    if receipt["promotion_allowed"] is not False:
        raise ValueError("paired oracle seal receipt cannot allow promotion")
    oracle_digest = _sha256_text(receipt["oracle_digest"], "oracle_digest")
    supplied_seal = _sha256_text(receipt["seal_digest"], "seal_digest")
    body = {
        "profile_version": ORACLE_SEAL_PROFILE_VERSION,
        "schema_version": _ORACLE_SEAL_RECEIPT_SCHEMA,
        "classification": classification,
        "oracle_frozen_at": frozen_at,
        "case_count": receipt["case_count"],
        "child_count": receipt["child_count"],
        "oracle_digest": oracle_digest,
        "promotion_allowed": False,
    }
    if supplied_seal != _digest(body):
        raise ValueError("seal_digest does not match receipt payload")
    return {**body, "seal_digest": supplied_seal}


def seal_event_family_paired_oracle(
    *,
    oracle: Mapping[str, object],
    shared_child_universe: Sequence[Mapping[str, object]],
) -> dict:
    """Return a deterministic aggregate-only public seal receipt."""

    return _build_receipt(oracle, shared_child_universe)


def verify_event_family_paired_oracle(
    *,
    oracle: Mapping[str, object],
    seal_receipt: Mapping[str, object],
    shared_child_universe: Sequence[Mapping[str, object]],
) -> dict:
    """Verify oracle/receipt identity without revealing structured outcome rows."""

    validated = _validated_receipt(seal_receipt)
    expected = _build_receipt(oracle, shared_child_universe)
    if validated != expected:
        raise ValueError("oracle does not match sealed paired oracle identity")
    return copy.deepcopy(expected)
