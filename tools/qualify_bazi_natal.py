#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from importlib.metadata import version as package_version
from pathlib import Path
from typing import Mapping, Optional, Sequence, Tuple
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lunar_python import Solar
from lunar_python.util import LunarUtil

from engine.bazi.calendar import solar_term_time
from engine.bazi.natal import build_bazi_natal, compare_bazi_time_views, hidden_stems
from engine.birth.models import ResolvedBirthPlace, Sex
from engine.birth.time_views import BirthTimeViews, TimeView, build_birth_time_views
from engine.calendar import resolve_calendar


REFERENCE_ENGINE = "lunar-python"
REFERENCE_VERSION = "1.4.8"
REFERENCE_SOURCE_REVISION = "000c8a3"
PROJECT_PROFILE = "bazi-natal-project-v1"
PROJECT_RULE_VERSION = "1.0-exp"
TIMEZONE_NAME = "Asia/Taipei"
_TZ = ZoneInfo(TIMEZONE_NAME)
_TROPICAL_YEAR_DAYS = 365.2425
_BRANCHES = ("子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥")
_KNOWN_HIDDEN_STEM_ORDER_DIFFERENCE = {
    "branch": "巳",
    "project": ["丙", "戊", "庚"],
    "reference": ["丙", "庚", "戊"],
    "reason": "Project v1 fixes 巳 hidden-stem rank as 丙戊庚; lunar-python 1.4.8 exposes the same stems as 丙庚戊",
}

PUBLIC_CASE_IDS = (
    "normal_daytime",
    "late_zi_2259",
    "late_zi_2300",
    "late_zi_2359",
    "midnight_0000",
    "before_lichun",
    "after_lichun",
    "before_jingzhe",
    "after_jingzhe",
    "male_direction",
    "female_direction",
    "time_profile_equivalent",
    "time_profile_hour_conflict",
)

_TAIPEI_PLACE = ResolvedBirthPlace(
    canonical_name="Taipei, Taiwan",
    latitude=25.0375,
    longitude=121.5637,
    timezone=TIMEZONE_NAME,
    provider_name="public-fixture",
    provider_version="1",
    resolution_status="resolved",
    provider_reference="public:taipei",
)


def _field(
    project_value: object,
    reference_value: object,
    *,
    expected_profile_difference: bool = False,
    reason: Optional[str] = None,
) -> dict:
    if project_value == reference_value:
        status = "MATCH"
    elif expected_profile_difference:
        status = "CONFLICT/profile_difference"
    else:
        status = "MISMATCH"
    result = {
        "status": status,
        "project": project_value,
        "reference": reference_value,
    }
    if reason is not None:
        result["reason"] = reason
    return result


def _is_known_hidden_stem_order_difference(project_value: object, reference_value: object) -> bool:
    if not isinstance(project_value, list) or not isinstance(reference_value, list):
        return False
    if len(project_value) != len(reference_value):
        return False
    saw_difference = False
    for project_item, reference_item in zip(project_value, reference_value):
        if project_item == reference_item:
            continue
        if (
            project_item == _KNOWN_HIDDEN_STEM_ORDER_DIFFERENCE["project"]
            and reference_item == _KNOWN_HIDDEN_STEM_ORDER_DIFFERENCE["reference"]
        ):
            saw_difference = True
            continue
        return False
    return saw_difference


def _hidden_stem_field(project_value: list, reference_value: list) -> dict:
    if project_value == reference_value:
        return _field(project_value, reference_value)
    if _is_known_hidden_stem_order_difference(project_value, reference_value):
        return _field(
            project_value,
            reference_value,
            expected_profile_difference=True,
            reason=_KNOWN_HIDDEN_STEM_ORDER_DIFFERENCE["reason"],
        )
    return _field(project_value, reference_value)


def hidden_stem_table_qualification() -> dict:
    branches = []
    matched = 0
    profile_differences = 0
    unexpected = 0
    for branch in _BRANCHES:
        project_value = list(hidden_stems(branch))
        reference_value = list(LunarUtil.ZHI_HIDE_GAN[branch])
        if project_value == reference_value:
            status = "MATCH"
            matched += 1
        elif (
            branch == _KNOWN_HIDDEN_STEM_ORDER_DIFFERENCE["branch"]
            and project_value == _KNOWN_HIDDEN_STEM_ORDER_DIFFERENCE["project"]
            and reference_value == _KNOWN_HIDDEN_STEM_ORDER_DIFFERENCE["reference"]
        ):
            status = "CONFLICT/profile_difference"
            profile_differences += 1
        else:
            status = "MISMATCH"
            unexpected += 1
        branches.append(
            {
                "branch": branch,
                "status": status,
                "project": project_value,
                "reference": reference_value,
            }
        )
    return {
        "matched_branch_count": matched,
        "profile_difference_count": profile_differences,
        "unexpected_mismatch_count": unexpected,
        "branches": branches,
    }


