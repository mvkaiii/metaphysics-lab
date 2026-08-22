from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from math import cos, pi, sin
from typing import Mapping, Optional

from engine.calendar.models import CalendarContext
from engine.calendar.timezone import hour_branch

from .errors import BirthFoundationError
from .models import ResolvedBirthPlace


@dataclass(frozen=True)
class TrueSolarTimeProfile:
    profile_id: str
    rule_version: str
    longitude_correction: bool
    equation_of_time: bool


TRUE_SOLAR_NOAA_GAMMA_V1 = TrueSolarTimeProfile(
    profile_id="true-solar-noaa-gamma-v1",
    rule_version="1.0-exp",
    longitude_correction=True,
    equation_of_time=True,
)


@dataclass(frozen=True)
class TimeView:
    kind: str
    local_datetime: datetime
    adjustment_minutes: float
    profile_id: str
    rule_version: str
    calculation_basis: str
    boundary_effect: Mapping[str, object]
    provenance: Mapping[str, str]

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "local_datetime": self.local_datetime.isoformat(),
            "adjustment_minutes": self.adjustment_minutes,
            "profile_id": self.profile_id,
            "rule_version": self.rule_version,
            "calculation_basis": self.calculation_basis,
            "boundary_effect": dict(self.boundary_effect),
            "provenance": dict(self.provenance),
        }


@dataclass(frozen=True)
class BirthTimeViews:
    reported_civil: TimeView
    normalized_civil: TimeView
    true_solar: TimeView

    def to_dict(self) -> dict:
        return {
            "reported_civil": self.reported_civil.to_dict(),
            "normalized_civil": self.normalized_civil.to_dict(),
            "true_solar": self.true_solar.to_dict(),
        }


def _require_aware(dt: datetime) -> None:
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise BirthFoundationError(
            "true_solar_profile_unavailable",
            "true-solar calculation requires a timezone-aware local datetime",
        )


def equation_of_time_minutes(dt: datetime) -> float:
    _require_aware(dt)
    day_of_year = dt.timetuple().tm_yday
    decimal_hour = (
        dt.hour
        + dt.minute / 60.0
        + dt.second / 3600.0
        + dt.microsecond / 3_600_000_000.0
    )
    gamma = 2.0 * pi / 365.0 * (
        day_of_year - 1 + (decimal_hour - 12.0) / 24.0
    )
    return 229.18 * (
        0.000075
        + 0.001868 * cos(gamma)
        - 0.032077 * sin(gamma)
        - 0.014615 * cos(2.0 * gamma)
        - 0.040849 * sin(2.0 * gamma)
    )


def standard_meridian_degrees(dt: datetime) -> float:
    _require_aware(dt)
    offset = dt.utcoffset()
    if offset is None:
        raise BirthFoundationError(
            "true_solar_profile_unavailable",
            "local UTC offset is unavailable",
        )
    return offset.total_seconds() / 3600.0 * 15.0


def true_solar_adjustment_minutes(
    dt: datetime,
    longitude: float,
    profile: TrueSolarTimeProfile = TRUE_SOLAR_NOAA_GAMMA_V1,
) -> float:
    _require_aware(dt)
    adjustment = 0.0
    if profile.longitude_correction:
        adjustment += 4.0 * (longitude - standard_meridian_degrees(dt))
    if profile.equation_of_time:
        adjustment += equation_of_time_minutes(dt)
    return adjustment


def _boundary_effect(source: datetime, target: datetime) -> dict:
    source_branch = hour_branch(source.hour)
    target_branch = hour_branch(target.hour)
    return {
        "date_changed": source.date() != target.date(),
        "hour_branch_changed": source_branch != target_branch,
        "from_hour_branch": source_branch,
        "to_hour_branch": target_branch,
    }


def _civil_view(
    kind: str,
    dt: datetime,
    *,
    calendar: CalendarContext,
) -> TimeView:
    return TimeView(
        kind=kind,
        local_datetime=dt,
        adjustment_minutes=0.0,
        profile_id="civil-time-v1",
        rule_version="1.0",
        calculation_basis="reported local civil time" if kind == "reported_civil" else "IANA-normalized local civil time",
        boundary_effect=_boundary_effect(dt, dt),
        provenance={
            "calendar_resolver_version": calendar.resolver_version,
            "timezone": calendar.normalized_time.timezone,
        },
    )


def build_birth_time_views(
    calendar: CalendarContext,
    location: ResolvedBirthPlace,
    profile: TrueSolarTimeProfile = TRUE_SOLAR_NOAA_GAMMA_V1,
) -> BirthTimeViews:
    normalized = calendar.normalized_time.local_datetime
    _require_aware(normalized)
    if calendar.normalized_time.timezone != location.timezone:
        raise BirthFoundationError(
            "true_solar_profile_unavailable",
            "location timezone does not match CalendarContext timezone",
            {
                "calendar_timezone": calendar.normalized_time.timezone,
                "location_timezone": location.timezone,
            },
        )

    reported = normalized
    adjustment = true_solar_adjustment_minutes(
        normalized,
        location.longitude,
        profile,
    )
    true_solar = normalized + timedelta(minutes=adjustment)

    return BirthTimeViews(
        reported_civil=_civil_view("reported_civil", reported, calendar=calendar),
        normalized_civil=_civil_view("normalized_civil", normalized, calendar=calendar),
        true_solar=TimeView(
            kind="true_solar",
            local_datetime=true_solar,
            adjustment_minutes=adjustment,
            profile_id=profile.profile_id,
            rule_version=profile.rule_version,
            calculation_basis="longitude correction + NOAA fractional-year equation of time",
            boundary_effect=_boundary_effect(normalized, true_solar),
            provenance={
                "calendar_resolver_version": calendar.resolver_version,
                "timezone": location.timezone,
                "location_provider": location.provider_name,
                "location_provider_version": location.provider_version,
                "longitude": str(location.longitude),
            },
        ),
    )
