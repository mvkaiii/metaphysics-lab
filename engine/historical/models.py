from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Tuple


@dataclass(frozen=True)
class ActivationEvidence:
    evidence_id: str
    tier: int
    relation_family: str
    target_layer: str
    target_component: str
    participants: Tuple[str, ...]
    metadata: Mapping[str, object]

    def __post_init__(self) -> None:
        if not isinstance(self.evidence_id, str) or not self.evidence_id:
            raise ValueError("evidence_id must be non-empty text")
        if self.tier not in (1, 2, 3):
            raise ValueError("tier must be 1, 2, or 3")
        if not isinstance(self.relation_family, str) or not self.relation_family:
            raise ValueError("relation_family must be non-empty text")
        if self.target_layer not in ("natal", "decadal", "pattern", "cycle"):
            raise ValueError("target_layer is invalid")
        if not isinstance(self.target_component, str) or not self.target_component:
            raise ValueError("target_component must be non-empty text")
        if not isinstance(self.participants, tuple) or any(not isinstance(item, str) for item in self.participants):
            raise ValueError("participants must be a tuple of text")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def to_dict(self) -> dict:
        return {
            "evidence_id": self.evidence_id,
            "tier": self.tier,
            "relation_family": self.relation_family,
            "target_layer": self.target_layer,
            "target_component": self.target_component,
            "participants": list(self.participants),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class ActivationRankVector:
    tier1_family_count: int
    tier1_evidence_count: int
    cross_layer_tier1: bool
    tier2_family_count: int
    tier2_evidence_count: int
    tier3_family_count: int
    tier3_evidence_count: int

    def __post_init__(self) -> None:
        for field in (
            "tier1_family_count", "tier1_evidence_count", "tier2_family_count",
            "tier2_evidence_count", "tier3_family_count", "tier3_evidence_count",
        ):
            value = getattr(self, field)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError("rank-vector counts must be non-negative integers")
        if not isinstance(self.cross_layer_tier1, bool):
            raise ValueError("cross_layer_tier1 must be boolean")

    def as_sort_key(self, label_year: int) -> tuple:
        return (
            self.tier1_family_count,
            self.tier1_evidence_count,
            1 if self.cross_layer_tier1 else 0,
            self.tier2_family_count,
            self.tier2_evidence_count,
            self.tier3_family_count,
            self.tier3_evidence_count,
            int(label_year),
        )

    def to_dict(self) -> dict:
        return {
            "tier1_family_count": self.tier1_family_count,
            "tier1_evidence_count": self.tier1_evidence_count,
            "cross_layer_tier1": self.cross_layer_tier1,
            "tier2_family_count": self.tier2_family_count,
            "tier2_evidence_count": self.tier2_evidence_count,
            "tier3_family_count": self.tier3_family_count,
            "tier3_evidence_count": self.tier3_evidence_count,
        }
