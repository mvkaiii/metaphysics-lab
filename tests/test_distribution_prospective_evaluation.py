import copy
import importlib
import unittest

from engine.distribution.errors import DistributionError


class DistributionProspectiveEvaluationTests(unittest.TestCase):
    @staticmethod
    def _prospective():
        return importlib.import_module("engine.distribution.prospective")

    @staticmethod
    def _evaluation():
        return importlib.import_module("engine.distribution.prospective_evaluation")

    def _anchor(self):
        return self._prospective().resolve_query_anchor(
            {
                "query_anchor_at": "2026-08-28T20:00:00+08:00",
                "query_timezone": "Asia/Taipei",
                "target_start": "2026-09-01T00:00:00+08:00",
                "target_end": "2026-12-31T23:59:59+08:00",
                "question_reference": "phase6-prospective-evaluation-fixture",
            }
        )

    def _claim(self, **overrides):
        anchor = self._anchor()
        claim = {
            "claim_id": "claim-2026-09-work-001",
            "forecast_window": {
                "start": "2026-09-01T00:00:00+08:00",
                "end": "2026-09-30T23:59:59+08:00",
            },
            "primary_domain": "工作",
            "event_family": "職責變動",
            "prediction": "9 月內出現可被正式記錄的工作職責調整。",
            "matched_if": "正式職稱、管理範圍或書面職責至少一項在預測窗內改變。",
            "not_matched_if": "預測窗結束時，上述三項均未發生正式改變。",
            "evidence_layers": ["bazi.yearly", "ziwei.yearly"],
            "evidence_time_scales": ["yearly"],
            "capability_maturity": "stable",
            "confidence": "medium",
            "knowledge_cutoff_at": anchor["knowledge_cutoff_at"],
            "evaluation_eligibility": "clean_scorable",
            "contamination_state": "clean_prospective",
            "method_version": "lin_tianji_v1.5-exp",
        }
        claim.update(overrides)
        return claim

    def _locked(self, **claim_overrides):
        anchor = self._anchor()
        return self._prospective().lock_prospective_forecast(
            {"anchor": anchor, "claims": [self._claim(**claim_overrides)]}
        )

    def _payload(self, locked=None, **overrides):
        locked = locked or self._locked()
        payload = {
            "locked_forecast": locked,
            "claim_id": locked["claims"][0]["claim_id"],
            "verification_state": "matched",
            "observed_actual": "9 月 12 日收到正式書面通知，管理範圍新增一個專案。",
            "evaluated_at": "2026-10-01T09:00:00+08:00",
        }
        payload.update(overrides)
        return payload

    def test_evaluation_preserves_locked_claim_and_appends_explicit_result(self):
        evaluation = self._evaluation()
        locked = self._locked()

        result = evaluation.evaluate_locked_claim(self._payload(locked))

        self.assertEqual(result["status"], "evaluated")
        self.assertEqual(result["locked_forecast_digest"], locked["canonical_digest"])
        self.assertEqual(result["claim"], locked["claims"][0])
        self.assertEqual(result["evaluation"]["verification_state"], "matched")
        self.assertEqual(
            result["evaluation"]["observed_actual"],
            "9 月 12 日收到正式書面通知，管理範圍新增一個專案。",
        )
        self.assertEqual(result["evaluation"]["evaluated_at"], "2026-10-01T09:00:00+08:00")
        self.assertTrue(result["evaluation"]["scorable"])

    def test_evaluation_rejects_locked_forecast_whose_prediction_was_changed_after_lock(self):
        evaluation = self._evaluation()
        locked = self._locked()
        tampered = copy.deepcopy(locked)
        tampered["claims"][0]["prediction"] = "事後改寫的預測文字"

        with self.assertRaises(DistributionError) as caught:
            evaluation.evaluate_locked_claim(self._payload(tampered))

        self.assertEqual(caught.exception.code, "invalid_prospective_evaluation")

    def test_evaluation_rejects_locked_forecast_whose_boundaries_were_changed_after_lock(self):
        evaluation = self._evaluation()
        mutations = (
            ("forecast_window", {"start": "2026-09-02T00:00:00+08:00", "end": "2026-09-30T23:59:59+08:00"}),
            ("matched_if", "事後放寬 matched 邊界"),
            ("not_matched_if", "事後放寬 not_matched 邊界"),
            ("knowledge_cutoff_at", "2026-08-29T20:00:00+08:00"),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                tampered = copy.deepcopy(self._locked())
                tampered["claims"][0][field] = value
                with self.assertRaises(DistributionError) as caught:
                    evaluation.evaluate_locked_claim(self._payload(tampered))
                self.assertEqual(caught.exception.code, "invalid_prospective_evaluation")

    def test_contaminated_claim_can_be_described_but_is_not_clean_scorable(self):
        evaluation = self._evaluation()
        locked = self._locked(
            contamination_state="known_before_lock",
            evaluation_eligibility="excluded_from_clean_accuracy",
        )

        result = evaluation.evaluate_locked_claim(self._payload(locked))

        self.assertEqual(result["evaluation"]["verification_state"], "matched")
        self.assertFalse(result["evaluation"]["scorable"])
        self.assertEqual(
            result["evaluation"]["score_exclusion_reason"],
            "excluded_from_clean_accuracy",
        )

    def test_cannot_recall_is_unscorable_even_for_clean_claim(self):
        evaluation = self._evaluation()

        result = evaluation.evaluate_locked_claim(
            self._payload(
                verification_state="cannot_recall",
                observed_actual="目前沒有足夠紀錄可確認。",
            )
        )

        self.assertFalse(result["evaluation"]["scorable"])
        self.assertEqual(result["evaluation"]["score_exclusion_reason"], "cannot_recall")

    def test_evaluator_uses_explicit_verification_state_without_reinterpreting_outcome_text(self):
        evaluation = self._evaluation()

        result = evaluation.evaluate_locked_claim(
            self._payload(
                verification_state="not_matched",
                observed_actual="雖然發生別的工作事件，但 matched_if 定義的正式職責變動沒有發生。",
            )
        )

        self.assertEqual(result["evaluation"]["verification_state"], "not_matched")


if __name__ == "__main__":
    unittest.main()
