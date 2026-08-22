import json
import unittest
from pathlib import Path

from tools.qualify_bazi_natal import PUBLIC_CASE_IDS, build_public_report, qualify_public_cases


PUBLIC_REPORT = Path("qualification/bazi/natal/public-lunar-python-1.4.8.json")
PRIVATE_SUMMARY = Path("qualification/bazi/natal/private-summary.json")
FORBIDDEN_KEYS = {"name", "full_address", "birth_datetime", "raw_chart", "raw_payload"}
REQUIRED_CASE_IDS = {
    "normal_daytime",
    "late_zi_2259",
    "late_zi_2300",
    "late_zi_2359",
    "midnight_0000",
    "before_lichun",
    "after_lichun",
    "before_jingzhe",
    "after_jingzhe",
    "male_direction",
    "female_direction",
    "time_profile_equivalent",
    "time_profile_hour_conflict",
}
REQUIRED_FIELDS = {
    "four_pillars",
    "day_master",
    "hidden_stems",
    "ten_gods",
    "decadal_direction",
    "decadal_start_age",
    "decadal_pillar_sequence",
}
ALLOWED_FIELD_STATUSES = {"MATCH", "CONFLICT/profile_difference"}


def walk_keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from walk_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk_keys(item)


class BaziNatalQualificationTests(unittest.TestCase):
    def test_public_matrix_covers_required_boundaries_and_profiles(self):
        self.assertTrue(REQUIRED_CASE_IDS.issubset(set(PUBLIC_CASE_IDS)))

    def test_live_public_qualification_has_explicit_status_for_every_required_field(self):
        report = qualify_public_cases()
        self.assertEqual(report["reference_engine"], "lunar-python")
        self.assertEqual(report["reference_version"], "1.4.8")
        self.assertEqual(report["project_profile"], "bazi-natal-project-v1")
        self.assertEqual(report["project_rule_version"], "1.0-exp")
        by_id = {case["case_id"]: case for case in report["cases"]}
        for case_id in REQUIRED_CASE_IDS - {"time_profile_equivalent", "time_profile_hour_conflict"}:
            self.assertIn(case_id, by_id)
            self.assertEqual(set(by_id[case_id]["fields"]), REQUIRED_FIELDS)
            for field in by_id[case_id]["fields"].values():
                self.assertIn(field["status"], ALLOWED_FIELD_STATUSES)
        self.assertTrue(FORBIDDEN_KEYS.isdisjoint(set(walk_keys(report))))

    def test_time_profile_cases_remain_project_comparison_evidence(self):
        report = qualify_public_cases()
        by_id = {case["case_id"]: case for case in report["cases"]}
        equivalent = by_id["time_profile_equivalent"]
        conflict = by_id["time_profile_hour_conflict"]
        self.assertEqual(equivalent["comparison_status"], "EQUIVALENT")
        self.assertEqual(conflict["comparison_status"], "CONFLICT")
        self.assertEqual(conflict["affected_components"], ["hour"])

    def test_report_builder_counts_match_and_profile_differences_without_hiding_them(self):
        report = build_public_report(
            [
                {
                    "case_id": "fixture",
                    "fields": {
                        "four_pillars": {"status": "MATCH"},
                        "decadal_start_age": {"status": "CONFLICT/profile_difference"},
                    },
                }
            ]
        )
        self.assertEqual(report["matched_field_count"], 1)
        self.assertEqual(report["profile_difference_count"], 1)
        self.assertEqual(report["unexpected_mismatch_count"], 0)

    def test_committed_public_and_private_evidence_are_privacy_safe(self):
        for path in (PUBLIC_REPORT, PRIVATE_SUMMARY):
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(FORBIDDEN_KEYS.isdisjoint(set(walk_keys(payload))))
        public = json.loads(PUBLIC_REPORT.read_text(encoding="utf-8"))
        private = json.loads(PRIVATE_SUMMARY.read_text(encoding="utf-8"))
        self.assertEqual(public["reference_version"], "1.4.8")
        self.assertEqual(private["classification"], "private_bazi_natal_qualification_summary")
        self.assertIn(private["status"], ("PENDING", "PASS", "FAIL"))


if __name__ == "__main__":
    unittest.main()
