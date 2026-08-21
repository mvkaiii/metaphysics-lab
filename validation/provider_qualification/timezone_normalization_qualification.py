#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from importlib.metadata import version
from zoneinfo import TZPATH, ZoneInfo, ZoneInfoNotFoundError

import tzdata

EXPECTED_TZDATA_VERSION = "2026.3"
EXPECTED_IANA_VERSION = "2026c"
ZHI = tuple("子丑寅卯辰巳午未申酉戌亥")


class ProbeError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class Candidate:
    local: datetime
    utc: datetime
    offset: timedelta


def hour_branch(hour: int) -> str:
    return ZHI[((hour + 1) // 2) % 12]


def parse_civil(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ProbeError("invalid_datetime", str(exc)) from exc
    if parsed.tzinfo is not None:
        raise ProbeError(
            "invalid_datetime",
            "civil_datetime must be a local wall time without an embedded UTC offset",
        )
    return parsed


def parse_offset_hint(value: str) -> timedelta:
    if len(value) != 6 or value[0] not in "+-" or value[3] != ":":
        raise ProbeError("invalid_utc_offset_hint", f"invalid offset hint: {value!r}")
    try:
        hours = int(value[1:3])
        minutes = int(value[4:6])
    except ValueError as exc:
        raise ProbeError("invalid_utc_offset_hint", f"invalid offset hint: {value!r}") from exc
    if hours > 23 or minutes > 59:
        raise ProbeError("invalid_utc_offset_hint", f"invalid offset hint: {value!r}")
    total = timedelta(hours=hours, minutes=minutes)
    return -total if value[0] == "-" else total


def offset_text(value: timedelta) -> str:
    seconds = int(value.total_seconds())
    sign = "+" if seconds >= 0 else "-"
    seconds = abs(seconds)
    hours, rem = divmod(seconds, 3600)
    minutes = rem // 60
    return f"{sign}{hours:02d}:{minutes:02d}"


def local_candidates(naive: datetime, timezone_name: str) -> list[Candidate]:
    if naive.tzinfo is not None:
        raise ProbeError("invalid_datetime", "expected naive local wall time")
    try:
        zone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ProbeError("invalid_timezone", timezone_name) from exc

    candidates: dict[tuple[datetime, timedelta], Candidate] = {}
    for fold in (0, 1):
        aware = naive.replace(tzinfo=zone, fold=fold)
        utc = aware.astimezone(timezone.utc)
        roundtrip = utc.astimezone(zone)
        if roundtrip.replace(tzinfo=None) != naive:
            continue
        if roundtrip.utcoffset() != aware.utcoffset():
            continue
        assert aware.utcoffset() is not None
        key = (utc, aware.utcoffset())
        candidates[key] = Candidate(local=aware, utc=utc, offset=aware.utcoffset())

    return sorted(candidates.values(), key=lambda item: item.utc)


def normalize(
    naive: datetime,
    timezone_name: str,
    utc_offset_hint: str | None = None,
) -> Candidate:
    candidates = local_candidates(naive, timezone_name)
    if not candidates:
        raise ProbeError("nonexistent_local_time", naive.isoformat())

    if utc_offset_hint is not None:
        wanted = parse_offset_hint(utc_offset_hint)
        matching = [candidate for candidate in candidates if candidate.offset == wanted]
        if len(matching) != 1:
            raise ProbeError(
                "invalid_utc_offset_hint",
                f"{utc_offset_hint} is not a valid offset for {naive.isoformat()} {timezone_name}",
            )
        return matching[0]

    if len(candidates) > 1:
        raise ProbeError("ambiguous_local_time", naive.isoformat())
    return candidates[0]


def expect_error(code: str, func, *args, **kwargs) -> None:
    try:
        func(*args, **kwargs)
    except ProbeError as exc:
        assert exc.code == code, f"expected {code}, got {exc.code}: {exc}"
        return
    raise AssertionError(f"expected ProbeError({code})")


def assert_unique(
    value: str,
    timezone_name: str,
    expected_offset: str,
    expected_utc: str | None = None,
) -> Candidate:
    naive = parse_civil(value)
    candidates = local_candidates(naive, timezone_name)
    assert len(candidates) == 1, (value, timezone_name, candidates)
    candidate = candidates[0]
    assert offset_text(candidate.offset) == expected_offset, (
        value,
        timezone_name,
        offset_text(candidate.offset),
        expected_offset,
    )
    if expected_utc is not None:
        assert candidate.utc.isoformat().replace("+00:00", "Z") == expected_utc
    assert candidate.utc.astimezone(candidate.local.tzinfo) == candidate.local
    return candidate


def main() -> int:
    assert version("tzdata") == EXPECTED_TZDATA_VERSION
    assert tzdata.__version__ == EXPECTED_TZDATA_VERSION
    assert tzdata.IANA_VERSION == EXPECTED_IANA_VERSION
    assert TZPATH == (), (
        "Qualification must force ZoneInfo to use the pinned tzdata package, "
        f"but TZPATH={TZPATH!r}"
    )

    checks = 0

    # 1. Asia/Taipei ordinary normalization and exact UTC conversion.
    taipei = assert_unique(
        "2026-09-18T14:00:00",
        "Asia/Taipei",
        "+08:00",
        "2026-09-18T06:00:00Z",
    )
    assert taipei.local.date().isoformat() == "2026-09-18"
    assert hour_branch(taipei.local.hour) == "未"
    checks += 1

    # 2. Civil-midnight date boundary is independent from the two-hour branch.
    boundary_cases = (
        ("2026-09-18T22:59:00", "2026-09-18", "亥"),
        ("2026-09-18T23:00:00", "2026-09-18", "子"),
        ("2026-09-18T23:59:00", "2026-09-18", "子"),
        ("2026-09-19T00:00:00", "2026-09-19", "子"),
        ("2026-09-19T00:59:00", "2026-09-19", "子"),
        ("2026-09-19T01:00:00", "2026-09-19", "丑"),
    )
    for value, expected_date, expected_branch in boundary_cases:
        candidate = assert_unique(value, "Asia/Taipei", "+08:00")
        assert candidate.local.date().isoformat() == expected_date
        assert hour_branch(candidate.local.hour) == expected_branch
        checks += 1

    # 3. Spring-forward gap must be rejected, never shifted to a nearby time.
    ny_gap = parse_civil("2026-03-08T02:30:00")
    assert local_candidates(ny_gap, "America/New_York") == []
    expect_error("nonexistent_local_time", normalize, ny_gap, "America/New_York")
    checks += 1

    # 4. Fall-back overlap must expose both valid offsets and UTC instants.
    ny_overlap = parse_civil("2026-11-01T01:30:00")
    overlap_candidates = local_candidates(ny_overlap, "America/New_York")
    assert len(overlap_candidates) == 2
    assert [offset_text(item.offset) for item in overlap_candidates] == ["-04:00", "-05:00"]
    assert [item.utc.isoformat().replace("+00:00", "Z") for item in overlap_candidates] == [
        "2026-11-01T05:30:00Z",
        "2026-11-01T06:30:00Z",
    ]
    expect_error("ambiguous_local_time", normalize, ny_overlap, "America/New_York")
    checks += 1

    # 5. utc_offset_hint resolves ambiguity; invalid hints are rejected.
    first = normalize(ny_overlap, "America/New_York", "-04:00")
    second = normalize(ny_overlap, "America/New_York", "-05:00")
    assert first.utc.isoformat().replace("+00:00", "Z") == "2026-11-01T05:30:00Z"
    assert second.utc.isoformat().replace("+00:00", "Z") == "2026-11-01T06:30:00Z"
    expect_error(
        "invalid_utc_offset_hint",
        normalize,
        ny_overlap,
        "America/New_York",
        "-06:00",
    )
    unique_ny = parse_civil("2026-07-15T12:00:00")
    expect_error(
        "invalid_utc_offset_hint",
        normalize,
        unique_ny,
        "America/New_York",
        "-05:00",
    )
    checks += 1

    # 6. Explicit cross-zone UTC round-trip checks, including DST seasons.
    roundtrip_cases = (
        ("2026-01-15T12:00:00", "America/New_York", "-05:00"),
        ("2026-07-15T12:00:00", "America/New_York", "-04:00"),
        ("2026-01-15T12:00:00", "Europe/London", "+00:00"),
        ("2026-07-15T12:00:00", "Europe/London", "+01:00"),
        ("2026-07-15T12:00:00", "Asia/Tokyo", "+09:00"),
        ("2026-01-15T12:00:00", "Australia/Sydney", "+11:00"),
        ("2026-07-15T12:00:00", "Australia/Sydney", "+10:00"),
    )
    for value, timezone_name, expected_offset in roundtrip_cases:
        candidate = assert_unique(value, timezone_name, expected_offset)
        roundtrip = candidate.utc.astimezone(ZoneInfo(timezone_name))
        assert roundtrip.replace(tzinfo=None) == parse_civil(value)
        assert roundtrip.utcoffset() == candidate.offset
        checks += 1

    # 7. Historical Asia/Taipei rules prove the provider is not a fixed +08:00 offset.
    historical_taipei = (
        ("1937-09-30T12:00:00", "+08:00"),
        ("1937-10-01T12:00:00", "+09:00"),
        ("1945-09-20T12:00:00", "+09:00"),
        ("1945-09-21T12:00:00", "+08:00"),
        ("1946-06-01T12:00:00", "+09:00"),
        ("1946-11-01T12:00:00", "+08:00"),
        ("1979-08-01T12:00:00", "+09:00"),
        ("1979-11-01T12:00:00", "+08:00"),
    )
    for value, expected_offset in historical_taipei:
        assert_unique(value, "Asia/Taipei", expected_offset)
        checks += 1

    # 8. Input contract errors remain explicit instead of silently guessing.
    expect_error("invalid_timezone", local_candidates, parse_civil("2026-09-18T12:00:00"), "Mars/Olympus")
    expect_error("invalid_datetime", parse_civil, "not-a-date")
    expect_error("invalid_datetime", parse_civil, "2026-09-18T12:00:00+08:00")
    expect_error("invalid_utc_offset_hint", parse_offset_hint, "UTC+8")
    checks += 4

    print(f"tzdata package version: {version('tzdata')}")
    print(f"IANA tzdb version: {tzdata.IANA_VERSION}")
    print(f"ZoneInfo TZPATH: {TZPATH!r}")
    print(f"qualification assertions/groups passed: {checks}")
    print("QUALIFICATION_PASS: timezone normalization, DST, offset-hint, UTC round-trip, and historical rules")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
