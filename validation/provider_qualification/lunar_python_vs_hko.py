#!/usr/bin/env python3
from __future__ import annotations

import csv
import io
import sys
import urllib.request
from datetime import date
from importlib.metadata import version

from lunar_python import Solar

EXPECTED_VERSION = "1.4.8"
YEARS = (1901, 1950, 1984, 2000, 2020, 2025, 2026, 2033, 2057, 2089, 2097, 2100)
HKO_URL = "https://data.weather.gov.hk/weatherAPI/hko_data/calendar/nongli_calendar_{year}.csv"

# HKO explicitly marks these future new-moon dates as potentially differing by one day
# because the calculated new moon is close to midnight.
KNOWN_HKO_UNCERTAIN_NEW_MOONS = {
    date(2057, 9, 28),
    date(2089, 9, 4),
    date(2097, 8, 7),
}

MONTHS = {
    "正月": 1,
    "一月": 1,
    "二月": 2,
    "三月": 3,
    "四月": 4,
    "五月": 5,
    "六月": 6,
    "七月": 7,
    "八月": 8,
    "九月": 9,
    "十月": 10,
    "十一月": 11,
    "十二月": 12,
}

DAYS = {
    "初一": 1, "初二": 2, "初三": 3, "初四": 4, "初五": 5,
    "初六": 6, "初七": 7, "初八": 8, "初九": 9, "初十": 10,
    "十一": 11, "十二": 12, "十三": 13, "十四": 14, "十五": 15,
    "十六": 16, "十七": 17, "十八": 18, "十九": 19, "二十": 20,
    "廿一": 21, "廿二": 22, "廿三": 23, "廿四": 24, "廿五": 25,
    "廿六": 26, "廿七": 27, "廿八": 28, "廿九": 29, "三十": 30,
}

MONTH_ABBR = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"


def ganzhi_for_year(year: int) -> str:
    return GAN[(year - 4) % 10] + ZHI[(year - 4) % 12] + "年"


def expected_lunar_year(gregorian_year: int, hko_ganzhi: str) -> int:
    if hko_ganzhi == ganzhi_for_year(gregorian_year):
        return gregorian_year
    if hko_ganzhi == ganzhi_for_year(gregorian_year - 1):
        return gregorian_year - 1
    raise AssertionError(
        f"Unexpected HKO Gan-Zhi {hko_ganzhi!r} for Gregorian year {gregorian_year}"
    )


def parse_hko_month(text: str) -> int:
    text = text.strip()
    leap = text.startswith(("閏", "闰"))
    if leap:
        text = text[1:]
    month = MONTHS[text]
    return -month if leap else month


def parse_hko_date(text: str, year: int) -> date:
    day_text, month_text, _ = text.strip().split("-")
    return date(year, MONTH_ABBR[month_text], int(day_text))


def fetch_hko_year(year: int) -> list[dict[str, str]]:
    request = urllib.request.Request(
        HKO_URL.format(year=year),
        headers={"User-Agent": "Metaphysics-Lab-Provider-Qualification/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = response.read().decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(payload)))


def main() -> int:
    installed = version("lunar_python")
    if installed != EXPECTED_VERSION:
        print(f"FAIL: expected lunar_python {EXPECTED_VERSION}, got {installed}")
        return 2

    strict_mismatches: list[str] = []
    boundary_observations: list[str] = []
    compared = 0

    for year in YEARS:
        rows = fetch_hko_year(year)
        expected_days = 366 if year % 400 == 0 or (year % 4 == 0 and year % 100 != 0) else 365
        if len(rows) != expected_days:
            strict_mismatches.append(
                f"HKO {year}: expected {expected_days} rows, got {len(rows)}"
            )
            continue

        for row in rows:
            civil = parse_hko_date(row["Gregorian Date"], year)
            expected = (
                expected_lunar_year(year, row["Chinese year (Gan-Zhi)"].strip()),
                parse_hko_month(row["Lunar month"]),
                DAYS[row["Lunar Date"].strip()],
            )
            lunar = Solar.fromYmd(civil.year, civil.month, civil.day).getLunar()
            actual = (lunar.getYear(), lunar.getMonth(), lunar.getDay())
            compared += 1

            if actual != expected:
                message = f"{civil.isoformat()}: HKO={expected}, lunar_python={actual}"
                if civil in KNOWN_HKO_UNCERTAIN_NEW_MOONS:
                    boundary_observations.append(message)
                else:
                    strict_mismatches.append(message)

    print(f"lunar_python version: {installed}")
    print(f"years checked: {', '.join(str(y) for y in YEARS)}")
    print(f"daily rows compared: {compared}")
    print(f"strict mismatches: {len(strict_mismatches)}")
    print(f"known HKO boundary observations: {len(boundary_observations)}")

    for item in boundary_observations:
        print(f"BOUNDARY_WARNING: {item}")
    for item in strict_mismatches[:50]:
        print(f"MISMATCH: {item}")

    if strict_mismatches:
        return 1

    print("QUALIFICATION_PASS: no mismatches outside HKO's documented new-moon uncertainty dates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
