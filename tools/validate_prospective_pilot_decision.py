"""Validate the public prospective-pilot human decision receipt.

The receipt records de-identified governance decisions only. It does not store
case data, predictions, outcomes, or prove that an approver had authority.
"""

from __future__ import annotations

from datetime import datetime
import math
import re
from typing import Any, Mapping


_DECISION_IDS = {"D%02d" % index for index in range(1, 13)}
_TOP_FIELDS = {
    "schema_version", "protocol_decision_status", "pilot_status", "decisions",
    "pilot_start_authorization",
}
_ROW_FIELDS = {
    "id", "status", "public_summary", "approver_role", "approved_at",
    "evidence_refs",
}
_AUTH_FIELDS = {
    "authorized", "authorized_by_role", "authorized_at", "candidate_commit",
    "package_sha256", "manifest_sha256", "protocol_sha256",
}
_ROW_STATUSES = {"PENDING", "APPROVED", "REJECTED"}
_PROTOCOL_STATUSES = {"PENDING_ITEM_APPROVAL", "ALL_ITEMS_APPROVED", "REJECTED"}
_PILOT_STATUSES = {"NOT_STARTED", "READY_FOR_START_AUTHORIZATION", "AUTHORIZED_NOT_STARTED"}
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40,64}$")
_FORBIDDEN_KEYS = {
    "case", "case_id", "case_ids", "birth", "birth_data", "prediction",
    "predictions", "prediction_lock", "outcome", "outcomes", "private_outcomes",
    "source_record", "source_records", "oracle_payload",
}


def _unknown_fields(value, allowed, path, errors):
    for key in sorted(set(value) - allowed):
        errors.append(f"{path}: unknown field {key!r}")


def _scan_forbidden(value, path, errors):
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key in _FORBIDDEN_KEYS or key.startswith("private_"):
                errors.append(f"{path}: forbidden private payload field {key!r}")
            _scan_forbidden(child, f"{path}.{key}", errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_forbidden(child, f"{path}[{index}]", errors)


def _nonempty(value, path, errors):
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path}: expected a non-empty string")
        return False
    return True


def _offset_datetime(value, path, errors):
    if not isinstance(value, str) or not value:
        errors.append(f"{path}: expected an ISO-8601 datetime with offset")
        return False
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        errors.append(f"{path}: invalid ISO-8601 datetime")
        return False
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        errors.append(f"{path}: datetime requires an explicit offset")
        return False
    return True


def _sha256(value, path, errors):
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        errors.append(f"{path}: expected a lowercase SHA256")
        return False
    return True


def _commit(value, path, errors):
    if not isinstance(value, str) or not _COMMIT.fullmatch(value):
        errors.append(f"{path}: expected a 40 to 64 character lowercase commit SHA")
        return False
    return True


