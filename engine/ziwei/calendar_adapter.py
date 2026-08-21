"""Ziwei adapter for trusted Calendar Resolver context."""
from __future__ import annotations

from engine.calendar.models import CalendarContext

from .day import project_derived_ziwei_day
from .hour import project_derived_ziwei_hour
from .month import project_derived_ziwei_month


class ZiweiCalendarAdapterError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


def _ensure_usable_context(context: CalendarContext) -> None:
    if context.validation.calendar_conversion.status == "boundary_conflict":
        raise ZiweiCalendarAdapterError(
            "boundary_conflict",
            context.validation.boundary_id or "calendar boundary conflict",
        )


def _calendar_payload(context: CalendarContext) -> dict:
    return {
        "gregorian_date": context.normalized_time.gregorian_date.isoformat(),
        "lunar": {
            "year": context.lunar.year,
            "month": context.lunar.month,
            "day": context.lunar.day,
            "is_leap_month": context.lunar.is_leap_month,
        },
        "hour_branch": context.normalized_time.hour_branch,
        "calendar_validation_status": context.validation.calendar_conversion.status,
        "boundary_id": context.validation.boundary_id,
        "metaphysics_day_boundary_applied": context.policies.metaphysics_day_boundary_applied,
    }


def ziwei_month_from_calendar(
    context: CalendarContext,
    birth_lunar_month: int,
    birth_hour_branch: str,
    flow_year_branch: str,
) -> dict:
    _ensure_usable_context(context)
    ziwei = project_derived_ziwei_month(
        birth_lunar_month,
        birth_hour_branch,
        flow_year_branch,
        context.lunar.month,
        context.lunar.day,
        context.lunar.is_leap_month,
    )
    return {"calendar": _calendar_payload(context), "ziwei": ziwei}


def ziwei_day_from_calendar(
    context: CalendarContext,
    birth_lunar_month: int,
    birth_hour_branch: str,
    flow_year_branch: str,
) -> dict:
    _ensure_usable_context(context)
    ziwei = project_derived_ziwei_day(
        birth_lunar_month,
        birth_hour_branch,
        flow_year_branch,
        context.lunar.month,
        context.lunar.day,
        context.lunar.is_leap_month,
    )
    return {"calendar": _calendar_payload(context), "ziwei": ziwei}


def ziwei_hour_from_calendar(
    context: CalendarContext,
    birth_lunar_month: int,
    birth_hour_branch: str,
    flow_year_branch: str,
) -> dict:
    _ensure_usable_context(context)
    ziwei = project_derived_ziwei_hour(
        birth_lunar_month,
        birth_hour_branch,
        flow_year_branch,
        context.lunar.month,
        context.lunar.day,
        context.lunar.is_leap_month,
        context.normalized_time.hour_branch,
    )
    return {"calendar": _calendar_payload(context), "ziwei": ziwei}
