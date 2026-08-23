import copy
import hashlib
import json
import unittest

from engine.distribution.calibration import (
    finalize_historical_calibration,
    lock_blind_forecast,
    lock_historical_calibration,
)

from tests.historical_authority_helpers import authoritative_finalize, authoritative_lock


BASE_FILES = [
    "00_專案索引.md",
    "01_命盤核心摘要.md",
    "02_命盤資料校驗紀錄.md",
    "03_八字結構化資料包.md",
    "04_紫微基礎資料包.md",
]


def _rank(tier1=0, tier2=0, tier3=0):
    return {
        "tier1_family_count": tier1,
        "tier1_evidence_count": tier1,
        "cross_layer_tier1": False,
        "tier2_family_count": tier2,
        "tier2_evidence_count": tier2,
        "tier3_family_count": tier3,
        "tier3_evidence_count": tier3,
    }


def _selector_row(year, rank, start=None, end=None):
    return {
        "label_year": year,
        "period_start": start or "%04d-02-04T12:00:00+08:00" % year,
        "period_end": end or "%04d-02-04T12:00:00+08:00" % (year + 1),
        "flow_year_pillar": "甲子",
        "decadal_index": 4,
        "decadal_pillar": "甲子",
        "decadal_boundary_in_period": False,
        "decadal_boundary_datetimes": [],
        "rank_vector": rank,
        "evidence": [],
    }


def _selector_result():
    ranked = [
        _selector_row(2016, _rank(tier1=4), "2016-02-04T17:00:00+08:00", "2017-02-03T22:00:00+08:00"),
        _selector_row(2018, _rank(tier1=3), "2018-02-04T05:00:00+08:00", "2019-02-04T11:00:00+08:00"),
        _selector_row(2020, _rank(tier1=2), "2020-02-04T17:00:00+08:00", "2021-02-03T22:00:00+08:00"),
        _selector_row(2023, _rank(tier1=1), "2023-02-04T10:00:00+08:00", "2024-02-04T16:00:00+08:00"),
        _selector_row(2025, _rank(tier2=3)),
        _selector_row(2024, _rank(tier2=2)),
        _selector_row(2022, _rank(tier2=1)),
        _selector_row(2021, _rank(tier3=3)),
        _selector_row(2017, _rank(tier3=1)),
        _selector_row(2019, _rank(), "2019-02-04T11:00:00+08:00", "2020-02-04T17:00:00+08:00"),
    ]
    result = {
        "profile_id": "historical-activation-bazi-v1",
        "rule_version": "1.0-exp",
        "as_of_datetime": "2026-08-23T10:30:00+08:00",
        "timezone": "Asia/Taipei",
        "ranked_periods": ranked,
        "high_years": ranked[:4],
        "control_year": ranked[-1],
        "control_quality": "strong_control",
        "major_cycle_coverage": "single_cycle",
    }
    canonical = {
        "profile_id": result["profile_id"],
        "rule_version": result["rule_version"],
        "as_of_datetime": result["as_of_datetime"],
        "timezone": result["timezone"],
        "ranked_periods": result["ranked_periods"],
        "high_year_labels": [row["label_year"] for row in result["high_years"]],
        "control_year_label": result["control_year"]["label_year"],
        "control_quality": result["control_quality"],
        "major_cycle_coverage": result["major_cycle_coverage"],
    }
    raw = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    result["selection_digest"] = hashlib.sha256(raw).hexdigest()
    return result


SELECTOR_RESULT = _selector_result()


def point(year, role="high_activation", blindness="blind"):
    return {
        "reference_year": year,
        "role": role,
        "primary_domains": ["工作／職責"],
        "event_family": ["職務或責任結構改變"],
        "confidence": "medium",
        "interpretation_text": "%s 流年工作／職責可能有明顯變化" % year,
        "blindness_status": blindness,
    }


