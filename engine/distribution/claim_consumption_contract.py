"""Deterministic downstream claim-consumption authority for v1.6 research.

This module consumes immutable Claim Evidence and Coordination bundles. It
never reranks evidence, creates claims, rewrites event-family candidates, or
raises confidence/specificity. Its only authority is whether an existing
claim may be rendered, rendered with a caveat, or abstained.
"""

from __future__ import annotations

import hashlib
import json
from typing import Mapping


CLAIM_CONSUMPTION_PROFILE_VERSION = "lin_tianji_claim_consumption_v1-exp"

_ALLOWED_RELATIONS = {
    "direct_domain_convergence",
    "layered_complement",
    "parallel_signals",
    "parallel_context",
    "single_system_support",
}
_SPECIFICITY_ORDER = {
    "domain": 0,
    "event_family": 1,
    "concrete_event": 2,
    "highly_specific_event": 3,
}
_LIMITING_ABSTENTIONS = {
    "abstain_event_family",
    "abstain_timing",
    "abstain_concrete_event",
}
_REASON_ORDER = (
    "single_system_support",
    "parallel_context",
    "parallel_signals",
    "layered_complement",
    "specificity_downgraded",
    "low_confidence",
    "existing_abstention",
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
        raise ValueError("claim consumption input must be canonical JSON") from exc


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be non-empty text")
    return value


def _source_digest(bundle: Mapping[str, object], field: str, label: str) -> str:
    supplied = _text(bundle.get(field), field)
    payload = dict(bundle)
    payload.pop(field, None)
    actual = _digest(payload)
    if supplied != actual:
        raise ValueError(f"{label} digest does not match payload")
    return supplied


def _specificity(value: object, label: str) -> str:
    if value not in _SPECIFICITY_ORDER:
        raise ValueError(f"{label} contains unsupported specificity")
    return str(value)


def _domain_index(rows: object, label: str) -> dict:
    if not isinstance(rows, list):
        raise ValueError(f"{label} must be a list")
    indexed = {}
    for raw in rows:
        if not isinstance(raw, Mapping):
            raise ValueError(f"{label} entries must be mappings")
        domain = _text(raw.get("primary_domain"), "primary_domain")
        if domain in indexed:
            raise ValueError(f"{label} primary domains must be unique")
        indexed[domain] = raw
    return indexed


def _packet_identity(packet: Mapping[str, object], target_scope: str) -> dict:
    domain = _text(packet.get("primary_domain"), "packet.primary_domain")
    claim_id = _text(packet.get("claim_id"), "packet.claim_id")
    if packet.get("time_scope") != target_scope:
        raise ValueError("packet time_scope must match source target_scope")

    reasoning = packet.get("reasoning_chain")
    if not isinstance(reasoning, Mapping):
        raise ValueError("packet reasoning_chain must be a mapping")
    ranking_digest = _text(
        reasoning.get("phase3_ranking_digest"),
        "packet.reasoning_chain.phase3_ranking_digest",
    )
    structural_digest = _text(
        reasoning.get("structural_interpretation_digest"),
        "packet.reasoning_chain.structural_interpretation_digest",
    )

    confidence = _text(packet.get("confidence_class"), "packet.confidence_class")
    effective = _specificity(
        packet.get("effective_specificity"),
        "packet.effective_specificity",
    )
    abstentions = packet.get("abstention_status")
    if not isinstance(abstentions, list) or any(
        not isinstance(item, str) or not item for item in abstentions
    ):
        raise ValueError("packet abstention_status must be a list of non-empty text")

    return {
        "claim_id": claim_id,
        "primary_domain": domain,
        "ranking_digest": ranking_digest,
        "structural_digest": structural_digest,
        "confidence_class": confidence,
        "effective_specificity": effective,
        "abstention_status": list(abstentions),
    }


def _relation_identity(relation: Mapping[str, object]) -> dict:
    domain = _text(relation.get("primary_domain"), "relation.primary_domain")
    coordination_relation = relation.get("coordination_relation")
    if coordination_relation not in _ALLOWED_RELATIONS:
        raise ValueError("unsupported coordination relation")

    cap = _specificity(
        relation.get("coordination_specificity_cap"),
        "relation.coordination_specificity_cap",
    )
    support_count = relation.get("system_support_count")
    if (
        isinstance(support_count, bool)
        or not isinstance(support_count, int)
        or support_count < 0
    ):
        raise ValueError("system_support_count must be a non-negative integer")
    systems = relation.get("same_scope_target_systems")
    if not isinstance(systems, list) or any(
        item not in {"bazi", "ziwei"} for item in systems
    ):
        raise ValueError("same_scope_target_systems must contain only bazi/ziwei")
    if len(systems) != len(set(systems)):
        raise ValueError("same_scope_target_systems must be unique")
    if support_count != len(systems):
        raise ValueError("system_support_count must match same_scope_target_systems")

    return {
        "primary_domain": domain,
        "coordination_relation": str(coordination_relation),
        "coordination_specificity_cap": cap,
        "system_support_count": support_count,
    }


def _decision_for(
    packet: Mapping[str, object],
    relation: Mapping[str, object],
    *,
    target_scope: str,
    source_ranking_digest: str,
    source_interpretation_digest: str,
) -> dict:
    p = _packet_identity(packet, target_scope)
    r = _relation_identity(relation)
    if p["primary_domain"] != r["primary_domain"]:
        raise ValueError("packet and relation domains must match")
    if p["ranking_digest"] != source_ranking_digest:
        raise ValueError("packet ranking provenance does not match source bundle")
    if p["structural_digest"] != source_interpretation_digest:
        raise ValueError("packet structural provenance does not match source bundle")

    effective = p["effective_specificity"]
    cap = r["coordination_specificity_cap"]
    if _SPECIFICITY_ORDER[cap] > _SPECIFICITY_ORDER[effective]:
        raise ValueError("coordination specificity cap cannot raise packet authority")
    authorized = cap if _SPECIFICITY_ORDER[cap] < _SPECIFICITY_ORDER[effective] else effective

    if r["system_support_count"] == 0:
        decision = "abstain_claim"
        reasons = ["no_same_scope_target_support"]
    else:
        reason_set = set()
        if r["coordination_relation"] in {
            "single_system_support",
            "parallel_context",
            "parallel_signals",
            "layered_complement",
        }:
            reason_set.add(r["coordination_relation"])
        if authorized != effective:
            reason_set.add("specificity_downgraded")
        if p["confidence_class"] == "low_confidence":
            reason_set.add("low_confidence")
        if _LIMITING_ABSTENTIONS.intersection(p["abstention_status"]):
            reason_set.add("existing_abstention")
        reasons = [item for item in _REASON_ORDER if item in reason_set]
        decision = "render_with_caveat" if reasons else "render"

    return {
        "claim_id": p["claim_id"],
        "primary_domain": p["primary_domain"],
        "decision": decision,
        "original_effective_specificity": effective,
        "authorized_specificity": authorized,
        "confidence_class": p["confidence_class"],
        "coordination_relation": r["coordination_relation"],
        "reason_codes": reasons,
    }


def build_claim_consumption_bundle(
    *,
    claim_evidence_bundle: Mapping[str, object],
    coordination_bundle: Mapping[str, object],
) -> dict:
    """Build a deterministic render-authorization bundle from frozen sources."""

    if not isinstance(claim_evidence_bundle, Mapping):
        raise ValueError("claim_evidence_bundle must be a mapping")
    if not isinstance(coordination_bundle, Mapping):
        raise ValueError("coordination_bundle must be a mapping")

    claim_digest = _source_digest(
        claim_evidence_bundle,
        "claim_evidence_digest",
        "claim evidence",
    )
    coordination_digest = _source_digest(
        coordination_bundle,
        "coordination_digest",
        "coordination",
    )

    target_scope = _text(claim_evidence_bundle.get("target_scope"), "target_scope")
    if coordination_bundle.get("target_scope") != target_scope:
        raise ValueError("claim and coordination target scopes must match")

    claim_ranking_digest = _text(
        claim_evidence_bundle.get("base_ranking_digest"),
        "base_ranking_digest",
    )
    coordination_ranking_digest = _text(
        coordination_bundle.get("source_ranking_digest"),
        "source_ranking_digest",
    )
    if claim_ranking_digest != coordination_ranking_digest:
        raise ValueError("claim and coordination ranking provenance must match")

    claim_structural_digest = _text(
        claim_evidence_bundle.get("structural_interpretation_digest"),
        "structural_interpretation_digest",
    )
    coordination_structural_digest = _text(
        coordination_bundle.get("source_interpretation_digest"),
        "source_interpretation_digest",
    )
    if claim_structural_digest != coordination_structural_digest:
        raise ValueError("claim and coordination structural provenance must match")

    packets = _domain_index(claim_evidence_bundle.get("packets"), "packets")
    relations = _domain_index(coordination_bundle.get("relations"), "relations")
    if set(packets) != set(relations):
        raise ValueError("claim packet and coordination domain sets must match")

    decisions = [
        _decision_for(
            packets[domain],
            relations[domain],
            target_scope=target_scope,
            source_ranking_digest=claim_ranking_digest,
            source_interpretation_digest=claim_structural_digest,
        )
        for domain in sorted(packets)
    ]

    result = {
        "profile_version": CLAIM_CONSUMPTION_PROFILE_VERSION,
        "claim_evidence_digest": claim_digest,
        "coordination_digest": coordination_digest,
        "target_scope": target_scope,
        "decisions": decisions,
    }
    result["claim_consumption_digest"] = _digest(result)
    return result
