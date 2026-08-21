#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import date, timedelta
from importlib.metadata import version
from pathlib import Path

from lunar_python import Solar

EXPECTED_VERSION = "1.4.8"
START_YEAR = 1901
END_YEAR = 2100
HKO_TEXT_URL = "https://www.hko.gov.hk/tc/gts/time/calendar/text/files/T{year}c.txt"

# HKO documents these new moons as close enough to midnight that a one-day
# difference can occur. Only a contiguous mismatch run beginning exactly on
# one of these dates is observation-only, capped at 31 days. Any mismatch
# outside those runs remains a strict failure.
KNOWN_HKO_UNCERTAIN_NEW_MOONS = {
    date(2057, 9, 28),
    date(2089, 9, 4),
    date(2097, 8, 7),
}
MAX_BOUNDARY_WINDOW_DAYS = 31

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", type=Path, required=True)
    return parser.parse_args()


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


def fetch_hko_year(year: int, cache_dir: Path) -> str:
    cache_dir.mkdir(parents=True, exist_ok=True)
    target = cache_dir / f"T{year}c.txt"
    if target.exists():
        return decode_hko(target.read_bytes())

    request = urllib.request.Request(
        HKO_TEXT_URL.format(year=year),
        headers={"User-Agent": "Metaphysics-Lab-Provider-Qualification/2.0"},
    )
    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = response.read()
            target.write_bytes(payload)
            return decode_hko(payload)
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt < 3:
                time.sleep(attempt)
    assert last_error is not None
    raise last_error


def expected_days_in_year(year: int) -> int:
    return 366 if year % 400 == 0 or (year % 4 == 0 and year % 100 != 0) else 365


def compare_year(year: int, cache_dir: Path) -> tuple[int, dict[date, str]]:
    text = fetch_hko_year(year, cache_dir)
    records: list[tuple[date, str]] = []
    for line in text.splitlines():
        match = LINE_RE.match(line)
        if not match:
            continue
        y, m, d, lunar_token = match.groups()
        records.append((date(int(y), int(m), int(d)), lunar_token.strip()))

    expected_rows = expected_days_in_year(year)
    if len(records) != expected_rows:
        return 0, {
            date(year, 1, 1): f"HKO {year}: expected {expected_rows} daily rows, got {len(records)}"
        }

    mismatches: dict[date, str] = {}
    current_month: int | None = None
    current_lunar_year: int | None = None

    for civil, token in records:
        lunar = Solar.fromYmd(civil.year, civil.month, civil.day).getLunar()
        actual = (lunar.getYear(), lunar.getMonth(), lunar.getDay())

        if token in DAYS:
            expected_day = DAYS[token]
            if current_month is None:
                # Before the first explicit month marker of the Gregorian year,
                # HKO states only the lunar day. Those dates belong to the prior
                # lunar year; compare exactly the facts available from the table.
                if lunar.getYear() != year - 1 or lunar.getDay() != expected_day:
                    mismatches[civil] = (
                        f"{civil.isoformat()}: HKO=(year {year - 1}, day {expected_day}, month unstated), "
                        f"lunar_python={actual}"
                    )
            else:
                expected = (current_lunar_year, current_month, expected_day)
                if actual != expected:
                    mismatches[civil] = (
                        f"{civil.isoformat()}: HKO={expected}, lunar_python={actual}"
                    )
        else:
            try:
                current_month = parse_hko_month(token)
            except KeyError:
                mismatches[civil] = f"{civil.isoformat()}: unrecognized HKO lunar token {token!r}"
                continue

            if current_month == 1:
                current_lunar_year = year
            elif current_lunar_year is None:
                current_lunar_year = year - 1

            expected = (current_lunar_year, current_month, 1)
            if actual != expected:
                mismatches[civil] = (
                    f"{civil.isoformat()}: HKO={expected}, lunar_python={actual}"
                )

    return len(records), mismatches


def split_boundary_observations(
    mismatches: dict[date, str],
) -> tuple[list[str], list[str], list[str]]:
    remaining = dict(mismatches)
    observations: list[str] = []
    boundary_summaries: list[str] = []

    for start in sorted(KNOWN_HKO_UNCERTAIN_NEW_MOONS):
        if start not in remaining:
            boundary_summaries.append(f"{start.isoformat()}: no mismatch")
            continue

        current = start
        consumed: list[date] = []
        while current in remaining and len(consumed) < MAX_BOUNDARY_WINDOW_DAYS:
            consumed.append(current)
            observations.append(remaining.pop(current))
            current += timedelta(days=1)

        if current in remaining:
            boundary_summaries.append(
                f"{start.isoformat()}: mismatch run exceeds {MAX_BOUNDARY_WINDOW_DAYS} days"
            )
        else:
            boundary_summaries.append(
                f"{start.isoformat()}: observation window {consumed[0].isoformat()}..{consumed[-1].isoformat()} "
                f"({len(consumed)} days)"
            )

    strict = [remaining[d] for d in sorted(remaining)]
    return strict, observations, boundary_summaries


def main() -> int:
    args = parse_args()
    installed = version("lunar_python")
    if installed != EXPECTED_VERSION:
        print(f"FAIL: expected lunar_python {EXPECTED_VERSION}, got {installed}")
        return 2

    all_mismatches: dict[date, str] = {}
    compared = 0
    years_checked = 0

    for year in range(START_YEAR, END_YEAR + 1):
        count, mismatches = compare_year(year, args.cache_dir)
        compared += count
        years_checked += 1
        all_mismatches.update(mismatches)
        if year == START_YEAR or year == END_YEAR or year % 10 == 0:
            print(f"progress: through {year}, rows={compared}, mismatches_seen={len(all_mismatches)}")

    strict, observations, boundary_summaries = split_boundary_observations(all_mismatches)

    print(f"lunar_python version: {installed}")
    print(f"years checked: {START_YEAR}-{END_YEAR} ({years_checked} years)")
    print(f"daily rows compared: {compared}")
    print(f"expected exhaustive rows: 73049")
    print(f"strict mismatches: {len(strict)}")
    print(f"boundary observations: {len(observations)}")
    for item in boundary_summaries:
        print(f"BOUNDARY_SUMMARY: {item}")
    for item in observations[:100]:
        print(f"BOUNDARY_OBSERVATION: {item}")
    for item in strict[:100]:
        print(f"MISMATCH: {item}")

    if compared != 73049:
        print(f"FAIL: exhaustive row count mismatch: expected 73049, got {compared}")
        return 3
    if strict:
        return 1

    print("EXHAUSTIVE_QUALIFICATION_PASS: zero mismatches outside HKO-documented boundary windows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
