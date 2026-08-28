"""Deterministic Phase 5 interpretation boundary for 林氏天機 v1.5.

Phase 5 consumes an immutable Phase 3 ranking plus a resolved prospective
anchor and turns them into machine-readable interpretation metadata.  It does
not re-rank evidence, generate events, or assign probability semantics.
"""

from __future__ import annotations

import hashlib
import json
from typing import Mapping, Sequence

from .errors import DistributionError
from .evidence_policy import POLICY_VERSION, SPECIFICITY_LEVELS


INTERPRETATION_PROFILE_VERSION = "lin_tianji_interpretation_contract_v1-exp"
PRIMARY_DOMAIN_DISPLAY_LIMIT = 3

_RESOLVED_ANCHOR_FIELDS = {
    "query_anchor_at",
    "query_timezone",
    "knowledge_cutoff_at",
    "prospective_window_start",
    "prospective_window_end",
    "question_reference",
    "status",
}

_REALITY_CONTEXT_POLICY = {
    "may_adjust_strategy": True,
    "may_adjust_priority_of_advice": True,
    "may_adjust_feasibility": True,
    "may_change_base_ranking": False,
    "may_change_personalization": False,
    "may_open_domain": False,
    "may_add_event_family": False,
    "may_raise_specificity": False,
    "may_relabel_known_fact_as_prediction": False,
}

_FORECAST_STRATEGY_POLICY = {
    "forecast_specificity_authority": "phase3",
    "strategy_specificity_authority": "reality_context",
    "strategy_must_not_be_presented_as_forecast": True,
    "known_reality_must_not_be_scored_as_hit": True,
    "stage2_must_not_rewrite_stage1": True,
}

_DISCLOSURE_POLICY = {
    "user_facing_language": "zh-Hant-TW",
    "default_explanation_level": "user_safe",
    "allow_high_level_method_rationale": True,
    "allow_metaphysical_terms_when_relevant": True,
    "expose_numeric_weights": False,
    "expose_numeric_thresholds": False,
    "expose_internal_feature_vectors": False,
    "expose_raw_gate_formula": False,
    "expose_ranking_digest_to_ordinary_user": False,
    "expose_runtime_field_names_to_ordinary_user": False,
    "technical_audit_may_use_internal_terms": True,
}


