import unittest

from engine.historical.capabilities import get_capability


class HistoricalActivationCapabilityTests(unittest.TestCase):
    def test_capability_is_experimental_on_demand_v1(self):
        capability = get_capability("historical.activation_selector")
        self.assertEqual(capability["implementation"], "implemented")
        self.assertEqual(capability["maturity"], "experimental")
        self.assertEqual(capability["routing"], "on_demand")
        self.assertEqual(capability["rule_version"], "1.0-exp")
        self.assertEqual(capability["profile_id"], "historical-activation-bazi-v1")
        self.assertEqual(capability["module"], "engine.historical.selector")


if __name__ == "__main__":
    unittest.main()
