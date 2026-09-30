import json
from datetime import datetime
from pathlib import Path
import unittest
from zoneinfo import ZoneInfo

from lunar_python import Lunar

from engine.bazi.calendar import solar_term_time
from tools.pilot4_structural_snapshot_enumerator import (
    REQUESTED_SCOPES,
    STRUCTURAL_SNAPSHOT_ENUMERATION_PROFILE,
    STRUCTURAL_SNAPSHOT_ENUMERATION_RULE,
    build_snapshot_manifest_from_enumeration,
    enumerate_structural_snapshot_segments,
    validate_structural_snapshot_enumeration,
)


POLICY_DIGEST = "1" * 64


def periods(*, boundary=None):
    rows = [
        {
            "index": 4,
            "pillar": "庚子",
            "start_datetime": "2015-06-01T00:00:00+08:00",
            "end_datetime": "2025-06-01T00:00:00+08:00",
        },
        {
            "index": 5,
            "pillar": "辛丑",
            "start_datetime": "2025-06-01T00:00:00+08:00",
            "end_datetime": "2035-06-01T00:00:00+08:00",
        },
    ]
    if boundary is None:
        return rows
    return [
        {
            "index": 1,
            "pillar": "庚子",
            "start_datetime": "2010-01-01T00:00:00+08:00",
            "end_datetime": boundary,
        },
        {
            "index": 2,
            "pillar": "辛丑",
            "start_datetime": boundary,
            "end_datetime": "2040-01-01T00:00:00+08:00",
        },
    ]


class Pilot4StructuralSnapshotEnumeratorTests(unittest.TestCase):
    def enumerate(self, start, end, decadal=None):
        return enumerate_structural_snapshot_segments(
            window_start=start,
            window_end=end,
            timezone_name="Asia/Taipei",
            window_policy_digest=POLICY_DIGEST,
            bazi_decadal_periods=periods() if decadal is None else decadal,
        )

    def test_contract_identity_and_determinism(self):
        first = self.enumerate(
            "2026-08-20T00:00:00+08:00",
            "2026-10-20T23:59:59+08:00",
        )
        second = self.enumerate(
            "2026-08-20T00:00:00+08:00",
            "2026-10-20T23:59:59+08:00",
        )
        self.assertEqual(first, second)
        self.assertEqual(validate_structural_snapshot_enumeration(first), first)
        self.assertEqual(first["profile_version"], STRUCTURAL_SNAPSHOT_ENUMERATION_PROFILE)
        self.assertEqual(first["enumeration_rule"], STRUCTURAL_SNAPSHOT_ENUMERATION_RULE)
        self.assertEqual(first["requested_scopes"], list(REQUESTED_SCOPES))
        self.assertEqual(first["target_scope"], "yearly")
        self.assertEqual(first["timing_scope"], "monthly")
        self.assertFalse(first["promotion_allowed"])

    def test_bazi_jie_and_boundary_warning_edges_are_explicit_fenceposts(self):
        zone = ZoneInfo("Asia/Taipei")
        term = solar_term_time(2026, "白露", zone)
        start = (term.replace(microsecond=0)).isoformat()
        enumeration = self.enumerate(
            (term.replace(microsecond=0) - __import__("datetime").timedelta(hours=2)).isoformat(),
            (term.replace(microsecond=0) + __import__("datetime").timedelta(hours=2)).isoformat(),
        )
        sources = {
            source
            for segment in enumeration["segments"]
            for source in segment["start_boundary_sources"]
        }
        self.assertIn("bazi_jie:白露", sources)
        self.assertIn("bazi_boundary_warning_enter:白露", sources)
        self.assertIn("bazi_boundary_warning_exit:白露", sources)
        self.assertGreater(enumeration["segment_count"], 1)
        self.assertTrue(start)

    def test_ziwei_leap_month_day16_source_change_is_discovered(self):
        day15 = Lunar.fromYmdHms(2023, -2, 15, 12, 0, 0).getSolar().toYmd()
        day16 = Lunar.fromYmdHms(2023, -2, 16, 12, 0, 0).getSolar().toYmd()
        enumeration = self.enumerate(
            f"{day15}T00:00:00+08:00",
            f"{day16}T23:59:59+08:00",
        )
        change_rows = [
            row
            for row in enumeration["segments"]
            if "ziwei_month_year_calendar_state_change"
            in row["start_boundary_sources"]
        ]
        self.assertEqual(len(change_rows), 1)
        self.assertEqual(change_rows[0]["segment_start"], f"{day16}T00:00:00+08:00")

    def test_bazi_decadal_boundary_is_part_of_census(self):
        boundary = "2026-09-10T12:00:00+08:00"
        enumeration = self.enumerate(
            "2026-09-01T00:00:00+08:00",
            "2026-09-20T23:59:59+08:00",
            decadal=periods(boundary=boundary),
        )
        row = next(
            item
            for item in enumeration["segments"]
            if item["segment_start"] == boundary
        )
        self.assertIn("bazi_decadal_start", row["start_boundary_sources"])
        self.assertIn("bazi_decadal_end", row["start_boundary_sources"])

    def test_manifest_requires_exact_one_digest_per_enumerated_segment(self):
        enumeration = self.enumerate(
            "2026-09-01T00:00:00+08:00",
            "2026-09-20T23:59:59+08:00",
        )
        with self.assertRaises(ValueError):
            build_snapshot_manifest_from_enumeration(
                enumeration=enumeration,
                structural_state_digests=["2" * 64],
            )
        manifest = build_snapshot_manifest_from_enumeration(
            enumeration=enumeration,
            structural_state_digests=[
                ("%064x" % (index + 1))
                for index in range(enumeration["segment_count"])
            ],
        )
        self.assertEqual(
            [row["snapshot_id"] for row in manifest["snapshots"]],
            [row["snapshot_id"] for row in enumeration["segments"]],
        )
        self.assertEqual(
            len(manifest["snapshots"]),
            enumeration["segment_count"],
        )

    def test_pre_efa_enumeration_contains_no_claim_or_outcome_material(self):
        enumeration = self.enumerate(
            "2026-09-01T00:00:00+08:00",
            "2026-09-20T23:59:59+08:00",
        )
        serialized = json.dumps(enumeration, ensure_ascii=False).lower()
        for forbidden in (
            '"claim_id":',
            '"child_claim_id":',
            '"event_family_attribution_digest":',
            '"prediction":',
            '"outcome":',
            '"score":',
        ):
            self.assertNotIn(forbidden, serialized)

    def test_fail_closed_for_wrong_timezone_cross_year_or_overlapping_decadal(self):
        with self.assertRaises(ValueError):
            enumerate_structural_snapshot_segments(
                window_start="2026-09-01T00:00:00+08:00",
                window_end="2026-09-20T23:59:59+08:00",
                timezone_name="UTC",
                window_policy_digest=POLICY_DIGEST,
                bazi_decadal_periods=periods(),
            )
        with self.assertRaises(ValueError):
            self.enumerate(
                "2026-12-01T00:00:00+08:00",
                "2027-01-20T23:59:59+08:00",
            )
        overlapping = [
            {
                "start_datetime": "2020-01-01T00:00:00+08:00",
                "end_datetime": "2030-01-01T00:00:00+08:00",
            },
            {
                "start_datetime": "2025-01-01T00:00:00+08:00",
                "end_datetime": "2035-01-01T00:00:00+08:00",
            },
        ]
        with self.assertRaises(ValueError):
            self.enumerate(
                "2026-09-01T00:00:00+08:00",
                "2026-09-20T23:59:59+08:00",
                decadal=overlapping,
            )


if __name__ == "__main__":
    unittest.main()
