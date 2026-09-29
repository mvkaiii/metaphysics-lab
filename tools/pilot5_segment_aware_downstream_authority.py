"""Pilot-5 preregistered segment-aware downstream authority adapter.

Research-only governance helper. It preserves each manifested segment's frozen
single-source Claim Evidence -> C1 -> EFA -> C2 -> HCC -> HOC authority chain.
It never synthesizes a replacement ranking/structural/EFA authority, selects a
best segment, or increases confidence/specificity because a claim repeats.

Window-level authority is conservative: only an identical render-unit
composition that is renderable in every manifested segment may remain
renderable across the full approved window. Existing yearly child claim
identity is preserved.
"""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping, Sequence

from engine.distribution.claim_consumption_contract import CLAIM_CONSUMPTION_PROFILE_VERSION
from engine.distribution.claim_evidence import CLAIM_EVIDENCE_PROFILE_VERSION
from engine.distribution.event_family_attribution import EVENT_FAMILY_ATTRIBUTION_PROFILE_VERSION
from engine.distribution.hierarchical_claim_authority import HIERARCHICAL_CLAIM_AUTHORITY_PROFILE_VERSION
from engine.distribution.hybrid_claim_composer import HYBRID_CLAIM_COMPOSER_PROFILE_VERSION
from engine.distribution.hybrid_output_contract import HYBRID_OUTPUT_CONTRACT_PROFILE_VERSION
from engine.distribution.interpretation_contract import INTERPRETATION_PROFILE_VERSION
from engine.distribution.prospective import METHOD_VERSION
from tools.pilot3_yearly_claim_universe import _validated_snapshot_manifest, _validated_universe

SEGMENT_AWARE_WINDOW_AUTHORITY_SCHEMA = "prospective-segment-aware-window-authority.v1"
SEGMENT_AWARE_WINDOW_AUTHORITY_PROFILE = "lin_tianji_segment_aware_window_authority_v1"
SEGMENT_AWARE_WINDOW_AUTHORITY_RULE = (
    "unanimous_stable_render_unit_across_all_manifested_segments_no_authority_synthesis"
)
PREDICTION_BRIDGE_RULE = (
    "full_window_single_child_exact_identity_all_eligible_claims_no_confidence_uplift"
)

_SEGMENT_FIELDS = frozenset((
    "snapshot_id",
    "structural_interpretation_digest",
    "base_ranking_digest",
    "claim_evidence_bundle",
    "claim_consumption_bundle",
    "event_family_attribution_bundle",
    "hierarchical_claim_authority_bundle",
    "interpretation_contract_bundle",
    "hybrid_claim_composer_bundle",
    "hybrid_output_contract_bundle",
))
_SPECIFICITY_ORDER = {"event_family": 0, "concrete_event": 1}
_CONFIDENCE_ORDER = {"low": 0, "medium": 1, "high": 2}
_CONFIDENCE_MAP = {
    "low_confidence": "low",
    "moderate_confidence": "medium",
    "high_confidence": "high",
}
_VISIBILITY_ORDER = {"secondary": 0, "primary": 1}


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
        raise ValueError("Pilot-5 authority input must contain canonical JSON values") from exc


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be a mapping")
    return value


def _sequence(value: object, label: str) -> Sequence[object]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError(f"{label} must be a sequence")
    return value


def _list(value: object, label: str) -> list:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be non-empty text")
    return value.strip()


def _sha256(value: object, label: str) -> str:
    text = _text(value, label)
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise ValueError(f"{label} must be lowercase SHA-256 hex")
    return text


def _exact_fields(value: Mapping[str, object], allowed: frozenset[str], label: str) -> None:
    missing = sorted(allowed - set(value))
    unknown = sorted(set(value) - allowed)
    if missing:
        raise ValueError(f"{label} is missing required fields: {missing}")
    if unknown:
        raise ValueError(f"{label} contains unknown fields: {unknown}")


def _validated_bundle(value: object, digest_field: str, label: str) -> dict:
    bundle = _mapping(value, label)
    supplied = _sha256(bundle.get(digest_field), f"{label}.{digest_field}")
    body = copy.deepcopy(dict(bundle))
    body.pop(digest_field, None)
    if _digest(body) != supplied:
        raise ValueError(f"{label} digest does not match canonical payload")
    return copy.deepcopy(dict(bundle))


