from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from importlib.metadata import PackageNotFoundError, version
from importlib.resources import files
from zoneinfo import ZoneInfo

import tzdata

from .models import (
    CalendarResolverException,
    NormalizedTime,
    TimezoneProviderMetadata,
)

EXPECTED_TZDATA_VERSION = "2026.3"
EXPECTED_IANA_VERSION = "2026c"
TIMEZONE_SOURCE_REVISION = "a44279419071b7aa41ebe7eca301ebb2e759571a"
TIMEZONE_PROFILE = "tzdata-2026.3-iana-2026c-v1"
ZHI = tuple("子丑寅卯辰巳午未申酉戌亥")


def hour_branch(hour: int) -> str:
    return ZHI[((hour + 1) // 2) % 12]


def _offset_text(value: timedelta) -> str:
    seconds = int(value.total_seconds())
    sign = "+" if seconds >= 0 else "-"
    seconds = abs(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes = remainder // 60
    return f"{sign}{hours:02d}:{minutes:02d}"


def _parse_offset_hint(value: str) -> timedelta:
    if len(value) != 6 or value[0] not in "+-" or value[3] != ":":
        raise CalendarResolverException(
            "invalid_utc_offset_hint",
            f"invalid utc_offset_hint: {value!r}",
            {"utc_offset_hint": value},
        )
    try:
        hours = int(value[1:3])
        minutes = int(value[4:6])
    except ValueError as exc:
        raise CalendarResolverException(
            "invalid_utc_offset_hint",
            f"invalid utc_offset_hint: {value!r}",
            {"utc_offset_hint": value},
        ) from exc
    if hours > 23 or minutes > 59:
        raise CalendarResolverException(
            "invalid_utc_offset_hint",
            f"invalid utc_offset_hint: {value!r}",
            {"utc_offset_hint": value},
        )
    offset = timedelta(hours=hours, minutes=minutes)
    return -offset if value[0] == "-" else offset


def _parse_civil(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise CalendarResolverException(
            "invalid_datetime",
            f"invalid civil_datetime: {value!r}",
            {"value": value},
        ) from exc
    if parsed.tzinfo is not None:
        raise CalendarResolverException(
            "invalid_datetime",
            "civil_datetime must not contain an embedded UTC offset",
            {"value": value},
        )
    return parsed


class PinnedTzdataProvider:
    def __init__(self) -> None:
        try:
            package_version = version("tzdata")
        except PackageNotFoundError as exc:
            raise CalendarResolverException(
                "provider_failure",
                "tzdata package is not installed",
                {"expected_version": EXPECTED_TZDATA_VERSION},
            ) from exc
        iana_version = getattr(tzdata, "IANA_VERSION", None)
        module_version = getattr(tzdata, "__version__", None)
        if (
            package_version != EXPECTED_TZDATA_VERSION
            or module_version != EXPECTED_TZDATA_VERSION
            or iana_version != EXPECTED_IANA_VERSION
        ):
            raise CalendarResolverException(
                "provider_failure",
                "tzdata provider version does not match the pinned profile",
                {
                    "expected_package_version": EXPECTED_TZDATA_VERSION,
                    "actual_package_version": package_version,
                    "actual_module_version": module_version,
                    "expected_tzdb_version": EXPECTED_IANA_VERSION,
                    "actual_tzdb_version": iana_version,
                },
            )
        self.metadata = TimezoneProviderMetadata(
            name="tzdata",
            package_version=package_version,
            tzdb_version=iana_version,
            source_revision=TIMEZONE_SOURCE_REVISION,
        )

    def zone(self, timezone_name: str) -> ZoneInfo:
        parts = timezone_name.split("/")
        if not timezone_name or any(part in ("", ".", "..") for part in parts):
            raise CalendarResolverException(
                "invalid_timezone",
                f"invalid IANA timezone: {timezone_name!r}",
                {"timezone": timezone_name},
            )
        resource = files("tzdata.zoneinfo").joinpath(*parts)
        try:
            with resource.open("rb") as handle:
                return ZoneInfo.from_file(handle, key=timezone_name)
        except (FileNotFoundError, IsADirectoryError, ValueError) as exc:
            raise CalendarResolverException(
                "invalid_timezone",
                f"unknown IANA timezone: {timezone_name!r}",
                {"timezone": timezone_name},
            ) from exc


@dataclass(frozen=True)
class _Candidate:
    local: datetime
    utc: datetime
    offset: timedelta


def _local_candidates(naive: datetime, zone: ZoneInfo) -> list[_Candidate]:
    candidates: dict[tuple[datetime, timedelta], _Candidate] = {}
    for fold in (0, 1):
        aware = naive.replace(tzinfo=zone, fold=fold)
        utc_value = aware.astimezone(timezone.utc)
        roundtrip = utc_value.astimezone(zone)
        offset = aware.utcoffset()
        if offset is None:
            continue
        if roundtrip.replace(tzinfo=None) != naive:
            continue
        if roundtrip.utcoffset() != offset:
            continue
        candidates[(utc_value, offset)] = _Candidate(aware, utc_value, offset)
    return sorted(candidates.values(), key=lambda candidate: candidate.utc)


def normalize_local_time(
    civil_datetime: str,
    timezone_name: str,
    utc_offset_hint: str | None = None,
    *,
    provider: PinnedTzdataProvider | None = None,
) -> NormalizedTime:
    naive = _parse_civil(civil_datetime)
    active_provider = provider if provider is not None else PinnedTzdataProvider()
    zone = active_provider.zone(timezone_name)
    candidates = _local_candidates(naive, zone)
    if not candidates:
        raise CalendarResolverException(
            "nonexistent_local_time",
            "local civil time does not exist in the requested timezone",
            {"civil_datetime": civil_datetime, "timezone": timezone_name},
        )
    if utc_offset_hint is not None:
        wanted = _parse_offset_hint(utc_offset_hint)
        matching = [candidate for candidate in candidates if candidate.offset == wanted]
        if len(matching) != 1:
            raise CalendarResolverException(
                "invalid_utc_offset_hint",
                "utc_offset_hint is not a legal offset for this local civil time",
                {
                    "civil_datetime": civil_datetime,
                    "timezone": timezone_name,
                    "utc_offset_hint": utc_offset_hint,
                    "candidates": [
                        {
                            "utc_offset": _offset_text(item.offset),
                            "utc_datetime": item.utc.isoformat(),
                        }
                        for item in candidates
                    ],
                },
            )
        candidate = matching[0]
    elif len(candidates) != 1:
        raise CalendarResolverException(
            "ambiguous_local_time",
            "local civil time maps to more than one UTC instant",
            {
                "civil_datetime": civil_datetime,
                "timezone": timezone_name,
                "candidates": [
                    {
                        "utc_offset": _offset_text(item.offset),
                        "utc_datetime": item.utc.isoformat(),
                    }
                    for item in candidates
                ],
            },
        )
    else:
        candidate = candidates[0]
    return NormalizedTime(
        local_datetime=candidate.local,
        utc_datetime=candidate.utc,
        utc_offset=_offset_text(candidate.offset),
        gregorian_date=candidate.local.date(),
        timezone=timezone_name,
        hour_branch=hour_branch(candidate.local.hour),
    )
