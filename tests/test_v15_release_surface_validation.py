import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tools" / "run_v15_release_surface_validation.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("v15_release_surface_validation", RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class V15ReleaseSurfaceValidationTests(unittest.TestCase):
    def test_all_release_surface_checks_pass(self):
        module = load_runner()
        report = module.run(ROOT / "dist" / "ai")
        self.assertEqual(report["status"], "PASS", report)
        self.assertTrue(report["runtime_ok"], report)
        self.assertEqual(len(report["checks"]), 8)
        self.assertTrue(all(row["status"] == "PASS" for row in report["checks"]), report)
        self.assertEqual(
            [row["check"] for row in report["checks"]],
            list(module.RELEASE_SURFACE_CHECKS),
        )

    def test_natural_language_check_rejects_generic_plain_language_words_without_override_boundary(self):
        module = load_runner()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "metaphysics_lab.py").write_text(
                "#!/usr/bin/env python3\nimport json\nprint(json.dumps({'ok': True}))\n",
                encoding="utf-8",
            )
            (root / "metaphysics_core.md").write_text(
                "時間 時間窗 event_family matched_if not_matched_if 事件校準 不得 "
                "known_before_lock clean prospective denominator Experimental 權重 策略 預測",
                encoding="utf-8",
            )
            (root / "project_instructions.txt").write_text(
                "一般回答使用台灣繁體中文與白話。",
                encoding="utf-8",
            )

            report = module.run(root)
            checks = {row["check"]: row["status"] for row in report["checks"]}
            self.assertEqual(checks["natural_language_contract_present"], "FAIL", report)


if __name__ == "__main__":
    unittest.main()
