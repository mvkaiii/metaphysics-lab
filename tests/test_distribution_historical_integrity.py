import copy
import hashlib
import json
import unittest

from engine.distribution.calibration import (
    finalize_historical_calibration,
    lock_historical_calibration,
)


def _row(year):
    return {
        "label_year": year,
        "period_start": "%04d-02-04T12:00:00+08:00" % year,
        "period_end": "%04d-02-04T12:00:00+08:00" % (year + 1),
        "flow_year_pillar": "甲子",
        "rank_vector": {
            "tier1_family_count": 0,
            "tier1_evidence_count": 0,
            "cross_layer_tier1": False,
            "tier2_family_count": 0,
            "tier2_evidence_count": 0,
            "tier3_family_count": 0,
            "tier3_evidence_count": 0,
        },
        "evidence": [],
    }


def _digest(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def selector_result():
    years = [2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016]
    ranked = [_row(year) for year in years]
    result = {
        "profile_id": "historical-activation-bazi-v1",
        "rule_version": "1.0-exp",
        "as_of_datetime": "2026-08-23T10:55:00+08:00",
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
    result["selection_digest"] = _digest(canonical)
    return result


def point(year, role="high_activation"):
    return {
        "reference_year": year,
        "role": role,
        "primary_domains": ["工作／職責"],
        "event_family": ["角色結構改變"],
        "confidence": "medium",
        "interpretation_text": "%s 流年工作／職責可能有明顯變化" % year,
        "blindness_status": "blind",
    }


def lock(selector=None, supplemental=None):
    selector = selector_result() if selector is None else selector
    years = [row["label_year"] for row in selector["high_years"]]
    points = [point(year) for year in years]
    points.append(point(selector["control_year"]["label_year"], "control"))
    return lock_historical_calibration({
        "calibration_id": "HC-integrity-001",
        "subject_id": "case-integrity",
        "selector_result": selector,
        "canonical_test_points": points,
        "supplemental_blind_points": [] if supplemental is None else supplemental,
        "locked_at": "2026-08-23T10:56:00+08:00",
    })


class HistoricalCalibrationIntegrityTests(unittest.TestCase):
    def test_lock_rejects_high_year_override_even_when_test_points_follow_override(self):
        tampered = selector_result()
        tampered["high_years"] = [
            tampered["ranked_periods"][0],
            tampered["ranked_periods"][1],
            tampered["ranked_periods"][2],
            tampered["ranked_periods"][5],
        ]
        with self.assertRaises(ValueError):
            lock(tampered)

    def test_lock_rejects_selector_content_changed_without_new_digest(self):
        tampered = selector_result()
        tampered = copy.deepcopy(tampered)
        tampered["ranked_periods"][5]["flow_year_pillar"] = "乙丑"
        with self.assertRaises(ValueError):
            lock(tampered)

    def test_finalize_rejects_duplicate_responses_for_same_locked_point(self):
        locked = lock()
        duplicate = {
            "reference_year": 2025,
            "verification_state": "matched",
            "actual_event": "同一題重複提交",
        }
        with self.assertRaises(ValueError):
            finalize_historical_calibration({
                "locked_payload": locked["locked_payload"],
                "payload_digest": locked["payload_digest"],
                "responses": [duplicate, duplicate, duplicate],
            })

    def test_lock_rejects_supplemental_point_outside_ranked_ten_year_window(self):
        with self.assertRaises(ValueError):
            lock(supplemental=[point(2015)])

    def test_lock_rejects_supplemental_point_that_duplicates_canonical_year(self):
        with self.assertRaises(ValueError):
            lock(supplemental=[point(2025)])

    def test_lock_rejects_duplicate_supplemental_years(self):
        with self.assertRaises(ValueError):
            lock(supplemental=[point(2020), point(2020)])


if __name__ == "__main__":
    unittest.main()
