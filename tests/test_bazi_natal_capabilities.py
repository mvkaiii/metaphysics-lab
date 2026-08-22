import unittest

from engine.bazi.capabilities import can_execute, get_capability, should_run_by_default


class BaziNatalCapabilityTests(unittest.TestCase):
    def test_bazi_natal_profile_is_not_stable_by_default(self):
        cap = get_capability("bazi.natal_chart")
        self.assertEqual(
            (cap["implementation"], cap["maturity"], cap["routing"]),
            ("implemented", "experimental", "on_demand"),
        )
        self.assertEqual(cap["rule_version"], "1.0-exp")
        self.assertTrue(can_execute("bazi.natal_chart"))
        self.assertFalse(should_run_by_default("bazi.natal_chart"))


if __name__ == "__main__":
    unittest.main()
