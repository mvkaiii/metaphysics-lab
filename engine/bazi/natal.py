from __future__ import annotations

from datetime import datetime
from typing import Mapping, Optional

from engine.birth.models import Sex
from engine.birth.time_views import BirthTimeViews
from engine.calendar.models import CalendarContext

from .calendar import bazi_pillars
from .natal_models import BaziNatalChart, BaziNatalProfile, Pillar


class BaziNatalError(ValueError):
    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[Mapping[str, object]] = None,
    ) -> None:
        self.code = code
        self.details = dict(details or {})
        super().__init__(message)


def select_bazi_effective_datetime(
    time_views: BirthTimeViews,
    profile: BaziNatalProfile,
) -> datetime:
    if profile.effective_time_basis != "normalized_civil":
        raise BaziNatalError(
            "unsupported_bazi_time_profile",
            "Bazi natal v1 supports normalized civil time as the effective default only",
            {"effective_time_basis": profile.effective_time_basis},
        )
    return time_views.normalized_civil.local_datetime


def _pillar(value: str) -> Pillar:
    if len(value) != 2:
        raise BaziNatalError(
            "invalid_bazi_pillar",
            "existing Bazi calendar engine returned a malformed pillar",
            {"value": value},
        )
    return Pillar(value[0], value[1])


def _validation(calendar: CalendarContext) -> dict:
    calendar_status = calendar.validation.overall_status
    if calendar_status == "boundary_conflict":
        raise BaziNatalError(
            "calendar_boundary_conflict",
            "Bazi natal materialization is blocked by Calendar boundary conflict",
            {
                "boundary_id": calendar.validation.boundary_id,
                "calendar_status": calendar_status,
            },
        )
    if calendar_status == "out_of_validated_range":
        status = "unqualified_candidate"
    elif calendar_status == "boundary_caution":
        status = "qualified_with_caution"
    else:
        status = "validated"
    return {
        "status": status,
        "calendar_status": calendar_status,
        "calendar_profile": calendar.validation.calendar_conversion.profile,
        "validated_range": calendar.validation.validated_range,
        "boundary_id": calendar.validation.boundary_id,
    }


def build_bazi_natal(
    calendar: CalendarContext,
    time_views: BirthTimeViews,
    sex: Sex,
    profile: BaziNatalProfile = BaziNatalProfile(),
) -> BaziNatalChart:
    validation = _validation(calendar)
    effective = select_bazi_effective_datetime(time_views, profile)
    if effective != calendar.normalized_time.local_datetime:
        raise BaziNatalError(
            "bazi_calendar_time_mismatch",
            "Bazi effective time must match the supplied CalendarContext normalized civil time",
        )
    pillars = tuple(_pillar(value) for value in bazi_pillars(effective))
    return BaziNatalChart(
        profile=profile,
        effective_datetime=effective,
        pillars=pillars,
        day_master=pillars[2].stem,
        pillar_details=(),
        element_counts=None,
        decadal_direction=None,
        decadal_start=None,
        decadal_periods=(),
        validation=validation,
        provenance={
            "classification": "Project 原生盤面",
            "calendar_resolver_version": calendar.resolver_version,
            "bazi_calendar_engine": "Project Bazi Calendar Engine",
            "bazi_natal_profile": profile.profile_id,
            "bazi_natal_rule_version": profile.rule_version,
            "sex": sex.value,
            "pending_sections": ("pillar_details", "element_counts", "decadal_luck"),
        },
    )
