import unittest

from engine.bazi.capabilities import get_capability as get_bazi_capability
from engine.birth.capabilities import get_capability as get_birth_capability
from engine.natal.capabilities import (
    can_execute as can_execute_natal,
    get_capability as get_natal_capability,
    should_run_by_default as natal_runs_by_default,
)
from engine.ziwei.capabilities import get_capability as get_ziwei_capability


class NatalCapabilityRegistryTests(unittest.TestCase):
    def test_state_matrix_is_explicit_after_phase2c_activation(self):
        expected = {
            "birth.input_resolution": ("implemented", "experimental", "on_demand", "1.0-exp"),
            "birth.location_resolution": ("implemented", "experimental", "on_demand", "1.0-exp"),
            "birth.true_solar_time": ("implemented", "experimental", "on_demand", "1.0-exp"),
            "bazi.natal_chart": ("implemented", "experimental", "on_demand", "1.0-exp"),
            "ziwei.natal_chart": ("implemented", "experimental", "on_demand", "1.0-exp"),
            "natal.reconciliation": ("implemented", "stable", "on_demand", "1.0"),
            "natal.markdown_export": ("implemented", "stable", "on_demand", "1.0"),
            "ziwei.flowing_stars": ("implemented", "experimental", "on_demand", "1.0-exp"),
        }
        getters = {
            "birth": get_birth_capability,
            "bazi": get_bazi_capability,
            "ziwei": get_ziwei_capability,
            "natal": get_natal_capability,
        }
        for capability_id, state in expected.items():
            with self.subTest(capability_id=capability_id):
                getter = getters[capability_id.split(".", 1)[0]]
                cap = getter(capability_id)
                self.assertEqual(
                    (cap["implementation"], cap["maturity"], cap["routing"], cap["rule_version"]),
                    state,
                )

    def test_natal_cross_system_capabilities_are_executable_but_not_default(self):
        for capability_id in ("natal.reconciliation", "natal.markdown_export"):
            with self.subTest(capability_id=capability_id):
                self.assertTrue(can_execute_natal(capability_id))
                self.assertFalse(natal_runs_by_default(capability_id))

    def test_dependency_graph_matches_actual_natal_pipeline(self):
        ziwei = get_ziwei_capability("ziwei.natal_chart")
        self.assertEqual(
            ziwei["dependencies"],
            ("birth.true_solar_time", "ziwei.transformations", "ziwei.flying"),
        )

        bazi = get_bazi_capability("bazi.natal_chart")
        self.assertEqual(
            bazi["dependencies"],
            ("birth.input_resolution", "birth.location_resolution", "calendar.resolve"),
        )

        export = get_natal_capability("natal.markdown_export")
        self.assertEqual(export["dependencies"], ("natal.reconciliation",))

    def test_phase2c_flowing_stars_is_experimental_not_default(self):
        cap = get_ziwei_capability("ziwei.flowing_stars")
        self.assertEqual(cap["implementation"], "implemented")
        self.assertEqual(cap["maturity"], "experimental")
        self.assertEqual(cap["routing"], "on_demand")
        self.assertEqual(cap["rule_version"], "1.0-exp")


if __name__ == "__main__":
    unittest.main()
