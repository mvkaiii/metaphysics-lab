import unittest

from engine.ziwei.capabilities import get_capability


class ZiweiNatalCapabilityTests(unittest.TestCase):
    def test_ziwei_natal_starts_experimental_without_promoting_phase2c(self):
        cap = get_capability("ziwei.natal_chart")
        self.assertEqual(
            (cap["implementation"], cap["maturity"], cap["routing"], cap["rule_version"]),
            ("implemented", "experimental", "on_demand", "1.0-exp"),
        )
        self.assertEqual(cap["module"], "engine.ziwei.natal")
        self.assertEqual(get_capability("ziwei.flowing_stars")["implementation"], "planned")
        self.assertIsNone(get_capability("ziwei.flowing_stars")["rule_version"])


if __name__ == "__main__":
    unittest.main()
