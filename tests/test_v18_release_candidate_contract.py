import unittest
from pathlib import Path

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


ROOT = Path(__file__).resolve().parents[1]


class V18ReleaseCandidateContractTests(unittest.TestCase):
    def test_published_v18_snapshot_remains_immutable_history(self):
        version = (ROOT / "VERSION.md").read_text(encoding="utf-8")
        self.assertIn("## v1.8.0 Release Snapshot", version)
        self.assertIn("Release Version            1.8.0", version)
        self.assertIn("Project Contract           1.2", version)
        self.assertIn("Runtime Schema             1.1", version)
        self.assertIn("Case Schema                1.1", version)
        self.assertIn("AI Distribution Runtime    1.4-exp", version)

        workflow = (ROOT / ".github" / "workflows" / "release-v1.8.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("name: Release v1.8.0", workflow)
        self.assertIn("Metaphysics-Lab-v1.8.0-User-Package.zip", workflow)

    def test_current_v19_candidate_identity_does_not_relabel_task3(self):
        self.assertEqual(RELEASE_VERSION, "1.9.0")
        self.assertEqual(DISTRIBUTION_RUNTIME_VERSION, "1.5-exp")
        self.assertEqual(PROJECT_CONTRACT_VERSION, "1.3")
        self.assertEqual(RUNTIME_SCHEMA_VERSION, "1.1")
        self.assertEqual(CASE_SCHEMA_VERSION, "1.1")

        info = dispatch("runtime_info", {})
        self.assertTrue(info["ok"], info)
        data = info["data"]
        self.assertEqual(data["release_version"], "1.9.0")
        self.assertEqual(data["distribution_runtime_version"], "1.5-exp")
        self.assertEqual(data["project_contract_version"], "1.3")
        self.assertEqual(data["runtime_schema_version"], "1.1")
        self.assertEqual(data["case_schema_version"], "1.1")

        bazi = get_bazi_capability("bazi.natal_chart")
        self.assertEqual(bazi["implementation"], "implemented")
        self.assertEqual(bazi["maturity"], "experimental")
        self.assertEqual(bazi["routing"], "on_demand")
        self.assertEqual(bazi["rule_version"], "1.0-exp")

    def test_current_package_builder_follows_candidate_release_authority(self):
        self.assertEqual(build_release_package.RELEASE_VERSION, RELEASE_VERSION)
        self.assertEqual(
            build_release_package.USER_PACKAGE_NAME,
            "Metaphysics-Lab-v1.9.0-User-Package.zip",
        )
        self.assertEqual(
            set(build_release_package.USER_ASSETS),
            {"metaphysics_core.md", "metaphysics_lab.py", "project_instructions.txt"},
        )
        self.assertIn("render_bazi_decadal_timeline", SUPPORTED_ACTIONS)
        self.assertNotIn("visualization", SUPPORTED_ACTIONS)


if __name__ == "__main__":
    unittest.main()
