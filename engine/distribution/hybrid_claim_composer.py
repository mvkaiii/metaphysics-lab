"""Deterministic Hybrid Claim Composer for v1.6 accuracy research.

HCC is a composition layer only. It consumes frozen C2 child authority,
frozen EFA provenance, the existing Interpretation presentation contract,
and Claim Evidence source/conflict provenance. It never creates children,
reranks domains or families, or reopens an abstained child.
"""

from __future__ import annotations

import hashlib
import json
from typing import Mapping


HYBRID_CLAIM_COMPOSER_PROFILE_VERSION = "lin_tianji_hybrid_claim_composer_v1-exp"

_SYSTEM_ORDER = ("bazi", "ziwei")
_RELATIONS = {
    "divergence",
    "direct_convergence",
    "layered_complement",
    "single_system_qualified",
    "no_direct_target_support",
}
_VISIBILITIES = {"primary", "secondary", "audit_only"}
_AUTHORITY_DECISIONS = {"render", "render_with_caveat", "abstain_child"}


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
        raise ValueError("hybrid claim composer input must be canonical JSON") from exc


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("%s must be non-empty text" % label)
    return value


def _validated_digest(bundle: Mapping[str, object], field: str, label: str) -> str:
    supplied = bundle.get(field)
    if (
        not isinstance(supplied, str)
        or len(supplied) != 64
        or any(character not in "0123456789abcdef" for character in supplied)
    ):
        raise ValueError("%s must include lowercase SHA-256 %s" % (label, field))
    body = dict(bundle)
    body.pop(field, None)
    actual = _digest(body)
    if supplied != actual:
        raise ValueError("%s digest does not match payload" % label)
    return supplied


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
    by_domain = {}
    feature_system = {}
    for packet in packets:
        if not isinstance(packet, Mapping):
            raise ValueError("claim evidence packet entries must be mappings")
        domain = _text(packet.get("primary_domain"), "claim packet primary_domain")
        claim_id = _text(packet.get("claim_id"), "claim packet claim_id")
        if domain in by_domain:
            raise ValueError("claim evidence packet domains must be unique")
        if packet.get("time_scope") != target_scope:
            raise ValueError("claim packet scope must match target_scope")
        families = _text_list(
            packet.get("event_family_candidates"), "claim packet event_family_candidates"
        )

        for system, field in (("bazi", "bazi_evidence"), ("ziwei", "ziwei_evidence")):
            rows = packet.get(field)
            if not isinstance(rows, list):
                raise ValueError("%s must be a list" % field)
            for row in rows:
                if not isinstance(row, Mapping):
                    raise ValueError("%s entries must be mappings" % field)
                feature_id = _text(row.get("feature_id"), "%s.feature_id" % field)
                declared_system = row.get("system")
                if declared_system != system:
                    raise ValueError("claim evidence feature system does not match evidence lane")
                previous = feature_system.get(feature_id)
                if previous is not None and previous != system:
                    raise ValueError("claim evidence feature id cannot belong to two systems")
                feature_system[feature_id] = system
        by_domain[domain] = {
            "claim_id": claim_id,
            "event_family_candidates": families,
        }

    conflicts = bundle.get("global_conflicts", [])
    if not isinstance(conflicts, list):
        raise ValueError("claim_evidence.global_conflicts must be a list")
    normalized_conflicts = []
    for raw in conflicts:
        if not isinstance(raw, Mapping):
            raise ValueError("global conflict entries must be mappings")
        reason = _text(raw.get("reason"), "global conflict reason")
        if reason != "disjoint_target_domain_sets":
            raise ValueError("unsupported global conflict reason")
        bazi_domains = _text_list(raw.get("bazi_target_domains"), "bazi_target_domains")
        ziwei_domains = _text_list(raw.get("ziwei_target_domains"), "ziwei_target_domains")
        normalized_conflicts.append(
            {
                "reason": reason,
                "bazi_target_domains": bazi_domains,
                "ziwei_target_domains": ziwei_domains,
            }
        )

    return {
        "digest": digest,
        "target_scope": target_scope,
        "ranking_digest": ranking_digest,
        "structural_digest": structural_digest,
        "by_domain": by_domain,
        "feature_system": feature_system,
        "global_conflicts": normalized_conflicts,
    }


