import json
import subprocess
import sys
from pathlib import Path

from tools.run_v16_acceptance import SCENARIOS, run_acceptance

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = ROOT / "tests" / "fixtures" / "v1.6-acceptance.expected.v1.json"
RUNNER = ROOT / "tools" / "run_v16_acceptance.py"


def test_expected_fixture_contains_exactly_ac01_through_ac10_once():
    payload = json.loads(EXPECTED.read_text(encoding="utf-8"))
    ids = payload["scenario_ids"]
    assert ids == list(SCENARIOS)
    assert len(ids) == 10
    assert len(set(ids)) == 10
    assert payload["required_status"] == "PASS"


def test_all_v16_acceptance_scenarios_pass():
    report = run_acceptance()
    assert report["schema_version"] == "v1.6-acceptance-report.v1"
    assert report["scenario_count"] == 10
    assert report["all_pass"] is True
    assert [row["scenario_id"] for row in report["scenarios"]] == list(SCENARIOS)
    assert all(row["status"] == "PASS" for row in report["scenarios"])
    assert len(report["report_digest"]) == 64


def test_every_scenario_has_named_boolean_assertions():
    report = run_acceptance()
    for row in report["scenarios"]:
        assert row["assertions"]
        for assertion in row["assertions"]:
            assert set(assertion) == {"name", "passed"}
            assert isinstance(assertion["name"], str) and assertion["name"]
            assert assertion["passed"] is True


def test_cli_is_byte_deterministic():
    first = subprocess.check_output([sys.executable, str(RUNNER)], cwd=ROOT)
    second = subprocess.check_output([sys.executable, str(RUNNER)], cwd=ROOT)
    assert first == second
    parsed = json.loads(first.decode("utf-8"))
    assert parsed["all_pass"] is True
