import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tools" / "run_v15_release_surface_validation.py"


class V15ReleaseSurfaceValidationTests(unittest.TestCase):
    def test_all_release_surface_checks_pass(self):
        spec = importlib.util.spec_from_file_location("v15_release_surface_validation", RUNNER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        report = module.run(ROOT / "dist" / "ai")
        self.assertEqual(report["status"], "PASS", report)
        self.assertTrue(report["runtime_ok"], report)
        self.assertEqual(len(report["checks"]), 8)
        self.assertTrue(all(row["status"] == "PASS" for row in report["checks"]), report)
        self.assertEqual(
            [row["check"] for row in report["checks"]],
            list(module.RELEASE_SURFACE_CHECKS),
        )


if __name__ == "__main__":
    unittest.main()
