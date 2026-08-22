from __future__ import annotations

from typing import Iterable, Sequence, Tuple

from .common import ZHI
from .natal_models import ZiweiPalaceRecord, ZiweiStarRecord
from .natal_profiles import ZiweiNatalProfile
from .star_catalog import MAJOR_STARS, STAR_CATALOG, category_for


_PALACE_INDEX_BRANCHES = tuple("寅卯辰巳午未申酉戌亥子丑")
_BUREAU_VALUES = (
    ("水二局", 2),
    ("木三局", 3),
    ("金四局", 4),
    ("土五局", 5),
    ("火六局", 6),
)
_ZIWEI_GROUP = (
    ("紫微", 0),
    ("天機", 1),
    ("太陽", 3),
    ("武曲", 4),
    ("天同", 5),
    ("廉貞", 8),
)
_TIANFU_GROUP = (
    ("天府", 0),
    ("太陰", 1),
    ("貪狼", 2),
    ("巨門", 3),
    ("天相", 4),
    ("天梁", 5),
    ("七殺", 6),
    ("破軍", 10),
)


def _bureau_value(bureau: str) -> int:
    for name, value in _BUREAU_VALUES:
        if bureau == name:
            return value
    raise ValueError("invalid Ziwei five-element bureau: %s" % bureau)


def _major_star_anchor_indices(lunar_day: int, bureau: str) -> Tuple[int, int]:
    if not isinstance(lunar_day, int) or isinstance(lunar_day, bool) or not 1 <= lunar_day <= 30:
        raise ValueError("lunar_day must be an integer from 1 to 30")
    bureau_value = _bureau_value(bureau)

    offset = 0
    while (lunar_day + offset) % bureau_value != 0:
        offset += 1

    quotient = ((lunar_day + offset) // bureau_value) % 12
    ziwei_index = quotient - 1
    if offset % 2 == 0:
        ziwei_index += offset
    else:
        ziwei_index -= offset
    ziwei_index %= 12
    tianfu_index = (12 - ziwei_index) % 12
    return ziwei_index, tianfu_index


def place_major_stars(lunar_day: int, bureau: str) -> Tuple[Tuple[str, str], ...]:
    ziwei_index, tianfu_index = _major_star_anchor_indices(lunar_day, bureau)
    by_star = {}
    for star, offset in _ZIWEI_GROUP:
        by_star[star] = _PALACE_INDEX_BRANCHES[(ziwei_index - offset) % 12]
    for star, offset in _TIANFU_GROUP:
        by_star[star] = _PALACE_INDEX_BRANCHES[(tianfu_index + offset) % 12]

    placements = tuple((star, by_star[star]) for star in MAJOR_STARS)
    if len(placements) != 14 or len({star for star, _ in placements}) != 14:
        raise RuntimeError("major-star placement invariant failed")
    if any(branch not in ZHI for _, branch in placements):
        raise RuntimeError("major-star placement produced invalid branch")
    return placements


def materialize_star_records(
    placements: Iterable[Tuple[str, str]],
    palaces: Sequence[ZiweiPalaceRecord],
    profile: ZiweiNatalProfile,
) -> Tuple[ZiweiStarRecord, ...]:
    palace_by_branch = {}
    for palace in palaces:
        if palace.branch in palace_by_branch:
            raise ValueError("duplicate palace branch in star materialization")
        palace_by_branch[palace.branch] = palace
    if set(palace_by_branch) != set(ZHI):
        raise ValueError("star materialization requires all twelve palace branches")

    items = tuple(placements)
    stars = tuple(star for star, _ in items)
    if len(set(stars)) != len(stars):
        raise ValueError("duplicate star placement")

    records = []
    for star, branch in items:
        if star not in STAR_CATALOG:
            raise ValueError("star is not present in active natal catalog: %s" % star)
        if branch not in palace_by_branch:
            raise ValueError("invalid or unmapped star branch: %s" % branch)
        palace = palace_by_branch[branch]
        records.append(
            ZiweiStarRecord(
                star=star,
                palace=palace.name,
                branch=branch,
                category=category_for(star),
                brightness=None,
                catalog_profile=profile.star_catalog,
            )
        )
    return tuple(records)
