from engine.ziwei.common import PALACE_NAMES
from engine.ziwei.models import ChartIdentity, LayerProvenance, PalaceStemRecord, StarLocationRecord

CHART = ChartIdentity("chart-fixture-A", "natal", "synthetic-v1")
PROVENANCE = LayerProvenance("validated_source_fact", "synthetic", "1", None, None, None)

TRANSFORMABLE_STARS = (
    "廉貞", "破軍", "武曲", "太陽", "天機",
    "天梁", "紫微", "太陰", "天同", "文昌",
    "貪狼", "右弼", "文曲", "巨門", "左輔",
)

SYNTHETIC_STAR_RECORDS = tuple(
    StarLocationRecord(star, PALACE_NAMES[idx % 12])
    for idx, star in enumerate(TRANSFORMABLE_STARS)
)

SYNTHETIC_PALACE_STEM_RECORDS = tuple(
    PalaceStemRecord(palace, "甲乙丙丁戊己庚辛壬癸甲乙"[idx])
    for idx, palace in enumerate(PALACE_NAMES)
)
