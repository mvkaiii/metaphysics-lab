from __future__ import annotations

from types import MappingProxyType

from .errors import ZiweiPhase2AError
from .models import (
    AvailabilityRecord,
    CycleTransformationLayer,
    LayerProvenance,
    TransformationOccurrence,
    ZiweiLayerStack,
)

SUPPORTED_SCOPES = {"birth_year", "decadal", "yearly", "monthly", "daily", "hourly"}
FINE_CYCLE_REASON = "fine_cycle_stem_resolver_not_enabled"
STACK_PROVENANCE = LayerProvenance(
    "project_derived",
    "Metaphysics Lab",
    None,
    None,
    "1.0",
    "engine.ziwei.composition",
)


def _raise_component_mismatch(message, details=None):
    raise ZiweiPhase2AError(
        "layer_component_mismatch",
        message,
        details,
    )


def _validate_cycle_layer_components(identity, source, transformations, flying_edges):
    if source.scope not in SUPPORTED_SCOPES:
        raise ZiweiPhase2AError(
            "unsupported_scope",
            "unsupported Ziwei transformation layer scope",
            {"scope": source.scope},
        )
    if source.chart_identity.chart_id != identity.chart_id:
        raise ZiweiPhase2AError(
            "chart_basis_mismatch",
            "layer identity and source chart mismatch",
        )
    if identity.scope != source.scope or identity.reference != source.reference:
        _raise_component_mismatch(
            "layer identity and cycle source scope/reference mismatch",
            {
                "identity_scope": identity.scope,
                "source_scope": source.scope,
                "identity_reference": identity.reference,
                "source_reference": source.reference,
            },
        )
    if identity.rule_profile != transformations.profile_id:
        _raise_component_mismatch(
            "layer identity and transformation profile mismatch",
            {
                "identity_rule_profile": identity.rule_profile,
                "transformation_profile": transformations.profile_id,
            },
        )
    if transformations.heavenly_stem != source.heavenly_stem:
        _raise_component_mismatch(
            "cycle source and transformation heavenly stem mismatch",
            {
                "source_stem": source.heavenly_stem,
                "transformation_stem": transformations.heavenly_stem,
            },
        )
    if len(transformations.transformations) != 4 or len(flying_edges) != 4:
        raise ZiweiPhase2AError(
            "invalid_transformation_profile",
            "cycle layer requires four transformations and four edges",
        )
    for item, edge in zip(transformations.transformations, flying_edges):
        if (
            edge.source != source
            or edge.heavenly_stem != source.heavenly_stem
            or edge.profile_id != transformations.profile_id
            or edge.transformation_type != item.type
            or edge.star != item.star
        ):
            _raise_component_mismatch(
                "flying edge does not match cycle source and transformation set",
                {
                    "transformation_type": item.type.value,
                    "transformation_star": item.star,
                    "edge_type": edge.transformation_type.value,
                    "edge_star": edge.star,
                },
            )


def _validate_birth_year_layer(chart_identity, birth_year_layer):
    if birth_year_layer is None:
        return
    if (
        birth_year_layer.identity.scope != "birth_year"
        or birth_year_layer.source.scope != "birth_year"
    ):
        _raise_component_mismatch(
            "natal birth-year slot requires a birth_year layer",
            {
                "identity_scope": birth_year_layer.identity.scope,
                "source_scope": birth_year_layer.source.scope,
            },
        )
    if (
        birth_year_layer.identity.chart_id != chart_identity.chart_id
        or birth_year_layer.source.chart_identity != chart_identity
    ):
        raise ZiweiPhase2AError(
            "chart_basis_mismatch",
            "birth-year layer and natal stack belong to different charts",
        )
    _validate_cycle_layer_components(
        birth_year_layer.identity,
        birth_year_layer.source,
        birth_year_layer.transformations,
        birth_year_layer.flying_edges,
    )


def build_cycle_layer(
    identity,
    source,
    transformations,
    flying_edges,
    provenance,
    earthly_branch=None,
):
    _validate_cycle_layer_components(
        identity,
        source,
        transformations,
        flying_edges,
    )
    return CycleTransformationLayer(
        identity,
        source,
        source.heavenly_stem,
        earthly_branch,
        transformations,
        tuple(flying_edges),
        provenance,
        "validated",
        AvailabilityRecord("available", None),
    )


def _availability():
    return MappingProxyType(
        {
            "birth_year_transformations": AvailabilityRecord("available", None),
            "natal_palace_flying": AvailabilityRecord("available", None),
            "decadal_transformations": AvailabilityRecord(
                "conditional", "trusted_decadal_stem_required"
            ),
            "yearly_transformations": AvailabilityRecord(
                "conditional", "trusted_yearly_stem_required"
            ),
            "monthly_transformations": AvailabilityRecord(
                "conditional", "matching_resolved_stem_required"
            ),
            "daily_transformations": AvailabilityRecord(
                "conditional", "matching_resolved_stem_required"
            ),
            "hourly_transformations": AvailabilityRecord(
                "conditional", "matching_resolved_stem_required"
            ),
        }
    )


def build_layer_stack(chart_identity, natal, cycles=(), small_limit=None):
    if (
        natal.star_locations.chart_identity != chart_identity
        or natal.palace_stems.chart_identity != chart_identity
        or natal.natal_flying_graph.chart_identity != chart_identity
    ):
        raise ZiweiPhase2AError(
            "chart_basis_mismatch",
            "natal basis and stack chart mismatch",
        )

    _validate_birth_year_layer(chart_identity, natal.birth_year_layer)

    seen = {}
    ordered = []
    for layer in cycles:
        if layer.identity.scope == "birth_year":
            raise ZiweiPhase2AError(
                "unsupported_scope",
                "birth_year layer belongs to natal reference frame",
            )
        key = layer.identity
        if key in seen:
            if seen[key] == layer:
                raise ZiweiPhase2AError(
                    "duplicate_layer_identity",
                    "duplicate layer identity",
                )
            raise ZiweiPhase2AError(
                "layer_conflict",
                "conflicting facts for one layer identity",
            )
        if layer.source.chart_identity != chart_identity:
            raise ZiweiPhase2AError(
                "chart_basis_mismatch",
                "cycle layer and stack chart mismatch",
            )
        seen[key] = layer
        ordered.append(layer)

    return ZiweiLayerStack(
        chart_identity,
        natal,
        tuple(ordered),
        small_limit,
        _availability(),
        STACK_PROVENANCE,
    )


class ZiweiCompositeView:
    def __init__(self, stack):
        self._stack = stack

    def _occurrences(self):
        layers = []
        if self._stack.natal.birth_year_layer is not None:
            layers.append(self._stack.natal.birth_year_layer)
        layers.extend(self._stack.cycles)

        rows = []
        for layer in layers:
            for edge in layer.flying_edges:
                rows.append(
                    TransformationOccurrence(
                        layer.identity.scope,
                        layer.identity.reference,
                        edge.transformation_type,
                        edge.star,
                        edge.target_palace,
                        layer.provenance,
                    )
                )
        return tuple(rows)

    def for_transformation(self, transformation_type):
        return tuple(
            row
            for row in self._occurrences()
            if row.transformation_type == transformation_type
        )

    def for_star(self, star):
        return tuple(row for row in self._occurrences() if row.star == star)

    def for_palace(self, palace):
        return tuple(
            row for row in self._occurrences() if row.target_palace == palace
        )
