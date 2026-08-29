#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import build_release_package  # noqa: E402
from tools import run_v15_release_surface_validation  # noqa: E402

EVIDENCE_SCHEMA_VERSION = "v1.5.0-isolated-sandbox-evidence.v1"
SCRIPT_VERSION = "v1.5.0-isolated-sandbox-script.v1"
FIXTURE_VERSION = "v1.5.0-isolated-sandbox-fixture.v1"
SCRIPT_PATH = Path("docs/release/v1.5.0-isolated-sandbox-script.md")
FIXTURE_PATH = Path("tests/fixtures/v1.5.0-isolated-sandbox-fixture.v1.json")
DEFAULT_EVIDENCE_PATH = Path("docs/release/v1.5.0-isolated-sandbox-conversation-validation.md")
RUBRICS = (
    "temporal_ownership_pass",
    "specificity_pass",
    "calibration_narrowing_pass",
    "cutoff_contamination_pass",
    "experimental_ceiling_pass",
    "natural_language_pass",
    "algorithm_disclosure_pass",
    "strategy_forecast_separation_pass",
)
_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_FIELD = re.compile(r"^([a-z0-9_]+):\s*(.*?)\s*$")
_RUBRIC = re.compile(r"^-\s+([a-z0-9_]+):\s*(.*?)\s*$")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_evidence(text: str):
    fields = {}
    rubrics = {}
    errors = []
    in_critical_rubric = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            in_critical_rubric = line == "## Critical rubric"
            continue

        if in_critical_rubric:
            rubric_match = _RUBRIC.match(line)
            if rubric_match and rubric_match.group(1) in RUBRICS:
                key, value = rubric_match.groups()
                if key in rubrics:
                    errors.append("duplicate_rubric:%s" % key)
                else:
                    rubrics[key] = value
            continue

        field_match = _FIELD.match(line)
        if field_match:
            key, value = field_match.groups()
            if key in fields:
                errors.append("duplicate_field:%s" % key)
            else:
                fields[key] = value
    return fields, rubrics, errors


def _is_ready(value: str) -> bool:
    return bool(value and value.strip() and value.strip().upper() != "PENDING")


def validate_evidence(root: Path, evidence_path: Path, current_sha: str) -> dict:
    root = Path(root)
    evidence_path = Path(evidence_path)
    if not evidence_path.is_absolute():
        evidence_path = root / evidence_path

    errors = []
    if not _HEX40.fullmatch(current_sha or ""):
        errors.append("invalid_current_sha")

    if not evidence_path.is_file():
        return {
            "status": "FAIL",
            "release_allowed": False,
            "current_sha": current_sha,
            "errors": errors + ["evidence_file_missing"],
        }

    fields, rubrics, parse_errors = _parse_evidence(evidence_path.read_text(encoding="utf-8"))
    errors.extend(parse_errors)
    evidence_status = fields.get("status", "")

    if fields.get("schema_version") != EVIDENCE_SCHEMA_VERSION:
        errors.append("evidence_schema_mismatch")
    if fields.get("script_version") != SCRIPT_VERSION:
        errors.append("script_version_mismatch")
    if fields.get("fixture_version") != FIXTURE_VERSION:
        errors.append("fixture_version_mismatch")

    if evidence_status != "PASS":
        errors.append("evidence_status_not_pass")
        reported_status = evidence_status if evidence_status in {"PENDING", "FAIL"} else "FAIL"
        return {
            "status": reported_status,
            "release_allowed": False,
            "current_sha": current_sha,
            "errors": sorted(set(errors)),
        }

    tested_sha = fields.get("tested_release_candidate_sha", "")
    if not _HEX40.fullmatch(tested_sha):
        errors.append("tested_release_candidate_sha_invalid")

    for key in ("tested_distribution_digest", "tested_user_package_sha256", "script_sha256", "fixture_sha256"):
        if not _HEX64.fullmatch(fields.get(key, "")):
            errors.append("%s_invalid" % key)

    for key in ("sandbox_run_id", "sandbox_environment", "executed_at", "transcript_reference"):
        if not _is_ready(fields.get(key, "")):
            errors.append("%s_missing" % key)

    for rubric in RUBRICS:
        if rubrics.get(rubric) != "PASS":
            errors.append("rubric_not_pass:%s" % rubric)
    for extra in sorted(set(rubrics) - set(RUBRICS)):
        errors.append("unknown_rubric:%s" % extra)

    script_path = root / SCRIPT_PATH
    fixture_path = root / FIXTURE_PATH
    distribution_dir = root / "dist" / "ai"
    if not script_path.is_file():
        errors.append("script_file_missing")
    if not fixture_path.is_file():
        errors.append("fixture_file_missing")

    if not errors:
        actual_script_sha = _sha256(script_path)
        actual_fixture_sha = _sha256(fixture_path)
        if fields["script_sha256"] != actual_script_sha:
            errors.append("script_sha256_mismatch")
        if fields["fixture_sha256"] != actual_fixture_sha:
            errors.append("fixture_sha256_mismatch")

        try:
            surface_report = run_v15_release_surface_validation.run(distribution_dir)
        except Exception as exc:  # fail closed at release time
            errors.append("release_surface_validation_error:%s" % type(exc).__name__)
        else:
            if surface_report.get("status") != "PASS":
                errors.append("release_surface_not_pass")
            if fields["tested_distribution_digest"] != surface_report.get("distribution_digest"):
                errors.append("tested_distribution_digest_mismatch")

        try:
            package = build_release_package.render_user_package(distribution_dir)
            package_report = build_release_package.verify_user_package(package, distribution_dir)
        except Exception as exc:  # fail closed at release time
            errors.append("user_package_validation_error:%s" % type(exc).__name__)
        else:
            if fields["tested_user_package_sha256"] != package_report.get("sha256"):
                errors.append("tested_user_package_sha256_mismatch")

    release_allowed = not errors
    return {
        "status": "PASS" if release_allowed else "FAIL",
        "release_allowed": release_allowed,
        "current_sha": current_sha,
        "tested_release_candidate_sha": tested_sha,
        "errors": sorted(set(errors)),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Validate v1.5 isolated sandbox conversation evidence")
    parser.add_argument("--evidence", default=str(DEFAULT_EVIDENCE_PATH))
    parser.add_argument("--current-sha", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    report = validate_evidence(ROOT, Path(args.evidence), args.current_sha)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True) if args.json else report)
    return 0 if report["release_allowed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
