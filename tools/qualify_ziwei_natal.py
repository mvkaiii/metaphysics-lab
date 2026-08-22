#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, time
from pathlib import Path
from typing import Dict, Iterable, Tuple
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.birth.calendar_adapter import resolve_birth_calendar
from engine.birth.models import (
    BirthDateInput,
    BirthInput,
    BirthPlaceInput,
    BirthTimeInput,
    ResolvedBirthPlace,
    Sex,
)
from engine.birth.time_views import build_birth_time_views
from engine.calendar.precision import TimePrecision
from engine.calendar.sexagenary import lunar_year_stem
from engine.ziwei.brightness_profiles import brightness_for
from engine.ziwei.common import ZHI
from engine.ziwei.natal import build_ziwei_natal
from engine.ziwei.natal_decadal import (
    build_ziwei_decadal_periods,
    resolve_decadal_direction,
    resolve_life_body_master,
)
from engine.ziwei.natal_palaces import (
    resolve_five_element_bureau,
    resolve_ming_body_branches,
    resolve_palace_stems,
)
from engine.ziwei.natal_stars import (
    place_chang_qu,
    place_fire_bell,
    place_kui_yue,
    place_left_right_assistants,
    place_lucun_yang_tuo,
    place_major_stars,
    place_tianma,
)
from engine.ziwei.natal_time import ZiweiBirthBasis
from engine.ziwei.star_catalog import MAJOR_STARS
from engine.ziwei.transformation_profiles import PROFILE


REFERENCE_REVISION = "814b77e6371e1050cac31bbf674db3c3138fcfde"
QUALIFICATION_DIR = ROOT / "qualification" / "ziwei" / "natal"
CONTRACT_PATH = QUALIFICATION_DIR / "public-iztro-814b77e6.json"
PALACE_PATH = QUALIFICATION_DIR / "public-iztro-palace-vectors.json"
MAJOR_PATH = QUALIFICATION_DIR / "public-iztro-major-star-vectors.json"
AUX_PATH = QUALIFICATION_DIR / "public-iztro-aux-star-vectors.json"
BRIGHTNESS_PATH = QUALIFICATION_DIR / "public-iztro-brightness-vectors.json"
DECADAL_PATH = QUALIFICATION_DIR / "public-iztro-decadal-vectors.json"

