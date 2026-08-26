#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build reproducible public qualification evidence for Ziwei month boundaries.

Production formulas remain owned by ``engine.ziwei.month`` and
``engine.ziwei.fine_cycle_stems``.  This tool qualifies those existing rules
against pinned ``lunar-python==1.4.8`` lunar-month continuity and binds the
existing lunar-lite Phase 2B source-contract report without pretending that
lunar-lite can directly execute the rare leap-twelfth second-half case.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lunar_python import LunarMonth, LunarYear

from engine.calendar.models import (
    CalendarContext,
    CalendarInput,
    CalendarPolicies,
    LunarDate,
    LunarProviderMetadata,
    NormalizedTime,
    ProviderBundle,
    TimezoneProviderMetadata,
    ValidationCheck,
    ValidationMetadata,
)
from engine.calendar.sexagenary import five_tiger_month, lunar_year_stem
from engine.ziwei.fine_cycle_stems import (
    FINE_CYCLE_PROFILE_ID,
    FINE_CYCLE_RULE_VERSION,
    resolve_month_stem,
)
from engine.ziwei.month import effective_lunar_month


REPORT_PATH = ROOT / "qualification" / "ziwei" / "month_boundary" / "public-lunar-python-1.4.8.json"
PHASE2B_ANCHOR_PATH = ROOT / "qualification" / "ziwei" / "phase2b" / "public-lunar-lite-1d104fff.json"
ORACLE_PACKAGE = "lunar-python"
ORACLE_VERSION = "1.4.8"
ORACLE_SOURCE_REVISION = "000c8a3d74eed098d6256a28fdd51b869324c559"
LUNAR_LITE_SOURCE = "SylarLong/lunar-lite"
LUNAR_LITE_REVISION = "1d104fffa31609e9f112898cc57545827e8d57ae"
LUNAR_LITE_VERSION = "0.2.8"
LUNAR_LITE_BRANCH_TABLE_SIZE = 12
ORDINARY_YEARS = (1901, 1984, 2000, 2023, 2033, 2099)
LEAP_CASES = (
    (1984, 10),
    (2014, 9),
    (2017, 6),
    (2020, 4),
    (2023, 2),
    (2033, 11),
    (1574, 12),
)


def _context(lunar_year: int, lunar_month: int, lunar_day: int, is_leap: bool) -> CalendarContext:
    civil = date(lunar_year, 1, 1)
    local = datetime(lunar_year, 1, 1, 12, 0, tzinfo=timezone.utc)
    status = "validated" if 1901 <= lunar_year <= 2100 else "out_of_validated_range"
    return CalendarContext(
        "1.0",
        "qualification",
        CalendarInput(local.strftime("%Y-%m-%dT%H:%M:%S"), "UTC"),
        NormalizedTime(local, local, "+00:00", civil, "UTC", "午"),
        LunarDate(lunar_year, lunar_month, lunar_day, is_leap),
        ProviderBundle(
            LunarProviderMetadata("lunar-python", ORACLE_VERSION, ORACLE_SOURCE_REVISION),
            TimezoneProviderMetadata("qualification", "n/a", "n/a", "n/a"),
        ),
        ValidationMetadata(
            ValidationCheck(status, "month-boundary-qualification"),
            ValidationCheck("validated", "fixed-utc"),
            status,
            "1901-01-01/2100-12-31",
            None,
            (),
        ),
        CalendarPolicies("UTC qualification fixture", "civil midnight", "fixed noon", False),
    )


def _project_month(lunar_year: int, lunar_month: int, lunar_day: int, is_leap: bool) -> Tuple[str, int, str]:
    resolved = resolve_month_stem(_context(lunar_year, lunar_month, lunar_day, is_leap))
    effective = effective_lunar_month(lunar_month, lunar_day, is_leap)
    return resolved.heavenly_stem + resolved.earthly_branch, effective, resolved.reference


def _oracle_month(lunar_year: int, lunar_month: int):
    item = LunarMonth.fromYm(lunar_year, lunar_month)
    if item is None:
        raise RuntimeError("lunar-python has no lunar month %s/%s" % (lunar_year, lunar_month))
    return item


