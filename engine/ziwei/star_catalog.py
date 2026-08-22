from __future__ import annotations

from types import MappingProxyType


MAJOR_STARS = (
    "紫微", "天機", "太陽", "武曲", "天同", "廉貞",
    "天府", "太陰", "貪狼", "巨門", "天相", "天梁", "七殺", "破軍",
)

# v1 intentionally contains only the auxiliary/malefic stars required by the
# approved Natal Foundation scope. Additional miscellaneous stars remain out of
# scope until their own reviewed profile is introduced.
AUXILIARY_STARS = (
    "左輔", "右弼", "文昌", "文曲",
    "天魁", "天鉞", "祿存", "擎羊", "陀羅", "火星", "鈴星", "天馬",
)

_AUXILIARY_CATEGORIES = MappingProxyType({
    "左輔": "soft",
    "右弼": "soft",
    "文昌": "soft",
    "文曲": "soft",
    "天魁": "soft",
    "天鉞": "soft",
    "祿存": "lucun",
    "擎羊": "tough",
    "陀羅": "tough",
    "火星": "tough",
    "鈴星": "tough",
    "天馬": "tianma",
})

# Pinned iztro does not define brightness for these stars, or defines a partial
# row with intentional blanks (擎羊/陀羅). None is therefore legal only for
# this explicit metadata set; it is never a generic fallback for unknown data.
_BRIGHTNESS_OPTIONAL = frozenset((
    "左輔", "右弼", "天魁", "天鉞", "祿存", "天馬", "擎羊", "陀羅",
))

STAR_CATALOG = frozenset(MAJOR_STARS + AUXILIARY_STARS)


def category_for(star: str) -> str:
    if star in MAJOR_STARS:
        return "major"
    if star in _AUXILIARY_CATEGORIES:
        return _AUXILIARY_CATEGORIES[star]
    raise ValueError("star is not present in ziwei-core-stars-v1: %s" % star)


def brightness_optional_for(star: str) -> bool:
    if star not in STAR_CATALOG:
        raise ValueError("star is not present in ziwei-core-stars-v1: %s" % star)
    return star in _BRIGHTNESS_OPTIONAL
