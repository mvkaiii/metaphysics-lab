#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import build_release_package  # noqa: E402
from tools import run_v16_release_surface_validation  # noqa: E402

EVIDENCE_SCHEMA_VERSION = "v1.6.0-isolated-sandbox-evidence.v2"
SCRIPT_VERSION = "v1.6.0-isolated-sandbox-script.v2"
BASE_FIXTURE_VERSION = "v1.6.0-isolated-sandbox-base.v1"
KNOWN_REALITY_FIXTURE_VERSION = "v1.6.0-isolated-sandbox-known-reality.v1"
HISTORICAL_LEDGER_FIXTURE_VERSION = "v1.6.0-isolated-sandbox-historical-ledger.v1"
SCRIPT_PATH = Path("docs/release/v1.6.0-isolated-sandbox-script.v2.md")
BASE_FIXTURE_PATH = Path("tests/fixtures/v1.6.0-isolated-sandbox-base.v1.json")
KNOWN_REALITY_FIXTURE_PATH = Path(
    "tests/fixtures/operator-only/v1.6.0-isolated-sandbox-known-reality.v1.json"
)
HISTORICAL_LEDGER_FIXTURE_PATH = Path(
    "tests/fixtures/operator-only/v1.6.0-isolated-sandbox-historical-ledger.v1.json"
)
TRANSCRIPT_PATH = Path("docs/release/v1.6.0-isolated-sandbox-transcript.md")
DEFAULT_EVIDENCE_PATH = Path(
    "docs/release/v1.6.0-isolated-sandbox-conversation-validation.md"
)
EVIDENCE_SEAL_ALLOWED_PATHS = frozenset(
    {
        "docs/release/v1.6.0-isolated-sandbox-transcript.md",
        "docs/release/v1.6.0-isolated-sandbox-conversation-validation.md",
        "docs/release/v1.6.0-qualification.md",
    }
)
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
            if rubric_match:
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


def _load_json(root: Path, relative_path: Path, label: str, errors: list[str]):
    path = root / relative_path
    if not path.is_file():
        errors.append("%s_fixture_file_missing" % label)
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        errors.append("%s_fixture_invalid_json" % label)
        return None


def _validate_fixture_version(payload, expected: str, label: str, errors: list[str]):
    if not isinstance(payload, dict):
        errors.append("%s_fixture_not_object" % label)
        return
    if payload.get("fixture_version") != expected:
        errors.append("%s_fixture_version_mismatch" % label)


