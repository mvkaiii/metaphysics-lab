#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build reproducible public qualification evidence for Ziwei flow-day/hour.

The Project formulas remain owned by ``engine.ziwei.fine_cycle_stems``.
This tool compares the existing daily/hourly stem resolution against pinned
``lunar-python==1.4.8`` day/hour Ganzhi behavior and also binds the result to
the already-committed lunar-lite Phase 2B public qualification anchor.

The public oracle is qualification evidence only; it is not Project runtime
authority and this tool does not promote capability maturity.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lunar_python import Solar

from engine.calendar.resolver import resolve_calendar
from engine.ziwei.fine_cycle_stems import (
    DAY_BOUNDARY_PROFILE,
    FINE_CYCLE_PROFILE_ID,
    FINE_CYCLE_RULE_VERSION,
    resolve_day_stem,
    resolve_hour_stem,
)


REPORT_PATH = ROOT / "qualification" / "ziwei" / "flow_time" / "public-lunar-python-1.4.8.json"
PHASE2B_ANCHOR_PATH = ROOT / "qualification" / "ziwei" / "phase2b" / "public-lunar-lite-1d104fff.json"
ORACLE_PACKAGE = "lunar-python"
ORACLE_VERSION = "1.4.8"
ORACLE_SOURCE_REVISION = "000c8a3d74eed098d6256a28fdd51b869324c559"
ORACLE_SECT = 1
LUNAR_LITE_SOURCE = "SylarLong/lunar-lite"
LUNAR_LITE_REVISION = "1d104fffa31609e9f112898cc57545827e8d57ae"
LUNAR_LITE_VERSION = "0.2.8"
DAY_SAMPLE_START = date(1980, 1, 1)
DAY_SAMPLE_END = date(2050, 12, 31)
DAY_SAMPLE_STEP_DAYS = 97
BOUNDARY_ZONES = (
    "Asia/Taipei",
    "Asia/Tokyo",
    "America/New_York",
    "Europe/London",
)
HOUR_MIDPOINTS = (0, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21)
GAN = tuple("甲乙丙丁戊己庚辛壬癸")
ZHI = tuple("子丑寅卯辰巳午未申酉戌亥")
SEXAGENARY = tuple(GAN[i % 10] + ZHI[i % 12] for i in range(60))


def _oracle_day_time(dt: datetime) -> Tuple[str, str]:
    solar = Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    eight_char = solar.getLunar().getEightChar()
    eight_char.setSect(ORACLE_SECT)
    return eight_char.getDay(), eight_char.getTime()


def _project_day_time(dt: datetime, timezone_name: str) -> Tuple[str, str, str, str]:
    civil = dt.strftime("%Y-%m-%dT%H:%M:%S")
    resolved = resolve_calendar(civil, timezone_name)
    if not resolved.ok or resolved.context is None:
        raise RuntimeError("Project calendar resolution failed for %s %s: %r" % (civil, timezone_name, resolved))
    day = resolve_day_stem(resolved.context)
    hour = resolve_hour_stem(resolved.context)
    return (
        day.heavenly_stem + day.earthly_branch,
        hour.heavenly_stem + hour.earthly_branch,
        day.effective_date.isoformat(),
        hour.hour_branch or "",
    )


def _mismatch(
    kind: str,
    dt: datetime,
    timezone_name: str,
    project_day: str,
    project_time: str,
    oracle_day: str,
    oracle_time: str,
    effective_date: str,
    hour_branch: str,
) -> Dict[str, str]:
    return {
        "kind": kind,
        "local_datetime": dt.strftime("%Y-%m-%dT%H:%M:%S"),
        "timezone": timezone_name,
        "project_day": project_day,
        "project_time": project_time,
        "oracle_day": oracle_day,
        "oracle_time": oracle_time,
        "project_effective_date": effective_date,
        "project_hour_branch": hour_branch,
    }


