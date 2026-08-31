import json
from pathlib import Path

from engine.distribution.capabilities import get_capability as get_distribution_capability
from engine.historical.capabilities import get_capability as get_historical_capability

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "qualification" / "interpretation" / "v1.6" / "summary.json"


def _qualification_passed():
    return json.loads(SUMMARY.read_text(encoding="utf-8"))["status"] == "PASS"


def test_pending_private_qualification_blocks_default_profile_promotion():
    assert _qualification_passed() is False
    selector = get_historical_capability("historical.activation_selector")
    interpretation = get_distribution_capability("distribution.interpretation_contract")
    assert selector["profile_id"] == "historical-activation-bazi-v1"
    assert selector["rule_version"] == "1.0-exp"
    assert interpretation["rule_version"] == "lin_tianji_interpretation_contract_v1-exp"
