from __future__ import annotations

from engine.calendar.models import CalendarContext
from engine.calendar.sexagenary import five_tiger_month, lunar_year_stem

from .errors import ZiweiFineCycleError
from .models import FineCycleStemProfile, LayerProvenance, ResolvedCycleStem

FINE_CYCLE_PROFILE_ID = "ziwei-fine-cycle-lunar-late-zi-v1"
FINE_CYCLE_RULE_VERSION = "1.0-exp"
DAY_BOUNDARY_PROFILE = "late_zi_forward-v1"

DEFAULT_FINE_CYCLE_PROFILE = FineCycleStemProfile(
    FINE_CYCLE_PROFILE_ID,
    FINE_CYCLE_RULE_VERSION,
    "lunar_month",
    "split_after_day_15",
    "lunar_year",
    DAY_BOUNDARY_PROFILE,
    "effective_ziwei_day_stem",
)


def get_fine_cycle_profile(profile_id=FINE_CYCLE_PROFILE_ID):
    if profile_id != FINE_CYCLE_PROFILE_ID:
        raise ZiweiFineCycleError(
            "invalid_fine_cycle_profile",
            "unknown Ziwei fine-cycle stem profile",
            {"profile_id": profile_id},
        )
    return DEFAULT_FINE_CYCLE_PROFILE


def _ensure_usable_context(context: CalendarContext) -> None:
    if context.validation.calendar_conversion.status == "boundary_conflict":
        raise ZiweiFineCycleError(
            "calendar_context_unusable",
            "calendar conversion is in boundary conflict",
            {"boundary_id": context.validation.boundary_id},
        )
    if context.policies.metaphysics_day_boundary_applied:
        raise ZiweiFineCycleError(
            "calendar_boundary_already_applied",
            "metaphysics day boundary must be applied by the Ziwei profile exactly once",
        )


def _provenance(profile: FineCycleStemProfile) -> LayerProvenance:
    return LayerProvenance(
        "project_derived",
        "Metaphysics Lab",
        None,
        profile.profile_id,
        profile.rule_version,
        "engine.ziwei.fine_cycle_stems",
    )


def _month_reference(context: CalendarContext) -> str:
    year = context.lunar.year
    month = context.lunar.month
    day = context.lunar.day
    if not context.lunar.is_leap_month:
        return "lunar:%04d-%02d" % (year, month)
    segment = "A" if day <= 15 else "B"
    return "lunar:%04d-L%02d-%s" % (year, month, segment)


def resolve_month_stem(
    context: CalendarContext,
    profile_id: str = FINE_CYCLE_PROFILE_ID,
) -> ResolvedCycleStem:
    _ensure_usable_context(context)
    profile = get_fine_cycle_profile(profile_id)
    month = context.lunar.month
    day = context.lunar.day
    if not 1 <= month <= 12 or not 1 <= day <= 30:
        raise ZiweiFineCycleError(
            "calendar_context_unusable",
            "invalid lunar month/day in CalendarContext",
            {"lunar_month": month, "lunar_day": day},
        )
    effective_month_ordinal = month + (
        1 if context.lunar.is_leap_month and day >= 16 else 0
    )
    year_stem = lunar_year_stem(context.lunar.year)
    stem, branch = five_tiger_month(year_stem, effective_month_ordinal)
    civil_date = context.normalized_time.gregorian_date
    return ResolvedCycleStem(
        "monthly",
        _month_reference(context),
        stem,
        branch,
        profile.profile_id,
        profile.rule_version,
        civil_date,
        civil_date,
        None,
        context.validation.overall_status,
        _provenance(profile),
    )
