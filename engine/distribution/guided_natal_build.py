"""Deterministic state authority for guided natal construction.

The authority is intentionally stateless: callers resubmit the facts and artifacts
they currently hold. The runtime validates those inputs, derives the only legal next
step, and emits a digest over the resulting authority snapshot. Chat/session memory
is never treated as workflow truth.
"""

from __future__ import annotations

import hashlib
import json
from typing import Mapping, Optional

from engine.birth.input_resolution import resolve_birth_input
from engine.calendar.models import CalendarResolverException
from engine.calendar.timezone import enumerate_local_time_occurrences

from .case_pack import _normalized_model, validate_case
from .case_revision import PROJECT_CONTRACT_V13, natal_revision_id
from .errors import DistributionError
from .natal import resolved_location_from_payload
from .partial_case import _validate_envelope
from .subjects import _validate_subject_entry


PROFILE_ID = "guided-natal-build-v1"
RULE_VERSION = "1.0-exp"
_ALLOWED_FIELDS = frozenset((
    "birth",
    "resolved_location",
    "normalized_natal",
    "candidate_envelope",
    "subject",
    "case_files",
))
_ALLOWED_BIRTH_FIELDS = frozenset((
    "sex",
    "birth_date",
    "birth_place",
    "birth_time_precision",
    "birth_time",
    "birth_time_range",
    "calendar_kind",
))


def _canonical_bytes(value: object) -> bytes:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise DistributionError(
            "invalid_guided_natal_state",
            "guided natal state must contain only standard JSON values",
        ) from exc
    return encoded.encode("utf-8")


def _digest(prefix: str, value: object) -> str:
    return prefix + hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _mapping(value: object, field: str, *, optional: bool = False) -> Optional[Mapping[str, object]]:
    if optional and value is None:
        return None
    if not isinstance(value, Mapping):
        raise DistributionError(
            "invalid_guided_natal_state",
            "%s must be a structured mapping" % field,
            {"field": field},
        )
    return value


def _next(kind: str, action: Optional[str] = None, required_fields=()) -> dict:
    return {
        "kind": kind,
        "action": action,
        "required_fields": list(required_fields),
    }


def _precision_from_birth(birth: Mapping[str, object]) -> Optional[str]:
    explicit = birth.get("birth_time_precision")
    if explicit in ("exact", "bounded", "unknown_time"):
        return str(explicit)
    if birth.get("birth_time") not in (None, ""):
        return "exact"
    if birth.get("birth_time_range") not in (None, ""):
        return "bounded"
    return None


def _birth_basis_digest(birth: Mapping[str, object], location: Optional[Mapping[str, object]]) -> str:
    return _digest(
        "gbirth_",
        {
            "birth": dict(birth),
            "resolved_location": None if location is None else dict(location),
        },
    )


def _base_authority(birth_digest: str) -> dict:
    return {
        "birth_basis_digest": birth_digest,
        "natal_kind": None,
        "natal_revision_id": None,
        "subject_id": None,
        "subject_identity": None,
        "case_project_contract_version": None,
        "case_natal_revision_id": None,
        "base_case_digest": None,
    }


def _finalize(
    *,
    stage: str,
    precision: Optional[str],
    local_time_resolution: Optional[str],
    authority: Mapping[str, object],
    next_step: Mapping[str, object],
) -> dict:
    body = {
        "profile_id": PROFILE_ID,
        "rule_version": RULE_VERSION,
        "stage": stage,
        "birth_time_precision": precision,
        "local_time_resolution": local_time_resolution,
        "authority": dict(authority),
        "next": dict(next_step),
    }
    result = dict(body)
    result["state_digest"] = _digest("gstate_", body)
    return result


def _exact_local_resolution(
    birth: Mapping[str, object],
    timezone_name: str,
) -> str:
    civil = "%sT%s:00" % (birth["birth_date"], birth["birth_time"])
    try:
        occurrences = enumerate_local_time_occurrences(civil, timezone_name)
    except CalendarResolverException as exc:
        raise DistributionError(
            exc.code,
            "guided natal state could not resolve the exact local-time occurrence",
            dict(exc.details),
        ) from exc
    if not occurrences:
        return "nonexistent"
    if len(occurrences) == 1:
        return "unique"
    return "ambiguous_fold"


