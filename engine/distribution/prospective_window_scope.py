"""Outcome-blind prospective-window to structural-scope governance."""

from __future__ import annotations

import calendar
import hashlib
import json
from datetime import datetime
from typing import Mapping
from zoneinfo import ZoneInfo

from .errors import DistributionError


PROSPECTIVE_WINDOW_SCOPE_SCHEMA = "v1.6-prospective-window-scope-policy.v1"
PROSPECTIVE_WINDOW_SCOPE_PROFILE = "lin_tianji_prospective_window_scope_v1"

_INPUT_FIELDS = frozenset(("window_start", "window_end", "timezone"))


def _raise(message: str, details=None) -> None:
    raise DistributionError(
        "invalid_prospective_window_scope",
        message,
        {} if details is None else dict(details),
    )


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _raise("%s must be non-empty text" % field, {"field": field})
    return value.strip()


def _zone(value: object) -> tuple[str, ZoneInfo]:
    name = _text(value, "timezone")
    try:
        return name, ZoneInfo(name)
    except Exception as exc:
        _raise("timezone must be a valid IANA timezone", {"field": "timezone"})
        raise AssertionError("unreachable") from exc


def _valid_zone_offsets(naive: datetime, zone: ZoneInfo) -> set:
    offsets = set()
    for fold in (0, 1):
        candidate = naive.replace(tzinfo=zone, fold=fold)
        roundtrip = candidate.astimezone(ZoneInfo("UTC")).astimezone(zone)
        if roundtrip.replace(tzinfo=None) == naive:
            offsets.add(candidate.utcoffset())
    return offsets


def _aware_iso(value: object, field: str, zone: ZoneInfo) -> datetime:
    text = _text(value, field)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        _raise("%s must be an ISO-8601 datetime" % field, {"field": field})
        raise AssertionError("unreachable") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        _raise("%s must include an explicit UTC offset" % field, {"field": field})

    naive = parsed.replace(tzinfo=None)
    if parsed.utcoffset() not in _valid_zone_offsets(naive, zone):
        _raise(
            "%s offset does not match timezone at that local time" % field,
            {"field": field},
        )
    return parsed.astimezone(zone)


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
        _raise("scope-policy payload must contain canonical JSON values")
        raise AssertionError("unreachable") from exc


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def resolve_prospective_window_scope(payload: Mapping[str, object]) -> dict:
    """Resolve the narrow v1 civil-time window class to existing scope authority."""

    if not isinstance(payload, Mapping):
        _raise("prospective window scope payload must be a mapping")
    keys = set(payload)
    missing = sorted(_INPUT_FIELDS - keys)
    unknown = sorted(keys - _INPUT_FIELDS)
    if missing or unknown:
        _raise(
            "prospective window scope fields do not match the fixed contract",
            {"missing_fields": missing, "unknown_fields": unknown},
        )

    timezone_name, zone = _zone(payload.get("timezone"))
    start = _aware_iso(payload.get("window_start"), "window_start", zone)
    end = _aware_iso(payload.get("window_end"), "window_end", zone)

    if start >= end:
        _raise("window_start must be earlier than window_end")
    if start.year != end.year:
        _raise("v1 supports only same-civil-year windows")
    if (start.year, start.month) == (end.year, end.month):
        _raise("v1 supports only multi-month windows")
    if start.day != 1:
        _raise("window_start must fall on the first civil day of its month")
    if end.day != calendar.monthrange(end.year, end.month)[1]:
        _raise("window_end must fall on the final civil day of its month")

    body = {
        "schema_version": PROSPECTIVE_WINDOW_SCOPE_SCHEMA,
        "policy_profile": PROSPECTIVE_WINDOW_SCOPE_PROFILE,
        "window_class": "calendar_aligned_same_year_multi_month",
        "window_start": start.isoformat(),
        "window_end": end.isoformat(),
        "timezone": timezone_name,
        "claim_target_scope": "yearly",
        "timing_scopes": ["monthly"],
        "child_opening_scope": "yearly",
        "promotion_allowed": False,
    }
    return {**body, "policy_digest": _digest(body)}
