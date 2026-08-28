"""Append-only evaluation for locked prospective forecast claims.

Phase 6 consumes the immutable Phase 1 forecast lock.  It verifies the
original lock before attaching an explicit human-supplied outcome state.
It does not reinterpret matched/not-matched prose and does not rewrite the
prediction contract.
"""

from __future__ import annotations

import copy
from datetime import datetime
from typing import Mapping

from .errors import DistributionError
from .prospective import lock_prospective_forecast


VERIFICATION_STATES = frozenset({"matched", "partial", "not_matched", "cannot_recall"})
FAILURE_MODES = frozenset(
    {
        "ai_compliance_failure",
        "specification_ambiguity",
        "deterministic_or_algorithm_failure",
        "metaphysical_signal_failure",
    }
)
NO_FAILURE_MODE = "none"
_FAILURE_EVIDENCE_FIELDS = frozenset(
    {
        "rule_violation",
        "specification_ambiguity",
        "algorithm_mismatch",
        "signal_miss",
    }
)
_FAILURE_MODE_EVIDENCE_FIELD = {
    "ai_compliance_failure": "rule_violation",
    "specification_ambiguity": "specification_ambiguity",
    "deterministic_or_algorithm_failure": "algorithm_mismatch",
    "metaphysical_signal_failure": "signal_miss",
}

_REQUIRED_FIELDS = frozenset(
    {
        "locked_forecast",
        "claim_id",
        "verification_state",
        "observed_actual",
        "evaluated_at",
    }
)
_OPTIONAL_FIELDS = frozenset({"notes", "failure_mode", "failure_evidence"})
_LOCK_FIELDS = frozenset({"status", "method_version", "anchor", "claims", "canonical_digest"})


def _invalid(message: str, **details: object) -> DistributionError:
    return DistributionError("invalid_prospective_evaluation", message, details)


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _invalid(f"{field} must be non-blank text", field=field)
    return value.strip()


def _aware_iso(value: object, field: str) -> str:
    text = _text(value, field)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise _invalid(f"{field} must be an ISO datetime", field=field) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise _invalid(f"{field} must be timezone-aware", field=field)
    return parsed.isoformat()


def _empty_failure_evidence() -> dict:
    return {
        "rule_violation": False,
        "specification_ambiguity": False,
        "algorithm_mismatch": False,
        "signal_miss": False,
    }


def _failure_attribution(payload: Mapping[str, object], verification_state: str) -> tuple[str, dict]:
    raw_mode = payload.get("failure_mode", NO_FAILURE_MODE)
    failure_mode = _text(raw_mode, "failure_mode")
    if failure_mode != NO_FAILURE_MODE and failure_mode not in FAILURE_MODES:
        raise _invalid("unsupported failure_mode", failure_mode=failure_mode)

    raw_evidence = payload.get("failure_evidence")
    if raw_evidence is None:
        failure_evidence = _empty_failure_evidence()
    else:
        if not isinstance(raw_evidence, Mapping) or set(raw_evidence) != _FAILURE_EVIDENCE_FIELDS:
            raise _invalid(
                "failure_evidence fields do not match the fixed taxonomy",
                required_fields=sorted(_FAILURE_EVIDENCE_FIELDS),
            )
        if any(type(raw_evidence[field]) is not bool for field in _FAILURE_EVIDENCE_FIELDS):
            raise _invalid("failure_evidence values must be booleans")
        failure_evidence = {
            field: raw_evidence[field]
            for field in ("rule_violation", "specification_ambiguity", "algorithm_mismatch", "signal_miss")
        }

    if verification_state == "not_matched" and failure_mode == NO_FAILURE_MODE:
        raise _invalid("not_matched evaluation requires an explicit failure_mode")

    if failure_mode == NO_FAILURE_MODE:
        if any(failure_evidence.values()):
            raise _invalid("failure_evidence cannot identify a failure when failure_mode is none")
        return failure_mode, failure_evidence

    expected_field = _FAILURE_MODE_EVIDENCE_FIELD[failure_mode]
    true_fields = [field for field, value in failure_evidence.items() if value]
    if true_fields != [expected_field]:
        raise _invalid(
            "failure_evidence must identify exactly the selected failure_mode",
            failure_mode=failure_mode,
            expected_evidence_field=expected_field,
            true_evidence_fields=true_fields,
        )
    return failure_mode, failure_evidence


