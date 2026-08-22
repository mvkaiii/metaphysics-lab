from __future__ import annotations

from typing import Iterable, Sequence, Tuple

from .common import ZHI
from .errors import ZiweiPhase2AError
from .natal_models import ZiweiPalaceRecord, ZiweiStarRecord
from .natal_profiles import ZiweiNatalProfile
from .star_catalog import AUXILIARY_STARS, MAJOR_STARS, STAR_CATALOG, category_for
from .transformation_profiles import LEGAL_STEMS, PROFILE


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

_KUI_YUE = {
    "甲": ("丑", "未"),
    "乙": ("子", "申"),
    "丙": ("亥", "酉"),
    "丁": ("亥", "酉"),
    "戊": ("丑", "未"),
    "己": ("子", "申"),
    "庚": ("丑", "未"),
    "辛": ("午", "寅"),
    "壬": ("卯", "巳"),
    "癸": ("卯", "巳"),
}
_LUCUN = {
    "甲": "寅", "乙": "卯", "丙": "巳", "丁": "午", "戊": "巳",
    "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子",
}


def _bureau_value(bureau: str) -> int:
    for name, value in _BUREAU_VALUES:
        if bureau == name:
            return value
    raise ValueError("invalid Ziwei five-element bureau: %s" % bureau)


def _palace_shift(branch: str, offset: int) -> str:
    if branch not in _PALACE_INDEX_BRANCHES:
        raise ValueError("invalid earthly branch: %s" % branch)
    return _PALACE_INDEX_BRANCHES[(_PALACE_INDEX_BRANCHES.index(branch) + offset) % 12]


def _validate_month(month: int) -> None:
    if not isinstance(month, int) or isinstance(month, bool) or not 1 <= month <= 12:
        raise ValueError("lunar_month must be an integer from 1 to 12")


def _validate_stem(stem: str) -> None:
    if stem not in LEGAL_STEMS:
        raise ValueError("invalid heavenly stem: %s" % stem)


def _validate_branch(branch: str) -> None:
    if branch not in ZHI:
        raise ValueError("invalid earthly branch: %s" % branch)


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


def place_left_right_assistants(lunar_month: int) -> dict:
    _validate_month(lunar_month)
    offset = lunar_month - 1
    return {
        "左輔": _palace_shift("辰", offset),
        "右弼": _palace_shift("戌", -offset),
    }


def place_chang_qu(hour_branch: str) -> dict:
    _validate_branch(hour_branch)
    time_index = ZHI.index(hour_branch)
    return {
        "文昌": _palace_shift("戌", -time_index),
        "文曲": _palace_shift("辰", time_index),
    }


def place_kui_yue(year_stem: str) -> dict:
    _validate_stem(year_stem)
    kui, yue = _KUI_YUE[year_stem]
    return {"天魁": kui, "天鉞": yue}


def place_lucun_yang_tuo(year_stem: str) -> dict:
    _validate_stem(year_stem)
    lu = _LUCUN[year_stem]
    return {
        "祿存": lu,
        "擎羊": _palace_shift(lu, 1),
        "陀羅": _palace_shift(lu, -1),
    }


def place_tianma(year_branch: str) -> dict:
    _validate_branch(year_branch)
    if year_branch in ("寅", "午", "戌"):
        ma = "申"
    elif year_branch in ("申", "子", "辰"):
        ma = "寅"
    elif year_branch in ("巳", "酉", "丑"):
        ma = "亥"
    else:
        ma = "巳"
    return {"天馬": ma}


def place_fire_bell(year_branch: str, hour_branch: str) -> dict:
    _validate_branch(year_branch)
    _validate_branch(hour_branch)
    time_index = ZHI.index(hour_branch)

    if year_branch in ("寅", "午", "戌"):
        fire_start, bell_start = "丑", "卯"
    elif year_branch in ("申", "子", "辰"):
        fire_start, bell_start = "寅", "戌"
    elif year_branch in ("巳", "酉", "丑"):
        fire_start, bell_start = "卯", "戌"
    else:
        fire_start, bell_start = "酉", "戌"

    return {
        "火星": _palace_shift(fire_start, time_index),
        "鈴星": _palace_shift(bell_start, time_index),
    }


def _year_branch_from_lunar_year(lunar_year: int) -> str:
    if not isinstance(lunar_year, int) or isinstance(lunar_year, bool):
        raise ValueError("lunar_year must be int")
    return ZHI[(lunar_year - 4) % 12]


def place_auxiliary_stars(
    birth_basis,
    birth_year_stem: str,
    profile: ZiweiNatalProfile,
) -> Tuple[Tuple[str, str], ...]:
    if not isinstance(profile, ZiweiNatalProfile):
        raise ValueError("profile must be ZiweiNatalProfile")
    if profile.star_catalog != "ziwei-core-stars-v1":
        raise ValueError("unsupported natal star catalog: %s" % profile.star_catalog)
    _validate_stem(birth_year_stem)

    try:
        lunar_month = birth_basis.lunar_month
        hour_branch = birth_basis.effective_hour_branch
        lunar_year = birth_basis.lunar_year
    except AttributeError as exc:
        raise ValueError("birth_basis is missing required auxiliary-star fields") from exc

    year_branch = _year_branch_from_lunar_year(lunar_year)
    by_star = {}
    for family in (
        place_left_right_assistants(lunar_month),
        place_chang_qu(hour_branch),
        place_kui_yue(birth_year_stem),
        place_lucun_yang_tuo(birth_year_stem),
        place_fire_bell(year_branch, hour_branch),
        place_tianma(year_branch),
    ):
        for star, branch in family.items():
            if star in by_star:
                raise RuntimeError("duplicate auxiliary-star placement: %s" % star)
            by_star[star] = branch

    placements = tuple((star, by_star[star]) for star in AUXILIARY_STARS)
    if len(placements) != len(AUXILIARY_STARS):
        raise RuntimeError("auxiliary-star placement invariant failed")
    if any(branch not in ZHI for _, branch in placements):
        raise RuntimeError("auxiliary-star placement produced invalid branch")
    return placements


def validate_transformation_star_locations(placements: Iterable[Tuple[str, str]]) -> None:
    items = tuple(placements)
    present = {star for star, branch in items if branch in ZHI}
    required = {star for stars in PROFILE.values() for star in stars}
    missing = tuple(sorted(required - present))
    if missing:
        raise ZiweiPhase2AError(
            "missing_transformation_star_location",
            "natal star catalog is missing one or more transformation-required star locations",
            {"missing_stars": missing},
        )


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
