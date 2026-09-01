#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.distribution.bakeoff import validate_v4_cutoff
from engine.distribution.claim_evidence import abstentions_for_packet, classify_cross_system_relation
from engine.distribution.errors import DistributionError
from engine.distribution.evidence_models import EvidenceFeature
from engine.historical.control_eligibility import evaluate_control_candidate
from engine.historical.models import ActivationRankVector
from engine.historical.selector import select_historical_activation, select_historical_activation_v2

SCENARIOS = (
    "AC-01", "AC-02", "AC-03", "AC-04", "AC-05",
    "AC-06", "AC-07", "AC-08", "AC-09", "AC-10",
)
REPORT_SCHEMA_VERSION = "v1.6-acceptance-report.v1"
V1_FROZEN_DIGEST = "756163f490440dbb51243c5bcba638c5029cff7045fc1bdc0e92f97eeae79ddd"

NATAL = {
    "validation": {"blocking_conflict_count": 0},
    "project": {
        "birth": {"timezone": "Asia/Taipei"},
        "bazi": {
            "pillars": {"year": "庚子", "month": "甲申", "day": "丙午", "hour": "戊辰"},
            "day_master": "丙",
            "decadal_periods": [
                {"index": 3, "pillar": "己亥", "start_datetime": "2005-06-01T00:00:00+08:00", "end_datetime": "2015-06-01T00:00:00+08:00"},
                {"index": 4, "pillar": "庚子", "start_datetime": "2015-06-01T00:00:00+08:00", "end_datetime": "2025-06-01T00:00:00+08:00"},
                {"index": 5, "pillar": "辛丑", "start_datetime": "2025-06-01T00:00:00+08:00", "end_datetime": "2035-06-01T00:00:00+08:00"},
            ],
        },
    },
}
SELECTOR_PAYLOAD = {
    "normalized_natal": NATAL,
    "as_of_datetime": "2026-08-23T10:27:00+08:00",
    "timezone": "Asia/Taipei",
}


