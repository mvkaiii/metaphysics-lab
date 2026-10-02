"""Project Contract 1.3 natal-revision and Base Case integrity helpers.

These helpers version semantic natal revision identity separately from exact rendered
Case bytes. They do not persist files or interpret metaphysical meaning.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Mapping

from .case_identity import parse_case_filename
from .errors import DistributionError


PROJECT_CONTRACT_V13 = "1.3"
NATAL_REVISION_PROFILE = "natal-revision-v1"
BASE_CASE_DIGEST_PROFILE = "base-case-digest-v1"
_NATAL_REVISION_RE = re.compile(r"^nrev_[0-9a-f]{64}$")
_BASE_CASE_DIGEST_RE = re.compile(r"^bcase_[0-9a-f]{64}$")
_CORRECTION_CLASSES = frozenset((
    "birth_basis_change",
    "source_correction",
    "external_refresh",
    "rule_upgrade",
))


def _canonical_bytes(value: object, error_code: str = "invalid_case_revision") -> bytes:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        return encoded.encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise DistributionError(
            error_code,
            "revision authority payload must contain only standard JSON values",
        ) from exc


def natal_revision_id(kind: str, value: Mapping[str, object]) -> str:
    if kind not in ("normalized_natal", "candidate_envelope"):
        raise DistributionError(
            "invalid_case_revision",
            "unsupported natal revision kind",
            {"kind": kind},
        )
    if not isinstance(value, Mapping):
        raise DistributionError(
            "invalid_case_revision",
            "natal revision source must be a structured mapping",
            {"kind": kind},
        )
    payload = {
        "profile": NATAL_REVISION_PROFILE,
        "kind": kind,
        "value": value,
    }
    return "nrev_" + hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def validate_natal_revision_id(value: object) -> str:
    if not isinstance(value, str) or not _NATAL_REVISION_RE.fullmatch(value):
        raise DistributionError(
            "invalid_case_metadata",
            "natal_revision_id is malformed",
            {"natal_revision_id": value},
        )
    return value


def validate_base_case_digest(value: object) -> str:
    if not isinstance(value, str) or not _BASE_CASE_DIGEST_RE.fullmatch(value):
        raise DistributionError(
            "invalid_case_revision",
            "base_case_digest is malformed",
            {"base_case_digest": value},
        )
    return value


def _length_prefix(value: bytes) -> bytes:
    return len(value).to_bytes(8, "big") + value


def base_case_digest(case_files: Mapping[str, object]) -> str:
    """Bind exact 00-04 filenames and UTF-8 bytes in canonical slot order."""

    if not isinstance(case_files, Mapping):
        raise DistributionError(
            "invalid_case_payload",
            "case_files must be a structured mapping",
        )

    from .case_pack import BASE_CASE_FILES, CASE_FILES

    by_canonical = {}
    for actual, content in case_files.items():
        if not isinstance(actual, str) or not isinstance(content, str):
            raise DistributionError(
                "invalid_case_markdown",
                "Case filenames and contents must be text",
            )
        try:
            parsed = parse_case_filename(actual, CASE_FILES)
        except ValueError:
            # External reference files are intentionally outside the Base Case digest.
            continue
        canonical = parsed["canonical_filename"]
        if canonical not in BASE_CASE_FILES:
            continue
        if canonical in by_canonical:
            raise DistributionError(
                "case_file_set_mismatch",
                "Base Case digest received duplicate canonical slots",
                {"canonical_filename": canonical},
            )
        by_canonical[canonical] = (actual, content)

    missing = [name for name in BASE_CASE_FILES if name not in by_canonical]
    if missing:
        raise DistributionError(
            "case_file_set_mismatch",
            "Base Case digest requires all 00-04 files",
            {"missing_base": missing},
        )

    digest = hashlib.sha256()
    digest.update((BASE_CASE_DIGEST_PROFILE + "\0").encode("utf-8"))
    for canonical in BASE_CASE_FILES:
        actual, content = by_canonical[canonical]
        digest.update(_length_prefix(canonical.encode("utf-8")))
        digest.update(_length_prefix(actual.encode("utf-8")))
        digest.update(_length_prefix(content.encode("utf-8")))
    return "bcase_" + digest.hexdigest()


def correction_class(value: object) -> str:
    if not isinstance(value, str) or value not in _CORRECTION_CLASSES:
        raise DistributionError(
            "invalid_case_revision",
            "unsupported correction_class",
            {
                "correction_class": value,
                "allowed": sorted(_CORRECTION_CLASSES),
            },
        )
    return value


def correction_reason(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DistributionError(
            "invalid_case_revision",
            "correction_reason must be non-empty text",
        )
    return value.strip()

_LINEAGE_START = "<!-- natal-revisions:start -->"
_LINEAGE_END = "<!-- natal-revisions:end -->"


def _lineage_records(body: str) -> list:
    start = body.find(_LINEAGE_START)
    end = body.find(_LINEAGE_END)
    if start < 0 and end < 0:
        return []
    if start < 0 or end < 0 or end <= start:
        raise DistributionError(
            "invalid_case_revision",
            "natal revision lineage markers are malformed",
        )
    content_start = start + len(_LINEAGE_START)
    block = body[content_start:end].strip()
    if not block.startswith("```json\n") or not block.endswith("\n```"):
        raise DistributionError(
            "invalid_case_revision",
            "natal revision lineage JSON block is malformed",
        )
    try:
        records = json.loads(block[len("```json\n"):-len("\n```")])
    except (TypeError, ValueError) as exc:
        raise DistributionError(
            "invalid_case_revision",
            "natal revision lineage JSON cannot be parsed",
        ) from exc
    if not isinstance(records, list) or any(not isinstance(item, Mapping) for item in records):
        raise DistributionError(
            "invalid_case_revision",
            "natal revision lineage must be a list of records",
        )
    return [dict(item) for item in records]


def _append_lineage(body: str, records: list) -> str:
    if _LINEAGE_START in body or _LINEAGE_END in body:
        raise DistributionError(
            "invalid_case_revision",
            "fresh Base Case calibration body unexpectedly contains lineage markers",
        )
    encoded = json.dumps(records, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
    return (
        body.rstrip()
        + "\n\n## Natal Revision Lineage\n\n"
        + _LINEAGE_START
        + "\n```json\n"
        + encoded
        + "\n```\n"
        + _LINEAGE_END
        + "\n"
    )


def build_base_case_digest(payload: Mapping[str, object]) -> dict:
    if not isinstance(payload, Mapping):
        raise DistributionError("invalid_case_payload", "payload must be a structured mapping")
    digest = base_case_digest(payload.get("case_files"))
    return {
        "profile": BASE_CASE_DIGEST_PROFILE,
        "base_case_digest": digest,
    }


def replace_natal_base(payload: Mapping[str, object]) -> dict:
    """Atomically prepare a Project Contract 1.3 natal Base Case replacement.

    The function returns changed canonical files but performs no external persistence.
    Existing tracking bodies and immutable historical records are preserved.
    """

    if not isinstance(payload, Mapping):
        raise DistributionError("invalid_case_payload", "payload must be a structured mapping")

    from . import case_pack
    from .partial_case import export_partial_case_markdown

    case_files = payload.get("case_files")
    validation = case_pack.validate_case({"case_files": case_files})
    if validation.get("case_schema_version") != case_pack.CASE_SCHEMA_VERSION:
        raise DistributionError(
            "case_schema_incompatible",
            "natal Base Case replacement requires Case Schema 1.1",
        )
    identity = validation.get("subject")
    if not isinstance(identity, Mapping):
        raise DistributionError(
            "invalid_case_metadata",
            "natal Base Case replacement requires subject-aware Case identity",
        )

    updated_at = case_pack._timestamp(payload.get("updated_at"), "updated_at")
    modified_by = case_pack._text(payload.get("last_modified_by", "ai"), "last_modified_by")
    change_class = correction_class(payload.get("correction_class"))
    reason = correction_reason(payload.get("correction_reason"))

    normalized = payload.get("normalized_natal")
    candidate = payload.get("candidate_envelope")
    if (normalized is None) == (candidate is None):
        raise DistributionError(
            "invalid_case_revision",
            "replacement requires exactly one of normalized_natal or candidate_envelope",
        )

    export_payload = {
        "subject_id": identity["subject_id"],
        "subject_display_name": identity["subject_display_name"],
        "subject_short_id": identity["subject_short_id"],
        "filename_label": identity["filename_label"],
        "generated_at": updated_at,
        "last_modified_by": modified_by,
        "project_contract_version": PROJECT_CONTRACT_V13,
    }
    if normalized is not None:
        export_payload["normalized_natal"] = normalized
        if payload.get("analysis_sections") is not None:
            export_payload["analysis_sections"] = payload.get("analysis_sections")
        fresh = case_pack.export_case_markdown(export_payload)
    else:
        export_payload["candidate_envelope"] = candidate
        export_payload["resolved_location"] = payload.get("resolved_location")
        fresh = export_partial_case_markdown(export_payload)

    new_revision = validate_natal_revision_id(fresh.get("natal_revision_id"))
    old_revision = validation.get("natal_revision_id")
    old_digest = base_case_digest(case_files)

    if (
        validation.get("project_contract_version") == PROJECT_CONTRACT_V13
        and old_revision == new_revision
    ):
        return {
            "status": "no_change",
            "subject_id": identity["subject_id"],
            "project_contract_version": PROJECT_CONTRACT_V13,
            "natal_revision_profile": NATAL_REVISION_PROFILE,
            "natal_revision_id": new_revision,
            "base_case_digest": old_digest,
            "changed_files": {},
            "preserved_tracking_files": [],
        }

    old_canonical, old_actual, _ = case_pack._case_files(case_files)
    fresh_canonical, _, _ = case_pack._case_files(fresh["files"])
    materialized = set(old_canonical)
    previous_lineage = []
    if "02_命盤資料校驗紀錄.md" in old_canonical:
        _, old_calibration_body = case_pack.parse_front_matter(
            old_canonical["02_命盤資料校驗紀錄.md"]
        )
        previous_lineage = _lineage_records(old_calibration_body)

    lineage_record = {
        "profile": NATAL_REVISION_PROFILE,
        "previous_natal_revision_id": old_revision,
        "previous_revision_authority": "bound" if old_revision else "legacy_unbound",
        "previous_project_contract_version": validation.get("project_contract_version"),
        "previous_base_case_digest": old_digest,
        "new_natal_revision_id": new_revision,
        "correction_class": change_class,
        "correction_reason": reason,
        "corrected_at": updated_at,
    }
    lineage = previous_lineage + [lineage_record]

    final_files = {}
    changed_files = {}
    for canonical in case_pack.BASE_CASE_FILES:
        old_text = old_canonical[canonical]
        old_metadata, _ = case_pack.parse_front_matter(old_text)
        new_metadata, new_body = case_pack.parse_front_matter(fresh_canonical[canonical])
        new_metadata["created_at"] = old_metadata["created_at"]
        new_metadata["last_updated_at"] = updated_at
        new_metadata["last_modified_by"] = modified_by
        if canonical == "00_專案索引.md":
            new_metadata["natal_revision_supersedes"] = old_revision or "legacy_unbound"
            new_metadata["natal_revision_correction_class"] = change_class
            new_metadata["natal_revision_corrected_at"] = updated_at
            new_metadata["natal_revision_reason_sha256"] = hashlib.sha256(
                reason.encode("utf-8")
            ).hexdigest()
            new_body = case_pack._replace_manifest_lines(
                new_body,
                identity,
                materialized,
            )
        if canonical == "02_命盤資料校驗紀錄.md":
            new_body = _append_lineage(new_body, lineage)
        actual = old_actual[canonical]
        rendered = case_pack._rewrite_case_file(new_metadata, new_body)
        final_files[actual] = rendered
        changed_files[actual] = rendered

    preserved_tracking = []
    for canonical in case_pack.PROGRESSIVE_CASE_FILES:
        if canonical not in old_canonical:
            continue
        actual = old_actual[canonical]
        old_text = old_canonical[canonical]
        # Tracking files are append-only / lock-bearing evidence. A natal Base Case
        # replacement must not rewrite their bytes merely to align contract metadata.
        final_files[actual] = old_text
        preserved_tracking.append(actual)

    final_validation = case_pack.validate_case({"case_files": final_files})
    if final_validation.get("natal_revision_id") != new_revision:
        raise DistributionError(
            "case_natal_revision_mismatch",
            "replacement output failed natal revision validation",
        )

    new_digest = base_case_digest(final_files)
    return {
        "status": "replacement_ready",
        "subject_id": identity["subject_id"],
        "project_contract_version": PROJECT_CONTRACT_V13,
        "natal_revision_profile": NATAL_REVISION_PROFILE,
        "previous_natal_revision_id": old_revision,
        "previous_revision_authority": "bound" if old_revision else "legacy_unbound",
        "natal_revision_id": new_revision,
        "previous_base_case_digest": old_digest,
        "base_case_digest": new_digest,
        "revision_lineage": lineage,
        "historical_calibration_status": "uncalibrated",
        "changed_files": changed_files,
        "case_files": final_files,
        "preserved_tracking_files": preserved_tracking,
        "validation": final_validation,
    }
