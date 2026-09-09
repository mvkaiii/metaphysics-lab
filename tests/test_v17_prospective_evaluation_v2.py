import copy
import unittest

from engine.distribution import prospective
from engine.distribution import prospective_evaluation as evaluation
from engine.distribution.errors import DistributionError


class ProspectiveEvaluationV2Tests(unittest.TestCase):
    @staticmethod
    def _anchor():
        return prospective.resolve_query_anchor(
            {
                "query_anchor_at": "2026-09-09T09:00:00+08:00",
                "query_timezone": "Asia/Taipei",
                "target_start": "2026-10-01T00:00:00+08:00",
                "target_end": "2026-10-31T23:59:59+08:00",
                "question_reference": "synthetic-v2-evaluation",
            }
        )

    @staticmethod
    def _context(context_class):
        if context_class == "clean_prospective":
            return {
                "target_time_relation_to_cutoff": "future",
                "known_arrangement_before_lock": False,
                "claim_describes_known_fact": False,
                "claim_depends_on_known_arrangement": False,
                "outcome_known_before_lock": False,
            }
        if context_class == "conditional_prospective":
            return {
                "target_time_relation_to_cutoff": "future",
                "known_arrangement_before_lock": True,
                "claim_describes_known_fact": False,
                "claim_depends_on_known_arrangement": True,
                "outcome_known_before_lock": False,
            }
        if context_class == "hidden_existing_reality":
            return {
                "target_time_relation_to_cutoff": "future",
                "known_arrangement_before_lock": True,
                "claim_describes_known_fact": True,
                "claim_depends_on_known_arrangement": False,
                "outcome_known_before_lock": False,
            }
        raise AssertionError(context_class)

    def _claim(self, context_class="conditional_prospective", **overrides):
        anchor = self._anchor()
        context_input = self._context(context_class)
        classified = prospective.classify_validation_context(context_input)
        claim = {
            "claim_id": "SYN-EVAL-%s" % context_class,
            "forecast_window": {
                "start": "2026-10-10T00:00:00+08:00",
                "end": "2026-10-20T23:59:59+08:00",
            },
            "primary_domain": "career",
            "event_family": "synthetic_event",
            "prediction": "A fictional event is recorded.",
            "matched_if": "The fictional event is explicitly recorded in the window.",
            "not_matched_if": "The fictional event is not recorded in the window.",
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
        claim.update(overrides)
        return claim

    def _locked(self, context_class="conditional_prospective"):
        return prospective.lock_prospective_forecast(
            {
                "anchor": self._anchor(),
                "claims": [self._claim(context_class)],
                "claim_contract_version": "2.0",
            }
        )

    def _evaluation_payload(self, locked, verification_state="matched"):
        return {
            "locked_forecast": locked,
            "claim_id": locked["claims"][0]["claim_id"],
            "verification_state": verification_state,
            "observed_actual": "Synthetic outcome recorded after the forecast window.",
            "evaluated_at": "2026-10-21T09:00:00+08:00",
        }

    def test_v2_contexts_route_to_separate_scoring_buckets(self):
        expected = {
            "clean_prospective": "clean_prospective",
            "conditional_prospective": "conditional_prospective",
            "hidden_existing_reality": "hidden_existing_reality_research",
        }
        for context_class, scoring_bucket in expected.items():
            with self.subTest(context_class=context_class):
                locked = self._locked(context_class)
                result = evaluation.evaluate_locked_claim(self._evaluation_payload(locked))
                self.assertEqual(result["evaluation"]["scoring_bucket"], scoring_bucket)
                self.assertTrue(result["evaluation"]["scorable"])
                self.assertIsNone(result["evaluation"]["score_exclusion_reason"])

    def test_v2_cannot_recall_stays_in_its_bucket_but_is_not_scorable(self):
        locked = self._locked("conditional_prospective")
        result = evaluation.evaluate_locked_claim(
            self._evaluation_payload(locked, verification_state="cannot_recall")
        )
        self.assertEqual(result["evaluation"]["scoring_bucket"], "conditional_prospective")
        self.assertFalse(result["evaluation"]["scorable"])
        self.assertEqual(result["evaluation"]["score_exclusion_reason"], "cannot_recall")

    def test_v2_lock_immutability_covers_context_boundaries_and_digest(self):
        locked = self._locked("conditional_prospective")
        mutations = []

        changed_context = copy.deepcopy(locked)
        changed_context["claims"][0]["validation_context_input"]["known_arrangement_before_lock"] = False
        changed_context["claims"][0]["validation_context_input"]["claim_depends_on_known_arrangement"] = False
        mutations.append(changed_context)

        changed_class = copy.deepcopy(locked)
        changed_class["claims"][0]["context_class"] = "clean_prospective"
        mutations.append(changed_class)

        changed_eligibility = copy.deepcopy(locked)
        changed_eligibility["claims"][0]["clean_accuracy_eligible"] = True
        mutations.append(changed_eligibility)

        changed_boundary = copy.deepcopy(locked)
        changed_boundary["claims"][0]["matched_if"] = "A post-lock relaxed boundary."
        mutations.append(changed_boundary)

        changed_digest = copy.deepcopy(locked)
        changed_digest["canonical_digest"] = "0" * 64
        mutations.append(changed_digest)

        for tampered in mutations:
            with self.subTest(tampered=tampered["claims"][0]["claim_id"]):
                with self.assertRaises(DistributionError) as caught:
                    evaluation.evaluate_locked_claim(self._evaluation_payload(tampered))
                self.assertEqual(caught.exception.code, "invalid_prospective_evaluation")

    def test_validation_context_summary_keeps_denominators_separate(self):
        clean = evaluation.evaluate_locked_claim(
            self._evaluation_payload(self._locked("clean_prospective"), "matched")
        )
        conditional = evaluation.evaluate_locked_claim(
            self._evaluation_payload(self._locked("conditional_prospective"), "partial")
        )
        hidden = evaluation.evaluate_locked_claim(
            self._evaluation_payload(self._locked("hidden_existing_reality"), "cannot_recall")
        )

        summary = evaluation.build_validation_context_summary([clean, conditional, hidden])

        self.assertEqual(summary["status"], "validation_context_summary")
        self.assertIsNone(summary["pooled_accuracy_denominator"])
        self.assertEqual(
            summary["buckets"]["clean_prospective"],
            {
                "scorable_count": 1,
                "matched_count": 1,
                "partial_count": 0,
                "not_matched_count": 0,
                "cannot_recall_count": 0,
            },
        )
        self.assertEqual(
            summary["buckets"]["conditional_prospective"],
            {
                "scorable_count": 1,
                "matched_count": 0,
                "partial_count": 1,
                "not_matched_count": 0,
                "cannot_recall_count": 0,
            },
        )
        self.assertEqual(
            summary["buckets"]["hidden_existing_reality_research"],
            {
                "scorable_count": 0,
                "matched_count": 0,
                "partial_count": 0,
                "not_matched_count": 0,
                "cannot_recall_count": 1,
            },
        )


if __name__ == "__main__":
    unittest.main()