def _canonical_digest(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _assertion(name: str, passed: bool) -> dict:
    return {"name": name, "passed": bool(passed)}


def _scenario(scenario_id: str, assertions: list[dict]) -> dict:
    return {
        "scenario_id": scenario_id,
        "status": "PASS" if assertions and all(item["passed"] for item in assertions) else "FAIL",
        "assertions": assertions,
    }


def _rank_row(rank: ActivationRankVector) -> dict:
    return {"label_year": 2020, "decadal_boundary_in_period": False, "rank_vector": rank.to_dict()}


def _feature(feature_id: str, *, system: str, domain: str, role: str = "target_evidence", scope: str = "yearly") -> EvidenceFeature:
    return EvidenceFeature(
        feature_id=feature_id,
        system=system,
        scope=scope,
        reference_window={"label": "synthetic-v1.6-acceptance"},
        primary_domain=domain,
        event_family_support=("role_change",) if role == "target_evidence" else (),
        strength_class="strong",
        maturity="stable",
        qualification_status="qualified",
        source_family="synthetic",
        dependency_family=f"{system}:{scope}:{feature_id}",
        role=role,
        provenance={"fixture": "v1.6-acceptance", "feature": feature_id},
    )


def _selector_results() -> tuple[dict, dict, dict]:
    payload = copy.deepcopy(SELECTOR_PAYLOAD)
    v1 = select_historical_activation(copy.deepcopy(payload))
    frozen_v1 = copy.deepcopy(v1)
    v2 = select_historical_activation_v2(copy.deepcopy(payload))
    return v1, frozen_v1, v2


def run_acceptance() -> dict:
    scenarios = []

    # AC-01: relative-low annual candidate with a strong local spike cannot be a control.
    ac01 = evaluate_control_candidate(
        annual_row=_rank_row(ActivationRankVector(0, 0, False, 0, 0, 1, 1)),
        next_higher_row=_rank_row(ActivationRankVector(0, 0, False, 1, 1, 0, 0)),
        local_windows=[{"window_type": "local_spike"}],
        coverage_complete=True,
    )
    scenarios.append(_scenario("AC-01", [
        _assertion("annual_role_is_localized_spike", ac01["annual_role"] == "localized_spike"),
        _assertion("localized_spike_is_not_control_eligible", ac01["control_eligible"] is False),
        _assertion("local_spike_reason_is_preserved", "local_spike" in ac01["control_rejection_reasons"]),
    ]))

    # AC-02: high activation without event-family localization must abstain at event-family level.
    ac02_abstentions = abstentions_for_packet(
        effective_specificity="domain",
        event_family_candidates=[],
        has_local_window=False,
        cross_system_relation=None,
    )
    scenarios.append(_scenario("AC-02", [
        _assertion("event_family_abstention_required", "abstain_event_family" in ac02_abstentions),
        _assertion("concrete_event_abstention_required", "abstain_concrete_event" in ac02_abstentions),
    ]))

    # AC-03: a structurally separated clean candidate qualifies as true control.
    ac03 = evaluate_control_candidate(
        annual_row=_rank_row(ActivationRankVector(0, 0, False, 1, 1, 0, 0)),
        next_higher_row=_rank_row(ActivationRankVector(0, 0, False, 2, 2, 0, 0)),
        local_windows=[],
        coverage_complete=True,
    )
    scenarios.append(_scenario("AC-03", [
        _assertion("clean_candidate_is_true_control", ac03["annual_role"] == "true_control"),
        _assertion("clean_candidate_is_control_eligible", ac03["control_eligible"] is True),
        _assertion("clean_candidate_has_no_rejection_reason", ac03["control_rejection_reasons"] == []),
    ]))

    v1, frozen_v1, v2 = _selector_results()

    # AC-04: the real v2 selector abstains when no low candidate passes the control gate.
    scenarios.append(_scenario("AC-04", [
        _assertion("selector_abstains_without_clean_control", v2["control_selection"] == "abstain"),
        _assertion("abstention_has_no_control_year", v2["control_year"] is None),
        _assertion("abstention_reports_no_clean_control", v2["control_quality"] == "no_clean_control"),
        _assertion("no_ranked_period_is_true_control", not any(row.get("annual_role") == "true_control" for row in v2["ranked_periods"])),
    ]))

    # AC-05: independent Bazi + Ziwei target evidence converges on the same domain.
    ac05_features = [_feature("b-career", system="bazi", domain="career"), _feature("z-career", system="ziwei", domain="career")]
    ac05_relation, ac05_conflicts = classify_cross_system_relation(
        packet_domain="career", selected_features=ac05_features, all_selected_features=ac05_features, target_scope="yearly"
    )
    scenarios.append(_scenario("AC-05", [
        _assertion("cross_system_relation_is_independent_convergence", ac05_relation == "independent_convergence"),
        _assertion("convergence_has_no_conflict", ac05_conflicts == []),
    ]))

    # AC-06: target evidence in one system + modifier in the other is layered complement.
    ac06_features = [
        _feature("b-career", system="bazi", domain="career"),
        _feature("z-career-mod", system="ziwei", domain="career", role="modifier", scope="decadal"),
    ]
    ac06_relation, ac06_conflicts = classify_cross_system_relation(
        packet_domain="career", selected_features=ac06_features, all_selected_features=ac06_features, target_scope="yearly"
    )
    scenarios.append(_scenario("AC-06", [
        _assertion("cross_system_relation_is_layered_complement", ac06_relation == "layered_complement"),
        _assertion("layered_complement_has_no_conflict", ac06_conflicts == []),
    ]))

    # AC-07: disjoint Bazi / Ziwei target domains preserve the conflict rather than resolving it.
    ac07_features = [_feature("b-fin", system="bazi", domain="finance"), _feature("z-career", system="ziwei", domain="career")]
    ac07_relation, ac07_conflicts = classify_cross_system_relation(
        packet_domain="finance", selected_features=[ac07_features[0]], all_selected_features=ac07_features, target_scope="yearly"
    )
    conflict = ac07_conflicts[0] if ac07_conflicts else {}
    scenarios.append(_scenario("AC-07", [
        _assertion("cross_system_relation_preserves_divergence", ac07_relation == "conflict_or_divergence"),
        _assertion("bazi_conflict_domain_is_preserved", conflict.get("bazi_target_domains") == ["finance"]),
        _assertion("ziwei_conflict_domain_is_preserved", conflict.get("ziwei_target_domains") == ["career"]),
    ]))

    # AC-08: event-family evidence cannot silently escalate to a concrete event.
    ac08_abstentions = abstentions_for_packet(
        effective_specificity="event_family",
        event_family_candidates=["role_change"],
        has_local_window=True,
        cross_system_relation="independent_convergence",
    )
    scenarios.append(_scenario("AC-08", [
        _assertion("event_family_is_not_over_abstained", "abstain_event_family" not in ac08_abstentions),
        _assertion("concrete_event_is_abstained", "abstain_concrete_event" in ac08_abstentions),
    ]))

    # AC-09: V4 post-cutoff personalization must fail closed.
    cutoff_failed_closed = False
    cutoff_error_code = None
    try:
        validate_v4_cutoff([
            {
                "record_id": "POST",
                "knowledge_available_at": "2021-01-01T00:00:00+08:00",
                "domain": "career",
                "event_family": "role_change",
                "evaluation": "matched",
            }
        ], "2020-12-31T23:59:59+08:00")
    except DistributionError as exc:
        cutoff_failed_closed = True
        cutoff_error_code = exc.code
    scenarios.append(_scenario("AC-09", [
        _assertion("post_cutoff_record_fails_closed", cutoff_failed_closed),
        _assertion("cutoff_error_code_is_specific", cutoff_error_code == "bakeoff_cutoff_contamination"),
    ]))

    # AC-10: running v2 separately must not mutate or change the frozen v1 result/digest.
    scenarios.append(_scenario("AC-10", [
        _assertion("v1_digest_matches_frozen_fixture", v1["selection_digest"] == V1_FROZEN_DIGEST),
        _assertion("v1_object_unchanged_after_v2_run", v1 == frozen_v1),
        _assertion("v1_digest_unchanged_after_v2_run", frozen_v1["selection_digest"] == V1_FROZEN_DIGEST),
        _assertion("v1_and_v2_profiles_are_distinct", v1["profile_id"] != v2["profile_id"]),
    ]))

    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "scenario_count": len(scenarios),
        "scenarios": scenarios,
        "all_pass": len(scenarios) == len(SCENARIOS) and all(row["status"] == "PASS" for row in scenarios),
    }
    report["report_digest"] = _canonical_digest(report)
    return report


def main() -> None:
    print(json.dumps(run_acceptance(), ensure_ascii=False, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
