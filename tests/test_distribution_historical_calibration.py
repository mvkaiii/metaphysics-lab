import copy
import unittest

from engine.distribution.calibration import (
    finalize_historical_calibration,
    lock_blind_forecast,
    lock_historical_calibration,
)


BASE_FILES = [
    "00_專案索引.md",
    "01_命盤核心摘要.md",
    "02_命盤資料校驗紀錄.md",
    "03_八字結構化資料包.md",
    "04_紫微基礎資料包.md",
]

SELECTOR_RESULT = {
    "selection_digest": "a" * 64,
    "high_years": [
        {"label_year": 2016, "period_start": "2016-02-04T17:00:00+08:00", "period_end": "2017-02-03T22:00:00+08:00"},
        {"label_year": 2018, "period_start": "2018-02-04T05:00:00+08:00", "period_end": "2019-02-04T11:00:00+08:00"},
        {"label_year": 2020, "period_start": "2020-02-04T17:00:00+08:00", "period_end": "2021-02-03T22:00:00+08:00"},
        {"label_year": 2023, "period_start": "2023-02-04T10:00:00+08:00", "period_end": "2024-02-04T16:00:00+08:00"},
    ],
    "control_year": {
        "label_year": 2019,
        "period_start": "2019-02-04T11:00:00+08:00",
        "period_end": "2020-02-04T17:00:00+08:00",
    },
    "control_quality": "strong_control",
}


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

    def test_historical_lock_binds_exact_selector_selection(self):
        points = [point(2016), point(2018), point(2020), point(2023), point(2019, "control")]
        result = lock_historical_calibration(
            {
                "calibration_id": "HC-2026-001",
                "subject_id": "case-001",
                "selector_result": SELECTOR_RESULT,
                "canonical_test_points": points,
                "supplemental_blind_points": [],
                "locked_at": "2026-08-23T10:31:00+08:00",
            }
        )
        self.assertEqual(result["canonical_selection_digest"], "a" * 64)
        self.assertEqual(len(result["payload_digest"]), 64)
        self.assertEqual([p["reference_year"] for p in result["locked_payload"]["canonical_test_points"]], [2016, 2018, 2020, 2023, 2019])
        self.assertIn("period_start", result["locked_payload"]["canonical_test_points"][0])

        wrong = points[:]
        wrong[0] = point(2017)
        with self.assertRaises(ValueError):
            lock_historical_calibration(
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
        one = lock_historical_calibration({**base, "supplemental_blind_points": []})
        two = lock_historical_calibration({**base, "supplemental_blind_points": [point(2021)]})
        self.assertEqual(one["canonical_selection_digest"], two["canonical_selection_digest"])
        self.assertNotEqual(one["payload_digest"], two["payload_digest"])

    def test_finalize_rejects_tampered_locked_payload(self):
        locked = lock_historical_calibration(
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
            finalize_historical_calibration(
                {
                    "locked_payload": tampered,
                    "payload_digest": locked["payload_digest"],
                    "responses": [],
                }
            )

    def test_finalize_maps_january_actual_date_to_same_flow_year(self):
        locked = lock_historical_calibration(
            {
                "calibration_id": "HC-2026-001",
                "subject_id": "case-001",
                "selector_result": SELECTOR_RESULT,
                "canonical_test_points": [point(2016), point(2018), point(2020), point(2023), point(2019, "control")],
                "supplemental_blind_points": [],
                "locked_at": "2026-08-23T10:31:00+08:00",
            }
        )
        result = finalize_historical_calibration(
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
        locked = lock_historical_calibration(
            {
                "calibration_id": "HC-2026-001",
                "subject_id": "case-001",
                "selector_result": SELECTOR_RESULT,
                "canonical_test_points": [point(2016), point(2018), point(2020), point(2023), point(2019, "control")],
                "supplemental_blind_points": [],
                "locked_at": "2026-08-23T10:31:00+08:00",
            }
        )
        result = finalize_historical_calibration(
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
        locked = lock_historical_calibration(
            {
                "calibration_id": "HC-2026-001",
                "subject_id": "case-001",
                "selector_result": SELECTOR_RESULT,
                "canonical_test_points": [point(2016), point(2018), point(2020), point(2023), point(2019, "control")],
                "supplemental_blind_points": [],
                "locked_at": "2026-08-23T10:31:00+08:00",
            }
        )
        result = finalize_historical_calibration(
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
        locked = lock_historical_calibration(
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
        result = finalize_historical_calibration(
            {"locked_payload": locked["locked_payload"], "payload_digest": locked["payload_digest"], "responses": responses}
        )
        self.assertEqual(result["blind_scorable_count"], 3)
        self.assertEqual(result["historical_calibration_status"], "basic")


if __name__ == "__main__":
    unittest.main()
