"""Pilot-3 prospective multi-segment yearly claim-universe authority.

This module resolves only claim *membership* across a predeclared ordered set
of structural snapshots. It does not merge evidence strength, rerank claims,
change specificity, or create event-family semantics.

The frozen aggregation rule is a complete set union across every manifested
EFA child inventory. A snapshot manifest contains only snapshot identity and
structural-state provenance; claim content is deliberately excluded.
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping, Sequence

from .event_family_attribution import EVENT_FAMILY_ATTRIBUTION_PROFILE_VERSION


YEARLY_SEGMENT_SNAPSHOT_MANIFEST_SCHEMA = (
    "prospective-yearly-segment-snapshot-manifest.v1"
)
YEARLY_SEGMENT_SNAPSHOT_MANIFEST_PROFILE = (
    "lin_tianji_yearly_segment_snapshot_manifest_v1"
)
MULTI_SEGMENT_YEARLY_UNIVERSE_SCHEMA = (
    "prospective-multi-segment-yearly-claim-universe.v1"
)
MULTI_SEGMENT_YEARLY_UNIVERSE_PROFILE = (
    "lin_tianji_multi_segment_yearly_claim_universe_v1"
)
MULTI_SEGMENT_YEARLY_UNIVERSE_RULE = (
    "complete_union_of_all_manifested_efa_child_inventories"
)

_MANIFEST_INPUT_FIELDS = frozenset(
    ("snapshot_index", "snapshot_id", "structural_state_digest")
)
_MANIFEST_FIELDS = frozenset(
    (
        "schema_version",
        "profile_version",
        "window_policy_digest",
        "snapshots",
        "promotion_allowed",
        "snapshot_manifest_digest",
    )
)
_EFA_SNAPSHOT_FIELDS = frozenset(
    ("snapshot_id", "event_family_attribution_bundle")
)
_UNIVERSE_FIELDS = frozenset(
    (
        "schema_version",
        "profile_version",
        "aggregation_rule",
        "snapshot_manifest_digest",
        "window_policy_digest",
        "snapshot_count",
        "source_snapshots",
        "locked_claim_ids",
        "locked_claim_count",
        "promotion_allowed",
        "claim_universe_digest",
    )
)
_SOURCE_SNAPSHOT_FIELDS = frozenset(
    (
        "snapshot_index",
        "snapshot_id",
        "structural_state_digest",
        "event_family_attribution_digest",
        "child_set_digest",
        "child_count",
    )
)


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
        raise ValueError(
            "multi-segment yearly universe input must contain canonical JSON values"
        ) from exc


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


def _exact_fields(
    value: Mapping[str, object],
    allowed: frozenset[str],
    label: str,
) -> None:
    missing = sorted(allowed - set(value))
    unknown = sorted(set(value) - allowed)
    if missing:
        raise ValueError(f"{label} is missing required fields: {missing}")
    if unknown:
        raise ValueError(f"{label} contains unknown fields: {unknown}")


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be non-empty text")
    return value.strip()


def _sha256(value: object, label: str) -> str:
    text = _text(value, label)
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise ValueError(f"{label} must be lowercase SHA-256 hex")
    return text


def _nonnegative_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    return value


def _promotion_false(value: object, label: str = "promotion_allowed") -> bool:
    if value is not False:
        raise ValueError(f"{label} must be false")
    return False


def _sequence(value: object, label: str) -> Sequence[object]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError(f"{label} must be a sequence")
    return value


def _normalized_manifest_snapshot(raw: object, expected_index: int) -> dict:
    row = _mapping(raw, "snapshot manifest row")
    _exact_fields(row, _MANIFEST_INPUT_FIELDS, "snapshot manifest row")
    index = _nonnegative_int(row.get("snapshot_index"), "snapshot_index")
    if index != expected_index:
        raise ValueError(
            "snapshot_index must be contiguous and equal manifest order"
        )
    return {
        "snapshot_index": index,
        "snapshot_id": _text(row.get("snapshot_id"), "snapshot_id"),
        "structural_state_digest": _sha256(
            row.get("structural_state_digest"),
            "structural_state_digest",
        ),
    }


def build_yearly_segment_snapshot_manifest(
    *,
    window_policy_digest: str,
    snapshots: Sequence[Mapping[str, object]],
) -> dict:
    """Freeze the complete ordered structural-snapshot census before EFA union.

    The manifest intentionally accepts no EFA child IDs, counts, rankings,
    render decisions, outcomes, or scoring fields.
    """

    policy_digest = _sha256(window_policy_digest, "window_policy_digest")
    rows = _sequence(snapshots, "snapshots")
    if not rows:
        raise ValueError("snapshots must contain at least one structural snapshot")
    normalized = [
        _normalized_manifest_snapshot(raw, index)
        for index, raw in enumerate(rows)
    ]
    ids = [row["snapshot_id"] for row in normalized]
    if len(ids) != len(set(ids)):
        raise ValueError("snapshot_id values must be unique")

    body = {
        "schema_version": YEARLY_SEGMENT_SNAPSHOT_MANIFEST_SCHEMA,
        "profile_version": YEARLY_SEGMENT_SNAPSHOT_MANIFEST_PROFILE,
        "window_policy_digest": policy_digest,
        "snapshots": normalized,
        "promotion_allowed": False,
    }
    return {**body, "snapshot_manifest_digest": _digest(body)}


def _validated_snapshot_manifest(value: object) -> dict:
    manifest = _mapping(value, "snapshot_manifest")
    _exact_fields(manifest, _MANIFEST_FIELDS, "snapshot_manifest")
    if manifest.get("schema_version") != YEARLY_SEGMENT_SNAPSHOT_MANIFEST_SCHEMA:
        raise ValueError("snapshot_manifest schema_version is unsupported")
    if manifest.get("profile_version") != YEARLY_SEGMENT_SNAPSHOT_MANIFEST_PROFILE:
        raise ValueError("snapshot_manifest profile_version is unsupported")
    policy_digest = _sha256(
        manifest.get("window_policy_digest"),
        "snapshot_manifest.window_policy_digest",
    )
    _promotion_false(manifest.get("promotion_allowed"))

    raw_rows = _list(manifest.get("snapshots"), "snapshot_manifest.snapshots")
    if not raw_rows:
        raise ValueError("snapshot_manifest.snapshots must not be empty")
    rows = [
        _normalized_manifest_snapshot(raw, index)
        for index, raw in enumerate(raw_rows)
    ]
    ids = [row["snapshot_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("snapshot_manifest snapshot_id values must be unique")

    body = {
        "schema_version": YEARLY_SEGMENT_SNAPSHOT_MANIFEST_SCHEMA,
        "profile_version": YEARLY_SEGMENT_SNAPSHOT_MANIFEST_PROFILE,
        "window_policy_digest": policy_digest,
        "snapshots": rows,
        "promotion_allowed": False,
    }
    supplied = _sha256(
        manifest.get("snapshot_manifest_digest"),
        "snapshot_manifest_digest",
    )
    if supplied != _digest(body):
        raise ValueError(
            "snapshot_manifest_digest does not match canonical manifest"
        )
    return {**body, "snapshot_manifest_digest": supplied}


def _validated_efa_bundle(value: object) -> dict:
    bundle = _mapping(value, "event_family_attribution_bundle")
    if bundle.get("profile_version") != EVENT_FAMILY_ATTRIBUTION_PROFILE_VERSION:
        raise ValueError("EFA profile does not match frozen authority")
    if bundle.get("target_scope") != "yearly":
        raise ValueError("multi-segment yearly universe requires yearly EFA bundles")
    supplied = _sha256(
        bundle.get("event_family_attribution_digest"),
        "event_family_attribution_digest",
    )
    body = copy.deepcopy(dict(bundle))
    body.pop("event_family_attribution_digest", None)
    if supplied != _digest(body):
        raise ValueError(
            "event_family_attribution_digest does not match canonical EFA bundle"
        )

    children = _list(bundle.get("children"), "EFA children")
    if not children:
        raise ValueError("every manifested EFA snapshot must have a non-empty child inventory")
    ids = []
    for raw in children:
        row = _mapping(raw, "EFA child")
        ids.append(_text(row.get("child_claim_id"), "EFA child_claim_id"))
    if len(ids) != len(set(ids)):
        raise ValueError("EFA child IDs must be unique within each snapshot")
    normalized_ids = tuple(sorted(ids))
    return {
        "event_family_attribution_digest": supplied,
        "child_ids": normalized_ids,
        "child_set_digest": _digest({"locked_claim_ids": list(normalized_ids)}),
    }


def build_multi_segment_yearly_claim_universe(
    *,
    snapshot_manifest: Mapping[str, object],
    efa_snapshots: Sequence[Mapping[str, object]],
) -> dict:
    """Union every complete manifested yearly EFA child inventory exactly once."""

    manifest = _validated_snapshot_manifest(snapshot_manifest)
    raw_efa_snapshots = _sequence(efa_snapshots, "efa_snapshots")
    expected_ids = [row["snapshot_id"] for row in manifest["snapshots"]]

    normalized_inputs = []
    observed_ids = []
    for raw in raw_efa_snapshots:
        row = _mapping(raw, "EFA snapshot")
        _exact_fields(row, _EFA_SNAPSHOT_FIELDS, "EFA snapshot")
        snapshot_id = _text(row.get("snapshot_id"), "EFA snapshot.snapshot_id")
        observed_ids.append(snapshot_id)
        normalized_inputs.append(
            (
                snapshot_id,
                _validated_efa_bundle(
                    row.get("event_family_attribution_bundle")
                ),
            )
        )

    if observed_ids != expected_ids:
        raise ValueError(
            "EFA snapshots must exactly equal the frozen snapshot manifest in canonical order"
        )
    if len(observed_ids) != len(set(observed_ids)):
        raise ValueError("EFA snapshot IDs must be unique")

    union_ids = set()
    sources = []
    for manifest_row, (snapshot_id, efa) in zip(
        manifest["snapshots"],
        normalized_inputs,
    ):
        union_ids.update(efa["child_ids"])
        sources.append(
            {
                "snapshot_index": manifest_row["snapshot_index"],
                "snapshot_id": snapshot_id,
                "structural_state_digest": manifest_row["structural_state_digest"],
                "event_family_attribution_digest": efa[
                    "event_family_attribution_digest"
                ],
                "child_set_digest": efa["child_set_digest"],
                "child_count": len(efa["child_ids"]),
            }
        )

    locked_claim_ids = sorted(union_ids)
    if not locked_claim_ids:
        raise ValueError("aggregated yearly claim universe must not be empty")

    body = {
        "schema_version": MULTI_SEGMENT_YEARLY_UNIVERSE_SCHEMA,
        "profile_version": MULTI_SEGMENT_YEARLY_UNIVERSE_PROFILE,
        "aggregation_rule": MULTI_SEGMENT_YEARLY_UNIVERSE_RULE,
        "snapshot_manifest_digest": manifest["snapshot_manifest_digest"],
        "window_policy_digest": manifest["window_policy_digest"],
        "snapshot_count": len(sources),
        "source_snapshots": sources,
        "locked_claim_ids": locked_claim_ids,
        "locked_claim_count": len(locked_claim_ids),
        "promotion_allowed": False,
    }
    return {**body, "claim_universe_digest": _digest(body)}


def _validated_universe(value: object) -> dict:
    universe = _mapping(value, "yearly claim universe")
    _exact_fields(universe, _UNIVERSE_FIELDS, "yearly claim universe")
    if universe.get("schema_version") != MULTI_SEGMENT_YEARLY_UNIVERSE_SCHEMA:
        raise ValueError("yearly claim universe schema_version is unsupported")
    if universe.get("profile_version") != MULTI_SEGMENT_YEARLY_UNIVERSE_PROFILE:
        raise ValueError("yearly claim universe profile_version is unsupported")
    if universe.get("aggregation_rule") != MULTI_SEGMENT_YEARLY_UNIVERSE_RULE:
        raise ValueError("yearly claim universe aggregation_rule is unsupported")
    _sha256(universe.get("snapshot_manifest_digest"), "snapshot_manifest_digest")
    _sha256(universe.get("window_policy_digest"), "window_policy_digest")
    _promotion_false(universe.get("promotion_allowed"))

    sources = _list(universe.get("source_snapshots"), "source_snapshots")
    snapshot_count = _nonnegative_int(
        universe.get("snapshot_count"),
        "snapshot_count",
    )
    if snapshot_count != len(sources) or snapshot_count < 1:
        raise ValueError("snapshot_count must equal a non-empty source snapshot census")

    normalized_sources = []
    for expected_index, raw in enumerate(sources):
        row = _mapping(raw, "source snapshot")
        _exact_fields(row, _SOURCE_SNAPSHOT_FIELDS, "source snapshot")
        index = _nonnegative_int(row.get("snapshot_index"), "snapshot_index")
        if index != expected_index:
            raise ValueError("source snapshot indices must be contiguous")
        child_count = _nonnegative_int(row.get("child_count"), "child_count")
        if child_count < 1:
            raise ValueError("source snapshot child_count must be positive")
        normalized_sources.append(
            {
                "snapshot_index": index,
                "snapshot_id": _text(row.get("snapshot_id"), "snapshot_id"),
                "structural_state_digest": _sha256(
                    row.get("structural_state_digest"),
                    "structural_state_digest",
                ),
                "event_family_attribution_digest": _sha256(
                    row.get("event_family_attribution_digest"),
                    "event_family_attribution_digest",
                ),
                "child_set_digest": _sha256(
                    row.get("child_set_digest"),
                    "child_set_digest",
                ),
                "child_count": child_count,
            }
        )

    ids = [
        _text(item, "locked_claim_ids")
        for item in _sequence(universe.get("locked_claim_ids"), "locked_claim_ids")
    ]
    if not ids or ids != sorted(ids) or len(ids) != len(set(ids)):
        raise ValueError("locked_claim_ids must be a non-empty sorted unique list")
    locked_count = _nonnegative_int(
        universe.get("locked_claim_count"),
        "locked_claim_count",
    )
    if locked_count != len(ids):
        raise ValueError("locked_claim_count must equal locked_claim_ids length")

    body = {
        "schema_version": MULTI_SEGMENT_YEARLY_UNIVERSE_SCHEMA,
        "profile_version": MULTI_SEGMENT_YEARLY_UNIVERSE_PROFILE,
        "aggregation_rule": MULTI_SEGMENT_YEARLY_UNIVERSE_RULE,
        "snapshot_manifest_digest": universe["snapshot_manifest_digest"],
        "window_policy_digest": universe["window_policy_digest"],
        "snapshot_count": snapshot_count,
        "source_snapshots": normalized_sources,
        "locked_claim_ids": ids,
        "locked_claim_count": locked_count,
        "promotion_allowed": False,
    }
    supplied = _sha256(
        universe.get("claim_universe_digest"),
        "claim_universe_digest",
    )
    if supplied != _digest(body):
        raise ValueError("claim_universe_digest does not match canonical universe")
    return {**body, "claim_universe_digest": supplied}


def validate_locked_claim_ids_against_multi_segment_yearly_universe(
    locked_claim_ids: Sequence[str],
    universe: Mapping[str, object],
) -> dict:
    """Fail closed unless S1 locks exactly the aggregated yearly universe."""

    validated = _validated_universe(universe)
    raw_ids = _sequence(locked_claim_ids, "locked_claim_ids")
    normalized = [_text(item, "locked_claim_ids") for item in raw_ids]
    if not normalized or len(normalized) != len(set(normalized)):
        raise ValueError("locked_claim_ids must be non-empty and unique")
    normalized = sorted(normalized)
    if normalized != validated["locked_claim_ids"]:
        raise ValueError(
            "S1 locked claim IDs must exactly equal the multi-segment yearly universe"
        )
    return {
        "status": "valid",
        "claim_count": len(normalized),
        "claim_set_digest": _digest({"locked_claim_ids": normalized}),
        "claim_universe_digest": validated["claim_universe_digest"],
        "aggregation_rule": MULTI_SEGMENT_YEARLY_UNIVERSE_RULE,
        "promotion_allowed": False,
    }
