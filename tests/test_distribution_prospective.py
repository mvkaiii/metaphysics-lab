import importlib
import importlib.util
import unittest
from datetime import datetime, timedelta

from engine.distribution.errors import DistributionError


class DistributionProspectiveQueryAnchorTests(unittest.TestCase):
    def _prospective(self):
        spec = importlib.util.find_spec("engine.distribution.prospective")
        self.assertIsNotNone(
            spec,
            "Phase 1 requires engine.distribution.prospective before Query Anchor can resolve",
        )
        return importlib.import_module("engine.distribution.prospective")

    @staticmethod
    def _payload(**overrides):
        payload = {
            "query_anchor_at": "2026-08-26T17:00:00+08:00",
            "query_timezone": "Asia/Taipei",
            "target_start": "2026-08-01T00:00:00+08:00",
            "target_end": "2026-12-31T23:59:59+08:00",
            "question_reference": "kai-2026-second-half",
        }
        payload.update(overrides)
        return payload

    def test_anchor_inside_target_truncates_window_to_immediately_after_cutoff(self):
        prospective = self._prospective()
        result = prospective.resolve_query_anchor(self._payload())

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["query_anchor_at"], "2026-08-26T17:00:00+08:00")
        self.assertEqual(result["query_timezone"], "Asia/Taipei")
        self.assertEqual(result["knowledge_cutoff_at"], result["query_anchor_at"])
        self.assertEqual(result["question_reference"], "kai-2026-second-half")
        self.assertEqual(
            datetime.fromisoformat(result["prospective_window_start"]),
            datetime.fromisoformat(result["knowledge_cutoff_at"]) + timedelta(microseconds=1),
        )
        self.assertEqual(
            result["prospective_window_end"],
            "2026-12-31T23:59:59+08:00",
        )

    def test_anchor_before_target_preserves_full_target_window(self):
        prospective = self._prospective()
        result = prospective.resolve_query_anchor(
            self._payload(
                query_anchor_at="2026-07-15T09:30:00+08:00",
                target_start="2026-08-01T00:00:00+08:00",
            )
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["prospective_window_start"], "2026-08-01T00:00:00+08:00")
        self.assertEqual(result["prospective_window_end"], "2026-12-31T23:59:59+08:00")

    def test_anchor_at_or_after_target_end_has_no_prospective_window(self):
        prospective = self._prospective()
        for anchor in (
            "2026-12-31T23:59:59+08:00",
            "2027-01-01T00:00:00+08:00",
        ):
            with self.subTest(anchor=anchor):
                result = prospective.resolve_query_anchor(self._payload(query_anchor_at=anchor))
                self.assertEqual(result["status"], "no_prospective_window")
                self.assertIsNone(result["prospective_window_start"])
                self.assertIsNone(result["prospective_window_end"])
                self.assertEqual(result["knowledge_cutoff_at"], anchor)

    def test_query_anchor_rejects_naive_datetimes_instead_of_guessing_timezone(self):
        prospective = self._prospective()
        for field in ("query_anchor_at", "target_start", "target_end"):
            with self.subTest(field=field):
                payload = self._payload()
                payload[field] = payload[field].split("+")[0]
                with self.assertRaises(DistributionError) as caught:
                    prospective.resolve_query_anchor(payload)
                self.assertEqual(caught.exception.code, "invalid_query_anchor")

    def test_query_anchor_rejects_offset_that_does_not_match_declared_timezone(self):
        prospective = self._prospective()
        for field in ("query_anchor_at", "target_start", "target_end"):
            with self.subTest(field=field):
                payload = self._payload()
                payload[field] = "2026-08-26T17:00:00+00:00"
                with self.assertRaises(DistributionError) as caught:
                    prospective.resolve_query_anchor(payload)
                self.assertEqual(caught.exception.code, "invalid_query_anchor")

    def test_query_anchor_rejects_invalid_range_or_blank_reference(self):
        prospective = self._prospective()
        invalid_payloads = (
            self._payload(
                target_start="2026-12-31T23:59:59+08:00",
                target_end="2026-08-01T00:00:00+08:00",
            ),
            self._payload(question_reference="   "),
        )
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                with self.assertRaises(DistributionError) as caught:
                    prospective.resolve_query_anchor(payload)
                self.assertEqual(caught.exception.code, "invalid_query_anchor")

    def test_query_anchor_does_not_accept_activation_or_change_metaphysical_strength(self):
        prospective = self._prospective()
        payload = self._payload(activation="high")
        with self.assertRaises(DistributionError) as caught:
            prospective.resolve_query_anchor(payload)
        self.assertEqual(caught.exception.code, "invalid_query_anchor")


