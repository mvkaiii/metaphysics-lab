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
_VERIFICATION_STATES = frozenset({"pending", "matched", "partial", "not_matched", "cannot_recall"})
_CONTEXT_OUTPUT_FIELDS = frozenset({
    "status", "classifier_version", "forecast_id", "locked_at",
    "knowledge_cutoff_at", "question_mode", "knowledge_state_at_lock",
    "prediction_window", "context_class", "clean_denominator_eligible",
    "adjudication_earliest_at", "outcome_status_at_lock", "reason_code",
    "canonical_digest",
})


def _invalid(message, **details):
    return DistributionError("invalid_validation_context", message, details)


def _invalid_summary(message, **details):
    return DistributionError("invalid_validation_summary", message, details)


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


def _verify_context(value):
    if not isinstance(value, Mapping) or set(value) != _CONTEXT_OUTPUT_FIELDS:
        raise _invalid_summary("validation_context fields do not match classifier output")
    raw = {
        "forecast_id": value["forecast_id"],
        "locked_at": value["locked_at"],
        "knowledge_cutoff_at": value["knowledge_cutoff_at"],
        "question_mode": value["question_mode"],
        "knowledge_state_at_lock": value["knowledge_state_at_lock"],
        "prediction_window": dict(value["prediction_window"]),
    }
    try:
        recomputed = classify_validation_context(raw)
    except DistributionError as exc:
        raise _invalid_summary("validation_context no longer satisfies classifier contract") from exc
    if recomputed != dict(value):
        raise _invalid_summary("validation_context digest or classified content was modified")
    return recomputed


def build_validation_summary(payload: Mapping[str, object]) -> dict:
    if not isinstance(payload, Mapping) or set(payload) != {"records"}:
        raise _invalid_summary("validation summary payload must contain exactly records")
    records = payload.get("records")
    if not isinstance(records, (list, tuple)) or not records:
        raise _invalid_summary("records must be a non-empty sequence")

    clean = {"scorable_count": 0, "matched_count": 0, "partial_count": 0, "not_matched_count": 0}
    excluded = {
        "conditional_prospective": 0,
        "hidden_existing_reality": 0,
        "retrospective_calibration": 0,
    }
    pending_count = 0
    cannot_recall_count = 0

    for index, record in enumerate(records):
        if not isinstance(record, Mapping) or set(record) != {"validation_context", "verification_state"}:
            raise _invalid_summary("each record must contain validation_context and verification_state", record_index=index)
        context = _verify_context(record.get("validation_context"))
        state = record.get("verification_state")
        if state not in _VERIFICATION_STATES:
            raise _invalid_summary("unsupported verification_state", record_index=index, verification_state=state)
        if state == "pending":
            pending_count += 1
            continue
        if state == "cannot_recall":
            cannot_recall_count += 1
            continue
        if context["context_class"] != "clean_prospective":
            excluded[context["context_class"]] += 1
            continue
        if context["clean_denominator_eligible"] is not True:
            raise _invalid_summary("clean context must explicitly be denominator eligible", record_index=index)
        clean["scorable_count"] += 1
        clean[state + "_count"] += 1

    return {
        "status": "validation_summary",
        "clean_denominator": clean,
        "excluded_context_counts": excluded,
        "pending_count": pending_count,
        "cannot_recall_count": cannot_recall_count,
        "accuracy_rate": None,
        "superiority_claim_status": "not_established",
    }
