import copy
from unittest.mock import patch

from engine.historical.models import ActivationRankVector
from engine.historical.selector import (
    build_month_activation_diagnostics,
    completed_flow_year_periods,
    flow_month_periods_for_year,
)
from engine.historical.control_eligibility import (
    evaluate_control_candidate,
    has_structural_separation,
    historical_strength_class,
)


def row(rank, *, decadal_boundary=False):
    return {
        "label_year": 2020,
        "decadal_boundary_in_period": decadal_boundary,
        "rank_vector": rank.to_dict(),
    }


def evaluate(annual_row, *, next_higher=None, local_windows=(), coverage_complete=True):
    return evaluate_control_candidate(
        annual_row=annual_row,
        next_higher_row=next_higher,
        local_windows=local_windows,
        coverage_complete=coverage_complete,
    )


def test_historical_strength_class_uses_tier_density():
    assert historical_strength_class(ActivationRankVector(1,1,False,0,0,0,0)) == "strong"
    assert historical_strength_class(ActivationRankVector(0,0,False,3,4,0,0)) == "strong"
    assert historical_strength_class(ActivationRankVector(0,0,False,2,2,0,0)) == "moderate"
    assert historical_strength_class(ActivationRankVector(0,0,False,0,0,1,1)) == "weak"
    assert historical_strength_class(ActivationRankVector(0,0,False,0,0,0,0)) == "unspecified"


def test_tier1_or_too_many_tier2_families_reject_control():
    tier1_row = row(ActivationRankVector(1,1,False,0,0,0,0))
    dense_tier2_row = row(ActivationRankVector(0,0,False,3,3,0,0))
    assert "annual_tier_ceiling" in evaluate(tier1_row)["control_rejection_reasons"]
    assert "annual_tier_ceiling" in evaluate(dense_tier2_row)["control_rejection_reasons"]


def test_tier3_or_label_year_only_difference_is_not_control_separation():
    low = ActivationRankVector(0,0,False,1,1,0,0)
    near = ActivationRankVector(0,0,False,1,1,4,8)
    assert has_structural_separation(low, near) is False


def test_tier2_difference_establishes_control_separation():
    low = ActivationRankVector(0,0,False,0,0,1,1)
    near = ActivationRankVector(0,0,False,1,1,0,0)
    assert has_structural_separation(low, near) is True


def _synthetic_bazi():
    return {
        "pillars": {
            "year": "庚子",
            "month": "甲申",
            "day": "丙午",
            "hour": "戊辰",
        },
        "decadal_periods": [
            {
                "index": 4,
                "pillar": "庚子",
                "start_datetime": "2015-06-01T00:00:00+08:00",
                "end_datetime": "2025-06-01T00:00:00+08:00",
            },
            {
                "index": 5,
                "pillar": "辛丑",
                "start_datetime": "2025-06-01T00:00:00+08:00",
                "end_datetime": "2035-06-01T00:00:00+08:00",
            },
        ],
    }


def _weak_annual_row():
    annual = dict(completed_flow_year_periods(
        "2026-08-23T10:27:00+08:00", "Asia/Taipei", 10
    )[0])
    annual.update({
        "decadal_boundary_in_period": False,
        "rank_vector": ActivationRankVector(0,0,False,0,0,1,1).to_dict(),
    })
    return annual


def test_flow_month_periods_cover_lichun_to_next_lichun_exactly():
    annual = completed_flow_year_periods(
        "2026-08-23T10:27:00+08:00", "Asia/Taipei", 10
    )[0]
    months = flow_month_periods_for_year(annual, "Asia/Taipei")
    assert len(months) == 12
    assert months[0]["period_start"] == annual["period_start"]
    assert months[-1]["period_end"] == annual["period_end"]


def test_ac01_strong_child_month_marks_local_spike_without_rewriting_parent_rank():
    annual = _weak_annual_row()
    original_rank = copy.deepcopy(annual["rank_vector"])
    bazi = _synthetic_bazi()
    diagnostics = build_month_activation_diagnostics(
        annual_row=annual,
        natal_pillars=bazi["pillars"],
        bazi=bazi,
        timezone="Asia/Taipei",
    )
    assert diagnostics["coverage_complete"] is True
    assert any(window["window_type"] == "local_spike" for window in diagnostics["local_windows"])
    assert annual["rank_vector"] == original_rank


def test_month_boundary_failure_marks_coverage_incomplete_and_rejects_true_control():
    annual = _weak_annual_row()
    bazi = _synthetic_bazi()
    from engine.historical import selector as selector_module
    original = selector_module.solar_term_time

    def fail_one_boundary(year, term, tz="Asia/Taipei"):
        if term == "驚蟄":
            raise ValueError("synthetic boundary failure")
        return original(year, term, tz)

    with patch("engine.historical.selector.solar_term_time", side_effect=fail_one_boundary):
        diagnostics = build_month_activation_diagnostics(
            annual_row=annual,
            natal_pillars=bazi["pillars"],
            bazi=bazi,
            timezone="Asia/Taipei",
        )
    assert diagnostics["coverage_complete"] is False
    result = evaluate(
        annual,
        next_higher=row(ActivationRankVector(0,0,False,1,1,0,0)),
        local_windows=diagnostics["local_windows"],
        coverage_complete=diagnostics["coverage_complete"],
    )
    assert result["control_eligible"] is False
    assert result["annual_role"] == "uncertain"
