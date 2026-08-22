from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Optional, Tuple

from engine.calendar.sexagenary import GAN, ZHI, is_valid_sexagenary_pair

from .errors import ZiweiFlowingStarError
from .models import ChartIdentity, CycleTransformationLayer, LayerIdentity, LayerProvenance


SUPPORTED_FLOWING_STAR_SCOPES = frozenset(("decadal", "yearly", "monthly", "daily", "hourly"))
FLOWING_STAR_CATEGORIES = frozenset(("soft", "lucun", "tough", "tianma", "flower", "helper"))
SOURCE_VALIDATION_STATUSES = frozenset(("validated", "boundary_caution", "boundary_conflict", "out_of_validated_range"))
AVAILABLE_SOURCE_STATUSES = frozenset(("validated", "boundary_caution"))


def _raise(code: str, message: str, details=None):
    raise ZiweiFlowingStarError(code, message, details)


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        _raise("invalid_flowing_star_layer", "%s must be a non-empty string" % name, {"field": name})


@dataclass(frozen=True)
class FlowingStarProfile:
    profile_id: str
    rule_version: str
    canonical_location: str
    qualification_target: str

    def __post_init__(self) -> None:
        for name in ("profile_id", "rule_version", "qualification_target"):
            _require_text(name, getattr(self, name))
        if self.canonical_location != "earthly_branch":
            _raise(
                "invalid_flowing_star_layer",
                "unsupported canonical flowing-star location",
                {"canonical_location": self.canonical_location},
            )


@dataclass(frozen=True)
class FlowingStarSource:
    chart_identity: ChartIdentity
    scope: str
    reference: str
    heavenly_stem: str
    earthly_branch: str
    source_profile: str
    rule_version: str
    validation_status: str
    provenance: LayerProvenance

    def __post_init__(self) -> None:
        if not isinstance(self.chart_identity, ChartIdentity):
            _raise("chart_basis_mismatch", "flowing-star source requires ChartIdentity")
        if self.scope not in SUPPORTED_FLOWING_STAR_SCOPES:
            _raise("unsupported_flowing_star_scope", "unsupported flowing-star scope", {"scope": self.scope})
        if not isinstance(self.reference, str) or not self.reference.strip():
            _raise("missing_cycle_stem_source", "flowing-star source requires a non-empty reference")
        if self.heavenly_stem not in GAN:
            _raise("invalid_flowing_star_stem", "invalid flowing-star heavenly stem", {"stem": self.heavenly_stem})
        if self.earthly_branch not in ZHI:
            _raise("invalid_flowing_star_branch", "invalid flowing-star earthly branch", {"branch": self.earthly_branch})
        if not is_valid_sexagenary_pair(self.heavenly_stem, self.earthly_branch):
            _raise(
                "invalid_sexagenary_pair",
                "flowing-star source stem/branch is not a legal sexagenary pair",
                {"stem": self.heavenly_stem, "branch": self.earthly_branch},
            )
        _require_text("source_profile", self.source_profile)
        _require_text("rule_version", self.rule_version)
        if self.validation_status not in SOURCE_VALIDATION_STATUSES:
            _raise(
                "invalid_flowing_star_layer",
                "unknown flowing-star source validation status",
                {"validation_status": self.validation_status},
            )
        if not isinstance(self.provenance, LayerProvenance):
            _raise("invalid_flowing_star_layer", "flowing-star source requires LayerProvenance")


@dataclass(frozen=True)
class FlowingStarPlacement:
    base_star: str
    category: str
    scope: str
    target_branch: str
    sequence: int
    provenance: LayerProvenance

    def __post_init__(self) -> None:
        _require_text("base_star", self.base_star)
        if self.category not in FLOWING_STAR_CATEGORIES:
            _raise("invalid_flowing_star_layer", "unknown flowing-star category", {"category": self.category})
        if self.scope not in SUPPORTED_FLOWING_STAR_SCOPES:
            _raise("unsupported_flowing_star_scope", "unsupported flowing-star scope", {"scope": self.scope})
        if self.target_branch not in ZHI:
            _raise("invalid_flowing_star_branch", "invalid flowing-star target branch", {"branch": self.target_branch})
        if not isinstance(self.sequence, int) or isinstance(self.sequence, bool) or self.sequence < 1:
            _raise("invalid_flowing_star_layer", "flowing-star sequence must be a positive integer")
        if not isinstance(self.provenance, LayerProvenance):
            _raise("invalid_flowing_star_layer", "flowing-star placement requires LayerProvenance")


