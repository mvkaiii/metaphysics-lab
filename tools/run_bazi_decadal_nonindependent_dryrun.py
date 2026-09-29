"""Run a Bazi decadal Task 3 non-independent diagnostic dry-run.

This runner is deliberately *not* independent evidence. It executes inside the
production repository context, uses production code for the actual side, and
uses the sealed HKO inputs plus the approved written specification for a
diagnostic reference side.

It must never emit qualification PASS or maturity promotion.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Mapping, Optional, Sequence
from zoneinfo import ZoneInfo

from engine.bazi.calendar import JIE, bazi_pillars, solar_term_time
from engine.bazi.natal import build_decadal_periods, decadal_direction
from engine.bazi.natal_models import Pillar
from engine.birth.models import Sex


SPEC_SHA256 = "0757d1275e55b84e2424d6131e9dbdc73e029e1b619f900147be928cc7e5e01d"
SEAL_SHA256 = "db32a95bc41a54531907e7e059655c094b1b1234a533770a88f2e3a52712874e"
CASE_BUNDLE_SHA256 = "ab7ebd72671c3020d67444f720c6f3645111005348efd56efe91ffd2ee699d3f"
HKO_2015_SHA256 = "60a45ab889ef436936571a04a49387c6f9ce8d43243fb21c64e3fcb0331c8320"
HKO_2016_SHA256 = "84beb01553646b807a7c15d6efebdd7550af1ac6d7f06e07bfdd124dab9e443b"
START_AGE_TOLERANCE = 0.0002314814814814815
DATETIME_TOLERANCE_SECONDS = 7304.85
TROPICAL_YEAR_DAYS = 365.2425

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
_MONTHS = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12,
}


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
        day = int(match.group(1))
        month_name = match.group(2)
        if month_name not in _MONTHS:
            raise ValueError(f"{path.name}: unknown month {month_name!r}")
        result[chinese] = datetime(
            year,
            _MONTHS[month_name],
            day,
            int(match.group(3)),
            int(match.group(4)),
            tzinfo=zone,
        )
    return result


def direction_from_sealed_coverage_tags(tags: list[str]) -> str:
    hits = [
        value for value in tags
        if value in {
            "forward_direction_expected_from_contract",
            "reverse_direction_expected_from_contract",
        }
    ]
    if len(hits) != 1:
        raise ValueError(f"expected exactly one sealed direction tag, got {hits!r}")
    return "forward" if hits[0].startswith("forward_") else "reverse"


def hko_boundary(
    birth: datetime,
    direction: str,
    boundaries: list[tuple[str, datetime]],
) -> tuple[str, datetime]:
    if direction == "forward":
        candidates = [(name, value) for name, value in boundaries if value >= birth]
        if not candidates:
            raise ValueError("no forward HKO Jie boundary available")
        return min(candidates, key=lambda item: item[1])
    candidates = [(name, value) for name, value in boundaries if value <= birth]
    if not candidates:
        raise ValueError("no reverse HKO Jie boundary available")
    return max(candidates, key=lambda item: item[1])


def production_boundary(birth: datetime, direction: str) -> tuple[str, datetime]:
    candidates = []
    for year in (birth.year - 1, birth.year, birth.year + 1):
        for name, *_ in JIE:
            candidates.append((name, solar_term_time(year, name, birth.tzinfo)))
    if direction == "forward":
        choices = [(name, value) for name, value in candidates if value > birth]
        return min(choices, key=lambda item: item[1])
    choices = [(name, value) for name, value in candidates if value < birth]
    return max(choices, key=lambda item: item[1])


def compare_number(expected: float, actual: float, tolerance: float) -> dict[str, Any]:
    difference = abs(float(actual) - float(expected))
    return {
        "status": "MATCH" if difference <= tolerance else "MISMATCH",
        "expected": expected,
        "actual": actual,
        "difference": difference,
        "tolerance": tolerance,
    }


def compare_datetime(expected: datetime, actual: datetime, tolerance: float) -> dict[str, Any]:
    difference = abs((actual - expected).total_seconds())
    return {
        "status": "MATCH" if difference <= tolerance else "MISMATCH",
        "expected": expected.isoformat(),
        "actual": actual.isoformat(),
        "difference_seconds": difference,
        "tolerance_seconds": tolerance,
    }


def run_dryrun(
    spec_path: Path,
    seal_path: Path,
    case_inputs_path: Path,
    hko_2015_path: Path,
    hko_2016_path: Path,
) -> dict[str, Any]:
    if file_sha256(spec_path) != SPEC_SHA256:
        raise ValueError("approved specification digest mismatch")
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    if seal.get("seal_sha256") != SEAL_SHA256:
        raise ValueError("pre-oracle seal binding mismatch")
    if file_sha256(hko_2015_path) != HKO_2015_SHA256:
        raise ValueError("HKO 2015 raw-byte digest mismatch")
    if file_sha256(hko_2016_path) != HKO_2016_SHA256:
        raise ValueError("HKO 2016 raw-byte digest mismatch")

    cases = json.loads(case_inputs_path.read_text(encoding="utf-8"))
    if cases.get("bundle_sha256") != CASE_BUNDLE_SHA256:
        raise ValueError("sealed case-input bundle binding mismatch")
    if cases.get("expected_values_present") is not False:
        raise ValueError("case-input bundle unexpectedly contains expected values")
    if len(cases.get("cases", [])) != 12:
        raise ValueError("expected exactly 12 sealed cases")

    hko_map = {}
    hko_map.update({(2015, name): value for name, value in parse_hko_jie(hko_2015_path, 2015).items()})
    hko_map.update({(2016, name): value for name, value in parse_hko_jie(hko_2016_path, 2016).items()})
    boundaries = sorted(
        [(name, value) for (_, name), value in hko_map.items()],
        key=lambda item: item[1],
    )

    strict_findings = [
        {
            "code": "YEAR_STEM_DERIVATION_NOT_SELF_CONTAINED",
            "severity": "BLOCKING_FOR_INDEPENDENT_ORACLE",
            "detail": (
                "The approved spec defines direction from natal-year stem polarity, "
                "but the sealed case inputs provide only birth_datetime/sex/timezone and "
                "the spec does not define how to derive the natal-year stem from those inputs."
            ),
        },
        {
            "code": "MONTH_PILLAR_DERIVATION_NOT_SELF_CONTAINED",
            "severity": "BLOCKING_FOR_INDEPENDENT_ORACLE",
            "detail": (
                "The approved spec defines the first Da Yun pillar relative to the natal "
                "month pillar, but neither the sealed inputs nor the approved spec define "
                "how to derive the natal month pillar."
            ),
        },
        {
            "code": "DIRECTION_EXPECTATION_LEAKED_IN_COVERAGE_TAGS",
            "severity": "INDEPENDENCE_WEAKENING",
            "detail": (
                "Every sealed case contains a coverage tag that directly states the expected "
                "forward/reverse direction. The diagnostic dry-run may use it, but the field "
                "cannot count as an independently derived oracle result."
            ),
        },
    ]

    counts = {"MATCH": 0, "MISMATCH": 0, "MISSING_REFERENCE": 0}
    per_case = []
    used_term_pairs = {}

    for case in cases["cases"]:
        birth = datetime.fromisoformat(case["input"]["birth_datetime"])
        sex = Sex(case["input"]["sex"])
        diagnostic_direction = direction_from_sealed_coverage_tags(case["coverage_tags"])

        pillars = bazi_pillars(birth)
        actual_direction = decadal_direction(pillars[0][0], sex)
        actual_periods = build_decadal_periods(
            Pillar(pillars[1][0], pillars[1][1]),
            birth,
            actual_direction,
            count=10,
        )
        actual_boundary_name, actual_boundary = production_boundary(birth, actual_direction)

        hko_name, hko_value = hko_boundary(birth, diagnostic_direction, boundaries)
        interval = (
            hko_value - birth if diagnostic_direction == "forward"
            else birth - hko_value
        )
        reference_start_age = interval.total_seconds() / (3.0 * 86400.0)
        reference_start_datetime = birth + timedelta(
            days=reference_start_age * TROPICAL_YEAR_DAYS
        )
        reference_second_end = birth + timedelta(
            days=(reference_start_age + 20.0) * TROPICAL_YEAR_DAYS
        )

        direction_row = {
            "path": "/decadal_direction",
            "status": "MATCH" if diagnostic_direction == actual_direction else "MISMATCH",
            "expected": diagnostic_direction,
            "actual": actual_direction,
            "evidence_note": "expected direction copied from sealed coverage metadata; not independently derived",
        }
        counts[direction_row["status"]] += 1

        pillar_row = {
            "path": "/periods/0/pillar",
            "status": "MISSING_REFERENCE",
            "expected": None,
            "actual": actual_periods[0].pillar.text,
            "reason": "approved spec/handoff does not define natal month-pillar derivation",
        }
        counts["MISSING_REFERENCE"] += 1

        age_row = {"path": "/periods/0/start_age_years"}
        age_row.update(compare_number(
            reference_start_age,
            actual_periods[0].start_age_years,
            START_AGE_TOLERANCE,
        ))
        counts[age_row["status"]] += 1

        start_row = {"path": "/periods/0/start_datetime"}
        start_row.update(compare_datetime(
            reference_start_datetime,
            actual_periods[0].start_datetime,
            DATETIME_TOLERANCE_SECONDS,
        ))
        counts[start_row["status"]] += 1

        endpoint_row = {"path": "/periods/1/end_datetime"}
        endpoint_row.update(compare_datetime(
            reference_second_end,
            actual_periods[1].end_datetime,
            DATETIME_TOLERANCE_SECONDS,
        ))
        counts[endpoint_row["status"]] += 1

        key = (hko_name, hko_value.isoformat(), actual_boundary_name, actual_boundary.isoformat())
        used_term_pairs[key] = {
            "hko_term": hko_name,
            "hko_datetime": hko_value.isoformat(),
            "production_selected_term": actual_boundary_name,
            "production_datetime": actual_boundary.isoformat(),
            "same_boundary_identity": hko_name == actual_boundary_name,
            "production_minus_hko_seconds": (
                (actual_boundary - hko_value).total_seconds()
                if hko_name == actual_boundary_name else None
            ),
        }

        per_case.append({
            "case_id": case["case_id"],
            "input_sha256": case["input_sha256"],
            "birth_datetime": birth.isoformat(),
            "production_year_pillar": pillars[0],
            "production_month_pillar": pillars[1],
            "diagnostic_direction_source": "sealed_coverage_tag",
            "reference_hko_boundary": {
                "term": hko_name,
                "datetime": hko_value.isoformat(),
            },
            "production_boundary": {
                "term": actual_boundary_name,
                "datetime": actual_boundary.isoformat(),
            },
            "rows": [direction_row, pillar_row, age_row, start_row, endpoint_row],
        })

    comparison_result = "MISMATCH" if counts["MISMATCH"] else (
        "PARTIAL" if counts["MISSING_REFERENCE"] else "MATCH"
    )
    return {
        "schema_version": "1.0",
        "run_type": "NON_INDEPENDENT_DRY_RUN",
        "evidence_class": "SAME_CONTEXT_DIAGNOSTIC_REPRODUCTION",
        "independent_qualification_usable": False,
        "qualification_decision": "HUMAN_REVIEW_REQUIRED",
        "maturity_promotion": False,
        "task3_independent_status": "NEEDS_EVIDENCE",
        "bindings": {
            "approved_spec_sha256": SPEC_SHA256,
            "preoracle_seal_sha256": SEAL_SHA256,
            "case_bundle_sha256": CASE_BUNDLE_SHA256,
            "hko_2015_sha256": HKO_2015_SHA256,
            "hko_2016_sha256": HKO_2016_SHA256,
        },
        "strict_cleanroom_executability": {
            "result": "FAIL_UNDER_SPECIFIED",
            "findings": strict_findings,
        },
        "diagnostic_mode": {
            "direction_source": "sealed coverage tags (tainted for independence)",
            "timing_reference": "sealed HKO raw bytes + approved D1/D2/D3 formulas",
            "first_pillar_reference": "MISSING_REFERENCE",
            "production_actual": "current repository production Bazi runtime",
        },
        "comparison_result": comparison_result,
        "counts": counts,
        "case_count": len(per_case),
        "field_count": sum(counts.values()),
        "used_boundary_pairs": sorted(
            used_term_pairs.values(),
            key=lambda item: (
                item["hko_datetime"],
                item["production_datetime"],
            ),
        ),
        "cases": per_case,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--seal", required=True, type=Path)
    parser.add_argument("--case-inputs", required=True, type=Path)
    parser.add_argument("--hko-2015", required=True, type=Path)
    parser.add_argument("--hko-2016", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        report = run_dryrun(
            args.spec,
            args.seal,
            args.case_inputs,
            args.hko_2015,
            args.hko_2016,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(json.dumps({
            "run_type": report["run_type"],
            "strict_cleanroom_executability": report["strict_cleanroom_executability"]["result"],
            "comparison_result": report["comparison_result"],
            "counts": report["counts"],
            "case_count": report["case_count"],
            "field_count": report["field_count"],
            "output": str(args.output),
        }, ensure_ascii=False, sort_keys=True))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"run_bazi_decadal_nonindependent_dryrun: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
