#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
import urllib.request
from datetime import date
from importlib.metadata import version

from lunar_python import Solar

EXPECTED_VERSION = "1.4.8"
STRICT_YEARS = (1901, 1950, 1984, 2000, 2020, 2025, 2026, 2033, 2100)
OBSERVATION_YEARS = (2057, 2089, 2097)
YEARS = STRICT_YEARS + OBSERVATION_YEARS
HKO_TEXT_URL = "https://www.hko.gov.hk/tc/gts/time/calendar/text/files/T{year}c.txt"

# HKO explicitly says these future new moons are close enough to midnight that
# the relevant lunar-month dates may differ by one day. Those years therefore
# remain observation-only and cannot be used as strict qualification gates.
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

LINE_RE = re.compile(r"^\s*(\d{4})年(\d{1,2})月(\d{1,2})日\s+(\S+)")


def parse_hko_month(text: str) -> int:
    text = text.strip()
    leap = text.startswith(("閏", "闰"))
    if leap:
        text = text[1:]
    month = MONTHS[text]
    return -month if leap else month


def decode_hko(payload: bytes) -> str:
    last_error: UnicodeDecodeError | None = None
    for encoding in ("utf-8-sig", "big5", "cp950"):
        try:
            return payload.decode(encoding)
        except UnicodeDecodeError as exc:
            last_error = exc
    assert last_error is not None
    raise last_error


def fetch_hko_year(year: int) -> str:
    request = urllib.request.Request(
        HKO_TEXT_URL.format(year=year),
        headers={"User-Agent": "Metaphysics-Lab-Provider-Qualification/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return decode_hko(response.read())


def expected_days_in_year(year: int) -> int:
    return 366 if year % 400 == 0 or (year % 4 == 0 and year % 100 != 0) else 365


def compare_year(year: int) -> tuple[int, list[str]]:
    text = fetch_hko_year(year)
    records = []
    for line in text.splitlines():
        match = LINE_RE.match(line)
        if not match:
            continue
        y, m, d, lunar_token = match.groups()
        records.append((date(int(y), int(m), int(d)), lunar_token.strip()))

    expected_rows = expected_days_in_year(year)
    if len(records) != expected_rows:
        return 0, [f"HKO {year}: expected {expected_rows} daily rows, got {len(records)}"]

    mismatches: list[str] = []
    current_month: int | None = None
    current_lunar_year: int | None = None
    compared = 0

    for civil, token in records:
        lunar = Solar.fromYmd(civil.year, civil.month, civil.day).getLunar()
        actual = (lunar.getYear(), lunar.getMonth(), lunar.getDay())

        if token in DAYS:
            expected_day = DAYS[token]
            if current_month is None:
                # Before the first explicit lunar-month marker of the Gregorian year,
                # HKO gives only the day number. We therefore compare only the facts
                # the source actually states: previous lunar year + lunar day.
                if lunar.getYear() != year - 1 or lunar.getDay() != expected_day:
                    mismatches.append(
                        f"{civil.isoformat()}: HKO=(year {year - 1}, day {expected_day}, month unstated), "
                        f"lunar_python={actual}"
                    )
            else:
                expected = (current_lunar_year, current_month, expected_day)
                if actual != expected:
                    mismatches.append(
                        f"{civil.isoformat()}: HKO={expected}, lunar_python={actual}"
                    )
        else:
            try:
                current_month = parse_hko_month(token)
            except KeyError:
                mismatches.append(f"{civil.isoformat()}: unrecognized HKO lunar token {token!r}")
                continue
            if abs(current_month) == 1 and current_month > 0:
                current_lunar_year = year
            if current_lunar_year is None:
                mismatches.append(
                    f"{civil.isoformat()}: HKO month marker {token!r} appeared before lunar year could be resolved"
                )
                continue
            expected = (current_lunar_year, current_month, 1)
            if actual != expected:
                mismatches.append(
                    f"{civil.isoformat()}: HKO={expected}, lunar_python={actual}"
                )

        compared += 1

    return compared, mismatches


def main() -> int:
    installed = version("lunar_python")
    if installed != EXPECTED_VERSION:
        print(f"FAIL: expected lunar_python {EXPECTED_VERSION}, got {installed}")
        return 2

    strict_mismatches: list[str] = []
    observations: list[str] = []
    compared = 0

    for year in YEARS:
        count, mismatches = compare_year(year)
        compared += count
        if year in STRICT_YEARS:
            strict_mismatches.extend(mismatches)
        else:
            observations.extend(f"{year}: {item}" for item in mismatches)

    print(f"lunar_python version: {installed}")
    print(f"strict years: {', '.join(str(y) for y in STRICT_YEARS)}")
    print(f"HKO uncertainty observation years: {', '.join(str(y) for y in OBSERVATION_YEARS)}")
    print(f"daily rows compared: {compared}")
    print(f"strict mismatches: {len(strict_mismatches)}")
    print(f"observation-year mismatches: {len(observations)}")
    print(
        "HKO documented uncertain new moons: "
        + ", ".join(sorted(d.isoformat() for d in KNOWN_HKO_UNCERTAIN_NEW_MOONS))
    )

    for item in observations[:50]:
        print(f"BOUNDARY_OBSERVATION: {item}")
    for item in strict_mismatches[:50]:
        print(f"MISMATCH: {item}")

    if strict_mismatches:
        return 1

    print("QUALIFICATION_PASS: zero mismatches in all strict HKO archive years")
    return 0


if __name__ == "__main__":
    sys.exit(main())
