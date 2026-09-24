import json
import subprocess
import sys
import unittest
from pathlib import Path

from engine.distribution.runtime import dispatch


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "v1.7-guided-inquiry.synthetic.json"
BUNDLE = ROOT / "dist" / "ai" / "metaphysics_lab.py"


class GuidedInquiryDistributionParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scenarios = json.loads(FIXTURE.read_text(encoding="utf-8"))
        if not BUNDLE.exists():
            raise AssertionError("generated bundle is missing: %s" % BUNDLE)

    @staticmethod
    def bundled_dispatch(payload):
        request = json.dumps(
            {"action": "suggest_inquiries", "payload": payload},
            ensure_ascii=False,
        )
        completed = subprocess.run(
            [sys.executable, str(BUNDLE), "request", "--input", "-"],
            cwd=str(ROOT),
            input=request,
            text=True,
            capture_output=True,
        )
        if completed.returncode != 0:
            raise AssertionError(completed.stdout + completed.stderr)
        try:
            return json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise AssertionError(completed.stdout + completed.stderr) from exc

    def iter_payloads(self):
        for scenario_id in sorted(self.scenarios):
            scenario = self.scenarios[scenario_id]
            if scenario_id == "GI-12":
                yield scenario_id + ":payload_a", scenario["payload_a"]
                yield scenario_id + ":payload_b", scenario["payload_b"]
            else:
                yield scenario_id, scenario

    def test_all_guided_inquiry_fixtures_match_modular_runtime(self):
        seen = []
        for case_id, payload in self.iter_payloads():
            with self.subTest(case_id=case_id):
                modular = dispatch("suggest_inquiries", payload)
                self.assertTrue(modular["ok"], modular)
                bundled = self.bundled_dispatch(payload)
                self.assertEqual(bundled, modular)
                seen.append(case_id)
        self.assertEqual(
            seen,
            [
                "GI-01",
                "GI-02",
                "GI-03",
                "GI-04",
                "GI-05",
                "GI-06",
                "GI-07",
                "GI-08",
                "GI-09",
                "GI-10",
                "GI-11",
                "GI-12:payload_a",
                "GI-12:payload_b",
            ],
        )


if __name__ == "__main__":
    unittest.main()
