"""Deterministic Guided Inquiry policy contract for v1.7."""
from __future__ import annotations

from typing import Mapping

from .errors import DistributionError


POLICY_VERSION = "guided_inquiry_v1"
MODES = frozenset({"entry", "post_answer"})
CASE_HEALTHS = frozenset({"PASS", "WARN", "BLOCKED"})
BLOCKING_STATES = frozenset({
    "none",
    "required_input",
    "historical_disclosure",
    "mutation_confirmation",
    "runtime_error",
    "non_metaphysics_utility",
})
TARGET_SCOPES = frozenset({"natal", "yearly", "monthly", "daily", "hourly", "decision"})
REFINEMENT_SCOPES = frozenset({"yearly", "monthly", "daily", "hourly"})
SPECIFICITIES = frozenset({"broad_domain", "event_family", "event_form"})

_INPUT_FIELDS = frozenset({
    "mode",
    "case_health",
    "user_opted_out",
    "blocking_state",
    "case_integrity_action_available",
    "pending_forecast_available",
    "current_answer",
})
_ANSWER_FIELDS = frozenset({
    "primary_domain",
    "target_scope",
    "allowed_specificity",
    "time_refinement_scopes",
    "actionable_options_present",
    "forecast_lock_eligible",
    "related_domains",
})
_SCOPE_ORDER = {"yearly": 0, "monthly": 1, "daily": 2, "hourly": 3}
_SUPPRESSION_BLOCKING_ORDER = (
    "runtime_error",
    "required_input",
    "historical_disclosure",
    "mutation_confirmation",
    "non_metaphysics_utility",
)


def _invalid(message, **details):
    return DistributionError("invalid_guided_inquiry_payload", message, details)


def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise _invalid("%s must be non-blank text" % field, field=field)
    return value.strip()


def _boolean(value, field):
    if type(value) is not bool:
        raise _invalid("%s must be boolean" % field, field=field)
    return value


def _enum(value, field, allowed):
    value = _text(value, field)
    if value not in allowed:
        raise _invalid("unsupported %s" % field, field=field, value=value)
    return value


def _text_list(value, field, *, allowed=None):
    if not isinstance(value, list):
        raise _invalid("%s must be a list" % field, field=field)
    normalized = []
    for index, item in enumerate(value):
        text = _text(item, "%s[%d]" % (field, index))
        if allowed is not None and text not in allowed:
            raise _invalid("unsupported %s value" % field, field=field, value=text)
        normalized.append(text)
    if len(normalized) != len(set(normalized)):
        raise _invalid("%s must not contain duplicates" % field, field=field)
    return normalized


def _normalize(payload):
    if not isinstance(payload, Mapping) or set(payload) != _INPUT_FIELDS:
        keys = set(payload) if isinstance(payload, Mapping) else set()
        raise _invalid(
            "guided inquiry fields do not match the fixed contract",
            missing_fields=sorted(_INPUT_FIELDS - keys),
            unknown_fields=sorted(keys - _INPUT_FIELDS),
        )

    mode = _enum(payload.get("mode"), "mode", MODES)
    case_health = _enum(payload.get("case_health"), "case_health", CASE_HEALTHS)
    blocking_state = _enum(payload.get("blocking_state"), "blocking_state", BLOCKING_STATES)
    normalized = {
        "mode": mode,
        "case_health": case_health,
        "user_opted_out": _boolean(payload.get("user_opted_out"), "user_opted_out"),
        "blocking_state": blocking_state,
        "case_integrity_action_available": _boolean(
            payload.get("case_integrity_action_available"),
            "case_integrity_action_available",
        ),
        "pending_forecast_available": _boolean(
            payload.get("pending_forecast_available"),
            "pending_forecast_available",
        ),
        "current_answer": None,
    }

    answer = payload.get("current_answer")
    if mode == "entry":
        if answer is not None:
            raise _invalid("entry mode requires current_answer to be null")
        return normalized

    if not isinstance(answer, Mapping) or set(answer) != _ANSWER_FIELDS:
        keys = set(answer) if isinstance(answer, Mapping) else set()
        raise _invalid(
            "post_answer requires the complete current_answer contract",
            missing_fields=sorted(_ANSWER_FIELDS - keys),
            unknown_fields=sorted(keys - _ANSWER_FIELDS),
        )

    primary_domain = _text(answer.get("primary_domain"), "current_answer.primary_domain")
    related_domains = _text_list(answer.get("related_domains"), "current_answer.related_domains")
    if primary_domain in related_domains:
        raise _invalid(
            "related_domains must not repeat primary_domain",
            field="current_answer.related_domains",
            value=primary_domain,
        )

    refinements = _text_list(
        answer.get("time_refinement_scopes"),
        "current_answer.time_refinement_scopes",
        allowed=REFINEMENT_SCOPES,
    )
    refinements = sorted(refinements, key=lambda value: (_SCOPE_ORDER[value], value))
    normalized["current_answer"] = {
        "primary_domain": primary_domain,
        "target_scope": _enum(answer.get("target_scope"), "current_answer.target_scope", TARGET_SCOPES),
        "allowed_specificity": _enum(
            answer.get("allowed_specificity"),
            "current_answer.allowed_specificity",
            SPECIFICITIES,
        ),
        "time_refinement_scopes": refinements,
        "actionable_options_present": _boolean(
            answer.get("actionable_options_present"),
            "current_answer.actionable_options_present",
        ),
        "forecast_lock_eligible": _boolean(
            answer.get("forecast_lock_eligible"),
            "current_answer.forecast_lock_eligible",
        ),
        "related_domains": sorted(related_domains),
    }
    return normalized


