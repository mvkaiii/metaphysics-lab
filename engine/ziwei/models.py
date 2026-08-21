from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Optional, Tuple, Union


class TransformationType(str, Enum):
    LU = "祿"
    QUAN = "權"
    KE = "科"
    JI = "忌"


class GeometricRelation(str, Enum):
    SAME_PALACE = "same_palace"
    OPPOSITE_PALACE_INCOMING = "opposite_palace_incoming"
    NORMAL = "normal"


@dataclass(frozen=True)
class LayerProvenance:
    classification: str
    source_name: str
    source_version: Optional[str]
    rule_profile: Optional[str]
    rule_version: Optional[str]
    derived_by: Optional[str]
    qualified_against: Tuple[str, ...] = ()
    qualification_status: str = "not_run"


@dataclass(frozen=True)
class Transformation:
    type: TransformationType
    star: str
    sequence: int


@dataclass(frozen=True)
class TransformationSet:
    heavenly_stem: str
    profile_id: str
    rule_version: str
    transformations: Tuple[Transformation, ...]
    provenance: LayerProvenance


@dataclass(frozen=True)
class ChartIdentity:
    chart_id: str
    chart_basis: str
    source_profile: str


@dataclass(frozen=True)
class StarLocationRecord:
    star: str
    palace: str


@dataclass(frozen=True)
class StarLocationIndex:
    chart_identity: ChartIdentity
    locations: Mapping[str, str]
    validation_status: str
    provenance: LayerProvenance


@dataclass(frozen=True)
class PalaceStemRecord:
    palace: str
    heavenly_stem: str


@dataclass(frozen=True)
class PalaceStemIndex:
    chart_identity: ChartIdentity
    stems: Mapping[str, str]
    validation_status: str
    provenance: LayerProvenance


@dataclass(frozen=True)
class PalaceStemSource:
    kind: str
    chart_identity: ChartIdentity
    palace: str
    heavenly_stem: str


@dataclass(frozen=True)
class CycleStemSource:
    kind: str
    chart_identity: ChartIdentity
    scope: str
    reference: str
    heavenly_stem: str


FlyingSource = Union[PalaceStemSource, CycleStemSource]


@dataclass(frozen=True)
class FlyingEdge:
    edge_id: str
    source: FlyingSource
    heavenly_stem: str
    transformation_type: TransformationType
    star: str
    target_palace: str
    target_basis: str
    profile_id: str
    geometric_relation: Optional[GeometricRelation]
    provenance: LayerProvenance


@dataclass(frozen=True)
class NatalFlyingGraph:
    chart_identity: ChartIdentity
    edges: Tuple[FlyingEdge, ...]
    outgoing_index: Mapping[str, Tuple[FlyingEdge, ...]]
    incoming_index: Mapping[str, Tuple[FlyingEdge, ...]]


@dataclass(frozen=True)
class LayerIdentity:
    chart_id: str
    scope: str
    reference: str
    rule_profile: str


@dataclass(frozen=True)
class AvailabilityRecord:
    status: str
    reason: Optional[str]


@dataclass(frozen=True)
class CycleTransformationLayer:
    identity: LayerIdentity
    source: CycleStemSource
    heavenly_stem: str
    earthly_branch: Optional[str]
    transformations: TransformationSet
    flying_edges: Tuple[FlyingEdge, ...]
    provenance: LayerProvenance
    validation: str
    availability: AvailabilityRecord


@dataclass(frozen=True)
class SmallLimitContext:
    reference: str
    palace: str
    stem_branch: str
    provenance: LayerProvenance
    transformation_layer: None = None


@dataclass(frozen=True)
class NatalContext:
    star_locations: StarLocationIndex
    palace_stems: PalaceStemIndex
    natal_flying_graph: NatalFlyingGraph
    birth_year_layer: Optional[CycleTransformationLayer]


@dataclass(frozen=True)
class ZiweiLayerStack:
    chart_identity: ChartIdentity
    natal: NatalContext
    cycles: Tuple[CycleTransformationLayer, ...]
    small_limit: Optional[SmallLimitContext]
    availability: Mapping[str, AvailabilityRecord]
    provenance: LayerProvenance


@dataclass(frozen=True)
class TransformationOccurrence:
    scope: str
    reference: str
    transformation_type: TransformationType
    star: str
    target_palace: str
    provenance: LayerProvenance