def _compare(kind: str, dt: datetime, timezone_name: str, mismatches: List[Dict[str, str]], compare_time: bool = True) -> None:
    project_day, project_time, effective_date, hour_branch = _project_day_time(dt, timezone_name)
    oracle_day, oracle_time = _oracle_day_time(dt)
    if project_day != oracle_day or (compare_time and project_time != oracle_time):
        mismatches.append(
            _mismatch(
                kind,
                dt,
                timezone_name,
                project_day,
                project_time,
                oracle_day,
                oracle_time,
                effective_date,
                hour_branch,
            )
        )


def _build_day_samples(mismatches: List[Dict[str, str]]) -> int:
    current = DAY_SAMPLE_START
    cases = 0
    while current <= DAY_SAMPLE_END:
        dt = datetime(current.year, current.month, current.day, 12, 0)
        _compare("day_sample", dt, "Asia/Taipei", mismatches, compare_time=False)
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
        for local_date, hour, minute in local_vectors:
            dt = datetime(local_date.year, local_date.month, local_date.day, hour, minute)
            _compare("late_zi_boundary", dt, zone_name, mismatches)
            cases += 1
    return cases


def _build_transition_vectors(mismatches: List[Dict[str, str]]) -> int:
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
        dt = datetime(value.year, value.month, value.day, 12, 0)
        _compare("gregorian_transition", dt, "Asia/Taipei", mismatches)
    return len(dates)


def _representative_date_by_oracle_stem() -> Dict[str, date]:
    current = date(2026, 1, 1)
    representatives: Dict[str, date] = {}
    while len(representatives) < len(GAN):
        dt = datetime(current.year, current.month, current.day, 12, 0)
        oracle_day, _ = _oracle_day_time(dt)
        representatives.setdefault(oracle_day[0], current)
        current += timedelta(days=1)
        if (current - date(2026, 1, 1)).days > 20:
            raise AssertionError("could not obtain oracle representatives for all ten day stems")
    return representatives


def _build_five_rat_matrix(mismatches: List[Dict[str, str]]) -> int:
    representatives = _representative_date_by_oracle_stem()
    cases = 0
    for stem in GAN:
        value = representatives[stem]
        for branch_index, hour in enumerate(HOUR_MIDPOINTS):
            dt = datetime(value.year, value.month, value.day, hour, 30)
            _compare("five_rat_matrix", dt, "Asia/Taipei", mismatches)
            _, project_time, _, hour_branch = _project_day_time(dt, "Asia/Taipei")
            if hour_branch != ZHI[branch_index] or project_time[1] != ZHI[branch_index]:
                raise AssertionError("Project Ziwei hour branch progression is not canonical")
            cases += 1
    return cases


def _build_consecutive_day_property() -> int:
    start = date(2025, 1, 1)
    pairs = 730
    for offset in range(pairs):
        current = start + timedelta(days=offset)
        following = current + timedelta(days=1)
        current_day, _, _, _ = _project_day_time(datetime(current.year, current.month, current.day, 12, 0), "Asia/Taipei")
        following_day, _, _, _ = _project_day_time(datetime(following.year, following.month, following.day, 12, 0), "Asia/Taipei")
        if (SEXAGENARY.index(following_day) - SEXAGENARY.index(current_day)) % 60 != 1:
            raise AssertionError("consecutive Project Ziwei day stems must advance exactly one sexagenary step")
    return pairs