def _record(
    checks: List[Dict[str, object]],
    mismatches: List[Dict[str, object]],
    *,
    case_id: str,
    category: str,
    project_ganzhi: str,
    oracle_ganzhi: str,
    project_effective_month: int,
    oracle_effective_year: int,
    oracle_effective_month: int,
    reference: str,
) -> None:
    row = {
        "case_id": case_id,
        "category": category,
        "project_ganzhi": project_ganzhi,
        "oracle_ganzhi": oracle_ganzhi,
        "project_effective_month": project_effective_month,
        "oracle_effective_year": oracle_effective_year,
        "oracle_effective_month": oracle_effective_month,
        "project_reference": reference,
        "matched": project_ganzhi == oracle_ganzhi and project_effective_month == abs(oracle_effective_month),
    }
    checks.append(row)
    if not row["matched"]:
        mismatches.append(row)


def _ordinary_checks(checks: List[Dict[str, object]], mismatches: List[Dict[str, object]]) -> int:
    cases = 0
    for year in ORDINARY_YEARS:
        for month in range(1, 13):
            oracle = _oracle_month(year, month)
            project_ganzhi, effective, reference = _project_month(year, month, 1, False)
            _record(
                checks,
                mismatches,
                case_id="ordinary-%04d-%02d" % (year, month),
                category="ordinary_lunar_month",
                project_ganzhi=project_ganzhi,
                oracle_ganzhi=oracle.getGanZhi(),
                project_effective_month=effective,
                oracle_effective_year=oracle.getYear(),
                oracle_effective_month=oracle.getMonth(),
                reference=reference,
            )
            cases += 1
    return cases


def _leap_checks(checks: List[Dict[str, object]], mismatches: List[Dict[str, object]]) -> Tuple[int, Dict[str, object]]:
    cases = 0
    leap_twelfth: Dict[str, object] = {}
    for year, expected_leap in LEAP_CASES:
        actual_leap = LunarYear.fromYear(year).getLeapMonth()
        if actual_leap != expected_leap:
            raise RuntimeError(
                "pinned lunar-python leap-month identity changed for %s: expected %s got %s"
                % (year, expected_leap, actual_leap)
            )
        leap = _oracle_month(year, -expected_leap)
        following = leap.next(1)
        if following is None:
            raise RuntimeError("lunar-python could not resolve month after leap %s/%s" % (year, expected_leap))

        before_ganzhi, before_effective, before_reference = _project_month(year, expected_leap, 15, True)
        _record(
            checks,
            mismatches,
            case_id="leap-%04d-%02d-day15" % (year, expected_leap),
            category="leap_first_half",
            project_ganzhi=before_ganzhi,
            oracle_ganzhi=leap.getGanZhi(),
            project_effective_month=before_effective,
            oracle_effective_year=leap.getYear(),
            oracle_effective_month=leap.getMonth(),
            reference=before_reference,
        )
        cases += 1

        after_ganzhi, after_effective, after_reference = _project_month(year, expected_leap, 16, True)
        _record(
            checks,
            mismatches,
            case_id="leap-%04d-%02d-day16" % (year, expected_leap),
            category="leap_second_half_next_month_continuity",
            project_ganzhi=after_ganzhi,
            oracle_ganzhi=following.getGanZhi(),
            project_effective_month=after_effective,
            oracle_effective_year=following.getYear(),
            oracle_effective_month=following.getMonth(),
            reference=after_reference,
        )
        cases += 1

        if expected_leap == 12:
            leap_twelfth = {
                "historical_lunar_year": year,
                "oracle_leap_month": leap.getMonth(),
                "oracle_following_year": following.getYear(),
                "oracle_following_month": following.getMonth(),
                "oracle_following_ganzhi": following.getGanZhi(),
                "project_day15_ganzhi": before_ganzhi,
                "project_day16_ganzhi": after_ganzhi,
                "project_day16_effective_month": after_effective,
                "qualified": (
                    following.getYear() == year + 1
                    and following.getMonth() == 1
                    and after_effective == 1
                    and after_ganzhi == following.getGanZhi()
                ),
            }
    if not leap_twelfth:
        raise RuntimeError("leap-twelfth qualification case was not constructed")
    return cases, leap_twelfth