def _unique_rows(rows: object, id_field: str, label: str) -> dict[str, Mapping[str, object]]:
    result = {}
    for raw in _list(rows, label):
        row = _mapping(raw, f"{label} row")
        identity = _text(row.get(id_field), f"{label}.{id_field}")
        if identity in result:
            raise ValueError(f"{label} {id_field} values must be unique")
        result[identity] = row
    return result


def _validated_segment(raw: object, manifest_row: Mapping[str, object], universe_source: Mapping[str, object]) -> dict:
    row = _mapping(raw, "segment authority row")
    _exact_fields(row, _SEGMENT_FIELDS, "segment authority row")
    snapshot_id = _text(row.get("snapshot_id"), "snapshot_id")
    if snapshot_id != manifest_row["snapshot_id"] or snapshot_id != universe_source["snapshot_id"]:
        raise ValueError("segment snapshot_id must match manifest and yearly universe order")

    structural_digest = _sha256(row.get("structural_interpretation_digest"), "structural_interpretation_digest")
    ranking_digest = _sha256(row.get("base_ranking_digest"), "base_ranking_digest")
    if structural_digest != manifest_row["structural_state_digest"]:
        raise ValueError("segment structural digest must equal frozen snapshot manifest")
    if structural_digest != universe_source["structural_state_digest"]:
        raise ValueError("segment structural digest must equal yearly universe provenance")

    claim = _validated_bundle(row.get("claim_evidence_bundle"), "claim_evidence_digest", "claim evidence")
    if claim.get("profile_version") != CLAIM_EVIDENCE_PROFILE_VERSION or claim.get("target_scope") != "yearly":
        raise ValueError("claim evidence profile/scope does not match Pilot-5 frozen authority")
    if claim.get("base_ranking_digest") != ranking_digest:
        raise ValueError("claim evidence ranking provenance mismatch")
    if claim.get("structural_interpretation_digest") != structural_digest:
        raise ValueError("claim evidence structural provenance mismatch")
    parents = _unique_rows(claim.get("packets"), "claim_id", "claim evidence packets")
    parent_confidence = {}
    for parent_id, packet in parents.items():
        confidence = packet.get("confidence_class")
        if confidence not in _CONFIDENCE_MAP:
            raise ValueError("claim evidence confidence_class is unsupported")
        parent_confidence[parent_id] = _CONFIDENCE_MAP[str(confidence)]

    c1 = _validated_bundle(row.get("claim_consumption_bundle"), "claim_consumption_digest", "claim consumption")
    if c1.get("profile_version") != CLAIM_CONSUMPTION_PROFILE_VERSION or c1.get("target_scope") != "yearly":
        raise ValueError("claim consumption profile/scope does not match Pilot-5 frozen authority")
    if c1.get("claim_evidence_digest") != claim["claim_evidence_digest"]:
        raise ValueError("claim consumption does not bind segment claim evidence")

    efa = _validated_bundle(row.get("event_family_attribution_bundle"), "event_family_attribution_digest", "EFA")
    if efa.get("profile_version") != EVENT_FAMILY_ATTRIBUTION_PROFILE_VERSION or efa.get("target_scope") != "yearly":
        raise ValueError("EFA profile/scope does not match Pilot-5 frozen authority")
    if efa.get("base_ranking_digest") != ranking_digest or efa.get("structural_interpretation_digest") != structural_digest:
        raise ValueError("EFA ranking/structural provenance mismatch")
    if efa["event_family_attribution_digest"] != universe_source["event_family_attribution_digest"]:
        raise ValueError("EFA digest must equal yearly-universe source provenance")
    children = _unique_rows(efa.get("children"), "child_claim_id", "EFA children")
    if not children:
        raise ValueError("every segment must contain a complete non-empty EFA child inventory")
    child_ids = sorted(children)
    if len(child_ids) != universe_source["child_count"]:
        raise ValueError("EFA child count must equal yearly-universe source provenance")
    if _digest({"locked_claim_ids": child_ids}) != universe_source["child_set_digest"]:
        raise ValueError("EFA child set must equal yearly-universe source provenance")

    child_identity = {}
    child_confidence = {}
    for child_id, child in children.items():
        parent_id = _text(child.get("parent_claim_id"), "EFA.parent_claim_id")
        domain = _text(child.get("primary_domain"), "EFA.primary_domain")
        family = _text(child.get("event_family"), "EFA.event_family")
        if parent_id not in parents:
            raise ValueError("EFA child parent must exist in Claim Evidence")
        if parents[parent_id].get("primary_domain") != domain:
            raise ValueError("EFA child domain must match Claim Evidence parent domain")
        child_identity[child_id] = {
            "parent_claim_id": parent_id,
            "primary_domain": domain,
            "event_family": family,
        }
        child_confidence[child_id] = parent_confidence[parent_id]

    c2 = _validated_bundle(row.get("hierarchical_claim_authority_bundle"), "hierarchical_claim_authority_digest", "C2")
    if c2.get("profile_version") != HIERARCHICAL_CLAIM_AUTHORITY_PROFILE_VERSION or c2.get("target_scope") != "yearly":
        raise ValueError("C2 profile/scope does not match Pilot-5 frozen authority")
    if c2.get("claim_evidence_digest") != claim["claim_evidence_digest"]:
        raise ValueError("C2 claim-evidence provenance mismatch")
    if c2.get("claim_consumption_digest") != c1["claim_consumption_digest"]:
        raise ValueError("C2 C1 provenance mismatch")
    if c2.get("event_family_attribution_digest") != efa["event_family_attribution_digest"]:
        raise ValueError("C2 EFA provenance mismatch")
    c2_rows = _unique_rows(c2.get("decisions"), "child_claim_id", "C2 decisions")
    if set(c2_rows) != set(children):
        raise ValueError("C2 child set must exactly equal segment EFA child set")

    interpretation = _validated_bundle(row.get("interpretation_contract_bundle"), "interpretation_contract_digest", "interpretation contract")
    if interpretation.get("profile_version") != INTERPRETATION_PROFILE_VERSION or interpretation.get("target_scope") != "yearly":
        raise ValueError("interpretation profile/scope does not match Pilot-5 frozen authority")
    if interpretation.get("base_ranking_digest") != ranking_digest:
        raise ValueError("interpretation ranking provenance mismatch")

    hcc = _validated_bundle(row.get("hybrid_claim_composer_bundle"), "hybrid_claim_composer_digest", "HCC")
    if hcc.get("profile_version") != HYBRID_CLAIM_COMPOSER_PROFILE_VERSION or hcc.get("target_scope") != "yearly":
        raise ValueError("HCC profile/scope does not match Pilot-5 frozen authority")
    if hcc.get("hierarchical_claim_authority_digest") != c2["hierarchical_claim_authority_digest"]:
        raise ValueError("HCC C2 provenance mismatch")
    if hcc.get("event_family_attribution_digest") != efa["event_family_attribution_digest"]:
        raise ValueError("HCC EFA provenance mismatch")
    if hcc.get("source_interpretation_contract_digest") != interpretation["interpretation_contract_digest"]:
        raise ValueError("HCC interpretation provenance mismatch")
    if hcc.get("source_claim_evidence_digest") != claim["claim_evidence_digest"]:
        raise ValueError("HCC claim-evidence provenance mismatch")
    hcc_children = _unique_rows(hcc.get("children"), "child_claim_id", "HCC children")
    if set(hcc_children) != set(children):
        raise ValueError("HCC child set must exactly equal segment EFA child set")

    hoc = _validated_bundle(row.get("hybrid_output_contract_bundle"), "hybrid_output_contract_digest", "HOC")
    if hoc.get("profile_version") != HYBRID_OUTPUT_CONTRACT_PROFILE_VERSION or hoc.get("target_scope") != "yearly":
        raise ValueError("HOC profile/scope does not match Pilot-5 frozen authority")
    if hoc.get("source_hybrid_claim_composer_digest") != hcc["hybrid_claim_composer_digest"]:
        raise ValueError("HOC HCC provenance mismatch")
    ordinary = _unique_rows(hoc.get("children"), "child_claim_id", "HOC children")
    audit = _unique_rows(hoc.get("audit_only_children"), "child_claim_id", "HOC audit children")
    if set(ordinary) & set(audit) or set(ordinary) | set(audit) != set(children):
        raise ValueError("HOC ordinary + audit child census must exactly equal EFA child census")
    for child_id, hoc_child in {**ordinary, **audit}.items():
        ident = child_identity[child_id]
        if hoc_child.get("parent_claim_id") != ident["parent_claim_id"]:
            raise ValueError("HOC child parent identity mismatch")
        if hoc_child.get("primary_domain") != ident["primary_domain"] or hoc_child.get("event_family") != ident["event_family"]:
            raise ValueError("HOC child domain/event-family identity mismatch")

    units = {}
    consumed = set()
    for raw_unit in _list(hoc.get("render_units"), "HOC render_units"):
        unit = _mapping(raw_unit, "HOC render unit")
        member_ids = [_text(item, "render unit member") for item in _sequence(unit.get("member_child_claim_ids"), "render unit members")]
        if not member_ids or len(member_ids) != len(set(member_ids)):
            raise ValueError("HOC render-unit members must be non-empty and unique")
        if any(child_id not in ordinary for child_id in member_ids):
            raise ValueError("HOC render unit may consume only ordinary renderable children")
        if consumed.intersection(member_ids):
            raise ValueError("HOC child may belong to only one render unit")
        consumed.update(member_ids)
        if unit.get("causality_allowed") is not False:
            raise ValueError("Pilot-5 requires HOC causality_allowed=false")
        if unit.get("source_efa_digest") != efa["event_family_attribution_digest"]:
            raise ValueError("HOC render unit EFA provenance mismatch")
        if unit.get("source_c2_digest") != c2["hierarchical_claim_authority_digest"]:
            raise ValueError("HOC render unit C2 provenance mismatch")
        if unit.get("source_hcc_digest") != hcc["hybrid_claim_composer_digest"]:
            raise ValueError("HOC render unit HCC provenance mismatch")
        domain = _text(unit.get("primary_domain"), "render unit primary_domain")
        composition = _text(unit.get("composition_type"), "render unit composition_type")
        specificity = unit.get("authorized_specificity")
        if specificity not in _SPECIFICITY_ORDER:
            raise ValueError("HOC render unit specificity is unsupported for Pilot-5")
        visibility = unit.get("visibility")
        if visibility not in _VISIBILITY_ORDER:
            raise ValueError("HOC render unit visibility is unsupported for Pilot-5")
        caveats = [_text(item, "required_caveat") for item in _sequence(unit.get("required_caveats"), "required_caveats")]
        relations = [_text(item, "cross_system_relation") for item in _sequence(unit.get("cross_system_relations"), "cross_system_relations")]
        key = _digest({
            "primary_domain": domain,
            "composition_type": composition,
            "member_child_claim_ids": member_ids,
        })
        if key in units:
            raise ValueError("HOC render-unit composition identities must be unique")
        units[key] = {
            "unit_identity_digest": key,
            "primary_domain": domain,
            "composition_type": composition,
            "member_child_claim_ids": member_ids,
            "visibility": str(visibility),
            "authorized_specificity": str(specificity),
            "required_caveats": caveats,
            "cross_system_relations": relations,
            "render_unit_id": _text(unit.get("render_unit_id"), "render_unit_id"),
        }
    if consumed != set(ordinary):
        raise ValueError("HOC render units must consume every ordinary child exactly once")

    return {
        "snapshot_id": snapshot_id,
        "structural_interpretation_digest": structural_digest,
        "base_ranking_digest": ranking_digest,
        "claim_evidence_digest": claim["claim_evidence_digest"],
        "claim_consumption_digest": c1["claim_consumption_digest"],
        "event_family_attribution_digest": efa["event_family_attribution_digest"],
        "hierarchical_claim_authority_digest": c2["hierarchical_claim_authority_digest"],
        "interpretation_contract_digest": interpretation["interpretation_contract_digest"],
        "hybrid_claim_composer_digest": hcc["hybrid_claim_composer_digest"],
        "hybrid_output_contract_digest": hoc["hybrid_output_contract_digest"],
        "child_ids": child_ids,
        "child_identity": child_identity,
        "child_confidence": child_confidence,
        "renderable_child_ids": sorted(ordinary),
        "units": units,
    }


