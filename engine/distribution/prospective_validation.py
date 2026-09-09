"""Deterministic v1.7 validation-context classification and denominator metadata."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Mapping

from .errors import DistributionError


CLASSIFIER_VERSION = "prospective-validation-v2-exp"
QUESTION_MODES = frozenset({
    "future_forecast",
    "hidden_existing_reality",
    "retrospective_calibration",
})
KNOWLEDGE_STATES = frozenset({"unknown", "partial", "known"})
CONTEXT_CLASSES = frozenset({
    "clean_prospective",
    "conditional_prospective",
    "hidden_existing_reality",
    "retrospective_calibration",
})
_CONTEXT_INPUT_FIELDS = frozenset({
    "forecast_id",
    "locked_at",
    "knowledge_cutoff_at",
    "question_mode",
    "knowledge_state_at_lock",
    "prediction_window",
})


def _invalid(message, **details):
    return DistributionError("invalid_validation_context", message, details)


def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise _invalid("%s must be non-blank text" % field, field=field)
    return value.strip()


def _aware(value, field):
    text = _text(value, field)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise _invalid("%s must be an ISO datetime" % field, field=field) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise _invalid("%s must be timezone-aware" % field, field=field)
    return parsed


def _digest(body):
    raw = json.dumps(
        body,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def classify_validation_context(payload: Mapping[str, object]) -> dict:
    if not isinstance(payload, Mapping) or set(payload) != _CONTEXT_INPUT_FIELDS:
        keys = set(payload) if isinstance(payload, Mapping) else set()
        raise _invalid(
            "validation context fields do not match the fixed contract",
            missing_fields=sorted(_CONTEXT_INPUT_FIELDS - keys),
            unknown_fields=sorted(keys - _CONTEXT_INPUT_FIELDS),
        )

    forecast_id = _text(payload.get("forecast_id"), "forecast_id")
    locked_at = _aware(payload.get("locked_at"), "locked_at")
    cutoff = _aware(payload.get("knowledge_cutoff_at"), "knowledge_cutoff_at")
    mode = _text(payload.get("question_mode"), "question_mode")
    knowledge = _text(payload.get("knowledge_state_at_lock"), "knowledge_state_at_lock")
    if mode not in QUESTION_MODES:
        raise _invalid("unsupported question_mode", value=mode)
    if knowledge not in KNOWLEDGE_STATES:
        raise _invalid("unsupported knowledge_state_at_lock", value=knowledge)
    if locked_at < cutoff:
        raise _invalid("locked_at cannot precede knowledge_cutoff_at")

    window = payload.get("prediction_window")
    if not isinstance(window, Mapping) or set(window) != {"start", "end"}:
        raise _invalid("prediction_window must contain exactly start and end")
    start = _aware(window.get("start"), "prediction_window.start")
    end = _aware(window.get("end"), "prediction_window.end")
    if start >= end:
        raise _invalid("prediction_window.start must be earlier than prediction_window.end")

    if start <= cutoff < end:
        raise _invalid("prediction_window crosses knowledge cutoff and must be split")

    if mode == "future_forecast":
        if cutoff >= start or locked_at >= start:
            raise _invalid("future_forecast must be locked before the prediction window")
        context_class = "clean_prospective" if knowledge == "unknown" else "conditional_prospective"
        reason_code = "future_unknown_at_lock" if knowledge == "unknown" else "future_has_known_conditions"
        adjudication = end
    elif mode == "hidden_existing_reality":
        if end > cutoff or knowledge != "unknown":
            raise _invalid("hidden_existing_reality must pre-exist cutoff and remain unknown at lock")
        context_class = "hidden_existing_reality"
        reason_code = "reality_preexists_cutoff_but_hidden"
        adjudication = locked_at
    else:
        if end > cutoff:
            raise _invalid("retrospective_calibration must end on or before knowledge cutoff")
        context_class = "retrospective_calibration"
        reason_code = "historical_window_precedes_cutoff"
        adjudication = locked_at

    body = {
        "status": "classified",
        "classifier_version": CLASSIFIER_VERSION,
        "forecast_id": forecast_id,
        "locked_at": locked_at.isoformat(),
        "knowledge_cutoff_at": cutoff.isoformat(),
        "question_mode": mode,
        "knowledge_state_at_lock": knowledge,
        "prediction_window": {"start": start.isoformat(), "end": end.isoformat()},
        "context_class": context_class,
        "clean_denominator_eligible": context_class == "clean_prospective",
        "adjudication_earliest_at": adjudication.isoformat(),
        "outcome_status_at_lock": "pending",
        "reason_code": reason_code,
    }
    return {**body, "canonical_digest": _digest(body)}
