import json
import subprocess
import sys
import unittest
from pathlib import Path

from engine.distribution.evidence_ranker import rank_evidence
from engine.distribution.runtime import dispatch


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "dist" / "ai" / "metaphysics_lab.py"


def _feature(feature_id, **overrides):
    payload = {
        "feature_id": feature_id,
        "system": "bazi",
        "scope": "yearly",
        "reference_window": {"scope": "yearly", "reference": "phase4-bundle-fixture"},
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


def _base_ranking():
    return rank_evidence(
        [
            _feature("career"),
            _feature(
                "finance",
                primary_domain="finance",
                event_family_support=["earned_income", "resource_management"],
                strength_class="weak",
            ),
        ],
        target_scope="yearly",
    )


def _record(year, record_id):
    return {
        "record_id": record_id,
        "record_type": "historical_calibration",
        "calibration_id": "HC-BUNDLE",
        "origin": "canonical",
        "blind_prediction": {
            "predicted_flow_year": year,
            "role": "high_activation",
            "primary_domains": ["career"],
            "event_family": ["role_change"],
            "blindness_status": "blind",
            "hypothesis": "synthetic text excluded from personalization identity",
        },
        "evaluation": {
            "verification_state": "matched",
            "domain_status": "matched",
            "event_form_status": "matched",
            "timing_status": "exact_flow_year",
            "offset_flow_years": 0,
            "boundary_ambiguity": False,
        },
        "user_confirmed_actual": {
            "actual_event": "synthetic outcome text excluded from personalization identity",
            "actual_date": "%04d-06-01" % year,
        },
    }


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


class HistoricalPersonalizationBundleParityTests(unittest.TestCase):
    def assert_bundle_parity(self, request):
        modular = dispatch("personalize_ranking", request)
        portable = _bundle_request("personalize_ranking", request)
        self.assertEqual(portable, modular)
        self.assertEqual(
            portable["data"]["personalization_digest"],
            modular["data"]["personalization_digest"],
        )
        self.assertEqual(
            portable["data"]["base_ranking_digest"],
            modular["data"]["base_ranking_digest"],
        )
        return portable

    def test_no_history_bundle_matches_modular_runtime_exactly(self):
        result = self.assert_bundle_parity(
            {
                "base_ranking": _base_ranking(),
                "historical_calibration_status": "basic",
                "historical_records": [],
            }
        )
        self.assertEqual(result["data"]["personalization_status"], "no_op")

    def test_applied_personalization_bundle_matches_modular_runtime_exactly(self):
        result = self.assert_bundle_parity(
            {
                "base_ranking": _base_ranking(),
                "historical_calibration_status": "basic",
                "historical_records": [
                    _record(2020, "HC-BUNDLE-2020"),
                    _record(2021, "HC-BUNDLE-2021"),
                ],
            }
        )
        self.assertEqual(result["data"]["personalization_status"], "applied")
        career = next(
            row for row in result["data"]["domains"] if row["primary_domain"] == "career"
        )
        self.assertEqual(career["historical_modifier_scaled"], 2)
        self.assertEqual(career["preferred_event_families"], ["role_change"])


if __name__ == "__main__":
    unittest.main()
