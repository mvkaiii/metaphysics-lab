import unittest

from engine.distribution.evidence_ranker import rank_evidence
from engine.distribution.prospective import resolve_query_anchor
from engine.distribution.runtime import dispatch, runtime_info


def feature(feature_id):
    return {
        "feature_id": feature_id,
        "system": "bazi",
        "scope": "yearly",
        "reference_window": {"scope": "yearly", "reference": "fixture"},
        "primary_domain": "career",
        "event_family_support": ["role_change"],
        "strength_class": "moderate",
        "maturity": "stable",
        "qualification_status": "qualified",
        "source_family": "fixture.bazi",
        "dependency_family": "dep:" + feature_id,
        "role": "target_evidence",
        "provenance": {"fixture": feature_id},
    }


def ranking():
    return rank_evidence([feature("career")], target_scope="yearly")


def anchor():
    return resolve_query_anchor({
        "query_anchor_at": "2026-08-28T16:00:00+08:00",
        "query_timezone": "Asia/Taipei",
        "target_start": "2026-08-01T00:00:00+08:00",
        "target_end": "2026-12-31T23:59:59+08:00",
        "question_reference": "synthetic-phase5-runtime",
    })


class InterpretationContractRuntimeTests(unittest.TestCase):
    def test_runtime_info_exposes_phase5_capability_and_action(self):
        info = runtime_info()
        self.assertIn("build_interpretation_contract", info["supported_actions"])
        cap = info["capabilities"]["distribution.interpretation_contract"]
        self.assertEqual(cap["implementation"], "implemented")
        self.assertEqual(cap["maturity"], "experimental")
        self.assertEqual(cap["routing"], "on_demand")
        self.assertEqual(
            cap["rule_version"],
            "lin_tianji_interpretation_contract_v1-exp",
        )
        self.assertFalse(cap["ranking_authority"])
        self.assertEqual(cap["dependencies"], ["distribution.evidence_engine"])

    def test_dispatch_build_interpretation_contract_returns_core_result(self):
        response = dispatch(
            "build_interpretation_contract",
            {"base_ranking": ranking(), "anchor": anchor()},
        )
        self.assertTrue(response["ok"], response)
        self.assertEqual(response["action"], "build_interpretation_contract")
        self.assertEqual(
            response["data"]["profile_version"],
            "lin_tianji_interpretation_contract_v1-exp",
        )

    def test_dispatch_rejects_unknown_reality_or_research_fields(self):
        response = dispatch(
            "build_interpretation_contract",
            {
                "base_ranking": ranking(),
                "anchor": anchor(),
                "reality_context": "not canonical input",
                "research_notes": "not canonical input",
            },
        )
        self.assertFalse(response["ok"])
        self.assertEqual(
            response["error"]["code"],
            "invalid_interpretation_contract",
        )
        self.assertEqual(
            response["error"]["details"]["unknown_fields"],
            ["reality_context", "research_notes"],
        )

    def test_dispatch_requires_base_ranking_and_anchor(self):
        response = dispatch("build_interpretation_contract", {})
        self.assertFalse(response["ok"])
        self.assertEqual(
            response["error"]["code"],
            "invalid_interpretation_contract",
        )
        self.assertEqual(
            response["error"]["details"]["missing_fields"],
            ["anchor", "base_ranking"],
        )


if __name__ == "__main__":
    unittest.main()
