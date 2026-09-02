"""Deterministic event-family attribution for v1.6 Hybrid accuracy research.

EFA is additive.  It preserves the already-materialized relationship between
Phase 3 event-family candidates and complete Structural Interpretation
EvidenceFeature provenance.  It does not rank domains or create candidates.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence

from .errors import DistributionError
from .evidence_models import EvidenceFeature, evidence_feature_from_dict
from .evidence_policy import POLICY_VERSION
from .evidence_ranker import evaluate_feature_eligibility


EVENT_FAMILY_ATTRIBUTION_PROFILE_VERSION = "lin_tianji_event_family_attribution_v1-exp"
_SUPPORTED_SYSTEMS = ("bazi", "ziwei")


def _raise(message: str, details: Mapping[str, Any] | None = None) -> None:
    raise DistributionError(
        "invalid_event_family_attribution",
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
        _raise("event-family attribution payload must be canonical JSON", {"error": str(exc)})
    raise AssertionError("unreachable")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        _raise("%s must be non-empty text" % field, {"field": field})
    return value


def _validated_digest(value: Mapping[str, object], digest_field: str, label: str) -> str:
    digest = value.get(digest_field)
    if not isinstance(digest, str) or len(digest) != 64:
        _raise("%s must include a SHA-256-shaped %s" % (label, digest_field))
    payload = dict(value)
    payload.pop(digest_field, None)
    actual = _digest(payload)
    if actual != digest:
        _raise(
            "%s digest does not match payload" % label,
            {"expected_digest": digest, "actual_digest": actual},
        )
    return digest


def _validated_ranking(value: object) -> dict:
    if not isinstance(value, Mapping):
        _raise("base_ranking must be a mapping")
    if value.get("policy_version") != POLICY_VERSION:
        _raise(
            "base_ranking policy version is unsupported",
            {"policy_version": value.get("policy_version"), "supported": POLICY_VERSION},
        )

    digest = _validated_digest(value, "ranking_digest", "base ranking")
    target_scope = _text(value.get("target_scope"), "target_scope")
    domains = value.get("domains")
    if not isinstance(domains, list):
        _raise("base_ranking domains must be a list")

    seen_domains = set()
    seen_ranks = set()
    normalized_domains = []
    for raw in domains:
        if not isinstance(raw, Mapping):
            _raise("base_ranking domain rows must be mappings")
        domain = _text(raw.get("primary_domain"), "primary_domain")
        if domain in seen_domains:
            _raise("base_ranking domains must be unique", {"primary_domain": domain})
        seen_domains.add(domain)

        rank = raw.get("rank")
        if isinstance(rank, bool) or not isinstance(rank, int) or rank < 1:
            _raise("base_ranking rank must be a positive integer", {"primary_domain": domain})
        if rank in seen_ranks:
            _raise("base_ranking ranks must be unique", {"rank": rank})
        seen_ranks.add(rank)

        event_families = raw.get("event_families")
        if not isinstance(event_families, list):
            _raise("base_ranking event_families must be a list", {"primary_domain": domain})
        normalized_families = []
        seen_families = set()
        for family in event_families:
            normalized = _text(family, "event_family")
            if normalized in seen_families:
                _raise(
                    "base_ranking event families must be unique within a domain",
                    {"primary_domain": domain, "event_family": normalized},
                )
            seen_families.add(normalized)
            normalized_families.append(normalized)

        normalized_domains.append(
            {
                "primary_domain": domain,
                "rank": rank,
                "event_families": normalized_families,
            }
        )

    expected_ranks = list(range(1, len(normalized_domains) + 1))
    actual_ranks = [row["rank"] for row in normalized_domains]
    if actual_ranks != expected_ranks:
        _raise("base_ranking domain ranks must be contiguous and ordered", {"ranks": actual_ranks})

    opened_domains = value.get("opened_domains")
    if opened_domains is not None:
        expected_domains = [row["primary_domain"] for row in normalized_domains]
        if opened_domains != expected_domains:
            _raise(
                "opened_domains must match ranked domain order",
                {"opened_domains": opened_domains, "domain_order": expected_domains},
            )

    return {
        "target_scope": target_scope,
        "ranking_digest": digest,
        "domains": normalized_domains,
    }


def _validated_structural_interpretation(value: object, target_scope: str) -> dict:
    if not isinstance(value, Mapping):
        _raise("structural_interpretation must be a mapping")
    digest = _validated_digest(value, "interpretation_digest", "structural interpretation")
    structural_scope = _text(value.get("target_scope"), "structural target_scope")
    if structural_scope != target_scope:
        _raise(
            "structural target scope does not match base ranking",
            {"ranking_scope": target_scope, "structural_scope": structural_scope},
        )

    raw_features = value.get("features")
    if not isinstance(raw_features, list):
        _raise("structural_interpretation features must be a list")

    features = []
    seen_feature_ids = set()
    for raw in raw_features:
        feature = evidence_feature_from_dict(raw)
        if feature.system not in _SUPPORTED_SYSTEMS:
            _raise(
                "structural interpretation contains unsupported system for EFA",
                {"feature_id": feature.feature_id, "system": feature.system},
            )
        if feature.feature_id in seen_feature_ids:
            _raise("structural feature IDs must be unique", {"feature_id": feature.feature_id})
        seen_feature_ids.add(feature.feature_id)
        features.append(feature)

    return {
        "target_scope": structural_scope,
        "interpretation_digest": digest,
        "features": features,
    }


def _parent_claim_id(target_scope: str, primary_domain: str) -> str:
    base = "claim:%s:%s" % (target_scope, primary_domain)
    if "\n" not in base and "\r" not in base and ":" not in primary_domain:
        return base
    token = _digest({"primary_domain": primary_domain, "target_scope": target_scope})[:16]
    return "claim:%s:%s" % (target_scope, token)


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


def _feature_membership(
    feature: EvidenceFeature,
    *,
    domain: str,
    event_family: str,
) -> bool:
    return (
        feature.primary_domain == domain
        and event_family in feature.event_family_support
        and feature.qualification_status != "unqualified"
    )


def _family_specificity(direct_targets: Sequence[EvidenceFeature]) -> str | None:
    if not direct_targets:
        return None
    dependencies = {feature.dependency_family for feature in direct_targets}
    has_stable = any(feature.maturity == "stable" for feature in direct_targets)
    if has_stable and len(dependencies) >= 2:
        return "concrete_event"
    return "event_family"


def _child_row(
    *,
    target_scope: str,
    domain: str,
    event_family: str,
    features: Sequence[EvidenceFeature],
    ranking_digest: str,
    structural_digest: str,
) -> dict:
    direct_targets = []
    modifiers = []
    timing_triggers = []

    for feature in features:
        if not _feature_membership(feature, domain=domain, event_family=event_family):
            continue
        eligibility = evaluate_feature_eligibility(feature, target_scope)
        if not eligibility["eligible"]:
            continue
        if feature.role == "target_evidence" and eligibility["can_open_domain"]:
            direct_targets.append(feature)
        elif feature.role == "modifier":
            modifiers.append(feature)
        elif feature.role == "timing_trigger":
            timing_triggers.append(feature)

    direct_targets = sorted(direct_targets, key=lambda item: item.feature_id)
    modifiers = sorted(modifiers, key=lambda item: item.feature_id)
    timing_triggers = sorted(timing_triggers, key=lambda item: item.feature_id)

    bazi_targets = [item.feature_id for item in direct_targets if item.system == "bazi"]
    ziwei_targets = [item.feature_id for item in direct_targets if item.system == "ziwei"]
    dependencies = sorted({item.dependency_family for item in direct_targets})
    systems = sorted({item.system for item in direct_targets}, key=_SUPPORTED_SYSTEMS.index)

    return {
        "child_claim_id": _child_claim_id(target_scope, domain, event_family),
        "parent_claim_id": _parent_claim_id(target_scope, domain),
        "primary_domain": domain,
        "event_family": event_family,
        "target_scope": target_scope,
        "candidate_source": "phase3",
        "child_opened": bool(direct_targets),
        "bazi_target_feature_ids": bazi_targets,
        "ziwei_target_feature_ids": ziwei_targets,
        "modifier_feature_ids": [item.feature_id for item in modifiers],
        "timing_trigger_feature_ids": [item.feature_id for item in timing_triggers],
        "direct_target_dependency_families": dependencies,
        "direct_target_systems": systems,
        "maturity_summary": sorted({item.maturity for item in direct_targets}),
        "qualification_summary": sorted({item.qualification_status for item in direct_targets}),
        "required_verification_caveat": any(
            item.qualification_status == "needs_verification" for item in direct_targets
        ),
        "family_specificity_ceiling": _family_specificity(direct_targets),
        "source_ranking_digest": ranking_digest,
        "source_structural_interpretation_digest": structural_digest,
    }


def build_event_family_attribution_bundle(
    *,
    base_ranking: Mapping[str, object],
    structural_interpretation: Mapping[str, object],
) -> dict:
    """Build deterministic child-event attribution without changing Phase 3."""

    ranking = _validated_ranking(base_ranking)
    structural = _validated_structural_interpretation(
        structural_interpretation,
        ranking["target_scope"],
    )

    children = []
    seen_child_ids = set()
    for domain_row in ranking["domains"]:
        domain = domain_row["primary_domain"]
        for event_family in domain_row["event_families"]:
            row = _child_row(
                target_scope=ranking["target_scope"],
                domain=domain,
                event_family=event_family,
                features=structural["features"],
                ranking_digest=ranking["ranking_digest"],
                structural_digest=structural["interpretation_digest"],
            )
            if row["child_claim_id"] in seen_child_ids:
                _raise("child claim IDs must be unique", {"child_claim_id": row["child_claim_id"]})
            seen_child_ids.add(row["child_claim_id"])
            children.append(row)

    payload = {
        "profile_version": EVENT_FAMILY_ATTRIBUTION_PROFILE_VERSION,
        "target_scope": ranking["target_scope"],
        "base_ranking_digest": ranking["ranking_digest"],
        "structural_interpretation_digest": structural["interpretation_digest"],
        "children": children,
    }
    payload["event_family_attribution_digest"] = _digest(payload)
    return payload
