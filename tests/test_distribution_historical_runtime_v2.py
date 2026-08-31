from unittest.mock import patch
import pytest
from engine.distribution.errors import DistributionError
from engine.distribution.runtime import _prepare_historical_calibration, _selected_historical_rows, _ziwei_historical_support
from engine.historical.selector import select_historical_activation, select_historical_activation_v2
from tests.test_historical_activation_selector import NATAL
from tests.test_historical_activation_selector_v2 import _v2_payload, _clean_month_diagnostics, _spike_month_diagnostics

def v1():
    return select_historical_activation({"normalized_natal":NATAL,"as_of_datetime":"2026-08-23T10:27:00+08:00","timezone":"Asia/Taipei"})
def v2_abstain():
    with patch("engine.historical.selector.build_month_activation_diagnostics", side_effect=_spike_month_diagnostics): return select_historical_activation_v2(_v2_payload())
def v2_selected():
    with patch("engine.historical.selector.build_month_activation_diagnostics", side_effect=_clean_month_diagnostics): return select_historical_activation_v2(_v2_payload())

def test_selected_rows_support_v2_abstain_without_fallback():
    assert len(_selected_historical_rows(v2_abstain())) == 4

def test_selected_rows_keep_five_for_v1_and_v2_selected():
    assert len(_selected_historical_rows(v1())) == 5
    assert len(_selected_historical_rows(v2_selected())) == 5

def test_ziwei_support_uses_actual_expected_selected_count():
    selector = v2_abstain()
    with patch(
        "engine.distribution.forecast.resolve_forecast_context",
        return_value={"ziwei": {"yearly": {"scope": "yearly", "reference": "synthetic"}}},
    ):
        result = _ziwei_historical_support(selector, _v2_payload())
    assert result["status"] == "available"
    assert len(result["years"]) == 4

def test_prepare_defaults_to_v1_and_routes_explicit_v2():
    default_payload={"normalized_natal":NATAL,"as_of_datetime":"2026-08-23T10:27:00+08:00","timezone":"Asia/Taipei"}
    assert _prepare_historical_calibration(default_payload)["profile_id"] == "historical-activation-bazi-v1"
    with patch("engine.historical.selector.build_month_activation_diagnostics", side_effect=_clean_month_diagnostics):
        explicit={**_v2_payload(),"selector_profile_id":"historical-activation-bazi-v2"}
        assert _prepare_historical_calibration(explicit)["profile_id"] == "historical-activation-bazi-v2"

def test_prepare_rejects_unknown_selector_profile():
    with pytest.raises(DistributionError) as exc:
        _prepare_historical_calibration({**_v2_payload(),"selector_profile_id":"unknown"})
    assert exc.value.code == "historical_selector_invalid"
