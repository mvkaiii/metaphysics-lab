"""Deterministic Phase 5 interpretation boundary for 林氏天機 v1.5.

Phase 5 consumes immutable Phase 3 ranking truth plus optional Phase 4
personalization, Phase 3 local-window metadata, and a Phase 1 locked forecast.
It never re-ranks evidence, creates candidates, or assigns probability
semantics.
"""

from __future__ import annotations

import hashlib
import json
from typing import Mapping, Sequence

from .errors import DistributionError
from .evidence_policy import POLICY_VERSION, SPECIFICITY_LEVELS
from .historical_personalization_policy import PERSONALIZATION_PROFILE_VERSION
from .prospective import METHOD_VERSION


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
_LOCAL_WINDOW_FIELDS = {
    "primary_domain",
    "window_type",
    "local_spike",
    "parent_scope",
    "child_scope",
    "parent_rank",
    "child_rank",
    "parent_strength_class",
    "child_strength_class",
    "source_allowed_specificity",
    "allowed_specificity",
    "specificity_capped",
    "parent_ranking_digest",
    "child_ranking_digest",
}
_LOCKED_FORECAST_FIELDS = {
    "status",
    "method_version",
    "anchor",
    "claims",
    "canonical_digest",
}
_EXPLANATION_CLASSES = {
    "independent_convergence",
    "single_system_support",
    "target_with_background_modifier",
    "background_modifier",
    "local_spike",
    "active_window",
    "historically_supported_order",
    "historically_mixed_order",
    "historically_contradicted_order",
    "experimental_only",
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


def _valid_digest(value: Mapping[str, object], digest_field: str, label: str) -> str:
    digest = value.get(digest_field)
    if not isinstance(digest, str) or not digest:
        _raise("%s must include %s" % (label, digest_field))
    payload = dict(value)
    payload.pop(digest_field, None)
    actual = _digest(payload)
    if actual != digest:
        _raise(
            "%s digest does not match payload" % label,
            {"expected_digest": digest, "actual_digest": actual},
        )
    return digest


def _validate_base_ranking(value: object) -> dict:
    if not isinstance(value, Mapping):
        _raise("base_ranking must be a mapping")
    if value.get("policy_version") != POLICY_VERSION:
        _raise(
            "unsupported base ranking policy",
            {"policy_version": value.get("policy_version"), "supported": POLICY_VERSION},
        )

    digest = _valid_digest(value, "ranking_digest", "base ranking")
    target_scope = _text(value.get("target_scope"), "target_scope")
    evaluated_features = value.get("evaluated_features")
    if not isinstance(evaluated_features, list) or any(
        not isinstance(item, Mapping) for item in evaluated_features
    ):
        _raise("base ranking evaluated_features must be a list of mappings")
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
            _raise("base ranking domain rank must be a positive integer", {"primary_domain": domain})
        if rank in seen_ranks:
            _raise("base ranking ranks must be unique", {"rank": rank})
        seen_ranks.add(rank)

        event_families = _ordered_texts(raw.get("event_families"), "event_families")
        if len(event_families) != len(set(event_families)):
            _raise("base event-family candidates must be unique", {"primary_domain": domain})
        allowed_specificity = raw.get("allowed_specificity")
        if allowed_specificity not in SPECIFICITY_LEVELS:
            _raise(
                "base ranking contains invalid specificity",
                {"primary_domain": domain, "allowed_specificity": allowed_specificity},
            )

        independent_dependency_count = raw.get("independent_dependency_count", 0)
        system_count = raw.get("system_count", 0)
        if isinstance(independent_dependency_count, bool) or not isinstance(independent_dependency_count, int):
            _raise("independent dependency count must be an integer", {"primary_domain": domain})
        if isinstance(system_count, bool) or not isinstance(system_count, int):
            _raise("system count must be an integer", {"primary_domain": domain})

        normalized_domains.append(
            {
                "primary_domain": domain,
                "rank": rank,
                "event_families": event_families,
                "allowed_specificity": allowed_specificity,
                "independent_dependency_count": independent_dependency_count,
                "system_count": system_count,
            }
        )

    actual_ranks = [row["rank"] for row in normalized_domains]
    expected_ranks = list(range(1, len(normalized_domains) + 1))
    if actual_ranks != expected_ranks:
        _raise("base ranking domain ranks must be contiguous and in rank order", {"ranks": actual_ranks})
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
        "evaluated_features": [dict(item) for item in evaluated_features],
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
        "prospective_window_start": _text(value.get("prospective_window_start"), "prospective_window_start"),
        "prospective_window_end": _text(value.get("prospective_window_end"), "prospective_window_end"),
        "question_reference": _text(value.get("question_reference"), "question_reference"),
        "status": "ok",
    }


