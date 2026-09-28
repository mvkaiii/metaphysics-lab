"""Pilot-4 deterministic complete window-to-structural-snapshot enumerator.

This research-only module fixes the temporal snapshot census before any Pilot-4
case exposure.  It does not inspect EFA children, claim IDs, rankings, outcomes,
or adjudication material.

The enumerator is intentionally a superset partition over every authoritative
boundary that can change the frozen yearly/monthly structural interpretation
path:

* Project Bazi Jie boundaries (flow-year / flow-month changes);
* entry/exit of the Project Bazi +/-15 minute boundary-warning interval;
* stored Project Bazi decadal start/end boundaries;
* local-civil-midnight changes in the Project Ziwei yearly/monthly calendar
  source signature (including lunar-year/month changes, leap-month split, and
  calendar validation-status changes).

No adjacent segments are merged after case exposure, even when their later
structural-state digests happen to be equal.  Every enumerated segment must be
represented exactly once in the pre-EFA snapshot manifest.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from engine.bazi.calendar import (
    JIE,
    SOLAR_TERM_BOUNDARY_CAUTION_MINUTES,
    solar_term_time,
)
from engine.calendar import resolve_calendar
from engine.ziwei.fine_cycle_stems import resolve_month_stem
from tools.pilot3_yearly_claim_universe import (
    build_yearly_segment_snapshot_manifest,
)


STRUCTURAL_SNAPSHOT_ENUMERATION_SCHEMA = (
    "prospective-structural-snapshot-enumeration.v1"
)
STRUCTURAL_SNAPSHOT_ENUMERATION_PROFILE = (
    "lin_tianji_complete_structural_snapshot_enumerator_v1"
)
STRUCTURAL_SNAPSHOT_ENUMERATION_RULE = (
    "complete_union_of_authoritative_yearly_monthly_time_boundaries_no_post_exposure_merge"
)
SUPPORTED_TIMEZONE = "Asia/Taipei"
TARGET_SCOPE = "yearly"
TIMING_SCOPE = "monthly"
REQUESTED_SCOPES = ("yearly", "monthly")

_ENUM_FIELDS = frozenset(
    (
        "schema_version",
        "profile_version",
        "enumeration_rule",
        "window_policy_digest",
        "timezone",
        "window_start",
        "window_end",
        "target_scope",
        "timing_scope",
        "requested_scopes",
        "internal_boundary_count",
        "segment_count",
        "segments",
        "promotion_allowed",
        "enumeration_digest",
    )
)
_SEGMENT_FIELDS = frozenset(
    (
        "snapshot_index",
        "snapshot_id",
        "segment_start",
        "segment_end",
        "representative_at",
        "start_boundary_sources",
    )
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
        raise ValueError("enumeration input must contain canonical JSON values") from exc


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be a mapping")
    return value


def _sequence(value: object, label: str) -> Sequence[object]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError(f"{label} must be a sequence")
    return value


def _sha256(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(ch not in "0123456789abcdef" for ch in value)
    ):
        raise ValueError(f"{label} must be lowercase SHA-256 hex")
    return value


def _parse_local(value: object, field: str, zone: ZoneInfo) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty ISO datetime text")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be a valid ISO datetime") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include an explicit UTC offset")
    localized = parsed.astimezone(zone)
    if localized.replace(tzinfo=None) != parsed.replace(tzinfo=None):
        raise ValueError(f"{field} wall time does not match {SUPPORTED_TIMEZONE}")
    if localized.utcoffset() != parsed.utcoffset():
        raise ValueError(f"{field} UTC offset does not match {SUPPORTED_TIMEZONE}")
    return localized


def _calendar_signature(day: date, timezone_name: str) -> tuple[str, ...]:
    resolved = resolve_calendar(
        f"{day.isoformat()}T00:00:00",
        timezone_name,
    )
    if not resolved.ok or resolved.context is None:
        code = None if resolved.error is None else resolved.error.code
        raise ValueError(
            "calendar resolution failed while enumerating Ziwei month/year "
            f"boundaries: {day.isoformat()} ({code})"
        )
    context = resolved.context
    monthly = resolve_month_stem(context)
    return (
        str(context.lunar.year),
        monthly.reference,
        monthly.heavenly_stem,
        monthly.earthly_branch,
        context.validation.overall_status,
    )


def _validated_decadal_boundaries(
    periods: Sequence[Mapping[str, object]],
    zone: ZoneInfo,
) -> list[tuple[datetime, str]]:
    rows = _sequence(periods, "bazi_decadal_periods")
    if not rows:
        raise ValueError("bazi_decadal_periods must not be empty")

    parsed = []
    for position, raw in enumerate(rows):
        row = _mapping(raw, f"bazi_decadal_periods[{position}]")
        if "start_datetime" not in row or "end_datetime" not in row:
            raise ValueError(
                "every Bazi decadal period requires start_datetime and end_datetime"
            )
        start = _parse_local(
            row["start_datetime"],
            f"bazi_decadal_periods[{position}].start_datetime",
            zone,
        )
        end = _parse_local(
            row["end_datetime"],
            f"bazi_decadal_periods[{position}].end_datetime",
            zone,
        )
        if start >= end:
            raise ValueError("Bazi decadal period must have positive duration")
        parsed.append((start, end, position))

    parsed.sort(key=lambda item: (item[0], item[1], item[2]))
    previous_end = None
    for start, end, _position in parsed:
        if previous_end is not None and start < previous_end:
            raise ValueError("Bazi decadal periods must not overlap")
        previous_end = end

    result = []
    for start, end, _position in parsed:
        result.append((start, "bazi_decadal_start"))
        result.append((end, "bazi_decadal_end"))
    return result


def enumerate_structural_snapshot_segments(
    *,
    window_start: str,
    window_end: str,
    timezone_name: str,
    window_policy_digest: str,
    bazi_decadal_periods: Sequence[Mapping[str, object]],
) -> dict:
    """Enumerate the complete pre-EFA Pilot-4 structural time partition."""

    policy_digest = _sha256(window_policy_digest, "window_policy_digest")
    if timezone_name != SUPPORTED_TIMEZONE:
        raise ValueError(
            f"Pilot-4 enumeration requires timezone {SUPPORTED_TIMEZONE}"
        )
    zone = ZoneInfo(timezone_name)
    start = _parse_local(window_start, "window_start", zone)
    end = _parse_local(window_end, "window_end", zone)
    if start >= end:
        raise ValueError("window_start must be earlier than window_end")
    if start.year != end.year:
        raise ValueError("Pilot-4 enumeration requires one civil year")

    events: dict[datetime, set[str]] = {}

    def add_boundary(boundary: datetime, source: str) -> None:
        local = boundary.astimezone(zone)
        if start < local < end:
            events.setdefault(local, set()).add(source)

    # Bazi year/month authority: exact Jie boundaries plus the qualification
    # status transitions created by the +/-15 minute caution window.
    caution = timedelta(minutes=SOLAR_TERM_BOUNDARY_CAUTION_MINUTES)
    for year in range(start.year - 1, end.year + 2):
        for term_name, _lon, _month, _day in JIE:
            boundary = solar_term_time(year, term_name, zone)
            add_boundary(boundary - caution, f"bazi_boundary_warning_enter:{term_name}")
            add_boundary(boundary, f"bazi_jie:{term_name}")
            add_boundary(boundary + caution, f"bazi_boundary_warning_exit:{term_name}")

    # Stored natal decadal boundaries participate in Bazi structural features
    # even when the requested dynamic scopes are only yearly/monthly.
    for boundary, source in _validated_decadal_boundaries(
        bazi_decadal_periods,
        zone,
    ):
        add_boundary(boundary, source)

    # Ziwei yearly/monthly authority is calendar-date based.  Scan local
    # midnights and add a boundary only when the canonical source signature
    # changes.  This covers ordinary lunar month/year rollover, leap-month
    # day-16 split, and validation-status transitions without guessing dates.
    cursor = start.date() + timedelta(days=1)
    while cursor <= end.date():
        midnight = datetime(
            cursor.year,
            cursor.month,
            cursor.day,
            tzinfo=zone,
        )
        if start < midnight < end:
            previous = _calendar_signature(cursor - timedelta(days=1), timezone_name)
            current = _calendar_signature(cursor, timezone_name)
            if current != previous:
                add_boundary(midnight, "ziwei_month_year_calendar_state_change")
        cursor += timedelta(days=1)

    internal = sorted(events)
    fenceposts = [start, *internal, end]
    segments = []
    for index, (left, right) in enumerate(zip(fenceposts, fenceposts[1:])):
        if left >= right:
            raise ValueError("enumerated segment fenceposts must be strictly increasing")
        left_utc = left.astimezone(timezone.utc)
        right_utc = right.astimezone(timezone.utc)
        representative = (
            left_utc + (right_utc - left_utc) / 2
        ).astimezone(zone)
        identity = {
            "profile_version": STRUCTURAL_SNAPSHOT_ENUMERATION_PROFILE,
            "enumeration_rule": STRUCTURAL_SNAPSHOT_ENUMERATION_RULE,
            "window_policy_digest": policy_digest,
            "snapshot_index": index,
            "segment_start": left.isoformat(),
            "segment_end": right.isoformat(),
        }
        snapshot_id = "p4seg-%03d-%s" % (index, _digest(identity)[:20])
        sources = (
            ["window_start"]
            if index == 0
            else sorted(events.get(left, {"enumerated_boundary"}))
        )
        segments.append(
            {
                "snapshot_index": index,
                "snapshot_id": snapshot_id,
                "segment_start": left.isoformat(),
                "segment_end": right.isoformat(),
                "representative_at": representative.isoformat(),
                "start_boundary_sources": sources,
            }
        )

    body = {
        "schema_version": STRUCTURAL_SNAPSHOT_ENUMERATION_SCHEMA,
        "profile_version": STRUCTURAL_SNAPSHOT_ENUMERATION_PROFILE,
        "enumeration_rule": STRUCTURAL_SNAPSHOT_ENUMERATION_RULE,
        "window_policy_digest": policy_digest,
        "timezone": timezone_name,
        "window_start": start.isoformat(),
        "window_end": end.isoformat(),
        "target_scope": TARGET_SCOPE,
        "timing_scope": TIMING_SCOPE,
        "requested_scopes": list(REQUESTED_SCOPES),
        "internal_boundary_count": len(internal),
        "segment_count": len(segments),
        "segments": segments,
        "promotion_allowed": False,
    }
    return {**body, "enumeration_digest": _digest(body)}


def validate_structural_snapshot_enumeration(value: object) -> dict:
    root = _mapping(value, "enumeration")
    missing = sorted(_ENUM_FIELDS - set(root))
    unknown = sorted(set(root) - _ENUM_FIELDS)
    if missing or unknown:
        raise ValueError(
            f"enumeration fields mismatch missing={missing} unknown={unknown}"
        )
    if root["schema_version"] != STRUCTURAL_SNAPSHOT_ENUMERATION_SCHEMA:
        raise ValueError("unsupported enumeration schema_version")
    if root["profile_version"] != STRUCTURAL_SNAPSHOT_ENUMERATION_PROFILE:
        raise ValueError("unsupported enumeration profile_version")
    if root["enumeration_rule"] != STRUCTURAL_SNAPSHOT_ENUMERATION_RULE:
        raise ValueError("unsupported enumeration_rule")
    _sha256(root["window_policy_digest"], "window_policy_digest")
    if root["timezone"] != SUPPORTED_TIMEZONE:
        raise ValueError("unsupported enumeration timezone")
    if root["target_scope"] != TARGET_SCOPE or root["timing_scope"] != TIMING_SCOPE:
        raise ValueError("enumeration scope contract mismatch")
    if root["requested_scopes"] != list(REQUESTED_SCOPES):
        raise ValueError("enumeration requested_scopes mismatch")
    if root["promotion_allowed"] is not False:
        raise ValueError("promotion_allowed must be false")

    zone = ZoneInfo(SUPPORTED_TIMEZONE)
    start = _parse_local(root["window_start"], "window_start", zone)
    end = _parse_local(root["window_end"], "window_end", zone)
    raw_segments = _sequence(root["segments"], "segments")
    if not raw_segments:
        raise ValueError("enumeration must contain at least one segment")
    if root["segment_count"] != len(raw_segments):
        raise ValueError("segment_count must equal segment census")
    if root["internal_boundary_count"] != len(raw_segments) - 1:
        raise ValueError("internal_boundary_count must equal segment_count - 1")

    normalized_segments = []
    prior_end = None
    ids = []
    for index, raw in enumerate(raw_segments):
        row = _mapping(raw, f"segments[{index}]")
        missing = sorted(_SEGMENT_FIELDS - set(row))
        unknown = sorted(set(row) - _SEGMENT_FIELDS)
        if missing or unknown:
            raise ValueError(
                f"segment fields mismatch missing={missing} unknown={unknown}"
            )
        if row["snapshot_index"] != index:
            raise ValueError("snapshot_index must be contiguous")
        segment_start = _parse_local(row["segment_start"], "segment_start", zone)
        segment_end = _parse_local(row["segment_end"], "segment_end", zone)
        representative = _parse_local(
            row["representative_at"],
            "representative_at",
            zone,
        )
        if segment_start >= segment_end:
            raise ValueError("segment must have positive duration")
        if not segment_start < representative < segment_end:
            raise ValueError("representative_at must be strictly inside segment")
        if index == 0 and segment_start != start:
            raise ValueError("first segment must start at window_start")
        if prior_end is not None and segment_start != prior_end:
            raise ValueError("segments must be contiguous without gaps/overlaps")
        prior_end = segment_end
        snapshot_id = row["snapshot_id"]
        if not isinstance(snapshot_id, str) or not snapshot_id:
            raise ValueError("snapshot_id must be non-empty text")
        sources = _sequence(row["start_boundary_sources"], "start_boundary_sources")
        if not sources or any(not isinstance(item, str) or not item for item in sources):
            raise ValueError("start_boundary_sources must be non-empty strings")
        ids.append(snapshot_id)
        normalized_segments.append(dict(row))
    if prior_end != end:
        raise ValueError("last segment must end at window_end")
    if len(ids) != len(set(ids)):
        raise ValueError("snapshot_id values must be unique")

    body = {
        key: root[key]
        for key in (
            "schema_version",
            "profile_version",
            "enumeration_rule",
            "window_policy_digest",
            "timezone",
            "window_start",
            "window_end",
            "target_scope",
            "timing_scope",
            "requested_scopes",
            "internal_boundary_count",
            "segment_count",
        )
    }
    body["segments"] = normalized_segments
    body["promotion_allowed"] = False
    supplied = _sha256(root["enumeration_digest"], "enumeration_digest")
    if supplied != _digest(body):
        raise ValueError("enumeration_digest does not match canonical enumeration")
    return {**body, "enumeration_digest": supplied}


def build_snapshot_manifest_from_enumeration(
    *,
    enumeration: Mapping[str, object],
    structural_state_digests: Sequence[str],
) -> dict:
    """Bind exactly one pre-EFA structural-state digest per enumerated segment."""

    validated = validate_structural_snapshot_enumeration(enumeration)
    digests = _sequence(structural_state_digests, "structural_state_digests")
    if len(digests) != validated["segment_count"]:
        raise ValueError(
            "structural_state_digests must exactly equal enumerated segment census"
        )
    snapshots = []
    for segment, raw_digest in zip(validated["segments"], digests):
        snapshots.append(
            {
                "snapshot_index": segment["snapshot_index"],
                "snapshot_id": segment["snapshot_id"],
                "structural_state_digest": _sha256(
                    raw_digest,
                    "structural_state_digest",
                ),
            }
        )
    return build_yearly_segment_snapshot_manifest(
        window_policy_digest=validated["window_policy_digest"],
        snapshots=snapshots,
    )
