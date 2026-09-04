"""Deterministic child-level claim authority for v1.6 Hybrid accuracy research.

C2 is strictly downstream of frozen Claim Consumption (C1) and frozen
Event-Family Attribution (EFA).  Claim Evidence is accepted only as an
identity bridge that binds both sources back to the same immutable Phase 3
and Structural Interpretation provenance.  C2 never creates children,
reranks evidence, or raises specificity.
"""

from __future__ import annotations

import hashlib
import json
from typing import Mapping


HIERARCHICAL_CLAIM_AUTHORITY_PROFILE_VERSION = (
    "lin_tianji_hierarchical_claim_authority_v1-exp"
)

C2_REASON_ORDER = (
    "parent_requires_caveat",
    "single_system_support",
    "needs_verification",
    "experimental_only",
    "specificity_downgraded",
)

_ABSTENTION_PRECEDENCE = (
    "parent_abstained",
    "no_direct_target_support",
    "parent_specificity_below_event_family",
)

_SPECIFICITY_ORDER = {
    "domain": 0,
    "event_family": 1,
    "concrete_event": 2,
    "highly_specific_event": 3,
}
_FAMILY_SPECIFICITIES = {"event_family", "concrete_event"}
_PARENT_DECISIONS = {"render", "render_with_caveat", "abstain_claim"}
_SYSTEMS = ("bazi", "ziwei")


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
        raise ValueError("hierarchical claim authority input must be canonical JSON") from exc


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("%s must be non-empty text" % label)
    return value


def _validated_digest(bundle: Mapping[str, object], field: str, label: str) -> str:
    supplied = bundle.get(field)
    if not isinstance(supplied, str) or len(supplied) != 64:
        raise ValueError("%s must include SHA-256-shaped %s" % (label, field))
    body = dict(bundle)
    body.pop(field, None)
    actual = _digest(body)
    if supplied != actual:
        raise ValueError("%s digest does not match payload" % label)
    return supplied


def _specificity(value: object, label: str) -> str:
    if value not in _SPECIFICITY_ORDER:
        raise ValueError("%s contains unsupported specificity" % label)
    return str(value)


def _text_list(value: object, label: str, *, allowed=None) -> list[str]:
    if not isinstance(value, list):
        raise ValueError("%s must be a list" % label)
    rows = []
    for item in value:
        if not isinstance(item, str) or not item:
            raise ValueError("%s entries must be non-empty text" % label)
        if allowed is not None and item not in allowed:
            raise ValueError("%s contains unsupported value" % label)
        rows.append(item)
    if len(rows) != len(set(rows)):
        raise ValueError("%s entries must be unique" % label)
    return rows


def _claim_evidence_identity(bundle: Mapping[str, object]) -> dict:
    digest = _validated_digest(bundle, "claim_evidence_digest", "claim evidence")
    target_scope = _text(bundle.get("target_scope"), "claim_evidence.target_scope")
    ranking_digest = _text(
        bundle.get("base_ranking_digest"), "claim_evidence.base_ranking_digest"
    )
    structural_digest = _text(
        bundle.get("structural_interpretation_digest"),
        "claim_evidence.structural_interpretation_digest",
    )
    packets = bundle.get("packets")
    if not isinstance(packets, list):
        raise ValueError("claim_evidence.packets must be a list")

    by_claim = {}
    by_domain = {}
    for raw in packets:
        if not isinstance(raw, Mapping):
            raise ValueError("claim_evidence packet entries must be mappings")
        claim_id = _text(raw.get("claim_id"), "packet.claim_id")
        domain = _text(raw.get("primary_domain"), "packet.primary_domain")
        if raw.get("time_scope") != target_scope:
            raise ValueError("claim evidence packet scope must match target_scope")
        if claim_id in by_claim or domain in by_domain:
            raise ValueError("claim evidence parent claims and domains must be unique")
        families = _text_list(raw.get("event_family_candidates"), "packet.event_family_candidates")
        reasoning = raw.get("reasoning_chain")
        if not isinstance(reasoning, Mapping):
            raise ValueError("packet.reasoning_chain must be a mapping")
        if reasoning.get("phase3_ranking_digest") != ranking_digest:
            raise ValueError("claim evidence packet ranking provenance mismatch")
        if reasoning.get("structural_interpretation_digest") != structural_digest:
            raise ValueError("claim evidence packet structural provenance mismatch")
        row = {
            "claim_id": claim_id,
            "primary_domain": domain,
            "event_family_candidates": families,
        }
        by_claim[claim_id] = row
        by_domain[domain] = row

    return {
        "digest": digest,
        "target_scope": target_scope,
        "ranking_digest": ranking_digest,
        "structural_digest": structural_digest,
        "by_claim": by_claim,
        "by_domain": by_domain,
    }


