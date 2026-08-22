from __future__ import annotations

from dataclasses import replace
from hashlib import sha256

from engine.birth.models import Sex
from engine.calendar.sexagenary import lunar_year_stem

from .basis import build_palace_stem_index, build_star_location_index
from .brightness_profiles import brightness_for
from .composition import build_cycle_layer, build_layer_stack
from .flying import build_natal_flying_graph, fly_transformations
from .models import (
    ChartIdentity,
    CycleStemSource,
    LayerIdentity,
    LayerProvenance,
    NatalContext,
    PalaceStemRecord,
    StarLocationRecord,
)
from .natal_decadal import (
    build_ziwei_decadal_periods,
    resolve_decadal_direction,
    resolve_life_body_master,
)
from .natal_models import ZiweiNatalChart
from .natal_palaces import (
    resolve_five_element_bureau,
    resolve_ming_body_branches,
    resolve_palace_stems,
)
from .natal_profiles import ZiweiNatalProfile
from .natal_stars import (
    materialize_star_records,
    place_auxiliary_stars,
    place_major_stars,
    validate_transformation_star_locations,
)
from .natal_time import ZiweiBirthBasis
from .transformations import get_transformation_set


_CHART_BASIS = "project_native_ziwei_natal"


def _birth_year_branch(lunar_year: int) -> str:
    from .common import ZHI

    if not isinstance(lunar_year, int) or isinstance(lunar_year, bool):
        raise ValueError("lunar_year must be int")
    return ZHI[(lunar_year - 4) % 12]


def _chart_identity(birth_basis: ZiweiBirthBasis, sex: Sex, profile: ZiweiNatalProfile) -> ChartIdentity:
    payload = "|".join(
        (
            profile.profile_id,
            profile.rule_version,
            sex.value,
            birth_basis.effective_datetime.isoformat(),
            str(birth_basis.lunar_year),
            str(birth_basis.lunar_month),
            str(birth_basis.lunar_day),
            "1" if birth_basis.is_leap_month else "0",
            birth_basis.effective_hour_branch,
        )
    )
    digest = sha256(payload.encode("utf-8")).hexdigest()[:24]
    return ChartIdentity(
        "ziwei-natal-%s" % digest,
        _CHART_BASIS,
        profile.profile_id,
    )


def _phase2a_provenance(profile: ZiweiNatalProfile) -> LayerProvenance:
    return LayerProvenance(
        "Project 原生盤面",
        "Metaphysics Lab",
        None,
        profile.profile_id,
        profile.rule_version,
        "engine.ziwei.natal",
        ("iztro@814b77e6371e1050cac31bbf674db3c3138fcfde",),
        "public_components_qualified",
    )