def validate_fixture_contract(root: Path) -> list[str]:
    """Validate v2 child-safe and operator-only fixture boundaries."""
    root = Path(root)
    errors = []
    base = _load_json(root, BASE_FIXTURE_PATH, "base", errors)
    known_reality = _load_json(
        root, KNOWN_REALITY_FIXTURE_PATH, "known_reality", errors
    )
    historical_ledger = _load_json(
        root, HISTORICAL_LEDGER_FIXTURE_PATH, "historical_ledger", errors
    )

    _validate_fixture_version(base, BASE_FIXTURE_VERSION, "base", errors)
    _validate_fixture_version(
        known_reality,
        KNOWN_REALITY_FIXTURE_VERSION,
        "known_reality",
        errors,
    )
    _validate_fixture_version(
        historical_ledger,
        HISTORICAL_LEDGER_FIXTURE_VERSION,
        "historical_ledger",
        errors,
    )

    if isinstance(base, dict):
        if "known_reality_context" in base:
            errors.append("base_fixture_contains_known_reality_context")
        if "historical_event_ledger" in base:
            errors.append("base_fixture_contains_historical_event_ledger")
        expected_keys = {
            "fixture_version",
            "classification",
            "privacy",
            "subject",
            "target_year",
        }
        unexpected = sorted(set(base) - expected_keys)
        errors.extend("base_fixture_unexpected_field:%s" % key for key in unexpected)
        if base.get("classification") != "synthetic_test_case":
            errors.append("base_fixture_classification_mismatch")
        if base.get("privacy") != "fictional_no_real_user_data":
            errors.append("base_fixture_privacy_mismatch")
        if not isinstance(base.get("subject"), dict):
            errors.append("base_fixture_subject_missing")
        if not isinstance(base.get("target_year"), int):
            errors.append("base_fixture_target_year_missing")

    if isinstance(known_reality, dict):
        expected_keys = {
            "fixture_version",
            "classification",
            "privacy",
            "known_reality_context",
        }
        unexpected = sorted(set(known_reality) - expected_keys)
        errors.extend(
            "known_reality_fixture_unexpected_field:%s" % key for key in unexpected
        )
        if known_reality.get("classification") != "operator_only_known_reality":
            errors.append("known_reality_fixture_classification_mismatch")
        if known_reality.get("privacy") != "fictional_no_real_user_data":
            errors.append("known_reality_fixture_privacy_mismatch")
        context = known_reality.get("known_reality_context")
        if not isinstance(context, dict):
            errors.append("known_reality_fixture_context_missing")
        else:
            expected_context_keys = {
                "known_before_lock",
                "event_date",
                "event_time",
                "summary",
            }
            unexpected_context = sorted(set(context) - expected_context_keys)
            errors.extend(
                "known_reality_fixture_unexpected_context_field:%s" % key
                for key in unexpected_context
            )
            if context.get("known_before_lock") is not True:
                errors.append("known_reality_fixture_lock_flag_mismatch")
            for key in ("event_date", "event_time", "summary"):
                if not _is_ready(str(context.get(key, ""))):
                    errors.append("known_reality_fixture_%s_missing" % key)
        if "historical_event_ledger" in known_reality:
            errors.append("known_reality_fixture_contains_historical_event_ledger")

    if isinstance(historical_ledger, dict):
        expected_keys = {
            "fixture_version",
            "classification",
            "privacy",
            "historical_event_ledger",
        }
        unexpected = sorted(set(historical_ledger) - expected_keys)
        errors.extend(
            "historical_ledger_fixture_unexpected_field:%s" % key
            for key in unexpected
        )
        if historical_ledger.get("classification") != "operator_only_historical_ledger":
            errors.append("historical_ledger_fixture_classification_mismatch")
        if historical_ledger.get("privacy") != "fictional_no_real_user_data":
            errors.append("historical_ledger_fixture_privacy_mismatch")
        rows = historical_ledger.get("historical_event_ledger")
        if not isinstance(rows, list) or not rows:
            errors.append("historical_ledger_fixture_rows_missing")
        elif any(
            not isinstance(row, dict)
            or not isinstance(row.get("year"), int)
            or not _is_ready(str(row.get("status", "")))
            or not _is_ready(str(row.get("summary", "")))
            for row in rows
        ):
            errors.append("historical_ledger_fixture_row_shape_invalid")
        elif [row["year"] for row in rows] != list(range(2016, 2026)):
            errors.append("historical_ledger_fixture_year_range_invalid")
        if "known_reality_context" in historical_ledger:
            errors.append("historical_ledger_fixture_contains_known_reality_context")

    return sorted(set(errors))


