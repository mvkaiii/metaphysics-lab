import unittest

from engine.ziwei.capabilities import get_capability, can_execute, should_run_by_default


class ZiweiCapabilitiesTests(unittest.TestCase):
    def test_flow_month_is_stable_default(self):
        cap = get_capability("ziwei.flow_month_palaces")
        self.assertEqual(cap["implementation"], "implemented")
        self.assertEqual(cap["maturity"], "stable")
        self.assertEqual(cap["routing"], "default")
        self.assertTrue(can_execute(cap["id"]))
        self.assertTrue(should_run_by_default(cap["id"]))

    def test_flow_day_is_experimental_on_demand(self):
        cap = get_capability("ziwei.flow_day_palaces")
        self.assertEqual(cap["implementation"], "implemented")
        self.assertEqual(cap["maturity"], "experimental")
        self.assertEqual(cap["routing"], "on_demand")
        self.assertTrue(can_execute(cap["id"]))
        self.assertFalse(should_run_by_default(cap["id"]))

    def test_flow_hour_is_experimental_on_demand(self):
        cap = get_capability("ziwei.flow_hour_palaces")
        self.assertEqual(cap["implementation"], "implemented")
        self.assertEqual(cap["maturity"], "experimental")
        self.assertEqual(cap["routing"], "on_demand")
        self.assertEqual(cap["rule_version"], "1.0-exp")
        self.assertTrue(can_execute(cap["id"]))
        self.assertFalse(should_run_by_default(cap["id"]))

    def test_unknown_capability_is_rejected(self):
        with self.assertRaises(KeyError):
            get_capability("ziwei.unknown")


if __name__ == "__main__":
    unittest.main()
