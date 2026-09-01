"""Frozen v2 coordination policy selected from general-only research evidence."""

from __future__ import annotations

import hashlib
import json
from typing import Mapping, Sequence


COORDINATION_POLICY_VERSION = "lin_tianji_coordination_v1-exp"
_ALLOWED_SYSTEMS = {"bazi", "ziwei"}
_ALLOWED_ROLES = {"target_evidence", "modifier", "timing_trigger"}
_SPECIFICITY_ORDER = {
    "domain": 0,
    "event_family": 1,
    "concrete_event": 2,
    "highly_specific_event": 3,
}
_REQUIRED_EVIDENCE_FIELDS = {
    "feature_id",
    "system",
    "scope",
    "role",
    "strength_class",
    "maturity",
    "qualification_status",
    "source_family",
    "dependency_family",
    "provenance",
}


def _digest(value: object) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be non-empty text")
    return value


def _validate_digest(value: object, field: str) -> str:
    text = _text(value, field)
    if len(text) != 64:
        raise ValueError(f"{field} must be a sha256 digest")
    try:
        int(text, 16)
    except ValueError as exc:
        raise ValueError(f"{field} must be a sha256 digest") from exc
    return text.lower()


def _evidence_rows(packet: Mapping[str, object]) -> list[dict]:
    rows = []
    for field, expected_system in (("bazi_evidence", "bazi"), ("ziwei_evidence", "ziwei")):
        raw = packet.get(field)
        if not isinstance(raw, list):
            raise ValueError(f"{field} must be a list")
        for item in raw:
            if not isinstance(item, Mapping) or set(item) != _REQUIRED_EVIDENCE_FIELDS:
                raise ValueError("claim evidence row fields do not match coordination schema")
            row = dict(item)
            if row["system"] != expected_system or row["system"] not in _ALLOWED_SYSTEMS:
                raise ValueError("claim evidence row system conflicts with packet evidence family")
            if row["role"] not in _ALLOWED_ROLES:
                raise ValueError("unsupported claim evidence role")
            for key in (
                "feature_id",
                "scope",
                "role",
                "strength_class",
                "maturity",
                "qualification_status",
                "source_family",
                "dependency_family",
            ):
                _text(row[key], key)
            if not isinstance(row["provenance"], Mapping):
                raise ValueError("evidence provenance must be a mapping")
            rows.append(row)
    return sorted(
        rows,
        key=lambda row: (
            row["scope"],
            row["system"],
            row["dependency_family"],
            row["feature_id"],
        ),
    )


def _validated_packet(
    packet: Mapping[str, object],
    *,
    target_scope: str,
    source_ranking_digest: str,
    source_interpretation_digest: str,
) -> dict:
    if not isinstance(packet, Mapping):
        raise ValueError("claim evidence packet must be a mapping")
    domain = _text(packet.get("primary_domain"), "primary_domain")
    if packet.get("time_scope") != target_scope:
        raise ValueError("claim evidence time_scope must match target_scope")
    specificity = packet.get("effective_specificity")
    if specificity not in _SPECIFICITY_ORDER:
        raise ValueError("effective_specificity is invalid")
    base_specificity = packet.get("base_allowed_specificity")
    if base_specificity not in _SPECIFICITY_ORDER:
        raise ValueError("base_allowed_specificity is invalid")
    if _SPECIFICITY_ORDER[specificity] > _SPECIFICITY_ORDER[base_specificity]:
        raise ValueError("effective specificity cannot exceed base specificity")
    reasoning = packet.get("reasoning_chain")
    if not isinstance(reasoning, Mapping):
        raise ValueError("reasoning_chain must be a mapping")
    if reasoning.get("phase3_ranking_digest") != source_ranking_digest:
        raise ValueError("packet phase3 ranking digest mismatch")
    if reasoning.get("structural_interpretation_digest") != source_interpretation_digest:
        raise ValueError("packet structural interpretation digest mismatch")
    rows = _evidence_rows(packet)
    actual_dependency_count = len({row["dependency_family"] for row in rows})
    if packet.get("independent_support_count") != actual_dependency_count:
        raise ValueError("packet independent_support_count does not match evidence")
    return {
        "primary_domain": domain,
        "legacy_cross_system_relation": packet.get("cross_system_relation"),
        "effective_specificity": specificity,
        "evidence": rows,
    }


def _dependency_class(count: int) -> str:
    if count == 0:
        return "no_dependency"
    if count == 1:
        return "single_dependency"
    return "multiple_independent_dependencies"