def _most_conservative(values: Sequence[str], order: Mapping[str, int], label: str) -> str:
    if not values:
        raise ValueError(f"{label} must not be empty")
    if any(value not in order for value in values):
        raise ValueError(f"{label} contains unsupported values")
    return min(values, key=order.__getitem__)


def build_segment_aware_window_authority(
    *,
    snapshot_manifest: Mapping[str, object],
    yearly_claim_universe: Mapping[str, object],
    segment_outputs: Sequence[Mapping[str, object]],
) -> dict:
    manifest = _validated_snapshot_manifest(snapshot_manifest)
    universe = _validated_universe(yearly_claim_universe)
    if universe["snapshot_manifest_digest"] != manifest["snapshot_manifest_digest"]:
        raise ValueError("yearly universe must bind the supplied snapshot manifest")
    if universe["window_policy_digest"] != manifest["window_policy_digest"]:
        raise ValueError("yearly universe/window policy must match snapshot manifest")

    raw_segments = list(_sequence(segment_outputs, "segment_outputs"))
    if len(raw_segments) != len(manifest["snapshots"]):
        raise ValueError("segment output census must exactly equal frozen snapshot manifest")
    if len(universe["source_snapshots"]) != len(manifest["snapshots"]):
        raise ValueError("yearly universe source census must equal snapshot manifest")

    segments = [
        _validated_segment(raw, manifest_row, universe_source)
        for raw, manifest_row, universe_source in zip(
            raw_segments, manifest["snapshots"], universe["source_snapshots"]
        )
    ]
    if [row["snapshot_id"] for row in segments] != [row["snapshot_id"] for row in manifest["snapshots"]]:
        raise ValueError("segment outputs must exactly preserve snapshot manifest order")

    observed_union = sorted({claim_id for segment in segments for claim_id in segment["child_ids"]})
    if observed_union != universe["locked_claim_ids"]:
        raise ValueError("segment EFA union must exactly equal AGG-01 yearly claim universe")

    common_unit_keys = set(segments[0]["units"])
    for segment in segments[1:]:
        common_unit_keys.intersection_update(segment["units"])

    window_units = []
    renderable_claim_ids = set()
    claim_to_unit = {}
    for unit_key in sorted(common_unit_keys):
        rows = [segment["units"][unit_key] for segment in segments]
        member_ids = list(rows[0]["member_child_claim_ids"])
        if any(row["member_child_claim_ids"] != member_ids for row in rows):
            raise ValueError("stable render-unit identity cannot change member order")
        specificity = _most_conservative(
            [row["authorized_specificity"] for row in rows],
            _SPECIFICITY_ORDER,
            "authorized_specificity",
        )
        visibility = _most_conservative(
            [row["visibility"] for row in rows],
            _VISIBILITY_ORDER,
            "visibility",
        )
        caveats = sorted({item for row in rows for item in row["required_caveats"]})
        relations = sorted({item for row in rows for item in row["cross_system_relations"]})
        segment_provenance = []
        for segment, row in zip(segments, rows):
            segment_provenance.append({
                "snapshot_id": segment["snapshot_id"],
                "structural_interpretation_digest": segment["structural_interpretation_digest"],
                "base_ranking_digest": segment["base_ranking_digest"],
                "claim_evidence_digest": segment["claim_evidence_digest"],
                "claim_consumption_digest": segment["claim_consumption_digest"],
                "event_family_attribution_digest": segment["event_family_attribution_digest"],
                "hierarchical_claim_authority_digest": segment["hierarchical_claim_authority_digest"],
                "interpretation_contract_digest": segment["interpretation_contract_digest"],
                "hybrid_claim_composer_digest": segment["hybrid_claim_composer_digest"],
                "hybrid_output_contract_digest": segment["hybrid_output_contract_digest"],
                "source_render_unit_id": row["render_unit_id"],
            })
        window_unit_id = "window-render-unit:" + _digest({
            "unit_identity_digest": unit_key,
            "snapshot_manifest_digest": manifest["snapshot_manifest_digest"],
        })
        for claim_id in member_ids:
            if claim_id in claim_to_unit:
                raise ValueError("window renderable child may belong to only one stable unit")
            claim_to_unit[claim_id] = window_unit_id
            renderable_claim_ids.add(claim_id)
        window_units.append({
            "window_render_unit_id": window_unit_id,
            "unit_identity_digest": unit_key,
            "primary_domain": rows[0]["primary_domain"],
            "composition_type": rows[0]["composition_type"],
            "member_child_claim_ids": member_ids,
            "visibility": visibility,
            "authorized_specificity": specificity,
            "required_caveats": caveats,
            "cross_system_relations_observed": relations,
            "causality_allowed": False,
            "repetition_increases_authority": False,
            "segment_provenance": segment_provenance,
        })

    abstained = []
    for claim_id in universe["locked_claim_ids"]:
        if claim_id in renderable_claim_ids:
            continue
        present_every = all(claim_id in segment["child_ids"] for segment in segments)
        render_every = all(claim_id in segment["renderable_child_ids"] for segment in segments)
        if not present_every:
            reason = "not_in_every_segment_universe"
        elif not render_every:
            reason = "not_renderable_in_every_segment"
        else:
            reason = "unstable_render_unit_composition"
        abstained.append({"child_claim_id": claim_id, "reason": reason})

    prediction_authority = []
    prediction_ineligible = []
    identity_by_claim = {}
    for claim_id in universe["locked_claim_ids"]:
        identities = [segment["child_identity"].get(claim_id) for segment in segments]
        existing = [identity for identity in identities if identity is not None]
        if existing and any(identity != existing[0] for identity in existing[1:]):
            raise ValueError("child claim identity cannot change across segments")
        if existing:
            identity_by_claim[claim_id] = existing[0]

    for unit in window_units:
        members = unit["member_child_claim_ids"]
        if len(members) != 1:
            for claim_id in members:
                prediction_ineligible.append({
                    "child_claim_id": claim_id,
                    "reason": "multi_member_render_unit_not_mappable_to_single_event_family_forecast_claim_v1",
                })
            continue
        claim_id = members[0]
        confidence_cap = _most_conservative(
            [segment["child_confidence"][claim_id] for segment in segments],
            _CONFIDENCE_ORDER,
            "confidence cap",
        )
        identity = identity_by_claim[claim_id]
        prediction_authority.append({
            "claim_id": claim_id,
            "primary_domain": identity["primary_domain"],
            "event_family": identity["event_family"],
            "authorized_specificity": unit["authorized_specificity"],
            "visibility": unit["visibility"],
            "confidence_cap": confidence_cap,
            "required_caveats": list(unit["required_caveats"]),
            "source_window_render_unit_id": unit["window_render_unit_id"],
        })

    prediction_authority.sort(key=lambda row: row["claim_id"])
    prediction_eligible = [row["claim_id"] for row in prediction_authority]
    prediction_ineligible.sort(key=lambda row: row["child_claim_id"])

    body = {
        "schema_version": SEGMENT_AWARE_WINDOW_AUTHORITY_SCHEMA,
        "profile_version": SEGMENT_AWARE_WINDOW_AUTHORITY_PROFILE,
        "authority_rule": SEGMENT_AWARE_WINDOW_AUTHORITY_RULE,
        "prediction_bridge_rule": PREDICTION_BRIDGE_RULE,
        "snapshot_manifest_digest": manifest["snapshot_manifest_digest"],
        "claim_universe_digest": universe["claim_universe_digest"],
        "window_policy_digest": manifest["window_policy_digest"],
        "segment_count": len(segments),
        "window_render_units": window_units,
        "window_renderable_claim_ids": sorted(renderable_claim_ids),
        "window_abstained_claims": abstained,
        "prediction_claim_authority": prediction_authority,
        "prediction_lock_eligible_claim_ids": prediction_eligible,
        "prediction_lock_ineligible_claims": prediction_ineligible,
        "confidence_repetition_uplift_allowed": False,
        "specificity_repetition_uplift_allowed": False,
        "best_snapshot_selection_allowed": False,
        "synthetic_single_source_authority_allowed": False,
        "promotion_allowed": False,
    }
    return {**body, "segment_aware_authority_digest": _digest(body)}