def validate_decision_receipt(receipt: Mapping[str, Any]) -> list[str]:
    errors = []
    if not isinstance(receipt, Mapping):
        return ["receipt: expected an object"]
    _scan_forbidden(receipt, "receipt", errors)
    _unknown_fields(receipt, _TOP_FIELDS, "receipt", errors)
    for key in sorted(_TOP_FIELDS):
        if key not in receipt:
            errors.append(f"receipt: missing field {key}")
    if receipt.get("schema_version") != "1.0":
        errors.append("receipt.schema_version: expected '1.0'")

    protocol_status = receipt.get("protocol_decision_status")
    if protocol_status not in _PROTOCOL_STATUSES:
        errors.append("receipt.protocol_decision_status: unsupported status")
    pilot_status = receipt.get("pilot_status")
    if pilot_status not in _PILOT_STATUSES:
        errors.append("receipt.pilot_status: unsupported status")

    decisions = receipt.get("decisions")
    rows_by_id = {}
    if not isinstance(decisions, list):
        errors.append("receipt.decisions: expected a list")
        decisions = []
    for index, row in enumerate(decisions):
        path = f"receipt.decisions[{index}]"
        if not isinstance(row, Mapping):
            errors.append(f"{path}: expected an object")
            continue
        _unknown_fields(row, _ROW_FIELDS, path, errors)
        decision_id = row.get("id")
        if decision_id not in _DECISION_IDS:
            errors.append(f"{path}.id: expected one of D01-D12")
        elif decision_id in rows_by_id:
            errors.append(f"{path}.id: duplicate decision {decision_id}")
        else:
            rows_by_id[decision_id] = row
        status = row.get("status")
        if status not in _ROW_STATUSES:
            errors.append(f"{path}.status: unsupported status")
            continue
        refs = row.get("evidence_refs")
        if not isinstance(refs, list) or any(not isinstance(ref, str) or not ref for ref in refs):
            errors.append(f"{path}.evidence_refs: expected a list of non-empty strings")
        if status == "PENDING":
            if row.get("public_summary") != "":
                errors.append(f"{path}.public_summary: PENDING decision must use an empty public summary")
            if row.get("approver_role") is not None:
                errors.append(f"{path}.approver_role: PENDING decision must be null")
            if row.get("approved_at") is not None:
                errors.append(f"{path}.approved_at: PENDING decision must be null")
        else:
            _nonempty(row.get("public_summary"), f"{path}.public_summary", errors)
            _nonempty(row.get("approver_role"), f"{path}.approver_role", errors)
            _offset_datetime(row.get("approved_at"), f"{path}.approved_at", errors)

    actual_ids = set(rows_by_id)
    if actual_ids != _DECISION_IDS:
        missing = sorted(_DECISION_IDS - actual_ids)
        extra = sorted(actual_ids - _DECISION_IDS)
        errors.append(f"receipt.decisions: decision census mismatch missing={missing} extra={extra}")

    statuses = {decision_id: rows_by_id[decision_id].get("status") for decision_id in sorted(rows_by_id)}
    all_approved = actual_ids == _DECISION_IDS and all(status == "APPROVED" for status in statuses.values())
    any_rejected = any(status == "REJECTED" for status in statuses.values())
    if protocol_status == "ALL_ITEMS_APPROVED" and not all_approved:
        errors.append("receipt.protocol_decision_status: ALL_ITEMS_APPROVED requires D01-D12 all APPROVED")
    if protocol_status == "REJECTED" and not any_rejected:
        errors.append("receipt.protocol_decision_status: REJECTED requires at least one rejected decision")
    if protocol_status == "PENDING_ITEM_APPROVAL" and all_approved:
        errors.append("receipt.protocol_decision_status: all approved decisions require ALL_ITEMS_APPROVED")
    if protocol_status == "PENDING_ITEM_APPROVAL" and any_rejected:
        errors.append("receipt.protocol_decision_status: rejected decision requires REJECTED status")

    auth = receipt.get("pilot_start_authorization")
    if not isinstance(auth, Mapping):
        errors.append("receipt.pilot_start_authorization: expected an object")
        auth = {}
    else:
        _unknown_fields(auth, _AUTH_FIELDS, "receipt.pilot_start_authorization", errors)
    authorized = auth.get("authorized")
    if not isinstance(authorized, bool):
        errors.append("receipt.pilot_start_authorization.authorized: expected boolean")
    elif authorized:
        if not all_approved or protocol_status != "ALL_ITEMS_APPROVED":
            errors.append("receipt.pilot_start_authorization: start authorization requires all D01-D12 approved")
        _nonempty(auth.get("authorized_by_role"), "receipt.pilot_start_authorization.authorized_by_role", errors)
        _offset_datetime(auth.get("authorized_at"), "receipt.pilot_start_authorization.authorized_at", errors)
        _commit(auth.get("candidate_commit"), "receipt.pilot_start_authorization.candidate_commit", errors)
        _sha256(auth.get("package_sha256"), "receipt.pilot_start_authorization.package_sha256", errors)
        _sha256(auth.get("manifest_sha256"), "receipt.pilot_start_authorization.manifest_sha256", errors)
        _sha256(auth.get("protocol_sha256"), "receipt.pilot_start_authorization.protocol_sha256", errors)
        if pilot_status != "AUTHORIZED_NOT_STARTED":
            errors.append("receipt.pilot_status: authorized start requires AUTHORIZED_NOT_STARTED")
    elif authorized is False:
        for key in ("authorized_by_role", "authorized_at", "candidate_commit", "package_sha256", "manifest_sha256", "protocol_sha256"):
            if auth.get(key) is not None:
                errors.append(f"receipt.pilot_start_authorization.{key}: must be null when not authorized")
        expected_pilot_status = "READY_FOR_START_AUTHORIZATION" if all_approved and protocol_status == "ALL_ITEMS_APPROVED" else "NOT_STARTED"
        if pilot_status != expected_pilot_status:
            errors.append(f"receipt.pilot_status: expected {expected_pilot_status} while start is not authorized")

    return sorted(set(errors))


def pilot_start_allowed(receipt: Mapping[str, Any]) -> bool:
    if validate_decision_receipt(receipt):
        return False
    return (
        receipt.get("protocol_decision_status") == "ALL_ITEMS_APPROVED"
        and receipt.get("pilot_status") == "AUTHORIZED_NOT_STARTED"
        and receipt.get("pilot_start_authorization", {}).get("authorized") is True
    )
