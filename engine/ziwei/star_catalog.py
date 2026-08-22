from __future__ import annotations


MAJOR_STARS = (
    "紫微", "天機", "太陽", "武曲", "天同", "廉貞",
    "天府", "太陰", "貪狼", "巨門", "天相", "天梁", "七殺", "破軍",
)

STAR_CATALOG = frozenset(MAJOR_STARS)


def category_for(star: str) -> str:
    if star in MAJOR_STARS:
        return "major"
    raise ValueError("star is not present in ziwei-core-stars-v1: %s" % star)