def _efa_identity(bundle: Mapping[str, object], claim: Mapping[str, object]) -> dict:
    digest = _validated_digest(
        bundle, "event_family_attribution_digest", "event-family attribution"
    )
    if bundle.get("target_scope") != claim["target_scope"]:
        raise ValueError("EFA target scope must match Claim Evidence")
    if bundle.get("base_ranking_digest") != claim["ranking_digest"]:
        raise ValueError("EFA ranking provenance must match Claim Evidence")
    if bundle.get("structural_interpretation_digest") != claim["structural_digest"]:
        raise ValueError("EFA structural provenance must match Claim Evidence")

    children = bundle.get("children")
    if not isinstance(children, list):
        raise ValueError("EFA.children must be a list")
    by_id = {}
    by_domain = {}
    for raw in children:
        if not isinstance(raw, Mapping):
            raise ValueError("EFA child entries must be mappings")
        child_id = _text(raw.get("child_claim_id"), "EFA child_claim_id")
        parent_id = _text(raw.get("parent_claim_id"), "EFA parent_claim_id")
        domain = _text(raw.get("primary_domain"), "EFA primary_domain")
        family = _text(raw.get("event_family"), "EFA event_family")
        if child_id in by_id:
            raise ValueError("EFA child ids must be unique")
        parent = claim["by_domain"].get(domain)
        if parent is None or parent["claim_id"] != parent_id:
            raise ValueError("EFA parent identity must match Claim Evidence")
        if family not in parent["event_family_candidates"]:
            raise ValueError("EFA child family must exist in Claim Evidence candidate set")
        if raw.get("target_scope") != claim["target_scope"]:
            raise ValueError("EFA child scope must match source scope")
        if raw.get("source_ranking_digest") != claim["ranking_digest"]:
            raise ValueError("EFA child ranking provenance mismatch")
        if raw.get("source_structural_interpretation_digest") != claim["structural_digest"]:
            raise ValueError("EFA child structural provenance mismatch")
        systems = _text_list(
            raw.get("direct_target_systems"),
            "EFA direct_target_systems",
            allowed=set(_SYSTEM_ORDER),
        )
        if systems != sorted(systems, key=_SYSTEM_ORDER.index):
            raise ValueError("EFA direct_target_systems must be canonical")
        modifier_ids = _text_list(raw.get("modifier_feature_ids"), "EFA modifier_feature_ids")
        timing_ids = _text_list(
            raw.get("timing_trigger_feature_ids"), "EFA timing_trigger_feature_ids"
        )
        row = {
            "child_claim_id": child_id,
            "parent_claim_id": parent_id,
            "primary_domain": domain,
            "event_family": family,
            "direct_target_systems": systems,
            "modifier_feature_ids": modifier_ids,
            "timing_trigger_feature_ids": timing_ids,
        }
        by_id[child_id] = row
        by_domain.setdefault(domain, {})[family] = row

    for domain, parent in claim["by_domain"].items():
        observed = set(by_domain.get(domain, {}))
        if observed != set(parent["event_family_candidates"]):
            raise ValueError("EFA child family set must equal Claim Evidence candidate set")
    return {"digest": digest, "by_id": by_id, "by_domain": by_domain}


def _authority_identity(bundle: Mapping[str, object], claim: Mapping[str, object], efa: Mapping[str, object]) -> dict:
    digest = _validated_digest(
        bundle, "hierarchical_claim_authority_digest", "hierarchical claim authority"
    )
    if bundle.get("target_scope") != claim["target_scope"]:
        raise ValueError("C2 target scope must match Claim Evidence")
    if bundle.get("claim_evidence_digest") != claim["digest"]:
        raise ValueError("C2 Claim Evidence source digest mismatch")
    if bundle.get("event_family_attribution_digest") != efa["digest"]:
        raise ValueError("C2 EFA source digest mismatch")
    decisions = bundle.get("decisions")
    if not isinstance(decisions, list):
        raise ValueError("C2 decisions must be a list")
    by_id = {}
    for raw in decisions:
        if not isinstance(raw, Mapping):
            raise ValueError("C2 decision entries must be mappings")
        child_id = _text(raw.get("child_claim_id"), "C2 child_claim_id")
        if child_id in by_id:
            raise ValueError("C2 child decisions must be unique")
        source = efa["by_id"].get(child_id)
        if source is None:
            raise ValueError("C2 cannot contain a child absent from EFA")
        for field in ("parent_claim_id", "primary_domain", "event_family"):
            if raw.get(field) != source[field]:
                raise ValueError("C2 child identity must match EFA")
        decision = raw.get("decision")
        if decision not in _AUTHORITY_DECISIONS:
            raise ValueError("unsupported C2 authority decision")
        reason_codes = _text_list(raw.get("reason_codes"), "C2 reason_codes")
        source_systems = _text_list(
            raw.get("source_systems"), "C2 source_systems", allowed=set(_SYSTEM_ORDER)
        )
        if source_systems != source["direct_target_systems"]:
            raise ValueError("C2 source systems must match EFA direct target systems")
        by_id[child_id] = {
            "decision": str(decision),
            "authorized_specificity": raw.get("authorized_specificity"),
            "reason_codes": reason_codes,
        }
    if set(by_id) != set(efa["by_id"]):
        raise ValueError("C2 and EFA child sets must match exactly")
    return {"digest": digest, "by_id": by_id}


