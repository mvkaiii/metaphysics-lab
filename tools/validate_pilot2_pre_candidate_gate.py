"""Validate Pilot-2's fail-closed pre-candidate sequencing gate.

This validator handles public/de-identified governance state only. It does not
read case data, source records, private digests, predictions, or outcomes.
"""

from __future__ import annotations

import re
from typing import Any, Mapping


_TOP_FIELDS = {
    "schema_version",
    "pilot_id",
    "gate_profile",
    "gate_status",
    "prerequisites",
    "public_bindings",
    "candidate_case_processing_allowed",
    "private_material_disclosed",
    "manual_override_allowed",
}
_PREREQUISITES = (
    "protocol_decisions_approved",
    "start_authorization_bound",
    "source_census_frozen",
    "intake_registry_valid",
    "intake_eligible_for_s1",
    "s1_source_manifest_frozen",
    "s1_candidate_exposure_unexposed",
    "s1_manifest_predates_candidate_processing",
)
_BINDINGS = {
    "candidate_commit",
    "package_sha256",
    "manifest_sha256",
    "protocol_sha256",
    "window_policy_digest",
}
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40,64}$")


def _unknown_fields(value, allowed, path, errors):
    for key in sorted(set(value) - set(allowed)):
        errors.append(f"{path}: unknown field {key!r}")


def _is_bool(value, path, errors):
    if not isinstance(value, bool):
        errors.append(f"{path}: expected boolean")
        return False
    return True


def _valid_sha(value):
    return isinstance(value, str) and _SHA256.fullmatch(value) is not None


def _valid_commit(value):
    return isinstance(value, str) and _COMMIT.fullmatch(value) is not None


def validate_pilot2_pre_candidate_gate(payload: Mapping[str, Any]) -> list[str]:
    errors = []
    if not isinstance(payload, Mapping):
        return ["gate: expected an object"]

    _unknown_fields(payload, _TOP_FIELDS, "gate", errors)
    for key in sorted(_TOP_FIELDS):
        if key not in payload:
            errors.append(f"gate: missing field {key}")

    if payload.get("schema_version") != "1.0":
        errors.append("gate.schema_version: expected '1.0'")
    if payload.get("pilot_id") != "Pilot-2":
        errors.append("gate.pilot_id: expected 'Pilot-2'")
    if payload.get("gate_profile") != "pilot2_pre_candidate_gate_v1":
        errors.append(
            "gate.gate_profile: expected 'pilot2_pre_candidate_gate_v1'"
        )

    status = payload.get("gate_status")
    if status not in {"BLOCKED", "READY"}:
        errors.append("gate.gate_status: expected BLOCKED or READY")

    prerequisites = payload.get("prerequisites")
    prerequisite_values = {}
    if not isinstance(prerequisites, Mapping):
        errors.append("gate.prerequisites: expected an object")
    else:
        _unknown_fields(
            prerequisites,
            set(_PREREQUISITES),
            "gate.prerequisites",
            errors,
        )
        for key in _PREREQUISITES:
            if key not in prerequisites:
                errors.append(f"gate.prerequisites: missing field {key}")
                prerequisite_values[key] = False
            else:
                value = prerequisites.get(key)
                _is_bool(value, f"gate.prerequisites.{key}", errors)
                prerequisite_values[key] = value is True

        # Prerequisites are a chronological chain. A later stage cannot be true
        # while an earlier stage is false.
        seen_false = False
        for key in _PREREQUISITES:
            value = prerequisite_values.get(key, False)
            if not value:
                seen_false = True
            elif seen_false:
                errors.append(
                    f"gate.prerequisites.{key}: sequencing violation; "
                    "an earlier prerequisite is false"
                )

    bindings = payload.get("public_bindings")
    if not isinstance(bindings, Mapping):
        errors.append("gate.public_bindings: expected an object")
        bindings = {}
    else:
        _unknown_fields(bindings, _BINDINGS, "gate.public_bindings", errors)
        for key in sorted(_BINDINGS):
            if key not in bindings:
                errors.append(f"gate.public_bindings: missing field {key}")

    processing = payload.get("candidate_case_processing_allowed")
    processing_is_bool = _is_bool(
        processing,
        "gate.candidate_case_processing_allowed",
        errors,
    )
    private_disclosed = payload.get("private_material_disclosed")
    _is_bool(private_disclosed, "gate.private_material_disclosed", errors)
    manual_override = payload.get("manual_override_allowed")
    _is_bool(manual_override, "gate.manual_override_allowed", errors)

    if private_disclosed is not False:
        errors.append(
            "gate.private_material_disclosed: public gate must keep private "
            "material undisclosed"
        )
    if manual_override is not False:
        errors.append(
            "gate.manual_override_allowed: Pilot-2 pre-candidate gate has no "
            "manual override"
        )

    start_bound = prerequisite_values.get("start_authorization_bound", False)
    if start_bound:
        if not _valid_commit(bindings.get("candidate_commit")):
            errors.append(
                "gate.public_bindings.candidate_commit: start authorization "
                "requires a lowercase 40-64 hex commit"
            )
        for key in (
            "package_sha256",
            "manifest_sha256",
            "protocol_sha256",
            "window_policy_digest",
        ):
            if not _valid_sha(bindings.get(key)):
                errors.append(
                    f"gate.public_bindings.{key}: start authorization requires "
                    "a lowercase SHA256"
                )
    else:
        for key in sorted(_BINDINGS):
            if bindings.get(key) is not None:
                errors.append(
                    f"gate.public_bindings.{key}: must be null before start "
                    "authorization is bound"
                )

    all_ready = bool(prerequisite_values) and all(
        prerequisite_values.get(key, False) for key in _PREREQUISITES
    )

    if all_ready:
        if status != "READY":
            errors.append(
                "gate.gate_status: all prerequisites require READY status"
            )
        if processing is not True:
            errors.append(
                "gate.candidate_case_processing_allowed: all prerequisites "
                "require true"
            )
    else:
        if status == "READY":
            errors.append(
                "gate.gate_status: READY requires every prerequisite true"
            )
        if processing_is_bool and processing is not False:
            errors.append(
                "gate.candidate_case_processing_allowed: must remain false "
                "until every prerequisite is true"
            )

    return sorted(set(errors))


def candidate_case_processing_allowed(payload: Mapping[str, Any]) -> bool:
    if validate_pilot2_pre_candidate_gate(payload):
        return False
    return (
        payload.get("gate_status") == "READY"
        and payload.get("candidate_case_processing_allowed") is True
        and payload.get("manual_override_allowed") is False
        and payload.get("private_material_disclosed") is False
        and all(
            payload.get("prerequisites", {}).get(key) is True
            for key in _PREREQUISITES
        )
    )
