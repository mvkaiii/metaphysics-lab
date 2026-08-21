from __future__ import annotations

from .composition import build_cycle_layer
from .errors import ZiweiFineCycleError, ZiweiPhase2AError
from .fine_cycle_stems import (
    DAY_BOUNDARY_PROFILE,
    FINE_CYCLE_PROFILE_ID,
    FINE_CYCLE_RULE_VERSION,
)
from .flying import fly_transformations
from .models import CycleStemSource, LayerIdentity
from .transformation_profiles import PROFILE_ID
from .transformations import get_transformation_set

FINE_SCOPES = {"monthly", "daily", "hourly"}


def _validate_resolution(resolution):
    if resolution.scope not in FINE_SCOPES:
        raise ZiweiFineCycleError(
            "invalid_fine_cycle_scope",
            "unsupported fine-cycle scope",
            {"scope": resolution.scope},
        )
    if (
        resolution.profile_id != FINE_CYCLE_PROFILE_ID
        or resolution.rule_version != FINE_CYCLE_RULE_VERSION
    ):
        raise ZiweiFineCycleError(
            "invalid_fine_cycle_profile",
            "resolution does not use the supported fine-cycle profile",
            {
                "profile_id": resolution.profile_id,
                "rule_version": resolution.rule_version,
            },
        )
    boundary_suffix = "@" + DAY_BOUNDARY_PROFILE
    if resolution.scope == "monthly":
        valid_reference = resolution.reference.startswith("lunar:")
        if resolution.hour_branch is not None:
            valid_reference = False
    elif resolution.scope == "daily":
        valid_reference = (
            resolution.reference.startswith("ziwei-day:")
            and resolution.reference.endswith(boundary_suffix)
            and resolution.hour_branch is None
            and resolution.effective_date.isoformat() in resolution.reference
        )
    else:
        valid_reference = (
            resolution.reference.startswith("ziwei-hour:")
            and resolution.reference.endswith(boundary_suffix)
            and resolution.hour_branch == resolution.earthly_branch
            and resolution.hour_branch is not None
            and (":" + resolution.hour_branch + "@") in resolution.reference
            and resolution.effective_date.isoformat() in resolution.reference
        )
    if not valid_reference:
        raise ZiweiFineCycleError(
            "fine_cycle_reference_conflict",
            "fine-cycle scope/reference metadata is incoherent",
            {"scope": resolution.scope, "reference": resolution.reference},
        )


def build_fine_cycle_layer(
    resolution,
    chart_identity,
    star_locations,
    transformation_profile_id=PROFILE_ID,
):
    _validate_resolution(resolution)
    if star_locations.chart_identity != chart_identity:
        raise ZiweiPhase2AError(
            "chart_basis_mismatch",
            "fine-cycle chart and star index mismatch",
        )
    source = CycleStemSource(
        "cycle_stem",
        chart_identity,
        resolution.scope,
        resolution.reference,
        resolution.heavenly_stem,
    )
    transformations = get_transformation_set(
        resolution.heavenly_stem,
        transformation_profile_id,
    )
    if transformations.heavenly_stem != resolution.heavenly_stem:
        raise ZiweiFineCycleError(
            "fine_cycle_stem_mismatch",
            "resolved and transformation stems differ",
            {
                "resolved_stem": resolution.heavenly_stem,
                "transformation_stem": transformations.heavenly_stem,
            },
        )
    edges = fly_transformations(transformations, star_locations, source)
    identity = LayerIdentity(
        chart_identity.chart_id,
        resolution.scope,
        resolution.reference,
        transformations.profile_id,
    )
    return build_cycle_layer(
        identity,
        source,
        transformations,
        edges,
        resolution.provenance,
        earthly_branch=resolution.earthly_branch,
    )
