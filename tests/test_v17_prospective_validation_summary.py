import copy
import unittest

from engine.distribution.errors import DistributionError
from engine.distribution.prospective_validation import (
    build_validation_summary,
    classify_validation_context,
)


class ProspectiveValidationSummaryTests(unittest.TestCase):
    @staticmethod
    def _context(forecast_id, mode="future_forecast", knowledge="unknown"):
        if mode == "future_forecast":
            window = {"start": "2026-10-01T00:00:00+08:00", "end": "2026-10-31T23:59:59+08:00"}
        else:
            window = {"start": "2026-09-01T00:00:00+08:00", "end": "2026-09-08T23:59:59+08:00"}
        return classify_validation_context({
            "forecast_id": forecast_id,
            "locked_at": "2026-09-09T09:30:00+08:00",
            "knowledge_cutoff_at": "2026-09-09T09:20:00+08:00",
            "question_mode": mode,
            "knowledge_state_at_lock": knowledge,
            "prediction_window": window,
        })

    def test_only_clean_adjudicated_records_enter_clean_denominator(self):
        records = [
            {"validation_context": self._context("clean"), "verification_state": "matched"},
            {"validation_context": self._context("conditional", knowledge="partial"), "verification_state": "matched"},
            {"validation_context": self._context("hidden", mode="hidden_existing_reality"), "verification_state": "matched"},
            {"validation_context": self._context("retro", mode="retrospective_calibration", knowledge="known"), "verification_state": "matched"},
        ]
        result = build_validation_summary({"records": records})
        self.assertEqual(result["clean_denominator"]["scorable_count"], 1)
        self.assertEqual(result["clean_denominator"]["matched_count"], 1)
        self.assertEqual(result["excluded_context_counts"]["conditional_prospective"], 1)
        self.assertEqual(result["excluded_context_counts"]["hidden_existing_reality"], 1)
        self.assertEqual(result["excluded_context_counts"]["retrospective_calibration"], 1)

    def test_pending_and_cannot_recall_are_not_clean_scorable(self):
        result = build_validation_summary({"records": [
            {"validation_context": self._context("pending"), "verification_state": "pending"},
            {"validation_context": self._context("recall"), "verification_state": "cannot_recall"},
        ]})
        self.assertEqual(result["clean_denominator"]["scorable_count"], 0)
        self.assertEqual(result["pending_count"], 1)
        self.assertEqual(result["cannot_recall_count"], 1)

    def test_context_digest_tampering_fails_closed(self):
        context = self._context("tampered")
        context["context_class"] = "clean_prospective"
        with self.assertRaises(DistributionError) as caught:
            build_validation_summary({"records": [
                {"validation_context": context, "verification_state": "matched"},
            ]})
        self.assertEqual(caught.exception.code, "invalid_validation_summary")


if __name__ == "__main__":
    unittest.main()
