from __future__ import annotations

from typing import Mapping

from .control_eligibility import (
    ANNUAL_ROLES,
    V2_PROFILE_ID,
    V2_RULE_VERSION,
    evaluate_control_candidate,
)
from .models import ActivationRankVector
from .selector import PROFILE_ID, RULE_VERSION, _canonical_digest


_ALLOWED_COVERAGE = frozenset(("single_cycle", "cross_cycle", "boundary_in_window"))
_ALLOWED_CONTROL_QUALITY = frozenset(("strong_control", "acceptable_control", "relative_low"))
_ALLOWED_STRENGTH = frozenset(("strong", "moderate", "weak", "unspecified"))
_ALLOWED_LOCAL_STATUS = frozenset(("complete", "incomplete", "not_required"))
_ALLOWED_WINDOW_TYPE = frozenset(("local_spike", "active_window"))
_V2_SEMANTICS = "structural_comparison_only_not_quiet_year"


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError("%s must be a mapping" % field)
    return value


def _rank_vector(row: Mapping[str, object]) -> ActivationRankVector:
    raw = _mapping(row.get("rank_vector"), "rank_vector")
    try:
        return ActivationRankVector(**dict(raw))
    except (TypeError, ValueError) as exc:
        raise ValueError("selector rank_vector is invalid") from exc


def _control_quality(rank: ActivationRankVector) -> str:
    if rank.tier1_family_count > 0:
        return "relative_low"
    if rank.tier2_family_count > 0:
        return "acceptable_control"
    return "strong_control"


def verify_v1_selection_result(result: Mapping[str, object]) -> str:
    """Verify the immutable historical-activation-bazi-v1 contract."""
    if not isinstance(result, Mapping):
        raise ValueError("selector result must be a mapping")
    if result.get("profile_id") != PROFILE_ID or result.get("rule_version") != RULE_VERSION:
        raise ValueError("selector profile or rule version is not supported")

    as_of = result.get("as_of_datetime")
    timezone = result.get("timezone")
    if not isinstance(as_of, str) or not as_of.strip():
        raise ValueError("selector as_of_datetime is missing")
    if not isinstance(timezone, str) or not timezone.strip():
        raise ValueError("selector timezone is missing")

    ranked = result.get("ranked_periods")
    high = result.get("high_years")
    control = result.get("control_year")
    if not isinstance(ranked, (list, tuple)) or len(ranked) != 10:
        raise ValueError("selector ranked_periods must contain exactly ten rows")
    if not isinstance(high, (list, tuple)) or len(high) != 4:
        raise ValueError("selector high_years must contain exactly four rows")
    if not isinstance(control, Mapping):
        raise ValueError("selector control_year must be a mapping")

    rows = []
    labels = []
    for raw in ranked:
        row = _mapping(raw, "ranked_period")
        label = row.get("label_year")
        if not isinstance(label, int) or isinstance(label, bool):
            raise ValueError("selector label_year must be an integer")
        labels.append(label)
        rows.append(row)
    if len(set(labels)) != 10:
        raise ValueError("selector ranked_periods must contain ten unique label years")

    expected_ranked = sorted(
        rows,
        key=lambda row: _rank_vector(row).as_sort_key(int(row["label_year"])),
        reverse=True,
    )
    if rows != expected_ranked:
        raise ValueError("selector ranked_periods are not in canonical rank order")

    high_rows = [_mapping(row, "high_year") for row in high]
    if high_rows != rows[:4]:
        raise ValueError("selector high_years are not the canonical Top 4")
    if dict(control) != dict(rows[-1]):
        raise ValueError("selector control_year is not the canonical Bottom 1")

    control_quality = result.get("control_quality")
    if control_quality not in _ALLOWED_CONTROL_QUALITY:
        raise ValueError("selector control_quality is invalid")
    expected_quality = _control_quality(_rank_vector(rows[-1]))
    if control_quality != expected_quality:
        raise ValueError("selector control_quality does not match the control rank")

    coverage = result.get("major_cycle_coverage")
    if coverage not in _ALLOWED_COVERAGE:
        raise ValueError("selector major_cycle_coverage is invalid")

    canonical = {
        "profile_id": result["profile_id"],
        "rule_version": result["rule_version"],
        "as_of_datetime": as_of,
        "timezone": timezone,
        "ranked_periods": rows,
        "high_year_labels": [int(row["label_year"]) for row in high_rows],
        "control_year_label": int(control["label_year"]),
        "control_quality": control_quality,
        "major_cycle_coverage": coverage,
    }
    digest = _canonical_digest(canonical)
    if result.get("selection_digest") != digest:
        raise ValueError("selector selection_digest does not match serialized selection truth")
    return digest