@dataclass(frozen=True)
class FlowingStarLayer:
    identity: LayerIdentity
    source: FlowingStarSource
    placements: Tuple[FlowingStarPlacement, ...]
    profile_id: str
    rule_version: str
    classification: str
    maturity: str
    validation: str
    provenance: LayerProvenance

    def __post_init__(self) -> None:
        if not isinstance(self.identity, LayerIdentity):
            _raise("invalid_flowing_star_layer", "flowing-star layer requires LayerIdentity")
        if not isinstance(self.source, FlowingStarSource):
            _raise("missing_cycle_stem_source", "flowing-star layer requires FlowingStarSource")
        items = tuple(self.placements)
        if any(not isinstance(item, FlowingStarPlacement) for item in items):
            _raise("invalid_flowing_star_layer", "placements must contain FlowingStarPlacement records")
        object.__setattr__(self, "placements", items)
        if self.identity.chart_id != self.source.chart_identity.chart_id:
            _raise("chart_basis_mismatch", "flowing-star identity and source chart mismatch")
        if self.identity.scope != self.source.scope:
            _raise(
                "cycle_scope_mismatch",
                "flowing-star identity and source scope mismatch",
                {"identity_scope": self.identity.scope, "source_scope": self.source.scope},
            )
        if self.identity.reference != self.source.reference:
            _raise(
                "cycle_reference_mismatch",
                "flowing-star identity and source reference mismatch",
                {"identity_reference": self.identity.reference, "source_reference": self.source.reference},
            )
        if self.identity.rule_profile != self.profile_id:
            _raise("invalid_flowing_star_layer", "flowing-star identity/profile mismatch")
        _require_text("profile_id", self.profile_id)
        _require_text("rule_version", self.rule_version)
        if self.classification != "Project 推導盤面":
            _raise("invalid_flowing_star_layer", "flowing-star classification must be Project 推導盤面")
        if self.maturity != "experimental":
            _raise("invalid_flowing_star_layer", "flowing-star v1 maturity must remain experimental")
        if self.source.validation_status not in AVAILABLE_SOURCE_STATUSES:
            _raise(
                "invalid_flowing_star_layer",
                "blocked source cannot materialize an available flowing-star layer",
                {"validation_status": self.source.validation_status},
            )
        if self.validation != self.source.validation_status:
            _raise("invalid_flowing_star_layer", "layer validation must match source validation status")
        expected_count = 11 if self.source.scope == "yearly" else 10
        if len(items) != expected_count:
            _raise(
                "incomplete_flowing_star_catalog",
                "flowing-star layer has the wrong star count",
                {"scope": self.source.scope, "expected": expected_count, "actual": len(items)},
            )
        stars = tuple(item.base_star for item in items)
        if len(set(stars)) != len(stars):
            _raise("duplicate_flowing_star_identity", "duplicate flowing-star identity in layer")
        if tuple(item.sequence for item in items) != tuple(range(1, expected_count + 1)):
            _raise("invalid_flowing_star_layer", "flowing-star sequence must be contiguous and deterministic")
        if any(item.scope != self.source.scope for item in items):
            _raise("cycle_scope_mismatch", "placement scope differs from source scope")
        if not isinstance(self.provenance, LayerProvenance):
            _raise("invalid_flowing_star_layer", "flowing-star layer requires LayerProvenance")


@dataclass(frozen=True)
class ScopePalaceMapping:
    chart_id: str
    scope: str
    reference: str
    palaces: Mapping[str, str]

    def __post_init__(self) -> None:
        _require_text("chart_id", self.chart_id)
        if self.scope not in SUPPORTED_FLOWING_STAR_SCOPES:
            _raise("unsupported_flowing_star_scope", "unsupported scope-palace mapping scope", {"scope": self.scope})
        _require_text("reference", self.reference)
        if not isinstance(self.palaces, Mapping):
            _raise("flowing_star_materialization_mismatch", "scope palace mapping must be a mapping")
        copied = dict(self.palaces)
        if set(copied) != set(ZHI) or len(copied) != 12:
            _raise("flowing_star_materialization_mismatch", "scope palace mapping requires all twelve branches")
        if any(not isinstance(value, str) or not value.strip() for value in copied.values()):
            _raise("flowing_star_materialization_mismatch", "scope palace names must be non-empty strings")
        if len(set(copied.values())) != 12:
            _raise("flowing_star_materialization_mismatch", "scope palace mapping requires twelve unique palace names")
        object.__setattr__(self, "palaces", MappingProxyType(copied))


@dataclass(frozen=True)
class FlowingStarMaterializedRecord:
    base_star: str
    display_name: str
    target_branch: str
    natal_palace: Optional[str]
    scope_palace: Optional[str]
    scope: str
    source_reference: str


@dataclass(frozen=True)
class ZiweiDynamicCycleView:
    transformation_layer: Optional[CycleTransformationLayer]
    flowing_star_layer: FlowingStarLayer
    materialized_records: Tuple[FlowingStarMaterializedRecord, ...]

    def __post_init__(self) -> None:
        if self.transformation_layer is not None and not isinstance(self.transformation_layer, CycleTransformationLayer):
            _raise("flowing_star_materialization_mismatch", "transformation_layer has invalid type")
        if not isinstance(self.flowing_star_layer, FlowingStarLayer):
            _raise("flowing_star_materialization_mismatch", "flowing_star_layer has invalid type")
        records = tuple(self.materialized_records)
        if any(not isinstance(item, FlowingStarMaterializedRecord) for item in records):
            _raise("flowing_star_materialization_mismatch", "materialized records have invalid type")
        object.__setattr__(self, "materialized_records", records)