def _ordinal_wrap_property() -> Dict[str, object]:
    representatives: Dict[str, int] = {}
    year = 2000
    while len(representatives) < 10:
        stem = lunar_year_stem(year)
        representatives.setdefault(stem, year)
        year += 1
        if year > 2020:
            raise RuntimeError("could not obtain all ten lunar year stems")
    failures = []
    for stem, representative in sorted(representatives.items()):
        current = "".join(five_tiger_month(stem, 13))
        following = "".join(five_tiger_month(lunar_year_stem(representative + 1), 1))
        if current != following:
            failures.append({"year_stem": stem, "year": representative, "ordinal13": current, "next_year_month1": following})
    return {
        "year_stems": len(representatives),
        "cases": len(representatives),
        "failures": failures,
        "passed": not failures,
    }


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
    if "leap_twelfth_month_second_half" not in payload.get("not_externally_covered", []):
        raise RuntimeError("Phase 2B lunar-lite report no longer records the leap-twelfth limitation")
    return {
        "source_name": payload["source_name"],
        "source_revision": payload["source_revision"],
        "package_version": payload["package_version"],
        "status": payload["status"],
        "cases_checked": payload["cases_checked"],
        "cases_matched": payload["cases_matched"],
        "direct_runtime_limit": {
            "case": "leap_twelfth_month_second_half",
            "normal_month_index_expression": "abs(lunarMonth) - 1 + fixLeap",
            "leap_twelfth_second_half_index": 12,
            "branch_table_entries": LUNAR_LITE_BRANCH_TABLE_SIZE,
            "direct_oracle_usable": False,
            "reason": "index 12 is outside a 12-entry zero-based monthly branch table",
        },
    }


def build_report() -> Dict[str, object]:
    installed = importlib.metadata.version(ORACLE_PACKAGE)
    if installed != ORACLE_VERSION:
        raise RuntimeError("qualification requires lunar-python==%s, got %s" % (ORACLE_VERSION, installed))

    checks: List[Dict[str, object]] = []
    mismatches: List[Dict[str, object]] = []
    ordinary_cases = _ordinary_checks(checks, mismatches)
    leap_cases, leap_twelfth = _leap_checks(checks, mismatches)
    wrap = _ordinal_wrap_property()
    anchor = _phase2b_anchor()

    if not wrap["passed"]:
        mismatches.extend(wrap["failures"])

    result = "PASS" if not mismatches and leap_twelfth.get("qualified") else "FAIL"
    return {
        "schema_version": "1.0",
        "qualification": "ziwei_month_boundary",
        "project_profile": {
            "profile_id": FINE_CYCLE_PROFILE_ID,
            "rule_version": FINE_CYCLE_RULE_VERSION,
            "month_boundary": "lunar month; leap days 1-15 original month, day 16+ next effective month",
            "late_zi_month_rule": "23:00 does not independently advance the month layer",
        },
        "oracle": {
            "package": ORACLE_PACKAGE,
            "version": ORACLE_VERSION,
            "source_revision": ORACLE_SOURCE_REVISION,
            "month_api": "LunarMonth.getGanZhi + LunarMonth.next(1)",
            "runtime_authority": False,
        },
        "phase2b_lunar_lite_anchor": anchor,
        "coverage": {
            "ordinary_months": {"years": list(ORDINARY_YEARS), "months_per_year": 12, "cases": ordinary_cases},
            "leap_month_boundaries": {
                "cases": leap_cases,
                "vectors": [{"lunar_year": year, "leap_month": month} for year, month in LEAP_CASES],
                "boundary_days": [15, 16],
            },
            "leap_twelfth_month_second_half": leap_twelfth,
            "ordinal_13_to_next_year_month_1_property": wrap,
            "adjacent_integration_boundaries": {
                "qualification": "tests/test_ziwei_month_boundary_qualification.py owns lunar month/year transitions, 23:00 neutrality, DST responsibility, monthly source reuse, and generated-runtime parity",
            },
        },
        "checks_count": len(checks),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches[:20],
        "result": result,
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
        print("Ziwei month-boundary qualification evidence is missing: %s" % path, file=sys.stderr)
        return False
    actual = path.read_text(encoding="utf-8")
    if actual != expected:
        print("Ziwei month-boundary qualification evidence is out of date", file=sys.stderr)
        return False
    print("Ziwei month-boundary qualification evidence is up to date")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify committed evidence matches a fresh qualification run")
    args = parser.parse_args()
    if args.check:
        raise SystemExit(0 if check_report() else 1)
    report = write_report()
    print("Built Ziwei month-boundary qualification: %s (%s mismatches)" % (REPORT_PATH, report["mismatch_count"]))
    print(_canonical_json(report), end="")
    raise SystemExit(0 if report["result"] == "PASS" else 1)


if __name__ == "__main__":
    main()
