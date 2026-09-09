import copy
import unittest

from engine.distribution.errors import DistributionError


class ProspectiveValidationClassifierTests(unittest.TestCase):
    def _module(self):
        from engine.distribution import prospective_validation
        return prospective_validation

    @staticmethod
    def _payload(**overrides):
        payload = {
            "forecast_id": "PV2-001",
            "locked_at": "2026-09-09T09:30:00+08:00",
            "knowledge_cutoff_at": "2026-09-09T09:20:00+08:00",
            "question_mode": "future_forecast",
            "knowledge_state_at_lock": "unknown",
            "prediction_window": {
                "start": "2026-10-01T00:00:00+08:00",
                "end": "2026-10-31T23:59:59+08:00",
            },
        }
        payload.update(overrides)
        return payload

    def test_unknown_future_is_clean_prospective(self):
        result = self._module().classify_validation_context(self._payload())
        self.assertEqual(result["status"], "classified")
        self.assertEqual(result["context_class"], "clean_prospective")
        self.assertTrue(result["clean_denominator_eligible"])
        self.assertEqual(result["outcome_status_at_lock"], "pending")
        self.assertEqual(result["adjudication_earliest_at"], "2026-10-31T23:59:59+08:00")
        self.assertEqual(len(result["canonical_digest"]), 64)

    def test_partially_or_fully_known_future_is_conditional(self):
        for state in ("partial", "known"):
            with self.subTest(state=state):
                result = self._module().classify_validation_context(
                    self._payload(knowledge_state_at_lock=state)
                )
                self.assertEqual(result["context_class"], "conditional_prospective")
                self.assertFalse(result["clean_denominator_eligible"])

    def test_hidden_existing_reality_is_never_clean(self):
        result = self._module().classify_validation_context(self._payload(
            question_mode="hidden_existing_reality",
            prediction_window={
                "start": "2026-09-01T00:00:00+08:00",
                "end": "2026-09-08T23:59:59+08:00",
            },
        ))
        self.assertEqual(result["context_class"], "hidden_existing_reality")
        self.assertFalse(result["clean_denominator_eligible"])
        self.assertEqual(result["adjudication_earliest_at"], "2026-09-09T09:30:00+08:00")

    def test_retrospective_calibration_is_never_clean(self):
        result = self._module().classify_validation_context(self._payload(
            question_mode="retrospective_calibration",
            knowledge_state_at_lock="known",
            prediction_window={
                "start": "2025-01-01T00:00:00+08:00",
                "end": "2025-12-31T23:59:59+08:00",
            },
        ))
        self.assertEqual(result["context_class"], "retrospective_calibration")
        self.assertFalse(result["clean_denominator_eligible"])

    def test_conflicting_mode_time_or_knowledge_fails_closed(self):
        cases = (
            self._payload(prediction_window={
                "start": "2026-09-01T00:00:00+08:00",
                "end": "2026-09-30T23:59:59+08:00",
            }),
            self._payload(
                question_mode="hidden_existing_reality",
                knowledge_state_at_lock="known",
                prediction_window={
                    "start": "2026-09-01T00:00:00+08:00",
                    "end": "2026-09-08T23:59:59+08:00",
                },
            ),
            self._payload(
                question_mode="retrospective_calibration",
                prediction_window={
                    "start": "2026-09-01T00:00:00+08:00",
                    "end": "2026-10-01T00:00:00+08:00",
                },
            ),
        )
        for payload in cases:
            with self.subTest(payload=payload):
                with self.assertRaises(DistributionError) as caught:
                    self._module().classify_validation_context(payload)
                self.assertEqual(caught.exception.code, "invalid_validation_context")

    def test_digest_is_deterministic_and_detects_semantic_change(self):
        first = self._module().classify_validation_context(self._payload())
        second = self._module().classify_validation_context(self._payload())
        changed = self._module().classify_validation_context(
            self._payload(forecast_id="PV2-002")
        )
        self.assertEqual(first, second)
        self.assertNotEqual(first["canonical_digest"], changed["canonical_digest"])


if __name__ == "__main__":
    unittest.main()
