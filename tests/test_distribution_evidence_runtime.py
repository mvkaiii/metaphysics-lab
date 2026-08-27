import json
import subprocess
import sys
import unittest
from pathlib import Path

from engine.distribution.capabilities import should_run_by_default
from engine.distribution.runtime import dispatch


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "dist" / "ai" / "metaphysics_lab.py"


def _feature(feature_id, **overrides):
    payload = {
        "feature_id": feature_id,
        "system": "bazi",
        "scope": "yearly",
        "reference_window": {"scope": "yearly", "reference": "synthetic"},
        "primary_domain": "career",
        "event_family_support": ["formal_role"],
        "strength_class": "moderate",
        "maturity": "stable",
        "qualification_status": "qualified",
        "source_family": "synthetic.bazi",
        "dependency_family": "dep:" + feature_id,
        "role": "target_evidence",
        "provenance": {"fixture": feature_id},
    }
    payload.update(overrides)
    return payload


def _bundle_request(action, payload):
    request = json.dumps({"action": action, "payload": payload}, ensure_ascii=False)
    completed = subprocess.run(
        [sys.executable, str(BUNDLE), "request", "--input", "-"],
        cwd=str(ROOT),
        input=request,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stdout + completed.stderr)
    return json.loads(completed.stdout)


class EvidenceRuntimeActionTests(unittest.TestCase):
    def test_rank_evidence_is_experimental_on_demand_portable_action(self):
        info = dispatch("runtime_info", {})
        self.assertTrue(info["ok"], info)
        self.assertIn("rank_evidence", info["data"]["supported_actions"])
        capability = info["data"]["capabilities"]["distribution.evidence_engine"]
        self.assertEqual(capability["implementation"], "implemented")
        self.assertEqual(capability["maturity"], "experimental")
        self.assertEqual(capability["routing"], "on_demand")
        self.assertFalse(should_run_by_default("distribution.evidence_engine"))

        result = dispatch(
            "rank_evidence",
            {"features": [_feature("year-career")], "target_scope": "yearly"},
        )
        self.assertTrue(result["ok"], result)
        summary = result["data"]
        self.assertEqual(summary["capability_id"], "distribution.evidence_engine")
        self.assertEqual(summary["maturity"], "experimental")
        self.assertEqual(summary["routing"], "on_demand")
        self.assertEqual(summary["ranking"]["opened_domains"], ["career"])
        self.assertEqual(summary["local_windows"], [])
        self.assertIn("ranking_digest", summary["ranking"])

    def test_synthetic_boundary_matrix_enforces_phase3_specificity_and_ownership(self):
        matrix = [
            {
                "name": "strong_decadal_modifier_cannot_open_yearly_finance",
                "payload": {
                    "target_scope": "yearly",
                    "features": [
                        _feature("year-career", strength_class="weak"),
                        _feature(
                            "decade-finance",
                            scope="decadal",
                            reference_window={"scope": "decadal", "reference": "synthetic"},
                            primary_domain="finance",
                            event_family_support=["income_assets"],
                            strength_class="strong",
                            role="modifier",
                        ),
                    ],
                },
                "opened_domains": ["career"],
                "specificity": "event_family",
            },
            {
                "name": "experimental_independent_targets_stop_at_event_family",
                "payload": {
                    "target_scope": "yearly",
                    "features": [
                        _feature("exp-a", maturity="experimental", dependency_family="dep:exp-a"),
                        _feature(
                            "exp-b",
                            system="ziwei",
                            source_family="synthetic.ziwei",
                            maturity="experimental",
                            dependency_family="dep:exp-b",
                        ),
                    ],
                },
                "opened_domains": ["career"],
                "specificity": "event_family",
            },
            {
                "name": "stable_independent_targets_can_reach_concrete_event",
                "payload": {
                    "target_scope": "yearly",
                    "features": [
                        _feature("stable-a", dependency_family="dep:stable-a"),
                        _feature(
                            "stable-b",
                            system="ziwei",
                            source_family="synthetic.ziwei",
                            dependency_family="dep:stable-b",
                        ),
                    ],
                },
                "opened_domains": ["career"],
                "specificity": "concrete_event",
            },
            {
                "name": "correlated_targets_do_not_gain_independent_convergence",
                "payload": {
                    "target_scope": "yearly",
                    "features": [
                        _feature("corr-a", dependency_family="dep:shared"),
                        _feature(
                            "corr-b",
                            system="ziwei",
                            source_family="synthetic.ziwei",
                            dependency_family="dep:shared",
                        ),
                    ],
                },
                "opened_domains": ["career"],
                "specificity": "event_family",
                "independent_dependency_count": 1,
            },
        ]

        for case in matrix:
            with self.subTest(case=case["name"]):
                result = dispatch("rank_evidence", case["payload"])
                self.assertTrue(result["ok"], result)
                ranking = result["data"]["ranking"]
                self.assertEqual(ranking["opened_domains"], case["opened_domains"])
                self.assertEqual(ranking["domains"][0]["allowed_specificity"], case["specificity"])
                if "independent_dependency_count" in case:
                    self.assertEqual(
                        ranking["domains"][0]["independent_dependency_count"],
                        case["independent_dependency_count"],
                    )

    def test_runtime_summary_exposes_local_spike_without_rewriting_parent(self):
        parent_result = dispatch(
            "rank_evidence",
            {
                "target_scope": "yearly",
                "features": [_feature("year-weak", strength_class="weak")],
            },
        )
        self.assertTrue(parent_result["ok"], parent_result)
        parent = parent_result["data"]["ranking"]
        parent_bytes = json.dumps(parent, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

        child_result = dispatch(
            "rank_evidence",
            {
                "target_scope": "monthly",
                "features": [
                    _feature(
                        "month-strong",
                        scope="monthly",
                        reference_window={"scope": "monthly", "reference": "synthetic"},
                        strength_class="strong",
                    )
                ],
                "parent_ranking": parent,
            },
        )
        self.assertTrue(child_result["ok"], child_result)
        windows = child_result["data"]["local_windows"]
        self.assertEqual(len(windows), 1)
        self.assertTrue(windows[0]["local_spike"])
        self.assertEqual(windows[0]["parent_ranking_digest"], parent["ranking_digest"])
        self.assertEqual(
            windows[0]["child_ranking_digest"],
            child_result["data"]["ranking"]["ranking_digest"],
        )
        self.assertEqual(
            json.dumps(parent, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            parent_bytes,
        )

    def test_portable_bundle_matches_modular_ranked_evidence_summary(self):
        payload = {
            "target_scope": "yearly",
            "features": [
                _feature("bazi-career", dependency_family="dep:bazi"),
                _feature(
                    "ziwei-career",
                    system="ziwei",
                    source_family="synthetic.ziwei",
                    dependency_family="dep:ziwei",
                ),
            ],
        }
        modular = dispatch("rank_evidence", payload)
        bundled = _bundle_request("rank_evidence", payload)
        self.assertEqual(bundled, modular)
        self.assertTrue(modular["ok"], modular)
        self.assertEqual(modular["data"]["ranking"]["opened_domains"], ["career"])
        self.assertEqual(
            modular["data"]["ranking"]["domains"][0]["allowed_specificity"],
            "concrete_event",
        )


if __name__ == "__main__":
    unittest.main()
