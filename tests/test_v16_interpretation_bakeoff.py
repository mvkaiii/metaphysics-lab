import copy
import json
from pathlib import Path

import pytest

from engine.distribution.bakeoff import evaluate_bakeoff, validate_bakeoff_fixture

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "v1.6-interpretation-bakeoff.synthetic.v1.json"


def load_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_schema_rejects_missing_variant_id():
    payload = load_fixture()
    payload["cases"][0]["variants"] = payload["cases"][0]["variants"][:-1]
    with pytest.raises(ValueError, match="V0.*V4|variant"):
        validate_bakeoff_fixture(payload)


def test_schema_rejects_duplicate_case_and_claim_ids():
    payload = load_fixture()
    payload["cases"][1]["case_id"] = payload["cases"][0]["case_id"]
    with pytest.raises(ValueError, match="case_id"):
        validate_bakeoff_fixture(payload)

    payload = load_fixture()
    payload["cases"][0]["variants"][1]["claims"][0]["claim_id"] = payload["cases"][0]["variants"][0]["claims"][0]["claim_id"]
    with pytest.raises(ValueError, match="claim_id"):
        validate_bakeoff_fixture(payload)


def test_schema_rejects_unsupported_specificity_naive_datetimes_and_private_fields():
    payload = load_fixture()
    payload["cases"][0]["variants"][0]["claims"][0]["specificity"] = "hyper_specific"
    with pytest.raises(ValueError, match="specificity"):
        validate_bakeoff_fixture(payload)

    payload = load_fixture()
    payload["cases"][0]["knowledge_cutoff_at"] = "2025-12-31T23:59:59"
    with pytest.raises(ValueError, match="offset-aware"):
        validate_bakeoff_fixture(payload)

    for forbidden in ("actual_event", "birth_date", "subject_name"):
        payload = load_fixture()
        payload["cases"][0][forbidden] = "private"
        with pytest.raises(ValueError, match="forbidden|unknown"):
            validate_bakeoff_fixture(payload)


def test_bakeoff_report_keeps_metric_groups_separate():
    report = evaluate_bakeoff(load_fixture())
    variant = report["variants"]["V0"]
    assert set(variant) >= {
        "structural_outcome_alignment",
        "honesty_safety",
        "explanation_ux",
    }
    assert "overall_accuracy" not in variant
    assert "total_score" not in variant


def test_alignment_rules_cover_match_miss_unscorable_and_specificity():
    report = evaluate_bakeoff(load_fixture())
    v0 = report["variants"]["V0"]["structural_outcome_alignment"]
    assert v0["domain_match"]["matched"] >= 1
    assert v0["domain_match"]["missed"] >= 1
    assert v0["event_family_match"]["unscorable"] >= 1
    assert v0["timing_match"]["matched"] >= 1
    assert v0["specificity_appropriateness"]["pass"] >= 1


def test_honesty_rules_count_false_positive_unsupported_inference_and_abstention_quality():
    report = evaluate_bakeoff(load_fixture())
    v0 = report["variants"]["V0"]["honesty_safety"]
    assert v0["false_positive_count"] >= 1
    assert v0["unsupported_inference_count"] >= 1
    assert v0["method_leakage_count"] >= 1
    assert v0["abstention_quality"]["appropriate"] >= 1


def test_ux_only_machine_scores_traceability():
    report = evaluate_bakeoff(load_fixture())
    ux = report["variants"]["V0"]["explanation_ux"]
    assert set(ux) == {"reasoning_traceability", "readability", "actionability"}
    assert ux["readability"] == "externally_adjudicated"
    assert ux["actionability"] == "externally_adjudicated"
    assert set(ux["reasoning_traceability"]) == {"traceable", "not_traceable"}

from engine.distribution.bakeoff import validate_v4_cutoff
from engine.distribution.errors import DistributionError


def test_v4_record_after_cutoff_fails_closed():
    payload = load_fixture()
    case = payload["cases"][0]
    case["knowledge_cutoff_at"] = "2020-12-31T23:59:59+08:00"
    case["variants"][4]["personalization_records"] = [{
        "record_id": "POST",
        "knowledge_available_at": "2021-01-01T00:00:00+08:00",
        "domain": "career",
        "event_family": "role_change",
        "evaluation": "matched",
    }]
    with pytest.raises(DistributionError, match="cutoff") as exc:
        evaluate_bakeoff(payload)
    assert exc.value.code == "bakeoff_cutoff_contamination"
    assert "POST" in exc.value.details["record_ids"]


def test_v4_record_exactly_at_cutoff_is_allowed():
    records = [{
        "record_id": "AT",
        "knowledge_available_at": "2020-12-31T23:59:59+08:00",
        "domain": "career",
        "event_family": "role_change",
        "evaluation": "matched",
    }]
    result = validate_v4_cutoff(records, "2020-12-31T23:59:59+08:00")
    assert result[0]["record_id"] == "AT"


def test_non_v4_variants_reject_personalization_records():
    payload = load_fixture()
    payload["cases"][0]["variants"][0]["personalization_records"] = [{
        "record_id": "NOPE",
        "knowledge_available_at": "2020-01-01T00:00:00+08:00",
        "domain": "career",
        "event_family": "role_change",
        "evaluation": "matched",
    }]
    with pytest.raises(DistributionError, match="V0.*personalization|personalization.*V0"):
        evaluate_bakeoff(payload)


def test_timing_abstention_is_appropriate_without_timing_evidence_and_over_abstained_with_it():
    payload = load_fixture()
    claim = payload["cases"][0]["variants"][0]["claims"][0]
    claim["abstentions"] = ["abstain_timing"]
    claim["evidence_ids"] = ["E-BZ-1"]
    first = evaluate_bakeoff(payload)["variants"]["V0"]["honesty_safety"]["abstention_quality"]
    assert first["appropriate"] >= 1

    claim["evidence_ids"] = ["E-BZ-1", "E-TIME-1"]
    second = evaluate_bakeoff(payload)["variants"]["V0"]["honesty_safety"]["abstention_quality"]
    assert second["over_abstained"] >= 1

import subprocess
import sys


def test_cli_output_is_byte_identical_and_contains_digests():
    command = [
        sys.executable,
        str(ROOT / "tools" / "evaluate_v16_interpretation_bakeoff.py"),
        "--fixture",
        str(FIXTURE),
    ]
    first = subprocess.run(command, cwd=ROOT, check=True, capture_output=True).stdout
    second = subprocess.run(command, cwd=ROOT, check=True, capture_output=True).stdout
    assert first == second
    report = json.loads(first.decode("utf-8"))
    assert report["classification"] == "synthetic_validation"
    assert report["case_count"] == 5
    assert report["variant_ids"] == ["V0", "V1", "V2", "V3", "V4"]
    assert len(report["fixture_sha256"]) == 64
    assert len(report["report_sha256"]) == 64


def test_method_doc_states_limits_and_metric_contract():
    text = (ROOT / "docs" / "research" / "v1.6-interpretation-bakeoff-method.md").read_text(encoding="utf-8")
    lowered = text.lower()
    assert "retrospective" in lowered
    assert "prospective accuracy" in lowered
    assert "no live llm" in lowered
    assert "ux" in lowered and "outcome accuracy" in lowered
    assert "per-target cutoff" in lowered
    assert "misses" in lowered and "abstentions" in lowered
    for variant in ("V0", "V1", "V2", "V3", "V4"):
        assert variant in text