def _specificity_is_no_more_permissive(candidate: str, authority: str) -> bool:
    return SPECIFICITY_LEVELS.index(candidate) <= SPECIFICITY_LEVELS.index(authority)


def _most_conservative(values: Sequence[str]) -> str:
    return min(values, key=lambda item: SPECIFICITY_LEVELS.index(item))


def _validate_personalization(value: object, base: Mapping[str, object]):
    if value is None:
        return None
    if not isinstance(value, Mapping):
        _raise("personalization must be a mapping when supplied")
    if value.get("profile_version") != PERSONALIZATION_PROFILE_VERSION:
        _raise("unsupported personalization profile", {"profile_version": value.get("profile_version")})
    digest = _valid_digest(value, "personalization_digest", "personalization")
    if value.get("base_policy_version") != base["policy_version"]:
        _raise("personalization base policy does not match base ranking")
    if value.get("target_scope") != base["target_scope"]:
        _raise("personalization target scope does not match base ranking")
    if value.get("base_ranking_digest") != base["ranking_digest"]:
        _raise("personalization base ranking digest does not match supplied base ranking")
    status = value.get("personalization_status")
    if status not in {"applied", "no_op"}:
        _raise("unsupported personalization status", {"personalization_status": status})

    rows = value.get("domains")
    if not isinstance(rows, list) or any(not isinstance(item, Mapping) for item in rows):
        _raise("personalization domains must be a list of mappings")
    base_by_domain = {row["primary_domain"]: row for row in base["domains"]}
    if {row.get("primary_domain") for row in rows} != set(base_by_domain):
        _raise("personalization domain set must equal base domain set")

    normalized = {}
    seen_personalized_ranks = set()
    for row in rows:
        domain_id = row.get("primary_domain")
        base_row = base_by_domain[domain_id]
        if row.get("base_rank") != base_row["rank"]:
            _raise("personalization base rank does not match", {"primary_domain": domain_id})
        base_families = _ordered_texts(row.get("base_event_families"), "base_event_families")
        order = _ordered_texts(
            row.get("personalized_event_family_order"),
            "personalized_event_family_order",
        )
        expected_set = set(base_row["event_families"])
        if len(base_families) != len(expected_set) or set(base_families) != expected_set:
            _raise("personalization base family set differs from base ranking", {"primary_domain": domain_id})
        if len(order) != len(expected_set) or set(order) != expected_set:
            _raise("personalized family order must preserve the base candidate set", {"primary_domain": domain_id})
        preferred = _ordered_texts(row.get("preferred_event_families"), "preferred_event_families")
        deprioritized = _ordered_texts(
            row.get("deprioritized_event_families"),
            "deprioritized_event_families",
        )
        if not set(preferred).issubset(expected_set) or not set(deprioritized).issubset(expected_set):
            _raise("personalization preference lists must be subsets of base candidates", {"primary_domain": domain_id})
        specificity = row.get("allowed_specificity")
        if specificity not in SPECIFICITY_LEVELS or not _specificity_is_no_more_permissive(
            specificity, base_row["allowed_specificity"]
        ):
            _raise("personalization cannot raise specificity", {"primary_domain": domain_id})
        personalized_rank = row.get("personalized_rank")
        if isinstance(personalized_rank, bool) or not isinstance(personalized_rank, int) or personalized_rank < 1:
            _raise("personalized rank must be a positive integer", {"primary_domain": domain_id})
        if personalized_rank in seen_personalized_ranks:
            _raise("personalized ranks must be unique", {"personalized_rank": personalized_rank})
        seen_personalized_ranks.add(personalized_rank)
        support_class = row.get("historical_support_class")
        if support_class not in {"insufficient", "contradicted", "mixed", "supported", "strongly_supported"}:
            _raise("unsupported historical support class", {"primary_domain": domain_id})
        normalized[domain_id] = {
            "personalized_rank": personalized_rank,
            "historical_support_class": support_class,
            "personalized_event_family_order": order,
            "preferred_event_families": preferred,
            "deprioritized_event_families": deprioritized,
            "allowed_specificity": specificity,
        }

    return {"digest": digest, "status": status, "domains": normalized}


