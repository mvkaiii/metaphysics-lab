#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_SCHEMA_VERSION = "v1.7.0-isolated-sandbox-evidence.v1"
SCRIPT_VERSION = "v1.7.0-isolated-sandbox-script.v1"
BASE_FIXTURE_VERSION = "v1.7.0-isolated-sandbox-base.v1"
SCRIPT_PATH = Path("docs/release/v1.7.0-isolated-sandbox-script.md")
BASE_FIXTURE_PATH = Path("docs/release/v1.7.0-isolated-sandbox-base.json")
TRANSCRIPT_PATH = Path("docs/release/v1.7.0-isolated-sandbox-transcript.md")
DEFAULT_EVIDENCE_PATH = Path("docs/release/v1.7.0-isolated-sandbox-conversation-validation.md")
SCENARIOS = tuple("S%02d" % number for number in range(1, 13))
RUBRICS = (
    "guided_count_pass",
    "guided_timing_pass",
    "guided_specificity_pass",
    "case_integrity_pass",
    "no_auto_delete_pass",
    "validation_context_pass",
    "clean_denominator_pass",
    "blindness_pass",
    "experimental_ceiling_pass",
    "natural_language_pass",
)
EVIDENCE_SEAL_ALLOWED_PATHS = frozenset({
    TRANSCRIPT_PATH.as_posix(),
    DEFAULT_EVIDENCE_PATH.as_posix(),
    "docs/release/v1.7.0-qualification.md",
})
_REQUIRED_FIELDS = frozenset({
    "schema_version", "status", "script_version", "base_fixture_version",
    "tested_release_candidate_sha", "candidate_frozen_at", "executed_at",
    "adjudicated_at", "sandbox_run_id", "sandbox_environment", "script_sha256",
    "base_fixture_sha256", "transcript_sha256", "transcript_reference",
})
_BASE_REQUIRED_FIELDS = frozenset({
    "fixture_version", "classification", "privacy", "contains_private_user_data",
    "contains_outcome_data", "subject", "baseline",
})
_FORBIDDEN_BASE_KEYS = frozenset({
    "known_reality_context", "historical_event_ledger", "validation_events",
    "actual_outcome", "private_user_data",
})
_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_FIELD = re.compile(r"^([a-z0-9_]+):\s*(.*?)\s*$")
_SCENARIO = re.compile(r"^-\s+(S\d{2}):\s*(.*?)\s*$")
_RUBRIC = re.compile(r"^-\s+([a-z0-9_]+):\s*(.*?)\s*$")


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _is_ready(value):
    return isinstance(value, str) and bool(value.strip()) and value.strip().upper() != "PENDING"


def _parse_timestamp(value, field, errors):
    if not _is_ready(value):
        errors.append("%s_missing" % field)
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        errors.append("%s_invalid" % field)
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        errors.append("%s_timezone_missing" % field)
        return None
    return parsed


def _parse_evidence(text):
    fields, scenarios, rubrics, errors = {}, {}, {}, []
    section = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line == "## Scenario results":
            section = "scenarios"
            continue
        if line == "## Critical rubric":
            section = "rubrics"
            continue
        if line.startswith("## "):
            section = None
            continue
        if section == "scenarios":
            match = _SCENARIO.match(line)
            if match:
                key, value = match.groups()
                if key in scenarios:
                    errors.append("duplicate_scenario:%s" % key)
                else:
                    scenarios[key] = value
            continue
        if section == "rubrics":
            match = _RUBRIC.match(line)
            if match:
                key, value = match.groups()
                if key in rubrics:
                    errors.append("duplicate_rubric:%s" % key)
                else:
                    rubrics[key] = value
            continue
        match = _FIELD.match(line)
        if match:
            key, value = match.groups()
            if key in fields:
                errors.append("duplicate_field:%s" % key)
            else:
                fields[key] = value
    return fields, scenarios, rubrics, errors