_BUREAU_VALUES = ("水二局", "木三局", "金四局", "土五局", "火六局")
_BRANCH_HOURS = {
    "子": 0, "丑": 2, "寅": 4, "卯": 6, "辰": 8, "巳": 10,
    "午": 12, "未": 14, "申": 16, "酉": 18, "戌": 20, "亥": 22,
}
_TZ = ZoneInfo("Asia/Taipei")
_PUBLIC_PLACE = ResolvedBirthPlace(
    canonical_name="Taipei City, Taiwan",
    latitude=25.0375,
    longitude=121.5637,
    timezone="Asia/Taipei",
    provider_name="public-fixture",
    provider_version="1",
    resolution_status="resolved",
    provider_reference="public:taipei",
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _record(group: dict, matched: bool, case_id: str) -> None:
    group["checks"] += 1
    if not matched:
        group["mismatches"] += 1
        group["mismatch_ids"].append(case_id)


def _component_qualification() -> Tuple[dict, int, int]:
    groups = {
        "palaces": {"checks": 0, "mismatches": 0, "mismatch_ids": []},
        "major_stars": {"checks": 0, "mismatches": 0, "mismatch_ids": []},
        "auxiliary_stars": {"checks": 0, "mismatches": 0, "mismatch_ids": []},
        "brightness": {"checks": 0, "mismatches": 0, "mismatch_ids": []},
        "masters_decadal": {"checks": 0, "mismatches": 0, "mismatch_ids": []},
    }

    palace = _load(PALACE_PATH)
    for row in palace["month_hour_matrix"]:
        for hour_branch, expected_ming, expected_body in zip(
            row["hour_branches"], row["ming_branches"], row["body_branches"]
        ):
            actual = resolve_ming_body_branches(row["lunar_month"], hour_branch)
            _record(
                groups["palaces"],
                actual == (expected_ming, expected_body),
                "ming_body:%d:%s" % (row["lunar_month"], hour_branch),
            )

    for row in palace["palace_stem_matrix"]:
        records = resolve_palace_stems(row["birth_year_stem"], "寅")
        by_branch = {record.branch: record.heavenly_stem for record in records}
        for branch, expected in zip(row["branches"], row["heavenly_stems"]):
            _record(
                groups["palaces"],
                by_branch[branch] == expected,
                "palace_stem:%s:%s" % (row["birth_year_stem"], branch),
            )

    bureau_legend = palace["bureau_legend"]
    for row in palace["bureau_matrix"]:
        for branch, stem, code in zip(row["branches"], row["heavenly_stems"], row["bureau_codes"]):
            actual = resolve_five_element_bureau(stem, branch)
            expected = bureau_legend[code]
            _record(
                groups["palaces"],
                actual == expected,
                "bureau:%s:%s" % (stem, branch),
            )

    major = _load(MAJOR_PATH)
    for row in major["matrices"]:
        for lunar_day, encoded in enumerate(row["placements"], start=1):
            actual = "".join(branch for _, branch in place_major_stars(lunar_day, row["bureau"]))
            _record(
                groups["major_stars"],
                actual == encoded,
                "major:%s:%d" % (row["bureau"], lunar_day),
            )

    aux = _load(AUX_PATH)
    for row in aux["left_right"]:
        actual = place_left_right_assistants(row["month"])
        _record(
            groups["auxiliary_stars"],
            actual == {"左輔": row["left"], "右弼": row["right"]},
            "left_right:%d" % row["month"],
        )
    for row in aux["chang_qu"]:
        actual = place_chang_qu(row["hour"])
        _record(
            groups["auxiliary_stars"],
            actual == {"文昌": row["chang"], "文曲": row["qu"]},
            "chang_qu:%s" % row["hour"],
        )
    for row in aux["kui_yue"]:
        actual = place_kui_yue(row["stem"])
        _record(
            groups["auxiliary_stars"],
            actual == {"天魁": row["kui"], "天鉞": row["yue"]},
            "kui_yue:%s" % row["stem"],
        )
    for row in aux["lu_yang_tuo"]:
        actual = place_lucun_yang_tuo(row["stem"])
        _record(
            groups["auxiliary_stars"],
            actual == {"祿存": row["lu"], "擎羊": row["yang"], "陀羅": row["tuo"]},
            "lu_yang_tuo:%s" % row["stem"],
        )
    for row in aux["tianma"]:
        actual = place_tianma(row["branch"])
        _record(
            groups["auxiliary_stars"],
            actual == {"天馬": row["ma"]},
            "tianma:%s" % row["branch"],
        )
    hour_order = tuple(aux["hour_branch_order"])
    for row in aux["fire_bell"]:
        for hour_branch, expected_fire, expected_bell in zip(hour_order, row["fire"], row["bell"]):
            actual = place_fire_bell(row["year_branch"], hour_branch)
            _record(
                groups["auxiliary_stars"],
                actual == {"火星": expected_fire, "鈴星": expected_bell},
                "fire_bell:%s:%s" % (row["year_branch"], hour_branch),
            )

    brightness = _load(BRIGHTNESS_PATH)
    branch_order = tuple(brightness["branch_order"])
    for row in brightness["vectors"]:
        for branch, expected in zip(branch_order, row["brightness"]):
            _record(
                groups["brightness"],
                brightness_for(row["star"], branch) == expected,
                "brightness:%s:%s" % (row["star"], branch),
            )
    for star in brightness["undefined_optional_stars"]:
        for branch in branch_order:
            _record(
                groups["brightness"],
                brightness_for(star, branch) is None,
                "brightness_optional:%s:%s" % (star, branch),
            )

    decadal = _load(DECADAL_PATH)
    for ming in decadal["masters"]:
        for birth in decadal["masters"]:
            actual = resolve_life_body_master(ming["branch"], birth["branch"])
            expected = (ming["life_master"], birth["body_master"])
            _record(
                groups["masters_decadal"],
                actual == expected,
                "masters:%s:%s" % (ming["branch"], birth["branch"]),
            )
    for row in decadal["directions"]:
        for sex, key in ((Sex.MALE, "male"), (Sex.FEMALE, "female")):
            _record(
                groups["masters_decadal"],
                resolve_decadal_direction(row["stem"], sex) == row[key],
                "direction:%s:%s" % (row["stem"], key),
            )
    sample_palaces = resolve_palace_stems("甲", "寅")
    for row in decadal["bureau_age_start"]:
        for direction in ("forward", "reverse"):
            periods = build_ziwei_decadal_periods(sample_palaces, row["bureau"], direction)
            matched = (
                len(periods) == 12
                and periods[0].age_start == row["age_start"]
                and periods[0].direction == direction
                and periods[-1].age_start == row["age_start"] + 110
            )
            _record(
                groups["masters_decadal"],
                matched,
                "decadal:%s:%s" % (row["bureau"], direction),
            )

    for value in groups.values():
        value["status"] = "PASS" if value["mismatches"] == 0 else "FAIL"
    total_checks = sum(value["checks"] for value in groups.values())
    total_mismatches = sum(value["mismatches"] for value in groups.values())
    return groups, total_checks, total_mismatches


def _basis(lunar_year: int, lunar_month: int, hour_branch: str, *, lunar_day: int = 11) -> ZiweiBirthBasis:
    hour = _BRANCH_HOURS[hour_branch]
    value = datetime(lunar_year, 6, 1, hour, 30, tzinfo=_TZ)
    return ZiweiBirthBasis(
        reported_datetime=value,
        normalized_datetime=value,
        true_solar_datetime=value,
        effective_datetime=value,
        effective_hour_branch=hour_branch,
        lunar_year=lunar_year,
        lunar_month=lunar_month,
        lunar_day=lunar_day,
        is_leap_month=False,
        validation={"calendar_status": "validated", "qualification_status": "qualified_candidate"},
        provenance={"classification": "Project 原生盤面", "effective_time_basis": "true_solar", "timezone": "Asia/Taipei"},
    )


def _find_input_for_bureau(lunar_year: int, target_bureau: str) -> Tuple[int, str]:
    stem = lunar_year_stem(lunar_year)
    for month in range(1, 13):
        for branch in ZHI:
            ming, _ = resolve_ming_body_branches(month, branch)
            palaces = resolve_palace_stems(stem, ming)
            ming_record = next(record for record in palaces if record.name == "命宮")
            bureau = resolve_five_element_bureau(ming_record.heavenly_stem, ming_record.branch)
            if bureau == target_bureau:
                return month, branch
    raise RuntimeError("no synthetic input found for bureau %s/%s" % (stem, target_bureau))


def _integration_qualification() -> Tuple[int, int, Tuple[str, ...]]:
    failures = []
    required_stars = {star for stars in PROFILE.values() for star in stars}
    count = 0
    for lunar_year in range(1984, 1994):
        stem = lunar_year_stem(lunar_year)
        for sex in (Sex.MALE, Sex.FEMALE):
            expected_direction = resolve_decadal_direction(stem, sex)
            for target_bureau in _BUREAU_VALUES:
                month, hour_branch = _find_input_for_bureau(lunar_year, target_bureau)
                case_id = "%s:%s:%s" % (stem, sex.value, target_bureau)
                count += 1
                try:
                    chart = build_ziwei_natal(_basis(lunar_year, month, hour_branch), sex)
                    star_names = {record.star for record in chart.stars}
                    major_names = tuple(record.star for record in chart.stars if record.star in MAJOR_STARS)
                    matched = (
                        chart.five_element_bureau == target_bureau
                        and len(chart.palaces) == 12
                        and len(chart.stars) == 26
                        and major_names == MAJOR_STARS
                        and required_stars.issubset(star_names)
                        and len(chart.decadal_periods) == 12
                        and chart.decadal_periods[0].direction == expected_direction
                        and len(chart.birth_transformations.transformations) == 4
                        and len(chart.natal_flying_graph.edges) == 48
                        and chart.classification == "Project 原生盤面"
                        and chart.maturity == "experimental"
                    )
                except Exception as exc:  # qualification must count, not hide, runtime failures
                    matched = False
                    case_id = "%s:%s" % (case_id, exc.__class__.__name__)
                if not matched:
                    failures.append(case_id)
    return count, len(failures), tuple(failures)


def _birth_input(hour: int, minute: int) -> BirthInput:
    return BirthInput(
        sex=Sex.MALE,
        birth_date=BirthDateInput(date(1984, 3, 13), TimePrecision.DAY),
        birth_time=BirthTimeInput(
            time(hour, minute),
            None,
            TimePrecision.HOUR,
            "%02d:%02d" % (hour, minute),
        ),
        birth_place=BirthPlaceInput("台北市"),
    )


def _public_place(longitude: float) -> ResolvedBirthPlace:
    return ResolvedBirthPlace(
        canonical_name="Public synthetic place",
        latitude=25.0,
        longitude=longitude,
        timezone="Asia/Taipei",
        provider_name="public-fixture",
        provider_version="1",
        resolution_status="resolved",
        provider_reference="public:synthetic",
    )


def _boundary_qualification() -> Tuple[int, int, Tuple[str, ...]]:
    results = []

    calendar = resolve_birth_calendar(_birth_input(19, 20), _PUBLIC_PLACE).context
    views = build_birth_time_views(calendar, _PUBLIC_PLACE)
    results.append((
        "true_solar_taipei_1984",
        abs(views.true_solar.adjustment_minutes - (-3.5750772239)) < 0.000001
        and views.true_solar.local_datetime.strftime("%Y-%m-%d %H:%M:%S") == "1984-03-13 19:16:25"
        and not views.true_solar.boundary_effect["hour_branch_changed"],
    ))

    synthetic = _public_place(117.0)
    calendar = resolve_birth_calendar(_birth_input(19, 10), synthetic).context
    views = build_birth_time_views(calendar, synthetic)
    results.append((
        "true_solar_cross_hour",
        views.true_solar.boundary_effect["from_hour_branch"] == "戌"
        and views.true_solar.boundary_effect["to_hour_branch"] == "酉"
        and views.true_solar.boundary_effect["hour_branch_changed"],
    ))

    def boundary_basis(day: int, hour: int, branch: str) -> ZiweiBirthBasis:
        value = datetime(1984, 8, 1, hour, 30, tzinfo=_TZ)
        return ZiweiBirthBasis(
            reported_datetime=value,
            normalized_datetime=value,
            true_solar_datetime=value,
            effective_datetime=value,
            effective_hour_branch=branch,
            lunar_year=1984,
            lunar_month=6,
            lunar_day=day,
            is_leap_month=True,
            validation={"calendar_status": "validated", "qualification_status": "qualified_candidate"},
            provenance={"classification": "Project 原生盤面", "effective_time_basis": "true_solar", "timezone": "Asia/Taipei"},
        )

    day15 = build_ziwei_natal(boundary_basis(15, 12, "午"), Sex.MALE)
    ming15 = next(record for record in day15.palaces if record.name == "命宮")
    results.append((
        "leap_month_day15",
        ming15.branch == "丑" and day15.provenance["structural_lunar_month"] == 6,
    ))

    day16 = build_ziwei_natal(boundary_basis(16, 12, "午"), Sex.MALE)
    ming16 = next(record for record in day16.palaces if record.name == "命宮")
    results.append((
        "leap_month_day16",
        ming16.branch == "寅" and day16.provenance["structural_lunar_month"] == 7,
    ))

    late = build_ziwei_natal(boundary_basis(16, 23, "子"), Sex.MALE)
    ming_late = next(record for record in late.palaces if record.name == "命宮")
    expected_major = dict(place_major_stars(17, late.five_element_bureau))
    actual_major = {record.star: record.branch for record in late.stars if record.star in MAJOR_STARS}
    results.append((
        "late_zi_forward",
        ming_late.branch == "未"
        and late.provenance["structural_lunar_month"] == 6
        and late.provenance["major_star_lunar_day"] == 17
        and actual_major == expected_major,
    ))

    failures = tuple(case_id for case_id, passed in results if not passed)
    return len(results), len(failures), failures


def qualify_public() -> dict:
    contract = _load(CONTRACT_PATH)
    groups, component_checks, component_mismatches = _component_qualification()
    integration_count, integration_failures, integration_failure_ids = _integration_qualification()
    boundary_count, boundary_failures, boundary_failure_ids = _boundary_qualification()

    expected_component = sum(row["expected_checks"] for row in contract["component_fixtures"])
    expected_integration = contract["integration_matrix"]["expected_chart_count"]
    expected_boundary = len(contract["boundary_matrix"])
    count_contract_ok = (
        component_checks == expected_component
        and integration_count == expected_integration
        and boundary_count == expected_boundary
    )

    status = "PASS" if (
        count_contract_ok
        and component_mismatches == 0
        and integration_failures == 0
        and boundary_failures == 0
    ) else "FAIL"

    return {
        "schema_version": "1.0",
        "status": status,
        "oracle_revision": REFERENCE_REVISION,
        "component_check_count": component_checks,
        "component_mismatch_count": component_mismatches,
        "component_groups": groups,
        "integration_chart_count": integration_count,
        "integration_failure_count": integration_failures,
        "integration_failure_ids": integration_failure_ids,
        "boundary_case_count": boundary_count,
        "boundary_failure_count": boundary_failures,
        "boundary_failure_ids": boundary_failure_ids,
        "count_contract_ok": count_contract_ok,
        "field_authorities": {
            "true_solar_adjustment": "project_formula_frozen",
            "lunar_birth": "calendar_resolver_validated",
            "ming_body_palaces": "iztro@" + REFERENCE_REVISION,
            "palace_stems": "iztro@" + REFERENCE_REVISION,
            "five_element_bureau": "iztro@" + REFERENCE_REVISION,
            "major_stars": "iztro@" + REFERENCE_REVISION,
            "selected_auxiliary_stars": "iztro@" + REFERENCE_REVISION,
            "brightness": "iztro@" + REFERENCE_REVISION,
            "life_body_master": "iztro@" + REFERENCE_REVISION,
            "decadal_cycles": "iztro@" + REFERENCE_REVISION,
            "birth_transformations": "phase2a_public_qualified",
            "natal_48_flying": "phase2a_public_qualified",
            "integration_matrix": "project_cross_component_invariant",
            "private_astralium": "PENDING",
        },
        "privacy_safe": True,
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Qualify Project-native Ziwei natal components")
    parser.add_argument("--compact", action="store_true", help="emit compact JSON")
    args = parser.parse_args(list(argv) if argv is not None else None)
    result = qualify_public()
    if args.compact:
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
