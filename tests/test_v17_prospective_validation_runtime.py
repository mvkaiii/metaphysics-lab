import unittest

from engine.distribution.runtime import dispatch


class ProspectiveValidationRuntimeTests(unittest.TestCase):
    @staticmethod
    def context_payload():
        return {
            "forecast_id": "PV2-runtime",
            "locked_at": "2026-09-09T09:30:00+08:00",
            "knowledge_cutoff_at": "2026-09-09T09:20:00+08:00",
            "question_mode": "future_forecast",
            "knowledge_state_at_lock": "unknown",
            "prediction_window": {
                "start": "2026-10-01T00:00:00+08:00",
                "end": "2026-10-31T23:59:59+08:00",
            },
        }

    def test_runtime_advertises_and_dispatches_v2_validation(self):
        info = dispatch("runtime_info", {})
        self.assertTrue(info["ok"], info)
        self.assertIn("classify_validation_context", info["data"]["supported_actions"])
        self.assertIn("build_validation_summary", info["data"]["supported_actions"])
        capability = info["data"]["capabilities"]["distribution.prospective_validation"]
        self.assertEqual(capability["implementation"], "implemented")
        self.assertEqual(capability["maturity"], "experimental")
        self.assertEqual(capability["routing"], "on_demand")
        self.assertEqual(capability["rule_version"], "prospective-validation-v2-exp")
        self.assertFalse(capability["ranking_authority"])

        classified = dispatch("classify_validation_context", self.context_payload())
        self.assertTrue(classified["ok"], classified)
        summary = dispatch("build_validation_summary", {
            "records": [{"validation_context": classified["data"], "verification_state": "matched"}],
        })
        self.assertTrue(summary["ok"], summary)
        self.assertEqual(summary["data"]["clean_denominator"]["scorable_count"], 1)


if __name__ == "__main__":
    unittest.main()
