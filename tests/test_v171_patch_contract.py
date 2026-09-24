import unittest

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
    def test_release_identity_is_distinct_from_component_versions(self):
        self.assertEqual(RELEASE_VERSION, "1.7.1")
        self.assertEqual(DISTRIBUTION_RUNTIME_VERSION, "1.2-exp")
        self.assertEqual(PROJECT_CONTRACT_VERSION, "1.2")
        self.assertEqual(RUNTIME_SCHEMA_VERSION, "1.1")
        self.assertEqual(CASE_SCHEMA_VERSION, "1.1")

        result = dispatch("runtime_info", {})
        self.assertTrue(result["ok"], result)
        data = result["data"]
        self.assertEqual(data["release_version"], "1.7.1")
        self.assertEqual(data["distribution_runtime_version"], "1.2-exp")
        self.assertEqual(data["project_contract_version"], "1.2")
        self.assertEqual(data["runtime_schema_version"], "1.1")
        self.assertEqual(data["case_schema_version"], "1.1")

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