def _validated_authority(value: object) -> dict:
    authority = _mapping(value, "segment-aware authority")
    supplied = _sha256(authority.get("segment_aware_authority_digest"), "segment_aware_authority_digest")
    body = copy.deepcopy(dict(authority))
    body.pop("segment_aware_authority_digest", None)
    if _digest(body) != supplied:
        raise ValueError("segment-aware authority digest does not match payload")
    if authority.get("schema_version") != SEGMENT_AWARE_WINDOW_AUTHORITY_SCHEMA:
        raise ValueError("segment-aware authority schema is unsupported")
    if authority.get("profile_version") != SEGMENT_AWARE_WINDOW_AUTHORITY_PROFILE:
        raise ValueError("segment-aware authority profile is unsupported")
    if authority.get("authority_rule") != SEGMENT_AWARE_WINDOW_AUTHORITY_RULE:
        raise ValueError("segment-aware authority rule is unsupported")
    if authority.get("prediction_bridge_rule") != PREDICTION_BRIDGE_RULE:
        raise ValueError("prediction bridge rule is unsupported")
    for field in (
        "confidence_repetition_uplift_allowed",
        "specificity_repetition_uplift_allowed",
        "best_snapshot_selection_allowed",
        "synthetic_single_source_authority_allowed",
        "promotion_allowed",
    ):
        if authority.get(field) is not False:
            raise ValueError(f"{field} must remain false")
    return copy.deepcopy(dict(authority))


