#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build reproducible public qualification evidence for Bazi flow-day/hour.

The Project formulas remain owned by ``engine.bazi.calendar``.  This tool
compares those formulas against pinned ``lunar-python==1.4.8`` using
EightChar sect 1, which matches the Project 23:00 early-Zi convention.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lunar_python import Solar

from engine.bazi.calendar import GAN, ZHI, day_pillar, time_pillar


REPORT_PATH = ROOT / "qualification" / "bazi" / "flow_time" / "public-lunar-python-1.4.8.json"
ORACLE_PACKAGE = "lunar-python"
ORACLE_VERSION = "1.4.8"
ORACLE_SOURCE_REVISION = "000c8a3d74eed098d6256a28fdd51b869324c559"
ORACLE_SECT = 1
DAY_SAMPLE_START = date(1980, 1, 1)
DAY_SAMPLE_END = date(2050, 12, 31)
DAY_SAMPLE_STEP_DAYS = 97
BOUNDARY_ZONES = (
    "Asia/Taipei",
    "Asia/Tokyo",
    "America/New_York",
    "Europe/London",
)
SEXAGENARY = tuple(GAN[i % 10] + ZHI[i % 12] for i in range(60))
HOUR_MIDPOINTS = (0, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21)


def _oracle_day_time(dt: datetime) -> Tuple[str, str]:
    solar = Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    eight_char = solar.getLunar().getEightChar()
    eight_char.setSect(ORACLE_SECT)
    return eight_char.getDay(), eight_char.getTime()


def _mismatch(kind: str, dt: datetime, project_day: str, project_time: str, oracle_day: str, oracle_time: str) -> Dict[str, str]:
    return {
        "kind": kind,
        "local_datetime": dt.isoformat(),
        "project_day": project_day,
        "project_time": project_time,
        "oracle_day": oracle_day,
        "oracle_time": oracle_time,
    }


def _compare(kind: str, dt: datetime, mismatches: List[Dict[str, str]], compare_time: bool = True) -> None:
    project_day = day_pillar(dt)
    project_time = time_pillar(dt)
    oracle_day, oracle_time = _oracle_day_time(dt)
    if project_day != oracle_day or (compare_time and project_time != oracle_time):
        mismatches.append(_mismatch(kind, dt, project_day, project_time, oracle_day, oracle_time))


def _build_day_samples(mismatches: List[Dict[str, str]]) -> int:
    zone = ZoneInfo("Asia/Taipei")
    current = DAY_SAMPLE_START
    cases = 0
    while current <= DAY_SAMPLE_END:
        dt = datetime(current.year, current.month, current.day, 12, 0, tzinfo=zone)
        _compare("day_sample", dt, mismatches, compare_time=False)
        cases += 1
        current += timedelta(days=DAY_SAMPLE_STEP_DAYS)
    return cases


def _build_boundary_vectors(mismatches: List[Dict[str, str]]) -> int:
    base = date(2026, 8, 20)
    local_vectors = (
        (base, 22, 59),
        (base, 23, 0),
        (base, 23, 59),
        (base + timedelta(days=1), 0, 0),
    )
    cases = 0
    for zone_name in BOUNDARY_ZONES:
        zone = ZoneInfo(zone_name)
        for local_date, hour, minute in local_vectors:
            dt = datetime(local_date.year, local_date.month, local_date.day, hour, minute, tzinfo=zone)
            _compare("early_zi_boundary", dt, mismatches)
            cases += 1
    return cases


def _build_transition_vectors(mismatches: List[Dict[str, str]]) -> int:
    zone = ZoneInfo("Asia/Taipei")
    dates = (
        date(1999, 12, 31),
        date(2000, 1, 1),
        date(2000, 2, 28),
        date(2000, 2, 29),
        date(2000, 3, 1),
        date(2024, 2, 28),
        date(2024, 2, 29),
        date(2024, 3, 1),
        date(2025, 12, 31),
        date(2026, 1, 1),
        date(2032, 2, 28),
        date(2032, 2, 29),
        date(2032, 3, 1),
    )
    for value in dates:
        dt = datetime(value.year, value.month, value.day, 12, 0, tzinfo=zone)
        _compare("gregorian_transition", dt, mismatches)
    return len(dates)


def _representative_date_by_stem() -> Dict[str, date]:
    zone = ZoneInfo("Asia/Taipei")
    current = date(2026, 1, 1)
    representatives: Dict[str, date] = {}
    while len(representatives) < len(GAN):
        dt = datetime(current.year, current.month, current.day, 12, 0, tzinfo=zone)
        representatives.setdefault(day_pillar(dt)[0], current)
        current += timedelta(days=1)
        if (current - date(2026, 1, 1)).days > 20:
            raise AssertionError("could not obtain representatives for all ten day stems")
    return representatives


