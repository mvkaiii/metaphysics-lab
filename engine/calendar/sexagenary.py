from __future__ import annotations

from datetime import date

GAN = tuple("甲乙丙丁戊己庚辛壬癸")
ZHI = tuple("子丑寅卯辰巳午未申酉戌亥")
MONTH_ZHI = tuple("寅卯辰巳午未申酉戌亥子丑")

FIRST_MONTH_STEM = {
    "甲": "丙", "己": "丙",
    "乙": "戊", "庚": "戊",
    "丙": "庚", "辛": "庚",
    "丁": "壬", "壬": "壬",
    "戊": "甲", "癸": "甲",
}

FIRST_HOUR_STEM = {
    "甲": "甲", "己": "甲",
    "乙": "丙", "庚": "丙",
    "丙": "戊", "辛": "戊",
    "丁": "庚", "壬": "庚",
    "戊": "壬", "癸": "壬",
}


def gregorian_jdn(value: date) -> int:
    if not isinstance(value, date):
        raise ValueError("value must be datetime.date")
    year, month, day = value.year, value.month, value.day
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    return day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045


def sexagenary_day(value: date) -> tuple[str, str]:
    offset = gregorian_jdn(value) - 11
    return GAN[offset % 10], ZHI[offset % 12]


def lunar_year_stem(lunar_year: int) -> str:
    if not isinstance(lunar_year, int) or isinstance(lunar_year, bool):
        raise ValueError("lunar_year must be int")
    return GAN[(lunar_year - 4) % 10]


def lunar_year_branch(lunar_year: int) -> str:
    if not isinstance(lunar_year, int) or isinstance(lunar_year, bool):
        raise ValueError("lunar_year must be int")
    return ZHI[(lunar_year - 4) % 12]


def is_valid_sexagenary_pair(stem: str, branch: str) -> bool:
    if stem not in GAN or branch not in ZHI:
        return False
    return GAN.index(stem) % 2 == ZHI.index(branch) % 2


def five_tiger_month(year_stem: str, effective_month_ordinal: int) -> tuple[str, str]:
    if year_stem not in FIRST_MONTH_STEM:
        raise ValueError("invalid heavenly stem")
    if not isinstance(effective_month_ordinal, int) or isinstance(effective_month_ordinal, bool):
        raise ValueError("effective_month_ordinal must be int")
    if not 1 <= effective_month_ordinal <= 13:
        raise ValueError("effective_month_ordinal must be 1..13")
    start = GAN.index(FIRST_MONTH_STEM[year_stem])
    offset = effective_month_ordinal - 1
    return GAN[(start + offset) % 10], MONTH_ZHI[offset % 12]


def five_mouse_hour(day_stem: str, hour_branch: str) -> tuple[str, str]:
    if day_stem not in FIRST_HOUR_STEM:
        raise ValueError("invalid heavenly stem")
    if hour_branch not in ZHI:
        raise ValueError("invalid earthly branch")
    branch_index = ZHI.index(hour_branch)
    start = GAN.index(FIRST_HOUR_STEM[day_stem])
    return GAN[(start + branch_index) % 10], hour_branch