def _phase2b_anchor() -> Dict[str, object]:
    payload = json.loads(PHASE2B_ANCHOR_PATH.read_text(encoding="utf-8"))
    expected = {
        "source_name": LUNAR_LITE_SOURCE,
        "source_revision": LUNAR_LITE_REVISION,
        "package_version": LUNAR_LITE_VERSION,
        "status": "PASS",
        "cases_checked": 18,
        "cases_matched": 18,
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            raise RuntimeError("Phase 2B lunar-lite anchor changed: %s=%r" % (key, payload.get(key)))
    if payload.get("mismatches") != []:
        raise RuntimeError("Phase 2B lunar-lite anchor contains mismatches")
    coverage = set(payload.get("external_coverage", []))
    required = {"regular_day_hour", "late_zi_day_hour"}
    if not required.issubset(coverage):
        raise RuntimeError("Phase 2B lunar-lite anchor no longer covers required day/hour boundaries")
    return {
        "source_name": payload["source_name"],
        "source_revision": payload["source_revision"],
        "package_version": payload["package_version"],
        "status": payload["status"],
        "cases_checked": payload["cases_checked"],
        "cases_matched": payload["cases_matched"],
        "required_external_coverage": sorted(required),
    }


def build_report() -> Dict[str, object]:
    installed = importlib.metadata.version(ORACLE_PACKAGE)
    if installed != ORACLE_VERSION:
        raise RuntimeError("qualification requires lunar-python==%s, got %s" % (ORACLE_VERSION, installed))

    phase2b_anchor = _phase2b_anchor()
    mismatches: List[Dict[str, str]] = []
    day_cases = _build_day_samples(mismatches)
    boundary_cases = _build_boundary_vectors(mismatches)
    transition_cases = _build_transition_vectors(mismatches)
    five_rat_cases = _build_five_rat_matrix(mismatches)
    consecutive_pairs = _build_consecutive_day_property()

    return {
        "schema_version": "1.0",
        "qualification": "ziwei_flow_day_hour",
        "project_profile": {
            "profile_id": FINE_CYCLE_PROFILE_ID,
            "rule_version": FINE_CYCLE_RULE_VERSION,
            "day_boundary": DAY_BOUNDARY_PROFILE,
            "day_rule": "23:00 forwards Ziwei effective date exactly once",
            "hour_rule": "Five Rat stem from effective Ziwei day stem + CalendarContext hour branch",
            "calendar_resolver_role": "neutral civil/timezone/DST authority; does not pre-apply Ziwei metaphysical day rollover",
        },
        "oracle": {
            "package": ORACLE_PACKAGE,
            "version": ORACLE_VERSION,
            "source_revision": ORACLE_SOURCE_REVISION,
            "eight_char_sect": ORACLE_SECT,
            "sect_alignment": "comparison only: sect 1 forwards day/hour at 23:00, matching the Project profile's day/hour behavior",
            "runtime_authority": False,
        },
        "phase2b_external_anchor": phase2b_anchor,
        "coverage": {
            "day_samples": {
                "start": DAY_SAMPLE_START.isoformat(),
                "end": DAY_SAMPLE_END.isoformat(),
                "step_days": DAY_SAMPLE_STEP_DAYS,
                "cases": day_cases,
            },
            "late_zi_boundary": {
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
                "qualification": "tests/test_ziwei_flow_time_qualification.py verifies nonexistent/ambiguous local time handling before Ziwei fine-cycle resolution",
            },
            "generated_runtime_parity": {
                "qualification": "tests/test_ziwei_flow_time_qualification.py compares modular and generated daily/hourly forecast context at ordinary and 23:xx inputs"
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
        print("Ziwei flow-time qualification evidence is missing: %s" % path, file=sys.stderr)
        return False
    actual = path.read_text(encoding="utf-8")
    if actual != expected:
        print("Ziwei flow-time qualification evidence is out of date", file=sys.stderr)
        return False
    print("Ziwei flow-time qualification evidence is up to date")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify committed evidence matches a fresh qualification run")
    args = parser.parse_args()
    if args.check:
        raise SystemExit(0 if check_report() else 1)
    report = write_report()
    print("Built Ziwei flow-time qualification: %s (%s mismatches)" % (REPORT_PATH, report["mismatch_count"]))
    print(_canonical_json(report), end="")
    raise SystemExit(0 if report["result"] == "PASS" else 1)


if __name__ == "__main__":
    main()
