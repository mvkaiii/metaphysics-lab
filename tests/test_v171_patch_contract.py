import unittest
from pathlib import Path


from engine.distribution.constants import (
    CASE_SCHEMA_VERSION,
    DISTRIBUTION_RUNTIME_VERSION,
    PROJECT_CONTRACT_VERSION,
    RELEASE_VERSION,
    RUNTIME_SCHEMA_VERSION,
)
from engine.distribution.runtime import dispatch
from engine.distribution.capabilities import get_capability as get_distribution_capability
from engine.historical.capabilities import get_capability as get_historical_capability


class V171PatchContractTests(unittest.TestCase):
    def test_v171_release_snapshot_remains_immutable_in_docs(self):
        root = Path(__file__).resolve().parents[1]
        version = (root / "VERSION.md").read_text(encoding="utf-8")
        notes = (root / "docs" / "發布說明-v1.7.1.md").read_text(encoding="utf-8")
        self.assertIn("Release Version            1.7.1", version)
        self.assertIn("AI Distribution Runtime    1.2-exp", version)
        self.assertIn("Metaphysics Lab v1.7.1", notes)
        self.assertIn("771f8493cd07b298c7971f38c601ce17a8acfcce5dab43c72e245f7b282943e8", notes)

        result = dispatch("runtime_info", {})
        self.assertTrue(result["ok"], result)
        data = result["data"]
        self.assertEqual(data["release_version"], RELEASE_VERSION)
        self.assertEqual(data["distribution_runtime_version"], DISTRIBUTION_RUNTIME_VERSION)
        self.assertEqual(data["project_contract_version"], PROJECT_CONTRACT_VERSION)
        self.assertEqual(data["runtime_schema_version"], RUNTIME_SCHEMA_VERSION)
        self.assertEqual(data["case_schema_version"], CASE_SCHEMA_VERSION)

    def test_patch_does_not_promote_research_capabilities(self):
        selector = get_historical_capability("historical.activation_selector")
        interpretation = get_distribution_capability("distribution.interpretation_contract")
        self.assertEqual(selector["profile_id"], "historical-activation-bazi-v1")
        self.assertEqual(selector["rule_version"], "1.0-exp")
        self.assertEqual(interpretation["rule_version"], "lin_tianji_interpretation_contract_v1-exp")

        result = dispatch("runtime_info", {})
        caps = result["data"]["capabilities"]
        self.assertEqual(caps["ziwei.flow_day_palaces"]["maturity"], "experimental")
        self.assertEqual(caps["ziwei.flow_hour_palaces"]["maturity"], "experimental")
        self.assertEqual(caps["ziwei.flowing_stars"]["maturity"], "experimental")
        self.assertEqual(caps["distribution.prospective_validation"]["maturity"], "experimental")


if __name__ == "__main__":
    unittest.main()
