import unittest

from engine.birth.capabilities import get_capability


class BirthCapabilityTests(unittest.TestCase):
    def test_phase2c0_birth_capabilities_start_without_false_promotion(self):
        expected = {
            "birth.input_resolution": ("implemented", "experimental", "on_demand", "1.0-exp"),
            "birth.location_resolution": ("implemented", "experimental", "on_demand", "1.0-exp"),
            "birth.true_solar_time": ("implemented", "experimental", "on_demand", "1.0-exp"),
        }
        for capability_id, state in expected.items():
            cap = get_capability(capability_id)
            self.assertEqual(
                (cap["implementation"], cap["maturity"], cap["routing"], cap["rule_version"]),
                state,
            )
            self.assertEqual(cap["id"], capability_id)
            self.assertIn("module", cap)
            self.assertIn("dependencies", cap)


if __name__ == "__main__":
    unittest.main()
