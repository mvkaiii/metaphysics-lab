from __future__ import annotations

from typing import Mapping

from .models import ActivationRankVector
from .selector import PROFILE_ID, RULE_VERSION, _canonical_digest


_ALLOWED_COVERAGE = frozenset(("single_cycle", "cross_cycle", "boundary_in_window"))
_ALLOWED_CONTROL_QUALITY = frozenset(("strong_control", "acceptable_control", "relative_low"))


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


def verify_selection_result(result: Mapping[str, object]) -> str:
    """Verify a serialized selector result before it can enter calibration.

    This does not recalculate natal evidence. It verifies that the serialized
    deterministic selector output is internally self-consistent: the ten rows
    are in canonical rank order, the selected High/Control rows are the true
    Top4/Bottom1 of that ranking, control quality matches the bottom row, and
    the stored selection digest still matches the serialized selection truth.
    """
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
