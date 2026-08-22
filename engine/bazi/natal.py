from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, Optional, Tuple

from engine.birth.models import Sex
from engine.birth.time_views import BirthTimeViews
from engine.calendar.models import CalendarContext

from .calendar import STEM_INFO, bazi_pillars, ten_god
from .natal_models import (
    BaziNatalChart,
    BaziNatalProfile,
    HiddenStem,
    Pillar,
    PillarDetail,
)

_HIDDEN_STEMS = {
    "子": ("癸",),
    "丑": ("己", "癸", "辛"),
    "寅": ("甲", "丙", "戊"),
    "卯": ("乙",),
    "辰": ("戊", "乙", "癸"),
    "巳": ("丙", "戊", "庚"),
    "午": ("丁", "己"),
    "未": ("己", "丁", "乙"),
    "申": ("庚", "壬", "戊"),
    "酉": ("辛",),
    "戌": ("戊", "辛", "丁"),
    "亥": ("壬", "甲"),
}

_BRANCH_PRIMARY_ELEMENT = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木",
    "辰": "土", "巳": "火", "午": "火", "未": "土",
    "申": "金", "酉": "金", "戌": "土", "亥": "水",
}
_COMPONENT_NAMES = ("year", "month", "day", "hour")


@dataclass(frozen=True)
class BaziTimeComparison:
    status: str
    default_pillars: Tuple[str, ...]
    true_solar_pillars: Tuple[str, ...]
    affected_components: Tuple[str, ...]
    severity: str
    error_code: Optional[str] = None


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


def hidden_stems(branch: str) -> Tuple[str, ...]:
    try:
        return _HIDDEN_STEMS[branch]
    except KeyError as exc:
        raise BaziNatalError(
            "invalid_bazi_branch",
            "unknown earthly branch for hidden stems",
            {"branch": branch},
        ) from exc


def compare_bazi_time_views(time_views: BirthTimeViews) -> BaziTimeComparison:
    default_pillars = tuple(bazi_pillars(time_views.normalized_civil.local_datetime))
    true_solar_pillars = tuple(bazi_pillars(time_views.true_solar.local_datetime))
    affected = tuple(
        component
        for component, default, solar in zip(
            _COMPONENT_NAMES,
            default_pillars,
            true_solar_pillars,
        )
        if default != solar
    )
    if not affected:
        return BaziTimeComparison(
            status="EQUIVALENT",
            default_pillars=default_pillars,
            true_solar_pillars=true_solar_pillars,
            affected_components=(),
            severity="INFO",
        )
    return BaziTimeComparison(
        status="CONFLICT",
        default_pillars=default_pillars,
        true_solar_pillars=true_solar_pillars,
        affected_components=affected,
        severity="BLOCKING",
        error_code="bazi_time_profile_conflict",
    )


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


def _pillar_detail(day_master: str, pillar: Pillar) -> PillarDetail:
    hidden = tuple(
        HiddenStem(stem, index)
        for index, stem in enumerate(hidden_stems(pillar.branch), start=1)
    )
    return PillarDetail(
        pillar=pillar,
        hidden_stems=hidden,
        stem_ten_god=ten_god(day_master, pillar.stem),
        hidden_ten_gods=tuple(ten_god(day_master, item.stem) for item in hidden),
    )


def _visible_element_counts(pillars: Tuple[Pillar, ...]) -> dict:
    counter = Counter()
    for pillar in pillars:
        counter[STEM_INFO[pillar.stem][0]] += 1
        counter[_BRANCH_PRIMARY_ELEMENT[pillar.branch]] += 1
    return {element: counter[element] for element in ("木", "火", "土", "金", "水")}


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
    day_master = pillars[2].stem
    details = tuple(_pillar_detail(day_master, pillar) for pillar in pillars)
    return BaziNatalChart(
        profile=profile,
        effective_datetime=effective,
        pillars=pillars,
        day_master=day_master,
        pillar_details=details,
        element_counts=_visible_element_counts(pillars),
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
            "element_count_basis": "visible_stems_plus_branch_primary_elements",
            "hidden_stem_basis": "fixed_branch_hidden_stems_v1",
            "pending_sections": ("decadal_luck",),
        },
    )
