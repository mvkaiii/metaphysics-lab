import unittest

from engine.distribution.claim_authority_manifest import build_claim_authority_manifest
from engine.distribution.errors import DistributionError
from engine.distribution.event_family_attribution import build_event_family_attribution_bundle
from engine.distribution.evidence_ranker import rank_evidence
from engine.distribution.prospective_arm_freeze import build_prospective_arm_freeze
from engine.distribution.prospective_window_scope import resolve_prospective_window_scope
from tests.test_distribution_claim_evidence import feature, structural


def _q4_anchor():
    return {
        "query_anchor_at": "2026-09-03T15:30:00+08:00",
        "query_timezone": "Asia/Taipei",
        "knowledge_cutoff_at": "2026-09-03T15:30:00+08:00",
        "prospective_window_start": "2026-10-01T00:00:00+08:00",
        "prospective_window_end": "2026-12-31T23:59:59+08:00",
        "question_reference": "synthetic-prospective-arm-freeze",
        "status": "ok",
    }


class ProspectiveArmFreezeTests(unittest.TestCase):
    def _fixture(self):
        features = [
            feature(
                "b-career",
                system="bazi",
                domain="career",
                role="target_evidence",
                scope="yearly",
                families=("role_change", "responsibility_shift"),
                dependency="b-career",
            ),
            feature(
                "z-career",
                system="ziwei",
                domain="career",
                role="target_evidence",
                scope="yearly",
                families=("role_change", "responsibility_shift"),
                dependency="z-career",
            ),
        ]
        ranking = rank_evidence(features, target_scope="yearly")
        interpretation = structural(features)
        scope_policy = resolve_prospective_window_scope(
            {
                "window_start": "2026-10-01T00:00:00+08:00",
                "window_end": "2026-12-31T23:59:59+08:00",
                "timezone": "Asia/Taipei",
            }
        )
        claim_authority = build_claim_authority_manifest(
            {
                "scope_policy": scope_policy,
                "structural_candidate_authority": {
                    "authority_profile": "synthetic-y1-authority",
                    "authority_digest": "1" * 64,
                },
                "mapping_profile": "lin_tianji_domain_v2-exp",
                "phase3_authority": {
                    "policy_profile": "synthetic-phase3",
                    "policy_digest": "2" * 64,
                },
                "efa_authority": {
                    "profile_version": "lin_tianji_event_family_attribution_v1-exp",
                    "authority_digest": "3" * 64,
                },
                "resolved_target_scope": "yearly",
                "promotion_allowed": False,
            }
        )
        efa = build_event_family_attribution_bundle(
            base_ranking=ranking,
            structural_interpretation=interpretation,
        )
        locked_ids = [row["child_claim_id"] for row in efa["children"]]
        return {
            "opaque_case_id": "case-synthetic-arm-freeze",
            "sealed_at": "2026-09-03T15:30:00+08:00",
            "scope_policy": scope_policy,
            "claim_authority_manifest": claim_authority,
            "forecast_context_digest": interpretation["source_context_digest"],
            "base_ranking": ranking,
            "structural_interpretation": interpretation,
            "anchor": _q4_anchor(),
            "locked_claim_ids": locked_ids,
            "s1_provenance": {
                "composite_claim_authority_digest": "4" * 64,
                "claim_universe_digest": "5" * 64,
                "sampling_frame_digest": "6" * 64,
                "sampling_receipt_digest": "7" * 64,
            },
        }

    def test_builds_both_arms_from_one_source_and_preserves_exact_s1_universe(self):
        payload = self._fixture()
        result = build_prospective_arm_freeze(payload)

        self.assertEqual(result["status"], "WAITING_FOR_OUTCOME")
        self.assertTrue(result["outcome_blind"])
        self.assertEqual(result["oracle_status"], "NOT_CREATED")
        self.assertEqual(result["scoring_status"], "NOT_PERFORMED")
        self.assertEqual(result["retuning_status"], "PROHIBITED")
        self.assertFalse(result["promotion_allowed"])
        self.assertEqual(result["target_scope"], "yearly")
        self.assertEqual(result["timing_scopes"], ["monthly"])

        locked = set(payload["locked_claim_ids"])
        legacy_ids = {row["child_claim_id"] for row in result["legacy_arm"]["children"]}
        candidate_ids = {
            row["child_claim_id"]
            for field in ("children", "audit_only_children")
            for row in result["candidate_arm"][field]
        }
        self.assertEqual(legacy_ids, locked)
        self.assertEqual(candidate_ids, locked)
        self.assertEqual(result["legacy_universe_validation"]["status"], "valid")
        self.assertEqual(result["candidate_universe_validation"]["status"], "valid")
        self.assertEqual(
            result["source_forecast_context_digest"],
            result["structural_interpretation_source_context_digest"],
        )
        self.assertTrue(result["arm_freeze_digest"])

    def test_is_byte_semantically_deterministic_for_same_explicit_seal_time(self):
        payload = self._fixture()
        self.assertEqual(
            build_prospective_arm_freeze(payload),
            build_prospective_arm_freeze(payload),
        )

    def test_rejects_any_outcome_or_post_lock_scoring_field(self):
        for field in (
            "outcome",
            "oracle",
            "historical_records",
            "verified_events",
            "legacy_score",
            "candidate_score",
            "q1_result",
            "t1_result",
        ):
            with self.subTest(field=field):
                payload = self._fixture()
                payload[field] = {}
                with self.assertRaises(DistributionError) as caught:
                    build_prospective_arm_freeze(payload)
                self.assertEqual(caught.exception.code, "invalid_prospective_arm_freeze")

    def test_fails_closed_on_s1_universe_or_source_context_mismatch(self):
        payload = self._fixture()
        payload["locked_claim_ids"] = payload["locked_claim_ids"][:-1]
        with self.assertRaises(DistributionError):
            build_prospective_arm_freeze(payload)

        payload = self._fixture()
        payload["forecast_context_digest"] = "f" * 64
        with self.assertRaises(DistributionError) as caught:
            build_prospective_arm_freeze(payload)
        self.assertEqual(caught.exception.code, "invalid_prospective_arm_freeze")

    def test_seal_must_be_offset_aware_and_strictly_before_outcome_window(self):
        for sealed_at in (
            "2026-09-03T15:30:00",
            "2026-10-01T00:00:00+08:00",
            "2026-10-01T00:00:01+08:00",
        ):
            with self.subTest(sealed_at=sealed_at):
                payload = self._fixture()
                payload["sealed_at"] = sealed_at
                with self.assertRaises(DistributionError) as caught:
                    build_prospective_arm_freeze(payload)
                self.assertEqual(caught.exception.code, "invalid_prospective_arm_freeze")

    def test_anchor_cutoff_and_query_must_not_extend_past_seal(self):
        for field in ("knowledge_cutoff_at", "query_anchor_at"):
            with self.subTest(field=field):
                payload = self._fixture()
                payload["anchor"][field] = "2026-09-03T15:30:01+08:00"
                with self.assertRaises(DistributionError) as caught:
                    build_prospective_arm_freeze(payload)
                self.assertEqual(caught.exception.code, "invalid_prospective_arm_freeze")

    def test_anchor_must_bind_exact_scoring_window_and_timezone(self):
        mutations = (
            ("prospective_window_start", "2026-10-02T00:00:00+08:00"),
            ("prospective_window_end", "2026-12-30T23:59:59+08:00"),
            ("query_timezone", "Asia/Tokyo"),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                payload = self._fixture()
                payload["anchor"][field] = value
                with self.assertRaises(DistributionError) as caught:
                    build_prospective_arm_freeze(payload)
                self.assertEqual(caught.exception.code, "invalid_prospective_arm_freeze")


if __name__ == "__main__":
    unittest.main()
