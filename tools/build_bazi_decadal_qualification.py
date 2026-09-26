#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a structural, fail-closed qualification packet for Bazi decadal data.

This packet audits the already-materialized Project natal output.  It does not
recalculate a Bazi chart, choose an interval convention, or promote maturity.
The endpoint and age semantics remain an explicit human decision until an
independent reference is bound to the same profile.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.bazi.natal import _SEXAGENARY_CYCLE

FIXTURE_PATH = ROOT / "qualification" / "bazi" / "decadal" / "synthetic-engine-view.v1.json"
REPORT_PATH = ROOT / "qualification" / "bazi" / "decadal" / "public-project-contract-v1.json"
BASELINE_SHA = "872c60b2e959ea48d25524b74686e488f576ec6f"
_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_PILLARS = frozenset(_SEXAGENARY_CYCLE)
ENGINE_SOURCE_BINDING = {
    "source_commit": BASELINE_SHA,
    "entrypoint": "engine.bazi.natal.build_bazi_natal",
    "serializer": "engine.natal.orchestration._serialize_bazi",
    "files": [
        {
            "path": "engine/bazi/natal.py",
            "git_blob_sha1": "2c0ec78efe8f1b0c83a1e19b2b037f08039e6495",
            "sha256": "5e9870a0be687545ff642a0d6806cef9f5216032d1c87be3935e135e843173e3",
        },
        {
            "path": "engine/bazi/natal_models.py",
            "git_blob_sha1": "7272400777f87a158610bc4372c2563225a13dd5",
            "sha256": "bd844a53e0b368c3cf05f8ab370cd99c7da8c637b4668d57723f9a5d8c05b633",
        },
        {
            "path": "engine/natal/orchestration.py",
            "git_blob_sha1": "06c746e5853c87a870294350e99ab6a397cc0a17",
            "sha256": "dc255b8d3778f1c503391d6bf4adc938af61f4282e726e4a219ff83d45113172",
        },
    ],
}
BIRTH_VECTOR = {
    "reported_datetime": "1984-03-13T19:20:00",
    "sex": "male",
    "timezone": "Asia/Taipei",
    "resolved_location": {
        "canonical_name": "Taipei, Taiwan",
        "latitude": 25.0375,
        "longitude": 121.5637,
        "provider_name": "public-fixture",
        "provider_version": "1",
        "resolution_status": "resolved",
        "provider_reference": "public:taipei",
    },
}
GENERATION_METHOD = {
    "entrypoint": "engine.bazi.natal.build_bazi_natal",
    "serializer": "engine.natal.orchestration._serialize_bazi",
    "reproduction_test": (
        "python -m unittest "
        "tests.test_bazi_decadal_qualification.BaziDecadalQualificationTests."
        "test_fixture_decadal_values_match_existing_project_engine_serializer -v"
    ),
}
HOSTED_VERIFICATION = {
    "candidate_commit": "270ee223f779f6621c0c74434799886f1df4af92",
    "environment": {
        "runner": "GitHub Actions ubuntu-latest",
        "python": "3.9.25",
    },
    "full_repository_regression": {
        "tests": 1292,
        "failures": 0,
        "status": "PASS",
    },
    "task_module_regression": {
        "module": "tests.test_bazi_decadal_qualification",
        "tests": 21,
        "status": "PASS",
        "included_in": "full_repository_regression",
    },
    "workflow_runs": [
        {
            "workflow": "Lin Tianji v1.5 Validation",
            "run_id": 36238276699,
            "job_id": 108393960224,
            "conclusion": "success",
        },
        {
            "workflow": "Lin Tianji v1.6 Validation",
            "run_id": 36238276717,
            "job_id": 108393960734,
            "conclusion": "success",
        },
        {
            "workflow": "Lin Tianji v1.7 Validation",
            "run_id": 36238276720,
            "job_id": 108393960350,
            "conclusion": "success",
        },
    ],
    "engineering_verification_status": "PASS",
    "qualification_status": "NEEDS_EVIDENCE",
}


def canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _is_finite_number(value: Any) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _parse_aware(
    value: Any,
    field: str,
    errors: list[str],
    timezone: Optional[ZoneInfo] = None,
) -> Optional[datetime]:
    if not isinstance(value, str):
        errors.append(f"{field} must be an ISO-8601 string")
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        errors.append(f"{field} is not a valid ISO-8601 datetime")
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        errors.append(f"{field} must include a UTC offset")
        return None
    if timezone is not None:
        try:
            converted_offset = parsed.astimezone(timezone).utcoffset()
        except OverflowError:
            errors.append(f"{field} timezone conversion is out of range")
            return None
        else:
            if parsed.utcoffset() != converted_offset:
                errors.append(f"{field} UTC offset does not match timezone")
    return parsed


