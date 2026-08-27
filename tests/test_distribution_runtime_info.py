import importlib
import importlib.util
import sys
import types
import unittest
from unittest import mock


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
        self.assertEqual(result["runtime_version"], "1.1-exp")
        data = result["data"]
        self.assertEqual(data["project_contract_version"], "1.1")
        self.assertEqual(data["runtime_schema_version"], "1.1")
        self.assertEqual(data["case_schema_version"], "1.1")
        self.assertEqual(data["distribution_runtime_version"], "1.1-exp")
        for action in (
            "runtime_info",
            "prepare_historical_calibration",
            "lock_blind_forecast",
            "lock_historical_calibration",
            "finalize_historical_calibration",
            "resolve_query_anchor",
            "lock_prospective_forecast",
            "rank_evidence",
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

        prospective = data["capabilities"]["distribution.prospective_forecast_governance"]
        self.assertEqual(prospective["implementation"], "implemented")
        self.assertEqual(prospective["maturity"], "experimental")
        self.assertEqual(prospective["routing"], "on_demand")
        self.assertEqual(prospective["rule_version"], "lin_tianji_v1.5-exp")

        evidence = data["capabilities"]["distribution.evidence_engine"]
        self.assertEqual(evidence["implementation"], "implemented")
        self.assertEqual(evidence["maturity"], "experimental")
        self.assertEqual(evidence["routing"], "on_demand")
        self.assertEqual(evidence["rule_version"], "lin_tianji_v1.5-exp")

    def test_runtime_info_separates_bundled_core_from_optional_external_dependencies(self):
        runtime = self._runtime()
        data = runtime.dispatch("runtime_info", {})["data"]
        self.assertEqual(data["dependency_authority"]["calendar_core"], "bundled")
        self.assertEqual(
            data["dependency_authority"]["network_location"],
            "execution_environment_optional",
        )

        bundled = data["bundled_dependencies"]
        self.assertEqual(set(bundled), {"lunar-python", "tzdata"})
        self.assertEqual(bundled["lunar-python"]["expected_version"], "1.4.8")
        self.assertEqual(bundled["tzdata"]["expected_version"], "2026.3")
        for value in bundled.values():
            self.assertIs(value["bundled"], True)
            self.assertIs(value["available"], True)
            self.assertIs(value["runtime_uses_environment_package"], False)

        optional = data["optional_external_dependencies"]
        self.assertEqual(set(optional), {"geopy", "timezonefinder"})
        for value in optional.values():
            self.assertIn("installed", value)
            self.assertIn("matches_pin", value)

    def test_bundled_core_availability_comes_from_committed_vendor_bytes(self):
        dependencies = importlib.import_module("engine.distribution.dependencies")
        manifest = importlib.import_module("engine.vendor.manifest")

        for package_name in ("lunar-python", "tzdata"):
            manifest_row = manifest.bundled_dependency(package_name)
            vendored_path = manifest_row.get("vendored_path")
            if isinstance(vendored_path, str):
                self.assertFalse(
                    (dependencies._repo_root() / vendored_path).is_dir(),
                    "qualification requires no committed private vendor tree",
                )

        fake_lunar = types.ModuleType("lunar_python")
        fake_lunar.__version__ = "999.0"
        fake_tzdata = types.ModuleType("tzdata")
        fake_tzdata.__version__ = "0.0"
        with mock.patch.dict(
            sys.modules,
            {"lunar_python": fake_lunar, "tzdata": fake_tzdata},
        ), mock.patch.object(
            dependencies.metadata,
            "version",
            side_effect=AssertionError("bundled authority must not consult host metadata"),
        ):
            bundled = dependencies.inspect_bundled_dependencies()

        self.assertEqual(bundled["lunar-python"]["version"], "1.4.8")
        self.assertEqual(bundled["tzdata"]["version"], "2026.3")
        for value in bundled.values():
            self.assertIs(value["available"], True)
            self.assertIs(value["runtime_uses_environment_package"], False)

    def test_runtime_info_exposes_exact_bundled_offline_registry_profile(self):
        runtime = self._runtime()
        info = runtime.dispatch("runtime_info", {})["data"]["offline_location_registry"]
        self.assertEqual(info["version"], "1.0")
        self.assertEqual(info["record_count"], 40)
        self.assertEqual(
            info["coverage_profile"],
            "taiwan-admin1-plus-explicit-major-cities-v1",
        )
        self.assertEqual(info["source_profiles"], ["geonames-curated-2026-08-24"])
        self.assertIs(info["bundled"], True)
        self.assertIs(info["available"], True)
        self.assertNotIn("records", info)
        self.assertNotIn("aliases", info)

    def test_legacy_external_dependency_view_is_diagnostic_only(self):
        runtime = self._runtime()
        dependencies = runtime.dispatch("runtime_info", {})["data"]["external_dependencies"]
        self.assertEqual(set(dependencies), {"lunar-python", "tzdata", "geopy", "timezonefinder"})
        for value in dependencies.values():
            self.assertIs(value["deprecated"], True)
            self.assertEqual(value["authority"], "diagnostic_only")
            self.assertIn("installed", value)
            self.assertIn("matches_pin", value)

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