def _validate_local_windows(value: object, base: Mapping[str, object]) -> list:
    if value is None:
        return []
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        _raise("local_windows must be a sequence")

    scope_order = ("major_cycle", "decadal", "yearly", "monthly", "daily", "hourly")
    base_by_domain = {row["primary_domain"]: row for row in base["domains"]}
    normalized = []
    for raw in value:
        if not isinstance(raw, Mapping) or set(raw) != _LOCAL_WINDOW_FIELDS:
            _raise("local window fields do not match the Phase 3 contract")
        row = dict(raw)
        domain = row.get("primary_domain")
        if domain not in base_by_domain:
            _raise("local window cannot create a domain absent from base ranking", {"primary_domain": domain})

        window_type = row.get("window_type")
        if window_type not in {"local_spike", "active_window"}:
            _raise("unsupported local window type", {"window_type": window_type})
        if row.get("local_spike") is not (window_type == "local_spike"):
            _raise("local_spike flag must agree with window_type")

        parent_digest = row.get("parent_ranking_digest")
        if (
            not isinstance(parent_digest, str)
            or len(parent_digest) != 64
            or any(character not in "0123456789abcdef" for character in parent_digest)
        ):
            _raise("local window parent digest must be a lowercase SHA-256 digest")
        if row.get("child_ranking_digest") != base["ranking_digest"]:
            _raise("local window child digest must match supplied base ranking")

        child_scope = row.get("child_scope")
        parent_scope = row.get("parent_scope")
        if child_scope != base["target_scope"]:
            _raise(
                "local window child scope must match supplied base ranking target scope",
                {"child_scope": child_scope, "target_scope": base["target_scope"]},
            )
        if parent_scope not in scope_order or child_scope not in scope_order:
            _raise(
                "local window scopes are unsupported",
                {"parent_scope": parent_scope, "child_scope": child_scope},
            )
        if scope_order.index(child_scope) <= scope_order.index(parent_scope):
            _raise(
                "local window parent scope must be coarser than child scope",
                {"parent_scope": parent_scope, "child_scope": child_scope},
            )

        source_specificity = row.get("source_allowed_specificity")
        allowed_specificity = row.get("allowed_specificity")
        if source_specificity not in SPECIFICITY_LEVELS or allowed_specificity not in SPECIFICITY_LEVELS:
            _raise("local window specificity is invalid")
        if source_specificity != base_by_domain[domain]["allowed_specificity"]:
            _raise(
                "local window source specificity must match supplied base domain",
                {
                    "primary_domain": domain,
                    "source_allowed_specificity": source_specificity,
                    "base_allowed_specificity": base_by_domain[domain]["allowed_specificity"],
                },
            )
        if not _specificity_is_no_more_permissive(allowed_specificity, source_specificity):
            _raise("local window cannot raise specificity", {"primary_domain": domain})

        specificity_capped = row.get("specificity_capped")
        if not isinstance(specificity_capped, bool):
            _raise("local window specificity_capped must be boolean", {"primary_domain": domain})
        expected_capped = allowed_specificity != source_specificity
        if specificity_capped is not expected_capped:
            _raise(
                "local window specificity_capped must match source and allowed specificity",
                {"primary_domain": domain},
            )

        normalized.append(row)
    return normalized


def _historical_explanation(support_class: str):
    if support_class in {"supported", "strongly_supported"}:
        return "historically_supported_order"
    if support_class == "mixed":
        return "historically_mixed_order"
    if support_class == "contradicted":
        return "historically_contradicted_order"
    return None


def _base_explanation_classes(base: Mapping[str, object], domain: Mapping[str, object]) -> list:
    classes = []
    if domain["independent_dependency_count"] >= 2:
        classes.append("independent_convergence")
    elif domain["system_count"] <= 1:
        classes.append("single_system_support")

    features = [
        item
        for item in base["evaluated_features"]
        if item.get("primary_domain") == domain["primary_domain"] and item.get("eligible") is True
    ]
    target_features = [item for item in features if item.get("can_open_domain") is True]
    modifiers = [item for item in features if item.get("role") == "modifier"]
    if target_features and modifiers:
        classes.extend(["target_with_background_modifier", "background_modifier"])
    if target_features and all(item.get("maturity") == "experimental" for item in target_features):
        classes.append("experimental_only")
    return classes


