import unittest

from engine.ziwei.capabilities import can_execute, get_capability, should_run_by_default


class ZiweiPhase2ACapabilityTests(unittest.TestCase):
    def test_core_is_stable_on_demand_after_promotion(self):
        for capability_id in ("ziwei.transformations", "ziwei.flying"):
            cap = get_capability(capability_id)
            self.assertEqual(cap["implementation"], "implemented")
            self.assertEqual(cap["maturity"], "stable")
            self.assertEqual(cap["routing"], "on_demand")
            self.assertEqual(cap["rule_version"], "1.0")
            self.assertTrue(can_execute(capability_id))
            self.assertFalse(should_run_by_default(capability_id))

    def test_phase2a_core_contract_remains_stable_after_later_capabilities(self):
        for capability_id in ("ziwei.transformations", "ziwei.flying"):
            cap = get_capability(capability_id)
            self.assertEqual(cap["implementation"], "implemented")
            self.assertEqual(cap["maturity"], "stable")
            self.assertEqual(cap["routing"], "on_demand")
            self.assertEqual(cap["rule_version"], "1.0")

    def test_flowing_stars_activation_does_not_promote_phase2a_core(self):
        flowing = get_capability("ziwei.flowing_stars")
        self.assertEqual((flowing["implementation"], flowing["maturity"]), ("implemented", "experimental"))
        for capability_id in ("ziwei.transformations", "ziwei.flying"):
            self.assertEqual(get_capability(capability_id)["maturity"], "stable")


class ZiweiPhase2AStablePromotionTests(unittest.TestCase):
    def test_core_is_stable_but_still_on_demand(self):
        for capability_id in ("ziwei.transformations", "ziwei.flying"):
            cap = get_capability(capability_id)
            self.assertEqual(cap["implementation"], "implemented")
            self.assertEqual(cap["maturity"], "stable")
            self.assertEqual(cap["routing"], "on_demand")
            self.assertFalse(should_run_by_default(capability_id))


if __name__ == "__main__":
    unittest.main()