def validate_fixture(payload: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, Mapping):
        return ["fixture must be an object"]
    if payload.get("schema_version") != "1.0":
        errors.append("schema_version must be 1.0")
    if payload.get("classification") != "synthetic_bazi_decadal_engine_view":
        errors.append("classification is not the synthetic Bazi decadal fixture")
    source_commit = payload.get("source_commit")
    if not isinstance(source_commit, str) or not _HEX40.fullmatch(source_commit):
        errors.append("source_commit must be a 40-character lowercase commit SHA")
    elif source_commit != BASELINE_SHA:
        errors.append(f"source_commit must equal baseline {BASELINE_SHA}")
    if payload.get("source_type") != "synthetic_engine_output":
        errors.append("source_type must be synthetic_engine_output")
    if payload.get("engine_source") != ENGINE_SOURCE_BINDING:
        errors.append("engine_source does not match the pinned baseline source files")
    if payload.get("generation") != GENERATION_METHOD:
        errors.append("generation metadata does not match the reproducible public vector")

    profile = payload.get("profile")
    if not isinstance(profile, Mapping):
        errors.append("profile must be an object")
        profile = {}
    for field, expected in (
        ("profile_id", "bazi-natal-project-v1"),
        ("rule_version", "1.0-exp"),
        ("decadal_rule", "three-days-one-year-v1"),
        ("age_basis", "continuous_years_from_jie_interval"),
        ("interval_semantics", "needs_confirmation"),
    ):
        if profile.get(field) != expected:
            errors.append(f"profile.{field} must be {expected}")

    timezone_name = payload.get("timezone")
    timezone = None
    if not isinstance(timezone_name, str) or not timezone_name:
        errors.append("timezone must be a non-empty string")
    else:
        try:
            timezone = ZoneInfo(timezone_name)
        except (ZoneInfoNotFoundError, ValueError):
            errors.append("timezone is unknown or unavailable")
    _parse_aware(payload.get("effective_datetime"), "effective_datetime", errors, timezone)
    if timezone_name != BIRTH_VECTOR["timezone"]:
        errors.append("timezone does not match the bound generation vector")
    if not isinstance(payload.get("birth_vector"), Mapping):
        errors.append("birth_vector must be an object")
    elif payload["birth_vector"] != BIRTH_VECTOR:
        errors.append("birth_vector does not match the bound generation vector")
    if payload.get("decadal_direction") not in ("forward", "reverse"):
        errors.append("decadal_direction must be forward or reverse")

    periods = payload.get("periods")
    if not isinstance(periods, list) or len(periods) < 2:
        errors.append("periods must contain at least two adjacent periods")
        return errors

    previous_end: Optional[datetime] = None
    previous_index: Optional[int] = None
    previous_age_end: Optional[float] = None
    for position, row in enumerate(periods):
        prefix = f"periods[{position}]"
        if not isinstance(row, Mapping):
            errors.append(f"{prefix} must be an object")
            continue
        index = row.get("index")
        if not isinstance(index, int) or isinstance(index, bool):
            errors.append(f"{prefix}.index must be an integer")
        elif index != position + 1:
            errors.append(f"{prefix}.index must start at 1 and be sequential")
        previous_index = index if isinstance(index, int) else previous_index
        pillar = row.get("pillar")
        if not isinstance(pillar, str) or pillar not in _PILLARS:
            errors.append(f"{prefix}.pillar is not a valid sexagenary pillar")
        start_age = row.get("start_age_years")
        end_age = row.get("end_age_years")
        start_age_is_finite = _is_finite_number(start_age)
        end_age_is_finite = _is_finite_number(end_age)
        if not start_age_is_finite:
            errors.append(f"{prefix}.start_age_years must be finite")
        if not end_age_is_finite:
            errors.append(f"{prefix}.end_age_years must be finite")
        if start_age_is_finite and end_age_is_finite:
            if start_age < 0:
                errors.append(f"{prefix}.start_age_years must be non-negative")
            if end_age <= start_age or not math.isclose(end_age - start_age, 10.0, abs_tol=1e-9):
                errors.append(f"{prefix} must span exactly ten age years")
            if previous_age_end is not None and not math.isclose(
                start_age, previous_age_end, abs_tol=1e-9
            ):
                errors.append(f"{prefix} age interval is not contiguous with the previous period")
            previous_age_end = end_age
        start = _parse_aware(
            row.get("start_datetime"), f"{prefix}.start_datetime", errors, timezone
        )
        end = _parse_aware(row.get("end_datetime"), f"{prefix}.end_datetime", errors, timezone)
        if start is not None and end is not None:
            if end <= start:
                errors.append(f"{prefix} end_datetime must be after start_datetime")
            if previous_end is not None and start != previous_end:
                errors.append(f"{prefix} is not contiguous with the previous period")
            previous_end = end

    return errors


