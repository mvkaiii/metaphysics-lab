from __future__ import annotations

from engine.calendar.sexagenary import (
    is_valid_sexagenary_pair,
    lunar_year_branch,
    lunar_year_stem,
)

from .errors import ZiweiFlowingStarError
from .flowing_star_models import FlowingStarSource
from .models import LayerProvenance


DECADAL_SOURCE_PROFILE = "ziwei-decadal-common-v1"
YEARLY_SOURCE_PROFILE = "ziwei-flowing-yearly-lunar-year-v1"
FLOWING_SOURCE_RULE_VERSION = "1.0-exp"
_FINE_SCOPES = frozenset(("monthly", "daily", "hourly"))
_ALLOWED_STATUSES = frozenset(("validated", "boundary_caution"))


def _raise(code, message, details=None):
    raise ZiweiFlowingStarError(code, message, details)


def _guard_validation(status):
    if status == "boundary_conflict":
        _raise("calendar_boundary_conflict", "calendar boundary conflict blocks flowing-star source")
    if status == "out_of_validated_range":
        _raise("calendar_out_of_validated_range", "calendar source is outside validated range")
    if status not in _ALLOWED_STATUSES:
        _raise(
            "invalid_flowing_star_layer",
            "unsupported flowing-star source validation status",
            {"validation_status": status},
        )


def _project_provenance(profile_id):
    return LayerProvenance(
        "project_derived",
        "Metaphysics Lab",
        None,
        profile_id,
        FLOWING_SOURCE_RULE_VERSION,
        "engine.ziwei.flowing_star_sources",
    )


def source_from_resolved_cycle(resolution, chart_identity, expected_scope):
    if expected_scope not in _FINE_SCOPES:
        _raise(
            "unsupported_flowing_star_scope",
            "resolved-cycle adapter supports only monthly/daily/hourly",
            {"scope": expected_scope},
        )
    if getattr(resolution, "scope", None) != expected_scope:
        _raise(
            "cycle_scope_mismatch",
            "resolved-cycle scope does not match requested flowing-star scope",
            {
                "expected_scope": expected_scope,
                "source_scope": getattr(resolution, "scope", None),
            },
        )
    status = getattr(resolution, "calendar_validation_status", None)
    _guard_validation(status)
    return FlowingStarSource(
        chart_identity,
        resolution.scope,
        resolution.reference,
        resolution.heavenly_stem,
        resolution.earthly_branch,
        resolution.profile_id,
        resolution.rule_version,
        status,
        resolution.provenance,
    )


def source_from_monthly(resolution, chart_identity):
    return source_from_resolved_cycle(resolution, chart_identity, "monthly")


def source_from_daily(resolution, chart_identity):
    return source_from_resolved_cycle(resolution, chart_identity, "daily")


def source_from_hourly(resolution, chart_identity):
    return source_from_resolved_cycle(resolution, chart_identity, "hourly")


def source_from_yearly(context, chart_identity):
    status = context.validation.overall_status
    _guard_validation(status)
    lunar_year = context.lunar.year
    stem = lunar_year_stem(lunar_year)
    branch = lunar_year_branch(lunar_year)
    return FlowingStarSource(
        chart_identity,
        "yearly",
        "lunar-year:%04d" % lunar_year,
        stem,
        branch,
        YEARLY_SOURCE_PROFILE,
        FLOWING_SOURCE_RULE_VERSION,
        status,
        _project_provenance(YEARLY_SOURCE_PROFILE),
    )


def source_from_decadal(period, chart_identity):
    stem_branch = getattr(period, "stem_branch", None)
    if not isinstance(stem_branch, str) or len(stem_branch) != 2:
        _raise(
            "decadal_source_not_resolved",
            "decadal flowing-star source requires a resolved two-character stem_branch",
        )
    stem, branch = stem_branch[0], stem_branch[1]
    if not is_valid_sexagenary_pair(stem, branch):
        _raise(
            "decadal_source_not_resolved",
            "decadal stem_branch is not a legal sexagenary pair",
            {"stem_branch": stem_branch},
        )
    try:
        reference = "ziwei-decadal:%d:%d-%d:%s" % (
            period.index,
            period.age_start,
            period.age_end,
            stem_branch,
        )
    except (AttributeError, TypeError, ValueError):
        _raise(
            "decadal_source_not_resolved",
            "decadal period metadata is incomplete",
        )
    return FlowingStarSource(
        chart_identity,
        "decadal",
        reference,
        stem,
        branch,
        DECADAL_SOURCE_PROFILE,
        FLOWING_SOURCE_RULE_VERSION,
        "validated",
        _project_provenance(DECADAL_SOURCE_PROFILE),
    )
