import unittest

import engine.ziwei as ziwei
from engine.ziwei.capabilities import can_execute, get_capability, should_run_by_default


class ZiweiPhase2CCapabilityTests(unittest.TestCase):
    def test_flowing_stars_is_implemented_experimental_on_demand(self):
        cap = get_capability("ziwei.flowing_stars")
        self.assertEqual(cap["implementation"], "implemented")
        self.assertEqual(cap["maturity"], "experimental")
        self.assertEqual(cap["routing"], "on_demand")
        self.assertEqual(cap["rule_version"], "1.0-exp")
        self.assertEqual(cap["module"], "engine.ziwei.flowing_stars")
        self.assertTrue(can_execute("ziwei.flowing_stars"))
        self.assertFalse(should_run_by_default("ziwei.flowing_stars"))

    def test_conditional_dependencies_are_scope_specific(self):
        cap = get_capability("ziwei.flowing_stars")
        self.assertEqual(cap["dependencies"], ())
        self.assertEqual(
            cap["conditional_dependencies"],
            {
                "decadal": ("ziwei.natal_chart",),
                "yearly": (),
                "monthly": ("ziwei.flow_month_stem",),
                "daily": ("ziwei.flow_day_stem",),
                "hourly": ("ziwei.flow_hour_stem",),
            },
        )

    def test_activation_does_not_cascade_maturity(self):
        for capability_id in ("ziwei.transformations", "ziwei.flying"):
            cap = get_capability(capability_id)
            self.assertEqual((cap["implementation"], cap["maturity"], cap["routing"], cap["rule_version"]),
                             ("implemented", "stable", "on_demand", "1.0"))
        for capability_id in (
            "ziwei.flow_month_stem",
            "ziwei.flow_day_stem",
            "ziwei.flow_hour_stem",
            "ziwei.natal_chart",
        ):
            cap = get_capability(capability_id)
            self.assertEqual(cap["implementation"], "implemented")
            self.assertEqual(cap["maturity"], "experimental")
            self.assertEqual(cap["routing"], "on_demand")

    def test_minimal_public_exports_are_available(self):
        expected = (
            "build_flowing_star_layer",
            "source_from_decadal",
            "source_from_yearly",
            "source_from_monthly",
            "source_from_daily",
            "source_from_hourly",
            "materialize_flowing_star_layer",
            "join_dynamic_cycle",
        )
        for name in expected:
            self.assertTrue(hasattr(ziwei, name), name)
            self.assertIn(name, ziwei.__all__)
        for private_name in ("_CHANG_QU_BY_STEM", "_LUAN_XI_BY_BRANCH", "_NIANJIE_BY_BRANCH"):
            self.assertFalse(hasattr(ziwei, private_name))
            self.assertNotIn(private_name, ziwei.__all__)


if __name__ == "__main__":
    unittest.main()