def _interpretation_identity(bundle: Mapping[str, object], claim: Mapping[str, object]) -> dict:
    digest = _validated_digest(
        bundle, "interpretation_contract_digest", "interpretation contract"
    )
    if bundle.get("target_scope") != claim["target_scope"]:
        raise ValueError("Interpretation target scope must match Claim Evidence")
    if bundle.get("base_ranking_digest") != claim["ranking_digest"]:
        raise ValueError("Interpretation base ranking must match Claim Evidence")

    primary = _text_list(bundle.get("primary_domains"), "Interpretation primary_domains")
    secondary = _text_list(bundle.get("secondary_domains"), "Interpretation secondary_domains")
    if set(primary).intersection(secondary):
        raise ValueError("Interpretation primary and secondary domains must be disjoint")

    rows = bundle.get("domain_interpretation")
    if not isinstance(rows, list):
        raise ValueError("Interpretation domain_interpretation must be a list")
    by_domain = {}
    ordered_domains = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("Interpretation domain rows must be mappings")
        domain = _text(row.get("primary_domain"), "Interpretation primary_domain")
        if domain in by_domain:
            raise ValueError("Interpretation domains must be unique")
        if domain not in claim["by_domain"]:
            raise ValueError("Interpretation domain must exist in Claim Evidence")
        families = _text_list(
            row.get("event_family_candidates"), "Interpretation event_family_candidates"
        )
        order = _text_list(
            row.get("personalized_event_family_order"),
            "Interpretation personalized_event_family_order",
        )
        if families != claim["by_domain"][domain]["event_family_candidates"]:
            raise ValueError("Interpretation family candidates must equal Claim Evidence order")
        if set(order) != set(families):
            raise ValueError("Interpretation family order must preserve candidate set")
        by_domain[domain] = {"family_order": order}
        ordered_domains.append(domain)

    if set(ordered_domains) != set(primary).union(secondary):
        raise ValueError("Interpretation visibility sets must cover domain rows exactly")
    return {
        "digest": digest,
        "by_domain": by_domain,
        "ordered_domains": ordered_domains,
        "primary": set(primary),
        "secondary": set(secondary),
    }


def _explicit_divergence_domains(conflicts: list[Mapping[str, object]]) -> set[str]:
    domains = set()
    for conflict in conflicts:
        if conflict["reason"] == "disjoint_target_domain_sets":
            domains.update(conflict["bazi_target_domains"])
            domains.update(conflict["ziwei_target_domains"])
    return domains


def _context_systems(child: Mapping[str, object], feature_system: Mapping[str, str]) -> set[str]:
    systems = set()
    for feature_id in child["modifier_feature_ids"] + child["timing_trigger_feature_ids"]:
        system = feature_system.get(feature_id)
        if system is None:
            raise ValueError("EFA context feature id must exist in Claim Evidence")
        systems.add(system)
    return systems


def _relation_for(
    *,
    child: Mapping[str, object],
    divergence_domains: set[str],
    feature_system: Mapping[str, str],
) -> str:
    if child["primary_domain"] in divergence_domains:
        return "divergence"
    systems = set(child["direct_target_systems"])
    if systems == {"bazi", "ziwei"}:
        return "direct_convergence"
    if len(systems) == 1:
        context_systems = _context_systems(child, feature_system)
        direct_system = next(iter(systems))
        other_system = "ziwei" if direct_system == "bazi" else "bazi"
        if other_system in context_systems:
            return "layered_complement"
        return "single_system_qualified"
    if not systems:
        _context_systems(child, feature_system)
        return "no_direct_target_support"
    raise ValueError("unsupported EFA direct target system combination")


