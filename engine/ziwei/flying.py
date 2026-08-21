from __future__ import annotations

from types import MappingProxyType

from .common import PALACE_NAMES, opposite_palace, validate_palace
from .errors import ZiweiPhase2AError
from .models import (
    CycleStemSource,
    FlyingEdge,
    GeometricRelation,
    NatalFlyingGraph,
    PalaceStemSource,
)
from .transformation_profiles import PROFILE_ID
from .transformations import get_transformation_set

PRESENTATION_PROFILE_ID = "astralium-compatible-v1"


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
    if transformations.heavenly_stem != source.heavenly_stem:
        raise ZiweiPhase2AError(
            "flying_source_mismatch",
            "transformation set and flying source heavenly stem mismatch",
            {
                "transformation_stem": transformations.heavenly_stem,
                "source_stem": source.heavenly_stem,
            },
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


def build_natal_flying_graph(palace_stems, star_locations, profile_id=PROFILE_ID):
    if palace_stems.chart_identity != star_locations.chart_identity:
        raise ZiweiPhase2AError(
            "chart_basis_mismatch",
            "natal indexes belong to different charts",
        )
    edges = []
    for palace in PALACE_NAMES:
        stem = palace_stems.stems[palace]
        source = PalaceStemSource(
            "palace_stem",
            palace_stems.chart_identity,
            palace,
            stem,
        )
        edges.extend(
            fly_transformations(
                get_transformation_set(stem, profile_id),
                star_locations,
                source,
            )
        )
    if len(edges) != 48:
        raise ZiweiPhase2AError(
            "invalid_palace_stem_index",
            "natal flying graph must contain exactly 48 edges",
        )
    outgoing = {palace: [] for palace in PALACE_NAMES}
    incoming = {palace: [] for palace in PALACE_NAMES}
    for edge in edges:
        outgoing[edge.source.palace].append(edge)
        incoming[edge.target_palace].append(edge)
    return NatalFlyingGraph(
        palace_stems.chart_identity,
        tuple(edges),
        MappingProxyType({key: tuple(value) for key, value in outgoing.items()}),
        MappingProxyType({key: tuple(value) for key, value in incoming.items()}),
    )


def presentation_relation(edge, profile_id=PRESENTATION_PROFILE_ID):
    if profile_id != PRESENTATION_PROFILE_ID:
        raise ZiweiPhase2AError(
            "unknown_profile",
            "unknown presentation profile",
            {"profile_id": profile_id},
        )
    mapping = {
        GeometricRelation.SAME_PALACE: "↓",
        GeometricRelation.OPPOSITE_PALACE_INCOMING: "↑",
        GeometricRelation.NORMAL: None,
        None: None,
    }
    return mapping[edge.geometric_relation]