def _v2_row_semantics(
    row: Mapping[str, object],
    *,
    top4: bool,
    next_higher_row: Mapping[str, object] | None = None,
) -> None:
    role = row.get("annual_role")
    if role not in ANNUAL_ROLES:
        raise ValueError("selector annual_role is invalid")
    eligible = row.get("annual_control_eligibility")
    if not isinstance(eligible, bool):
        raise ValueError("selector annual_control_eligibility must be boolean")
    reasons = row.get("control_rejection_reasons")
    if not isinstance(reasons, (list, tuple)) or any(not isinstance(item, str) for item in reasons):
        raise ValueError("selector control_rejection_reasons must be text list")
    strength = row.get("annual_strength_class")
    if strength not in _ALLOWED_STRENGTH:
        raise ValueError("selector annual_strength_class is invalid")
    local_status = row.get("local_window_status")
    if local_status not in _ALLOWED_LOCAL_STATUS:
        raise ValueError("selector local_window_status is invalid")
    windows = row.get("local_windows")
    if not isinstance(windows, (list, tuple)):
        raise ValueError("selector local_windows must be a list")
    window_rows = [_mapping(item, "local_window") for item in windows]
    window_types = [item.get("window_type") for item in window_rows]
    if any(item not in _ALLOWED_WINDOW_TYPE for item in window_types):
        raise ValueError("selector local window type is invalid")
    has_spike = "local_spike" in window_types

    if top4:
        if role != "sustained_high" or eligible:
            raise ValueError("selector Top 4 row semantics are invalid")
        if list(reasons) != ["top4_high_activation"]:
            raise ValueError("selector Top 4 rejection reason is invalid")
        if local_status != "not_required" or window_rows:
            raise ValueError("selector Top 4 local-window state is invalid")
        return

    if local_status == "not_required":
        raise ValueError("selector non-Top4 row requires local-window evaluation")
    expected = evaluate_control_candidate(
        annual_row=row,
        next_higher_row=next_higher_row,
        local_windows=window_rows,
        coverage_complete=local_status == "complete",
    )
    if eligible != expected["control_eligible"]:
        raise ValueError("selector control eligibility does not match serialized evidence")
    if list(reasons) != expected["control_rejection_reasons"]:
        raise ValueError("selector control rejection reasons do not match serialized evidence")
    if strength != expected["annual_strength_class"]:
        raise ValueError("selector annual strength does not match rank vector")
    expected_role = expected["annual_role"]
    if expected["control_eligible"]:
        if role not in ("true_control", "relative_low"):
            raise ValueError("selector eligible control semantics are invalid")
    elif role != expected_role:
        raise ValueError("selector rejected annual role does not match serialized evidence")


