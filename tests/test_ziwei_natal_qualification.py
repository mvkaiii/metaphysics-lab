import json
import subprocess
import sys
import unittest
from pathlib import Path

from engine.ziwei.capabilities import get_capability, should_run_by_default
from tools.qualify_ziwei_natal import qualify_public


PUBLIC_CONTRACT = Path("qualification/ziwei/natal/public-iztro-814b77e6.json")
PRIVATE_SUMMARY = Path("qualification/ziwei/natal/private-astralium-summary.json")
EXPECTED_REVISION = "814b77e6371e1050cac31bbf674db3c3138fcfde"


class ZiweiNatalQualificationTests(unittest.TestCase):
    def test_public_contract_is_pinned_and_has_required_coverage(self):
        contract = json.loads(PUBLIC_CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(contract["oracle"]["engine"], "iztro")
        self.assertEqual(contract["oracle"]["version"], "2.6.0")
        self.assertEqual(contract["oracle"]["revision"], EXPECTED_REVISION)
        self.assertEqual(sum(row["expected_checks"] for row in contract["component_fixtures"]), 1160)
        self.assertEqual(contract["integration_matrix"]["expected_chart_count"], 100)
        self.assertEqual(len(contract["boundary_matrix"]), 5)
        self.assertEqual(contract["integration_matrix"]["coverage"], {
            "birth_year_stems": 10,
            "sexes": 2,
            "five_element_bureaus": 5,
        })

    def test_public_qualification_has_no_unexpected_mismatch(self):
        result = qualify_public()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["oracle_revision"], EXPECTED_REVISION)
        self.assertEqual(result["component_check_count"], 1160)
        self.assertEqual(result["component_mismatch_count"], 0)
        self.assertEqual(result["integration_chart_count"], 100)
        self.assertEqual(result["integration_failure_count"], 0)
        self.assertEqual(result["boundary_case_count"], 5)
        self.assertEqual(result["boundary_failure_count"], 0)
        self.assertTrue(result["privacy_safe"])

    def test_field_authorities_do_not_overclaim_true_solar_or_private_astrallium(self):
        result = qualify_public()
        authorities = result["field_authorities"]
        self.assertEqual(authorities["true_solar_adjustment"], "project_formula_frozen")
        self.assertEqual(authorities["lunar_birth"], "calendar_resolver_validated")
        for field in (
            "ming_body_palaces", "palace_stems", "five_element_bureau",
            "major_stars", "selected_auxiliary_stars", "brightness",
            "life_body_master", "decadal_cycles",
        ):
            self.assertEqual(authorities[field], "iztro@" + EXPECTED_REVISION)
        self.assertEqual(authorities["birth_transformations"], "phase2a_public_qualified")
        self.assertEqual(authorities["natal_48_flying"], "phase2a_public_qualified")
        self.assertNotIn("Astralium_MATCH", json.dumps(result, ensure_ascii=False))

    def test_private_summary_records_authorized_aggregate_pass_without_raw_payload(self):
        summary = json.loads(PRIVATE_SUMMARY.read_text(encoding="utf-8"))
        self.assertEqual(summary["status"], "PASS")
        self.assertEqual(summary["source_system"], "Astralium")
        self.assertEqual(summary["case_count"], 1)
        self.assertEqual(summary["aggregate_field_conflicts"]["unexpected_mismatch_count"], 0)
        matches = summary["aggregate_field_matches"]
        self.assertEqual(matches["palace_structure_match_count"], 12)
        self.assertEqual(matches["star_position_match_count"], 26)
        self.assertEqual(matches["brightness_match_count"], 20)
        self.assertEqual(matches["birth_transformation_match_count"], 4)
        self.assertEqual(matches["natal_flying_match_count"], 48)
        self.assertEqual(matches["decadal_cycle_match_count"], 12)
        self.assertEqual(matches["total_match_count"], 129)
        self.assertEqual(matches["total_equivalent_count"], 1)
        self.assertFalse(summary["contains_raw_birth_data"])
        self.assertFalse(summary["contains_raw_chart_payload"])
        self.assertFalse(summary["promotion_allowed"])
        self.assertTrue(summary["source_digest"].startswith("sha256:"))
        self.assertTrue(summary["aggregate_digest"].startswith("sha256:"))
        serialized = json.dumps(summary, ensure_ascii=False).lower()
        for forbidden in ("birth_datetime", "reported_datetime", "full_address", "raw_chart", "latitude", "longitude"):
            self.assertNotIn('"%s"' % forbidden, serialized)

    def test_public_report_contains_no_raw_birth_or_location_payload(self):
        serialized = json.dumps(qualify_public(), ensure_ascii=False).lower()
        for forbidden in ("birth_datetime", "reported_datetime", "full_address", "latitude", "longitude", "chart_payload"):
            self.assertNotIn('"%s"' % forbidden, serialized)

    def test_capability_remains_experimental_after_public_pass(self):
        cap = get_capability("ziwei.natal_chart")
        self.assertEqual(cap["maturity"], "experimental")
        self.assertEqual(cap["routing"], "on_demand")
        self.assertFalse(should_run_by_default("ziwei.natal_chart"))

    def test_direct_cli_invocation_can_import_project_engine(self):
        proc = subprocess.run(
            [sys.executable, "tools/qualify_ziwei_natal.py", "--compact"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["component_mismatch_count"], 0)


if __name__ == "__main__":
    unittest.main()
