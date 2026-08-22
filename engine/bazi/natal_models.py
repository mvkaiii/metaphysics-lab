from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Mapping, Optional, Tuple

from .calendar import GAN, ZHI

_ELEMENTS = frozenset(("木", "火", "土", "金", "水"))


def _require_aware(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("%s must be timezone-aware" % field_name)


@dataclass(frozen=True)
class BaziNatalProfile:
    profile_id: str = "bazi-natal-project-v1"
    rule_version: str = "1.0-exp"
    effective_time_basis: str = "normalized_civil"
    day_boundary: str = "23:00"
    decadal_rule: str = "three-days-one-year-v1"


@dataclass(frozen=True)
class Pillar:
    stem: str
    branch: str

    def __post_init__(self) -> None:
        if self.stem not in GAN:
            raise ValueError("invalid heavenly stem: %s" % self.stem)
        if self.branch not in ZHI:
            raise ValueError("invalid earthly branch: %s" % self.branch)

    @property
    def text(self) -> str:
        return self.stem + self.branch


@dataclass(frozen=True)
class HiddenStem:
    stem: str
    weight_rank: int

    def __post_init__(self) -> None:
        if self.stem not in GAN:
            raise ValueError("invalid hidden stem: %s" % self.stem)
        if not isinstance(self.weight_rank, int) or self.weight_rank < 1:
            raise ValueError("hidden stem weight_rank must be a positive integer")


@dataclass(frozen=True)
class PillarDetail:
    pillar: Pillar
    hidden_stems: Tuple[HiddenStem, ...]
    stem_ten_god: str
    hidden_ten_gods: Tuple[str, ...]

    def __post_init__(self) -> None:
        if len(self.hidden_stems) != len(self.hidden_ten_gods):
            raise ValueError("hidden stems and hidden ten gods must have equal length")
        if not self.stem_ten_god:
            raise ValueError("stem_ten_god must not be blank")
        if any(not value for value in self.hidden_ten_gods):
            raise ValueError("hidden_ten_gods must not contain blank values")


@dataclass(frozen=True)
class BaziDecadalPeriod:
    index: int
    pillar: Pillar
    start_age_years: float
    end_age_years: float
    start_datetime: datetime
    end_datetime: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.index, int) or self.index < 1:
            raise ValueError("decadal period index must be a positive integer")
        if self.start_age_years < 0 or self.end_age_years < self.start_age_years:
            raise ValueError("invalid decadal age range")
        _require_aware(self.start_datetime, "start_datetime")
        _require_aware(self.end_datetime, "end_datetime")
        if self.end_datetime < self.start_datetime:
            raise ValueError("decadal end_datetime must not precede start_datetime")


@dataclass(frozen=True)
class BaziNatalChart:
    profile: BaziNatalProfile
    effective_datetime: datetime
    pillars: Tuple[Pillar, ...]
    day_master: str
    pillar_details: Tuple[PillarDetail, ...]
    element_counts: Mapping[str, int]
    decadal_direction: str
    decadal_start: Optional[datetime]
    decadal_periods: Tuple[BaziDecadalPeriod, ...]
    validation: Mapping[str, object]
    provenance: Mapping[str, object]

    def __post_init__(self) -> None:
        _require_aware(self.effective_datetime, "effective_datetime")
        if len(self.pillars) != 4:
            raise ValueError("Bazi natal chart requires exactly four pillars")
        if len(self.pillar_details) != 4:
            raise ValueError("Bazi natal chart requires exactly four pillar details")
        if self.day_master not in GAN:
            raise ValueError("invalid day master: %s" % self.day_master)
        if self.pillars[2].stem != self.day_master:
            raise ValueError("day master must equal the day pillar stem")
        if set(self.element_counts) != _ELEMENTS:
            raise ValueError("element_counts must contain exactly 木火土金水")
        if any(
            not isinstance(value, int) or value < 0
            for value in self.element_counts.values()
        ):
            raise ValueError("element_counts values must be non-negative integers")
        if self.decadal_direction not in ("forward", "reverse"):
            raise ValueError("decadal_direction must be forward or reverse")
        if self.decadal_start is not None:
            _require_aware(self.decadal_start, "decadal_start")
        object.__setattr__(self, "element_counts", MappingProxyType(dict(self.element_counts)))
        object.__setattr__(self, "validation", MappingProxyType(dict(self.validation)))
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))
