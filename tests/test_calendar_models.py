import unittest
from datetime import date, datetime, timezone
from engine.calendar.models import *


class CalendarModelTests(unittest.TestCase):
    def test_provider_negative_month_is_normalized(self):
        self.assertEqual(
            LunarDate.from_provider_values(2025, -6, 1),
            LunarDate(2025, 6, 1, True),
        )

    def test_validation_precedence(self):
        self.assertEqual(
            combine_validation_status("validated", "boundary_caution"),
            "boundary_caution",
        )
        self.assertEqual(
            combine_validation_status("out_of_validated_range", "boundary_conflict"),
            "boundary_conflict",
        )

    def test_error_result_serializes_public_contract(self):
        result = CalendarResolution.failure(
            ResolverError("invalid_datetime", "bad input", {"value": "x"})
        )
        self.assertEqual(
            result.to_dict(),
            {"ok": False, "error": {
                "code": "invalid_datetime",
                "message": "bad input",
                "details": {"value": "x"},
            }},
        )

    def test_success_context_serializes_contract(self):
        context = CalendarContext(
            schema_version="1.0",
            resolver_version="1.0.0",
            input=CalendarInput("2026-09-18T14:00:00", "Asia/Taipei"),
            normalized_time=NormalizedTime(
                datetime(2026, 9, 18, 14, 0),
                datetime(2026, 9, 18, 6, 0, tzinfo=timezone.utc),
                "+08:00",
                date(2026, 9, 18),
                "Asia/Taipei",
                "未",
            ),
            lunar=LunarDate(2026, 8, 8, False),
            providers=ProviderBundle(
                LunarProviderMetadata(
                    "lunar-python", "1.4.8",
                    "000c8a3d74eed098d6256a28fdd51b869324c559",
                ),
                TimezoneProviderMetadata(
                    "tzdata", "2026.3", "2026c",
                    "a44279419071b7aa41ebe7eca301ebb2e759571a",
                ),
            ),
            validation=ValidationMetadata(
                ValidationCheck("validated", "hko-gregorian-lunar-1901-2100-v1"),
                ValidationCheck("validated", "tzdata-2026.3-iana-2026c-v1"),
                "validated",
                "1901-01-01/2100-12-31",
                None,
                (),
            ),
            policies=CalendarPolicies(
                "IANA legal local civil time",
                "local civil midnight (00:00)",
                "local civil clock; 子=23:00-00:59",
                False,
            ),
        )
        payload = CalendarResolution.success(context).to_dict()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["schema_version"], "1.0")
        self.assertEqual(payload["resolver_version"], "1.0.0")
        self.assertEqual(payload["providers"]["lunar_calendar"]["version"], "1.4.8")
        self.assertEqual(payload["providers"]["timezone_database"]["tzdb_version"], "2026c")
        self.assertFalse(payload["policies"]["metaphysics_day_boundary_applied"])


if __name__ == "__main__":
    unittest.main()
