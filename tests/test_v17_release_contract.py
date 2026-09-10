import unittest
from pathlib import Path

from engine.distribution.capabilities import get_capability as get_distribution_capability
from engine.distribution.constants import (
    CASE_SCHEMA_VERSION,
    DISTRIBUTION_RUNTIME_VERSION,
    PROJECT_CONTRACT_VERSION,
    RUNTIME_SCHEMA_VERSION,
    SUPPORTED_ACTIONS,
)
from engine.historical.capabilities import get_capability as get_historical_capability
from tests.test_v17_prospective_validation_compatibility import (
    FROZEN_V15_DIGEST,
    ProspectiveValidationCompatibilityTests,
)
from tools import build_release_package

ROOT = Path(__file__).resolve().parents[1]

V16_PUBLIC_ACTIONS = frozenset((
    "runtime_info",
    "subject.create_identity",
    "subject.registry_validate",
    "subject.rename",
    "subject.prepare_astralium_references",
    "build_natal",
    "natal.candidate_envelope",
    "reconcile_natal",
    "resolve_forecast_context",
    "resolve_query_anchor",
    "lock_prospective_forecast",
    "interpret_structural_evidence",
    "rank_evidence",
    "personalize_ranking",
    "build_interpretation_contract",
    "prepare_historical_calibration",
    "lock_blind_forecast",
    "lock_historical_calibration",
    "finalize_historical_calibration",
    "export_case_markdown",
    "build_delivery_bundle",
    "validate_case",
    "migrate_case",
    "update_case_record",
))

V17_PUBLIC_ACTIONS = frozenset((
    "diagnose_case",
    "plan_case_reconciliation",
    "classify_validation_context",
    "build_validation_summary",
    "suggest_inquiries",
))


class V17ReleaseContractTests(unittest.TestCase):
    def test_version_contract_is_frozen_for_v170(self):
        self.assertEqual(PROJECT_CONTRACT_VERSION, "1.2")
        self.assertEqual(RUNTIME_SCHEMA_VERSION, "1.1")
        self.assertEqual(CASE_SCHEMA_VERSION, "1.1")
        self.assertEqual(DISTRIBUTION_RUNTIME_VERSION, "1.2-exp")

    def test_current_release_package_builder_is_v170_successor(self):
        self.assertEqual(build_release_package.RELEASE_VERSION, "1.7.0")
        self.assertEqual(
            build_release_package.USER_PACKAGE_NAME,
            "Metaphysics-Lab-v1.7.0-User-Package.zip",
        )

    def test_v16_public_actions_remain_and_v17_actions_are_registered(self):
        supported = set(SUPPORTED_ACTIONS)
        self.assertTrue(V16_PUBLIC_ACTIONS <= supported, V16_PUBLIC_ACTIONS - supported)
        self.assertTrue(V17_PUBLIC_ACTIONS <= supported, V17_PUBLIC_ACTIONS - supported)

    def test_v1_defaults_remain_authoritative(self):
        selector = get_historical_capability("historical.activation_selector")
        interpretation = get_distribution_capability("distribution.interpretation_contract")
        self.assertEqual(selector["profile_id"], "historical-activation-bazi-v1")
        self.assertEqual(selector["rule_version"], "1.0-exp")
        self.assertEqual(
            interpretation["rule_version"],
            "lin_tianji_interpretation_contract_v1-exp",
        )

    def test_v15_prospective_lock_identity_remains_exact(self):
        _, locked = ProspectiveValidationCompatibilityTests._legacy_lock()
        self.assertEqual(locked["canonical_digest"], FROZEN_V15_DIGEST)

    def test_v17_release_surface_validator_exists(self):
        self.assertTrue((ROOT / "tools" / "run_v17_release_surface_validation.py").is_file())

    def test_version_docs_state_v17_release_boundaries(self):
        version = (ROOT / "VERSION.md").read_text(encoding="utf-8")
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        combined = version + "\n" + changelog
        for required in (
            "v1.7.0",
            "可靠性",
            "Case Schema 1.1",
            "不需要破壞性重建",
            "selector v1",
            "interpretation v1",
            "Guided Inquiry",
            "不是新的命理證據",
        ):
            self.assertIn(required, combined)


if __name__ == "__main__":
    unittest.main()
