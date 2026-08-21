import unittest
from dataclasses import FrozenInstanceError
from datetime import date

from engine.ziwei.errors import ZiweiFineCycleError, ZiweiPhase2AError
from engine.ziwei.models import FineCycleStemProfile, LayerProvenance, ResolvedCycleStem


class FineCycleModelTests(unittest.TestCase):
    def test_phase2a_error_contract_still_exists(self):
        err = ZiweiPhase2AError("x", "message", {"a": 1})
        self.assertEqual(err.code, "x")
        self.assertEqual(err.details, {"a": 1})

    def test_fine_cycle_error_contract(self):
        err = ZiweiFineCycleError(
            "invalid_fine_cycle_scope", "message", {"scope": "weekly"}
        )
        self.assertEqual(err.code, "invalid_fine_cycle_scope")
        self.assertEqual(err.details, {"scope": "weekly"})

    def test_fine_cycle_profile_is_immutable(self):
        profile = FineCycleStemProfile(
            "p", "1", "lunar_month", "split_after_day_15",
            "lunar_year", "late_zi_forward-v1", "effective_ziwei_day_stem",
        )
        with self.assertRaises(FrozenInstanceError):
            profile.rule_version = "2"

    def test_resolved_cycle_stem_is_immutable(self):
        provenance = LayerProvenance(
            "project_derived", "Metaphysics Lab", None, "p", "1", "test"
        )
        item = ResolvedCycleStem(
            "daily",
            "ziwei-day:2026-08-22@late_zi_forward-v1",
            "甲",
            "子",
            "ziwei-fine-cycle-lunar-late-zi-v1",
            "1.0-exp",
            date(2026, 8, 21),
            date(2026, 8, 22),
            None,
            "validated",
            provenance,
        )
        with self.assertRaises(FrozenInstanceError):
            item.heavenly_stem = "乙"


if __name__ == "__main__":
    unittest.main()

from engine.ziwei.errors import ZiweiFineCycleError
from engine.ziwei.fine_cycle_stems import (
    FINE_CYCLE_PROFILE_ID,
    get_fine_cycle_profile,
    resolve_month_stem,
)
from tests.ziwei_phase2b_fixtures import calendar_context


class FineCycleMonthTests(unittest.TestCase):
    def test_profile_is_explicit(self):
        profile = get_fine_cycle_profile()
        self.assertEqual(profile.profile_id, "ziwei-fine-cycle-lunar-late-zi-v1")
        self.assertEqual(profile.rule_version, "1.0-exp")
        self.assertEqual(profile.ziwei_day_boundary, "late_zi_forward-v1")
        self.assertEqual(FINE_CYCLE_PROFILE_ID, profile.profile_id)

    def test_unknown_profile_has_no_fallback(self):
        with self.assertRaises(ZiweiFineCycleError) as cm:
            get_fine_cycle_profile("unknown")
        self.assertEqual(cm.exception.code, "invalid_fine_cycle_profile")

    def test_public_2023_lunar_sixth_month_vector(self):
        result = resolve_month_stem(
            calendar_context(lunar_year=2023, lunar_month=6, lunar_day=13)
        )
        self.assertEqual((result.heavenly_stem, result.earthly_branch), ("己", "未"))
        self.assertEqual(result.reference, "lunar:2023-06")
        self.assertEqual(result.scope, "monthly")

    def test_leap_month_day_15_and_16_split(self):
        before = resolve_month_stem(calendar_context(
            lunar_year=2023, lunar_month=2, lunar_day=15, is_leap_month=True
        ))
        after = resolve_month_stem(calendar_context(
            lunar_year=2023, lunar_month=2, lunar_day=16, is_leap_month=True
        ))
        self.assertEqual(before.reference, "lunar:2023-L02-A")
        self.assertEqual(after.reference, "lunar:2023-L02-B")
        self.assertEqual((before.heavenly_stem, before.earthly_branch), ("乙", "卯"))
        self.assertEqual((after.heavenly_stem, after.earthly_branch), ("丙", "辰"))

    def test_synthetic_leap_twelfth_second_half_continues_ordinal_13(self):
        result = resolve_month_stem(calendar_context(
            lunar_year=2023, lunar_month=12, lunar_day=16, is_leap_month=True
        ))
        self.assertEqual(result.reference, "lunar:2023-L12-B")
        self.assertEqual((result.heavenly_stem, result.earthly_branch), ("丙", "寅"))

    def test_23xx_does_not_advance_month_stem(self):
        result = resolve_month_stem(calendar_context(
            local_hour=23,
            lunar_year=2023,
            lunar_month=6,
            lunar_day=30,
        ))
        self.assertEqual((result.heavenly_stem, result.earthly_branch), ("己", "未"))
        self.assertEqual(result.reference, "lunar:2023-06")

    def test_calendar_boundary_conflict_and_preapplied_boundary_fail_closed(self):
        with self.assertRaises(ZiweiFineCycleError) as cm1:
            resolve_month_stem(calendar_context(calendar_status="boundary_conflict"))
        self.assertEqual(cm1.exception.code, "calendar_context_unusable")
        with self.assertRaises(ZiweiFineCycleError) as cm2:
            resolve_month_stem(calendar_context(metaphysics_day_boundary_applied=True))
        self.assertEqual(cm2.exception.code, "calendar_boundary_already_applied")
