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

from engine.ziwei.fine_cycle_stems import resolve_day_stem


class FineCycleDayTests(unittest.TestCase):
    def test_2259_uses_civil_date(self):
        result = resolve_day_stem(calendar_context(
            gregorian_date=date(1987, 12, 6), local_hour=22, local_minute=59,
        ))
        self.assertEqual(result.effective_date, date(1987, 12, 6))
        self.assertEqual((result.heavenly_stem, result.earthly_branch), ("己", "丑"))

    def test_2300_advances_effective_date(self):
        result = resolve_day_stem(calendar_context(
            gregorian_date=date(1987, 12, 6), local_hour=23, local_minute=0,
            hour_branch="子",
        ))
        self.assertEqual(result.effective_date, date(1987, 12, 7))
        self.assertEqual((result.heavenly_stem, result.earthly_branch), ("庚", "寅"))
        self.assertEqual(result.reference, "ziwei-day:1987-12-07@late_zi_forward-v1")

    def test_0000_does_not_double_advance(self):
        result = resolve_day_stem(calendar_context(
            gregorian_date=date(1987, 12, 7), local_hour=0, local_minute=0,
            hour_branch="子",
        ))
        self.assertEqual(result.effective_date, date(1987, 12, 7))
        self.assertEqual((result.heavenly_stem, result.earthly_branch), ("庚", "寅"))

    def test_preapplied_metaphysics_boundary_is_rejected(self):
        with self.assertRaises(ZiweiFineCycleError) as cm:
            resolve_day_stem(calendar_context(metaphysics_day_boundary_applied=True))
        self.assertEqual(cm.exception.code, "calendar_boundary_already_applied")

    def test_calendar_boundary_conflict_is_rejected_but_caution_is_preserved(self):
        with self.assertRaises(ZiweiFineCycleError) as cm:
            resolve_day_stem(calendar_context(calendar_status="boundary_conflict"))
        self.assertEqual(cm.exception.code, "calendar_context_unusable")
        caution = resolve_day_stem(calendar_context(calendar_status="boundary_caution"))
        self.assertEqual(caution.calendar_validation_status, "boundary_caution")

from engine.calendar.sexagenary import GAN, ZHI, five_mouse_hour
from engine.ziwei.fine_cycle_stems import resolve_hour_stem


class FineCycleHourTests(unittest.TestCase):
    def test_public_regular_hour_vector(self):
        result = resolve_hour_stem(calendar_context(
            gregorian_date=date(1987, 12, 6),
            local_hour=21,
            local_minute=30,
            hour_branch="亥",
        ))
        self.assertEqual((result.heavenly_stem, result.earthly_branch), ("乙", "亥"))
        self.assertEqual(result.effective_date, date(1987, 12, 6))
        self.assertEqual(result.hour_branch, "亥")

    def test_late_zi_uses_next_day_stem_for_hour(self):
        context = calendar_context(
            gregorian_date=date(1987, 12, 6),
            local_hour=23,
            local_minute=30,
            hour_branch="子",
        )
        day = resolve_day_stem(context)
        hour = resolve_hour_stem(context)
        self.assertEqual(day.heavenly_stem, "庚")
        self.assertEqual((hour.heavenly_stem, hour.earthly_branch), ("丙", "子"))
        self.assertEqual(hour.effective_date, day.effective_date)
        self.assertEqual(hour.reference, "ziwei-hour:1987-12-07:子@late_zi_forward-v1")

    def test_all_ten_day_stems_by_twelve_hour_branches(self):
        first_hour_stem = {
            "甲": "甲", "己": "甲",
            "乙": "丙", "庚": "丙",
            "丙": "戊", "辛": "戊",
            "丁": "庚", "壬": "庚",
            "戊": "壬", "癸": "壬",
        }
        for day_stem in GAN:
            start = GAN.index(first_hour_stem[day_stem])
            for branch_index, branch in enumerate(ZHI):
                expected = (GAN[(start + branch_index) % 10], branch)
                self.assertEqual(five_mouse_hour(day_stem, branch), expected)

    def test_resolver_uses_calendar_hour_branch_without_recomputing_from_clock(self):
        result = resolve_hour_stem(calendar_context(
            gregorian_date=date(1987, 12, 6),
            local_hour=21,
            local_minute=30,
            hour_branch="子",
        ))
        self.assertEqual(result.earthly_branch, "子")
        self.assertEqual(result.hour_branch, "子")

    def test_hour_inherits_context_fail_closed_guards(self):
        with self.assertRaises(ZiweiFineCycleError) as cm1:
            resolve_hour_stem(calendar_context(calendar_status="boundary_conflict"))
        self.assertEqual(cm1.exception.code, "calendar_context_unusable")
        with self.assertRaises(ZiweiFineCycleError) as cm2:
            resolve_hour_stem(calendar_context(metaphysics_day_boundary_applied=True))
        self.assertEqual(cm2.exception.code, "calendar_boundary_already_applied")
