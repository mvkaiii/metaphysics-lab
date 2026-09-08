import math
import unittest

from engine.distribution.manifest import (
    CAPABILITY_MANIFEST_VERSION,
    load_capability_manifest,
    validate_capability_registry_entry,
)


class CapabilityManifestV1Tests(unittest.TestCase):
    def test_manifest_exposes_version_and_sorted_capabilities(self):
        manifest = load_capability_manifest()
        self.assertEqual(CAPABILITY_MANIFEST_VERSION, "1.0")
        self.assertEqual(manifest["manifest_version"], "1.0")
        self.assertEqual(
            list(manifest["capabilities"]),
            sorted(manifest["capabilities"]),
        )

    def test_required_core_fields_are_present(self):
        required = {
            "id",
            "implementation",
            "maturity",
            "routing",
            "rule_version",
            "module",
            "dependencies",
        }
        manifest = load_capability_manifest()
        for capability_id, capability in manifest["capabilities"].items():
            self.assertTrue(required <= set(capability), capability_id)

    def test_v16_capability_maturity_and_routing_are_frozen(self):
        capabilities = load_capability_manifest()["capabilities"]
        expected = {
            "ziwei.flow_month_palaces": ("implemented", "stable", "default"),
            "ziwei.flow_day_palaces": ("implemented", "experimental", "on_demand"),
            "ziwei.flow_hour_palaces": ("implemented", "experimental", "on_demand"),
            "ziwei.flowing_stars": ("implemented", "experimental", "on_demand"),
            "distribution.prospective_forecast_governance": (
                "implemented",
                "experimental",
                "on_demand",
            ),
            "distribution.interpretation_contract": (
                "implemented",
                "experimental",
                "on_demand",
            ),
        }
        for capability_id, frozen in expected.items():
            capability = capabilities[capability_id]
            actual = (
                capability["implementation"],
                capability["maturity"],
                capability["routing"],
            )
            self.assertEqual(actual, frozen, capability_id)

    def test_ziwei_scope_specific_capabilities_expose_supported_scopes(self):
        capabilities = load_capability_manifest()["capabilities"]
        expected = {
            "ziwei.flow_month_palaces": ["monthly"],
            "ziwei.flow_day_palaces": ["daily"],
            "ziwei.flow_hour_palaces": ["hourly"],
            "ziwei.flow_month_stem": ["monthly"],
            "ziwei.flow_day_stem": ["daily"],
            "ziwei.flow_hour_stem": ["hourly"],
            "ziwei.flow_month_transformations": ["monthly"],
            "ziwei.flow_day_transformations": ["daily"],
            "ziwei.flow_hour_transformations": ["hourly"],
            "ziwei.flow_month_flying": ["monthly"],
            "ziwei.flow_day_flying": ["daily"],
            "ziwei.flow_hour_flying": ["hourly"],
            "ziwei.flowing_stars": [
                "decadal",
                "yearly",
                "monthly",
                "daily",
                "hourly",
            ],
        }
        for capability_id, scopes in expected.items():
            self.assertEqual(
                capabilities[capability_id].get("supported_scopes"),
                scopes,
                capability_id,
            )

    def test_validator_normalizes_json_safe_sequences(self):
        capability = {
            "id": "synthetic.capability",
            "implementation": "implemented",
            "maturity": "experimental",
            "routing": "on_demand",
            "rule_version": "1.0-exp",
            "module": "engine.synthetic",
            "dependencies": ("synthetic.base",),
            "supported_scopes": ("monthly", "daily"),
        }
        normalized = validate_capability_registry_entry(
            "synthetic.capability", capability
        )
        self.assertEqual(normalized["dependencies"], ["synthetic.base"])
        self.assertEqual(normalized["supported_scopes"], ["monthly", "daily"])

    def test_validator_rejects_id_mismatch(self):
        capability = self._valid_capability()
        capability["id"] = "synthetic.other"
        with self.assertRaises(ValueError):
            validate_capability_registry_entry("synthetic.capability", capability)

    def test_validator_rejects_missing_required_field(self):
        capability = self._valid_capability()
        del capability["module"]
        with self.assertRaises(ValueError):
            validate_capability_registry_entry("synthetic.capability", capability)

    def test_validator_rejects_unknown_top_level_field(self):
        capability = self._valid_capability()
        capability["surprise"] = True
        with self.assertRaises(ValueError):
            validate_capability_registry_entry("synthetic.capability", capability)

    def test_validator_rejects_invalid_enums(self):
        for field, value in (
            ("implementation", "partial"),
            ("maturity", "beta"),
            ("routing", "automatic"),
        ):
            with self.subTest(field=field):
                capability = self._valid_capability()
                capability[field] = value
                with self.assertRaises(ValueError):
                    validate_capability_registry_entry(
                        "synthetic.capability", capability
                    )

    def test_validator_rejects_non_string_dependencies(self):
        capability = self._valid_capability()
        capability["dependencies"] = ("synthetic.base", 7)
        with self.assertRaises(ValueError):
            validate_capability_registry_entry("synthetic.capability", capability)

    def test_validator_rejects_non_json_safe_values(self):
        capability = self._valid_capability()
        capability["required_inputs"] = {"threshold": math.nan}
        with self.assertRaises(ValueError):
            validate_capability_registry_entry("synthetic.capability", capability)

    @staticmethod
    def _valid_capability():
        return {
            "id": "synthetic.capability",
            "implementation": "implemented",
            "maturity": "experimental",
            "routing": "on_demand",
            "rule_version": "1.0-exp",
            "module": "engine.synthetic",
            "dependencies": (),
        }


if __name__ == "__main__":
    unittest.main()
