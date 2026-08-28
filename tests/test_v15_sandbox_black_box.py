import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tools" / "run_v15_sandbox_black_box.py"


class V15SandboxBlackBoxTests(unittest.TestCase):
    def test_all_critical_black_box_rubric_items_pass(self):
        spec = importlib.util.spec_from_file_location("v15_black_box", RUNNER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        report = module.run(ROOT / "dist" / "ai")
        self.assertEqual(report["status"], "PASS", report)
        self.assertTrue(report["runtime_ok"], report)
        self.assertEqual(len(report["rubric"]), 8)
        self.assertTrue(all(row["status"] == "PASS" for row in report["rubric"]), report)


if __name__ == "__main__":
    unittest.main()
