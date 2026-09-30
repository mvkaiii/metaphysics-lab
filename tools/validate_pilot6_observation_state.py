"""Validate Pilot-6's post-lock observation lifecycle without exposing private lock material."""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

_EXPECTED_CANDIDATE = "6cb37e8b6f1ef1c9638008e9a7757ec757d20161"
_EXPECTED_PARENT_HEAD = "0da9062be73ac035a2ddc2238671ef95b825e92b"
_EXPECTED_TZ = "Asia/Taipei"
_EXPECTED_START = "2027-09-01T00:00:00+08:00"
_EXPECTED_END = "2027-10-31T23:59:59+08:00"
_EXPECTED_MATURITY = "2027-11-03T23:59:59+08:00"


def _aware_iso(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    if dt.tzinfo is None or dt.utcoffset() is None:
        return None
    return dt


def validate_pilot6_observation_state(payload):
    errors = []
    if not isinstance(payload, Mapping):
        return ["observation: expected object"]
    if payload.get("schema_version") != "1.0":
        errors.append("observation.schema_version")
    if payload.get("pilot_id") != "Pilot-6":
        errors.append("observation.pilot_id")
    if payload.get("lifecycle_state") != "OBSERVATION_PENDING":
        errors.append("observation.lifecycle_state")
    if payload.get("prediction_side_status") != "PREDICTION_LOCKED":
        errors.append("observation.prediction_side_status")
    if payload.get("prediction_side_evidence_class") != "OWNER_REPORTED_EXTERNAL_PRIVATE_EXECUTION":
        errors.append("observation.prediction_side_evidence_class")
    if payload.get("artifact_integrity_review_status") != "NOT_PERFORMED_IN_PUBLIC_GOVERNANCE_CONTEXT":
        errors.append("observation.artifact_integrity_review_status")
    if payload.get("frozen_candidate_commit") != _EXPECTED_CANDIDATE:
        errors.append("observation.frozen_candidate_commit")
    if payload.get("public_governance_parent_head") != _EXPECTED_PARENT_HEAD:
        errors.append("observation.public_governance_parent_head")

    window = payload.get("outcome_window")
    if not isinstance(window, Mapping):
        errors.append("observation.outcome_window")
        window = {}
    if window.get("timezone") != _EXPECTED_TZ:
        errors.append("observation.outcome_window.timezone")
    if window.get("start") != _EXPECTED_START:
        errors.append("observation.outcome_window.start")
    if window.get("end") != _EXPECTED_END:
        errors.append("observation.outcome_window.end")
    if window.get("maturity_delay_hours") != 72:
        errors.append("observation.outcome_window.maturity_delay_hours")
    if window.get("earliest_post_window_maturity_at") != _EXPECTED_MATURITY:
        errors.append("observation.outcome_window.earliest_post_window_maturity_at")

    start = _aware_iso(window.get("start"))
    end = _aware_iso(window.get("end"))
    maturity = _aware_iso(window.get("earliest_post_window_maturity_at"))
    if start is None or end is None or maturity is None:
        errors.append("observation.outcome_window.datetime")
    elif not (start < end < maturity):
        errors.append("observation.outcome_window.order")

    state = payload.get("execution_state")
    if not isinstance(state, Mapping):
        errors.append("observation.execution_state")
        state = {}
    for key in ("outcome_collection", "adjudication", "scoring"):
        if state.get(key) != "NOT_STARTED":
            errors.append(f"observation.execution_state.{key}")

    permissions = payload.get("permissions")
    if not isinstance(permissions, Mapping):
        errors.append("observation.permissions")
        permissions = {}
    expected_permissions = {
        "engineering_development_continuation_allowed": True,
        "frozen_candidate_mutation_allowed": False,
        "replacement_case_allowed": False,
        "retrospective_prediction_repair_allowed": False,
        "pilot_capability_stable_promotion_allowed": False,
    }
    if set(permissions) != set(expected_permissions):
        errors.append("observation.permissions.fields")
    for key, expected in expected_permissions.items():
        if permissions.get(key) is not expected:
            errors.append(f"observation.permissions.{key}")

    gates = payload.get("gates")
    if not isinstance(gates, Mapping):
        errors.append("observation.gates")
        gates = {}
    expected_gates = {
        "outcome_collection": "ONLY_WHILE_APPROVED_WINDOW_OPEN",
        "adjudication": "NOT_BEFORE_WINDOW_END_PLUS_MATURITY_DELAY",
        "scoring": "NOT_BEFORE_WINDOW_END_PLUS_MATURITY_DELAY",
    }
    if dict(gates) != expected_gates:
        errors.append("observation.gates")

    privacy = payload.get("privacy")
    if not isinstance(privacy, Mapping):
        errors.append("observation.privacy")
        privacy = {}
    required_privacy = {
        "private_case_identity_disclosed",
        "private_prediction_lock_digest_disclosed",
        "private_execution_artifact_digest_disclosed",
        "private_prediction_content_disclosed",
        "private_outcome_content_disclosed",
    }
    if set(privacy) != required_privacy:
        errors.append("observation.privacy.fields")
    for key in required_privacy:
        if privacy.get(key) is not False:
            errors.append(f"observation.privacy.{key}")

    if payload.get("next_engineering_action") != "CONTINUE_V1_8_ENGINEERING_WITH_PILOT6_FROZEN_AND_OBSERVATION_PENDING":
        errors.append("observation.next_engineering_action")
    return sorted(set(errors))


def engineering_development_allowed(payload) -> bool:
    return (
        not validate_pilot6_observation_state(payload)
        and payload["permissions"]["engineering_development_continuation_allowed"] is True
        and payload["permissions"]["frozen_candidate_mutation_allowed"] is False
    )


def outcome_collection_window_open(payload, when: datetime) -> bool:
    if validate_pilot6_observation_state(payload):
        return False
    if when.tzinfo is None or when.utcoffset() is None:
        return False
    start = datetime.fromisoformat(payload["outcome_window"]["start"])
    end = datetime.fromisoformat(payload["outcome_window"]["end"])
    return start <= when <= end


def adjudication_allowed_at(payload, when: datetime) -> bool:
    if validate_pilot6_observation_state(payload):
        return False
    if when.tzinfo is None or when.utcoffset() is None:
        return False
    maturity = datetime.fromisoformat(payload["outcome_window"]["earliest_post_window_maturity_at"])
    return when >= maturity