def _validate_normalized_basis(
    artifact: Mapping[str, object],
    birth: Mapping[str, object],
    location: Mapping[str, object],
) -> dict:
    chart = _normalized_model(artifact).to_dict()
    project = chart.get("project")
    if not isinstance(project, Mapping):
        raise DistributionError(
            "guided_natal_artifact_basis_mismatch",
            "guided exact natal artifact requires Project-native natal authority",
        )
    project_birth = project.get("birth")
    if not isinstance(project_birth, Mapping):
        raise DistributionError(
            "guided_natal_artifact_basis_mismatch",
            "guided exact natal artifact is missing Project birth authority",
        )

    reported = project_birth.get("reported_datetime")
    expected_prefix = "%sT%s" % (birth.get("birth_date"), birth.get("birth_time"))
    matches = (
        project_birth.get("sex") == birth.get("sex")
        and project_birth.get("place_label") == birth.get("birth_place")
        and project_birth.get("resolved_place_label") == location.get("canonical_name")
        and project_birth.get("timezone") == location.get("timezone")
        and isinstance(reported, str)
        and reported.startswith(expected_prefix)
    )
    if not matches:
        raise DistributionError(
            "guided_natal_artifact_basis_mismatch",
            "normalized natal artifact does not match the current guided birth/location basis",
        )
    return chart


def _validate_candidate_basis(
    artifact: Mapping[str, object],
    birth: Mapping[str, object],
    location: Mapping[str, object],
    precision: str,
) -> dict:
    envelope = _validate_envelope(artifact)
    if envelope.get("profile_id") != "natal-candidate-envelope-v2" or envelope.get("rule_version") != "2.0-exp":
        raise DistributionError(
            "guided_natal_candidate_profile_incompatible",
            "guided v1.9 natal state requires Candidate Envelope v2",
            {
                "profile_id": envelope.get("profile_id"),
                "rule_version": envelope.get("rule_version"),
            },
        )

    known = envelope.get("known_facts")
    if not isinstance(known, Mapping):
        raise DistributionError(
            "guided_natal_artifact_basis_mismatch",
            "candidate envelope is missing known birth facts",
        )
    matches = (
        envelope.get("natal_precision_state") == precision
        and known.get("sex") == birth.get("sex")
        and known.get("birth_date") == birth.get("birth_date")
        and known.get("birth_place") == birth.get("birth_place")
        and known.get("resolved_place_label") == location.get("canonical_name")
        and known.get("timezone") == location.get("timezone")
    )
    if precision == "exact":
        matches = matches and known.get("reported_birth_time") == birth.get("birth_time")
    elif precision == "bounded":
        matches = matches and list(known.get("reported_birth_time_range") or []) == list(birth.get("birth_time_range") or [])
    elif precision == "unknown_time":
        matches = matches and known.get("reported_birth_time") is None and known.get("reported_birth_time_range") is None

    if not matches:
        raise DistributionError(
            "guided_natal_artifact_basis_mismatch",
            "candidate envelope does not match the current guided birth/location basis",
        )
    return envelope


