from __future__ import annotations

from types import MappingProxyType

from .common import ZHI
from .star_catalog import STAR_CATALOG, brightness_optional_for


BRIGHTNESS_PROFILE_ID = "ziwei-brightness-common-v1"
_BRANCH_ORDER = tuple("寅卯辰巳午未申酉戌亥子丑")
_ALLOWED = frozenset(("廟", "旺", "得", "利", "平", "不", "陷"))

# Pinned public oracle: iztro 2.6.0 revision
# 814b77e6371e1050cac31bbf674db3c3138fcfde, src/data/stars.ts:STARS_INFO.
# Rows follow palace branch order 寅卯辰巳午未申酉戌亥子丑.
_TABLE = MappingProxyType({
    "紫微": ("旺", "旺", "得", "旺", "廟", "廟", "旺", "旺", "得", "旺", "平", "廟"),
    "天機": ("得", "旺", "利", "平", "廟", "陷", "得", "旺", "利", "平", "廟", "陷"),
    "太陽": ("旺", "廟", "旺", "旺", "旺", "得", "得", "陷", "不", "陷", "陷", "不"),
    "武曲": ("得", "利", "廟", "平", "旺", "廟", "得", "利", "廟", "平", "旺", "廟"),
    "天同": ("利", "平", "平", "廟", "陷", "不", "旺", "平", "平", "廟", "旺", "不"),
    "廉貞": ("廟", "平", "利", "陷", "平", "利", "廟", "平", "利", "陷", "平", "利"),
    "天府": ("廟", "得", "廟", "得", "旺", "廟", "得", "旺", "廟", "得", "廟", "廟"),
    "太陰": ("旺", "陷", "陷", "陷", "不", "不", "利", "不", "旺", "廟", "廟", "廟"),
    "貪狼": ("平", "利", "廟", "陷", "旺", "廟", "平", "利", "廟", "陷", "旺", "廟"),
    "巨門": ("廟", "廟", "陷", "旺", "旺", "不", "廟", "廟", "陷", "旺", "旺", "不"),
    "天相": ("廟", "陷", "得", "得", "廟", "得", "廟", "陷", "得", "得", "廟", "廟"),
    "天梁": ("廟", "廟", "廟", "陷", "廟", "旺", "陷", "得", "廟", "陷", "廟", "旺"),
    "七殺": ("廟", "旺", "廟", "平", "旺", "廟", "廟", "廟", "廟", "平", "旺", "廟"),
    "破軍": ("得", "陷", "旺", "平", "廟", "旺", "得", "陷", "旺", "平", "廟", "旺"),
    "文昌": ("陷", "利", "得", "廟", "陷", "利", "得", "廟", "陷", "利", "得", "廟"),
    "文曲": ("平", "旺", "得", "廟", "陷", "旺", "得", "廟", "陷", "旺", "得", "廟"),
    "火星": ("廟", "利", "陷", "得", "廟", "利", "陷", "得", "廟", "利", "陷", "得"),
    "鈴星": ("廟", "利", "陷", "得", "廟", "利", "陷", "得", "廟", "利", "陷", "得"),
    "擎羊": (None, "陷", "廟", None, "陷", "廟", None, "陷", "廟", None, "陷", "廟"),
    "陀羅": ("陷", None, "廟", "陷", None, "廟", "陷", None, "廟", "陷", None, "廟"),
})


def brightness_for(star: str, branch: str, profile_id: str = BRIGHTNESS_PROFILE_ID):
    if profile_id != BRIGHTNESS_PROFILE_ID:
        raise ValueError("unknown Ziwei brightness profile: %s" % profile_id)
    if star not in STAR_CATALOG:
        raise ValueError("star is not present in active natal catalog: %s" % star)
    if branch not in ZHI:
        raise ValueError("invalid earthly branch: %s" % branch)

    row = _TABLE.get(star)
    if row is None:
        if brightness_optional_for(star):
            return None
        raise RuntimeError("brightness table missing required star: %s" % star)

    if len(row) != 12:
        raise RuntimeError("brightness row must contain twelve branches: %s" % star)
    value = row[_BRANCH_ORDER.index(branch)]
    if value is None:
        if not brightness_optional_for(star):
            raise RuntimeError("required brightness unexpectedly missing: %s/%s" % (star, branch))
        return None
    if value not in _ALLOWED:
        raise RuntimeError("invalid brightness label in profile: %s" % value)
    return value
