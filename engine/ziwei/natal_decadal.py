from __future__ import annotations

from typing import Iterable, Tuple

from engine.birth.models import Sex

from .common import PALACE_NAMES, ZHI
from .natal_models import ZiweiDecadalPeriod, ZiweiPalaceRecord
from .transformation_profiles import LEGAL_STEMS


_LIFE_MASTER = {
    "子": "貪狼", "丑": "巨門", "寅": "祿存", "卯": "文曲",
    "辰": "廉貞", "巳": "武曲", "午": "破軍", "未": "武曲",
    "申": "廉貞", "酉": "文曲", "戌": "祿存", "亥": "巨門",
}
_BODY_MASTER = {
    "子": "火星", "丑": "天相", "寅": "天梁", "卯": "天同",
    "辰": "文昌", "巳": "天機", "午": "火星", "未": "天相",
    "申": "天梁", "酉": "天同", "戌": "文昌", "亥": "天機",
}
_YANG_STEMS = frozenset(("甲", "丙", "戊", "庚", "壬"))
_BUREAU_AGE_START = {
    "水二局": 2,
    "木三局": 3,
    "金四局": 4,
    "土五局": 5,
    "火六局": 6,
}


def resolve_life_body_master(ming_branch: str, birth_year_branch: str) -> Tuple[str, str]:
    if ming_branch not in ZHI:
        raise ValueError("invalid Ming palace branch: %s" % ming_branch)
    if birth_year_branch not in ZHI:
        raise ValueError("invalid birth-year branch: %s" % birth_year_branch)
    return _LIFE_MASTER[ming_branch], _BODY_MASTER[birth_year_branch]


def resolve_decadal_direction(birth_year_stem: str, sex: Sex) -> str:
    if birth_year_stem not in LEGAL_STEMS:
        raise ValueError("invalid birth-year stem: %s" % birth_year_stem)
    if not isinstance(sex, Sex):
        raise ValueError("sex must be engine.birth.models.Sex")

    is_yang_year = birth_year_stem in _YANG_STEMS
    is_forward = (is_yang_year and sex is Sex.MALE) or ((not is_yang_year) and sex is Sex.FEMALE)
    return "forward" if is_forward else "reverse"


def build_ziwei_decadal_periods(
    palaces: Iterable[ZiweiPalaceRecord],
    bureau: str,
    direction: str,
    count: int = 12,
) -> Tuple[ZiweiDecadalPeriod, ...]:
    if bureau not in _BUREAU_AGE_START:
        raise ValueError("invalid Ziwei five-element bureau: %s" % bureau)
    if direction not in ("forward", "reverse"):
        raise ValueError("decadal direction must be forward or reverse")
    if not isinstance(count, int) or isinstance(count, bool) or not 1 <= count <= 12:
        raise ValueError("decadal count must be an integer from 1 to 12")

    records = tuple(palaces)
    if len(records) != 12 or any(not isinstance(item, ZiweiPalaceRecord) for item in records):
        raise ValueError("Ziwei decadal periods require exactly twelve palace records")
    if {item.name for item in records} != set(PALACE_NAMES):
        raise ValueError("Ziwei decadal periods require all canonical palace names")
    if {item.branch for item in records} != set(ZHI):
        raise ValueError("Ziwei decadal periods require all twelve palace branches")

    palace_by_branch = {item.branch: item for item in records}
    ming = next((item for item in records if item.name == "命宮"), None)
    if ming is None:
        raise ValueError("Ziwei decadal periods require a Ming palace")

    start_age = _BUREAU_AGE_START[bureau]
    step = 1 if direction == "forward" else -1
    ming_index = ZHI.index(ming.branch)
    periods = []
    for offset in range(count):
        branch = ZHI[(ming_index + step * offset) % 12]
        palace = palace_by_branch[branch]
        age_start = start_age + 10 * offset
        periods.append(
            ZiweiDecadalPeriod(
                index=offset + 1,
                age_start=age_start,
                age_end=age_start + 9,
                palace=palace.name,
                stem_branch=palace.stem_branch,
                direction=direction,
            )
        )
    return tuple(periods)