def build_guided_natal_state(payload: Mapping[str, object]) -> dict:
    """Validate one complete workflow snapshot and derive the legal next step."""

    payload = _mapping(payload, "payload")
    unknown = sorted(set(payload) - _ALLOWED_FIELDS)
    if unknown:
        raise DistributionError(
            "invalid_guided_natal_state",
            "guided natal state contains unknown top-level fields",
            {"unknown_fields": unknown},
        )

    birth = dict(_mapping(payload.get("birth", {}), "birth"))
    unknown_birth = sorted(set(birth) - _ALLOWED_BIRTH_FIELDS)
    if unknown_birth:
        raise DistributionError(
            "invalid_guided_natal_state",
            "guided natal birth basis contains unknown fields",
            {"unknown_birth_fields": unknown_birth},
        )

    resolution = resolve_birth_input(birth, target="ziwei_natal")
    precision = _precision_from_birth(birth)

    if not resolution.ok or resolution.input is None:
        if resolution.error_code == "missing_required_birth_field":
            authority = _base_authority(_birth_basis_digest(birth, None))
            return _finalize(
                stage="collect_birth_input",
                precision=precision,
                local_time_resolution=None,
                authority=authority,
                next_step=_next("user_input", required_fields=resolution.missing_fields),
            )
        raise DistributionError(
            resolution.error_code or "invalid_guided_natal_birth",
            "guided natal birth basis is invalid",
            {
                "missing_fields": list(resolution.missing_fields),
                "allowed_actions": list(resolution.allowed_actions),
            },
        )

    canonical_birth = resolution.input.to_dict()

    raw_location = payload.get("resolved_location")
    if raw_location is None:
        authority = _base_authority(_birth_basis_digest(canonical_birth, None))
        return _finalize(
            stage="resolve_location",
            precision=precision,
            local_time_resolution=None,
            authority=authority,
            next_step=_next("runtime_action", "birth.resolve_location"),
        )

    location_model = resolved_location_from_payload(raw_location)
    location = location_model.to_dict()
    birth_digest = _birth_basis_digest(canonical_birth, location)
    authority = _base_authority(birth_digest)

    local_time_resolution = None
    if precision == "exact":
        local_time_resolution = _exact_local_resolution(birth, location_model.timezone)
        if local_time_resolution == "nonexistent":
            return _finalize(
                stage="unsupported_local_time",
                precision=precision,
                local_time_resolution=local_time_resolution,
                authority=authority,
                next_step=_next("user_input", required_fields=("birth_time",)),
            )

    normalized_raw = payload.get("normalized_natal")
    candidate_raw = payload.get("candidate_envelope")
    if normalized_raw is not None and candidate_raw is not None:
        raise DistributionError(
            "invalid_guided_natal_state",
            "guided natal state accepts exactly one current natal artifact",
        )

    if normalized_raw is None and candidate_raw is None:
        if precision == "exact" and local_time_resolution == "unique":
            return _finalize(
                stage="build_exact_natal",
                precision=precision,
                local_time_resolution=local_time_resolution,
                authority=authority,
                next_step=_next("runtime_action", "build_natal"),
            )
        return _finalize(
            stage="build_candidate_envelope",
            precision=precision,
            local_time_resolution=local_time_resolution,
            authority=authority,
            next_step=_next("runtime_action", "natal.candidate_envelope"),
        )

    if normalized_raw is not None:
        if precision != "exact" or local_time_resolution != "unique":
            raise DistributionError(
                "guided_natal_artifact_basis_mismatch",
                "single normalized natal artifact is not authoritative for the current time domain",
            )
        normalized = _validate_normalized_basis(
            _mapping(normalized_raw, "normalized_natal"),
            birth,
            location,
        )
        natal_kind = "normalized_natal"
        natal_artifact = normalized
    else:
        candidate = _validate_candidate_basis(
            _mapping(candidate_raw, "candidate_envelope"),
            birth,
            location,
            str(precision),
        )
        if precision == "exact" and local_time_resolution != "ambiguous_fold":
            raise DistributionError(
                "guided_natal_artifact_basis_mismatch",
                "exact Candidate Envelope is authoritative only for an ambiguous local-time fold",
            )
        natal_kind = "candidate_envelope"
        natal_artifact = candidate

    revision = natal_revision_id(natal_kind, natal_artifact)
    authority["natal_kind"] = natal_kind
    authority["natal_revision_id"] = revision

    subject_raw = payload.get("subject")
    if subject_raw is None:
        return _finalize(
            stage="collect_subject_identity",
            precision=precision,
            local_time_resolution=local_time_resolution,
            authority=authority,
            next_step=_next("user_input", required_fields=("subject",)),
        )
    subject = _validate_subject_entry(subject_raw)
    identity_fields = (
        "subject_id",
        "subject_display_name",
        "subject_short_id",
        "filename_label",
    )
    subject_identity = {field: subject.get(field) for field in identity_fields}
    authority["subject_id"] = subject["subject_id"]
    authority["subject_identity"] = subject_identity

    case_files = payload.get("case_files")
    if case_files is None:
        return _finalize(
            stage="ready_case_export",
            precision=precision,
            local_time_resolution=local_time_resolution,
            authority=authority,
            next_step=_next("runtime_action", "export_case_markdown"),
        )

    case_validation = validate_case({"case_files": case_files})
    case_identity = case_validation.get("subject")
    actual_identity = (
        {field: case_identity.get(field) for field in identity_fields}
        if isinstance(case_identity, Mapping)
        else None
    )
    if actual_identity != subject_identity:
        raise DistributionError(
            "guided_natal_case_subject_mismatch",
            "Case authority identity does not match the current subject identity",
            {
                "subject": subject_identity,
                "case_subject": actual_identity,
            },
        )

    contract = case_validation.get("project_contract_version")
    authority["case_project_contract_version"] = contract

    if contract != PROJECT_CONTRACT_V13:
        return _finalize(
            stage="case_revision_upgrade_required",
            precision=precision,
            local_time_resolution=local_time_resolution,
            authority=authority,
            next_step=_next("runtime_action", "case.replace_natal_base"),
        )

    case_revision = case_validation.get("natal_revision_id")
    case_digest = case_validation.get("base_case_digest")
    authority["case_natal_revision_id"] = case_revision
    authority["base_case_digest"] = case_digest
    if case_revision != revision:
        raise DistributionError(
            "guided_natal_case_revision_mismatch",
            "Case natal revision does not match the current guided natal artifact",
            {
                "natal_revision_id": revision,
                "case_natal_revision_id": case_revision,
            },
        )

    return _finalize(
        stage="complete",
        precision=precision,
        local_time_resolution=local_time_resolution,
        authority=authority,
        next_step=_next("none"),
    )