def verify_v2_selection_result(result: Mapping[str, object]) -> str:
    """Verify the optional-control historical-activation-bazi-v2 contract."""
    if not isinstance(result, Mapping):
        raise ValueError("selector result must be a mapping")
    if result.get("profile_id") != V2_PROFILE_ID or result.get("rule_version") != V2_RULE_VERSION:
        raise ValueError("selector profile or rule version is not supported")

    as_of = result.get("as_of_datetime")
    timezone = result.get("timezone")
    if not isinstance(as_of, str) or not as_of.strip():
        raise ValueError("selector as_of_datetime is missing")
    if not isinstance(timezone, str) or not timezone.strip():
        raise ValueError("selector timezone is missing")

    ranked = result.get("ranked_periods")
    high = result.get("high_years")
    if not isinstance(ranked, (list, tuple)) or len(ranked) != 10:
        raise ValueError("selector ranked_periods must contain exactly ten rows")
    if not isinstance(high, (list, tuple)) or len(high) != 4:
        raise ValueError("selector high_years must contain exactly four rows")

    rows = []
    labels = []
    for raw in ranked:
        row = _mapping(raw, "ranked_period")
        label = row.get("label_year")
        if not isinstance(label, int) or isinstance(label, bool):
            raise ValueError("selector label_year must be an integer")
        labels.append(label)
        rows.append(row)
    if len(set(labels)) != 10:
        raise ValueError("selector ranked_periods must contain ten unique label years")

    expected_ranked = sorted(
        rows,
        key=lambda row: _rank_vector(row).as_sort_key(int(row["label_year"])),
        reverse=True,
    )
    if rows != expected_ranked:
        raise ValueError("selector ranked_periods are not in canonical rank order")

    high_rows = [_mapping(row, "high_year") for row in high]
    if high_rows != rows[:4]:
        raise ValueError("selector high_years are not the canonical Top 4")

    for index, row in enumerate(rows):
        _v2_row_semantics(
            row,
            top4=index < 4,
            next_higher_row=None if index == 0 else rows[index - 1],
        )

    coverage = result.get("major_cycle_coverage")
    if coverage not in _ALLOWED_COVERAGE:
        raise ValueError("selector major_cycle_coverage is invalid")
    semantics = result.get("control_quality_semantics")
    if semantics != _V2_SEMANTICS:
        raise ValueError("selector control_quality_semantics is invalid")

    control_selection = result.get("control_selection")
    control_quality = result.get("control_quality")
    control = result.get("control_year")
    true_controls = [row for row in rows[4:] if row.get("annual_role") == "true_control"]
    eligible_indexes = [
        index for index in range(4, len(rows))
        if rows[index].get("annual_control_eligibility") is True
    ]

    if control_selection == "selected":
        if control_quality != "true_control" or not isinstance(control, Mapping):
            raise ValueError("selector selected control contract is invalid")
        if len(true_controls) != 1:
            raise ValueError("selector must contain exactly one true_control row")
        selected_row = true_controls[0]
        if dict(control) != dict(selected_row):
            raise ValueError("selector control_year does not match true_control row")
        if not eligible_indexes or rows[eligible_indexes[-1]] != selected_row:
            raise ValueError("selector control_year is not the lowest-ranked eligible row")
        if selected_row.get("control_rejection_reasons"):
            raise ValueError("selector true_control row cannot have rejection reasons")
    elif control_selection == "abstain":
        if control_quality != "no_clean_control" or control is not None:
            raise ValueError("selector abstention contract is invalid")
        if true_controls or eligible_indexes:
            raise ValueError("selector abstention cannot hide an eligible fallback control")
    else:
        raise ValueError("selector control_selection is invalid")

    canonical = {
        "profile_id": result["profile_id"],
        "rule_version": result["rule_version"],
        "as_of_datetime": as_of,
        "timezone": timezone,
        "ranked_periods": rows,
        "high_year_labels": [int(row["label_year"]) for row in high_rows],
        "control_year_label": None if control is None else int(control["label_year"]),
        "control_selection": control_selection,
        "control_quality": control_quality,
        "control_quality_semantics": semantics,
        "major_cycle_coverage": coverage,
    }
    digest = _canonical_digest(canonical)
    if result.get("selection_digest") != digest:
        raise ValueError("selector selection_digest does not match serialized selection truth")
    return digest


def verify_selection_result(result: Mapping[str, object]) -> str:
    if not isinstance(result, Mapping):
        raise ValueError("selector result must be a mapping")
    profile_id = result.get("profile_id")
    rule_version = result.get("rule_version")
    if profile_id == PROFILE_ID and rule_version == RULE_VERSION:
        return verify_v1_selection_result(result)
    if profile_id == V2_PROFILE_ID and rule_version == V2_RULE_VERSION:
        return verify_v2_selection_result(result)
    raise ValueError("selector profile or rule version is not supported")
