from __future__ import annotations

from .common import opposite_palace, validate_palace
from .errors import ZiweiPhase2AError
from .models import CycleStemSource, FlyingEdge, GeometricRelation, PalaceStemSource


def classify_geometric_relation(source, target_palace):
    try:
        validate_palace(target_palace)
    except ValueError as exc:
        raise ZiweiPhase2AError(
            "invalid_palace",
            str(exc),
            {"palace": target_palace},
        ) from exc
    if isinstance(source, CycleStemSource):
        return None
    if not isinstance(source, PalaceStemSource):
        raise ZiweiPhase2AError("unsupported_source", "unsupported flying source")
    if source.palace == target_palace:
        return GeometricRelation.SAME_PALACE
    if source.palace == opposite_palace(target_palace):
        return GeometricRelation.OPPOSITE_PALACE_INCOMING
    return GeometricRelation.NORMAL


def fly_transformations(transformations, star_locations, source):
    if source.chart_identity != star_locations.chart_identity:
        raise ZiweiPhase2AError(
            "chart_basis_mismatch",
            "source and star index belong to different charts",
        )
    edges = []
    for item in transformations.transformations:
        if item.star not in star_locations.locations:
            raise ZiweiPhase2AError(
                "missing_star_location",
                "transformation star has no natal location",
                {"star": item.star},
            )
        target = star_locations.locations[item.star]
        edge_id = "%s:%s:%s:%s" % (
            source.kind,
            source.heavenly_stem,
            item.type.value,
            item.sequence,
        )
        edges.append(
            FlyingEdge(
                edge_id,
                source,
                source.heavenly_stem,
                item.type,
                item.star,
                target,
                "natal_star_location",
                transformations.profile_id,
                classify_geometric_relation(source, target),
                transformations.provenance,
            )
        )
    if len(edges) != 4:
        raise ZiweiPhase2AError(
            "invalid_transformation_profile",
            "flying requires exactly four transformations",
        )
    return tuple(edges)