def validate_locked_forecast_against_segment_aware_authority(
    *,
    locked_forecast: Mapping[str, object],
    segment_aware_authority: Mapping[str, object],
    approved_window_start: str,
    approved_window_end: str,
) -> dict:
    authority = _validated_authority(segment_aware_authority)
    eligible = list(authority.get("prediction_lock_eligible_claim_ids", []))
    if not eligible:
        raise ValueError("no claim is eligible for Pilot-5 prediction lock")

    forecast = _mapping(locked_forecast, "locked_forecast")
    if forecast.get("status") != "locked" or forecast.get("method_version") != METHOD_VERSION:
        raise ValueError("locked_forecast must be an existing valid prospective lock")
    supplied = _sha256(forecast.get("canonical_digest"), "locked_forecast.canonical_digest")
    body = {
        "method_version": forecast.get("method_version"),
        "anchor": forecast.get("anchor"),
        "claims": forecast.get("claims"),
    }
    if _digest(body) != supplied:
        raise ValueError("locked_forecast canonical digest does not match payload")

    claims = _unique_rows(forecast.get("claims"), "claim_id", "locked forecast claims")
    if sorted(claims) != eligible:
        raise ValueError("prediction lock claim IDs must exactly equal every Pilot-5 eligible claim")
    authority_by_id = {
        row["claim_id"]: row
        for row in _list(authority.get("prediction_claim_authority"), "prediction_claim_authority")
    }
    if set(authority_by_id) != set(eligible):
        raise ValueError("prediction authority census must equal eligible claim IDs")

    for claim_id in eligible:
        claim = claims[claim_id]
        allowed = authority_by_id[claim_id]
        if "priority" in claim or "partial_if" in claim:
            raise ValueError("Pilot-5 prediction bridge forbids priority/partial_if subset semantics")
        if claim.get("primary_domain") != allowed["primary_domain"] or claim.get("event_family") != allowed["event_family"]:
            raise ValueError("prediction claim domain/event-family identity exceeds Pilot-5 authority")
        window = _mapping(claim.get("forecast_window"), "forecast_window")
        if window.get("start") != approved_window_start or window.get("end") != approved_window_end:
            raise ValueError("Pilot-5 eligible claims must use the entire approved outcome window")
        confidence = claim.get("confidence")
        cap = allowed["confidence_cap"]
        if confidence not in _CONFIDENCE_ORDER or cap not in _CONFIDENCE_ORDER:
            raise ValueError("Pilot-5 prediction confidence is unsupported")
        if _CONFIDENCE_ORDER[str(confidence)] > _CONFIDENCE_ORDER[str(cap)]:
            raise ValueError("prediction confidence cannot exceed the most conservative segment cap")
        if claim.get("contamination_state") != "clean_prospective":
            raise ValueError("Pilot-5 prediction claims must remain clean prospective")
        if claim.get("evaluation_eligibility") != "clean_scorable":
            raise ValueError("Pilot-5 prediction claims must remain clean scorable")
        if claim.get("method_version") != METHOD_VERSION:
            raise ValueError("Pilot-5 prediction claim method version mismatch")

    return {
        "status": "valid",
        "prediction_claim_count": len(eligible),
        "segment_aware_authority_digest": authority["segment_aware_authority_digest"],
        "locked_forecast_digest": supplied,
        "prediction_bridge_rule": PREDICTION_BRIDGE_RULE,
        "promotion_allowed": False,
    }
