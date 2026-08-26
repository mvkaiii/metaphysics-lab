import sys
import types
import unittest
from datetime import date
from unittest.mock import patch

from engine.calendar.lunar import (
    LunarProviderFailure,
    LunarProviderUnsupportedDate,
    LunarPythonProvider,
    calendar_validation_for,
)
from engine.calendar.models import LunarDate


class _SyntheticLunar:
    def __init__(self, year, month, day):
        self._year = year
        self._month = month
        self._day = day

    def getYear(self):
        return self._year

    def getMonth(self):
        return self._month

    def getDay(self):
        return self._day


class _SyntheticSolarValue:
    def __init__(self, lunar):
        self._lunar = lunar

    def getLunar(self):
        return self._lunar


class _SyntheticPrivateSolar:
    @staticmethod
    def fromYmd(year, month, day):
        return _SyntheticSolarValue(_SyntheticLunar(year, -6 if (month, day) == (7, 25) else 1, 1))


PINNED_METADATA = {
    "package_name": "lunar-python",
    "version": "1.4.8",
    "source_revision": "000c8a3d74eed098d6256a28fdd51b869324c559",
    "bundled": True,
    "runtime_authority": "bundled",
}


class CalendarLunarTests(unittest.TestCase):
    def _synthetic_private_provider(self):
        private = types.ModuleType("_metaphysics_lab_vendor.lunar_python")
        private.Solar = _SyntheticPrivateSolar
        public = types.ModuleType("lunar_python")
        public.Solar = object()
        modules = {
            "_metaphysics_lab_vendor.lunar_python": private,
            "lunar_python": public,
        }
        return modules

    def test_private_provider_ignores_preloaded_public_lunar_python(self):
        modules = self._synthetic_private_provider()
        with patch.dict(sys.modules, modules, clear=False), patch(
            "engine.calendar.lunar.bundled_dependency", return_value=PINNED_METADATA
        ):
            provider = LunarPythonProvider()
            self.assertIs(provider._solar, _SyntheticPrivateSolar)
            self.assertEqual(provider.metadata.version, "1.4.8")
            self.assertEqual(
                provider.metadata.source_revision,
                "000c8a3d74eed098d6256a28fdd51b869324c559",
            )

    def test_actual_bundled_provider_ignores_public_package_and_environment_metadata(self):
        public = types.ModuleType("lunar_python")
        public.Solar = object()
        public.__version__ = "0.0.fake"
        with patch.dict(sys.modules, {"lunar_python": public}, clear=False), patch(
            "importlib.metadata.version", return_value="0.0.fake"
        ) as environment_version:
            provider = LunarPythonProvider()
            self.assertEqual(provider.metadata.version, "1.4.8")
            self.assertEqual(
                provider.metadata.source_revision,
                "000c8a3d74eed098d6256a28fdd51b869324c559",
            )
            self.assertEqual(
                provider.convert(date(2025, 1, 29)),
                LunarDate(2025, 1, 1, False),
            )
            environment_version.assert_not_called()

    def test_provider_rejects_non_bundled_metadata_even_if_private_module_exists(self):
        modules = self._synthetic_private_provider()
        wrong = dict(PINNED_METADATA, runtime_authority="execution_environment")
        with patch.dict(sys.modules, modules, clear=False), patch(
            "engine.calendar.lunar.bundled_dependency", return_value=wrong
        ):
            with self.assertRaises(LunarProviderFailure):
                LunarPythonProvider()

    def test_synthetic_private_provider_conversion_contract(self):
        modules = self._synthetic_private_provider()
        with patch.dict(sys.modules, modules, clear=False), patch(
            "engine.calendar.lunar.bundled_dependency", return_value=PINNED_METADATA
        ):
            provider = LunarPythonProvider()
            self.assertEqual(provider.convert(date(2025, 1, 29)), LunarDate(2025, 1, 1, False))
            self.assertEqual(provider.convert(date(2025, 7, 25)), LunarDate(2025, 6, 1, True))

    def test_validated_edges(self):
        self.assertEqual(calendar_validation_for(date(1901, 1, 1)).check.status, "validated")
        self.assertEqual(calendar_validation_for(date(2100, 12, 31)).check.status, "validated")

    def test_2057_conflict_window(self):
        for value in (date(2057, 9, 28), date(2057, 10, 10), date(2057, 10, 27)):
            decision = calendar_validation_for(value)
            self.assertEqual(decision.check.status, "boundary_conflict")
            self.assertEqual(decision.boundary_id, "hko-new-moon-2057-09-28-conflict")
        self.assertEqual(calendar_validation_for(date(2057, 10, 28)).check.status, "validated")

    def test_caution_dates(self):
        self.assertEqual(calendar_validation_for(date(2089, 9, 4)).check.status, "boundary_caution")
        self.assertEqual(calendar_validation_for(date(2097, 8, 7)).check.status, "boundary_caution")

    def test_out_of_validated_range(self):
        self.assertEqual(
            calendar_validation_for(date(2150, 3, 1)).check.status,
            "out_of_validated_range",
        )

    def test_provider_unsupported_date(self):
        modules = self._synthetic_private_provider()
        with patch.dict(sys.modules, modules, clear=False), patch(
            "engine.calendar.lunar.bundled_dependency", return_value=PINNED_METADATA
        ):
            provider = LunarPythonProvider()
            with patch.object(provider._solar, "fromYmd", side_effect=IndexError("unsupported")):
                with self.assertRaises(LunarProviderUnsupportedDate):
                    provider.convert(date(2150, 3, 1))

    def test_provider_failure(self):
        modules = self._synthetic_private_provider()
        with patch.dict(sys.modules, modules, clear=False), patch(
            "engine.calendar.lunar.bundled_dependency", return_value=PINNED_METADATA
        ):
            provider = LunarPythonProvider()
            with patch.object(provider._solar, "fromYmd", side_effect=RuntimeError("boom")):
                with self.assertRaises(LunarProviderFailure):
                    provider.convert(date(2026, 8, 21))


if __name__ == "__main__":
    unittest.main()
