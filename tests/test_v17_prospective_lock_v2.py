import copy
import unittest

from engine.distribution.errors import DistributionError
from engine.distribution import prospective


class ProspectiveLockV2Tests(unittest.TestCase):
    @staticmethod
    def _anchor():
        return prospective.resolve_query_anchor(
            {
                "query_anchor_at": "2026-09-09T09:00:00+08:00",
                "query_timezone": "Asia/Taipei",
                "target_start": "2026-10-01T00:00:00+08:00",
                "target_end": "2026-10-31T23:59:59+08:00",
                "question_reference": "synthetic-v2-contract",
            }
        )

    def _context_input(self, **overrides):
        payload = {
            "target_time_relation_to_cutoff": "future",
            "known_arrangement_before_lock": True,
            "claim_describes_known_fact": False,
            "claim_depends_on_known_arrangement": True,
            "outcome_known_before_lock": False,
        }
        payload.update(overrides)
        return payload

    def _claim(self, **overrides):
        anchor = self._anchor()
        context_input = self._context_input()
        classification = prospective.classify_validation_context(context_input)
        claim = {
            "claim_id": "SYN-V2-001",
            "forecast_window": {
                "start": "2026-10-10T00:00:00+08:00",
                "end": "2026-10-20T23:59:59+08:00",
            },
            "primary_domain": "career",
            "event_family": "resource_discussion",
            "prediction": "A fictional scheduled review includes a resource discussion.",
            "matched_if": "A resource discussion is explicitly recorded during the review window.",
            "not_matched_if": "No resource discussion is recorded during the review window.",
            "evidence_layers": ["synthetic_bazi"],
            "evidence_time_scales": ["monthly"],
            "capability_maturity": "experimental",
            "confidence": "medium",
            "knowledge_cutoff_at": anchor["knowledge_cutoff_at"],
            "context_class": classification["context_class"],
            "clean_accuracy_eligible": classification["clean_accuracy_eligible"],
            "conditional_accuracy_eligible": classification["conditional_accuracy_eligible"],
            "validation_context_input": context_input,
        }
        claim.update(overrides)
        return claim

    def _payload(self, claim=None):
        return {
            "anchor": self._anchor(),
            "claims": [claim or self._claim()],
            "claim_contract_version": "2.0",
        }

    def test_v2_conditional_claim_locks_with_separate_eligibility(self):
        locked = prospective.lock_prospective_forecast(self._payload())
        self.assertEqual(locked["status"], "locked")
        self.assertEqual(locked["method_version"], "lin_tianji_v1.7-validation-v2-exp")
        self.assertEqual(locked["claim_contract_version"], "2.0")
        claim = locked["claims"][0]
        self.assertEqual(claim["context_class"], "conditional_prospective")
        self.assertFalse(claim["clean_accuracy_eligible"])
        self.assertTrue(claim["conditional_accuracy_eligible"])
        self.assertEqual(claim["validation_context_input"], self._context_input())
        self.assertEqual(len(locked["canonical_digest"]), 64)

    def test_v2_recomputes_context_and_rejects_forged_declaration(self):
        forged = self._claim(context_class="clean_prospective")
        with self.assertRaises(DistributionError) as caught:
            prospective.lock_prospective_forecast(self._payload(forged))
        self.assertEqual(caught.exception.code, "validation_context_mismatch")

    def test_v2_rejects_forged_eligibility(self):
        forged = self._claim(clean_accuracy_eligible=True)
        with self.assertRaises(DistributionError) as caught:
            prospective.lock_prospective_forecast(self._payload(forged))
        self.assertEqual(caught.exception.code, "validation_context_mismatch")

    def test_retrospective_claim_cannot_enter_prospective_lock(self):
        context_input = self._context_input(
            target_time_relation_to_cutoff="past_or_present",
            known_arrangement_before_lock=False,
            claim_depends_on_known_arrangement=False,
        )
        classification = prospective.classify_validation_context(context_input)
        claim = self._claim(
            context_class=classification["context_class"],
            clean_accuracy_eligible=classification["clean_accuracy_eligible"],
            conditional_accuracy_eligible=classification["conditional_accuracy_eligible"],
            validation_context_input=context_input,
        )
        with self.assertRaises(DistributionError) as caught:
            prospective.lock_prospective_forecast(self._payload(claim))
        self.assertEqual(caught.exception.code, "retrospective_claim_not_lockable")

    def test_v2_rejects_unknown_contract_version(self):
        payload = self._payload()
        payload["claim_contract_version"] = "2.1"
        with self.assertRaises(DistributionError) as caught:
            prospective.lock_prospective_forecast(payload)
        self.assertEqual(caught.exception.code, "invalid_prospective_forecast")

    def test_v2_digest_detects_context_input_change(self):
        first = prospective.lock_prospective_forecast(self._payload())
        changed = copy.deepcopy(self._claim())
        changed_context = self._context_input(
            known_arrangement_before_lock=False,
            claim_depends_on_known_arrangement=False,
        )
        changed_classification = prospective.classify_validation_context(changed_context)
        changed["validation_context_input"] = changed_context
        changed["context_class"] = changed_classification["context_class"]
        changed["clean_accuracy_eligible"] = changed_classification["clean_accuracy_eligible"]
        changed["conditional_accuracy_eligible"] = changed_classification["conditional_accuracy_eligible"]
        second = prospective.lock_prospective_forecast(self._payload(changed))
        self.assertNotEqual(first["canonical_digest"], second["canonical_digest"])


if __name__ == "__main__":
    unittest.main()
