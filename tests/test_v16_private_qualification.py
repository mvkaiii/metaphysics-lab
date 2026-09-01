import copy
import json
import pathlib
import re
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from build_v16_interpretation_qualification import aggregate_private_qualification


def case(case_id="opaque-1", *, contaminated=False, v2_selection="abstain"):
    return {
        "case_id": case_id,
        "selector_v1": {"control_result": "false_negative"},
        "selector_v2": {
            "annual_role": "localized_spike",
            "control_eligible": False,
            "control_selection": v2_selection,
        },
        "interpretation_v1": {
            "domain_result": "missed",
            "event_family_result": "missed",
            "false_positive": True,
            "abstained": False,
        },
        "interpretation_v2": {
            "domain_result": "matched",
            "event_family_result": "partial",
            "false_positive": False,
            "abstained": True,
        },
        "cutoff_contamination": contaminated,
        "input_digest": "a" * 64,
    }


def payload(*cases):
    return {
        "schema_version": "v1.6-private-qualification-input.v1",
        "cases": list(cases),
    }


def test_rejects_unknown_private_fields_instead_of_ignoring_them():
    raw = payload(case())
    raw["cases"][0]["subject_name"] = "PRIVATE NAME"
    raw["cases"][0]["birth_date"] = "1980-01-01"
    raw["cases"][0]["actual_event"] = "PRIVATE EVENT TEXT"
    with pytest.raises(ValueError, match="unknown fields"):
        aggregate_private_qualification(raw)


def test_public_report_is_aggregate_only():
    raw = payload(case("opaque-super-secret"))
    report = aggregate_private_qualification(raw)
    serialized = json.dumps(report, ensure_ascii=False, sort_keys=True)
    assert "opaque-super-secret" not in serialized
    assert "case_id" not in serialized
    assert "birth_date" not in serialized
    assert "actual_event" not in serialized
    assert "subject_name" not in serialized
    assert set(report) == {
        "schema_version", "status", "case_count", "selector", "interpretation",
        "cutoff_contamination_count", "input_set_digest", "summary_digest",
        "promotion_allowed",
    }


def test_any_cutoff_contamination_fails_closed():
    report = aggregate_private_qualification(payload(case(contaminated=True)))
    assert report["status"] == "FAIL"
    assert report["cutoff_contamination_count"] == 1


def test_qualification_never_promotes_capability_maturity():
    report = aggregate_private_qualification(payload(case()))
    assert report["promotion_allowed"] is False


def test_counts_selector_and_interpretation_fields():
    first = case("one")
    second = copy.deepcopy(case("two", v2_selection="selected"))
    second["selector_v1"]["control_result"] = "not_false_negative"
    second["selector_v2"]["annual_role"] = "true_control"
    second["selector_v2"]["control_eligible"] = True
    second["interpretation_v1"] = {
        "domain_result": "matched",
        "event_family_result": "partial",
        "false_positive": False,
        "abstained": False,
    }
    second["interpretation_v2"] = {
        "domain_result": "partial",
        "event_family_result": "missed",
        "false_positive": True,
        "abstained": False,
    }
    second["input_digest"] = "b" * 64

    report = aggregate_private_qualification(payload(first, second))
    assert report["status"] == "PASS"
    assert report["case_count"] == 2
    assert report["selector"] == {
        "v1_control_false_negative_count": 1,
        "v2_not_true_control_count": 1,
        "v2_true_control_count": 1,
        "v2_abstention_count": 1,
    }
    assert report["interpretation"]["v1_domain"] == {"matched": 1, "partial": 0, "missed": 1}
    assert report["interpretation"]["v2_domain"] == {"matched": 1, "partial": 1, "missed": 0}
    assert report["interpretation"]["v1_event_family"] == {"matched": 0, "partial": 1, "missed": 1}
    assert report["interpretation"]["v2_event_family"] == {"matched": 0, "partial": 1, "missed": 1}
    assert report["interpretation"]["v1_false_positive_count"] == 1
    assert report["interpretation"]["v2_false_positive_count"] == 1
    assert report["interpretation"]["v2_abstention_count"] == 1


def test_digests_are_deterministic_across_case_order():
    first = case("one")
    first["input_digest"] = "1" * 64
    second = case("two")
    second["input_digest"] = "2" * 64
    a = aggregate_private_qualification(payload(first, second))
    b = aggregate_private_qualification(payload(second, first))
    assert a["input_set_digest"] == b["input_set_digest"]
    assert a["summary_digest"] == b["summary_digest"]
    assert re.fullmatch(r"[0-9a-f]{64}", a["input_set_digest"])
    assert re.fullmatch(r"[0-9a-f]{64}", a["summary_digest"])


def test_empty_real_qualification_input_is_rejected():
    with pytest.raises(ValueError, match="at least one case"):
        aggregate_private_qualification(payload())
