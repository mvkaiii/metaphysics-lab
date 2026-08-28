import copy
import hashlib
import inspect
import json
import unittest

from engine.distribution.errors import DistributionError
from engine.distribution.evidence_ranker import detect_local_spike, rank_evidence
from engine.distribution.historical_personalization import personalize_ranking
from engine.distribution.prospective import (
    METHOD_VERSION,
    lock_prospective_forecast,
    resolve_query_anchor,
)


def feature(feature_id, domain="career", families=None, scope="yearly", **overrides):
    payload = {
        "feature_id": feature_id,
        "system": "bazi",
        "scope": scope,
        "reference_window": {"scope": scope, "reference": "fixture"},
        "primary_domain": domain,
        "event_family_support": list(families or ["role_change"]),
        "strength_class": "moderate",
        "maturity": "stable",
        "qualification_status": "qualified",
        "source_family": "fixture.bazi",
        "dependency_family": "dep:" + feature_id,
        "role": "target_evidence",
        "provenance": {"fixture": feature_id},
    }
    payload.update(overrides)
    return payload


def anchor():
    return resolve_query_anchor({
        "query_anchor_at": "2026-08-28T16:00:00+08:00",
        "query_timezone": "Asia/Taipei",
        "target_start": "2026-08-01T00:00:00+08:00",
        "target_end": "2026-12-31T23:59:59+08:00",
        "question_reference": "synthetic-phase5",
    })


def yearly_ranking():
    return rank_evidence([
        feature("career", "career", ["role_change", "responsibility"]),
        feature("finance", "finance", ["earned_income", "resource_management"]),
        feature("relationship", "relationship", ["one_to_one_change"]),
        feature("family", "family", ["family_responsibility"]),
    ], target_scope="yearly")


def historical_record(record_id, year, domain="finance", family="earned_income", status="matched"):
    verification = "matched" if status in {"matched", "partial"} else "not_matched"
    return {
        "record_id": record_id,
        "record_type": "historical_calibration",
        "calibration_id": "HC-P5",
        "origin": "canonical",
        "blind_prediction": {
            "predicted_flow_year": year,
            "role": "high_activation",
            "primary_domains": [domain],
            "event_family": [family],
            "blindness_status": "blind",
            "hypothesis": "synthetic blind hypothesis",
        },
        "evaluation": {
            "verification_state": verification,
            "domain_status": status,
            "event_form_status": status,
            "timing_status": "exact_flow_year" if verification == "matched" else "missed",
            "offset_flow_years": 0,
            "boundary_ambiguity": False,
        },
        "user_confirmed_actual": {
            "actual_event": "synthetic event that must not affect contract identity",
            "actual_date": "%04d-06-01" % year,
        },
    }


def canonical_digest(value):
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def resign_personalization(value):
    result = copy.deepcopy(value)
    result.pop("personalization_digest", None)
    result["personalization_digest"] = canonical_digest(result)
    return result


def clean_claim(current_anchor, contamination_state="clean_prospective"):
    eligibility = (
        "clean_scorable"
        if contamination_state == "clean_prospective"
        else "excluded_from_clean_accuracy"
    )
    return {
        "claim_id": "P5-C1",
        "forecast_window": {
            "start": "2026-09-01T00:00:00+08:00",
            "end": "2026-09-30T23:59:59+08:00",
        },
        "primary_domain": "career",
        "event_family": "role_change",
        "prediction": "synthetic prospective claim",
        "matched_if": "synthetic event family occurs inside the window",
        "not_matched_if": "synthetic event family does not occur inside the window",
        "evidence_layers": ["bazi"],
        "evidence_time_scales": ["yearly"],
        "capability_maturity": "stable",
        "confidence": "medium",
        "knowledge_cutoff_at": current_anchor["knowledge_cutoff_at"],
        "evaluation_eligibility": eligibility,
        "contamination_state": contamination_state,
        "method_version": METHOD_VERSION,
    }


