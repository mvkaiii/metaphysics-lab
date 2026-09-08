"""Read-only Case integrity diagnostics and reconciliation planning primitives."""

from __future__ import annotations

import hashlib
import json
from typing import Mapping, Optional

from .case_identity import parse_case_filename
from .case_pack import CASE_FILES, parse_front_matter, validate_case
from .errors import DistributionError


_GENERIC_LEGACY_BASENAMES = frozenset(
    {
        "命盤核心摘要.md",
        "命盤資料校驗紀錄.md",
        "驗證事件紀錄.md",
        "流年追蹤紀錄.md",
        "問事追蹤紀錄.md",
        "重大決策紀錄.md",
        "命主索引.md",
    }
)
_SAFE_ANALYSIS_SCOPES = ("natal", "yearly", "decision")
_CASE_ERROR_MAP = {
    "case_subject_mismatch": "subject_id_conflict",
    "case_subject_filename_mismatch": "canonical_filename_manifest_mismatch",
    "case_manifest_mismatch": "canonical_filename_manifest_mismatch",
    "case_schema_incompatible": "case_schema_incompatible",
}


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise DistributionError(
            "invalid_case_doctor_payload",
            "%s must be a structured mapping" % field,
            {"field": field},
        )
    return value


def _optional_text(value: object, field: str) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise DistributionError(
            "invalid_case_doctor_payload",
            "%s must be non-blank text when provided" % field,
            {"field": field},
        )
    return value.strip()


def _finding(
    code: str,
    severity: str,
    files=(),
    message: str = "",
    details: Optional[Mapping[str, object]] = None,
) -> dict:
    row = {
        "code": code,
        "severity": severity,
        "files": sorted(str(name) for name in files),
        "message": message,
    }
    if details:
        row["details"] = dict(details)
    return row


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _diagnostic_digest(result_without_digest: Mapping[str, object]) -> str:
    return hashlib.sha256(_canonical_json(result_without_digest)).hexdigest()


def _classify_project_file(filename: str, text: str) -> dict:
    """Classify one Project text file without changing it."""
    try:
        parsed = parse_case_filename(filename, CASE_FILES)
    except ValueError:
        parsed = None

    if parsed is not None and not parsed["legacy"]:
        return {
            "category": "canonical_subject_aware",
            "filename": filename,
            "slot": parsed["canonical_filename"],
            "filename_label": parsed["filename_label"],
            "subject_short_id": parsed["subject_short_id"],
        }

    if parsed is not None and parsed["legacy"]:
        try:
            metadata, _ = parse_front_matter(text)
        except DistributionError:
            metadata = {}
        if metadata.get("case_schema_version") == "1.0":
            return {
                "category": "formal_legacy_case_1_0",
                "filename": filename,
                "slot": parsed["canonical_filename"],
            }

    if filename in _GENERIC_LEGACY_BASENAMES:
        return {
            "category": "generic_legacy_known_name",
            "filename": filename,
        }

    lowered = filename.lower()
    if "astralium" in lowered or "external" in lowered:
        return {"category": "external_reference", "filename": filename}

    return {"category": "unrelated", "filename": filename}


def _case_validation_finding(
    error: DistributionError, authoritative_files
) -> dict:
    code = _CASE_ERROR_MAP.get(error.code, "case_validation_failed")
    messages = {
        "subject_id_conflict": "Canonical Case subject identity is inconsistent.",
        "canonical_filename_manifest_mismatch": "Canonical Case filename or 00 manifest is inconsistent.",
        "case_schema_incompatible": "Canonical Case schema is not supported by this runtime.",
        "case_validation_failed": "Canonical Case failed authoritative validation.",
    }
    details = {"original_error_code": error.code}
    if error.details:
        details["validation_details"] = dict(error.details)
    return _finding(
        code,
        "BLOCKING",
        authoritative_files,
        messages[code],
        details,
    )


