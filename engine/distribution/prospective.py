"""Deterministic prospective forecast governance primitives.

Phase 1 begins by fixing the query-time coordinate system.  This module does
not interpret metaphysical activation, rank evidence, or generate events.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Mapping
from zoneinfo import ZoneInfo

from .errors import DistributionError


_QUERY_ANCHOR_FIELDS = {
    "query_anchor_at",
    "query_timezone",
    "target_start",
    "target_end",
    "question_reference",
}


def _invalid(message: str, **details: object) -> DistributionError:
    return DistributionError("invalid_query_anchor", message, details)


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _invalid("%s must be a non-empty string" % field, field=field)
    return value.strip()


def _zone(value: object) -> tuple[str, ZoneInfo]:
    name = _text(value, "query_timezone")
    try:
        return name, ZoneInfo(name)
    except Exception as exc:
        raise _invalid("query_timezone must be a valid IANA timezone", field="query_timezone") from exc


def _valid_zone_offsets(naive: datetime, zone: ZoneInfo) -> set:
    """Return offsets whose local wall time round-trips through the zone.

    Checking both folds accepts explicit offsets for a real DST ambiguity while
    rejecting nonexistent local wall times and offsets that belong to another
    timezone.
    """
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


def resolve_query_anchor(payload: Mapping[str, object]) -> dict:
    """Resolve the knowledge cutoff and remaining prospective target window.

    The anchor is governance metadata only.  It intentionally accepts no
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
