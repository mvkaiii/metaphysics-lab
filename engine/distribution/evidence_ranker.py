"""Deterministic evidence eligibility and ordinal ranking for 林氏天機 v1.5.

Phase 3 ranking is intentionally non-probabilistic.  The values produced here
represent structural ordering only; they are not event likelihoods.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence

from .errors import DistributionError
from .evidence_models import EvidenceFeature, evidence_feature_from_dict
from .evidence_policy import (
    EXPERIMENTAL_FACTOR_NUM,
    INDEPENDENT_CONVERGENCE_BONUS,
    MODIFIER_CAP,
    POLICY_VERSION,
    STABLE_FACTOR_NUM,
    TARGET_SCOPE_BASE,
    TIMING_TRIGGER_CAP,
)


_SCOPE_ORDER = ("major_cycle", "decadal", "yearly", "monthly", "daily", "hourly")
_ORDINAL_SCALE = 2
_STRENGTH_ORDER = {
    "unspecified": 0,
    "weak": 1,
    "moderate": 2,
    "strong": 3,
}
_ROLE_ORDER = {
    "target_evidence": 3,
    "modifier": 2,
    "timing_trigger": 1,
}


def _raise(code: str, message: str, details: Mapping[str, Any] | None = None) -> None:
    raise DistributionError(code, message, {} if details is None else dict(details))


def _canonical_bytes(value: object) -> bytes:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        _raise(
            "invalid_evidence_ranking",
            "ranking payload must be canonical JSON",
            {"error": str(exc)},
        )
    return encoded.encode("utf-8")


def _canonical_digest(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _validate_policy_version(policy_version: object) -> str:
    if policy_version != POLICY_VERSION:
        _raise(
            "unsupported_evidence_policy",
            "unsupported evidence ranking policy",
            {"policy_version": policy_version, "supported": POLICY_VERSION},
        )
    return POLICY_VERSION


def _validate_target_scope(target_scope: object) -> str:
    if not isinstance(target_scope, str) or target_scope not in _SCOPE_ORDER:
        _raise(
            "evidence_rank_scope_blocked",
            "target scope is unsupported for evidence ranking",
            {"target_scope": target_scope, "allowed_scopes": list(_SCOPE_ORDER)},
        )
    return target_scope


def _normalize_feature(feature: object) -> EvidenceFeature:
    if isinstance(feature, EvidenceFeature):
        return feature
    if not isinstance(feature, Mapping):
        _raise(
            "invalid_evidence_ranking",
            "evidence feature must be a structured mapping",
            {"type": type(feature).__name__},
        )
    return evidence_feature_from_dict(feature)


def _role_scope_is_valid(feature: EvidenceFeature, target_scope: str) -> bool:
    if feature.scope not in _SCOPE_ORDER:
        return False
    scope_index = _SCOPE_ORDER.index(feature.scope)
    target_index = _SCOPE_ORDER.index(target_scope)
    if feature.role == "target_evidence":
        return scope_index == target_index
    if feature.role == "modifier":
        return scope_index < target_index
    if feature.role == "timing_trigger":
        return scope_index > target_index
    return False


def _base_contribution(role: str) -> int:
    if role == "target_evidence":
        return TARGET_SCOPE_BASE
    if role == "modifier":
        return MODIFIER_CAP
    if role == "timing_trigger":
        return TIMING_TRIGGER_CAP
    return 0


def _maturity_numerator(maturity: str) -> int:
    if maturity == "stable":
        return STABLE_FACTOR_NUM
    return EXPERIMENTAL_FACTOR_NUM


def evaluate_feature_eligibility(
    feature: object,
    target_scope: str,
    policy_version: str = POLICY_VERSION,
) -> dict:
    """Evaluate one feature without assigning probability semantics."""

    profile = _validate_policy_version(policy_version)
    target = _validate_target_scope(target_scope)
    normalized = _normalize_feature(feature)

    result = {
        "feature_id": normalized.feature_id,
        "primary_domain": normalized.primary_domain,
        "system": normalized.system,
        "scope": normalized.scope,
        "role": normalized.role,
        "dependency_family": normalized.dependency_family,
        "maturity": normalized.maturity,
        "qualification_status": normalized.qualification_status,
        "strength_class": normalized.strength_class,
        "policy_version": profile,
        "eligible": False,
        "reason": "ineligible",
        "can_open_domain": False,
        "ordinal_contribution_scaled": 0,
        "ordinal_scale": _ORDINAL_SCALE,
        "verification_required": normalized.qualification_status == "needs_verification",
    }

    if normalized.qualification_status == "unqualified":
        result["reason"] = "unqualified"
        return result

    if normalized.role not in _ROLE_ORDER:
        result["reason"] = "unsupported_role_phase3"
        return result

    if not _role_scope_is_valid(normalized, target):
        result["reason"] = "role_scope_mismatch"
        return result

    base = _base_contribution(normalized.role)
    contribution = base * _maturity_numerator(normalized.maturity)
    result.update(
        {
            "eligible": True,
            "reason": "eligible",
            "can_open_domain": normalized.role == "target_evidence" and normalized.scope == target,
            "ordinal_contribution_scaled": contribution,
        }
    )
    return result


def _selected_dependency_feature(items: Sequence[tuple[EvidenceFeature, dict]]) -> tuple[EvidenceFeature, dict]:
    return sorted(
        items,
        key=lambda item: (
            -item[1]["ordinal_contribution_scaled"],
            -_STRENGTH_ORDER[item[0].strength_class],
            -_ROLE_ORDER.get(item[0].role, 0),
            item[0].feature_id,
        ),
    )[0]


def _allowed_specificity(target_features: Sequence[EvidenceFeature]) -> str:
    event_families = {
        family
        for feature in target_features
        for family in feature.event_family_support
    }
    if not event_families:
        return "domain"

    stable_targets = [feature for feature in target_features if feature.maturity == "stable"]
    independent_target_dependencies = {feature.dependency_family for feature in target_features}
    if stable_targets and len(independent_target_dependencies) >= 2:
        return "concrete_event"
    return "event_family"


def rank_evidence(
    features: Sequence[object],
    target_scope: str,
    parent_ranking: Mapping[str, object] | None = None,
    policy_version: str = POLICY_VERSION,
) -> dict:
    """Rank target-owned domains using deterministic ordinal contributions.

    Coarser modifiers and finer timing triggers may contribute only after a
    target-scope feature has opened the domain.  Dependency families are
    de-duplicated before convergence is counted.
    """

    profile = _validate_policy_version(policy_version)
    target = _validate_target_scope(target_scope)
    if not isinstance(features, (list, tuple)):
        _raise(
            "invalid_evidence_ranking",
            "features must be an ordered sequence",
            {"type": type(features).__name__},
        )
    if parent_ranking is not None and not isinstance(parent_ranking, Mapping):
        _raise(
            "invalid_evidence_ranking",
            "parent_ranking must be a mapping when provided",
        )

    normalized = [_normalize_feature(feature) for feature in features]
    evaluated = [
        evaluate_feature_eligibility(feature, target, profile)
        for feature in normalized
    ]
    pairs = list(zip(normalized, evaluated))

    opened = {
        feature.primary_domain
        for feature, eligibility in pairs
        if eligibility["eligible"] and eligibility["can_open_domain"]
    }

    domains = []
    for domain in sorted(opened):
        eligible_pairs = [
            (feature, eligibility)
            for feature, eligibility in pairs
            if eligibility["eligible"] and feature.primary_domain == domain
        ]
        target_pairs = [
            (feature, eligibility)
            for feature, eligibility in eligible_pairs
            if eligibility["can_open_domain"]
        ]

        dependency_groups = {}
        for feature, eligibility in eligible_pairs:
            dependency_groups.setdefault(feature.dependency_family, []).append((feature, eligibility))
        selected_pairs = [
            _selected_dependency_feature(dependency_groups[dependency])
            for dependency in sorted(dependency_groups)
        ]

        base_score = sum(
            eligibility["ordinal_contribution_scaled"]
            for _, eligibility in selected_pairs
        )
        independent_dependency_count = len(selected_pairs)
        convergence_bonus = (
            INDEPENDENT_CONVERGENCE_BONUS * _ORDINAL_SCALE
            if independent_dependency_count >= 2
            else 0
        )
        ordinal_score = base_score + convergence_bonus

        target_features = [feature for feature, _ in target_pairs]
        target_dependency_count = len({feature.dependency_family for feature in target_features})
        system_count = len({feature.system for feature, _ in selected_pairs})
        target_strength_rank = max(_STRENGTH_ORDER[feature.strength_class] for feature in target_features)
        target_strength_class = max(
            (feature.strength_class for feature in target_features),
            key=lambda value: _STRENGTH_ORDER[value],
        )
        event_families = sorted(
            {
                family
                for feature in target_features
                for family in feature.event_family_support
            }
        )

        domains.append(
            {
                "primary_domain": domain,
                "ordinal_score_scaled": ordinal_score,
                "ordinal_scale": _ORDINAL_SCALE,
                "independent_dependency_count": independent_dependency_count,
                "target_dependency_count": target_dependency_count,
                "system_count": system_count,
                "allowed_specificity": _allowed_specificity(target_features),
                "target_strength_class": target_strength_class,
                "target_strength_rank": target_strength_rank,
                "event_families": event_families,
                "feature_ids": [feature.feature_id for feature, _ in selected_pairs],
            }
        )

    domains.sort(
        key=lambda item: (
            -item["ordinal_score_scaled"],
            -item["target_strength_rank"],
            item["primary_domain"],
        )
    )
    for index, domain in enumerate(domains, start=1):
        domain["rank"] = index
        del domain["target_strength_rank"]

    payload = {
        "policy_version": profile,
        "target_scope": target,
        "ordinal_scale": _ORDINAL_SCALE,
        "feature_count": len(normalized),
        "evaluated_features": evaluated,
        "opened_domains": [domain["primary_domain"] for domain in domains],
        "domains": domains,
    }
    payload["ranking_digest"] = _canonical_digest(payload)
    return payload
