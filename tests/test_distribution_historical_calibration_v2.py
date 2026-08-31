from unittest.mock import patch
import pytest
from engine.distribution.calibration import lock_historical_calibration
from engine.distribution.errors import DistributionError
from engine.historical.selector import select_historical_activation, select_historical_activation_v2
from tests.test_historical_activation_selector import NATAL
from tests.test_historical_activation_selector_v2 import _v2_payload, _clean_month_diagnostics, _spike_month_diagnostics

def point(year, role="high_activation"):
    return {"reference_year":year,"role":role,"primary_domains":["工作／職責"],"event_family":["角色結構改變"],"confidence":"medium","interpretation_text":f"{year} structural test","blindness_status":"blind"}

def v1_result():
    return select_historical_activation({"normalized_natal":NATAL,"as_of_datetime":"2026-08-23T10:27:00+08:00","timezone":"Asia/Taipei"})

def v2_abstain():
    with patch("engine.historical.selector.build_month_activation_diagnostics", side_effect=_spike_month_diagnostics):
        return select_historical_activation_v2(_v2_payload())

def v2_selected():
    with patch("engine.historical.selector.build_month_activation_diagnostics", side_effect=_clean_month_diagnostics):
        return select_historical_activation_v2(_v2_payload())

def lock(selector, points):
    return lock_historical_calibration({"calibration_id":"HC-V2-001","subject_id":"case-001","selector_result":selector,"canonical_test_points":points,"supplemental_blind_points":[],"locked_at":"2026-08-31T12:00:00+08:00"})

def test_v2_abstain_accepts_exactly_four_canonical_points():
    selector=v2_abstain(); points=[point(r["label_year"]) for r in selector["high_years"]]
    locked=lock(selector, points)
    assert len(locked["locked_payload"]["canonical_test_points"]) == 4

def test_v2_abstain_rejects_synthetic_fallback_control():
    selector=v2_abstain(); points=[point(r["label_year"]) for r in selector["high_years"]] + [point(selector["ranked_periods"][-1]["label_year"],"control")]
    with pytest.raises(DistributionError) as exc:
        lock(selector, points)
    assert exc.value.code == "selector_binding_mismatch"

def test_v2_selected_keeps_five_points():
    selector=v2_selected(); points=[point(r["label_year"]) for r in selector["high_years"]] + [point(selector["control_year"]["label_year"],"control")]
    locked=lock(selector, points)
    assert len(locked["locked_payload"]["canonical_test_points"]) == 5

def test_v1_keeps_exactly_five_points():
    selector=v1_result(); points=[point(r["label_year"]) for r in selector["high_years"]] + [point(selector["control_year"]["label_year"],"control")]
    locked=lock(selector, points)
    assert len(locked["locked_payload"]["canonical_test_points"]) == 5
