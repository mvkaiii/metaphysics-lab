from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Mapping, Optional

from engine.birth.time_views import BirthTimeViews
from engine.calendar import resolve_calendar
from engine.calendar.models import CalendarContext, combine_validation_status
from engine.calendar.timezone import hour_branch

from .natal_profiles import ZiweiNatalProfile


class ZiweiNatalTimeError(ValueError):
    def __init__(self, code: str, message: str, details: Optional[Mapping[str, object]] = None) -> None:
        self.code = code
        self.details = dict(details or {})
        super().__init__(message)


@dataclass(frozen=True)
class ZiweiBirthBasis:
    reported_datetime: datetime
    normalized_datetime: datetime
    true_solar_datetime: datetime
    effective_datetime: datetime
    effective_hour_branch: str
    lunar_year: int
    lunar_month: int
    lunar_day: int
    is_leap_month: bool
    validation: Mapping[str, object]
    provenance: Mapping[str, object]

    def __post_init__(self) -> None:
        for field_name in (
            "reported_datetime",
            "normalized_datetime",
            "true_solar_datetime",
            "effective_datetime",
        ):
            value = getattr(self, field_name)
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError("%s must be timezone-aware" % field_name)
        object.__setattr__(self, "validation", MappingProxyType(dict(self.validation)))
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


def _offset_hint(value: datetime) -> Optional[str]:
    offset = value.utcoffset()
    if offset is None:
        return None
    total_minutes = int(offset.total_seconds() // 60)
    sign = "+" if total_minutes >= 0 else "-"
    total_minutes = abs(total_minutes)
    return "%s%02d:%02d" % (sign, total_minutes // 60, total_minutes % 60)


def _resolve_effective_calendar(calendar: CalendarContext, effective: datetime) -> CalendarContext:
    timezone_name = calendar.normalized_time.timezone
    resolution = resolve_calendar(
        effective.replace(tzinfo=None).isoformat(timespec="seconds"),
        timezone_name,
        _offset_hint(effective),
    )
    if not resolution.ok or resolution.context is None:
        error_code = resolution.error.code if resolution.error is not None else "unknown"
        raise ZiweiNatalTimeError(
            "effective_calendar_resolution_failed",
            "Ziwei true-solar effective datetime could not be resolved by Calendar Resolver",
            {"calendar_error_code": error_code},
        )
    return resolution.context


def build_ziwei_birth_basis(
    calendar: CalendarContext,
    time_views: BirthTimeViews,
    profile: ZiweiNatalProfile = ZiweiNatalProfile(),
) -> ZiweiBirthBasis:
    if profile.time_basis != "true_solar":
        raise ZiweiNatalTimeError(
            "unsupported_ziwei_time_basis",
            "Ziwei natal v1 requires the versioned true-solar time basis",
            {"time_basis": profile.time_basis},
        )

    original_status = calendar.validation.overall_status
    if original_status == "boundary_conflict":
        raise ZiweiNatalTimeError(
            "calendar_boundary_conflict",
            "Calendar boundary conflict blocks Ziwei natal materialization",
            {"calendar_status": original_status, "boundary_id": calendar.validation.boundary_id},
        )

    reported = time_views.reported_civil.local_datetime
    normalized = time_views.normalized_civil.local_datetime
    true_solar = time_views.true_solar.local_datetime
    for field_name, value in (
        ("reported", reported),
        ("normalized", normalized),
        ("true_solar", true_solar),
    ):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ZiweiNatalTimeError(
                "invalid_ziwei_time_view",
                "%s Ziwei time view must be timezone-aware" % field_name,
            )

    timezone_name = calendar.normalized_time.timezone
    if getattr(true_solar.tzinfo, "key", timezone_name) != timezone_name:
        raise ZiweiNatalTimeError(
            "ziwei_time_zone_mismatch",
            "Ziwei true-solar view must preserve the Calendar Resolver timezone",
            {"calendar_timezone": timezone_name},
        )

    effective = true_solar
    date_changed = normalized.date() != effective.date()
    normalized_branch = hour_branch(normalized.hour)
    effective_branch = hour_branch(effective.hour)
    branch_changed = normalized_branch != effective_branch

    effective_calendar = calendar
    re_resolved = False
    if date_changed:
        effective_calendar = _resolve_effective_calendar(calendar, effective)
        re_resolved = True

    effective_status = effective_calendar.validation.overall_status
    combined_status = combine_validation_status(original_status, effective_status)
    if combined_status == "boundary_conflict":
        raise ZiweiNatalTimeError(
            "calendar_boundary_conflict",
            "Effective Ziwei date falls on a Calendar boundary conflict",
            {
                "original_calendar_status": original_status,
                "effective_calendar_status": effective_status,
                "boundary_id": effective_calendar.validation.boundary_id,
            },
        )

    affected = []
    if date_changed:
        affected.append("date")
    if branch_changed:
        affected.append("hour")
    has_material_time_change = bool(affected)

    qualification_status = (
        "unqualified_candidate"
        if combined_status == "out_of_validated_range"
        else "qualified_candidate"
    )
    validation = {
        "calendar_status": combined_status,
        "original_calendar_status": original_status,
        "effective_calendar_status": effective_status,
        "qualification_status": qualification_status,
        "effective_calendar_re_resolved": re_resolved,
        "time_profile_status": "CONFLICT" if has_material_time_change else "EQUIVALENT",
        "severity": "BLOCKING" if has_material_time_change else "INFO",
        "affected_components": tuple(affected),
        "normalized_hour_branch": normalized_branch,
        "effective_hour_branch": effective_branch,
    }
    if has_material_time_change:
        validation["error_code"] = "ziwei_time_profile_conflict"

    lunar = effective_calendar.lunar
    return ZiweiBirthBasis(
        reported_datetime=reported,
        normalized_datetime=normalized,
        true_solar_datetime=true_solar,
        effective_datetime=effective,
        effective_hour_branch=effective_branch,
        lunar_year=lunar.year,
        lunar_month=lunar.month,
        lunar_day=lunar.day,
        is_leap_month=lunar.is_leap_month,
        validation=validation,
        provenance={
            "classification": "Project 原生盤面",
            "profile_id": profile.profile_id,
            "rule_version": profile.rule_version,
            "effective_time_basis": profile.time_basis,
            "time_view_profile_id": time_views.true_solar.profile_id,
            "time_view_rule_version": time_views.true_solar.rule_version,
            "calendar_resolver_version": effective_calendar.resolver_version,
            "timezone": timezone_name,
        },
    )
