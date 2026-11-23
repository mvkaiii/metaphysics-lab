"""v1.9.1 candidate identity, compatibility, and publication boundaries."""
import unittest
from pathlib import Path

from engine.distribution.constants import (
    CASE_SCHEMA_VERSION, DISTRIBUTION_RUNTIME_VERSION,
    PROJECT_CONTRACT_VERSION, RELEASE_VERSION, RUNTIME_SCHEMA_VERSION,
)
from engine.distribution.runtime import dispatch
from engine.distribution.capabilities import get_capability as distribution_capability
from engine.historical.capabilities import get_capability as historical_capability
from tools import build_release_package

ROOT = Path(__file__).resolve().parents[1]


class V191PatchContractTests(unittest.TestCase):
    def test_current_identity_and_unchanged_component_versions(self):
        self.assertEqual((RELEASE_VERSION, PROJECT_CONTRACT_VERSION,
                          RUNTIME_SCHEMA_VERSION, CASE_SCHEMA_VERSION,
                          DISTRIBUTION_RUNTIME_VERSION),
                         ("1.9.1", "1.3", "1.1", "1.1", "1.5-exp"))
        info = dispatch("runtime_info", {})
        self.assertTrue(info["ok"], info)
        data = info["data"]
        self.assertEqual(data["release_version"], "1.9.1")
        self.assertEqual(data["project_contract_version"], "1.3")
        self.assertEqual(data["runtime_schema_version"], "1.1")
        self.assertEqual(data["case_schema_version"], "1.1")
        self.assertEqual(data["distribution_runtime_version"], "1.5-exp")

    def test_package_identity_and_historical_sha(self):
        self.assertEqual(build_release_package.USER_PACKAGE_NAME,
                         "Metaphysics-Lab-v1.9.1-User-Package.zip")
        self.assertEqual(set(build_release_package.USER_ASSETS),
                         {"metaphysics_core.md", "metaphysics_lab.py",
                          "project_instructions.txt"})
        historical = (ROOT / "docs/release/v1.9.0-qualification.md").read_text(encoding="utf-8")
        self.assertIn("e263c25ea6efb8184a2d66c2bc2ce3edf31b29324152b2bccb9f96333aa504fa", historical)

    def test_capabilities_and_defaults_do_not_change(self):
        result = dispatch("runtime_info", {})
        self.assertTrue(result["ok"], result)
        caps = result["data"]["capabilities"]
        for key in ("natal.candidate_envelope", "distribution.case_revision_integrity",
                    "distribution.lock_provenance", "distribution.guided_natal_build",
                    "distribution.candidate_envelope_visualization"):
            self.assertEqual(caps[key]["implementation"], "implemented")
            self.assertEqual(caps[key]["maturity"], "experimental")
            self.assertEqual(caps[key]["routing"], "on_demand")
        selector = historical_capability("historical.activation_selector")
        self.assertEqual(selector["profile_id"], "historical-activation-bazi-v1")
        interpretation = distribution_capability("distribution.interpretation_contract")
        self.assertEqual(interpretation["rule_version"], "lin_tianji_interpretation_contract_v1-exp")

    def test_pinned_package_digest_matches_candidate_receipt(self):
        digest = "aed00ed82c0066b77639fdd5c5bae92c82b7566d6de4cafe27a2f5cbd09207e7"
        receipt = (ROOT / "docs/release/v1.9.1-qualification.md").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/v191-release-candidate-validation.yml").read_text(encoding="utf-8")
        self.assertIn("user_package_sha256: " + digest, receipt)
        self.assertIn("EXPECTED_PACKAGE_SHA256: " + digest, workflow)
        self.assertIn('test "$actual" = "$EXPECTED_PACKAGE_SHA256"', workflow)
    def test_candidate_does_not_claim_published_status(self):
        notes = (ROOT / "docs/發布說明-v1.9.1.md").read_text(encoding="utf-8")
        self.assertIn("尚未正式發布", notes)
        for name in ("README.md", "docs/快速開始.md",
                     "docs/安裝到ChatGPT-Project.md", "docs/更新與版本同步.md"):
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn("v1.9.0", text)
            self.assertIn("v1.9.1", text)


if __name__ == "__main__":
    unittest.main()