class DistributionProspectiveClaimTests(unittest.TestCase):
    @staticmethod
    def _prospective():
        return importlib.import_module("engine.distribution.prospective")

    def _anchor(self):
        prospective = self._prospective()
        return prospective.resolve_query_anchor(
            {
                "query_anchor_at": "2026-08-26T17:00:00+08:00",
                "query_timezone": "Asia/Taipei",
                "target_start": "2026-08-01T00:00:00+08:00",
                "target_end": "2026-12-31T23:59:59+08:00",
                "question_reference": "prospective-holdout-2026-h2",
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

    def test_claim_requires_nonblank_matched_and_not_matched_conditions(self):
        prospective = self._prospective()
        anchor = self._anchor()
        cases = (
            {"matched_if": ""},
            {"matched_if": "   "},
            {"not_matched_if": ""},
            {"not_matched_if": "   "},
        )
        for override in cases:
            with self.subTest(override=override):
                with self.assertRaises(DistributionError) as caught:
                    prospective.validate_forecast_claim(self._claim(**override), anchor)
                self.assertEqual(caught.exception.code, "invalid_forecast_claim")

    def test_clean_prospective_claim_cannot_cover_time_at_or_before_cutoff(self):
        prospective = self._prospective()
        anchor = self._anchor()
        with self.assertRaises(DistributionError) as caught:
            prospective.validate_forecast_claim(
                self._claim(
                    forecast_window={
                        "start": "2026-08-20T00:00:00+08:00",
                        "end": "2026-09-01T00:00:00+08:00",
                    }
                ),
                anchor,
            )
        self.assertEqual(caught.exception.code, "invalid_forecast_claim")

    def test_known_or_partially_known_claim_cannot_be_clean_scorable(self):
        prospective = self._prospective()
        anchor = self._anchor()
        for contamination_state in ("known_before_lock", "partially_known"):
            with self.subTest(contamination_state=contamination_state):
                with self.assertRaises(DistributionError) as caught:
                    prospective.validate_forecast_claim(
                        self._claim(contamination_state=contamination_state),
                        anchor,
                    )
                self.assertEqual(caught.exception.code, "invalid_forecast_claim")

    def test_known_before_lock_may_be_preserved_only_as_excluded_context(self):
        prospective = self._prospective()
        anchor = self._anchor()
        validated = prospective.validate_forecast_claim(
            self._claim(
                contamination_state="known_before_lock",
                evaluation_eligibility="excluded_from_clean_accuracy",
            ),
            anchor,
        )
        self.assertEqual(validated["contamination_state"], "known_before_lock")
        self.assertEqual(validated["evaluation_eligibility"], "excluded_from_clean_accuracy")

    def test_claim_rejects_unsupported_confidence_maturity_contamination_and_method_version(self):
        prospective = self._prospective()
        anchor = self._anchor()
        cases = (
            {"confidence": "certain"},
            {"capability_maturity": "qualified"},
            {"contamination_state": "probably_clean"},
            {"evaluation_eligibility": "maybe"},
            {"method_version": "lin_tianji_v1.5-stable"},
        )
        for override in cases:
            with self.subTest(override=override):
                with self.assertRaises(DistributionError) as caught:
                    prospective.validate_forecast_claim(self._claim(**override), anchor)
                self.assertEqual(caught.exception.code, "invalid_forecast_claim")

    def test_lock_rejects_duplicate_claim_ids(self):
        prospective = self._prospective()
        anchor = self._anchor()
        claim = self._claim()
        duplicate = self._claim(prediction="同一 ID 的另一段預測不得混入同一 lock。")
        with self.assertRaises(DistributionError) as caught:
            prospective.lock_prospective_forecast(
                {"anchor": anchor, "claims": [claim, duplicate]}
            )
        self.assertEqual(caught.exception.code, "invalid_prospective_forecast")

    def test_lock_is_deterministic_immutable_and_contains_no_outcome_fields(self):
        prospective = self._prospective()
        anchor = self._anchor()
        payload = {"anchor": anchor, "claims": [self._claim()]}

        first = prospective.lock_prospective_forecast(payload)
        second = prospective.lock_prospective_forecast(payload)

        self.assertEqual(first, second)
        self.assertEqual(first["status"], "locked")
        self.assertEqual(first["method_version"], "lin_tianji_v1.5-exp")
        self.assertEqual(len(first["canonical_digest"]), 64)
        self.assertEqual(first["claims"][0]["claim_id"], "claim-2026-09-work-001")
        serialized = repr(first)
        self.assertNotIn("observed_actual", serialized)
        self.assertNotIn("evaluation", serialized)
        self.assertNotIn("failure_mode", serialized)

    def test_claim_rejects_outcome_fields_at_lock_time(self):
        prospective = self._prospective()
        anchor = self._anchor()
        for forbidden in ("observed_actual", "evaluation", "failure_mode"):
            with self.subTest(forbidden=forbidden):
                claim = self._claim(**{forbidden: "premature"})
                with self.assertRaises(DistributionError) as caught:
                    prospective.validate_forecast_claim(claim, anchor)
                self.assertEqual(caught.exception.code, "invalid_forecast_claim")


if __name__ == "__main__":
    unittest.main()
