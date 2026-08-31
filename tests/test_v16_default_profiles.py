import json
from pathlib import Path

from engine.distribution.capabilities import get_capability as get_distribution_capability
from engine.historical.capabilities import get_capability as get_historical_capability

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "qualification" / "interpretation" / "v1.6" / "summary.json"


def _summary():
    return json.loads(SUMMARY.read_text(encoding="utf-8"))


def _release_behavior_gate_passed():
    summary = _summary()
    interpretation = summary["interpretation"]
    selector = summary["selector"]
    return all((
        summary["status"] == "PASS",
        summary["cutoff_contamination_count"] == 0,
        interpretation["v2_false_positive_count"] <= interpretation["v1_false_positive_count"],
        interpretation["v2_domain"]["missed"] <= interpretation["v1_domain"]["missed"],
        interpretation["v2_event_family"]["missed"] <= interpretation["v1_event_family"]["missed"] + 1,
        selector["v1_control_false_negative_count"] >= 1
        and (selector["v2_not_true_control_count"] >= 1 or selector["v2_abstention_count"] >= 1),
    ))


def test_private_aggregate_pass_does_not_bypass_failed_release_behavior_gate():
    summary = _summary()
    assert summary["status"] == "PASS"
    assert summary["promotion_allowed"] is False
    assert _release_behavior_gate_passed() is False

    selector = get_historical_capability("historical.activation_selector")
    interpretation = get_distribution_capability("distribution.interpretation_contract")
    assert selector["profile_id"] == "historical-activation-bazi-v1"
    assert selector["rule_version"] == "1.0-exp"
    assert interpretation["rule_version"] == "lin_tianji_interpretation_contract_v1-exp"