def _raise(message: str, details=None) -> None:
    raise DistributionError(
        "invalid_interpretation_contract",
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
        _raise(
            "interpretation contract input must be canonical JSON",
            {"error": str(exc)},
        )


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        _raise("%s must be non-empty text" % label, {"field": label})
    return value


def _ordered_texts(value: object, label: str) -> list:
    if not isinstance(value, list):
        _raise("%s must be a list" % label, {"field": label})
    result = []
    for item in value:
        if not isinstance(item, str) or not item:
            _raise("%s entries must be non-empty text" % label, {"field": label})
        result.append(item)
    return result


def _validate_base_ranking(value: object) -> dict:
    if not isinstance(value, Mapping):
        _raise("base_ranking must be a mapping")
    if value.get("policy_version") != POLICY_VERSION:
        _raise(
            "unsupported base ranking policy",
            {
                "policy_version": value.get("policy_version"),
                "supported": POLICY_VERSION,
            },
        )

    digest = value.get("ranking_digest")
    if not isinstance(digest, str) or not digest:
        _raise("base ranking must include ranking_digest")
    digest_payload = dict(value)
    digest_payload.pop("ranking_digest", None)
    actual_digest = _digest(digest_payload)
    if actual_digest != digest:
        _raise(
            "base ranking digest does not match payload",
            {"expected_digest": digest, "actual_digest": actual_digest},
        )

    target_scope = _text(value.get("target_scope"), "target_scope")
    evaluated_features = value.get("evaluated_features")
    if not isinstance(evaluated_features, list):
        _raise("base ranking evaluated_features must be a list")
    opened_domains = _ordered_texts(value.get("opened_domains"), "opened_domains")

    domains = value.get("domains")
    if not isinstance(domains, list):
        _raise("base ranking domains must be a list")

    seen_domains = set()
    seen_ranks = set()
    normalized_domains = []
    for raw in domains:
        if not isinstance(raw, Mapping):
            _raise("base ranking domain rows must be mappings")
        domain = _text(raw.get("primary_domain"), "primary_domain")
        if domain in seen_domains:
            _raise("base ranking domains must be unique", {"primary_domain": domain})
        seen_domains.add(domain)

        rank = raw.get("rank")
        if isinstance(rank, bool) or not isinstance(rank, int) or rank < 1:
            _raise(
                "base ranking domain rank must be a positive integer",
                {"primary_domain": domain},
            )
        if rank in seen_ranks:
            _raise("base ranking ranks must be unique", {"rank": rank})
        seen_ranks.add(rank)

        event_families = _ordered_texts(raw.get("event_families"), "event_families")
        if len(event_families) != len(set(event_families)):
            _raise(
                "base event-family candidates must be unique",
                {"primary_domain": domain},
            )
        allowed_specificity = raw.get("allowed_specificity")
        if allowed_specificity not in SPECIFICITY_LEVELS:
            _raise(
                "base ranking contains invalid specificity",
                {"primary_domain": domain, "allowed_specificity": allowed_specificity},
            )

        normalized_domains.append(
            {
                "primary_domain": domain,
                "rank": rank,
                "event_families": event_families,
                "allowed_specificity": allowed_specificity,
            }
        )

    expected_ranks = list(range(1, len(normalized_domains) + 1))
    actual_ranks = [row["rank"] for row in normalized_domains]
    if actual_ranks != expected_ranks:
        _raise(
            "base ranking domain ranks must be contiguous and in rank order",
            {"ranks": actual_ranks},
        )

    domain_order = [row["primary_domain"] for row in normalized_domains]
    if opened_domains != domain_order:
        _raise(
            "opened_domains must exactly match ranked domain order",
            {"opened_domains": opened_domains, "domain_order": domain_order},
        )

    return {
        "policy_version": POLICY_VERSION,
        "target_scope": target_scope,
        "ranking_digest": digest,
        "evaluated_features": list(evaluated_features),
        "opened_domains": opened_domains,
        "domains": normalized_domains,
    }


def _validate_anchor(value: object) -> dict:
    if not isinstance(value, Mapping):
        _raise("anchor must be a resolved query-anchor mapping")
    keys = set(value)
    missing = sorted(_RESOLVED_ANCHOR_FIELDS - keys)
    unknown = sorted(keys - _RESOLVED_ANCHOR_FIELDS)
    if missing or unknown:
        _raise(
            "resolved anchor fields do not match the fixed contract",
            {"missing_fields": missing, "unknown_fields": unknown},
        )
    if value.get("status") != "ok":
        _raise("formal interpretation contract requires an active prospective window")

    query_anchor_at = _text(value.get("query_anchor_at"), "query_anchor_at")
    knowledge_cutoff_at = _text(value.get("knowledge_cutoff_at"), "knowledge_cutoff_at")
    if query_anchor_at != knowledge_cutoff_at:
        _raise("knowledge_cutoff_at must equal query_anchor_at")

    return {
        "query_anchor_at": query_anchor_at,
        "query_timezone": _text(value.get("query_timezone"), "query_timezone"),
        "knowledge_cutoff_at": knowledge_cutoff_at,
        "prospective_window_start": _text(
            value.get("prospective_window_start"),
            "prospective_window_start",
        ),
        "prospective_window_end": _text(
            value.get("prospective_window_end"),
            "prospective_window_end",
        ),
        "question_reference": _text(
            value.get("question_reference"),
            "question_reference",
        ),
        "status": "ok",
    }


def _specificity_ceiling(rows: Sequence[Mapping[str, object]]):
    if not rows:
        return None
    return max(
        (row["effective_specificity"] for row in rows),
        key=lambda value: SPECIFICITY_LEVELS.index(value),
    )


def build_interpretation_contract(
    base_ranking: Mapping[str, object],
    anchor: Mapping[str, object],
    personalization: Mapping[str, object] = None,
    local_windows: Sequence[object] = None,
    locked_forecast: Mapping[str, object] = None,
) -> dict:
    """Build the deterministic cold-start interpretation boundary.

    Optional Phase 4, local-window, and locked-forecast integrations are added
    in the following implementation task.  Until then, non-empty optional
    inputs fail closed rather than being silently ignored.
    """

    base = _validate_base_ranking(base_ranking)
    resolved_anchor = _validate_anchor(anchor)

    if personalization is not None:
        _raise("personalization is not supported by the cold-start core yet")
    if local_windows not in (None, [], ()):
        _raise("local_windows are not supported by the cold-start core yet")
    if locked_forecast is not None:
        _raise("locked_forecast is not supported by the cold-start core yet")

    domain_rows = []
    for domain in base["domains"]:
        domain_rows.append(
            {
                "primary_domain": domain["primary_domain"],
                "base_rank": domain["rank"],
                "presentation_rank": domain["rank"],
                "personalization_applied": False,
                "base_allowed_specificity": domain["allowed_specificity"],
                "effective_specificity": domain["allowed_specificity"],
                "event_family_candidates": list(domain["event_families"]),
                "personalized_event_family_order": list(domain["event_families"]),
                "preferred_event_families": [],
                "deprioritized_event_families": [],
                "evidence_explanation_classes": [],
            }
        )

    presentation_domains = [row["primary_domain"] for row in domain_rows]
    primary_domains = presentation_domains[:PRIMARY_DOMAIN_DISPLAY_LIMIT]
    secondary_domains = presentation_domains[PRIMARY_DOMAIN_DISPLAY_LIMIT:]

    result = {
        "profile_version": INTERPRETATION_PROFILE_VERSION,
        "target_scope": base["target_scope"],
        "knowledge_cutoff_at": resolved_anchor["knowledge_cutoff_at"],
        "prospective_window_start": resolved_anchor["prospective_window_start"],
        "prospective_window_end": resolved_anchor["prospective_window_end"],
        "base_ranking_digest": base["ranking_digest"],
        "personalization_digest": None,
        "personalization_status": "not_provided",
        "primary_domains": primary_domains,
        "secondary_domains": secondary_domains,
        "domain_interpretation": domain_rows,
        "local_windows": [],
        "specificity_ceiling": _specificity_ceiling(domain_rows),
        "reality_context_policy": dict(_REALITY_CONTEXT_POLICY),
        "forecast_strategy_policy": dict(_FORECAST_STRATEGY_POLICY),
        "disclosure_policy": dict(_DISCLOSURE_POLICY),
        "claim_boundaries": [],
    }
    result["interpretation_contract_digest"] = _digest(result)
    return result
