from .errors import ZiweiPhase2AError

PROFILE_ID = "metaphysics-lab-common-v1"
RULE_VERSION = "1.0"
LEGAL_STEMS = tuple("甲乙丙丁戊己庚辛壬癸")
PROFILE = {
    "甲": ("廉貞", "破軍", "武曲", "太陽"),
    "乙": ("天機", "天梁", "紫微", "太陰"),
    "丙": ("天同", "天機", "文昌", "廉貞"),
    "丁": ("太陰", "天同", "天機", "巨門"),
    "戊": ("貪狼", "太陰", "右弼", "天機"),
    "己": ("武曲", "貪狼", "天梁", "文曲"),
    "庚": ("太陽", "武曲", "太陰", "天同"),
    "辛": ("巨門", "太陽", "文曲", "文昌"),
    "壬": ("天梁", "紫微", "左輔", "武曲"),
    "癸": ("破軍", "巨門", "太陰", "貪狼"),
}


def validate_transformation_profile(profile_id, rule_version, table):
    if not profile_id or not rule_version:
        raise ZiweiPhase2AError(
            "invalid_transformation_profile",
            "profile id and rule version are required",
        )
    if len(table) != 10 or set(table) != set(LEGAL_STEMS):
        raise ZiweiPhase2AError(
            "invalid_transformation_profile",
            "profile must contain exactly ten stems",
        )
    for stem in LEGAL_STEMS:
        stars = tuple(table[stem])
        if len(stars) != 4 or any(not star for star in stars):
            raise ZiweiPhase2AError(
                "invalid_transformation_profile",
                "each stem must provide four non-empty stars",
                {"stem": stem},
            )
