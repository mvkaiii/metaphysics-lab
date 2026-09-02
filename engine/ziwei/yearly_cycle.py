from __future__ import annotations

from .composition import build_cycle_layer
from .errors import ZiweiPhase2AError
from .flying import fly_transformations
from .models import CycleStemSource, LayerIdentity
from .transformation_profiles import PROFILE_ID
from .transformations import get_transformation_set


def build_yearly_cycle_layer(
    yearly_source,
    chart_identity,
    star_locations,
    transformation_profile_id=PROFILE_ID,
):
    if yearly_source.scope != "yearly":
        raise ZiweiPhase2AError(
            "unsupported_scope",
            "yearly transformation builder requires a yearly source",
            {"scope": yearly_source.scope},
        )
    if (
        yearly_source.chart_identity != chart_identity
        or star_locations.chart_identity != chart_identity
    ):
        raise ZiweiPhase2AError(
            "chart_basis_mismatch",
            "yearly transformation inputs belong to different charts",
        )

    source = CycleStemSource(
        "cycle_stem",
        chart_identity,
        "yearly",
        yearly_source.reference,
        yearly_source.heavenly_stem,
    )
    transformations = get_transformation_set(
        yearly_source.heavenly_stem,
        transformation_profile_id,
    )
    edges = fly_transformations(transformations, star_locations, source)
    identity = LayerIdentity(
        chart_identity.chart_id,
        "yearly",
        yearly_source.reference,
        transformations.profile_id,
    )
    return build_cycle_layer(
        identity,
        source,
        transformations,
        edges,
        yearly_source.provenance,
        earthly_branch=yearly_source.earthly_branch,
    )
