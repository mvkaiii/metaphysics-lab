from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time
from enum import Enum
from typing import Optional, Tuple

from engine.calendar.precision import TimePrecision

from .errors import BirthFoundationError


class Sex(str, Enum):
    MALE = "male"
    FEMALE = "female"


@dataclass(frozen=True)
class BirthDateInput:
    value: date
    precision: TimePrecision

    def to_dict(self) -> dict:
        return {
            "value": self.value.isoformat(),
            "precision": self.precision.name.lower(),
        }


@dataclass(frozen=True)
class BirthTimeInput:
    start: time
    end: Optional[time]
    precision: TimePrecision
    label: Optional[str]

    def __post_init__(self) -> None:
        if self.end is not None and self.end < self.start:
            raise BirthFoundationError(
                "invalid_birth_time_range",
                "birth time range must not run backwards within the same civil day",
                {"start": self.start.isoformat(), "end": self.end.isoformat()},
            )
        if self.start.second or self.start.microsecond:
            raise BirthFoundationError(
                "unsupported_birth_time_precision",
                "Phase 2C0 v1 accepts minute precision, not reported seconds",
            )
        if self.end is not None and (self.end.second or self.end.microsecond):
            raise BirthFoundationError(
                "unsupported_birth_time_precision",
                "Phase 2C0 v1 accepts minute precision, not reported seconds",
            )

    @property
    def is_exact(self) -> bool:
        return self.end is None or self.end == self.start

    def to_dict(self) -> dict:
        return {
            "start": self.start.strftime("%H:%M"),
            "end": self.end.strftime("%H:%M") if self.end is not None else None,
            "precision": self.precision.name.lower(),
            "label": self.label,
        }


@dataclass(frozen=True)
class BirthPlaceInput:
    label: str

    def __post_init__(self) -> None:
        normalized = self.label.strip()
        if not normalized:
            raise BirthFoundationError(
                "invalid_birth_place",
                "birth place label must not be blank",
            )
        object.__setattr__(self, "label", normalized)

    def to_dict(self) -> dict:
        return {"label": self.label}


@dataclass(frozen=True)
class BirthInput:
    sex: Optional[Sex]
    birth_date: BirthDateInput
    birth_time: BirthTimeInput
    birth_place: BirthPlaceInput
    calendar_kind: str = "gregorian"

    def __post_init__(self) -> None:
        if self.calendar_kind != "gregorian":
            raise BirthFoundationError(
                "unsupported_birth_calendar",
                "Phase 2C0 Mode A v1 accepts Gregorian birth dates only",
                {"calendar_kind": self.calendar_kind},
            )

    def to_dict(self) -> dict:
        return {
            "sex": self.sex.value if self.sex is not None else None,
            "birth_date": self.birth_date.to_dict(),
            "birth_time": self.birth_time.to_dict(),
            "birth_place": self.birth_place.to_dict(),
            "calendar_kind": self.calendar_kind,
        }


@dataclass(frozen=True)
class BirthInputCandidate:
    input: BirthInput
    reason: str

    def to_dict(self) -> dict:
        return {"input": self.input.to_dict(), "reason": self.reason}


@dataclass(frozen=True)
class BirthInputResolution:
    ok: bool
    input: Optional[BirthInput]
    candidates: Tuple[BirthInputCandidate, ...] = ()
    missing_fields: Tuple[str, ...] = ()
    error_code: Optional[str] = None
    allowed_actions: Tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "input": self.input.to_dict() if self.input is not None else None,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "missing_fields": list(self.missing_fields),
            "error_code": self.error_code,
            "allowed_actions": list(self.allowed_actions),
        }


@dataclass(frozen=True)
class GeocodeCandidate:
    name: str
    latitude: float
    longitude: float
    country_code: str
    raw_id: str

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "country_code": self.country_code,
            "raw_id": self.raw_id,
        }


@dataclass(frozen=True)
class ResolvedBirthPlace:
    canonical_name: str
    latitude: float
    longitude: float
    timezone: str
    provider_name: str
    provider_version: str
    resolution_status: str
    provider_reference: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "canonical_name": self.canonical_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timezone": self.timezone,
            "provider_name": self.provider_name,
            "provider_version": self.provider_version,
            "resolution_status": self.resolution_status,
            "provider_reference": self.provider_reference,
        }
