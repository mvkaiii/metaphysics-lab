import json
import unittest
from copy import deepcopy
from pathlib import Path

from engine.distribution.guided_inquiry import suggest_inquiries
from engine.distribution.runtime import dispatch, runtime_info


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "v1.7-guided-inquiry.synthetic.json"


class GuidedInquiryRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scenarios = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def scenario(self, scenario_id):
        return deepcopy(self.scenarios[scenario_id])

    def test_runtime_info_exposes_suggest_inquiries_action(self):
        self.assertIn("suggest_inquiries", runtime_info()["supported_actions"])

    def test_dispatch_matches_direct_policy_output(self):
        for scenario_id in ("GI-01", "GI-04", "GI-07"):
            with self.subTest(scenario_id=scenario_id):
                payload = self.scenario(scenario_id)
                expected = suggest_inquiries(payload)
                actual = dispatch("suggest_inquiries", payload)
                self.assertTrue(actual["ok"], actual)
                self.assertEqual(actual["action"], "suggest_inquiries")
                self.assertEqual(actual["data"], expected)


if __name__ == "__main__":
    unittest.main()
