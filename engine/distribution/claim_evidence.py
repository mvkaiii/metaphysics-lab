"""Deterministic Claim Evidence Packet builder for Interpretation vNext."""

from __future__ import annotations

import hashlib
import json
from typing import Mapping, Sequence

from .errors import DistributionError
from .evidence_models import EvidenceFeature, SCOPES, evidence_feature_from_dict
from .evidence_policy import POLICY_VERSION, SPECIFICITY_LEVELS


CLAIM_EVIDENCE_PROFILE_VERSION = "lin_tianji_claim_evidence_v1-exp"
CROSS_SYSTEM_RELATIONS = (
    "independent_convergence",
    "layered_complement",
    "conflict_or_divergence",
)
CONFIDENCE_CLASSES = (
    "high_confidence",
    "moderate_confidence",
    "low_confidence",
)
ABSTENTION_LABELS = (
    "abstain_domain",
    "abstain_event_family",
    "abstain_timing",
    "abstain_concrete_event",
)
_ALLOWED_SYSTEMS = frozenset(("bazi", "ziwei"))


def _raise(message: str, details=None) -> None:
    raise DistributionError(
        "invalid_claim_evidence",
        message,
        {} if details is None else dict(details),
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
        _raise("claim evidence input must be canonical JSON", {"error": str(exc)})
    raise AssertionError("unreachable")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _validated_digest(value: Mapping[str, object], field: str, label: str) -> str:
    expected = value.get(field)
    if not isinstance(expected, str) or not expected:
        _raise("%s must include %s" % (label, field))
    body = dict(value)
    body.pop(field, None)
    actual = _digest(body)
    if actual != expected:
        _raise(
            "%s digest does not match payload" % label,
            {"expected_digest": expected, "actual_digest": actual},
        )
    return expected


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        _raise("%s must be non-empty text" % field, {"field": field})
    return value


def _texts(value: object, field: str) -> list[str]:
    if not isinstance(value, list):
        _raise("%s must be a list" % field, {"field": field})
    rows = []
    for item in value:
        if not isinstance(item, str) or not item:
            _raise("%s entries must be non-empty text" % field, {"field": field})
        rows.append(item)
    if len(rows) != len(set(rows)):
        _raise("%s entries must be unique" % field, {"field": field})
    return rows


def _validate_base_ranking(value: object) -> dict:
    if not isinstance(value, Mapping):
        _raise("base_ranking must be a mapping")
    if value.get("policy_version") != POLICY_VERSION:
        _raise("unsupported base ranking policy", {"policy_version": value.get("policy_version")})
    digest = _validated_digest(value, "ranking_digest", "base ranking")
    target_scope = _text(value.get("target_scope"), "target_scope")
    domains = value.get("domains")
    if not isinstance(domains, list) or any(not isinstance(item, Mapping) for item in domains):
        _raise("base ranking domains must be a list of mappings")
    normalized = []
    seen = set()
    for raw in domains:
        domain = _text(raw.get("primary_domain"), "primary_domain")
        if domain in seen:
            _raise("base ranking domains must be unique", {"primary_domain": domain})
        seen.add(domain)
        families = _texts(raw.get("event_families"), "event_families")
        feature_ids = _texts(raw.get("feature_ids"), "feature_ids")
        specificity = raw.get("allowed_specificity")
        if specificity not in SPECIFICITY_LEVELS:
            _raise("base ranking specificity is invalid", {"primary_domain": domain})
        independent = raw.get("independent_dependency_count")
        if isinstance(independent, bool) or not isinstance(independent, int) or independent < 0:
            _raise("independent_dependency_count must be a non-negative integer")
        normalized.append(
            {
                "primary_domain": domain,
                "rank": raw.get("rank"),
                "event_families": families,
                "feature_ids": feature_ids,
                "allowed_specificity": specificity,
                "independent_dependency_count": independent,
            }
        )
    return {
        "target_scope": target_scope,
        "ranking_digest": digest,
        "domains": normalized,
    }


def _validate_structural_interpretation(value: object, target_scope: str) -> tuple[str, list[EvidenceFeature]]:
    if not isinstance(value, Mapping):
        _raise("structural_interpretation must be a mapping")
    digest = _validated_digest(value, "interpretation_digest", "structural interpretation")
    if value.get("target_scope") != target_scope:
        _raise("structural interpretation target scope does not match base ranking")
    raw_features = value.get("features")
    if not isinstance(raw_features, list):
        _raise("structural interpretation features must be a list")
    features = []
    seen_ids = set()
    for raw in raw_features:
        try:
            feature = evidence_feature_from_dict(raw)
        except DistributionError as exc:
            _raise("structural interpretation contains invalid evidence feature", {"cause": str(exc)})
        if feature.feature_id in seen_ids:
            _raise("structural feature IDs must be unique", {"feature_id": feature.feature_id})
        seen_ids.add(feature.feature_id)
        features.append(feature)
    return digest, features


def _validate_domain_interpretation(value: object, base_domains: Sequence[Mapping[str, object]]) -> dict[str, dict]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        _raise("domain_interpretation must be a sequence")
    rows = {}
    for raw in value:
        if not isinstance(raw, Mapping):
            _raise("domain_interpretation rows must be mappings")
        domain = _text(raw.get("primary_domain"), "primary_domain")
        if domain in rows:
            _raise("domain_interpretation domains must be unique", {"primary_domain": domain})
        candidates = _texts(raw.get("event_family_candidates"), "event_family_candidates")
        effective = raw.get("effective_specificity")
        base_specificity = raw.get("base_allowed_specificity")
        if effective not in SPECIFICITY_LEVELS or base_specificity not in SPECIFICITY_LEVELS:
            _raise("domain_interpretation specificity is invalid", {"primary_domain": domain})
        if SPECIFICITY_LEVELS.index(effective) > SPECIFICITY_LEVELS.index(base_specificity):
            _raise("domain_interpretation cannot raise specificity", {"primary_domain": domain})
        explanation_classes = raw.get("evidence_explanation_classes", [])
        if not isinstance(explanation_classes, list) or any(not isinstance(item, str) for item in explanation_classes):
            _raise("evidence_explanation_classes must be a text list", {"primary_domain": domain})
        rows[domain] = {
            "event_family_candidates": candidates,
            "effective_specificity": effective,
            "base_allowed_specificity": base_specificity,
            "evidence_explanation_classes": list(explanation_classes),
        }
    base_ids = {str(item["primary_domain"]) for item in base_domains}
    if set(rows) != base_ids:
        _raise(
            "domain_interpretation domain set must equal base ranking domain set",
            {"base_domains": sorted(base_ids), "interpretation_domains": sorted(rows)},
        )
    return rows


def _claim_id(target_scope: str, primary_domain: str) -> str:
    if ":" not in primary_domain and "\n" not in primary_domain and "\r" not in primary_domain:
        return "claim:%s:%s" % (target_scope, primary_domain)
    token = _digest({"target_scope": target_scope, "primary_domain": primary_domain})[:16]
    return "claim:%s:%s" % (target_scope, token)


def _evidence_row(feature: EvidenceFeature) -> dict:
    payload = feature.to_dict()
    return {
        "feature_id": payload["feature_id"],
        "system": payload["system"],
        "scope": payload["scope"],
        "role": payload["role"],
        "strength_class": payload["strength_class"],
        "maturity": payload["maturity"],
        "qualification_status": payload["qualification_status"],
        "source_family": payload["source_family"],
        "dependency_family": payload["dependency_family"],
        "provenance": payload["provenance"],
    }


def classify_cross_system_relation(
    *,
    packet_domain: str,
    selected_features: Sequence[EvidenceFeature],
    all_selected_features: Sequence[EvidenceFeature],
    target_scope: str,
) -> tuple[str | None, list[dict]]:
    bazi_target_domains = sorted({
        feature.primary_domain
        for feature in all_selected_features
        if feature.system == "bazi" and feature.role == "target_evidence" and feature.scope == target_scope
    })
    ziwei_target_domains = sorted({
        feature.primary_domain
        for feature in all_selected_features
        if feature.system == "ziwei" and feature.role == "target_evidence" and feature.scope == target_scope
    })
    if bazi_target_domains and ziwei_target_domains and not (set(bazi_target_domains) & set(ziwei_target_domains)):
        conflict = {
            "reason": "disjoint_target_domain_sets",
            "bazi_target_domains": bazi_target_domains,
            "ziwei_target_domains": ziwei_target_domains,
        }
        return "conflict_or_divergence", [conflict]

    packet = [feature for feature in selected_features if feature.primary_domain == packet_domain]
    systems = {feature.system for feature in packet}
    if not {"bazi", "ziwei"} <= systems:
        return None, []

    bazi_target = any(
        feature.system == "bazi" and feature.role == "target_evidence" and feature.scope == target_scope
        for feature in packet
    )
    ziwei_target = any(
        feature.system == "ziwei" and feature.role == "target_evidence" and feature.scope == target_scope
        for feature in packet
    )
    if bazi_target and ziwei_target:
        return "independent_convergence", []
    if bazi_target != ziwei_target:
        supporting_system = "ziwei" if bazi_target else "bazi"
        if any(
            feature.system == supporting_system and feature.role in {"modifier", "timing_trigger"}
            for feature in packet
        ):
            return "layered_complement", []
    return None, []


def abstentions_for_packet(
    *,
    effective_specificity: str,
    event_family_candidates: Sequence[str],
    has_local_window: bool,
    cross_system_relation: str | None,
) -> list[str]:
    if effective_specificity not in SPECIFICITY_LEVELS:
        _raise("effective specificity is invalid", {"effective_specificity": effective_specificity})
    abstentions = []
    if effective_specificity == "domain" or not event_family_candidates:
        abstentions.append("abstain_event_family")
    if not has_local_window:
        abstentions.append("abstain_timing")
    if effective_specificity != "concrete_event":
        abstentions.append("abstain_concrete_event")
    return [label for label in ABSTENTION_LABELS if label in abstentions]


def confidence_class_for_packet(packet_inputs: Mapping[str, object]) -> str:
    relation = packet_inputs.get("cross_system_relation")
    specificity = packet_inputs.get("effective_specificity")
    selected = packet_inputs.get("selected_features")
    target_scope = packet_inputs.get("target_scope")
    if not isinstance(selected, Sequence) or isinstance(selected, (str, bytes)):
        _raise("selected_features must be a sequence for confidence classification")
    target_features = [
        feature for feature in selected
        if isinstance(feature, EvidenceFeature)
        and feature.role == "target_evidence"
        and feature.scope == target_scope
    ]
    if relation == "conflict_or_divergence" or specificity == "domain":
        return "low_confidence"
    if target_features and all(
        feature.maturity == "experimental" or feature.qualification_status == "needs_verification"
        for feature in target_features
    ):
        return "low_confidence"
    if (
        relation == "independent_convergence"
        and target_features
        and all(feature.qualification_status == "qualified" for feature in target_features)
        and any(feature.maturity == "stable" for feature in target_features)
        and specificity in {"event_family", "concrete_event"}
    ):
        return "high_confidence"
    return "moderate_confidence"


def build_claim_evidence_packets(
    *,
    base_ranking: Mapping[str, object],
    structural_interpretation: Mapping[str, object],
    domain_interpretation: Sequence[Mapping[str, object]],
) -> dict:
    base = _validate_base_ranking(base_ranking)
    structural_digest, features = _validate_structural_interpretation(
        structural_interpretation,
        base["target_scope"],
    )
    domains = _validate_domain_interpretation(domain_interpretation, base["domains"])
    by_id = {feature.feature_id: feature for feature in features}

    selected_by_domain = {}
    all_selected = []
    for base_domain in base["domains"]:
        domain = str(base_domain["primary_domain"])
        selected = []
        for feature_id in base_domain["feature_ids"]:
            feature = by_id.get(feature_id)
            if feature is None:
                _raise("selected feature ID is missing from structural interpretation", {"feature_id": feature_id})
            if feature.primary_domain != domain:
                _raise(
                    "selected feature domain does not match ranking domain",
                    {"feature_id": feature_id, "ranking_domain": domain, "feature_domain": feature.primary_domain},
                )
            if feature.system not in _ALLOWED_SYSTEMS:
                _raise(
                    "claim evidence packets accept only Bazi and Ziwei structural evidence",
                    {"feature_id": feature.feature_id, "system": feature.system},
                )
            selected.append(feature)
        selected_by_domain[domain] = selected
        all_selected.extend(selected)

    packets = []
    global_conflicts = []
    for base_domain in base["domains"]:
        domain = str(base_domain["primary_domain"])
        domain_row = domains[domain]
        if domain_row["event_family_candidates"] != base_domain["event_families"]:
            _raise("event-family candidate set must equal Phase 3 candidate set", {"primary_domain": domain})
        if domain_row["base_allowed_specificity"] != base_domain["allowed_specificity"]:
            _raise("domain base specificity must equal Phase 3 specificity", {"primary_domain": domain})

        selected = selected_by_domain[domain]
        relation, conflicts = classify_cross_system_relation(
            packet_domain=domain,
            selected_features=selected,
            all_selected_features=all_selected,
            target_scope=base["target_scope"],
        )
        has_local_window = any(
            item in {"local_spike", "active_window"}
            for item in domain_row["evidence_explanation_classes"]
        )
        abstentions = abstentions_for_packet(
            effective_specificity=domain_row["effective_specificity"],
            event_family_candidates=base_domain["event_families"],
            has_local_window=has_local_window,
            cross_system_relation=relation,
        )
        confidence = confidence_class_for_packet({
            "cross_system_relation": relation,
            "effective_specificity": domain_row["effective_specificity"],
            "selected_features": selected,
            "target_scope": base["target_scope"],
        })
        for conflict in conflicts:
            if conflict not in global_conflicts:
                global_conflicts.append(conflict)

        dependency_count = len({feature.dependency_family for feature in selected})
        if dependency_count != base_domain["independent_dependency_count"]:
            _raise(
                "selected feature dependency count does not match Phase 3 ranking",
                {"primary_domain": domain, "expected": base_domain["independent_dependency_count"], "actual": dependency_count},
            )
        source_layers = sorted(
            {feature.scope for feature in selected},
            key=lambda scope: SCOPES.index(scope),
        )
        bazi = [_evidence_row(feature) for feature in selected if feature.system == "bazi"]
        ziwei = [_evidence_row(feature) for feature in selected if feature.system == "ziwei"]
        packet = {
            "claim_id": _claim_id(base["target_scope"], domain),
            "primary_domain": domain,
            "event_family_candidates": list(base_domain["event_families"]),
            "time_scope": base["target_scope"],
            "bazi_evidence": bazi,
            "ziwei_evidence": ziwei,
            "source_layers": source_layers,
            "independent_support_count": dependency_count,
            "cross_system_relation": relation,
            "conflicts": conflicts,
            "assumptions": [],
            "base_allowed_specificity": base_domain["allowed_specificity"],
            "effective_specificity": domain_row["effective_specificity"],
            "abstention_status": abstentions,
            "confidence_class": confidence,
            "reasoning_chain": {
                "phase3_ranking_digest": base["ranking_digest"],
                "structural_interpretation_digest": structural_digest,
                "selected_feature_ids": list(base_domain["feature_ids"]),
                "specificity_authority": "phase3_with_existing_local_window_cap",
            },
        }
        packets.append(packet)

    result = {
        "profile_version": CLAIM_EVIDENCE_PROFILE_VERSION,
        "target_scope": base["target_scope"],
        "base_ranking_digest": base["ranking_digest"],
        "structural_interpretation_digest": structural_digest,
        "packets": packets,
        "global_conflicts": global_conflicts,
    }
    result["claim_evidence_digest"] = _digest(result)
    return result
