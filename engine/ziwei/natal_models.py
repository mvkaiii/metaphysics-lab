from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Optional, Tuple

from .common import PALACE_NAMES, ZHI
from .models import ChartIdentity, NatalFlyingGraph, TransformationSet
from .natal_profiles import ZiweiNatalProfile
from .transformation_profiles import LEGAL_STEMS


@dataclass(frozen=True)
class ZiweiPalaceRecord:
    name: str
    branch: str
    heavenly_stem: str
    stem_branch: str

    def __post_init__(self) -> None:
        if self.name not in PALACE_NAMES:
            raise ValueError("invalid Ziwei palace name: %s" % self.name)
        if self.branch not in ZHI:
            raise ValueError("invalid Ziwei palace branch: %s" % self.branch)
        if self.heavenly_stem not in LEGAL_STEMS:
            raise ValueError("invalid Ziwei palace stem: %s" % self.heavenly_stem)
        if self.stem_branch != self.heavenly_stem + self.branch:
            raise ValueError("stem_branch must equal heavenly_stem + branch")


@dataclass(frozen=True)
class ZiweiStarRecord:
    star: str
    palace: str
    branch: str
    category: str
    brightness: Optional[str]
    catalog_profile: str

    def __post_init__(self) -> None:
        if not self.star:
            raise ValueError("star must not be blank")
        if self.palace not in PALACE_NAMES:
            raise ValueError("invalid Ziwei star palace: %s" % self.palace)
        if self.branch not in ZHI:
            raise ValueError("invalid Ziwei star branch: %s" % self.branch)
        if not self.category:
            raise ValueError("star category must not be blank")
        if self.brightness is not None and not self.brightness:
            raise ValueError("brightness must be None or non-blank")
        if not self.catalog_profile:
            raise ValueError("catalog_profile must not be blank")


@dataclass(frozen=True)
class ZiweiDecadalPeriod:
    index: int
    age_start: int
    age_end: int
    palace: str
    stem_branch: str
    direction: str

    def __post_init__(self) -> None:
        if not isinstance(self.index, int) or self.index < 1:
            raise ValueError("decadal period index must be a positive integer")
        if not isinstance(self.age_start, int) or not isinstance(self.age_end, int):
            raise ValueError("decadal ages must be integers")
        if self.age_start < 0 or self.age_end < self.age_start:
            raise ValueError("invalid decadal age range")
        if self.palace not in PALACE_NAMES:
            raise ValueError("invalid decadal palace: %s" % self.palace)
        if len(self.stem_branch) != 2:
            raise ValueError("decadal stem_branch must contain one stem and one branch")
        if self.stem_branch[0] not in LEGAL_STEMS or self.stem_branch[1] not in ZHI:
            raise ValueError("invalid decadal stem_branch: %s" % self.stem_branch)
        if self.direction not in ("forward", "reverse"):
            raise ValueError("decadal direction must be forward or reverse")


@dataclass(frozen=True)
class ZiweiNatalChart:
    profile: ZiweiNatalProfile
    palaces: Tuple[ZiweiPalaceRecord, ...]
    stars: Tuple[ZiweiStarRecord, ...]
    decadal_periods: Tuple[ZiweiDecadalPeriod, ...]
    validation: Mapping[str, object]
    provenance: Mapping[str, object]
    chart_identity: Optional[ChartIdentity] = None
    ming_palace: Optional[str] = None
    body_palace: Optional[str] = None
    five_element_bureau: Optional[str] = None
    life_master: Optional[str] = None
    body_master: Optional[str] = None
    birth_transformations: Optional[TransformationSet] = None
    natal_flying_graph: Optional[NatalFlyingGraph] = None
    classification: str = "Project 原生盤面"
    maturity: str = "experimental"

    def __post_init__(self) -> None:
        if len(self.palaces) != 12:
            raise ValueError("Ziwei natal chart requires exactly twelve palace records")
        palace_names = tuple(record.name for record in self.palaces)
        if len(set(palace_names)) != 12 or set(palace_names) != set(PALACE_NAMES):
            raise ValueError("Ziwei natal chart requires all twelve unique canonical palace names")
        palace_branches = tuple(record.branch for record in self.palaces)
        if len(set(palace_branches)) != 12 or set(palace_branches) != set(ZHI):
            raise ValueError("Ziwei natal chart requires twelve unique canonical palace branches")

        palace_by_name = {record.name: record for record in self.palaces}
        star_names = tuple(record.star for record in self.stars)
        if len(set(star_names)) != len(star_names):
            raise ValueError("duplicate star identity in Ziwei natal chart")
        for star in self.stars:
            if palace_by_name[star.palace].branch != star.branch:
                raise ValueError("star branch must match its palace branch")

        if self.ming_palace is not None and self.ming_palace not in PALACE_NAMES:
            raise ValueError("invalid ming_palace")
        if self.body_palace is not None and self.body_palace not in PALACE_NAMES:
            raise ValueError("invalid body_palace")
        if self.classification != "Project 原生盤面":
            raise ValueError("Ziwei natal chart classification must be Project 原生盤面")
        if self.maturity != "experimental":
            raise ValueError("Ziwei natal v1 remains experimental until qualification promotion")

        object.__setattr__(self, "validation", MappingProxyType(dict(self.validation)))
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))