def _row(kind, domain, target_scope, requested, maximum, reason):
    return {
        "type": kind,
        "domain": domain,
        "target_scope": target_scope,
        "requested_specificity": requested,
        "max_specificity": maximum,
        "reason_code": reason,
    }


def _suppressed(reason):
    return {
        "suppressed": True,
        "suppression_reason": reason,
        "suggestions": [],
        "policy_version": POLICY_VERSION,
    }


def _suppression_reason_normalized(payload):
    if payload["user_opted_out"]:
        return "user_opted_out"
    if payload["case_health"] == "BLOCKED":
        return "case_blocked"
    for state in _SUPPRESSION_BLOCKING_ORDER:
        if payload["blocking_state"] == state:
            return state
    return None


def suppression_reason(payload: Mapping[str, object]):
    """Return the first applicable suppression reason for a valid policy payload."""
    return _suppression_reason_normalized(_normalize(payload))


def _entry_candidates(payload):
    rows = []
    if payload["case_health"] == "WARN" and payload["case_integrity_action_available"]:
        rows.append(_row("integrity", None, None, "broad_domain", "broad_domain", "case_integrity_action"))
    rows.extend([
        _row("overview", None, "yearly", "broad_domain", "broad_domain", "entry_overview"),
        _row("deep_dive", "career", "natal", "broad_domain", "broad_domain", "entry_domain_career"),
        _row("deep_dive", "finance", "natal", "broad_domain", "broad_domain", "entry_domain_finance"),
    ])
    if payload["pending_forecast_available"]:
        rows.append(_row("validation", None, None, "broad_domain", "broad_domain", "pending_forecast_tracking"))
    return rows


def _post_answer_candidates(payload):
    answer = payload["current_answer"]
    domain = answer["primary_domain"]
    scope = answer["target_scope"]
    ceiling = answer["allowed_specificity"]
    rows = [
        _row("deep_dive", domain, scope, ceiling, ceiling, "deepen_current_answer"),
    ]
    if answer["actionable_options_present"]:
        rows.append(_row("decision", domain, "decision", ceiling, ceiling, "compare_actionable_options"))
    if answer["forecast_lock_eligible"]:
        rows.append(_row("validation", domain, scope, ceiling, ceiling, "forecast_can_be_tracked"))
    if answer["time_refinement_scopes"]:
        rows.append(_row(
            "time_refine",
            domain,
            answer["time_refinement_scopes"][0],
            ceiling,
            ceiling,
            "legal_time_refinement",
        ))
    for related_domain in answer["related_domains"]:
        rows.append(_row(
            "related_domain",
            related_domain,
            scope,
            "broad_domain",
            ceiling,
            "explicit_related_domain",
        ))
    return rows


def _unique(rows):
    result = []
    seen = set()
    for row in rows:
        key = (row["type"], row["domain"], row["target_scope"])
        if key in seen:
            continue
        seen.add(key)
        result.append(row)
    return result


def suggest_inquiries(payload: Mapping[str, object]) -> dict:
    normalized = _normalize(payload)
    reason = _suppression_reason_normalized(normalized)
    if reason is not None:
        return _suppressed(reason)

    candidates = _unique(
        _entry_candidates(normalized)
        if normalized["mode"] == "entry"
        else _post_answer_candidates(normalized)
    )
    allow_fourth = normalized["mode"] == "entry" and normalized["pending_forecast_available"]
    selected = candidates[:4] if allow_fourth and len(candidates) >= 4 else candidates[:3]
    if len(selected) < 3:
        return _suppressed("insufficient_legal_suggestions")
    return {
        "suppressed": False,
        "suppression_reason": None,
        "suggestions": selected,
        "policy_version": POLICY_VERSION,
    }
