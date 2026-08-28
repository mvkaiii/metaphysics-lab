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

_REQUIRED_FIELDS = frozenset(
    {
        "locked_forecast",
        "claim_id",
        "verification_state",
        "observed_actual",
        "evaluated_at",
    }
)
_OPTIONAL_FIELDS = frozenset({"notes"})
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

    The caller supplies the verification state.  This function deliberately
    does not parse ``matched_if``, ``not_matched_if`` or ``observed_actual``
    to infer a different outcome.
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
    }
    if "notes" in payload:
        evaluation["notes"] = _text(payload.get("notes"), "notes")

    return {
        "status": "evaluated",
        "locked_forecast_digest": locked["canonical_digest"],
        "claim": claim,
        "evaluation": evaluation,
    }