def _validate_evidence_seal_delta(root: Path, tested_sha: str, current_sha: str):
    if tested_sha == current_sha:
        return []
    try:
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", tested_sha, current_sha],
            cwd=str(root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except OSError:
        return ["git_evidence_seal_check_unavailable"]
    if ancestor.returncode != 0:
        return ["tested_release_candidate_not_ancestor"]
    changed = subprocess.run(
        ["git", "diff", "--name-only", tested_sha, current_sha, "--"],
        cwd=str(root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if changed.returncode != 0:
        return ["git_evidence_seal_diff_failed"]
    changed_paths = {
        line.strip().replace("\\", "/")
        for line in changed.stdout.splitlines()
        if line.strip()
    }
    forbidden = sorted(changed_paths - EVIDENCE_SEAL_ALLOWED_PATHS)
    return ["post_sandbox_non_evidence_change:%s" % path for path in forbidden]


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

    fields, rubrics, parse_errors = _parse_evidence(
        evidence_path.read_text(encoding="utf-8")
    )
    errors.extend(parse_errors)
    errors.extend(validate_fixture_contract(root))
    evidence_status = fields.get("status", "")
    if fields.get("schema_version") != EVIDENCE_SCHEMA_VERSION:
        errors.append("evidence_schema_mismatch")
    if fields.get("script_version") != SCRIPT_VERSION:
        errors.append("script_version_mismatch")
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
    elif _HEX40.fullmatch(current_sha or ""):
        errors.extend(_validate_evidence_seal_delta(root, tested_sha, current_sha))

    for key, expected in (
        ("base_fixture_version", BASE_FIXTURE_VERSION),
        ("known_reality_fixture_version", KNOWN_REALITY_FIXTURE_VERSION),
        ("historical_ledger_fixture_version", HISTORICAL_LEDGER_FIXTURE_VERSION),
    ):
        if fields.get(key) != expected:
            errors.append("%s_mismatch" % key)

    for key in (
        "tested_distribution_digest",
        "tested_user_package_sha256",
        "script_sha256",
        "base_fixture_sha256",
        "known_reality_fixture_sha256",
        "historical_ledger_fixture_sha256",
        "transcript_sha256",
    ):
        if not _HEX64.fullmatch(fields.get(key, "")):
            errors.append("%s_invalid" % key)

    for key in ("sandbox_run_id", "sandbox_environment", "executed_at", "transcript_reference"):
        if not _is_ready(fields.get(key, "")):
            errors.append("%s_missing" % key)
    if _is_ready(fields.get("transcript_reference", "")) and fields.get(
        "transcript_reference"
    ) != TRANSCRIPT_PATH.as_posix():
        errors.append("transcript_reference_mismatch")

    for rubric in RUBRICS:
        if rubrics.get(rubric) != "PASS":
            errors.append("rubric_not_pass:%s" % rubric)
    for extra in sorted(set(rubrics) - set(RUBRICS)):
        errors.append("unknown_rubric:%s" % extra)

    script_path = root / SCRIPT_PATH
    fixture_paths = {
        "base_fixture_sha256": root / BASE_FIXTURE_PATH,
        "known_reality_fixture_sha256": root / KNOWN_REALITY_FIXTURE_PATH,
        "historical_ledger_fixture_sha256": root / HISTORICAL_LEDGER_FIXTURE_PATH,
        "transcript_sha256": root / TRANSCRIPT_PATH,
    }
    distribution_dir = root / "dist" / "ai"
    if not script_path.is_file():
        errors.append("script_file_missing")
    for path in fixture_paths.values():
        if not path.is_file():
            errors.append("evidence_bound_file_missing:%s" % path.relative_to(root).as_posix())

    if not errors:
        if fields["script_sha256"] != _sha256(script_path):
            errors.append("script_sha256_mismatch")
        for field, path in fixture_paths.items():
            if fields[field] != _sha256(path):
                errors.append("%s_mismatch" % field)
        try:
            surface_report = run_v16_release_surface_validation.run(distribution_dir)
        except Exception as exc:
            errors.append("release_surface_validation_error:%s" % type(exc).__name__)
        else:
            if surface_report.get("status") != "PASS":
                errors.append("release_surface_not_pass")
            if fields["tested_distribution_digest"] != surface_report.get(
                "distribution_digest"
            ):
                errors.append("tested_distribution_digest_mismatch")
        try:
            package = build_release_package.render_user_package(distribution_dir)
            package_report = build_release_package.verify_user_package(package, distribution_dir)
        except Exception as exc:
            errors.append("user_package_validation_error:%s" % type(exc).__name__)
        else:
            if package_report.get("release_version") != "1.6.0":
                errors.append("user_package_release_version_mismatch")
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
    parser = argparse.ArgumentParser(description="Validate v1.6 isolated sandbox conversation evidence")
    parser.add_argument("--evidence", default=str(DEFAULT_EVIDENCE_PATH))
    parser.add_argument("--current-sha", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = validate_evidence(ROOT, Path(args.evidence), args.current_sha)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True) if args.json else report)
    return 0 if report["release_allowed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
