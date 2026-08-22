from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import TYPE_CHECKING, Any, Mapping, Optional

from engine.bazi.natal import build_bazi_natal, compare_bazi_time_views
from engine.birth.calendar_adapter import resolve_birth_calendar
from engine.birth.input_resolution import resolve_birth_input
from engine.birth.models import BirthInput, BirthInputResolution, ResolvedBirthPlace
from engine.birth.time_views import build_birth_time_views
from engine.ziwei.natal import build_ziwei_natal
from engine.ziwei.natal_time import build_ziwei_birth_basis

from .errors import NatalFoundationError
from .external import import_external_natal
from .models import ExternalNatalView, NatalSource, NormalizedNatalChart, ProjectNatalView
from .reconciliation import reconcile_natal

if TYPE_CHECKING:
    from engine.birth.location import LocationProvider


_PROJECT_SOURCE_VERSION = "phase2c0-exp"
_PROJECT_RULE_PROFILE = "natal-foundation-v1"
_PROJECT_RULE_VERSION = "1.0-exp"
_PILLAR_NAMES = ("year", "month", "day", "hour")


def resolve_mode_a_input(payload: Mapping[str, object]) -> BirthInputResolution:
    """Resolve Mode A input without rendering any natural-language prompt."""
    return resolve_birth_input(payload, target="ziwei_natal")


def _calendar_context(birth_input: BirthInput, location):
    resolution = resolve_birth_calendar(birth_input, location)
    if not resolution.ok or resolution.context is None:
        if resolution.error is None:
            raise NatalFoundationError(
                "calendar_resolution_failed",
                "birth calendar resolution failed without a structured error",
            )
        raise NatalFoundationError(
            resolution.error.code,
            resolution.error.message,
            resolution.error.details,
        )
    return resolution.context


def _serialize_bazi(chart) -> dict:
    pillars = {name: pillar.text for name, pillar in zip(_PILLAR_NAMES, chart.pillars)}
    details = []
    for name, detail in zip(_PILLAR_NAMES, chart.pillar_details):
        details.append({
            "component": name,
            "pillar": detail.pillar.text,
            "stem_ten_god": detail.stem_ten_god,
            "hidden_stems": [
                {"stem": hidden.stem, "weight_rank": hidden.weight_rank}
                for hidden in detail.hidden_stems
            ],
            "hidden_ten_gods": list(detail.hidden_ten_gods),
        })
    periods = [
        {
            "index": period.index,
            "pillar": period.pillar.text,
            "start_age_years": period.start_age_years,
            "end_age_years": period.end_age_years,
            "start_datetime": period.start_datetime.isoformat(),
            "end_datetime": period.end_datetime.isoformat(),
        }
        for period in chart.decadal_periods
    ]
    return {
        "pillars": pillars,
        "day_master": chart.day_master,
        "pillar_details": details,
        "element_counts": None if chart.element_counts is None else dict(chart.element_counts),
        "decadal_direction": chart.decadal_direction,
        "decadal_start": None if chart.decadal_start is None else chart.decadal_start.isoformat(),
        "decadal_periods": periods,
    }


def _serialize_ziwei(chart) -> dict:
    transformations = {}
    if chart.birth_transformations is not None:
        transformations = {
            item.type.value: item.star
            for item in chart.birth_transformations.transformations
        }
    return {
        "ming_palace": chart.ming_palace,
        "body_palace": chart.body_palace,
        "five_element_bureau": chart.five_element_bureau,
        "life_master": chart.life_master,
        "body_master": chart.body_master,
        "palaces": [
            {
                "name": palace.name,
                "branch": palace.branch,
                "heavenly_stem": palace.heavenly_stem,
                "stem_branch": palace.stem_branch,
            }
            for palace in chart.palaces
        ],
        "stars": [
            {
                "star": star.star,
                "palace": star.palace,
                "branch": star.branch,
                "category": star.category,
                "brightness": star.brightness,
                "catalog_profile": star.catalog_profile,
            }
            for star in chart.stars
        ],
        "birth_transformations": transformations,
        "decadal_cycles": [
            {
                "index": period.index,
                "palace": period.palace,
                "start_age": period.age_start,
                "end_age": period.age_end,
                "stem_branch": period.stem_branch,
                "direction": period.direction,
            }
            for period in chart.decadal_periods
        ],
    }


def _project_validation_status(calendar, ziwei_basis) -> str:
    if calendar.validation.overall_status == "out_of_validated_range":
        return "unqualified_candidate"
    return str(ziwei_basis.validation.get("qualification_status", "qualified_candidate"))