def _validate_locked_forecast(value: object, anchor: Mapping[str, object]):
    if value is None:
        return None
    if not isinstance(value, Mapping) or set(value) != _LOCKED_FORECAST_FIELDS:
        _raise("locked_forecast fields do not match the Phase 1 locked contract")
    if value.get("status") != "locked":
        _raise("locked_forecast status must be locked")
    if value.get("method_version") != METHOD_VERSION:
        _raise("locked_forecast method version is unsupported")
    digest = value.get("canonical_digest")
    if not isinstance(digest, str) or not digest:
        _raise("locked_forecast must include canonical_digest")
    body = {
        "method_version": value.get("method_version"),
        "anchor": value.get("anchor"),
        "claims": value.get("claims"),
    }
    actual = _digest(body)
    if actual != digest:
        _raise(
            "locked_forecast digest does not match payload",
            {"expected_digest": digest, "actual_digest": actual},
        )
    if _canonical_bytes(value.get("anchor")) != _canonical_bytes(anchor):
        _raise("locked_forecast anchor must equal supplied anchor")
    claims = value.get("claims")
    if not isinstance(claims, list) or any(not isinstance(item, Mapping) for item in claims):
        _raise("locked_forecast claims must be a list of mappings")
    boundaries = []
    required = {
        "claim_id",
        "forecast_window",
        "primary_domain",
        "event_family",
        "contamination_state",
        "evaluation_eligibility",
        "method_version",
    }
    for claim in claims:
        if not required.issubset(claim):
            _raise("locked forecast claim is missing structural identity fields")
        if claim.get("method_version") != METHOD_VERSION:
            _raise("locked forecast claim method version is unsupported")
        boundaries.append(
            {
                "claim_id": claim["claim_id"],
                "forecast_window": claim["forecast_window"],
                "primary_domain": claim["primary_domain"],
                "event_family": claim["event_family"],
                "contamination_state": claim["contamination_state"],
                "evaluation_eligibility": claim["evaluation_eligibility"],
                "method_version": claim["method_version"],
                "locked_forecast_digest": digest,
            }
        )
    return {"digest": digest, "boundaries": boundaries}


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
    """Build the deterministic interpretation boundary without rewriting authority."""

    base = _validate_base_ranking(base_ranking)
    resolved_anchor = _validate_anchor(anchor)
    personalized = _validate_personalization(personalization, base)
    windows = _validate_local_windows(local_windows, base)
    locked = _validate_locked_forecast(locked_forecast, resolved_anchor)

    windows_by_domain = {}
    for window in windows:
        windows_by_domain.setdefault(window["primary_domain"], []).append(window)

    base_by_domain = {row["primary_domain"]: row for row in base["domains"]}
    if personalized is not None and personalized["status"] == "applied":
        presentation_order = sorted(
            base["opened_domains"],
            key=lambda domain_id: personalized["domains"][domain_id]["personalized_rank"],
        )
    else:
        presentation_order = list(base["opened_domains"])

    domain_rows = []
    for presentation_rank, domain_id in enumerate(presentation_order, start=1):
        domain = base_by_domain[domain_id]
        personal_row = None if personalized is None else personalized["domains"][domain_id]
        classes = _base_explanation_classes(base, domain)
        applicable_windows = windows_by_domain.get(domain_id, [])
        for window in applicable_windows:
            classes.append(window["window_type"])
        if personal_row is not None:
            history_class = _historical_explanation(personal_row["historical_support_class"])
            if history_class is not None:
                classes.append(history_class)

        effective_candidates = [domain["allowed_specificity"]]
        effective_candidates.extend(window["allowed_specificity"] for window in applicable_windows)
        effective_specificity = _most_conservative(effective_candidates)

        family_order = (
            list(domain["event_families"])
            if personal_row is None
            else list(personal_row["personalized_event_family_order"])
        )
        preferred = [] if personal_row is None else list(personal_row["preferred_event_families"])
        deprioritized = [] if personal_row is None else list(personal_row["deprioritized_event_families"])
        classes = [item for item in _EXPLANATION_CLASSES if item in set(classes)]

        domain_rows.append(
            {
                "primary_domain": domain_id,
                "base_rank": domain["rank"],
                "presentation_rank": presentation_rank,
                "personalization_applied": personalized is not None and personalized["status"] == "applied",
                "base_allowed_specificity": domain["allowed_specificity"],
                "effective_specificity": effective_specificity,
                "event_family_candidates": list(domain["event_families"]),
                "personalized_event_family_order": family_order,
                "preferred_event_families": preferred,
                "deprioritized_event_families": deprioritized,
                "evidence_explanation_classes": classes,
            }
        )

    presentation_domains = [row["primary_domain"] for row in domain_rows]
    result = {
        "profile_version": INTERPRETATION_PROFILE_VERSION,
        "target_scope": base["target_scope"],
        "knowledge_cutoff_at": resolved_anchor["knowledge_cutoff_at"],
        "prospective_window_start": resolved_anchor["prospective_window_start"],
        "prospective_window_end": resolved_anchor["prospective_window_end"],
        "base_ranking_digest": base["ranking_digest"],
        "personalization_digest": None if personalized is None else personalized["digest"],
        "personalization_status": "not_provided" if personalized is None else personalized["status"],
        "primary_domains": presentation_domains[:PRIMARY_DOMAIN_DISPLAY_LIMIT],
        "secondary_domains": presentation_domains[PRIMARY_DOMAIN_DISPLAY_LIMIT:],
        "domain_interpretation": domain_rows,
        "local_windows": windows,
        "specificity_ceiling": _specificity_ceiling(domain_rows),
        "reality_context_policy": dict(_REALITY_CONTEXT_POLICY),
        "forecast_strategy_policy": dict(_FORECAST_STRATEGY_POLICY),
        "disclosure_policy": dict(_DISCLOSURE_POLICY),
        "claim_boundaries": [] if locked is None else locked["boundaries"],
    }
    result["interpretation_contract_digest"] = _digest(result)
    return result
