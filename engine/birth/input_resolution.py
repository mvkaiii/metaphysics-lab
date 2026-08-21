from __future__ import annotations

from datetime import date, datetime, time
from typing import Mapping, Optional, Tuple

from engine.calendar.precision import TimePrecision, assess_precision

from .errors import BirthFoundationError
from .models import (
    BirthDateInput,
    BirthInput,
    BirthInputResolution,
    BirthPlaceInput,
    BirthTimeInput,
    Sex,
)

_ALLOWED_ACTIONS = ("ask", "keep_candidates", "downgrade")
_SUPPORTED_TARGETS = ("bazi_static", "bazi_natal", "ziwei_natal")


def _parse_date(value: object) -> date:
    if not isinstance(value, str):
        raise BirthFoundationError("ambiguous_birth_date", "birth_date must be YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise BirthFoundationError(
            "ambiguous_birth_date",
            "birth_date must be a valid Gregorian YYYY-MM-DD date",
            {"value": value},
        ) from exc


def _parse_time(value: object) -> time:
    if not isinstance(value, str):
        raise BirthFoundationError("ambiguous_birth_time", "birth time must be HH:MM")
    try:
        parsed = datetime.strptime(value, "%H:%M").time()
    except ValueError as exc:
        raise BirthFoundationError(
            "ambiguous_birth_time",
            "birth time must be a valid HH:MM value",
            {"value": value},
        ) from exc
    return parsed


def _parse_sex(value: object) -> Sex:
    if not isinstance(value, str):
        raise BirthFoundationError("invalid_sex", "sex must be male or female")
    try:
        return Sex(value)
    except ValueError as exc:
        raise BirthFoundationError(
            "invalid_sex",
            "sex must be male or female",
            {"value": value},
        ) from exc


def _failure(
    *,
    missing_fields: Tuple[str, ...] = (),
    error_code: Optional[str] = None,
) -> BirthInputResolution:
    return BirthInputResolution(
        ok=False,
        input=None,
        missing_fields=missing_fields,
        error_code=error_code,
        allowed_actions=_ALLOWED_ACTIONS,
    )


def resolve_birth_input(
    payload: Mapping[str, object],
    *,
    target: str,
) -> BirthInputResolution:
    if target not in _SUPPORTED_TARGETS:
        raise ValueError("unsupported birth input target: %s" % target)

    required = ["birth_date", "birth_place"]
    if "birth_time" not in payload and "birth_time_range" not in payload:
        required.append("birth_time")
    if target in ("bazi_natal", "ziwei_natal"):
        required.insert(0, "sex")

    missing = tuple(field for field in required if payload.get(field) in (None, ""))
    if missing:
        return _failure(missing_fields=missing, error_code="missing_required_birth_field")

    try:
        birth_date = BirthDateInput(_parse_date(payload["birth_date"]), TimePrecision.DAY)
        birth_place = BirthPlaceInput(str(payload["birth_place"]))
        sex = _parse_sex(payload["sex"]) if payload.get("sex") is not None else None

        if "birth_time_range" in payload:
            raw_range = payload["birth_time_range"]
            if (
                not isinstance(raw_range, (list, tuple))
                or len(raw_range) != 2
            ):
                return _failure(error_code="ambiguous_birth_time")
            start = _parse_time(raw_range[0])
            end = _parse_time(raw_range[1])
            birth_time = BirthTimeInput(
                start,
                end,
                TimePrecision.HOUR,
                "%s-%s" % (raw_range[0], raw_range[1]),
            )
            precision = assess_precision(
                TimePrecision.HOUR,
                TimePrecision.HOUR,
                is_unique=birth_time.is_exact,
            )
            if not precision.can_execute:
                return _failure(error_code=precision.reason)
        else:
            parsed_time = _parse_time(payload["birth_time"])
            birth_time = BirthTimeInput(
                parsed_time,
                None,
                TimePrecision.HOUR,
                str(payload["birth_time"]),
            )
            precision = assess_precision(
                TimePrecision.HOUR,
                TimePrecision.HOUR,
                is_unique=True,
            )
            if not precision.can_execute:
                return _failure(error_code=precision.reason)

        birth_input = BirthInput(
            sex=sex,
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=birth_place,
            calendar_kind=str(payload.get("calendar_kind", "gregorian")),
        )
    except BirthFoundationError as exc:
        return _failure(error_code=exc.code)

    return BirthInputResolution(ok=True, input=birth_input)
