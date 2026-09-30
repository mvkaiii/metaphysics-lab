import unittest

from engine.bazi.capabilities import get_capability as get_bazi_capability
from engine.distribution.constants import (
    CASE_SCHEMA_VERSION,
    DISTRIBUTION_RUNTIME_VERSION,
    PROJECT_CONTRACT_VERSION,
    RELEASE_VERSION,
    RUNTIME_SCHEMA_VERSION,
    SUPPORTED_ACTIONS,
)
from engine.distribution.runtime import dispatch
from tools import build_release_package


class V18ReleaseCandidateContractTests(unittest.TestCase):
    def test_candidate_version_contract(self):
        self.assertEqual(RELEASE_VERSION, "1.8.0")
        self.assertEqual(DISTRIBUTION_RUNTIME_VERSION, "1.4-exp")
        self.assertEqual(PROJECT_CONTRACT_VERSION, "1.2")
        self.assertEqual(RUNTIME_SCHEMA_VERSION, "1.1")
        self.assertEqual(CASE_SCHEMA_VERSION, "1.1")

        info = dispatch("runtime_info", {})
        self.assertTrue(info["ok"], info)
        data = info["data"]
        self.assertEqual(data["release_version"], "1.8.0")
        self.assertEqual(data["distribution_runtime_version"], "1.4-exp")
        self.assertEqual(data["project_contract_version"], "1.2")
        self.assertEqual(data["runtime_schema_version"], "1.1")
        self.assertEqual(data["case_schema_version"], "1.1")

    def test_task3_sealed_bazi_rule_identity_is_not_relabelled(self):
        bazi = get_bazi_capability("bazi.natal_chart")
        self.assertEqual(bazi["implementation"], "implemented")
        self.assertEqual(bazi["maturity"], "experimental")
        self.assertEqual(bazi["routing"], "on_demand")
        self.assertEqual(bazi["rule_version"], "1.0-exp")

    def test_release_package_and_visualization_surface_boundaries(self):
        self.assertEqual(build_release_package.RELEASE_VERSION, "1.8.0")
        self.assertEqual(
            build_release_package.USER_PACKAGE_NAME,
            "Metaphysics-Lab-v1.8.0-User-Package.zip",
        )
        self.assertEqual(
            set(build_release_package.USER_ASSETS),
            {"metaphysics_core.md", "metaphysics_lab.py", "project_instructions.txt"},
        )
        self.assertIn("render_bazi_decadal_timeline", SUPPORTED_ACTIONS)
        self.assertNotIn("visualization", SUPPORTED_ACTIONS)


if __name__ == "__main__":
    unittest.main()
