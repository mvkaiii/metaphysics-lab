import json
import subprocess
import sys
import unittest
from pathlib import Path

from tools.qualify_natal_phase2c0 import REQUIRED_SECTIONS, build_phase2c0_summary


SUMMARY_PATH = Path("qualification/natal/phase2c0-summary.json")


class NatalQualificationSummaryTests(unittest.TestCase):
    def test_required_phase_summary_sections_are_fixed(self):
        self.assertEqual(
            REQUIRED_SECTIONS,
            (
                "birth_location_time",
                "bazi_natal",
                "ziwei_natal",
                "reconciliation",
                "markdown_export",
                "regression",
                "privacy",
                "phase2c_boundary",
            ),
        )
        summary = build_phase2c0_summary()
        for section in REQUIRED_SECTIONS:
            self.assertIn(section, summary)

    def test_committed_summary_matches_deterministic_builder(self):
        committed = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
        self.assertEqual(committed, build_phase2c0_summary())
        self.assertEqual(committed["schema_version"], "1.0")
        self.assertEqual(committed["classification"], "phase2c0_qualification_summary")
        self.assertEqual(committed["status"], "PENDING_FINAL_ACCEPTANCE")

    def test_workstream_qualification_evidence_is_aggregated_without_overclaim(self):
        summary = build_phase2c0_summary()

        birth = summary["birth_location_time"]
        self.assertEqual(birth["public_status"], "PENDING_LIVE_QUALIFICATION")
        self.assertEqual(birth["provider"], "nominatim@2.5.0")
        self.assertRegex(birth["source_digest"], r"^sha256:[0-9a-f]{64}$")

        bazi = summary["bazi_natal"]
        self.assertEqual(bazi["public_status"], "PASS")
        self.assertEqual(bazi["reference"], "lunar-python@1.4.8")
        self.assertEqual(bazi["case_count"], 13)
        self.assertEqual(bazi["unexpected_mismatch_count"], 0)
        self.assertEqual(bazi["profile_difference_count"], 23)
        self.assertEqual(bazi["private_status"], "PASS")
        self.assertEqual(bazi["private_case_count"], 1)
        self.assertRegex(bazi["private_source_digest"], r"^sha256:[0-9a-f]{64}$")

        ziwei = summary["ziwei_natal"]
        self.assertEqual(ziwei["public_contract_status"], "PINNED")
        self.assertEqual(ziwei["reference"], "iztro@2.6.0")
        self.assertEqual(ziwei["oracle_revision"], "814b77e6371e1050cac31bbf674db3c3138fcfde")
        self.assertEqual(ziwei["component_expected_check_count"], 1160)
        self.assertEqual(ziwei["integration_expected_chart_count"], 100)
        self.assertEqual(ziwei["boundary_expected_case_count"], 5)
        self.assertEqual(ziwei["private_status"], "PASS")
        self.assertEqual(ziwei["private_case_count"], 1)
        self.assertFalse(ziwei["private_promotion_allowed"])
        self.assertRegex(ziwei["private_source_digest"], r"^sha256:[0-9a-f]{64}$")

    def test_cross_system_capabilities_and_phase2c_boundary_are_exact(self):
        summary = build_phase2c0_summary()
        self.assertEqual(
            summary["reconciliation"],
            {
                "implementation": "implemented",
                "maturity": "stable",
                "routing": "on_demand",
                "rule_version": "1.0",
            },
        )
        self.assertEqual(
            summary["markdown_export"],
            {
                "implementation": "implemented",
                "maturity": "stable",
                "routing": "on_demand",
                "rule_version": "1.0",
            },
        )
        boundary = summary["phase2c_boundary"]
        self.assertEqual(boundary["ziwei_flowing_stars_implementation"], "planned")
        self.assertIsNone(boundary["ziwei_flowing_stars_maturity"])
        self.assertEqual(boundary["ziwei_flowing_stars_routing"], "on_demand")
        self.assertIsNone(boundary["ziwei_flowing_stars_rule_version"])
        self.assertTrue(boundary["phase2c0_only"])

    def test_regression_section_does_not_claim_final_acceptance_early(self):
        regression = build_phase2c0_summary()["regression"]
        self.assertEqual(regression["status"], "PENDING_FINAL_ACCEPTANCE")
        self.assertFalse(regression["phase2c0_acceptance_pass"])
        self.assertEqual(regression["final_gate_task"], 10)

    def test_cli_outputs_same_default_summary(self):
        proc = subprocess.run(
            [sys.executable, "tools/qualify_natal_phase2c0.py", "--compact"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout), build_phase2c0_summary())


if __name__ == "__main__":
    unittest.main()
