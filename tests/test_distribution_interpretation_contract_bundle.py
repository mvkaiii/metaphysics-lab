import json
import subprocess
import sys
import unittest
from pathlib import Path

from engine.distribution.evidence_ranker import rank_evidence
from engine.distribution.prospective import resolve_query_anchor
from engine.distribution.runtime import dispatch


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "dist" / "ai" / "metaphysics_lab.py"


def _feature(feature_id):
    return {
        "feature_id": feature_id,
        "system": "bazi",
        "scope": "yearly",
        "reference_window": {
            "scope": "yearly",
            "reference": "synthetic-phase5-bundle",
        },
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


def _ranking():
    return rank_evidence([_feature("career")], target_scope="yearly")


def _anchor():
    return resolve_query_anchor(
        {
            "query_anchor_at": "2026-08-28T16:00:00+08:00",
            "query_timezone": "Asia/Taipei",
            "target_start": "2026-08-01T00:00:00+08:00",
            "target_end": "2026-12-31T23:59:59+08:00",
            "question_reference": "synthetic-phase5-bundle",
        }
    )


def _bundle_request(action, payload):
    request = json.dumps(
        {"action": action, "payload": payload},
        ensure_ascii=False,
    )
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


class InterpretationContractBundleParityTests(unittest.TestCase):
    def test_contract_bundle_matches_modular_runtime_exactly(self):
        payload = {"base_ranking": _ranking(), "anchor": _anchor()}
        modular = dispatch("build_interpretation_contract", payload)
        portable = _bundle_request("build_interpretation_contract", payload)
        self.assertTrue(modular["ok"], modular)
        self.assertTrue(portable["ok"], portable)
        self.assertEqual(modular["data"], portable["data"])
        self.assertEqual(
            modular["data"]["interpretation_contract_digest"],
            portable["data"]["interpretation_contract_digest"],
        )

    def test_runtime_info_bundle_matches_phase5_capability_metadata(self):
        modular = dispatch("runtime_info", {})
        portable = _bundle_request("runtime_info", {})
        self.assertTrue(modular["ok"], modular)
        self.assertTrue(portable["ok"], portable)
        self.assertIn(
            "build_interpretation_contract",
            modular["data"]["supported_actions"],
        )
        self.assertIn(
            "build_interpretation_contract",
            portable["data"]["supported_actions"],
        )
        self.assertEqual(
            modular["data"]["capabilities"]["distribution.interpretation_contract"],
            portable["data"]["capabilities"]["distribution.interpretation_contract"],
        )


if __name__ == "__main__":
    unittest.main()