def _build_five_rat_matrix(mismatches: List[Dict[str, str]]) -> int:
    zone = ZoneInfo("Asia/Taipei")
    representatives = _representative_date_by_stem()
    cases = 0
    for stem in GAN:
        value = representatives[stem]
        for branch_index, hour in enumerate(HOUR_MIDPOINTS):
            dt = datetime(value.year, value.month, value.day, hour, 30, tzinfo=zone)
            project_day = day_pillar(dt)
            if project_day[0] != stem:
                raise AssertionError("representative day stem changed unexpectedly")
            _compare("five_rat_matrix", dt, mismatches)
            if time_pillar(dt)[1] != ZHI[branch_index]:
                raise AssertionError("Project hour branch progression is not canonical")
            cases += 1
    return cases


def _build_consecutive_day_property() -> int:
    zone = ZoneInfo("Asia/Taipei")
    start = date(2025, 1, 1)
    pairs = 730
    for offset in range(pairs):
        current = start + timedelta(days=offset)
        following = current + timedelta(days=1)
        current_name = day_pillar(datetime(current.year, current.month, current.day, 12, 0, tzinfo=zone))
        following_name = day_pillar(datetime(following.year, following.month, following.day, 12, 0, tzinfo=zone))
        if (SEXAGENARY.index(following_name) - SEXAGENARY.index(current_name)) % 60 != 1:
            raise AssertionError("consecutive Project day pillars must advance exactly one sexagenary step")
    return pairs


def build_report() -> Dict[str, object]:
    installed = importlib.metadata.version(ORACLE_PACKAGE)
    if installed != ORACLE_VERSION:
        raise RuntimeError("qualification requires lunar-python==%s, got %s" % (ORACLE_VERSION, installed))

    mismatches: List[Dict[str, str]] = []
    day_cases = _build_day_samples(mismatches)
    boundary_cases = _build_boundary_vectors(mismatches)
    transition_cases = _build_transition_vectors(mismatches)
    five_rat_cases = _build_five_rat_matrix(mismatches)
    consecutive_pairs = _build_consecutive_day_property()

    return {
        "schema_version": "1.0",
        "qualification": "bazi_flow_day_hour",
        "project_profile": {
            "engine": "Project Bazi Calendar Engine",
            "day_rollover": "23:00 early-Zi",
            "day_formula": "offset = Gregorian effective civil date JDN - 11",
            "hour_formula": "(day_stem_index mod 5 * 2 + hour_branch_index) mod 10",
        },
        "oracle": {
            "package": ORACLE_PACKAGE,
            "version": ORACLE_VERSION,
            "source_revision": ORACLE_SOURCE_REVISION,
            "eight_char_sect": ORACLE_SECT,
            "sect_meaning": "late-Zi day is counted as next day",
        },
        "coverage": {
            "day_samples": {
                "start": DAY_SAMPLE_START.isoformat(),
                "end": DAY_SAMPLE_END.isoformat(),
                "step_days": DAY_SAMPLE_STEP_DAYS,
                "cases": day_cases,
            },
            "early_zi_boundary": {
                "zones": list(BOUNDARY_ZONES),
                "local_times": ["22:59", "23:00", "23:59", "00:00 next civil day"],
                "cases": boundary_cases,
            },
            "gregorian_transitions": {"cases": transition_cases},
            "five_rat_matrix": {
                "day_stems": 10,
                "hour_branches": 12,
                "cases": five_rat_cases,
            },
            "consecutive_day_property": {"pairs": consecutive_pairs},
            "dst_responsibility": {
                "owner": "Calendar Resolver",
                "qualification": "tests/test_bazi_flow_time_qualification.py verifies nonexistent/ambiguous local time handling before Bazi flow-time calculation",
            },
            "generated_runtime_parity": {
                "qualification": "tests/test_bazi_flow_time_qualification.py compares modular and generated resolve_forecast_context for ordinary and 23:xx inputs"
            },
        },
        "mismatch_count": len(mismatches),
        "mismatches": mismatches[:20],
        "result": "PASS" if not mismatches else "FAIL",
        "maturity_promotion": False,
    }


def _canonical_json(report: Dict[str, object]) -> str:
    return json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def write_report(path: Path = REPORT_PATH) -> Dict[str, object]:
    report = build_report()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_canonical_json(report), encoding="utf-8")
    return report


def check_report(path: Path = REPORT_PATH) -> bool:
    expected = _canonical_json(build_report())
    if not path.is_file():
        print("Bazi flow-time qualification evidence is missing: %s" % path, file=sys.stderr)
        return False
    actual = path.read_text(encoding="utf-8")
    if actual != expected:
        print("Bazi flow-time qualification evidence is out of date", file=sys.stderr)
        return False
    print("Bazi flow-time qualification evidence is up to date")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify committed evidence matches a fresh qualification run")
    args = parser.parse_args()
    if args.check:
        raise SystemExit(0 if check_report() else 1)
    report = write_report()
    print("Built Bazi flow-time qualification: %s (%s mismatches)" % (REPORT_PATH, report["mismatch_count"]))
    raise SystemExit(0 if report["result"] == "PASS" else 1)


if __name__ == "__main__":
    main()
