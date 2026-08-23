"""Case-backed authority for immutable historical calibration locks.

The public SHA-256 digest remains a deterministic content checksum. The trust anchor
is host-retrieved persisted Case state: finalize reloads the original lock instead of
trusting request-supplied lock material, and public Case mutation cannot create this
reserved record type. This does not cryptographically authenticate a persistence layer
that an attacker can rewrite outside the runtime's mutation boundary.
"""

from __future__ import annotations

from typing import Mapping

from .case_identity import parse_case_filename
from .case_pack import CASE_FILES, _append_internal_case_record, _record_entries, parse_front_matter, validate_case
from .errors import DistributionError


_LOCK_SLOT = "07_問事追蹤紀錄.md"
_LOCK_RECORD_TYPE = "historical_calibration_lock"


def _actual_slot_filename(case_files: Mapping[str, object], canonical: str) -> str:
    matches = []
    for filename in case_files:
        if not isinstance(filename, str):
            continue
        try:
            parsed = parse_case_filename(filename, CASE_FILES)
        except ValueError:
            continue
        if parsed["canonical_filename"] == canonical:
            matches.append(filename)
    if len(matches) != 1:
        raise DistributionError(
            "lock_authority_required",
            "historical lock authority Case must contain exactly one persisted lock slot",
            {"canonical_filename": canonical, "matches": matches},
        )
    return matches[0]


def persist_historical_lock(
    case_files: Mapping[str, object],
    *,
    subject_id: str,
    calibration_id: str,
    locked_payload: Mapping[str, object],
    payload_digest: str,
    updated_at: str,
    last_modified_by: str,
) -> dict:
    if not isinstance(case_files, Mapping):
        raise DistributionError("invalid_case_payload", "case_files must be a mapping")
    validation = validate_case({"case_files": case_files})
    if validation.get("subject_id") != subject_id:
        raise DistributionError(
            "immutable_calibration_violation",
            "historical lock subject does not match Case subject",
            {"lock_subject_id": subject_id, "case_subject_id": validation.get("subject_id")},
        )
    record_id = "historical-lock-%s" % calibration_id
    entry = {
        "record_id": record_id,
        "record_type": _LOCK_RECORD_TYPE,
        "subject_id": subject_id,
        "locked_payload": dict(locked_payload),
        "payload_digest": payload_digest,
        "immutable": True,
    }
    update = _append_internal_case_record({
        "case_files": case_files,
        "filename": _LOCK_SLOT,
        "operation": "append",
        "updated_at": updated_at,
        "last_modified_by": last_modified_by,
        "entry": entry,
    })
    return {
        "lock_record_id": record_id,
        "changed_files": update["changed_files"],
    }


def load_historical_lock(case_files: Mapping[str, object], lock_record_id: str) -> dict:
    if not isinstance(case_files, Mapping):
        raise DistributionError("lock_authority_required", "finalize requires authoritative Case files")
    if not isinstance(lock_record_id, str) or not lock_record_id.strip():
        raise DistributionError("lock_authority_required", "finalize requires a historical lock_record_id")
    validation = validate_case({"case_files": case_files})
    actual = _actual_slot_filename(case_files, _LOCK_SLOT)
    _, body = parse_front_matter(case_files[actual])
    records = _record_entries(body)
    record = records.get(lock_record_id)
    if not isinstance(record, Mapping):
        raise DistributionError(
            "lock_authority_required",
            "historical lock_record_id is not present in the authoritative Case",
            {"lock_record_id": lock_record_id},
        )
    if record.get("record_type") != _LOCK_RECORD_TYPE or record.get("immutable") is not True:
        raise DistributionError(
            "immutable_calibration_violation",
            "historical lock authority record has invalid immutable semantics",
            {"lock_record_id": lock_record_id},
        )
    if record.get("subject_id") != validation.get("subject_id"):
        raise DistributionError(
            "immutable_calibration_violation",
            "historical lock authority subject does not match Case subject",
            {"lock_record_id": lock_record_id},
        )
    locked = record.get("locked_payload")
    digest = record.get("payload_digest")
    if not isinstance(locked, Mapping) or not isinstance(digest, str) or not digest:
        raise DistributionError(
            "immutable_calibration_violation",
            "historical lock authority record is malformed",
            {"lock_record_id": lock_record_id},
        )
    calibration_id = locked.get("calibration_id")
    if not isinstance(calibration_id, str) or not calibration_id or lock_record_id != "historical-lock-%s" % calibration_id:
        raise DistributionError(
            "immutable_calibration_violation",
            "historical lock record_id is not bound to locked calibration_id",
            {"lock_record_id": lock_record_id},
        )
    if locked.get("subject_id") != record.get("subject_id"):
        raise DistributionError(
            "immutable_calibration_violation",
            "historical locked payload subject does not match authority record subject",
            {"lock_record_id": lock_record_id},
        )
    return {
        "subject_id": validation["subject_id"],
        "locked_payload": dict(locked),
        "payload_digest": digest,
        "lock_record_id": lock_record_id,
    }
