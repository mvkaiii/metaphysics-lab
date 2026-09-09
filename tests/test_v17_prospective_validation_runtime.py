import unittest

from engine.distribution.prospective import classify_validation_context, lock_prospective_forecast, resolve_query_anchor
from engine.distribution.prospective_evaluation import evaluate_locked_claim
from engine.distribution.runtime import dispatch, runtime_info


class ProspectiveValidationRuntimeTests(unittest.TestCase):
    @staticmethod
    def _conditional_context():
        return {
            "target_time_relation_to_cutoff": "future",
            "known_arrangement_before_lock": True,
            "claim_describes_known_fact": False,
            "claim_depends_on_known_arrangement": True,
            "outcome_known_before_lock": False,
        }

    def _locked(self):
        anchor = resolve_query_anchor(
            {
                "query_anchor_at": "2026-09-09T09:00:00+08:00",
                "query_timezone": "Asia/Taipei",
                "target_start": "2026-10-01T00:00:00+08:00",
                "target_end": "2026-10-31T23:59:59+08:00",
                "question_reference": "synthetic-runtime-v2",
            }
        )
        context_input = self._conditional_context()
        classified = classify_validation_context(context_input)
        claim = {
            "claim_id": "SYN-RUNTIME-V2-001",
            "forecast_window": {
                "start": "2026-10-10T00:00:00+08:00",
                "end": "2026-10-20T23:59:59+08:00",
            },
            "primary_domain": "career",
            "event_family": "synthetic_event",
            "prediction": "A fictional conditional event is recorded.",
            "matched_if": "The fictional conditional event is recorded in the window.",
            "not_matched_if": "The fictional conditional event is not recorded in the window.",
            "evidence_layers": ["synthetic_bazi"],
            "evidence_time_scales": ["monthly"],
            "capability_maturity": "experimental",
            "confidence": "medium",
            "knowledge_cutoff_at": anchor["knowledge_cutoff_at"],
            "context_class": classified["context_class"],
            "clean_accuracy_eligible": classified["clean_accuracy_eligible"],
            "conditional_accuracy_eligible": classified["conditional_accuracy_eligible"],
            "validation_context_input": context_input,
        }
        return lock_prospective_forecast(
            {
                "anchor": anchor,
                "claims": [claim],
                "claim_contract_version": "2.0",
            }
        )

    def _evaluation_payload(self):
        locked = self._locked()
        return {
            "locked_forecast": locked,
            "claim_id": locked["claims"][0]["claim_id"],
            "verification_state": "matched",
            "observed_actual": "Synthetic conditional outcome recorded after the forecast window.",
            "evaluated_at": "2026-10-21T09:00:00+08:00",
        }

    def test_runtime_info_advertises_all_validation_v2_actions(self):
        supported = runtime_info()["supported_actions"]
        for action in (
            "classify_validation_context",
            "evaluate_locked_claim",
            "summarize_validation_contexts",
        ):
            with self.subTest(action=action):
                self.assertIn(action, supported)

    def test_classifier_dispatch_matches_core_result(self):
        payload = self._conditional_context()
        result = dispatch("classify_validation_context", payload)

        self.assertTrue(result["ok"], result)
        self.assertEqual(result["data"], classify_validation_context(payload))
        self.assertEqual(result["data"]["context_class"], "conditional_prospective")

    def test_evaluation_dispatch_matches_core_result(self):
        payload = self._evaluation_payload()
        result = dispatch("evaluate_locked_claim", payload)

        self.assertTrue(result["ok"], result)
        self.assertEqual(result["data"], evaluate_locked_claim(payload))
        self.assertEqual(result["data"]["evaluation"]["scoring_bucket"], "conditional_prospective")

    def test_summary_dispatch_keeps_pooled_denominator_none(self):
        evaluated = evaluate_locked_claim(self._evaluation_payload())
        result = dispatch("summarize_validation_contexts", {"records": [evaluated]})

        self.assertTrue(result["ok"], result)
        self.assertIsNone(result["data"]["pooled_accuracy_denominator"])
        self.assertEqual(
            result["data"]["buckets"]["conditional_prospective"]["scorable_count"],
            1,
        )


if __name__ == "__main__":
    unittest.main()