def diagnose_case(payload: Mapping[str, object]) -> dict:
    """Return a deterministic, read-only diagnostic of Project Case files."""
    payload = _mapping(payload, "payload")
    unknown = sorted(set(payload) - {"project_files", "subject_context"})
    if unknown:
        raise DistributionError(
            "invalid_case_doctor_payload",
            "Case Doctor payload contains unsupported fields",
            {"unknown_fields": unknown},
        )

    project_files = _mapping(payload.get("project_files"), "project_files")
    subject_context_raw = payload.get("subject_context", {})
    subject_context = _mapping(subject_context_raw, "subject_context")
    unknown_context = sorted(
        set(subject_context)
        - {"subject_id", "subject_short_id", "subject_display_name"}
    )
    if unknown_context:
        raise DistributionError(
            "invalid_case_doctor_payload",
            "subject_context contains unsupported fields",
            {"unknown_fields": unknown_context},
        )

    target_subject_id = _optional_text(
        subject_context.get("subject_id"), "subject_context.subject_id"
    )
    target_short_id = _optional_text(
        subject_context.get("subject_short_id"), "subject_context.subject_short_id"
    )
    target_display_name = _optional_text(
        subject_context.get("subject_display_name"),
        "subject_context.subject_display_name",
    )

    classified = []
    for filename in sorted(project_files):
        text = project_files[filename]
        if not isinstance(filename, str) or not filename:
            raise DistributionError(
                "invalid_case_doctor_payload",
                "project_files keys must be non-empty filenames",
            )
        if not isinstance(text, str):
            raise DistributionError(
                "invalid_case_doctor_payload",
                "Project file content must be UTF-8 text",
                {"filename": filename},
            )
        classified.append(_classify_project_file(filename, text))

    canonical_rows = [
        row for row in classified if row["category"] == "canonical_subject_aware"
    ]
    formal_legacy = sorted(
        row["filename"]
        for row in classified
        if row["category"] == "formal_legacy_case_1_0"
    )
    generic_legacy = sorted(
        row["filename"]
        for row in classified
        if row["category"] == "generic_legacy_known_name"
    )
    authoritative_files = sorted(row["filename"] for row in canonical_rows)
    legacy_files = sorted(formal_legacy + generic_legacy)

    findings = []
    canonical_subject = None
    identities = []

    if authoritative_files:
        canonical_case_files = {
            filename: project_files[filename] for filename in authoritative_files
        }
        try:
            validate_case({"case_files": canonical_case_files})
        except DistributionError as exc:
            findings.append(_case_validation_finding(exc, authoritative_files))

    for row in canonical_rows:
        filename = row["filename"]
        try:
            metadata, _ = parse_front_matter(project_files[filename])
        except DistributionError as exc:
            findings.append(
                _finding(
                    "case_validation_failed",
                    "BLOCKING",
                    [filename],
                    "Canonical Case file metadata cannot be parsed.",
                    {"original_error_code": exc.code},
                )
            )
            continue

        identity = {
            "subject_id": metadata.get("subject_id"),
            "subject_short_id": metadata.get("subject_short_id"),
            "subject_display_name": metadata.get("subject_display_name"),
            "filename_label": metadata.get("filename_label"),
        }
        identities.append((filename, identity))

        if target_subject_id is not None and identity["subject_id"] != target_subject_id:
            findings.append(
                _finding(
                    "subject_id_conflict",
                    "BLOCKING",
                    [filename],
                    "Canonical Case subject_id conflicts with the requested subject.",
                    {
                        "expected_subject_id": target_subject_id,
                        "actual_subject_id": identity["subject_id"],
                    },
                )
            )

        if target_short_id is not None and row["subject_short_id"] != target_short_id:
            findings.append(
                _finding(
                    "duplicate_subject_candidate",
                    "BLOCKING",
                    [filename],
                    "Canonical Case filename short id conflicts with the requested subject.",
                    {
                        "expected_subject_short_id": target_short_id,
                        "actual_subject_short_id": row["subject_short_id"],
                    },
                )
            )

    valid_identities = [identity for _, identity in identities]
    if valid_identities:
        canonical_subject = dict(valid_identities[0])
        subject_ids = sorted(
            {identity.get("subject_id") for identity in valid_identities},
            key=lambda value: "" if value is None else str(value),
        )
        if len(subject_ids) > 1:
            findings.append(
                _finding(
                    "subject_id_conflict",
                    "BLOCKING",
                    [filename for filename, _ in identities],
                    "Canonical Case files contain more than one subject_id.",
                    {"subject_ids": subject_ids},
                )
            )
        short_ids = {identity.get("subject_short_id") for identity in valid_identities}
        display_names = {
            identity.get("subject_display_name") for identity in valid_identities
        }
        if len(short_ids) > 1 or len(display_names) > 1:
            findings.append(
                _finding(
                    "duplicate_subject_candidate",
                    "BLOCKING",
                    [filename for filename, _ in identities],
                    "Canonical Case identity metadata is ambiguous.",
                )
            )

        if target_display_name is not None and canonical_subject.get(
            "subject_display_name"
        ) != target_display_name:
            findings.append(
                _finding(
                    "duplicate_subject_candidate",
                    "BLOCKING",
                    [filename for filename, _ in identities],
                    "Canonical Case display name conflicts with the requested subject.",
                )
            )

    if generic_legacy:
        findings.append(
            _finding(
                "legacy_generic_file_detected",
                "WARN",
                generic_legacy,
                "Known generic legacy Project files are present alongside Case data.",
            )
        )
    if formal_legacy:
        findings.append(
            _finding(
                "duplicate_subject_candidate",
                "WARN",
                formal_legacy,
                "Formal legacy Case 1.0 files are present and require reconciliation review.",
            )
        )

    findings = sorted(
        findings,
        key=lambda row: (
            0 if row["severity"] == "BLOCKING" else 1,
            row["code"],
            tuple(row["files"]),
            row["message"],
        ),
    )
    blocked = any(row["severity"] == "BLOCKING" for row in findings)
    warned = any(row["severity"] == "WARN" for row in findings)
    if blocked:
        health = "BLOCKED"
        recommended_next_action = "user_resolution_required"
        safe_analysis_scopes = []
    elif warned:
        health = "WARN"
        recommended_next_action = "plan_reconciliation"
        safe_analysis_scopes = list(_SAFE_ANALYSIS_SCOPES)
    else:
        health = "PASS"
        recommended_next_action = "none"
        safe_analysis_scopes = list(_SAFE_ANALYSIS_SCOPES)

    result = {
        "health": health,
        "canonical_subject": canonical_subject,
        "authoritative_files": authoritative_files,
        "legacy_files": legacy_files,
        "findings": findings,
        "safe_analysis_scopes": safe_analysis_scopes,
        "recommended_next_action": recommended_next_action,
    }
    result["diagnostic_digest"] = _diagnostic_digest(result)
    return result
