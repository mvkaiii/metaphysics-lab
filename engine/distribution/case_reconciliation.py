"""Deterministic dry-run reconciliation planner for Case Doctor diagnostics."""

from __future__ import annotations

import hashlib
import json
from typing import Mapping

from .errors import DistributionError


_TIME_KEYS = ("date", "event_date", "year", "target_year")
_CATEGORY_KEYS = ("category", "record_category", "domain", "event_family")
_ALLOWED_ACTION_TYPES = frozenset(
    {
        "ignore_exact_duplicate",
        "import_missing_record_via_update_case_record",
        "migrate_formal_legacy_case",
        "request_subject_resolution",
        "request_semantic_duplicate_resolution",
        "retain_unrelated_file",
    }
)


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise DistributionError(
            "invalid_case_reconciliation_payload",
            "%s must be a structured mapping" % field,
            {"field": field},
        )
    return value


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _digest(value: Mapping[str, object]) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _subject_context_from_diagnostic(diagnostic: Mapping[str, object]) -> dict:
    subject = diagnostic.get("canonical_subject")
    if not isinstance(subject, Mapping):
        return {}
    context = {}
    for key in ("subject_id", "subject_short_id", "subject_display_name"):
        value = subject.get(key)
        if isinstance(value, str) and value.strip():
            context[key] = value.strip()
    return context


def _first_explicit(record: Mapping[str, object], keys) -> object:
    for key in keys:
        if key in record and record[key] not in (None, ""):
            return record[key]
    return None


def _possible_semantic_pair(left: Mapping[str, object], right: Mapping[str, object]) -> bool:
    left_time = _first_explicit(left, _TIME_KEYS)
    right_time = _first_explicit(right, _TIME_KEYS)
    left_category = _first_explicit(left, _CATEGORY_KEYS)
    right_category = _first_explicit(right, _CATEGORY_KEYS)
    return (
        left_time is not None
        and right_time is not None
        and left_time == right_time
        and left_category is not None
        and right_category is not None
        and left_category == right_category
    )


def _missing_record_actions(project_files: Mapping[str, object], classified) -> list:
    from .case_doctor import _structured_tracking_records

    records = _structured_tracking_records(project_files, classified)
    canonical_by_slot = {}
    legacy_records = []
    for row in records:
        if row["source_kind"] == "canonical":
            canonical_by_slot.setdefault(row["slot"], []).append(row)
        else:
            legacy_records.append(row)

    actions = []
    seen = set()
    for legacy in legacy_records:
        canonical_records = canonical_by_slot.get(legacy["slot"], [])
        if any(
            candidate["fingerprint"] == legacy["fingerprint"]
            for candidate in canonical_records
        ):
            continue
        if any(
            _possible_semantic_pair(candidate["record"], legacy["record"])
            for candidate in canonical_records
        ):
            continue
        key = (legacy["slot"], legacy["file"], legacy["fingerprint"])
        if key in seen:
            continue
        seen.add(key)
        actions.append(
            {
                "type": "import_missing_record_via_update_case_record",
                "source_file": legacy["file"],
                "target_slot": legacy["slot"],
                "record": dict(legacy["record"]),
                "record_fingerprint": legacy["fingerprint"],
            }
        )
    return actions


def _validate_action_types(actions) -> None:
    invalid = sorted(
        {
            action.get("type")
            for action in actions
            if not isinstance(action, Mapping)
            or action.get("type") not in _ALLOWED_ACTION_TYPES
        },
        key=str,
    )
    if invalid:
        raise DistributionError(
            "unsafe_case_reconciliation_plan",
            "reconciliation plan contains a non-allowlisted action",
            {"invalid_action_types": invalid},
        )


def plan_case_reconciliation(payload: Mapping[str, object]) -> dict:
    """Return a deterministic dry-run plan without mutating any Project file."""
    from .case_doctor import _classify_project_file, diagnose_case

    payload = _mapping(payload, "payload")
    unknown = sorted(set(payload) - {"project_files", "diagnostic"})
    if unknown:
        raise DistributionError(
            "invalid_case_reconciliation_payload",
            "reconciliation payload contains unsupported fields",
            {"unknown_fields": unknown},
        )
    project_files = _mapping(payload.get("project_files"), "project_files")
    diagnostic = _mapping(payload.get("diagnostic"), "diagnostic")

    recomputed = diagnose_case(
        {
            "project_files": project_files,
            "subject_context": _subject_context_from_diagnostic(diagnostic),
        }
    )
    if _canonical_json(diagnostic) != _canonical_json(recomputed):
        raise DistributionError(
            "case_diagnostic_mismatch",
            "supplied Case diagnostic does not match the current Project files",
            {
                "supplied_digest": diagnostic.get("diagnostic_digest"),
                "recomputed_digest": recomputed.get("diagnostic_digest"),
            },
        )

    preserve_files = sorted(str(name) for name in project_files)
    do_not_delete_yet = list(recomputed.get("legacy_files", []))
    actions = []
    conflicts = []

    if recomputed["health"] == "BLOCKED":
        actions.append(
            {
                "type": "request_subject_resolution",
                "finding_codes": sorted(
                    {
                        finding["code"]
                        for finding in recomputed.get("findings", [])
                        if finding.get("severity") == "BLOCKING"
                    }
                ),
            }
        )
        result = {
            "status": "blocked",
            "actions": actions,
            "requires_user_confirmation": True,
            "preserve_files": preserve_files,
            "do_not_delete_yet": do_not_delete_yet,
            "conflicts_requiring_user_choice": [],
        }
        result["plan_digest"] = _digest(result)
        return result

    if recomputed["health"] == "PASS":
        result = {
            "status": "no_change",
            "actions": [],
            "requires_user_confirmation": False,
            "preserve_files": preserve_files,
            "do_not_delete_yet": [],
            "conflicts_requiring_user_choice": [],
        }
        result["plan_digest"] = _digest(result)
        return result

    for finding in recomputed.get("findings", []):
        code = finding.get("code")
        details = finding.get("details", {})
        if code == "record_duplicate_exact":
            actions.append(
                {
                    "type": "ignore_exact_duplicate",
                    "files": list(finding.get("files", [])),
                    "slot": details.get("slot"),
                    "record_ids": list(details.get("record_ids", [])),
                    "auto_merge_allowed": False,
                }
            )
        elif code == "record_possible_semantic_duplicate":
            conflict = {
                "code": code,
                "files": list(finding.get("files", [])),
                "slot": details.get("slot"),
                "record_ids": list(details.get("record_ids", [])),
            }
            conflicts.append(conflict)
            actions.append(
                {
                    "type": "request_semantic_duplicate_resolution",
                    **conflict,
                }
            )

    classified = [
        _classify_project_file(filename, project_files[filename])
        for filename in sorted(project_files)
    ]
    formal_legacy_files = sorted(
        row["filename"]
        for row in classified
        if row["category"] == "formal_legacy_case_1_0"
    )
    if formal_legacy_files:
        actions.append(
            {
                "type": "migrate_formal_legacy_case",
                "files": formal_legacy_files,
            }
        )

    actions.extend(_missing_record_actions(project_files, classified))
    actions = sorted(actions, key=lambda action: _canonical_json(action))
    conflicts = sorted(conflicts, key=lambda conflict: _canonical_json(conflict))
    _validate_action_types(actions)

    result = {
        "status": "safe_plan",
        "actions": actions,
        "requires_user_confirmation": True,
        "preserve_files": preserve_files,
        "do_not_delete_yet": do_not_delete_yet,
        "conflicts_requiring_user_choice": conflicts,
    }
    result["plan_digest"] = _digest(result)
    return result