class HistoricalCalibrationTests(unittest.TestCase):
    def test_blind_forecast_lock_is_deterministic_and_base_only(self):
        payload = {
            "blind_forecast_id": "bf-001",
            "subject_id": "case-001",
            "question_type": "流年問事",
            "question_reference": "2027-work",
            "locked_at": "2026-08-23T10:30:00+08:00",
            "source_files_used": BASE_FILES,
            "blind_forecast_payload": {"核心結論": "2027工作責任活躍"},
        }
        first = lock_blind_forecast(payload)
        second = lock_blind_forecast(payload)
        self.assertEqual(first, second)
        self.assertEqual(len(first["payload_digest"]), 64)

        bad = dict(payload)
        bad["source_files_used"] = BASE_FILES + ["05_驗證事件紀錄.md"]
        with self.assertRaises(ValueError):
            lock_blind_forecast(bad)

    def test_blind_forecast_rejects_mixed_subject_aware_base_files(self):
        payload = {
            "blind_forecast_id": "bf-mixed-subjects",
            "subject_id": "subj_aaaaaaaaaaaa",
            "question_type": "流年問事",
            "question_reference": "2027-work",
            "locked_at": "2026-08-23T10:30:00+08:00",
            "source_files_used": [
                "Kai_AAAAAA_00_專案索引.md",
                "Other_BBBBBB_01_命盤核心摘要.md",
                "Kai_AAAAAA_02_命盤資料校驗紀錄.md",
                "Other_BBBBBB_03_八字結構化資料包.md",
                "Kai_AAAAAA_04_紫微基礎資料包.md",
            ],
            "blind_forecast_payload": {"核心結論": "2027工作責任活躍"},
        }
        with self.assertRaises(ValueError):
            lock_blind_forecast(payload)

    def test_blind_forecast_rejects_subject_id_short_id_mismatch(self):
        payload = {
            "blind_forecast_id": "bf-subject-mismatch",
            "subject_id": "subj_aaaaaaaaaaaa",
            "question_type": "flow-year",
            "question_reference": "2027-work",
            "locked_at": "2026-08-23T10:30:00+08:00",
            "source_files_used": [
                "Kai_BBBBBB_00_專案索引.md",
                "Kai_BBBBBB_01_命盤核心摘要.md",
                "Kai_BBBBBB_02_命盤資料校驗紀錄.md",
                "Kai_BBBBBB_03_八字結構化資料包.md",
                "Kai_BBBBBB_04_紫微基礎資料包.md",
            ],
            "blind_forecast_payload": {"summary": "active"},
        }
        with self.assertRaises(ValueError):
            lock_blind_forecast(payload)

    def test_historical_lock_binds_exact_selector_selection(self):
        points = [point(2016), point(2018), point(2020), point(2023), point(2019, "control")]
        result = authoritative_lock(
            {
                "calibration_id": "HC-2026-001",
                "subject_id": "case-001",
                "selector_result": SELECTOR_RESULT,
                "canonical_test_points": points,
                "supplemental_blind_points": [],
                "locked_at": "2026-08-23T10:31:00+08:00",
            }
        )
        self.assertEqual(result["canonical_selection_digest"], SELECTOR_RESULT["selection_digest"])
        self.assertEqual(len(result["payload_digest"]), 64)
        self.assertEqual([p["reference_year"] for p in result["locked_payload"]["canonical_test_points"]], [2016, 2018, 2020, 2023, 2019])
        self.assertIn("period_start", result["locked_payload"]["canonical_test_points"][0])

        wrong = points[:]
        wrong[0] = point(2017)
        with self.assertRaises(ValueError):
            authoritative_lock(
                {
                    "calibration_id": "HC-2026-002",
                    "subject_id": "case-001",
                    "selector_result": SELECTOR_RESULT,
                    "canonical_test_points": wrong,
                    "supplemental_blind_points": [],
                    "locked_at": "2026-08-23T10:31:00+08:00",
                }
            )

    def test_supplemental_points_do_not_change_canonical_selection_digest(self):
        points = [point(2016), point(2018), point(2020), point(2023), point(2019, "control")]
        base = {
            "calibration_id": "HC-2026-001",
            "subject_id": "case-001",
            "selector_result": SELECTOR_RESULT,
            "canonical_test_points": points,
            "locked_at": "2026-08-23T10:31:00+08:00",
        }
        one = authoritative_lock({**base, "supplemental_blind_points": []})
        two = authoritative_lock({**base, "supplemental_blind_points": [point(2021)]})
        self.assertEqual(one["canonical_selection_digest"], two["canonical_selection_digest"])
        self.assertNotEqual(one["payload_digest"], two["payload_digest"])

    def test_finalize_rejects_tampered_locked_payload(self):
        locked = authoritative_lock(
            {
                "calibration_id": "HC-2026-001",
                "subject_id": "case-001",
                "selector_result": SELECTOR_RESULT,
                "canonical_test_points": [point(2016), point(2018), point(2020), point(2023), point(2019, "control")],
                "supplemental_blind_points": [],
                "locked_at": "2026-08-23T10:31:00+08:00",
            }
        )
        tampered = copy.deepcopy(locked["locked_payload"])
        tampered["canonical_test_points"][0]["interpretation_text"] = "事後改答案"
        with self.assertRaises(ValueError):
            authoritative_finalize(locked, 
                {
                    "locked_payload": tampered,
                    "payload_digest": locked["payload_digest"],
                    "responses": [],
                }
            )

    def test_finalize_maps_january_actual_date_to_same_flow_year(self):
        locked = authoritative_lock(
            {
                "calibration_id": "HC-2026-001",
                "subject_id": "case-001",
                "selector_result": SELECTOR_RESULT,
                "canonical_test_points": [point(2016), point(2018), point(2020), point(2023), point(2019, "control")],
                "supplemental_blind_points": [],
                "locked_at": "2026-08-23T10:31:00+08:00",
            }
        )
        result = authoritative_finalize(locked, 
            {
                "locked_payload": locked["locked_payload"],
                "payload_digest": locked["payload_digest"],
                "responses": [
                    {
                        "reference_year": 2016,
                        "verification_state": "matched",
                        "actual_date": "2017-01-15",
                        "actual_event": "換工作並升任主管",
                    }
                ],
            }
        )
        evaluation = result["records"][0]["evaluation"]
        self.assertEqual(evaluation["timing_status"], "exact_flow_year")
        self.assertEqual(evaluation["offset_flow_years"], 0)

    def test_finalize_marks_after_next_lichun_as_shifted(self):
        locked = authoritative_lock(
            {
                "calibration_id": "HC-2026-001",
                "subject_id": "case-001",
                "selector_result": SELECTOR_RESULT,
                "canonical_test_points": [point(2016), point(2018), point(2020), point(2023), point(2019, "control")],
                "supplemental_blind_points": [],
                "locked_at": "2026-08-23T10:31:00+08:00",
            }
        )
        result = authoritative_finalize(locked, 
            {
                "locked_payload": locked["locked_payload"],
                "payload_digest": locked["payload_digest"],
                "responses": [
                    {
                        "reference_year": 2016,
                        "verification_state": "partial",
                        "actual_date": "2017-03-01",
                        "actual_event": "工作內容改變",
                    }
                ],
            }
        )
        evaluation = result["records"][0]["evaluation"]
        self.assertEqual(evaluation["timing_status"], "shifted")
        self.assertEqual(evaluation["offset_flow_years"], 1)

    def test_cannot_recall_is_unscorable_and_creates_no_actual_event(self):
        locked = authoritative_lock(
            {
                "calibration_id": "HC-2026-001",
                "subject_id": "case-001",
                "selector_result": SELECTOR_RESULT,
                "canonical_test_points": [point(2016), point(2018), point(2020), point(2023), point(2019, "control")],
                "supplemental_blind_points": [],
                "locked_at": "2026-08-23T10:31:00+08:00",
            }
        )
        result = authoritative_finalize(locked, 
            {
                "locked_payload": locked["locked_payload"],
                "payload_digest": locked["payload_digest"],
                "responses": [{"reference_year": 2016, "verification_state": "cannot_recall"}],
            }
        )
        record = result["records"][0]
        self.assertNotIn("user_confirmed_actual", record)
        self.assertEqual(record["evaluation"]["timing_status"], "unscorable")
        self.assertEqual(result["historical_calibration_status"], "uncalibrated")

    def test_three_blind_scorable_points_produce_basic_but_contaminated_do_not_count(self):
        points = [
            point(2016), point(2018), point(2020), point(2023, blindness="contaminated"), point(2019, "control")
        ]
        locked = authoritative_lock(
            {
                "calibration_id": "HC-2026-001",
                "subject_id": "case-001",
                "selector_result": SELECTOR_RESULT,
                "canonical_test_points": points,
                "supplemental_blind_points": [],
                "locked_at": "2026-08-23T10:31:00+08:00",
            }
        )
        responses = [
            {"reference_year": 2016, "verification_state": "matched", "actual_event": "A"},
            {"reference_year": 2018, "verification_state": "not_matched", "actual_event": "B"},
            {"reference_year": 2020, "verification_state": "partial", "actual_event": "C"},
            {"reference_year": 2023, "verification_state": "matched", "actual_event": "D"},
        ]
        result = authoritative_finalize(locked, 
            {"locked_payload": locked["locked_payload"], "payload_digest": locked["payload_digest"], "responses": responses}
        )
        self.assertEqual(result["blind_scorable_count"], 3)
        self.assertEqual(result["historical_calibration_status"], "basic")


if __name__ == "__main__":
    unittest.main()