def _find_forbidden_base_keys(value):
    found = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in _FORBIDDEN_BASE_KEYS:
                found.append(key)
            found.extend(_find_forbidden_base_keys(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(_find_forbidden_base_keys(child))
    return found


def validate_base_fixture(root):
    path = Path(root) / BASE_FIXTURE_PATH
    if not path.is_file():
        return ["base_fixture_file_missing"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return ["base_fixture_invalid_json"]
    if not isinstance(payload, dict):
        return ["base_fixture_not_object"]
    errors = []
    if payload.get("fixture_version") != BASE_FIXTURE_VERSION:
        errors.append("base_fixture_version_mismatch")
    if payload.get("classification") != "synthetic_test_case":
        errors.append("base_fixture_classification_mismatch")
    if payload.get("privacy") != "fictional_no_real_user_data":
        errors.append("base_fixture_privacy_mismatch")
    if payload.get("contains_private_user_data") is not False:
        errors.append("base_fixture_private_data_flag_not_false")
    if payload.get("contains_outcome_data") is not False:
        errors.append("base_fixture_outcome_data_flag_not_false")
    missing = sorted(_BASE_REQUIRED_FIELDS - set(payload))
    unknown = sorted(set(payload) - _BASE_REQUIRED_FIELDS)
    errors.extend("base_fixture_missing_field:%s" % key for key in missing)
    errors.extend("base_fixture_unexpected_field:%s" % key for key in unknown)
    for key in sorted(set(_find_forbidden_base_keys(payload))):
        errors.append("base_fixture_contains_%s" % key)
    subject = payload.get("subject")
    if not isinstance(subject, dict):
        errors.append("base_fixture_subject_missing")
    else:
        if subject.get("classification") != "fictional_subject":
            errors.append("base_fixture_subject_classification_mismatch")
        if not _is_ready(subject.get("subject_id")):
            errors.append("base_fixture_subject_id_missing")
        if not _is_ready(subject.get("display_name")):
            errors.append("base_fixture_display_name_missing")
    baseline = payload.get("baseline")
    if not isinstance(baseline, dict):
        errors.append("base_fixture_baseline_missing")
    else:
        if baseline.get("case_health") != "PASS":
            errors.append("base_fixture_case_health_mismatch")
        if baseline.get("historical_blind_disclosure_pending") is not False:
            errors.append("base_fixture_blind_gate_flag_mismatch")
    return sorted(set(errors))


def _validate_evidence_seal_delta(root, tested_sha, current_sha):
    if tested_sha == current_sha:
        return []
    try:
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", tested_sha, current_sha],
            cwd=str(root), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, check=False,
        )
    except OSError:
        return ["git_evidence_seal_check_unavailable"]
    if ancestor.returncode != 0:
        return ["tested_release_candidate_not_ancestor"]
    changed = subprocess.run(
        ["git", "diff", "--name-only", tested_sha, current_sha, "--"],
        cwd=str(root), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, check=False,
    )
    if changed.returncode != 0:
        return ["git_evidence_seal_diff_failed"]
    changed_paths = {
        line.strip().replace("\\", "/")
        for line in changed.stdout.splitlines() if line.strip()
    }
    forbidden = sorted(changed_paths - EVIDENCE_SEAL_ALLOWED_PATHS)
    return ["post_sandbox_non_evidence_change:%s" % path for path in forbidden]


def validate_evidence(root, evidence_path, current_sha):
    root = Path(root)
    evidence_path = Path(evidence_path)
    if not evidence_path.is_absolute():
        evidence_path = root / evidence_path
    errors = []
    if not _HEX40.fullmatch(current_sha or ""):
        errors.append("invalid_current_sha")
    if not evidence_path.is_file():
        return {"status": "FAIL", "release_allowed": False, "current_sha": current_sha,
                "errors": errors + ["evidence_file_missing"]}
    try:
        evidence_text = evidence_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {"status": "FAIL", "release_allowed": False, "current_sha": current_sha,
                "errors": errors + ["evidence_file_unreadable"]}
    fields, scenarios, rubrics, parse_errors = _parse_evidence(evidence_text)
    errors.extend(parse_errors)
    errors.extend(validate_base_fixture(root))
    errors.extend("missing_field:%s" % key for key in sorted(_REQUIRED_FIELDS - set(fields)))
    errors.extend("unknown_field:%s" % key for key in sorted(set(fields) - _REQUIRED_FIELDS))
    if fields.get("schema_version") != EVIDENCE_SCHEMA_VERSION:
        errors.append("evidence_schema_mismatch")
    if fields.get("script_version") != SCRIPT_VERSION:
        errors.append("script_version_mismatch")
    if fields.get("base_fixture_version") != BASE_FIXTURE_VERSION:
        errors.append("base_fixture_version_field_mismatch")
    evidence_status = fields.get("status", "")
    if evidence_status not in {"PENDING", "PASS", "FAIL"}:
        errors.append("evidence_status_invalid")
    if evidence_status != "PASS":
        return {"status": evidence_status if evidence_status in {"PENDING", "FAIL"} else "FAIL",
                "release_allowed": False, "current_sha": current_sha,
                "errors": sorted(set(errors + ["evidence_status_not_pass"]))}
    tested_sha = fields.get("tested_release_candidate_sha", "")
    if not _HEX40.fullmatch(tested_sha):
        errors.append("tested_release_candidate_sha_invalid")
    elif _HEX40.fullmatch(current_sha or ""):
        errors.extend(_validate_evidence_seal_delta(root, tested_sha, current_sha))
    frozen_at = _parse_timestamp(fields.get("candidate_frozen_at", ""), "candidate_frozen_at", errors)
    executed_at = _parse_timestamp(fields.get("executed_at", ""), "executed_at", errors)
    adjudicated_at = _parse_timestamp(fields.get("adjudicated_at", ""), "adjudicated_at", errors)
    if frozen_at is not None and executed_at is not None and not (executed_at > frozen_at):
        errors.append("execution_not_after_candidate_freeze")
    if executed_at is not None and adjudicated_at is not None and adjudicated_at < executed_at:
        errors.append("adjudication_before_execution")
    for key in ("sandbox_run_id", "sandbox_environment"):
        if not _is_ready(fields.get(key, "")):
            errors.append("%s_missing" % key)
    for key in ("script_sha256", "base_fixture_sha256", "transcript_sha256"):
        if not _HEX64.fullmatch(fields.get(key, "")):
            errors.append("%s_invalid" % key)
    if fields.get("transcript_reference") != TRANSCRIPT_PATH.as_posix():
        errors.append("transcript_reference_mismatch")
    for scenario in SCENARIOS:
        if scenarios.get(scenario) != "PASS":
            errors.append("scenario_not_pass:%s" % scenario)
    for extra in sorted(set(scenarios) - set(SCENARIOS)):
        errors.append("unknown_scenario:%s" % extra)
    for rubric in RUBRICS:
        if rubrics.get(rubric) != "PASS":
            errors.append("rubric_not_pass:%s" % rubric)
    for extra in sorted(set(rubrics) - set(RUBRICS)):
        errors.append("unknown_rubric:%s" % extra)
    paths = {
        "script_sha256": root / SCRIPT_PATH,
        "base_fixture_sha256": root / BASE_FIXTURE_PATH,
        "transcript_sha256": root / TRANSCRIPT_PATH,
    }
    for field, path in paths.items():
        if not path.is_file():
            errors.append("%s_file_missing" % field.removesuffix("_sha256"))
        elif _HEX64.fullmatch(fields.get(field, "")) and fields[field] != _sha256(path):
            errors.append("%s_mismatch" % field)
    release_allowed = not errors
    return {"status": "PASS" if release_allowed else "FAIL",
            "release_allowed": release_allowed, "current_sha": current_sha,
            "tested_release_candidate_sha": tested_sha, "errors": sorted(set(errors))}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate v1.7 isolated sandbox evidence.")
    parser.add_argument("--evidence", default=str(DEFAULT_EVIDENCE_PATH))
    parser.add_argument("--current-sha", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = validate_evidence(ROOT, Path(args.evidence), args.current_sha)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("status: %s" % report["status"])
        for error in report["errors"]:
            print("- %s" % error)
    return 0 if report["release_allowed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
