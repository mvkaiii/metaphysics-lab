import unittest

from engine.ziwei.capabilities import can_execute, get_capability, should_run_by_default


class ZiweiPhase2ACapabilityTests(unittest.TestCase):
    def test_core_is_experimental_on_demand_after_internal_gates(self):
        for capability_id in ("ziwei.transformations", "ziwei.flying"):
            cap = get_capability(capability_id)
            self.assertEqual(cap["implementation"], "implemented")
            self.assertEqual(cap["maturity"], "experimental")
            self.assertEqual(cap["routing"], "on_demand")
            self.assertTrue(can_execute(capability_id))
            self.assertFalse(should_run_by_default(capability_id))

    def test_fine_cycle_capabilities_remain_planned(self):
        ids = (
            "ziwei.flow_month_transformations",
            "ziwei.flow_day_transformations",
            "ziwei.flow_hour_transformations",
            "ziwei.flow_month_flying",
            "ziwei.flow_day_flying",
            "ziwei.flow_hour_flying",
        )
        for capability_id in ids:
            self.assertEqual(get_capability(capability_id)["implementation"], "planned")
            self.assertFalse(can_execute(capability_id))

    def test_flowing_stars_remain_planned(self):
        self.assertEqual(get_capability("ziwei.flowing_stars")["implementation"], "planned")


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