def _child_row(
    *,
    child: Mapping[str, object],
    authority: Mapping[str, object],
    visibility: str,
    relation: str,
) -> dict:
    if visibility not in _VISIBILITIES or relation not in _RELATIONS:
        raise AssertionError("unreachable HCC state")
    decision = authority["decision"]
    if decision == "abstain_child":
        visibility = "audit_only"
        required_caveats = []
    else:
        required_caveats = list(authority["reason_codes"])
        if relation == "divergence" and "explicit_divergence" not in required_caveats:
            required_caveats.append("explicit_divergence")
    return {
        "child_claim_id": child["child_claim_id"],
        "parent_claim_id": child["parent_claim_id"],
        "primary_domain": child["primary_domain"],
        "event_family": child["event_family"],
        "authority_decision": decision,
        "authorized_specificity": authority["authorized_specificity"],
        "source_systems": list(child["direct_target_systems"]),
        "cross_system_relation": relation,
        "visibility": visibility,
        "required_caveats": required_caveats,
    }


def _composition_groups(children: list[Mapping[str, object]]) -> list[dict]:
    by_domain = {}
    for row in children:
        if row["authority_decision"] == "abstain_child":
            continue
        if row["cross_system_relation"] != "single_system_qualified":
            continue
        systems = row["source_systems"]
        if len(systems) != 1:
            continue
        by_domain.setdefault(row["primary_domain"], []).append(row)

    groups = []
    for domain, rows in by_domain.items():
        observed = {row["source_systems"][0] for row in rows}
        if observed != {"bazi", "ziwei"}:
            continue
        groups.append(
            {
                "composition_type": "parallel_sibling",
                "primary_domain": domain,
                "member_child_claim_ids": [row["child_claim_id"] for row in rows],
            }
        )
    return groups


def build_hybrid_claim_composer_bundle(
    *,
    hierarchical_authority_bundle: Mapping[str, object],
    event_family_attribution_bundle: Mapping[str, object],
    interpretation_contract: Mapping[str, object],
    claim_evidence_bundle: Mapping[str, object],
) -> dict:
    """Compose child-level Hybrid presentation without changing claim authority."""

    for value, label in (
        (hierarchical_authority_bundle, "hierarchical_authority_bundle"),
        (event_family_attribution_bundle, "event_family_attribution_bundle"),
        (interpretation_contract, "interpretation_contract"),
        (claim_evidence_bundle, "claim_evidence_bundle"),
    ):
        if not isinstance(value, Mapping):
            raise ValueError("%s must be a mapping" % label)

    claim = _claim_evidence_identity(claim_evidence_bundle)
    efa = _efa_identity(event_family_attribution_bundle, claim)
    authority = _authority_identity(hierarchical_authority_bundle, claim, efa)
    interpretation = _interpretation_identity(interpretation_contract, claim)
    divergence_domains = _explicit_divergence_domains(claim["global_conflicts"])

    children = []
    for domain in interpretation["ordered_domains"]:
        domain_visibility = "primary" if domain in interpretation["primary"] else "secondary"
        for family in interpretation["by_domain"][domain]["family_order"]:
            child = efa["by_domain"][domain][family]
            authority_row = authority["by_id"][child["child_claim_id"]]
            relation = _relation_for(
                child=child,
                divergence_domains=divergence_domains,
                feature_system=claim["feature_system"],
            )
            children.append(
                _child_row(
                    child=child,
                    authority=authority_row,
                    visibility=domain_visibility,
                    relation=relation,
                )
            )

    if {row["child_claim_id"] for row in children} != set(efa["by_id"]):
        raise ValueError("Interpretation presentation must cover every EFA child exactly once")

    result = {
        "profile_version": HYBRID_CLAIM_COMPOSER_PROFILE_VERSION,
        "target_scope": claim["target_scope"],
        "hierarchical_claim_authority_digest": authority["digest"],
        "event_family_attribution_digest": efa["digest"],
        "source_interpretation_contract_digest": interpretation["digest"],
        "source_claim_evidence_digest": claim["digest"],
        "children": children,
        "composition_groups": _composition_groups(children),
    }
    result["hybrid_claim_composer_digest"] = _digest(result)
    return result