def _c1_identity(bundle: Mapping[str, object], claim_identity: Mapping[str, object]) -> dict:
    digest = _validated_digest(bundle, "claim_consumption_digest", "claim consumption")
    target_scope = _text(bundle.get("target_scope"), "claim_consumption.target_scope")
    if target_scope != claim_identity["target_scope"]:
        raise ValueError("C1 and Claim Evidence target scopes must match")
    if bundle.get("claim_evidence_digest") != claim_identity["digest"]:
        raise ValueError("C1 source Claim Evidence digest mismatch")

    decisions = bundle.get("decisions")
    if not isinstance(decisions, list):
        raise ValueError("claim_consumption.decisions must be a list")
    by_claim = {}
    by_domain = {}
    for raw in decisions:
        if not isinstance(raw, Mapping):
            raise ValueError("C1 decision entries must be mappings")
        claim_id = _text(raw.get("claim_id"), "C1.claim_id")
        domain = _text(raw.get("primary_domain"), "C1.primary_domain")
        if claim_id in by_claim or domain in by_domain:
            raise ValueError("C1 parent claims and domains must be unique")
        evidence_parent = claim_identity["by_claim"].get(claim_id)
        if evidence_parent is None or evidence_parent["primary_domain"] != domain:
            raise ValueError("C1 parent identity does not match Claim Evidence")
        decision = raw.get("decision")
        if decision not in _PARENT_DECISIONS:
            raise ValueError("C1 contains unsupported parent decision")
        authorized = raw.get("authorized_specificity")
        if decision == "abstain_claim":
            if authorized is not None:
                authorized = _specificity(authorized, "C1.authorized_specificity")
        else:
            authorized = _specificity(authorized, "C1.authorized_specificity")
        row = {
            "claim_id": claim_id,
            "primary_domain": domain,
            "decision": str(decision),
            "authorized_specificity": authorized,
        }
        by_claim[claim_id] = row
        by_domain[domain] = row

    if set(by_claim) != set(claim_identity["by_claim"]):
        raise ValueError("C1 parent claim set must equal Claim Evidence claim set")
    return {"digest": digest, "by_claim": by_claim}


def _efa_identity(bundle: Mapping[str, object], claim_identity: Mapping[str, object]) -> dict:
    digest = _validated_digest(
        bundle, "event_family_attribution_digest", "event-family attribution"
    )
    target_scope = _text(bundle.get("target_scope"), "EFA.target_scope")
    if target_scope != claim_identity["target_scope"]:
        raise ValueError("EFA and Claim Evidence target scopes must match")
    if bundle.get("base_ranking_digest") != claim_identity["ranking_digest"]:
        raise ValueError("EFA ranking provenance does not match Claim Evidence")
    if bundle.get("structural_interpretation_digest") != claim_identity["structural_digest"]:
        raise ValueError("EFA structural provenance does not match Claim Evidence")

    children = bundle.get("children")
    if not isinstance(children, list):
        raise ValueError("EFA.children must be a list")
    seen_child_ids = set()
    seen_domain_family = set()
    normalized = []
    observed_families = {domain: [] for domain in claim_identity["by_domain"]}

    for raw in children:
        if not isinstance(raw, Mapping):
            raise ValueError("EFA child entries must be mappings")
        child_id = _text(raw.get("child_claim_id"), "EFA.child_claim_id")
        parent_id = _text(raw.get("parent_claim_id"), "EFA.parent_claim_id")
        domain = _text(raw.get("primary_domain"), "EFA.primary_domain")
        family = _text(raw.get("event_family"), "EFA.event_family")
        if child_id in seen_child_ids or (domain, family) in seen_domain_family:
            raise ValueError("EFA child identities must be unique")
        seen_child_ids.add(child_id)
        seen_domain_family.add((domain, family))

        parent = claim_identity["by_claim"].get(parent_id)
        if parent is None or parent["primary_domain"] != domain:
            raise ValueError("EFA parent claim identity does not match Claim Evidence")
        if raw.get("target_scope") != target_scope:
            raise ValueError("EFA child scope must match target_scope")
        if raw.get("source_ranking_digest") != claim_identity["ranking_digest"]:
            raise ValueError("EFA child ranking provenance mismatch")
        if raw.get("source_structural_interpretation_digest") != claim_identity["structural_digest"]:
            raise ValueError("EFA child structural provenance mismatch")

        child_opened = raw.get("child_opened")
        if not isinstance(child_opened, bool):
            raise ValueError("EFA.child_opened must be boolean")
        systems = _text_list(
            raw.get("direct_target_systems"),
            "EFA.direct_target_systems",
            allowed=set(_SYSTEMS),
        )
        if systems != sorted(systems, key=_SYSTEMS.index):
            raise ValueError("EFA direct target systems must use canonical order")
        qualifications = _text_list(
            raw.get("qualification_summary"), "EFA.qualification_summary"
        )
        maturities = _text_list(raw.get("maturity_summary"), "EFA.maturity_summary")
        ceiling = raw.get("family_specificity_ceiling")
        if child_opened:
            if ceiling not in _FAMILY_SPECIFICITIES:
                raise ValueError("opened EFA child must have supported family specificity ceiling")
            if not systems:
                raise ValueError("opened EFA child must have direct target system support")
        else:
            if ceiling is not None or systems:
                raise ValueError("closed EFA child cannot carry direct target authority")

        observed_families[domain].append(family)
        normalized.append(
            {
                "child_claim_id": child_id,
                "parent_claim_id": parent_id,
                "primary_domain": domain,
                "event_family": family,
                "child_opened": child_opened,
                "direct_target_systems": systems,
                "qualification_summary": qualifications,
                "maturity_summary": maturities,
                "family_specificity_ceiling": ceiling,
            }
        )

    for domain, parent in claim_identity["by_domain"].items():
        if observed_families.get(domain, []) != parent["event_family_candidates"]:
            raise ValueError("EFA child universe/order must equal Claim Evidence event-family candidates")

    return {"digest": digest, "children": normalized}


