import unittest

from engine.ziwei.capabilities import can_execute, get_capability, should_run_by_default


class ZiweiPhase2BCapabilityTests(unittest.TestCase):
    def test_fine_cycle_stems_are_experimental_on_demand(self):
        for capability_id in (
            "ziwei.flow_month_stem",
            "ziwei.flow_day_stem",
            "ziwei.flow_hour_stem",
        ):
            cap = get_capability(capability_id)
            self.assertEqual(cap["implementation"], "implemented")
            self.assertEqual(cap["maturity"], "experimental")
            self.assertEqual(cap["routing"], "on_demand")
            self.assertEqual(cap["rule_version"], "1.0-exp")
            self.assertEqual(cap["module"], "engine.ziwei.fine_cycle_stems")
            self.assertTrue(can_execute(capability_id))
            self.assertFalse(should_run_by_default(capability_id))

    def test_fine_cycle_transformations_and_flying_are_experimental_on_demand(self):
        for capability_id in (
            "ziwei.flow_month_transformations",
            "ziwei.flow_day_transformations",
            "ziwei.flow_hour_transformations",
            "ziwei.flow_month_flying",
            "ziwei.flow_day_flying",
            "ziwei.flow_hour_flying",
        ):
            cap = get_capability(capability_id)
            self.assertEqual(cap["implementation"], "implemented")
            self.assertEqual(cap["maturity"], "experimental")
            self.assertEqual(cap["routing"], "on_demand")
            self.assertEqual(cap["rule_version"], "1.0-exp")
            self.assertTrue(can_execute(capability_id))
            self.assertFalse(should_run_by_default(capability_id))

    def test_existing_palace_and_core_maturity_do_not_change(self):
        month = get_capability("ziwei.flow_month_palaces")
        self.assertEqual((month["maturity"], month["routing"]), ("stable", "default"))
        for capability_id in ("ziwei.flow_day_palaces", "ziwei.flow_hour_palaces"):
            cap = get_capability(capability_id)
            self.assertEqual((cap["maturity"], cap["routing"]), ("experimental", "on_demand"))
        for capability_id in ("ziwei.transformations", "ziwei.flying"):
            cap = get_capability(capability_id)
            self.assertEqual((cap["implementation"], cap["maturity"], cap["routing"], cap["rule_version"]),
                             ("implemented", "stable", "on_demand", "1.0"))

    def test_flowing_stars_activation_does_not_promote_fine_cycle_stems(self):
        cap = get_capability("ziwei.flowing_stars")
        self.assertEqual((cap["implementation"], cap["maturity"], cap["routing"]),
                         ("implemented", "experimental", "on_demand"))
        self.assertTrue(can_execute("ziwei.flowing_stars"))
        for capability_id in ("ziwei.flow_month_stem", "ziwei.flow_day_stem", "ziwei.flow_hour_stem"):
            self.assertEqual(get_capability(capability_id)["maturity"], "experimental")

    def test_dependencies_are_scope_specific(self):
        self.assertEqual(
            get_capability("ziwei.flow_day_transformations")["dependencies"],
            ("ziwei.flow_day_stem", "ziwei.transformations"),
        )
        self.assertEqual(
            get_capability("ziwei.flow_hour_flying")["dependencies"],
            ("ziwei.flow_hour_transformations", "ziwei.flying"),
        )


if __name__ == "__main__":
    unittest.main()
