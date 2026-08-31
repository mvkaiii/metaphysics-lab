from engine.historical.models import ActivationRankVector
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