def _verified_locked_forecast(value: object) -> dict:
    if not isinstance(value, Mapping) or set(value) != _LOCK_FIELDS:
        raise _invalid("locked_forecast fields do not match the Phase 1 lock contract")
    if value.get("status") != "locked":
        raise _invalid("locked_forecast must have status locked")

    try:
        recomputed = lock_prospective_forecast(
            {
                "anchor": value.get("anchor"),
                "claims": value.get("claims"),
            }
        )
    except DistributionError as exc:
        raise _invalid("locked_forecast no longer validates against the Phase 1 contract") from exc

    if recomputed != dict(value):
        raise _invalid("locked_forecast digest or immutable prediction content does not match")
    return recomputed


def evaluate_locked_claim(payload: Mapping[str, object]) -> dict:
    """Verify one locked claim and append an explicit evaluation block.

    The caller supplies the verification state and, when a failure is
    identified, its explicit attribution.  This function deliberately does
    not parse ``matched_if``, ``not_matched_if`` or ``observed_actual`` to
    infer either outcome or failure mode.
    """
    if not isinstance(payload, Mapping):
        raise _invalid("prospective evaluation payload must be a mapping")

    keys = set(payload)
    missing = sorted(_REQUIRED_FIELDS - keys)
    unknown = sorted(keys - (_REQUIRED_FIELDS | _OPTIONAL_FIELDS))
    if missing or unknown:
        raise _invalid(
            "prospective evaluation fields do not match the fixed contract",
            missing_fields=missing,
            unknown_fields=unknown,
        )

    locked = _verified_locked_forecast(payload.get("locked_forecast"))
    claim_id = _text(payload.get("claim_id"), "claim_id")
    verification_state = _text(payload.get("verification_state"), "verification_state")
    if verification_state not in VERIFICATION_STATES:
        raise _invalid("unsupported verification_state", verification_state=verification_state)

    matches = [claim for claim in locked["claims"] if claim.get("claim_id") == claim_id]
    if len(matches) != 1:
        raise _invalid("claim_id must identify exactly one locked claim", claim_id=claim_id)
    claim = copy.deepcopy(matches[0])

    observed_actual = _text(payload.get("observed_actual"), "observed_actual")
    evaluated_at = _aware_iso(payload.get("evaluated_at"), "evaluated_at")
    failure_mode, failure_evidence = _failure_attribution(payload, verification_state)

    clean_eligible = (
        claim.get("contamination_state") == "clean_prospective"
        and claim.get("evaluation_eligibility") == "clean_scorable"
    )
    scorable = clean_eligible and verification_state != "cannot_recall"

    if verification_state == "cannot_recall":
        exclusion_reason = "cannot_recall"
    elif not clean_eligible:
        exclusion_reason = claim.get("evaluation_eligibility") or "excluded_from_clean_accuracy"
    else:
        exclusion_reason = None

    evaluation = {
        "verification_state": verification_state,
        "observed_actual": observed_actual,
        "evaluated_at": evaluated_at,
        "scorable": scorable,
        "score_exclusion_reason": exclusion_reason,
        "failure_mode": failure_mode,
        "failure_evidence": failure_evidence,
    }
    if "notes" in payload:
        evaluation["notes"] = _text(payload.get("notes"), "notes")

    return {
        "status": "evaluated",
        "locked_forecast_digest": locked["canonical_digest"],
        "claim": claim,
        "evaluation": evaluation,
    }
