"""Deterministic prospective forecast governance primitives.

Phase 1 fixes the query-time coordinate system and freezes falsifiable forecast
claims before any outcome is observed. This module does not interpret
metaphysical activation, rank evidence, or generate events.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping, Sequence
from zoneinfo import ZoneInfo

from .errors import DistributionError


METHOD_VERSION = "lin_tianji_v1.5-exp"

_QUERY_ANCHOR_FIELDS = {
    "query_anchor_at",
    "query_timezone",
    "target_start",
    "target_end",
    "question_reference",
}
_RESOLVED_ANCHOR_FIELDS = {
    "query_anchor_at",
    "query_timezone",
    "knowledge_cutoff_at",
    "prospective_window_start",
    "prospective_window_end",
    "question_reference",
    "status",
}
_REQUIRED_CLAIM_FIELDS = {
    "claim_id",
    "forecast_window",
    "primary_domain",
    "event_family",
    "prediction",
    "matched_if",
    "not_matched_if",
    "evidence_layers",
    "evidence_time_scales",
    "capability_maturity",
    "confidence",
    "knowledge_cutoff_at",
    "evaluation_eligibility",
    "contamination_state",
    "method_version",
}
_OPTIONAL_CLAIM_FIELDS = {"priority", "partial_if"}
_CLAIM_FIELDS = _REQUIRED_CLAIM_FIELDS | _OPTIONAL_CLAIM_FIELDS
_OUTCOME_FIELDS = {"observed_actual", "evaluation", "failure_mode"}
_CONFIDENCE = {"high", "medium", "low"}
_PRIORITIES = {"primary", "secondary"}
_CAPABILITY_MATURITY = {"stable", "experimental"}
_CONTAMINATION_STATES = {"clean_prospective", "known_before_lock", "partially_known"}
_EVALUATION_ELIGIBILITY = {"clean_scorable", "excluded_from_clean_accuracy"}


def _invalid(message: str, **details: object) -> DistributionError:
    return DistributionError("invalid_query_anchor", message, details)


def _invalid_claim(message: str, **details: object) -> DistributionError:
    return DistributionError("invalid_forecast_claim", message, details)


def _invalid_forecast(message: str, **details: object) -> DistributionError:
    return DistributionError("invalid_prospective_forecast", message, details)


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _invalid("%s must be a non-empty string" % field, field=field)
    return value.strip()


def _claim_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _invalid_claim("%s must be a non-empty string" % field, field=field)
    return value.strip()


def _zone(value: object) -> tuple[str, ZoneInfo]:
    name = _text(value, "query_timezone")
    try:
        return name, ZoneInfo(name)
    except Exception as exc:
        raise _invalid("query_timezone must be a valid IANA timezone", field="query_timezone") from exc


def _valid_zone_offsets(naive: datetime, zone: ZoneInfo) -> set:
    """Return offsets whose local wall time round-trips through the zone."""
    offsets = set()
    for fold in (0, 1):
        candidate = naive.replace(tzinfo=zone, fold=fold)
        roundtrip = candidate.astimezone(timezone.utc).astimezone(zone)
        if roundtrip.replace(tzinfo=None) == naive:
            offsets.add(candidate.utcoffset())
    return offsets


def _aware_iso(value: object, field: str, zone: ZoneInfo) -> datetime:
    text = _text(value, field)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise _invalid("%s must be an ISO-8601 datetime" % field, field=field) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise _invalid("%s must include an explicit UTC offset" % field, field=field)

    naive = parsed.replace(tzinfo=None)
    if parsed.utcoffset() not in _valid_zone_offsets(naive, zone):
        raise _invalid(
            "%s offset does not match query_timezone at that local time" % field,
            field=field,
        )
    return parsed.astimezone(zone)


def _claim_datetime(value: object, field: str, zone: ZoneInfo) -> datetime:
    try:
        return _aware_iso(value, field, zone)
    except DistributionError as exc:
        raise _invalid_claim(str(exc), field=field) from exc


def _claim_sequence(value: object, field: str) -> list[str]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise _invalid_claim("%s must be a non-empty sequence of strings" % field, field=field)
    normalized = []
    for item in value:
        normalized.append(_claim_text(item, field))
    if not normalized:
        raise _invalid_claim("%s must not be empty" % field, field=field)
    return normalized


def _json_normalize(value: object, error_code: str) -> Any:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        return json.loads(encoded)
    except (TypeError, ValueError) as exc:
        raise DistributionError(error_code, "payload must contain only standard JSON values") from exc


def _canonical_bytes(value: object, error_code: str) -> bytes:
    normalized = _json_normalize(value, error_code)
    return json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def resolve_query_anchor(payload: Mapping[str, object]) -> dict:
    """Resolve the knowledge cutoff and remaining prospective target window.

    The anchor is governance metadata only. It intentionally accepts no
    metaphysical strength or activation inputs.
    """
    if not isinstance(payload, Mapping):
        raise _invalid("query anchor payload must be a mapping")

    keys = set(payload)
    missing = sorted(_QUERY_ANCHOR_FIELDS - keys)
    unknown = sorted(keys - _QUERY_ANCHOR_FIELDS)
    if missing or unknown:
        raise _invalid(
            "query anchor payload fields do not match the fixed contract",
            missing_fields=missing,
            unknown_fields=unknown,
        )

    timezone_name, zone = _zone(payload.get("query_timezone"))
    anchor = _aware_iso(payload.get("query_anchor_at"), "query_anchor_at", zone)
    target_start = _aware_iso(payload.get("target_start"), "target_start", zone)
    target_end = _aware_iso(payload.get("target_end"), "target_end", zone)
    question_reference = _text(payload.get("question_reference"), "question_reference")

    if target_start >= target_end:
        raise _invalid("target_start must be earlier than target_end")

    anchor_iso = anchor.isoformat()
    base = {
        "query_anchor_at": anchor_iso,
        "query_timezone": timezone_name,
        "knowledge_cutoff_at": anchor_iso,
        "question_reference": question_reference,
    }

    if anchor >= target_end:
        return {
            **base,
            "prospective_window_start": None,
            "prospective_window_end": None,
            "status": "no_prospective_window",
        }

    prospective_start = target_start if anchor < target_start else anchor + timedelta(microseconds=1)
    if prospective_start > target_end:
        return {
            **base,
            "prospective_window_start": None,
            "prospective_window_end": None,
            "status": "no_prospective_window",
        }

    return {
        **base,
        "prospective_window_start": prospective_start.isoformat(),
        "prospective_window_end": target_end.isoformat(),
        "status": "ok",
    }


def _validate_resolved_anchor(anchor: Mapping[str, object]) -> dict:
    if not isinstance(anchor, Mapping):
        raise _invalid_forecast("anchor must be a resolved query-anchor mapping")
    keys = set(anchor)
    missing = sorted(_RESOLVED_ANCHOR_FIELDS - keys)
    unknown = sorted(keys - _RESOLVED_ANCHOR_FIELDS)
    if missing or unknown:
        raise _invalid_forecast(
            "resolved anchor fields do not match the fixed contract",
            missing_fields=missing,
            unknown_fields=unknown,
        )
    if anchor.get("status") != "ok":
        raise _invalid_forecast("prospective forecast requires an active prospective window")

    try:
        timezone_name, zone = _zone(anchor.get("query_timezone"))
        query_anchor = _aware_iso(anchor.get("query_anchor_at"), "query_anchor_at", zone)
        cutoff = _aware_iso(anchor.get("knowledge_cutoff_at"), "knowledge_cutoff_at", zone)
        start = _aware_iso(anchor.get("prospective_window_start"), "prospective_window_start", zone)
        end = _aware_iso(anchor.get("prospective_window_end"), "prospective_window_end", zone)
        question_reference = _text(anchor.get("question_reference"), "question_reference")
    except DistributionError as exc:
        raise _invalid_forecast(str(exc)) from exc

    if cutoff != query_anchor:
        raise _invalid_forecast("knowledge_cutoff_at must equal query_anchor_at")
    if start <= cutoff or start > end:
        raise _invalid_forecast("resolved prospective window is inconsistent with the cutoff")

    return {
        "query_anchor_at": query_anchor.isoformat(),
        "query_timezone": timezone_name,
        "knowledge_cutoff_at": cutoff.isoformat(),
        "prospective_window_start": start.isoformat(),
        "prospective_window_end": end.isoformat(),
        "question_reference": question_reference,
        "status": "ok",
    }


def validate_forecast_claim(claim: Mapping[str, object], anchor: Mapping[str, object]) -> dict:
    """Validate and normalize one falsifiable pre-outcome forecast claim."""
    if not isinstance(claim, Mapping):
        raise _invalid_claim("forecast claim must be a mapping")
    if not isinstance(anchor, Mapping):
        raise _invalid_claim("anchor must be a resolved query-anchor mapping")

    keys = set(claim)
    forbidden = sorted(keys & _OUTCOME_FIELDS)
    missing = sorted(_REQUIRED_CLAIM_FIELDS - keys)
    unknown = sorted(keys - _CLAIM_FIELDS)
    if forbidden or missing or unknown:
        raise _invalid_claim(
            "forecast claim fields do not match the fixed pre-outcome contract",
            forbidden_outcome_fields=forbidden,
            missing_fields=missing,
            unknown_fields=unknown,
        )

    try:
        timezone_name, zone = _zone(anchor.get("query_timezone"))
        anchor_cutoff = _aware_iso(anchor.get("knowledge_cutoff_at"), "knowledge_cutoff_at", zone)
    except DistributionError as exc:
        raise _invalid_claim("anchor is not a valid resolved query anchor") from exc

    if anchor.get("status") != "ok":
        raise _invalid_claim("claim requires an active prospective window")

    claim_id = _claim_text(claim.get("claim_id"), "claim_id")
    primary_domain = _claim_text(claim.get("primary_domain"), "primary_domain")
    event_family = _claim_text(claim.get("event_family"), "event_family")
    prediction = _claim_text(claim.get("prediction"), "prediction")
    matched_if = _claim_text(claim.get("matched_if"), "matched_if")
    not_matched_if = _claim_text(claim.get("not_matched_if"), "not_matched_if")
    priority = None
    partial_if = None
    if "priority" in claim:
        priority = _claim_text(claim.get("priority"), "priority")
        if priority not in _PRIORITIES:
            raise _invalid_claim("unsupported priority", value=priority)
    if "partial_if" in claim:
        partial_if = _claim_text(claim.get("partial_if"), "partial_if")

    forecast_window = claim.get("forecast_window")
    if not isinstance(forecast_window, Mapping) or set(forecast_window) != {"start", "end"}:
        raise _invalid_claim("forecast_window must contain exactly start and end")
    window_start = _claim_datetime(forecast_window.get("start"), "forecast_window.start", zone)
    window_end = _claim_datetime(forecast_window.get("end"), "forecast_window.end", zone)
    if window_start >= window_end:
        raise _invalid_claim("forecast_window.start must be earlier than forecast_window.end")

    claim_cutoff = _claim_datetime(claim.get("knowledge_cutoff_at"), "knowledge_cutoff_at", zone)
    if claim_cutoff != anchor_cutoff:
        raise _invalid_claim("claim knowledge_cutoff_at must match the resolved query anchor")

    capability_maturity = _claim_text(claim.get("capability_maturity"), "capability_maturity")
    confidence = _claim_text(claim.get("confidence"), "confidence")
    contamination_state = _claim_text(claim.get("contamination_state"), "contamination_state")
    evaluation_eligibility = _claim_text(claim.get("evaluation_eligibility"), "evaluation_eligibility")
    method_version = _claim_text(claim.get("method_version"), "method_version")

    if capability_maturity not in _CAPABILITY_MATURITY:
        raise _invalid_claim("unsupported capability_maturity", value=capability_maturity)
    if confidence not in _CONFIDENCE:
        raise _invalid_claim("unsupported confidence", value=confidence)
    if contamination_state not in _CONTAMINATION_STATES:
        raise _invalid_claim("unsupported contamination_state", value=contamination_state)
    if evaluation_eligibility not in _EVALUATION_ELIGIBILITY:
        raise _invalid_claim("unsupported evaluation_eligibility", value=evaluation_eligibility)
    if method_version != METHOD_VERSION:
        raise _invalid_claim("unsupported method_version", value=method_version)

    if contamination_state == "clean_prospective" and window_start <= anchor_cutoff:
        raise _invalid_claim("clean prospective claims must begin strictly after the knowledge cutoff")
    if contamination_state in {"known_before_lock", "partially_known"} and evaluation_eligibility == "clean_scorable":
        raise _invalid_claim("known or partially known claims cannot count toward clean prospective accuracy")

    normalized = {
        "claim_id": claim_id,
        "forecast_window": {
            "start": window_start.isoformat(),
            "end": window_end.isoformat(),
        },
        "primary_domain": primary_domain,
        "event_family": event_family,
        "prediction": prediction,
        "matched_if": matched_if,
        "not_matched_if": not_matched_if,
        "evidence_layers": _claim_sequence(claim.get("evidence_layers"), "evidence_layers"),
        "evidence_time_scales": _claim_sequence(claim.get("evidence_time_scales"), "evidence_time_scales"),
        "capability_maturity": capability_maturity,
        "confidence": confidence,
        "knowledge_cutoff_at": anchor_cutoff.isoformat(),
        "evaluation_eligibility": evaluation_eligibility,
        "contamination_state": contamination_state,
        "method_version": METHOD_VERSION,
    }
    if priority is not None:
        normalized["priority"] = priority
    if partial_if is not None:
        normalized["partial_if"] = partial_if
    return _json_normalize(normalized, "invalid_forecast_claim")


def lock_prospective_forecast(payload: Mapping[str, object]) -> dict:
    """Freeze a deterministic, immutable-by-digest pre-outcome forecast record."""
    if not isinstance(payload, Mapping) or set(payload) != {"anchor", "claims"}:
        raise _invalid_forecast("prospective forecast payload must contain exactly anchor and claims")

    anchor = payload.get("anchor")
    if not isinstance(anchor, Mapping):
        raise _invalid_forecast("anchor must be a resolved query-anchor mapping")
    normalized_anchor = _validate_resolved_anchor(anchor)

    claims = payload.get("claims")
    if isinstance(claims, (str, bytes)) or not isinstance(claims, Sequence) or not claims:
        raise _invalid_forecast("claims must be a non-empty sequence")

    normalized_claims = []
    claim_ids = set()
    for claim in claims:
        if not isinstance(claim, Mapping):
            raise _invalid_forecast("each claim must be a mapping")
        try:
            normalized = validate_forecast_claim(claim, normalized_anchor)
        except DistributionError as exc:
            raise _invalid_forecast(
                "prospective forecast contains an invalid claim",
                claim_id=claim.get("claim_id"),
                claim_error=exc.code,
            ) from exc
        claim_id = normalized["claim_id"]
        if claim_id in claim_ids:
            raise _invalid_forecast("duplicate claim_id", claim_id=claim_id)
        claim_ids.add(claim_id)
        normalized_claims.append(normalized)

    enhanced = ["priority" in claim or "partial_if" in claim for claim in normalized_claims]
    if any(enhanced):
        if not all("priority" in claim and "partial_if" in claim for claim in normalized_claims):
            raise _invalid_forecast(
                "enhanced v1.5 claims must provide priority and partial_if for every claim"
            )
        primary_count = sum(claim["priority"] == "primary" for claim in normalized_claims)
        secondary_count = sum(claim["priority"] == "secondary" for claim in normalized_claims)
        if primary_count > 3 or secondary_count > 2:
            raise _invalid_forecast(
                "enhanced v1.5 claim volume exceeds the fixed 3 primary / 2 secondary boundary",
                primary_count=primary_count,
                secondary_count=secondary_count,
            )

    locked_body = {
        "method_version": METHOD_VERSION,
        "anchor": normalized_anchor,
        "claims": normalized_claims,
    }
    digest = hashlib.sha256(
        _canonical_bytes(locked_body, "invalid_prospective_forecast")
    ).hexdigest()
    return {
        "status": "locked",
        **locked_body,
        "canonical_digest": digest,
    }