def build_ziwei_natal(
    birth_basis: ZiweiBirthBasis,
    sex: Sex,
    profile: ZiweiNatalProfile = ZiweiNatalProfile(),
) -> ZiweiNatalChart:
    if not isinstance(birth_basis, ZiweiBirthBasis):
        raise ValueError("birth_basis must be ZiweiBirthBasis")
    if not isinstance(sex, Sex):
        raise ValueError("sex must be engine.birth.models.Sex")
    if not isinstance(profile, ZiweiNatalProfile):
        raise ValueError("profile must be ZiweiNatalProfile")
    if profile.time_basis != "true_solar":
        raise ValueError("Ziwei natal builder requires true-solar profile")

    calendar_status = birth_basis.validation.get("calendar_status")
    if calendar_status == "boundary_conflict":
        raise ValueError("Calendar boundary conflict blocks Ziwei natal assembly")

    birth_year_stem = lunar_year_stem(birth_basis.lunar_year)
    birth_year_branch = _birth_year_branch(birth_basis.lunar_year)

    ming_branch, body_branch = resolve_ming_body_branches(
        birth_basis.lunar_month,
        birth_basis.effective_hour_branch,
    )
    palaces = resolve_palace_stems(birth_year_stem, ming_branch)
    palace_by_branch = {record.branch: record for record in palaces}
    ming_record = palace_by_branch[ming_branch]
    body_record = palace_by_branch[body_branch]
    bureau = resolve_five_element_bureau(ming_record.heavenly_stem, ming_record.branch)

    major = place_major_stars(birth_basis.lunar_day, bureau)
    auxiliary = place_auxiliary_stars(birth_basis, birth_year_stem, profile)
    placements = major + auxiliary
    validate_transformation_star_locations(placements)

    raw_star_records = materialize_star_records(placements, palaces, profile)
    stars = tuple(
        replace(
            record,
            brightness=brightness_for(record.star, record.branch, profile.brightness_profile),
        )
        for record in raw_star_records
    )

    life_master, body_master = resolve_life_body_master(ming_branch, birth_year_branch)
    direction = resolve_decadal_direction(birth_year_stem, sex)
    decadal_periods = build_ziwei_decadal_periods(palaces, bureau, direction)

    chart_identity = _chart_identity(birth_basis, sex, profile)
    provenance = _phase2a_provenance(profile)

    star_locations = build_star_location_index(
        tuple(StarLocationRecord(record.star, record.palace) for record in stars),
        chart_identity,
        provenance,
    )
    palace_stems = build_palace_stem_index(
        tuple(PalaceStemRecord(record.name, record.heavenly_stem) for record in palaces),
        chart_identity,
        provenance,
    )
    natal_flying_graph = build_natal_flying_graph(palace_stems, star_locations)

    birth_transformations = get_transformation_set(birth_year_stem)
    birth_reference = "lunar-birth-year:%d:%s%s" % (
        birth_basis.lunar_year,
        birth_year_stem,
        birth_year_branch,
    )
    birth_source = CycleStemSource(
        "cycle_stem",
        chart_identity,
        "birth_year",
        birth_reference,
        birth_year_stem,
    )
    birth_edges = fly_transformations(birth_transformations, star_locations, birth_source)
    birth_identity = LayerIdentity(
        chart_identity.chart_id,
        "birth_year",
        birth_reference,
        birth_transformations.profile_id,
    )
    birth_year_layer = build_cycle_layer(
        birth_identity,
        birth_source,
        birth_transformations,
        birth_edges,
        birth_transformations.provenance,
        earthly_branch=birth_year_branch,
    )

    # Build the existing Phase 2A stack once as an assembly invariant. This is
    # deliberately not a parallel implementation: Phase 2A validates that all
    # indexes, graph, and birth-year layer belong to one ChartIdentity.
    natal_context = NatalContext(
        star_locations,
        palace_stems,
        natal_flying_graph,
        birth_year_layer,
    )
    build_layer_stack(chart_identity, natal_context)

    validation = dict(birth_basis.validation)
    validation.update(
        {
            "natal_structure": "validated",
            "star_location_index": star_locations.validation_status,
            "palace_stem_index": palace_stems.validation_status,
            "birth_year_layer": birth_year_layer.validation,
            "major_star_count": 14,
            "selected_auxiliary_star_count": len(auxiliary),
            "natal_flying_edge_count": len(natal_flying_graph.edges),
            "decadal_period_count": len(decadal_periods),
        }
    )
    chart_provenance = dict(birth_basis.provenance)
    chart_provenance.update(
        {
            "classification": "Project 原生盤面",
            "profile_id": profile.profile_id,
            "rule_version": profile.rule_version,
            "star_catalog": profile.star_catalog,
            "brightness_profile": profile.brightness_profile,
            "decadal_profile": profile.decadal_profile,
            "transformation_profile": birth_transformations.profile_id,
            "assembled_by": "engine.ziwei.natal",
            "public_qualification_target": "iztro@814b77e6371e1050cac31bbf674db3c3138fcfde",
        }
    )

    return ZiweiNatalChart(
        profile=profile,
        palaces=palaces,
        stars=stars,
        decadal_periods=decadal_periods,
        validation=validation,
        provenance=chart_provenance,
        chart_identity=chart_identity,
        ming_palace=ming_record.name,
        body_palace=body_record.name,
        five_element_bureau=bureau,
        life_master=life_master,
        body_master=body_master,
        birth_transformations=birth_transformations,
        natal_flying_graph=natal_flying_graph,
    )
