"""Deterministic Legacy child-level projection for paired v1.6 research.

This adapter projects frozen Interpretation v2 / C1 / Coordination parent
claims onto the existing event-family candidate universe.  It intentionally
preserves legacy breadth and never reads outcomes, oracle data, or renderer
prose.
"""

from __future__ import annotations

import hashlib
import json
from typing import Mapping

from .interpretation_contract_v2 import INTERPRETATION_PROFILE_VERSION_V2


EVENT_FAMILY_LEGACY_ADAPTER_PROFILE_VERSION = (
    "lin_tianji_event_family_legacy_adapter_v1-exp"
)

LEGACY_RELATION_PROJECTIONS = {
    "direct_domain_convergence": "direct_convergence_projection",
    "layered_complement": "layered_complement_projection",
    "single_system_support": "single_system_projection",
    "parallel_context": "parallel_context_projection",
    "parallel_signals": "parallel_signals_projection",
}

_SPECIFICITY_ORDER = {
    "domain": 0,
    "event_family": 1,
    "concrete_event": 2,
    "highly_specific_event": 3,
}
_PARENT_DECISIONS = {"render", "render_with_caveat", "abstain_claim"}


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
        raise ValueError("legacy adapter input must be canonical JSON") from exc


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be non-empty text")
    return value


def _child_claim_id(target_scope: str, primary_domain: str, event_family: str) -> str:
    safe = all(
        ":" not in item and "\n" not in item and "\r" not in item
        for item in (primary_domain, event_family)
    )
    if safe:
        return "child:%s:%s:%s" % (target_scope, primary_domain, event_family)
    token = _digest(
        {
            "target_scope": target_scope,
            "primary_domain": primary_domain,
            "event_family": event_family,
        }
    )[:16]
    return "child:%s:%s" % (target_scope, token)


def _validated_source(value: object) -> dict:
    if not isinstance(value, Mapping):
        raise ValueError("interpretation_contract_v2 must be a mapping")
    if value.get("profile_version") != INTERPRETATION_PROFILE_VERSION_V2:
        raise ValueError("unsupported Interpretation v2 profile")

    source_digest = _text(
        value.get("interpretation_contract_digest"),
        "interpretation_contract_digest",
    )
    if len(source_digest) != 64:
        raise ValueError("interpretation_contract_digest must be a SHA-256 digest")
    source_body = dict(value)
    source_body.pop("interpretation_contract_digest", None)
    if _digest(source_body) != source_digest:
        raise ValueError("Interpretation v2 digest does not match payload")

    target_scope = _text(value.get("target_scope"), "target_scope")
    domains = value.get("domain_interpretation")
    decisions = value.get("claim_consumption_decisions")
    relations = value.get("coordination_relations")
    if not isinstance(domains, list):
        raise ValueError("domain_interpretation must be a list")
    if not isinstance(decisions, list):
        raise ValueError("claim_consumption_decisions must be a list")
    if not isinstance(relations, list):
        raise ValueError("coordination_relations must be a list")

    domain_rows = []
    domain_index = {}
    for raw in domains:
        if not isinstance(raw, Mapping):
            raise ValueError("domain_interpretation rows must be mappings")
        domain = _text(raw.get("primary_domain"), "primary_domain")
        if domain in domain_index:
            raise ValueError("domain_interpretation domains must be unique")
        candidates = raw.get("event_family_candidates")
        if not isinstance(candidates, list):
            raise ValueError("event_family_candidates must be a list")
        normalized_candidates = []
        seen_candidates = set()
        for raw_family in candidates:
            family = _text(raw_family, "event_family")
            if family in seen_candidates:
                raise ValueError("event_family_candidates must be unique within domain")
            seen_candidates.add(family)
            normalized_candidates.append(family)
        row = {
            "primary_domain": domain,
            "event_family_candidates": normalized_candidates,
        }
        domain_rows.append(row)
        domain_index[domain] = row

    decision_index = {}
    for raw in decisions:
        if not isinstance(raw, Mapping):
            raise ValueError("claim_consumption_decisions rows must be mappings")
        domain = _text(raw.get("primary_domain"), "decision.primary_domain")
        if domain in decision_index:
            raise ValueError("claim_consumption_decisions domains must be unique")
        claim_id = _text(raw.get("claim_id"), "claim_id")
        decision = raw.get("decision")
        if decision not in _PARENT_DECISIONS:
            raise ValueError("unsupported parent claim-consumption decision")
        specificity = raw.get("authorized_specificity")
        if specificity not in _SPECIFICITY_ORDER:
            raise ValueError("unsupported parent authorized specificity")
        decision_index[domain] = {
            "claim_id": claim_id,
            "decision": str(decision),
            "authorized_specificity": str(specificity),
        }

    relation_index = {}
    for raw in relations:
        if not isinstance(raw, Mapping):
            raise ValueError("coordination_relations rows must be mappings")
        domain = _text(raw.get("primary_domain"), "relation.primary_domain")
        if domain in relation_index:
            raise ValueError("coordination_relations domains must be unique")
        relation = raw.get("coordination_relation")
        if relation not in LEGACY_RELATION_PROJECTIONS:
            raise ValueError("unsupported legacy coordination relation")
        relation_index[domain] = str(relation)

    domain_set = set(domain_index)
    if set(decision_index) != domain_set or set(relation_index) != domain_set:
        raise ValueError(
            "domain_interpretation, claim_consumption_decisions, and coordination_relations domains must match"
        )

    return {
        "target_scope": target_scope,
        "source_digest": source_digest,
        "domains": domain_rows,
        "decisions": decision_index,
        "relations": relation_index,
    }


def build_event_family_legacy_adapter_bundle(
    *,
    interpretation_contract_v2: Mapping[str, object],
) -> dict:
    """Project frozen legacy parent authority onto all existing child candidates."""

    source = _validated_source(interpretation_contract_v2)
    target_scope = source["target_scope"]
    children = []

    for domain_row in source["domains"]:
        domain = domain_row["primary_domain"]
        parent = source["decisions"][domain]
        source_relation = source["relations"][domain]
        parent_decision = parent["decision"]
        parent_specificity = parent["authorized_specificity"]

        if parent_decision == "abstain_claim" or parent_specificity == "domain":
            child_decision = "abstain_child"
            child_specificity = None
        else:
            child_decision = parent_decision
            child_specificity = parent_specificity

        for family in domain_row["event_family_candidates"]:
            children.append(
                {
                    "child_claim_id": _child_claim_id(target_scope, domain, family),
                    "parent_claim_id": parent["claim_id"],
                    "primary_domain": domain,
                    "event_family": family,
                    "decision": child_decision,
                    "authorized_specificity": child_specificity,
                    "caveat_required": parent_decision == "render_with_caveat",
                    "projected_cross_system_relation": LEGACY_RELATION_PROJECTIONS[
                        source_relation
                    ],
                    "source_parent_decision": parent_decision,
                    "source_coordination_relation": source_relation,
                }
            )

    result = {
        "profile_version": EVENT_FAMILY_LEGACY_ADAPTER_PROFILE_VERSION,
        "target_scope": target_scope,
        "source_interpretation_contract_digest": source["source_digest"],
        "children": children,
    }
    result["legacy_adapter_digest"] = _digest(result)
    return result
