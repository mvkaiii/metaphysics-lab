import copy
from unittest.mock import patch

import pytest

from engine.historical.selection_integrity import verify_selection_result
from engine.historical.selector import _canonical_digest, select_historical_activation, select_historical_activation_v2
from tests.test_historical_activation_selector import NATAL
from tests.test_historical_activation_selector_v2 import (
    _clean_month_diagnostics,
    _spike_month_diagnostics,
    _v2_payload,
)


def _v1_result():
    return select_historical_activation({
        "normalized_natal": NATAL,
        "as_of_datetime": "2026-08-23T10:27:00+08:00",
        "timezone": "Asia/Taipei",
    })


def _v2_selected():
    with patch(
        "engine.historical.selector.build_month_activation_diagnostics",
        side_effect=_clean_month_diagnostics,
    ):
        return select_historical_activation_v2(_v2_payload())


def _v2_abstain():
    with patch(
        "engine.historical.selector.build_month_activation_diagnostics",
        side_effect=_spike_month_diagnostics,
    ):
        return select_historical_activation_v2(_v2_payload())


def _refresh_v2_digest(result):
    control = result["control_year"]
    canonical = {
        "profile_id": result["profile_id"],
        "rule_version": result["rule_version"],
        "as_of_datetime": result["as_of_datetime"],
        "timezone": result["timezone"],
        "ranked_periods": result["ranked_periods"],
        "high_year_labels": [item["label_year"] for item in result["high_years"]],
        "control_year_label": None if control is None else control["label_year"],
        "control_selection": result["control_selection"],
        "control_quality": result["control_quality"],
        "control_quality_semantics": result["control_quality_semantics"],
        "major_cycle_coverage": result["major_cycle_coverage"],
    }
    result["selection_digest"] = _canonical_digest(canonical)


def test_v1_routing_still_returns_legacy_digest():
    result = _v1_result()
    assert verify_selection_result(result) == result["selection_digest"]
    assert result["selection_digest"] == "756163f490440dbb51243c5bcba638c5029cff7045fc1bdc0e92f97eeae79ddd"


def test_v2_selected_control_verifies():
    result = _v2_selected()
    assert verify_selection_result(result) == result["selection_digest"]


def test_v2_abstain_verifies_without_fallback_control():
    result = _v2_abstain()
    assert result["control_year"] is None
    assert verify_selection_result(result) == result["selection_digest"]


@pytest.mark.parametrize("mutation", ["annual_role", "local_window", "reasons", "control_selection"])
def test_v2_semantic_tampering_fails_closed_even_with_refreshed_digest(mutation):
    result = copy.deepcopy(_v2_selected())
    control = result["control_year"]
    assert control is not None
    label = control["label_year"]
    row = next(item for item in result["ranked_periods"] if item["label_year"] == label)
    if mutation == "annual_role":
        row["annual_role"] = "relative_low"
    elif mutation == "local_window":
        row["local_windows"] = [{"window_type": "local_spike"}]
    elif mutation == "reasons":
        row["control_rejection_reasons"] = ["local_spike"]
    elif mutation == "control_selection":
        result["control_selection"] = "abstain"
    _refresh_v2_digest(result)
    with pytest.raises(ValueError):
        verify_selection_result(result)


def test_v2_digest_tampering_fails_closed():
    result = _v2_selected()
    result["selection_digest"] = "0" * 64
    with pytest.raises(ValueError):
        verify_selection_result(result)
