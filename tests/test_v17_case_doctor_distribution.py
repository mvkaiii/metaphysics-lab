import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from engine.distribution.runtime import dispatch
from tools import build_ai_distribution


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist" / "ai"
WORKFLOW = ROOT / "core" / "AI工作流程.md"


class CaseDoctorDistributionTests(unittest.TestCase):
    def _bundle_request(self, action, payload):
        with tempfile.TemporaryDirectory() as temp_dir:
            request_path = Path(temp_dir) / "request.json"
            request_path.write_text(
                json.dumps({"action": action, "payload": payload}, ensure_ascii=False),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(DIST / "metaphysics_lab.py"),
                    "request",
                    "--input",
                    str(request_path),
                ],
                cwd=str(ROOT),
                check=True,
                capture_output=True,
                text=True,
            )
        return json.loads(completed.stdout)

    def test_ai_workflow_requires_case_doctor_before_case_authority(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        for required in (
            "Case Doctor",
            "diagnose_case",
            "plan_case_reconciliation",
            "safe_analysis_scopes",
            "BLOCKED",
            "WARN",
            "不得自動刪除 legacy",
            "不得自動合併",
        ):
            self.assertIn(required, text)

    def test_generated_core_contains_case_doctor_workflow_contract(self):
        text = (DIST / "metaphysics_core.md").read_text(encoding="utf-8")
        self.assertIn("diagnose_case", text)
        self.assertIn("plan_case_reconciliation", text)
        self.assertIn("safe_analysis_scopes", text)
        self.assertIn("不得自動刪除 legacy", text)

    def test_committed_distribution_matches_official_generator(self):
        expected = build_ai_distribution.render_distribution(ROOT)
        for name, content in expected.items():
            self.assertEqual((DIST / name).read_bytes(), content, name)

    def test_bundled_runtime_advertises_case_doctor_actions(self):
        result = self._bundle_request("runtime_info", {})
        self.assertTrue(result["ok"], result)
        actions = result["data"]["supported_actions"]
        self.assertIn("diagnose_case", actions)
        self.assertIn("plan_case_reconciliation", actions)

    def test_modular_and_bundled_diagnose_case_are_identical(self):
        payload = {"project_files": {}, "subject_context": {}}
        modular = dispatch("diagnose_case", payload)
        bundled = self._bundle_request("diagnose_case", payload)
        self.assertEqual(bundled, modular)

    def test_modular_and_bundled_planner_are_identical(self):
        project_files = {}
        diagnostic = dispatch(
            "diagnose_case",
            {"project_files": project_files, "subject_context": {}},
        )
        self.assertTrue(diagnostic["ok"], diagnostic)
        payload = {
            "project_files": project_files,
            "diagnostic": diagnostic["data"],
        }
        modular = dispatch("plan_case_reconciliation", payload)
        bundled = self._bundle_request("plan_case_reconciliation", payload)
        self.assertEqual(bundled, modular)


if __name__ == "__main__":
    unittest.main()
