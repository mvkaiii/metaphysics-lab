"""Deterministic Hybrid Output Contract for v1.6 accuracy research.

HOC is the final structured renderer authority. It consumes only the frozen
Hybrid Claim Composer bundle, groups already-authorized children into render
units, keeps abstained children audit-only, and never creates new event
families, upgrades specificity, or authorizes causality.
"""

from __future__ import annotations

import hashlib
import json
from typing import Mapping


HYBRID_OUTPUT_CONTRACT_PROFILE_VERSION = "lin_tianji_hybrid_output_contract_v1-exp"

COMPOSITION_TYPES = (
    "single_child",
    "direct_convergence_child",
    "parallel_sibling_group",
    "layered_complement_child",
    "divergence_child",
)

_HCC_PROFILE_VERSION = "lin_tianji_hybrid_claim_composer_v1-exp"
_RENDERABLE_DECISIONS = {"render", "render_with_caveat"}
_VISIBILITIES = {"primary", "secondary", "audit_only"}
_SPECIFICITY_ORDER = {"event_family": 0, "concrete_event": 1}
_RELATION_TO_COMPOSITION = {
    "single_system_qualified": "single_child",
    "direct_convergence": "direct_convergence_child",
    "layered_complement": "layered_complement_child",
    "divergence": "divergence_child",
}


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
        raise ValueError("hybrid output contract input must be canonical JSON") from exc


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("%s must be non-empty text" % label)
    return value