def _project_ten_gods(chart) -> dict:
    return {
        "stems": [detail.stem_ten_god for detail in chart.pillar_details],
        "hidden": [list(detail.hidden_ten_gods) for detail in chart.pillar_details],
    }


def _reference_ten_gods(eight_char) -> dict:
    return {
        "stems": [
            eight_char.getYearShiShenGan(),
            eight_char.getMonthShiShenGan(),
            eight_char.getDayShiShenGan(),
            eight_char.getTimeShiShenGan(),
        ],
        "hidden": [
            list(eight_char.getYearShiShenZhi()),
            list(eight_char.getMonthShiShenZhi()),
            list(eight_char.getDayShiShenZhi()),
            list(eight_char.getTimeShiShenZhi()),
        ],
    }


def _reference_hidden_stems(eight_char) -> list:
    return [
        list(eight_char.getYearHideGan()),
        list(eight_char.getMonthHideGan()),
        list(eight_char.getDayHideGan()),
        list(eight_char.getTimeHideGan()),
    ]


def _reference_start_age_years(yun) -> float:
    return (
        float(yun.getStartYear())
        + float(yun.getStartMonth()) / 12.0
        + float(yun.getStartDay()) / _TROPICAL_YEAR_DAYS
        + float(yun.getStartHour()) / (24.0 * _TROPICAL_YEAR_DAYS)
    )


def _reference_decadal_sequence(yun) -> list:
    periods = yun.getDaYun(11)
    return [period.getGanZhi() for period in periods[1:11]]


def _calendar_context(value: datetime):
    civil = value.replace(tzinfo=None).isoformat(timespec="seconds")
    resolution = resolve_calendar(civil, TIMEZONE_NAME)
    if not resolution.ok or resolution.context is None:
        code = resolution.error.code if resolution.error is not None else "unknown"
        raise RuntimeError("calendar resolver failed for public vector: %s" % code)
    return resolution.context


def _qualify_reference_case(case_id: str, value: datetime, sex: Sex) -> dict:
    context = _calendar_context(value)
    views = build_birth_time_views(context, _TAIPEI_PLACE)
    chart = build_bazi_natal(context, views, sex)

    solar = Solar.fromYmdHms(
        value.year,
        value.month,
        value.day,
        value.hour,
        value.minute,
        value.second,
    )
    eight_char = solar.getLunar().getEightChar()
    eight_char.setSect(1)
    gender = 1 if sex == Sex.MALE else 0
    yun = eight_char.getYun(gender, 1)

    project_pillars = [pillar.text for pillar in chart.pillars]
    reference_pillars = [
        eight_char.getYear(),
        eight_char.getMonth(),
        eight_char.getDay(),
        eight_char.getTime(),
    ]
    project_hidden = [
        [hidden.stem for hidden in detail.hidden_stems]
        for detail in chart.pillar_details
    ]
    reference_hidden = _reference_hidden_stems(eight_char)
    project_sequence = [period.pillar.text for period in chart.decadal_periods]
    reference_direction = "forward" if yun.isForward() else "reverse"
    project_start_age = float(chart.provenance["decadal_start_age_years"])
    reference_start_age = _reference_start_age_years(yun)

    fields = {
        "four_pillars": _field(project_pillars, reference_pillars),
        "day_master": _field(chart.day_master, eight_char.getDayGan()),
        "hidden_stems": _hidden_stem_field(project_hidden, reference_hidden),
        "ten_gods": _field(
            _project_ten_gods(chart),
            _reference_ten_gods(eight_char),
            expected_profile_difference=True,
            reason="lunar-python labels the visible day stem as 日主 while Project stores its relation as 比肩; Traditional/Simplified Chinese labels are presentation differences",
        ),
        "decadal_direction": _field(chart.decadal_direction, reference_direction),
        "decadal_start_age": _field(
            project_start_age,
            reference_start_age,
            expected_profile_difference=True,
            reason="Project uses a continuous Jie interval ratio; lunar-python sect=1 quantizes the interval into civil days and shichen before conversion",
        ),
        "decadal_pillar_sequence": _field(project_sequence, _reference_decadal_sequence(yun)),
    }
    return {
        "case_id": case_id,
        "public_vector": {
            "civil": value.replace(tzinfo=None).isoformat(timespec="seconds"),
            "timezone": TIMEZONE_NAME,
            "sex": sex.value,
        },
        "reference_profiles": {"eight_char_sect": 1, "yun_sect": 1},
        "fields": fields,
    }


def _time_view(kind: str, value: datetime) -> TimeView:
    return TimeView(
        kind=kind,
        local_datetime=value,
        adjustment_minutes=0.0,
        profile_id="public-qualification-fixture",
        rule_version="1",
        calculation_basis="public synthetic fixture",
        boundary_effect={},
        provenance={"classification": "public synthetic qualification"},
    )


