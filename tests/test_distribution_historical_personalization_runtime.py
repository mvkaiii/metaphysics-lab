import unittest

from engine.distribution.evidence_ranker import rank_evidence
from engine.distribution.runtime import dispatch, runtime_info


class HistoricalPersonalizationRuntimeTests(unittest.TestCase):
    def feature(self, feature_id, **overrides):
        payload = {
            "feature_id": feature_id,
            "system": "bazi",
            "scope": "yearly",
            "reference_window": {"scope": "yearly", "reference": "fixture"},
            "primary_domain": "career",
            "event_family_support": ["role_change", "responsibility"],
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

    def base_ranking(self):
        return rank_evidence([self.feature("career")], target_scope="yearly")

    def test_runtime_info_exposes_phase4_capability_and_action(self):
        info = runtime_info()
        self.assertIn("personalize_ranking", info["supported_actions"])
        cap = info["capabilities"]["distribution.historical_personalization"]
        self.assertEqual(cap["implementation"], "implemented")
        self.assertEqual(cap["maturity"], "experimental")
        self.assertEqual(cap["routing"], "on_demand")
        self.assertFalse(cap["ranking_authority"])
        self.assertEqual(
            cap["rule_version"],
            "lin_tianji_historical_personalization_v1-exp",
        )

    def test_dispatch_personalize_ranking_returns_core_result(self):
        response = dispatch(
            "personalize_ranking",
            {
                "base_ranking": self.base_ranking(),
                "historical_calibration_status": "basic",
                "historical_records": [],
            },
        )
        self.assertTrue(response["ok"], response)
        self.assertEqual(response["action"], "personalize_ranking")
        self.assertEqual(response["data"]["personalization_status"], "no_op")
        self.assertEqual(
            response["data"]["base_ranking_digest"],
            self.base_ranking()["ranking_digest"],
        )

    def test_dispatch_rejects_unknown_training_or_research_payload_fields(self):
        response = dispatch(
            "personalize_ranking",
            {
                "base_ranking": self.base_ranking(),
                "historical_calibration_status": "basic",
                "historical_records": [],
                "actual_event_text_as_training_input": "must not be accepted",
                "research_notes": "must not be accepted",
            },
        )
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "invalid_historical_personalization")
        self.assertEqual(
            response["error"]["details"]["unknown_fields"],
            ["actual_event_text_as_training_input", "research_notes"],
        )


if __name__ == "__main__":
    unittest.main()
