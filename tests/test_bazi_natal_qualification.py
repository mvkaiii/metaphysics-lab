import json
import unittest
from pathlib import Path

from tools.qualify_bazi_natal import (
    PUBLIC_CASE_IDS,
    build_public_report,
    hidden_stem_table_qualification,
    qualify_public_cases,
)


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
ALLOWED_FIELD_STATUSES = {"MATCH", "CONFLICT/profile_difference", "MISMATCH"}


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

    def test_hidden_stem_reference_table_has_only_one_known_order_difference(self):
        comparison = hidden_stem_table_qualification()
        self.assertEqual(comparison["unexpected_mismatch_count"], 0)
        self.assertEqual(comparison["profile_difference_count"], 1)
        by_branch = {item["branch"]: item for item in comparison["branches"]}
        self.assertEqual(by_branch["巳"]["status"], "CONFLICT/profile_difference")
        self.assertEqual(by_branch["巳"]["project"], ["丙", "戊", "庚"])
        self.assertEqual(by_branch["巳"]["reference"], ["丙", "庚", "戊"])
        for branch, item in by_branch.items():
            if branch != "巳":
                self.assertEqual(item["status"], "MATCH")

    def test_live_public_qualification_has_explicit_status_for_every_required_field(self):
        report = qualify_public_cases()
        self.assertEqual(report["reference_engine"], "lunar-python")
        self.assertEqual(report["reference_version"], "1.4.8")
        self.assertEqual(report["project_profile"], "bazi-natal-project-v1")
        self.assertEqual(report["project_rule_version"], "1.0-exp")
        self.assertEqual(
            report["unexpected_mismatch_count"],
            0,
            json.dumps(report, ensure_ascii=False, indent=2),
        )
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
                        "hidden_stems": {"status": "MISMATCH"},
                    },
                }
            ]
        )
        self.assertEqual(report["matched_field_count"], 1)
        self.assertEqual(report["profile_difference_count"], 1)
        self.assertEqual(report["unexpected_mismatch_count"], 1)

    def test_committed_public_summary_is_complete_and_privacy_safe(self):
        public = json.loads(PUBLIC_REPORT.read_text(encoding="utf-8"))
        self.assertEqual(public["classification"], "public_bazi_natal_qualification_summary")
        self.assertEqual(public["reference_engine"], "lunar-python")
        self.assertEqual(public["reference_version"], "1.4.8")
        self.assertEqual(public["project_profile"], "bazi-natal-project-v1")
        self.assertEqual(public["project_rule_version"], "1.0-exp")
        self.assertEqual(public["status"], "PASS")
        self.assertEqual(public["case_count"], 13)
        self.assertEqual(public["matched_field_count"], 54)
        self.assertEqual(public["profile_difference_count"], 23)
        self.assertEqual(public["unexpected_mismatch_count"], 0)
        self.assertEqual(set(public["case_ids"]), REQUIRED_CASE_IDS)
        self.assertEqual(public["hidden_stem_table"]["matched_branch_count"], 11)
        self.assertEqual(public["hidden_stem_table"]["profile_difference_count"], 1)
        self.assertEqual(public["hidden_stem_table"]["unexpected_mismatch_count"], 0)
        digest = public["live_report_sha256"]
        self.assertEqual(len(digest), 64)
        self.assertTrue(all(char in "0123456789abcdef" for char in digest))
        self.assertTrue(FORBIDDEN_KEYS.isdisjoint(set(walk_keys(public))))

    def test_private_evidence_remains_pending_without_private_source_and_is_privacy_safe(self):
        private = json.loads(PRIVATE_SUMMARY.read_text(encoding="utf-8"))
        self.assertEqual(private["classification"], "private_bazi_natal_qualification_summary")
        self.assertEqual(private["status"], "PENDING")
        self.assertTrue(FORBIDDEN_KEYS.isdisjoint(set(walk_keys(private))))


if __name__ == "__main__":
    unittest.main()