def _decision_for(child: Mapping[str, object], parent: Mapping[str, object]) -> dict:
    abstention_reason = None
    if parent["decision"] == "abstain_claim":
        abstention_reason = _ABSTENTION_PRECEDENCE[0]
    elif not child["child_opened"]:
        abstention_reason = _ABSTENTION_PRECEDENCE[1]
    else:
        parent_specificity = parent["authorized_specificity"]
        if parent_specificity is None:
            raise ValueError("renderable C1 parent must carry authorized specificity")
        if _SPECIFICITY_ORDER[parent_specificity] < _SPECIFICITY_ORDER["event_family"]:
            abstention_reason = _ABSTENTION_PRECEDENCE[2]

    if abstention_reason is not None:
        return {
            "child_claim_id": child["child_claim_id"],
            "parent_claim_id": child["parent_claim_id"],
            "primary_domain": child["primary_domain"],
            "event_family": child["event_family"],
            "decision": "abstain_child",
            "parent_decision": parent["decision"],
            "parent_authorized_specificity": parent["authorized_specificity"],
            "family_specificity_ceiling": child["family_specificity_ceiling"],
            "authorized_specificity": None,
            "source_systems": list(child["direct_target_systems"]),
            "reason_codes": [abstention_reason],
        }

    parent_specificity = parent["authorized_specificity"]
    family_ceiling = child["family_specificity_ceiling"]
    if parent_specificity is None or family_ceiling not in _FAMILY_SPECIFICITIES:
        raise ValueError("renderable child must have valid parent and family specificity")
    authorized = min(
        (parent_specificity, family_ceiling),
        key=lambda value: _SPECIFICITY_ORDER[value],
    )

    reason_set = set()
    if parent["decision"] == "render_with_caveat":
        reason_set.add("parent_requires_caveat")
    if len(child["direct_target_systems"]) == 1:
        reason_set.add("single_system_support")
    if "needs_verification" in child["qualification_summary"]:
        reason_set.add("needs_verification")
    if child["maturity_summary"] == ["experimental"]:
        reason_set.add("experimental_only")
    if authorized != family_ceiling:
        reason_set.add("specificity_downgraded")

    reasons = [reason for reason in C2_REASON_ORDER if reason in reason_set]
    return {
        "child_claim_id": child["child_claim_id"],
        "parent_claim_id": child["parent_claim_id"],
        "primary_domain": child["primary_domain"],
        "event_family": child["event_family"],
        "decision": "render_with_caveat" if reasons else "render",
        "parent_decision": parent["decision"],
        "parent_authorized_specificity": parent_specificity,
        "family_specificity_ceiling": family_ceiling,
        "authorized_specificity": authorized,
        "source_systems": list(child["direct_target_systems"]),
        "reason_codes": reasons,
    }


def build_hierarchical_claim_authority_bundle(
    *,
    claim_consumption_bundle: Mapping[str, object],
    event_family_attribution_bundle: Mapping[str, object],
    claim_evidence_bundle: Mapping[str, object],
) -> dict:
    """Compose frozen parent and child authority without reopening upstream truth."""

    if not isinstance(claim_consumption_bundle, Mapping):
        raise ValueError("claim_consumption_bundle must be a mapping")
    if not isinstance(event_family_attribution_bundle, Mapping):
        raise ValueError("event_family_attribution_bundle must be a mapping")
    if not isinstance(claim_evidence_bundle, Mapping):
        raise ValueError("claim_evidence_bundle must be a mapping")

    claim_identity = _claim_evidence_identity(claim_evidence_bundle)
    c1 = _c1_identity(claim_consumption_bundle, claim_identity)
    efa = _efa_identity(event_family_attribution_bundle, claim_identity)

    decisions = []
    for child in efa["children"]:
        parent = c1["by_claim"].get(child["parent_claim_id"])
        if parent is None:
            raise ValueError("every EFA child must have exactly one C1 parent")
        decisions.append(_decision_for(child, parent))

    result = {
        "profile_version": HIERARCHICAL_CLAIM_AUTHORITY_PROFILE_VERSION,
        "target_scope": claim_identity["target_scope"],
        "claim_evidence_digest": claim_identity["digest"],
        "claim_consumption_digest": c1["digest"],
        "event_family_attribution_digest": efa["digest"],
        "decisions": decisions,
    }
    result["hierarchical_claim_authority_digest"] = _digest(result)
    return result
