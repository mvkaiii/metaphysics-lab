import unittest

from engine.ziwei.capabilities import get_capability


class ZiweiNatalCapabilityTests(unittest.TestCase):
    def test_ziwei_natal_remains_experimental_after_phase2c_activation(self):
        cap = get_capability("ziwei.natal_chart")
        self.assertEqual(
            (cap["implementation"], cap["maturity"], cap["routing"], cap["rule_version"]),
            ("implemented", "experimental", "on_demand", "1.0-exp"),
        )
        self.assertEqual(cap["module"], "engine.ziwei.natal")
        flowing = get_capability("ziwei.flowing_stars")
        self.assertEqual(
            (flowing["implementation"], flowing["maturity"], flowing["routing"], flowing["rule_version"]),
            ("implemented", "experimental", "on_demand", "1.0-exp"),
        )


if __name__ == "__main__":
    unittest.main()
