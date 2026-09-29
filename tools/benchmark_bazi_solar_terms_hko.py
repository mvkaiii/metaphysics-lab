"""Benchmark solar-term engines against public HKO archival Jie times.

This is a general engineering qualification benchmark, not metaphysical
prediction evidence. It compares:
- the current Project solar_term_time implementation; and
- the already pinned lunar-python 1.4.8 JieQi table

against HKO published minute-resolution times over a preregistered continuous
year range. No Bazi case outcomes are used.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import math
from pathlib import Path
import re
import statistics
import sys
from typing import Any, Optional, Sequence
from zoneinfo import ZoneInfo

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from engine.bazi.calendar import JIE, solar_term_time
from lunar_python import Solar

START_YEAR = 2013
END_YEAR = 2019
HKO_TOLERANCE_SECONDS = 60.0

_ENGLISH_JIE = {
    "Moderate cold": "小寒",
    "Spring commences": "立春",
    "Insects waken": "驚蟄",
    "Bright and clear": "清明",
    "Summer commences": "立夏",
    "Corn on ear": "芒種",
    "Moderate heat": "小暑",
    "Autumn commences": "立秋",
    "White dew": "白露",
    "Cold dew": "寒露",
    "Winter commences": "立冬",
    "Heavy snow": "大雪",
}
_LUNAR_KEYS = {"驚蟄": "惊蛰", "芒種": "芒种"}
_MONTHS = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12,
}


def parse_hko_jie(path: Path, year: int) -> dict[str, datetime]:
    raw = path.read_text(encoding="utf-8", errors="strict")
    zone = ZoneInfo("Asia/Taipei")
    result = {}
    for english, chinese in _ENGLISH_JIE.items():
        pattern = re.compile(
            r"<td[^>]*>\s*" + re.escape(english) + r"\s*</td>\s*"
            r"<td[^>]*>\s*(\d{1,2})\s*</td>\s*"
            r"<td[^>]*>\s*(?:&nbsp;)?\s*([A-Za-z]+)(?:\s*</td>)?\s*"
            r"<td[^>]*>\s*(\d{2}):(\d{2})\s*</td>",
            re.IGNORECASE | re.DOTALL,
        )
        match = pattern.search(raw)
        if match is None:
            raise ValueError(f"{path.name}: missing HKO Jie row for {english}")
        month_name = match.group(2)
        if month_name not in _MONTHS:
            raise ValueError(f"{path.name}: unknown month {month_name!r}")
        result[chinese] = datetime(
            year, _MONTHS[month_name], int(match.group(1)),
            int(match.group(3)), int(match.group(4)), tzinfo=zone,
        )
    return result


def lunar_python_jie(year: int, term: str) -> datetime:
    table = Solar.fromYmd(year, 7, 1).getLunar().getJieQiTable()
    key = _LUNAR_KEYS.get(term, term)
    if key not in table:
        raise ValueError(f"lunar-python JieQi table missing {term!r} for {year}")
    solar = table[key]
    value = datetime(
        solar.getYear(), solar.getMonth(), solar.getDay(),
        solar.getHour(), solar.getMinute(), solar.getSecond(),
        tzinfo=ZoneInfo("Asia/Taipei"),
    )
    if value.year != year:
        raise ValueError(
            f"lunar-python returned wrong year for {year} {term}: {value.isoformat()}"
        )
    return value


def _engine_summary(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    errors = [row[key] for row in rows]
    within = sum(value <= HKO_TOLERANCE_SECONDS for value in errors)
    return {
        "point_count": len(errors),
        "within_60_seconds": within,
        "within_60_rate": within / len(errors),
        "mean_abs_seconds": statistics.fmean(errors),
        "median_abs_seconds": statistics.median(errors),
        "p95_abs_seconds": sorted(errors)[math.ceil(len(errors) * 0.95) - 1],
        "max_abs_seconds": max(errors),
    }


def run_benchmark(input_dir: Path) -> dict[str, Any]:
    rows = []
    for year in range(START_YEAR, END_YEAR + 1):
        page = input_dir / ("Solar_Term_%d.htm" % year)
        if not page.is_file() or page.stat().st_size <= 0:
            raise ValueError(f"missing non-empty HKO page: {page}")
        hko = parse_hko_jie(page, year)
        if set(hko) != {name for name, *_ in JIE}:
            raise ValueError(f"{year}: HKO Jie census mismatch")
        for term, *_ in JIE:
            expected = hko[term]
            current = solar_term_time(year, term, "Asia/Taipei")
            library = lunar_python_jie(year, term)
            rows.append({
                "year": year,
                "term": term,
                "hko": expected.isoformat(),
                "current_project": current.isoformat(),
                "lunar_python_1_4_8": library.isoformat(),
                "current_abs_seconds": abs((current - expected).total_seconds()),
                "lunar_python_abs_seconds": abs((library - expected).total_seconds()),
            })

    expected_points = (END_YEAR - START_YEAR + 1) * len(JIE)
    if len(rows) != expected_points:
        raise ValueError(f"point census mismatch: {len(rows)} != {expected_points}")

    current = _engine_summary(rows, "current_abs_seconds")
    library = _engine_summary(rows, "lunar_python_abs_seconds")
    candidate_gate = {
        "candidate": "lunar-python==1.4.8 JieQi table",
        "requirements": {
            "all_points_within_hko_60_seconds": True,
            "candidate_max_not_worse_than_current": True,
            "candidate_mean_not_worse_than_current": True,
        },
        "pass": (
            library["within_60_seconds"] == expected_points
            and library["max_abs_seconds"] <= current["max_abs_seconds"]
            and library["mean_abs_seconds"] <= current["mean_abs_seconds"]
        ),
    }
    return {
        "schema_version": "1.0",
        "benchmark_type": "PUBLIC_HKO_GENERAL_SOLAR_TERM_QUALIFICATION",
        "evidence_scope": "engineering_calendar_accuracy",
        "years": {"start": START_YEAR, "end": END_YEAR, "continuous": True},
        "jie_per_year": len(JIE),
        "point_count": expected_points,
        "hko_published_precision_seconds": 60,
        "current_project": current,
        "lunar_python_1_4_8": library,
        "candidate_gate": candidate_gate,
        "rows": rows,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        report = run_benchmark(args.input_dir)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({
            "point_count": report["point_count"],
            "current_project": report["current_project"],
            "lunar_python_1_4_8": report["lunar_python_1_4_8"],
            "candidate_gate": report["candidate_gate"],
        }, ensure_ascii=False, sort_keys=True))
    except (OSError, ValueError) as exc:
        print(f"benchmark_bazi_solar_terms_hko: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
