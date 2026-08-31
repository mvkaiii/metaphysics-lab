from __future__ import annotations

from typing import Mapping, Sequence

from .models import ActivationRankVector

V2_PROFILE_ID = "historical-activation-bazi-v2"
V2_RULE_VERSION = "2.0-exp"
ANNUAL_ROLES = (
    "sustained_high",
    "localized_spike",
    "relative_low",
    "true_control",
    "uncertain",
)


def historical_strength_class(rank: ActivationRankVector) -> str:
    if not isinstance(rank, ActivationRankVector):
        raise ValueError("rank must be an ActivationRankVector")
    if rank.tier1_family_count > 0 or rank.tier2_family_count >= 3:
        return "strong"
    if rank.tier2_family_count in (1, 2):
        return "moderate"
    if rank.tier3_family_count > 0:
        return "weak"
    return "unspecified"


def structural_control_signature(rank: ActivationRankVector) -> tuple[int, int, int, int]:
    if not isinstance(rank, ActivationRankVector):
        raise ValueError("rank must be an ActivationRankVector")
    return (
        rank.tier1_family_count,
        rank.tier1_evidence_count,
        rank.tier2_family_count,
        rank.tier2_evidence_count,
    )


def has_structural_separation(
    candidate: ActivationRankVector,
    next_higher: ActivationRankVector | None,
) -> bool:
    if not isinstance(candidate, ActivationRankVector):
        raise ValueError("candidate must be an ActivationRankVector")
    if next_higher is None:
        return False
    if not isinstance(next_higher, ActivationRankVector):
        raise ValueError("next_higher must be an ActivationRankVector or None")
    return structural_control_signature(candidate) < structural_control_signature(next_higher)


def _rank_from_row(row: Mapping[str, object], field: str) -> ActivationRankVector:
    raw = row.get("rank_vector")
    if not isinstance(raw, Mapping):
        raise ValueError("%s.rank_vector must be a mapping" % field)
    try:
        return ActivationRankVector(**dict(raw))
    except (TypeError, ValueError) as exc:
        raise ValueError("%s.rank_vector is invalid" % field) from exc


def evaluate_control_candidate(
    *,
    annual_row: Mapping[str, object],
    next_higher_row: Mapping[str, object] | None,
    local_windows: Sequence[Mapping[str, object]],
    coverage_complete: bool,
) -> dict:
    if not isinstance(annual_row, Mapping):
        raise ValueError("annual_row must be a mapping")
    if next_higher_row is not None and not isinstance(next_higher_row, Mapping):
        raise ValueError("next_higher_row must be a mapping or None")
    if not isinstance(local_windows, (list, tuple)):
        raise ValueError("local_windows must be a sequence")
    if not isinstance(coverage_complete, bool):
        raise ValueError("coverage_complete must be bool")

    annual_rank = _rank_from_row(annual_row, "annual_row")
    next_higher_rank = None if next_higher_row is None else _rank_from_row(next_higher_row, "next_higher_row")
    strength = historical_strength_class(annual_rank)
    separated = has_structural_separation(annual_rank, next_higher_rank)

    reasons = []
    if annual_rank.tier1_family_count > 0 or annual_rank.tier2_family_count > 2:
        reasons.append("annual_tier_ceiling")
    if bool(annual_row.get("decadal_boundary_in_period", False)):
        reasons.append("decadal_boundary")
    if not coverage_complete:
        reasons.append("incomplete_local_coverage")
    has_local_spike = any(
        isinstance(window, Mapping) and window.get("window_type") == "local_spike"
        for window in local_windows
    )
    if has_local_spike:
        reasons.append("local_spike")
    if not separated:
        reasons.append("insufficient_separation")

    eligible = not reasons
    if not coverage_complete:
        annual_role = "uncertain"
    elif has_local_spike:
        annual_role = "localized_spike"
    elif eligible:
        annual_role = "true_control"
    else:
        annual_role = "relative_low"

    return {
        "control_eligible": eligible,
        "annual_role": annual_role,
        "control_rejection_reasons": reasons,
        "annual_strength_class": strength,
        "structural_separation": separated,
    }