def build_project_natal(
    birth_input: BirthInput,
    location_provider: Optional["LocationProvider"] = None,
    *,
    resolved_location: Optional[ResolvedBirthPlace] = None,
) -> ProjectNatalView:
    if not isinstance(birth_input, BirthInput):
        raise NatalFoundationError("invalid_natal_input", "birth_input must be BirthInput")
    if birth_input.sex is None:
        raise NatalFoundationError(
            "missing_required_birth_field",
            "complete Project natal build requires sex",
            {"missing_fields": ("sex",)},
        )
    if location_provider is not None and resolved_location is not None:
        raise NatalFoundationError(
            "ambiguous_location_resolution",
            "provide either location_provider or resolved_location, not both",
        )
    if location_provider is None and resolved_location is None:
        raise NatalFoundationError(
            "location_resolution_required",
            "Project natal build requires location_provider or resolved_location",
        )

    if resolved_location is not None:
        if not isinstance(resolved_location, ResolvedBirthPlace):
            raise NatalFoundationError(
                "invalid_resolved_location",
                "resolved_location must be ResolvedBirthPlace",
            )
        location = resolved_location
    else:
        from engine.birth.location import resolve_birth_place

        location = resolve_birth_place(birth_input.birth_place, location_provider)

    calendar = _calendar_context(birth_input, location)
    time_views = build_birth_time_views(calendar, location)

    bazi_chart = build_bazi_natal(calendar, time_views, birth_input.sex)
    bazi_time_comparison = compare_bazi_time_views(time_views)

    ziwei_basis = build_ziwei_birth_basis(calendar, time_views)
    ziwei_chart = build_ziwei_natal(ziwei_basis, birth_input.sex)

    source = NatalSource(
        source_type="project",
        source_name="Metaphysics Lab",
        source_version=_PROJECT_SOURCE_VERSION,
        rule_profile=_PROJECT_RULE_PROFILE,
        rule_version=_PROJECT_RULE_VERSION,
        maturity="experimental",
        validation_status=_project_validation_status(calendar, ziwei_basis),
    )

    birth = {
        "sex": birth_input.sex.value,
        "reported_datetime": time_views.reported_civil.local_datetime.isoformat(),
        "place_label": birth_input.birth_place.label,
        "resolved_place_label": location.canonical_name,
        "timezone": location.timezone,
        "calendar_kind": birth_input.calendar_kind,
    }
    time_basis = {
        "reported_civil_time": time_views.reported_civil.local_datetime.isoformat(),
        "normalized_civil_time": time_views.normalized_civil.local_datetime.isoformat(),
        "true_solar_time": time_views.true_solar.local_datetime.isoformat(),
        "adjustment_minutes": time_views.true_solar.adjustment_minutes,
        "profile_id": time_views.true_solar.profile_id,
        "rule_version": time_views.true_solar.rule_version,
        "bazi_effective_time": bazi_chart.effective_datetime.isoformat(),
        "ziwei_effective_time": ziwei_basis.effective_datetime.isoformat(),
        "effective_hour_branch": ziwei_basis.effective_hour_branch,
        "bazi_time_status": bazi_time_comparison.status,
        "bazi_time_severity": bazi_time_comparison.severity,
        "ziwei_time_status": ziwei_basis.validation.get("time_profile_status"),
        "ziwei_time_severity": ziwei_basis.validation.get("severity"),
        "timezone": location.timezone,
        "location_provider": location.provider_name,
        "location_provider_version": location.provider_version,
    }

    return ProjectNatalView(
        birth=birth,
        time_basis=time_basis,
        bazi=_serialize_bazi(bazi_chart),
        ziwei=_serialize_ziwei(ziwei_chart),
        source=source,
    )


def build_bazi_imported_view(
    four_pillars_payload: Mapping[str, object],
    source: NatalSource,
) -> ExternalNatalView:
    if not isinstance(four_pillars_payload, Mapping):
        raise NatalFoundationError(
            "invalid_natal_schema",
            "four_pillars_payload must be a structured mapping",
        )
    pillars = four_pillars_payload.get("pillars")
    if pillars is None:
        pillars = four_pillars_payload
    payload = {
        "birth": {},
        "bazi": {"pillars": pillars},
        "ziwei": {},
    }
    return import_external_natal(payload, source)


def _normalized_identity(
    external: Optional[ExternalNatalView],
    project: Optional[ProjectNatalView],
) -> str:
    payload = {
        "external": None if external is None else external.to_dict(),
        "project": None if project is None else project.to_dict(),
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "natal-%s" % hashlib.sha256(encoded).hexdigest()[:24]


def build_normalized_natal(
    *,
    project: Optional[ProjectNatalView] = None,
    external: Optional[ExternalNatalView] = None,
) -> NormalizedNatalChart:
    if project is None and external is None:
        raise NatalFoundationError(
            "missing_natal_view",
            "normalized natal build requires at least one project or external view",
        )
    if project is not None and not isinstance(project, ProjectNatalView):
        raise NatalFoundationError("invalid_natal_view", "project must be ProjectNatalView or None")
    if external is not None and not isinstance(external, ExternalNatalView):
        raise NatalFoundationError("invalid_natal_view", "external must be ExternalNatalView or None")

    project_maturity = "experimental" if project is None else project.source.maturity
    resolved = reconcile_natal(
        external,
        project,
        project_maturity=project_maturity,
    )
    blocking = sum(
        1 for field in resolved.fields
        if field.status == "CONFLICT" and field.severity == "BLOCKING"
    )
    caution = sum(
        1 for field in resolved.fields
        if field.status == "CONFLICT" and field.severity == "CAUTION"
    )
    overall_status = "CONFLICT" if blocking else ("CAUTION" if caution else "resolved")

    return NormalizedNatalChart(
        identity=_normalized_identity(external, project),
        external=external,
        project=project,
        resolved=resolved,
        validation={
            "overall_status": overall_status,
            "resolved_field_count": len(resolved.fields),
            "blocking_conflict_count": blocking,
            "caution_conflict_count": caution,
        },
        provenance={
            "classification": "Normalized Natal Model",
            "reconciled_by": "engine.natal.orchestration",
            "project_source": None if project is None else project.source.source_name,
            "external_source": None if external is None else external.source.source_name,
        },
    )