def _relation_for_packet(
    packet: Mapping[str, object],
    *,
    target_scope: str,
    global_bazi_target_domains: set[str],
    global_ziwei_target_domains: set[str],
) -> str:
    rows = packet["evidence"]
    target_systems = {
        row["system"]
        for row in rows
        if row["role"] == "target_evidence" and row["scope"] == target_scope
    }
    if target_systems == {"bazi", "ziwei"}:
        return "direct_domain_convergence"

    if len(target_systems) == 1:
        target_system = next(iter(target_systems))
        other_system = "ziwei" if target_system == "bazi" else "bazi"
        if any(
            row["system"] == other_system and row["role"] in {"modifier", "timing_trigger"}
            for row in rows
        ):
            return "layered_complement"

    if (
        global_bazi_target_domains
        and global_ziwei_target_domains
        and not (global_bazi_target_domains & global_ziwei_target_domains)
    ):
        return "parallel_signals"

    if target_systems:
        target_system = next(iter(target_systems)) if len(target_systems) == 1 else None
        if target_system is not None:
            other_system = "ziwei" if target_system == "bazi" else "bazi"
            if any(row["system"] == other_system for row in rows):
                return "parallel_context"
        return "single_system_support"

    return "single_system_support"


def build_coordination_bundle(
    *,
    claim_evidence_packets: Sequence[Mapping[str, object]],
    target_scope: str,
    source_ranking_digest: str,
    source_interpretation_digest: str,
    phase3_specificity_by_domain: Mapping[str, str],
) -> dict:
    """Return frozen C coordination audit without rewriting legacy packets."""

    target = _text(target_scope, "target_scope")
    ranking_digest = _validate_digest(source_ranking_digest, "source_ranking_digest")
    interpretation_digest = _validate_digest(source_interpretation_digest, "source_interpretation_digest")
    if isinstance(claim_evidence_packets, (str, bytes)) or not isinstance(claim_evidence_packets, Sequence):
        raise ValueError("claim_evidence_packets must be a sequence")
    if not isinstance(phase3_specificity_by_domain, Mapping):
        raise ValueError("phase3_specificity_by_domain must be a mapping")

    normalized = [
        _validated_packet(
            packet,
            target_scope=target,
            source_ranking_digest=ranking_digest,
            source_interpretation_digest=interpretation_digest,
        )
        for packet in claim_evidence_packets
    ]
    domains = [row["primary_domain"] for row in normalized]
    if len(domains) != len(set(domains)):
        raise ValueError("claim evidence packet domains must be unique")
    normalized.sort(key=lambda row: row["primary_domain"])

    global_bazi_target_domains = {
        row["primary_domain"]
        for row in normalized
        if any(
            evidence["system"] == "bazi"
            and evidence["role"] == "target_evidence"
            and evidence["scope"] == target
            for evidence in row["evidence"]
        )
    }
    global_ziwei_target_domains = {
        row["primary_domain"]
        for row in normalized
        if any(
            evidence["system"] == "ziwei"
            and evidence["role"] == "target_evidence"
            and evidence["scope"] == target
            for evidence in row["evidence"]
        )
    }
    disjoint_target_domains = (
        global_bazi_target_domains
        and global_ziwei_target_domains
        and not (global_bazi_target_domains & global_ziwei_target_domains)
    )
    parallel_domains = sorted(global_bazi_target_domains | global_ziwei_target_domains) if disjoint_target_domains else []

    relations = []
    for packet in normalized:
        domain = packet["primary_domain"]
        phase3_cap = phase3_specificity_by_domain.get(domain)
        if phase3_cap not in _SPECIFICITY_ORDER:
            raise ValueError("phase3 specificity map is incomplete or invalid")
        packet_cap = packet["effective_specificity"]
        coordination_cap = min(
            (phase3_cap, packet_cap),
            key=lambda item: _SPECIFICITY_ORDER[item],
        )
        evidence = packet["evidence"]
        target_systems = sorted({
            row["system"]
            for row in evidence
            if row["role"] == "target_evidence" and row["scope"] == target
        })
        dependencies = {row["dependency_family"] for row in evidence}
        relations.append({
            "primary_domain": domain,
            "legacy_cross_system_relation": packet["legacy_cross_system_relation"],
            "coordination_relation": _relation_for_packet(
                packet,
                target_scope=target,
                global_bazi_target_domains=global_bazi_target_domains,
                global_ziwei_target_domains=global_ziwei_target_domains,
            ),
            "dependency_independence_class": _dependency_class(len(dependencies)),
            "independent_dependency_count": len(dependencies),
            "system_support_count": len(target_systems),
            "same_scope_target_systems": target_systems,
            "parallel_domains": parallel_domains,
            "conflict_evidence_status": "unavailable",
            "coordination_specificity_cap": coordination_cap,
        })

    result = {
        "policy_version": COORDINATION_POLICY_VERSION,
        "target_scope": target,
        "relations": relations,
        "source_ranking_digest": ranking_digest,
        "source_interpretation_digest": interpretation_digest,
    }
    result["coordination_digest"] = _digest(result)
    return result
