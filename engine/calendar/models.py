from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


VALIDATION_PRECEDENCE = {
    "validated": 0,
    "out_of_validated_range": 1,
    "boundary_caution": 2,
    "boundary_conflict": 3,
}


def _serialize(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_serialize(item) for item in value]
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    if hasattr(value, "to_dict"):
        return value.to_dict()
    return value


@dataclass(frozen=True)
class CalendarInput:
    civil_datetime: str
    timezone: str
    utc_offset_hint: str | None = None

    def to_dict(self) -> dict:
        payload = {
            "civil_datetime": self.civil_datetime,
            "timezone": self.timezone,
        }
        if self.utc_offset_hint is not None:
            payload["utc_offset_hint"] = self.utc_offset_hint
        return payload


@dataclass(frozen=True)
class NormalizedTime:
    local_datetime: datetime
    utc_datetime: datetime
    utc_offset: str
    gregorian_date: date
    timezone: str
    hour_branch: str

    def to_dict(self) -> dict:
        return {
            "local_datetime": self.local_datetime.isoformat(),
            "utc_datetime": self.utc_datetime.isoformat(),
            "utc_offset": self.utc_offset,
            "gregorian_date": self.gregorian_date.isoformat(),
            "timezone": self.timezone,
            "hour_branch": self.hour_branch,
        }


@dataclass(frozen=True)
class LunarDate:
    year: int
    month: int
    day: int
    is_leap_month: bool

    @classmethod
    def from_provider_values(cls, year: int, month: int, day: int) -> "LunarDate":
        return cls(year, abs(month), day, month < 0)

    def to_dict(self) -> dict:
        return {
            "year": self.year,
            "month": self.month,
            "day": self.day,
            "is_leap_month": self.is_leap_month,
        }


@dataclass(frozen=True)
class LunarProviderMetadata:
    name: str
    version: str
    source_revision: str

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "source_revision": self.source_revision,
        }


@dataclass(frozen=True)
class TimezoneProviderMetadata:
    name: str
    package_version: str
    tzdb_version: str
    source_revision: str

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "package_version": self.package_version,
            "tzdb_version": self.tzdb_version,
            "source_revision": self.source_revision,
        }


@dataclass(frozen=True)
class ProviderBundle:
    lunar_calendar: LunarProviderMetadata
    timezone_database: TimezoneProviderMetadata

    def to_dict(self) -> dict:
        return {
            "lunar_calendar": self.lunar_calendar.to_dict(),
            "timezone_database": self.timezone_database.to_dict(),
        }


@dataclass(frozen=True)
class ValidationCheck:
    status: str
    profile: str

    def to_dict(self) -> dict:
        return {"status": self.status, "profile": self.profile}


@dataclass(frozen=True)
class CalendarValidationDecision:
    check: ValidationCheck
    validated_range: str
    boundary_id: str | None
    notes: tuple[str, ...]


@dataclass(frozen=True)
class ValidationMetadata:
    calendar_conversion: ValidationCheck
    timezone_normalization: ValidationCheck
    overall_status: str
    validated_range: str
    boundary_id: str | None
    notes: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "calendar_conversion": self.calendar_conversion.to_dict(),
            "timezone_normalization": self.timezone_normalization.to_dict(),
            "overall_status": self.overall_status,
            "validated_range": self.validated_range,
            "boundary_id": self.boundary_id,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class CalendarPolicies:
    timezone_basis: str
    lunar_date_boundary: str
    hour_branch_basis: str
    metaphysics_day_boundary_applied: bool

    def to_dict(self) -> dict:
        return {
            "timezone_basis": self.timezone_basis,
            "lunar_date_boundary": self.lunar_date_boundary,
            "hour_branch_basis": self.hour_branch_basis,
            "metaphysics_day_boundary_applied": self.metaphysics_day_boundary_applied,
        }


@dataclass(frozen=True)
class CalendarContext:
    schema_version: str
    resolver_version: str
    input: CalendarInput
    normalized_time: NormalizedTime
    lunar: LunarDate
    providers: ProviderBundle
    validation: ValidationMetadata
    policies: CalendarPolicies

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "resolver_version": self.resolver_version,
            "input": self.input.to_dict(),
            "normalized_time": self.normalized_time.to_dict(),
            "lunar": self.lunar.to_dict(),
            "providers": self.providers.to_dict(),
            "validation": self.validation.to_dict(),
            "policies": self.policies.to_dict(),
        }


@dataclass(frozen=True)
class ResolverError:
    code: str
    message: str
    details: dict

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "details": _serialize(self.details),
        }


@dataclass(frozen=True)
class CalendarResolution:
    ok: bool
    context: CalendarContext | None
    error: ResolverError | None

    @classmethod
    def success(cls, context: CalendarContext) -> "CalendarResolution":
        return cls(True, context, None)

    @classmethod
    def failure(cls, error: ResolverError) -> "CalendarResolution":
        return cls(False, None, error)

    def to_dict(self) -> dict:
        if self.ok:
            if self.context is None:
                raise ValueError("successful CalendarResolution requires context")
            return {"ok": True, **self.context.to_dict()}
        if self.error is None:
            raise ValueError("failed CalendarResolution requires error")
        return {"ok": False, "error": self.error.to_dict()}


class CalendarResolverException(ValueError):
    def __init__(self, code: str, message: str, details: dict | None = None):
        self.error = ResolverError(code, message, details or {})
        super().__init__(message)


def combine_validation_status(*statuses: str) -> str:
    if not statuses:
        raise ValueError("at least one validation status is required")
    return max(statuses, key=VALIDATION_PRECEDENCE.__getitem__)
