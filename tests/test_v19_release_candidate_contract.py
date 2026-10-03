import unittest
from pathlib import Path

from engine.distribution.capabilities import get_capability as get_distribution_capability
from engine.distribution.constants import (
    CASE_SCHEMA_VERSION,
    DISTRIBUTION_RUNTIME_VERSION,
    PROJECT_CONTRACT_VERSION,
    RELEASE_VERSION,
    RUNTIME_SCHEMA_VERSION,
    SUPPORTED_ACTIONS,
)
from engine.distribution.runtime import dispatch
from engine.historical.capabilities import get_capability as get_historical_capability
from tools import build_release_package


ROOT = Path(__file__).resolve().parents[1]
RC_WORKFLOW = ROOT / ".github" / "workflows" / "v19-release-candidate-validation.yml"
QUALIFICATION = ROOT / "docs" / "release" / "v1.9.0-qualification.md"
EXPECTED_PACKAGE_SHA256 = "e263c25ea6efb8184a2d66c2bc2ce3edf31b29324152b2bccb9f96333aa504fa"


class V19ReleaseCandidateContractTests(unittest.TestCase):
    def test_v19_release_identity_and_schema_contract_are_frozen(self):
        self.assertEqual(RELEASE_VERSION, "1.9.0")
        self.assertEqual(DISTRIBUTION_RUNTIME_VERSION, "1.5-exp")
        self.assertEqual(PROJECT_CONTRACT_VERSION, "1.3")
        self.assertEqual(RUNTIME_SCHEMA_VERSION, "1.1")
        self.assertEqual(CASE_SCHEMA_VERSION, "1.1")
        self.assertEqual(
            build_release_package.USER_PACKAGE_NAME,
            "Metaphysics-Lab-v1.9.0-User-Package.zip",
        )
        self.assertEqual(
            set(build_release_package.USER_ASSETS),
            {"metaphysics_core.md", "metaphysics_lab.py", "project_instructions.txt"},
        )

    def test_v19_release_surface_contains_completed_candidate_slices(self):
        required = {
            "natal.candidate_envelope",
            "natal.guided_build_state",
            "render_candidate_envelope_summary",
            "case.base_digest",
            "case.replace_natal_base",
            "lock_prospective_forecast",
            "lock_blind_forecast",
            "lock_historical_calibration",
        }
        self.assertTrue(required.issubset(set(SUPPORTED_ACTIONS)))

        info = dispatch("runtime_info", {})
        self.assertTrue(info["ok"], info)
        caps = info["data"]["capabilities"]
        for capability_id in (
            "natal.candidate_envelope",
            "distribution.case_revision_integrity",
            "distribution.lock_provenance",
            "distribution.guided_natal_build",
            "distribution.candidate_envelope_visualization",
        ):
            cap = caps[capability_id]
            self.assertEqual(cap["implementation"], "implemented")
            self.assertEqual(cap["maturity"], "experimental")
            self.assertEqual(cap["routing"], "on_demand")

        self.assertFalse(
            caps["distribution.candidate_envelope_visualization"]["ranking_authority"]
        )

    def test_prediction_and_default_profiles_remain_frozen(self):
        prospective = get_distribution_capability(
            "distribution.prospective_forecast_governance"
        )
        self.assertEqual(prospective["rule_version"], "lin_tianji_v1.5-exp")

        interpretation = get_distribution_capability(
            "distribution.interpretation_contract"
        )
        self.assertEqual(
            interpretation["rule_version"],
            "lin_tianji_interpretation_contract_v1-exp",
        )

        selector = get_historical_capability("historical.activation_selector")
        self.assertEqual(selector["profile_id"], "historical-activation-bazi-v1")
        self.assertEqual(selector["rule_version"], "1.0-exp")

    def test_rc_workflow_is_read_only_fail_closed_and_digest_bound(self):
        self.assertTrue(RC_WORKFLOW.is_file(), "v1.9 RC workflow is missing")
        text = RC_WORKFLOW.read_text(encoding="utf-8")
        for required in (
            "name: Metaphysics Lab v1.9 Release Candidate Validation",
            "permissions:\n  contents: read",
            "Checkout exact candidate",
            'test "$(git rev-parse HEAD)" = "$CANDIDATE_SHA"',
            "tests.test_v19_release_candidate_contract",
            "tests.test_v19_visualization_p1_candidate_envelope",
            "tests.test_v19_instructions_core_integration",
            "python tools/build_ai_distribution.py --check",
            "python tools/run_v17_release_surface_validation.py --json",
            "python -m unittest discover -s tests -p 'test_*.py' -v",
            "Build deterministic v1.9.0 User Package twice and verify frozen digest",
            EXPECTED_PACKAGE_SHA256,
            "Private outcome contamination scan",
            '"release_authorized": False',
        ):
            self.assertIn(required, text)
        for forbidden in (
            "contents: write",
            "gh release create",
            "git tag",
            "promote_to_stable",
            "switch_default",
        ):
            self.assertNotIn(forbidden, text)

    def test_rc_qualification_receipt_preserves_authorization_boundary(self):
        self.assertTrue(QUALIFICATION.is_file(), "v1.9 qualification receipt is missing")
        text = QUALIFICATION.read_text(encoding="utf-8")
        for required in (
            "status: RC_FROZEN_RELEASE_NOT_AUTHORIZED",
            "release_version: v1.9.0",
            "distribution_runtime_version: 1.5-exp",
            "project_contract_version: 1.3",
            "runtime_schema_version: 1.1",
            "case_schema_version: 1.1",
            EXPECTED_PACKAGE_SHA256,
            "Fresh-host qualification",
            "Stable promotion: NOT INCLUDED",
            "default switch: NOT INCLUDED",
            "merge",
            "tag",
            "GitHub Release",
            "publish",
        ):
            self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