def build_report(
    fixture: Mapping[str, Any],
    fixture_path: Path = FIXTURE_PATH,
    fixture_sha256: Optional[str] = None,
) -> dict[str, Any]:
    errors = validate_fixture(fixture)
    if errors:
        raise ValueError("invalid Bazi decadal fixture: " + "; ".join(errors))
    _verify_engine_source_binding(fixture["engine_source"])
    if fixture_sha256 is None:
        fixture_text = fixture_path.read_text(encoding="utf-8")
        fixture_sha256 = hashlib.sha256(fixture_text.encode("utf-8")).hexdigest()
    if not _HEX64.fullmatch(fixture_sha256):
        raise ValueError("fixture_sha256 must be a 64-character lowercase SHA256")
    periods = fixture["periods"]
    return {
        "schema_version": "1.0",
        "classification": "bazi_decadal_qualification_packet",
        "source_commit": BASELINE_SHA,
        "source_type": "synthetic_engine_output",
        "engine_source": fixture["engine_source"],
        "generation": fixture["generation"],
        "birth_vector": fixture["birth_vector"],
        "verification_contract": {
            "source_reproduction_command": GENERATION_METHOD["reproduction_test"],
            "packet_check_command": "python tools/build_bazi_decadal_qualification.py --check",
            "focused_test_command": "python -m unittest tests.test_bazi_decadal_qualification -v",
            "required_python": "3.9",
            "verification_candidate_commit": HOSTED_VERIFICATION["candidate_commit"],
            "execution_count": HOSTED_VERIFICATION["full_repository_regression"]["tests"],
            "failure_count": HOSTED_VERIFICATION["full_repository_regression"]["failures"],
            "execution_status": "PASS: exact-candidate hosted regression; engineering verification only",
        },
        "hosted_verification": HOSTED_VERIFICATION,
        "fixture": {
            "path": _display_path(fixture_path),
            "sha256": fixture_sha256,
        },
        "project_profile": dict(fixture["profile"]),
        "coverage": {
            "period_count": len(periods),
            "adjacent_boundary_count": len(periods) - 1,
            "direction": fixture["decadal_direction"],
            "effective_datetime": fixture["effective_datetime"],
            "timezone": fixture["timezone"],
        },
        "boundary_semantics": {
            "status": "needs_confirmation",
            "interval_convention": None,
            "reason": "The current engine stores adjacent endpoints, but the public contract has not yet chosen inclusive versus half-open semantics.",
        },
        "independent_reference": {
            "status": "not_available",
            "reason": "No independent reference packet is bound to the same Project age and endpoint profile.",
        },
        "known_limitations": [
            "Synthetic engine output proves structural continuity only.",
            "Age basis and endpoint semantics require explicit human confirmation.",
            "No ten-god or element overlay is qualified for this packet.",
            "No prospective evidence or event claim is included.",
        ],
        "result": "NEEDS_EVIDENCE",
        "maturity_promotion": False,
        "promotion_decision": "not_decided",
    }


def _verify_engine_source_binding(engine_source: Mapping[str, Any]) -> None:
    if engine_source != ENGINE_SOURCE_BINDING:
        raise ValueError("engine source binding does not match the pinned baseline")
    try:
        source_type = subprocess.check_output(
            ["git", "cat-file", "-t", BASELINE_SHA], cwd=str(ROOT), stderr=subprocess.PIPE
        ).decode("ascii").strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError("baseline source commit is unavailable in this checkout") from exc
    if source_type != "commit":
        raise ValueError("baseline source reference is not a commit")
    for row in ENGINE_SOURCE_BINDING["files"]:
        try:
            blob_id = subprocess.check_output(
                ["git", "rev-parse", "%s:%s" % (BASELINE_SHA, row["path"])],
                cwd=str(ROOT),
                stderr=subprocess.PIPE,
            ).decode("ascii").strip()
            blob_bytes = subprocess.check_output(
                ["git", "cat-file", "blob", blob_id], cwd=str(ROOT), stderr=subprocess.PIPE
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            raise ValueError("baseline engine source is unavailable: %s" % row["path"]) from exc
        if blob_id != row["git_blob_sha1"] or hashlib.sha256(blob_bytes).hexdigest() != row["sha256"]:
            raise ValueError("baseline engine source hash mismatch: %s" % row["path"])


def write_report(fixture_path: Path = FIXTURE_PATH, report_path: Path = REPORT_PATH) -> dict[str, Any]:
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    report = build_report(fixture, fixture_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(canonical_json(report), encoding="utf-8")
    return report


def check_report(fixture_path: Path = FIXTURE_PATH, report_path: Path = REPORT_PATH) -> bool:
    try:
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        expected = canonical_json(build_report(fixture, fixture_path))
        actual = report_path.read_text(encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Bazi decadal qualification evidence is unavailable: {exc}", file=sys.stderr)
        return False
    if actual != expected:
        print("Bazi decadal qualification evidence is out of date", file=sys.stderr)
        return False
    print("Bazi decadal qualification evidence is up to date")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, default=FIXTURE_PATH)
    parser.add_argument("--report", type=Path, default=REPORT_PATH)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        raise SystemExit(0 if check_report(args.fixture, args.report) else 1)
    report = write_report(args.fixture, args.report)
    print(f"Built Bazi decadal qualification: {args.report} ({report['result']})")


if __name__ == "__main__":
    main()