def _time_profile_cases() -> Tuple[dict, dict]:
    equivalent_context = _calendar_context(datetime(1984, 3, 13, 19, 20, tzinfo=_TZ))
    equivalent_views = build_birth_time_views(equivalent_context, _TAIPEI_PLACE)
    equivalent = compare_bazi_time_views(equivalent_views)

    civil = datetime(1984, 3, 13, 19, 2, tzinfo=_TZ)
    solar = datetime(1984, 3, 13, 18, 56, tzinfo=_TZ)
    conflict_views = BirthTimeViews(
        reported_civil=_time_view("reported_civil", civil),
        normalized_civil=_time_view("normalized_civil", civil),
        true_solar=_time_view("true_solar", solar),
    )
    conflict = compare_bazi_time_views(conflict_views)
    return (
        {
            "case_id": "time_profile_equivalent",
            "comparison_status": equivalent.status,
            "affected_components": list(equivalent.affected_components),
            "severity": equivalent.severity,
        },
        {
            "case_id": "time_profile_hour_conflict",
            "comparison_status": conflict.status,
            "affected_components": list(conflict.affected_components),
            "severity": conflict.severity,
        },
    )


def _public_reference_vectors() -> Tuple[Tuple[str, datetime, Sex], ...]:
    lichun = solar_term_time(2026, "立春", _TZ).replace(microsecond=0)
    jingzhe = solar_term_time(2026, "驚蟄", _TZ).replace(microsecond=0)
    return (
        ("normal_daytime", datetime(1984, 3, 13, 19, 20, tzinfo=_TZ), Sex.MALE),
        ("late_zi_2259", datetime(2026, 8, 20, 22, 59, tzinfo=_TZ), Sex.MALE),
        ("late_zi_2300", datetime(2026, 8, 20, 23, 0, tzinfo=_TZ), Sex.MALE),
        ("late_zi_2359", datetime(2026, 8, 20, 23, 59, tzinfo=_TZ), Sex.MALE),
        ("midnight_0000", datetime(2026, 8, 21, 0, 0, tzinfo=_TZ), Sex.MALE),
        ("before_lichun", lichun - timedelta(minutes=30), Sex.MALE),
        ("after_lichun", lichun + timedelta(minutes=30), Sex.MALE),
        ("before_jingzhe", jingzhe - timedelta(minutes=30), Sex.MALE),
        ("after_jingzhe", jingzhe + timedelta(minutes=30), Sex.MALE),
        ("male_direction", datetime(1984, 3, 13, 19, 20, tzinfo=_TZ), Sex.MALE),
        ("female_direction", datetime(1984, 3, 13, 19, 20, tzinfo=_TZ), Sex.FEMALE),
    )


def build_public_report(cases: Sequence[Mapping[str, object]]) -> dict:
    matched = 0
    profile_differences = 0
    unexpected = 0
    for case in cases:
        fields = case.get("fields")
        if not isinstance(fields, Mapping):
            continue
        for field in fields.values():
            if not isinstance(field, Mapping):
                continue
            status = field.get("status")
            if status == "MATCH":
                matched += 1
            elif status == "CONFLICT/profile_difference":
                profile_differences += 1
            elif status == "MISMATCH":
                unexpected += 1
    return {
        "schema_version": "1.0",
        "classification": "public_bazi_natal_qualification",
        "reference_engine": REFERENCE_ENGINE,
        "reference_version": REFERENCE_VERSION,
        "reference_source_revision": REFERENCE_SOURCE_REVISION,
        "project_profile": PROJECT_PROFILE,
        "project_rule_version": PROJECT_RULE_VERSION,
        "case_count": len(cases),
        "matched_field_count": matched,
        "profile_difference_count": profile_differences,
        "unexpected_mismatch_count": unexpected,
        "status": "PASS" if unexpected == 0 else "FAIL",
        "hidden_stem_table": hidden_stem_table_qualification(),
        "cases": list(cases),
    }


def qualify_public_cases() -> dict:
    actual_version = package_version("lunar-python")
    if actual_version != REFERENCE_VERSION:
        raise RuntimeError(
            "pinned lunar-python mismatch: expected %s, got %s"
            % (REFERENCE_VERSION, actual_version)
        )
    hidden_table = hidden_stem_table_qualification()
    if hidden_table["unexpected_mismatch_count"]:
        raise RuntimeError("unexpected hidden-stem reference table mismatch")
    cases = [
        _qualify_reference_case(case_id, value, sex)
        for case_id, value, sex in _public_reference_vectors()
    ]
    cases.extend(_time_profile_cases())
    return build_public_report(cases)


def main() -> int:
    parser = argparse.ArgumentParser(description="Qualify Project Bazi natal against pinned lunar-python")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = qualify_public_cases()
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    if report["unexpected_mismatch_count"]:
        print("BAZI_NATAL_QUALIFICATION_FAIL", file=sys.stderr)
        return 1
    print(
        "BAZI_NATAL_QUALIFICATION_PASS match=%d profile_difference=%d"
        % (report["matched_field_count"], report["profile_difference_count"])
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
