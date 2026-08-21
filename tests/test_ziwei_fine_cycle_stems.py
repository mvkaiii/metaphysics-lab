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