class InterpretationContractTests(unittest.TestCase):
    def test_cold_start_contract_keeps_phase3_authority_and_primary_limit(self):
        from engine.distribution.interpretation_contract import build_interpretation_contract

        ranking = yearly_ranking()
        result = build_interpretation_contract(ranking, anchor())
        self.assertEqual(
            result["profile_version"],
            "lin_tianji_interpretation_contract_v1-exp",
        )
        self.assertEqual(result["base_ranking_digest"], ranking["ranking_digest"])
        self.assertIsNone(result["personalization_digest"])
        self.assertEqual(result["personalization_status"], "not_provided")
        self.assertEqual(len(result["primary_domains"]), 3)
        self.assertEqual(len(result["secondary_domains"]), 1)
        self.assertEqual(
            [row["primary_domain"] for row in result["domain_interpretation"]],
            ranking["opened_domains"],
        )
        for row in result["domain_interpretation"]:
            self.assertEqual(row["base_rank"], row["presentation_rank"])
            self.assertEqual(
                row["base_allowed_specificity"],
                row["effective_specificity"],
            )
            self.assertFalse(row["personalization_applied"])

    def test_same_canonical_input_produces_same_contract_digest(self):
        from engine.distribution.interpretation_contract import build_interpretation_contract

        first = build_interpretation_contract(yearly_ranking(), anchor())
        second = build_interpretation_contract(yearly_ranking(), anchor())
        self.assertEqual(first, second)
        self.assertEqual(
            first["interpretation_contract_digest"],
            second["interpretation_contract_digest"],
        )

    def test_base_ranking_digest_mismatch_fails_closed(self):
        from engine.distribution.interpretation_contract import build_interpretation_contract

        ranking = copy.deepcopy(yearly_ranking())
        ranking["domains"][0]["rank"] = 99
        with self.assertRaises(DistributionError) as caught:
            build_interpretation_contract(ranking, anchor())
        self.assertEqual(caught.exception.code, "invalid_interpretation_contract")
        self.assertIn("digest", str(caught.exception).lower())

    def test_personalization_changes_presentation_only_and_preserves_base_truth(self):
        from engine.distribution.interpretation_contract import build_interpretation_contract

        ranking = yearly_ranking()
        personalization = personalize_ranking(
            ranking,
            "basic",
            [
                historical_record("H1", 2020),
                historical_record("H2", 2021),
            ],
        )
        self.assertEqual(personalization["personalization_status"], "applied")
        result = build_interpretation_contract(
            ranking,
            anchor(),
            personalization=personalization,
        )
        self.assertEqual(result["personalization_status"], "applied")
        self.assertEqual(
            result["personalization_digest"],
            personalization["personalization_digest"],
        )
        base_by_domain = {row["primary_domain"]: row for row in ranking["domains"]}
        for row in result["domain_interpretation"]:
            base = base_by_domain[row["primary_domain"]]
            self.assertEqual(row["base_rank"], base["rank"])
            self.assertEqual(set(row["event_family_candidates"]), set(base["event_families"]))
            self.assertEqual(row["base_allowed_specificity"], base["allowed_specificity"])

    def test_personalization_no_op_preserves_base_presentation_order(self):
        from engine.distribution.interpretation_contract import build_interpretation_contract

        ranking = yearly_ranking()
        personalization = personalize_ranking(ranking, "basic", [])
        result = build_interpretation_contract(ranking, anchor(), personalization=personalization)
        self.assertEqual(result["personalization_status"], "no_op")
        self.assertEqual(
            [row["primary_domain"] for row in result["domain_interpretation"]],
            ranking["opened_domains"],
        )

    def test_personalization_candidate_set_and_specificity_tampering_fail_closed(self):
        from engine.distribution.interpretation_contract import build_interpretation_contract

        ranking = yearly_ranking()
        valid = personalize_ranking(ranking, "basic", [])

        bad_domain = copy.deepcopy(valid)
        bad_domain["domains"][0]["primary_domain"] = "invented"
        bad_domain = resign_personalization(bad_domain)

        bad_family = copy.deepcopy(valid)
        bad_family["domains"][0]["base_event_families"].append("invented_family")
        bad_family["domains"][0]["personalized_event_family_order"].append("invented_family")
        bad_family = resign_personalization(bad_family)

        bad_specificity = copy.deepcopy(valid)
        bad_specificity["domains"][0]["allowed_specificity"] = "highly_specific_event"
        bad_specificity = resign_personalization(bad_specificity)

        for forged in (bad_domain, bad_family, bad_specificity):
            with self.assertRaises(DistributionError):
                build_interpretation_contract(ranking, anchor(), personalization=forged)

    def test_personalization_base_digest_mismatch_fails_closed(self):
        from engine.distribution.interpretation_contract import build_interpretation_contract

        ranking = yearly_ranking()
        forged = personalize_ranking(ranking, "basic", [])
        forged = copy.deepcopy(forged)
        forged["base_ranking_digest"] = "0" * 64
        forged = resign_personalization(forged)
        with self.assertRaises(DistributionError):
            build_interpretation_contract(ranking, anchor(), personalization=forged)

    def test_daily_local_spike_only_lowers_specificity(self):
        from engine.distribution.interpretation_contract import build_interpretation_contract

        parent = rank_evidence([
            feature("parent-finance", "finance", ["earned_income"], scope="yearly")
        ], target_scope="yearly")
        child = rank_evidence([
            feature(
                "daily-career-a",
                "career",
                ["role_change"],
                scope="daily",
                strength_class="strong",
                dependency_family="daily-a",
            ),
            feature(
                "daily-career-b",
                "career",
                ["role_change"],
                scope="daily",
                strength_class="strong",
                system="ziwei",
                dependency_family="daily-b",
            ),
        ], target_scope="daily")
        self.assertEqual(child["domains"][0]["allowed_specificity"], "concrete_event")
        windows = detect_local_spike(parent, child)
        result = build_interpretation_contract(child, anchor(), local_windows=windows)
        row = result["domain_interpretation"][0]
        self.assertEqual(row["effective_specificity"], "event_family")
        self.assertIn("local_spike", row["evidence_explanation_classes"])

    def test_active_window_is_not_relabelled_local_spike(self):
        from engine.distribution.interpretation_contract import build_interpretation_contract

        parent = rank_evidence([
            feature("year-career", scope="yearly", strength_class="strong")
        ], target_scope="yearly")
        child = rank_evidence([
            feature("month-career", scope="monthly", strength_class="strong")
        ], target_scope="monthly")
        windows = detect_local_spike(parent, child)
        self.assertEqual(windows[0]["window_type"], "active_window")
        result = build_interpretation_contract(child, anchor(), local_windows=windows)
        classes = result["domain_interpretation"][0]["evidence_explanation_classes"]
        self.assertIn("active_window", classes)
        self.assertNotIn("local_spike", classes)

    def test_local_window_wrong_child_digest_or_specificity_promotion_fails_closed(self):
        from engine.distribution.interpretation_contract import build_interpretation_contract

        parent = rank_evidence([], target_scope="yearly")
        child = rank_evidence([
            feature("daily-career", scope="daily", strength_class="strong")
        ], target_scope="daily")
        windows = detect_local_spike(parent, child)

        bad_digest = copy.deepcopy(windows)
        bad_digest[0]["child_ranking_digest"] = "0" * 64
        with self.assertRaises(DistributionError):
            build_interpretation_contract(child, anchor(), local_windows=bad_digest)

        bad_specificity = copy.deepcopy(windows)
        bad_specificity[0]["source_allowed_specificity"] = "domain"
        bad_specificity[0]["allowed_specificity"] = "concrete_event"
        with self.assertRaises(DistributionError):
            build_interpretation_contract(child, anchor(), local_windows=bad_specificity)

    def test_explanation_classes_are_metadata_only_and_do_not_leak_scores(self):
        from engine.distribution.interpretation_contract import build_interpretation_contract

        ranking = rank_evidence([
            feature(
                "career-a",
                dependency_family="dep-a",
                strength_class="strong",
                maturity="experimental",
            ),
            feature(
                "career-b",
                system="ziwei",
                dependency_family="dep-b",
                strength_class="strong",
                maturity="experimental",
            ),
            feature(
                "career-background",
                scope="decadal",
                role="modifier",
                dependency_family="dep-bg",
            ),
        ], target_scope="yearly")
        result = build_interpretation_contract(ranking, anchor())
        row = result["domain_interpretation"][0]
        self.assertIn("independent_convergence", row["evidence_explanation_classes"])
        self.assertIn("target_with_background_modifier", row["evidence_explanation_classes"])
        self.assertIn("experimental_only", row["evidence_explanation_classes"])
        serialized = json.dumps(row["evidence_explanation_classes"], ensure_ascii=False)
        self.assertNotIn("ordinal_score_scaled", serialized)
        self.assertNotIn("threshold", serialized)

    def test_locked_forecast_adds_structural_boundary_without_prediction_prose(self):
        from engine.distribution.interpretation_contract import build_interpretation_contract

        current_anchor = anchor()
        claim = clean_claim(current_anchor)
        locked = lock_prospective_forecast({"anchor": current_anchor, "claims": [claim]})
        result = build_interpretation_contract(
            yearly_ranking(),
            current_anchor,
            locked_forecast=locked,
        )
        self.assertEqual(len(result["claim_boundaries"]), 1)
        boundary = result["claim_boundaries"][0]
        self.assertEqual(boundary["claim_id"], claim["claim_id"])
        self.assertEqual(boundary["locked_forecast_digest"], locked["canonical_digest"])
        self.assertNotIn("prediction", boundary)
        self.assertNotIn("matched_if", boundary)
        self.assertNotIn("not_matched_if", boundary)

    def test_locked_forecast_digest_anchor_and_unlocked_shape_fail_closed(self):
        from engine.distribution.interpretation_contract import build_interpretation_contract

        current_anchor = anchor()
        locked = lock_prospective_forecast({
            "anchor": current_anchor,
            "claims": [clean_claim(current_anchor)],
        })

        bad_digest = copy.deepcopy(locked)
        bad_digest["canonical_digest"] = "0" * 64
        with self.assertRaises(DistributionError):
            build_interpretation_contract(yearly_ranking(), current_anchor, locked_forecast=bad_digest)

        other_anchor = copy.deepcopy(current_anchor)
        other_anchor["question_reference"] = "different-question"
        with self.assertRaises(DistributionError):
            build_interpretation_contract(yearly_ranking(), other_anchor, locked_forecast=locked)

        with self.assertRaises(DistributionError):
            build_interpretation_contract(
                yearly_ranking(),
                current_anchor,
                locked_forecast={"claims": locked["claims"]},
            )

    def test_partially_known_claim_remains_excluded_from_clean_accuracy(self):
        from engine.distribution.interpretation_contract import build_interpretation_contract

        current_anchor = anchor()
        locked = lock_prospective_forecast({
            "anchor": current_anchor,
            "claims": [clean_claim(current_anchor, contamination_state="partially_known")],
        })
        result = build_interpretation_contract(
            yearly_ranking(), current_anchor, locked_forecast=locked
        )
        boundary = result["claim_boundaries"][0]
        self.assertEqual(boundary["contamination_state"], "partially_known")
        self.assertEqual(
            boundary["evaluation_eligibility"],
            "excluded_from_clean_accuracy",
        )

    def test_contract_has_no_reality_free_text_input(self):
        from engine.distribution.interpretation_contract import build_interpretation_contract

        self.assertEqual(
            list(inspect.signature(build_interpretation_contract).parameters),
            [
                "base_ranking",
                "anchor",
                "personalization",
                "local_windows",
                "locked_forecast",
            ],
        )


if __name__ == "__main__":
    unittest.main()
