import copy
import unittest

from engine.distribution.errors import DistributionError
from engine.distribution.evidence_ranker import rank_evidence
from engine.distribution.prospective import resolve_query_anchor


def feature(feature_id, domain="career", families=None, scope="yearly", **overrides):
    payload = {
        "feature_id": feature_id,
        "system": "bazi",
        "scope": scope,
        "reference_window": {"scope": scope, "reference": "fixture"},
        "primary_domain": domain,
        "event_family_support": list(families or ["role_change"]),
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


def anchor():
    return resolve_query_anchor({
        "query_anchor_at": "2026-08-28T16:00:00+08:00",
        "query_timezone": "Asia/Taipei",
        "target_start": "2026-08-01T00:00:00+08:00",
        "target_end": "2026-12-31T23:59:59+08:00",
        "question_reference": "synthetic-phase5",
    })


def yearly_ranking():
    return rank_evidence([
        feature("career", "career", ["role_change", "responsibility"]),
        feature("finance", "finance", ["resource_shift"]),
        feature("relationship", "relationship", ["one_to_one_change"]),
        feature("family", "family", ["family_responsibility"]),
    ], target_scope="yearly")


class InterpretationContractTests(unittest.TestCase):
    def test_cold_start_contract_keeps_phase3_authority_and_primary_limit(self):
        from engine.distribution.interpretation_contract import build_interpretation_contract

        ranking = yearly_ranking()
        result = build_interpretation_contract(ranking, anchor())
        self.assertEqual(
            result["profile_version"],
            "lin_tianji_interpretation_contract_v1-exp",
        )
        self.assertEqual(result["base_ranking_digest"], ranking["ranking_digest"])
        self.assertIsNone(result["personalization_digest"])
        self.assertEqual(result["personalization_status"], "not_provided")
        self.assertEqual(len(result["primary_domains"]), 3)
        self.assertEqual(len(result["secondary_domains"]), 1)
        self.assertEqual(
            [row["primary_domain"] for row in result["domain_interpretation"]],
            ranking["opened_domains"],
        )
        for row in result["domain_interpretation"]:
            self.assertEqual(row["base_rank"], row["presentation_rank"])
            self.assertEqual(
                row["base_allowed_specificity"],
                row["effective_specificity"],
            )
            self.assertFalse(row["personalization_applied"])

    def test_same_canonical_input_produces_same_contract_digest(self):
        from engine.distribution.interpretation_contract import build_interpretation_contract

        first = build_interpretation_contract(yearly_ranking(), anchor())
        second = build_interpretation_contract(yearly_ranking(), anchor())
        self.assertEqual(first, second)
        self.assertEqual(
            first["interpretation_contract_digest"],
            second["interpretation_contract_digest"],
        )

    def test_base_ranking_digest_mismatch_fails_closed(self):
        from engine.distribution.interpretation_contract import build_interpretation_contract

        ranking = copy.deepcopy(yearly_ranking())
        ranking["domains"][0]["rank"] = 99
        with self.assertRaises(DistributionError) as caught:
            build_interpretation_contract(ranking, anchor())
        self.assertEqual(caught.exception.code, "invalid_interpretation_contract")
        self.assertIn("digest", str(caught.exception).lower())


if __name__ == "__main__":
    unittest.main()
