import importlib
import importlib.util
import unittest


class DistributionRuntimeInfoTests(unittest.TestCase):
    def _find_spec_or_none(self, name):
        try:
            return importlib.util.find_spec(name)
        except ModuleNotFoundError:
            return None

    def _runtime(self):
        spec = self._find_spec_or_none("engine.distribution.runtime")
        self.assertIsNotNone(spec, "engine.distribution.runtime must exist")
        return importlib.import_module("engine.distribution.runtime")

    def test_runtime_info_is_self_describing_and_registry_driven(self):
        runtime = self._runtime()
        result = runtime.dispatch("runtime_info", {})
        self.assertTrue(result["ok"])
        self.assertEqual(result["action"], "runtime_info")
        self.assertEqual(result["runtime_version"], "1.0-exp")
        data = result["data"]
        self.assertEqual(data["project_contract_version"], "1.1")
        self.assertEqual(data["runtime_schema_version"], "1.0")
        self.assertEqual(data["case_schema_version"], "1.1")
        for action in (
            "runtime_info",
            "prepare_historical_calibration",
            "lock_blind_forecast",
            "lock_historical_calibration",
            "finalize_historical_calibration",
        ):
            self.assertIn(action, data["supported_actions"])

        flowing = data["capabilities"]["ziwei.flowing_stars"]
        self.assertEqual(flowing["implementation"], "implemented")
        self.assertEqual(flowing["maturity"], "experimental")
        self.assertEqual(flowing["routing"], "on_demand")

        historical = data["capabilities"]["historical.activation_selector"]
        self.assertEqual(historical["implementation"], "implemented")
        self.assertEqual(historical["maturity"], "experimental")
        self.assertEqual(historical["routing"], "on_demand")
        self.assertEqual(historical["rule_version"], "1.0-exp")
        self.assertEqual(historical["profile_id"], "historical-activation-bazi-v1")

    def test_runtime_info_reports_all_pinned_external_dependencies_without_importing_them(self):
        runtime = self._runtime()
        data = runtime.dispatch("runtime_info", {})["data"]
        dependencies = data["external_dependencies"]
        self.assertEqual(set(dependencies), {"lunar-python", "tzdata", "geopy", "timezonefinder"})
        self.assertEqual(dependencies["lunar-python"]["expected_version"], "1.4.8")
        for value in dependencies.values():
            self.assertIn("installed", value)
            self.assertIn("matches_pin", value)
            self.assertIn("required_for", value)

    def test_dependency_status_can_report_missing_optional_location_packages(self):
        dependencies = importlib.import_module("engine.distribution.dependencies")

        def missing(_name):
            return None

        geopy = dependencies.inspect_dependency("geopy", find_spec=missing, version_getter=lambda _name: None)
        timezonefinder = dependencies.inspect_dependency(
            "timezonefinder", find_spec=missing, version_getter=lambda _name: None
        )
        self.assertFalse(geopy["installed"])
        self.assertFalse(timezonefinder["installed"])
        self.assertEqual(geopy["role"], "location")
        self.assertEqual(timezonefinder["role"], "location")

    def test_unknown_action_is_structured_error_not_exception(self):
        runtime = self._runtime()
        result = runtime.dispatch("does_not_exist", {})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "unsupported_action")
        self.assertEqual(result["action"], "does_not_exist")


if __name__ == "__main__":
    unittest.main()