def _sha256(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError("%s must be a lowercase SHA-256 digest" % label)
    return value


def _text_list(value: object, label: str, *, allow_empty: bool = True) -> list[str]:
    if not isinstance(value, list):
        raise ValueError("%s must be a list" % label)
    rows = []
    for item in value:
        if not isinstance(item, str) or not item:
            raise ValueError("%s entries must be non-empty text" % label)
        rows.append(item)
    if not allow_empty and not rows:
        raise ValueError("%s must not be empty" % label)
    if len(rows) != len(set(rows)):
        raise ValueError("%s entries must be unique" % label)
    return rows


def _canonical_union(rows: list[list[str]]) -> list[str]:
    result = []
    seen = set()
    for row in rows:
        for item in row:
            if item not in seen:
                seen.add(item)
                result.append(item)
    return result


def _validated_hcc(bundle: Mapping[str, object]) -> dict:
    if not isinstance(bundle, Mapping):
        raise ValueError("hybrid_claim_composer_bundle must be a mapping")
    if bundle.get("profile_version") != _HCC_PROFILE_VERSION:
        raise ValueError("unsupported Hybrid Claim Composer profile")

    target_scope = _text(bundle.get("target_scope"), "HCC target_scope")
    c2_digest = _sha256(
        bundle.get("hierarchical_claim_authority_digest"),
        "HCC hierarchical_claim_authority_digest",
    )
    efa_digest = _sha256(
        bundle.get("event_family_attribution_digest"),
        "HCC event_family_attribution_digest",
    )
    _text(
        bundle.get("source_interpretation_contract_digest"),
        "HCC source_interpretation_contract_digest",
    )
    _text(
        bundle.get("source_claim_evidence_digest"),
        "HCC source_claim_evidence_digest",
    )
    supplied_digest = _sha256(
        bundle.get("hybrid_claim_composer_digest"),
        "HCC hybrid_claim_composer_digest",
    )
    body = dict(bundle)
    body.pop("hybrid_claim_composer_digest", None)
    if _digest(body) != supplied_digest:
        raise ValueError("Hybrid Claim Composer digest does not match payload")

    raw_children = bundle.get("children")
    if not isinstance(raw_children, list):
        raise ValueError("HCC children must be a list")

    children = []
    by_id = {}
    renderable_ids = set()
    audit_ids = set()
    for raw in raw_children:
        if not isinstance(raw, Mapping):
            raise ValueError("HCC child entries must be mappings")
        child_id = _text(raw.get("child_claim_id"), "HCC child_claim_id")
        if child_id in by_id:
            raise ValueError("HCC child ids must be unique")
        parent_id = _text(raw.get("parent_claim_id"), "HCC parent_claim_id")
        domain = _text(raw.get("primary_domain"), "HCC primary_domain")
        family = _text(raw.get("event_family"), "HCC event_family")
        decision = raw.get("authority_decision")
        visibility = raw.get("visibility")
        if visibility not in _VISIBILITIES:
            raise ValueError("unsupported HCC child visibility")
        caveats = _text_list(raw.get("required_caveats"), "HCC required_caveats")
        source_systems = _text_list(raw.get("source_systems"), "HCC source_systems")
        relation = raw.get("cross_system_relation")
        specificity = raw.get("authorized_specificity")

        if decision in _RENDERABLE_DECISIONS:
            if visibility == "audit_only":
                raise ValueError("renderable HCC child cannot be audit-only")
            if specificity not in _SPECIFICITY_ORDER:
                raise ValueError("renderable HCC child has unsupported specificity")
            if relation not in _RELATION_TO_COMPOSITION:
                raise ValueError("renderable HCC child has unsupported relation")
            renderable_ids.add(child_id)
        elif decision == "abstain_child":
            if visibility != "audit_only":
                raise ValueError("abstained HCC child must be audit-only")
            if specificity is not None:
                raise ValueError("abstained HCC child cannot carry specificity")
            if relation not in (None, "no_direct_target_support"):
                raise ValueError("abstained HCC child has unsupported relation")
            audit_ids.add(child_id)
        else:
            raise ValueError("unsupported HCC child authority decision")

        row = {
            "child_claim_id": child_id,
            "parent_claim_id": parent_id,
            "primary_domain": domain,
            "event_family": family,
            "authority_decision": decision,
            "authorized_specificity": specificity,
            "source_systems": source_systems,
            "cross_system_relation": relation,
            "visibility": visibility,
            "required_caveats": caveats,
        }
        children.append(row)
        by_id[child_id] = row

    raw_groups = bundle.get("composition_groups")
    if not isinstance(raw_groups, list):
        raise ValueError("HCC composition_groups must be a list")
    groups = []
    consumed = set()
    for raw in raw_groups:
        if not isinstance(raw, Mapping):
            raise ValueError("HCC composition group entries must be mappings")
        if raw.get("composition_type") != "parallel_sibling":
            raise ValueError("unsupported HCC composition group type")
        domain = _text(raw.get("primary_domain"), "HCC composition group domain")
        member_ids = _text_list(
            raw.get("member_child_claim_ids"),
            "HCC composition group member ids",
            allow_empty=False,
        )
        if len(member_ids) < 2:
            raise ValueError("parallel sibling group requires at least two members")
        if any(member_id in consumed for member_id in member_ids):
            raise ValueError("HCC child cannot belong to multiple composition groups")
        for member_id in member_ids:
            child = by_id.get(member_id)
            if child is None:
                raise ValueError("HCC composition group references unknown child")
            if member_id not in renderable_ids:
                raise ValueError("HCC composition group cannot reference audit child")
            if child["primary_domain"] != domain:
                raise ValueError("HCC composition group domain must match every member")
        consumed.update(member_ids)
        groups.append(
            {
                "composition_type": "parallel_sibling",
                "primary_domain": domain,
                "member_child_claim_ids": member_ids,
            }
        )

    return {
        "target_scope": target_scope,
        "c2_digest": c2_digest,
        "efa_digest": efa_digest,
        "hcc_digest": supplied_digest,
        "children": children,
        "by_id": by_id,
        "renderable_ids": renderable_ids,
        "audit_ids": audit_ids,
        "groups": groups,
    }


def _render_unit_id(
    *,
    target_scope: str,
    primary_domain: str,
    composition_type: str,
    member_child_claim_ids: list[str],
) -> str:
    identity = {
        "target_scope": target_scope,
        "primary_domain": primary_domain,
        "composition_type": composition_type,
        "member_child_claim_ids": member_child_claim_ids,
    }
    return "render-unit:%s" % _digest(identity)


def _build_unit(
    *,
    source: Mapping[str, object],
    members: list[Mapping[str, object]],
    composition_type: str,
) -> dict:
    domain = members[0]["primary_domain"]
    if any(member["primary_domain"] != domain for member in members):
        raise ValueError("render unit members must share one primary domain")
    visibilities = {member["visibility"] for member in members}
    if len(visibilities) != 1 or "audit_only" in visibilities:
        raise ValueError("render unit members must share ordinary visibility")

    member_ids = [str(member["child_claim_id"]) for member in members]
    specificities = [str(member["authorized_specificity"]) for member in members]
    unit_specificity = min(specificities, key=_SPECIFICITY_ORDER.__getitem__)
    caveats = _canonical_union(
        [list(member["required_caveats"]) for member in members]
    )
    relations = _canonical_union(
        [[str(member["cross_system_relation"])] for member in members]
    )

    return {
        "render_unit_id": _render_unit_id(
            target_scope=str(source["target_scope"]),
            primary_domain=str(domain),
            composition_type=composition_type,
            member_child_claim_ids=member_ids,
        ),
        "member_child_claim_ids": member_ids,
        "primary_domain": domain,
        "target_scope": source["target_scope"],
        "composition_type": composition_type,
        "cross_system_relations": relations,
        "visibility": next(iter(visibilities)),
        "authorized_specificity": unit_specificity,
        "required_caveats": caveats,
        "causality_allowed": False,
        "source_efa_digest": source["efa_digest"],
        "source_c2_digest": source["c2_digest"],
        "source_hcc_digest": source["hcc_digest"],
    }


def build_hybrid_output_contract(
    *,
    hybrid_claim_composer_bundle: Mapping[str, object],
) -> dict:
    """Build a deterministic renderer manifest from one validated HCC bundle."""

    source = _validated_hcc(hybrid_claim_composer_bundle)
    render_units = []
    consumed = set()

    for group in source["groups"]:
        members = [source["by_id"][member_id] for member_id in group["member_child_claim_ids"]]
        render_units.append(
            _build_unit(
                source=source,
                members=members,
                composition_type="parallel_sibling_group",
            )
        )
        consumed.update(group["member_child_claim_ids"])

    for child in source["children"]:
        child_id = child["child_claim_id"]
        if child_id not in source["renderable_ids"] or child_id in consumed:
            continue
        relation = child["cross_system_relation"]
        composition_type = _RELATION_TO_COMPOSITION.get(relation)
        if composition_type is None:
            raise ValueError("renderable child relation has no composition mapping")
        render_units.append(
            _build_unit(
                source=source,
                members=[child],
                composition_type=composition_type,
            )
        )
        consumed.add(child_id)

    if consumed != source["renderable_ids"]:
        raise ValueError("every renderable HCC child must be consumed exactly once")

    ordinary_children = [
        dict(child)
        for child in source["children"]
        if child["child_claim_id"] in source["renderable_ids"]
    ]
    audit_only_children = [
        dict(child)
        for child in source["children"]
        if child["child_claim_id"] in source["audit_ids"]
    ]

    result = {
        "profile_version": HYBRID_OUTPUT_CONTRACT_PROFILE_VERSION,
        "target_scope": source["target_scope"],
        "source_hybrid_claim_composer_digest": source["hcc_digest"],
        "render_units": render_units,
        "children": ordinary_children,
        "audit_only_children": audit_only_children,
    }
    result["hybrid_output_contract_digest"] = _digest(result)
    return result
