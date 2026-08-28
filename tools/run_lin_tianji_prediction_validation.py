#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCENARIO_TESTS = {
    "C01-decadal-strong-yearly-weak": ("tests.test_distribution_evidence_ranker.EvidenceRankerTests.test_modifier_cannot_open_domain_without_target_scope_ownership", "lin_tianji_rank_v1-exp"),
    "C02-yearly-strong-monthly-weak": ("tests.test_distribution_evidence_ranker.EvidenceRankerTests.test_yearly_strong_monthly_same_direction_is_active_window_not_local_spike", "lin_tianji_rank_v1-exp"),
    "C03-yearly-weak-monthly-strong": ("tests.test_distribution_evidence_ranker.EvidenceRankerTests.test_yearly_weak_monthly_strong_is_local_spike_without_mutating_parent", "lin_tianji_rank_v1-exp"),
    "C04-experimental-day-hour-spike": ("tests.test_distribution_evidence_ranker.EvidenceRankerTests.test_day_only_spike_with_weak_parent_cannot_claim_major_event_specificity", "lin_tianji_rank_v1-exp"),
    "C05-correlated-ziwei-derivatives": ("tests.test_distribution_evidence_ranker.EvidenceRankerTests.test_same_dependency_family_does_not_stack_as_independent_votes", "lin_tianji_rank_v1-exp"),
    "C06-independent-bazi-ziwei-convergence": ("tests.test_distribution_evidence_ranker.EvidenceRankerTests.test_cross_system_convergence_raises_rank_without_bypassing_ownership", "lin_tianji_rank_v1-exp"),
    "C07-historical-repeated-support": ("tests.test_distribution_historical_personalization.HistoricalPersonalizationTests.test_two_exact_canonical_family_matches_prefer_existing_candidate_only", "lin_tianji_historical_personalization_v1-exp"),
    "C08-historical-unsupported-domain": ("tests.test_distribution_historical_personalization.HistoricalPersonalizationTests.test_history_cannot_create_domain_absent_from_base", "lin_tianji_historical_personalization_v1-exp"),
    "C09-known-before-cutoff-plan": ("tests.test_distribution_prospective.DistributionProspectiveClaimTests.test_known_before_lock_may_be_preserved_only_as_excluded_context", "lin_tianji_v1.5-exp"),
    "C10-algorithm-weight-request": ("tests.test_project_ux_contract.ProjectUXContractTests.test_phase5_disclosure_and_branding_boundary", "lin_tianji_interpretation_contract_v1-exp"),
    "C11-user-language-lexical-audit": ("tests.test_project_ux_contract.ProjectUXContractTests.test_user_facing_prose_uses_taiwan_traditional_chinese_without_unnecessary_english", "lin_tianji_interpretation_contract_v1-exp"),
    "C12-progressive-case-stage1-isolation": ("tests.test_lin_tianji_prediction_validation_progressive.PredictionValidationProgressiveIsolationTests.test_05_and_06_materialized_but_stage1_reads_base_only", "blind-source-v1.1"),
}


def _digest(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _run_test(test_id):
    suite = unittest.defaultTestLoader.loadTestsFromName(test_id)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=0).run(suite)
    status = "PASS" if result.wasSuccessful() and result.testsRun == 1 else "FAIL"
    summary = {
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
    }
    if status == "FAIL":
        summary["detail"] = stream.getvalue()[-2000:]
    return status, summary


def run_scenarios(fixture_path):
    payload = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
    rows = payload.get("scenarios")
    if payload.get("fixture_version") != "lin_tianji_prediction_validation.v1" or not isinstance(rows, list):
        raise ValueError("unsupported prediction-validation fixture")
    ids = [row.get("id") for row in rows]
    if ids != list(SCENARIO_TESTS):
        raise ValueError("prediction-validation scenario set/order does not match the fixed v1 matrix")
    results = []
    for row in rows:
        scenario_id = row["id"]
        test_id, version = SCENARIO_TESTS[scenario_id]
        status, observed = _run_test(test_id)
        results.append({
            "scenario_id": scenario_id,
            "status": status,
            "reason": row.get("expected") if status == "PASS" else observed.get("detail", "governance check failed"),
            "policy_or_method_version": version,
            "input_digest": _digest({"fixture_version": payload["fixture_version"], "scenario": row, "test_id": test_id}),
            "output_digest": _digest({"status": status, "observed": observed}),
        })
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run deterministic 林氏天機 v1.5 prediction-validation scenarios")
    parser.add_argument("--fixture", default="tests/fixtures/lin_tianji_prediction_validation.v1.json")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    fixture = Path(args.fixture)
    if not fixture.is_absolute():
        fixture = ROOT / fixture
    results = run_scenarios(fixture)
    failed = [row for row in results if row["status"] != "PASS"]
    report = {
        "fixture_version": "lin_tianji_prediction_validation.v1",
        "status": "FAIL" if failed else "PASS",
        "scenario_count": len(results),
        "failed_count": len(failed),
        "results": results,
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    else:
        for row in results:
            print("%s %s - %s" % (row["status"], row["scenario_id"], row["reason"]))
        print("prediction-validation: %s (%d/%d PASS)" % (report["status"], len(results) - len(failed), len(results)))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
