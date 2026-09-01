import unittest

from tools.check_phase2c_rule_source import check_phase2c_rule_source


class Phase2CRuleSourceTests(unittest.TestCase):
    def test_current_approved_phase2c_state_matches_rule_source(self):
        report = check_phase2c_rule_source()
        self.assertEqual(report["release_identity"], "v1.5.0")
        self.assertEqual(report["expected_release_identity"], "v1.5.0")
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["checks"]["ziwei.transformations"], "implemented/stable/on_demand")
        self.assertEqual(report["checks"]["ziwei.flying"], "implemented/stable/on_demand")
        self.assertEqual(report["checks"]["ziwei.flow_month_stem"], "implemented/experimental/on_demand")
        self.assertEqual(report["checks"]["ziwei.flow_day_stem"], "implemented/experimental/on_demand")
        self.assertEqual(report["checks"]["ziwei.flow_hour_stem"], "implemented/experimental/on_demand")
        self.assertEqual(report["checks"]["ziwei.natal_chart"], "implemented/experimental/on_demand")
        self.assertEqual(report["checks"]["ziwei.flowing_stars"], "implemented/experimental/on_demand")


if __name__ == "__main__":
    unittest.main()
