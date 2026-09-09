from pathlib import Path
import importlib.util
import unittest

from engine.distribution.runtime import dispatch
from tools import build_ai_distribution


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist" / "ai"


class ProspectiveValidationDistributionTests(unittest.TestCase):
    @staticmethod
    def _load_bundle():
        spec = importlib.util.spec_from_file_location("pv2_bundle", DIST / "metaphysics_lab.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    @staticmethod
    def _context_payload():
        return {
            "forecast_id": "PV2-distribution",
            "locked_at": "2026-09-09T09:30:00+08:00",
            "knowledge_cutoff_at": "2026-09-09T09:20:00+08:00",
            "question_mode": "future_forecast",
            "knowledge_state_at_lock": "unknown",
            "prediction_window": {
                "start": "2026-10-01T00:00:00+08:00",
                "end": "2026-10-31T23:59:59+08:00",
            },
        }

    def test_ai_workflow_separates_clean_and_non_clean_validation_contexts(self):
        text = (ROOT / "core" / "AI工作流程.md").read_text(encoding="utf-8")
        for required in (
            "classify_validation_context",
            "clean_prospective",
            "conditional_prospective",
            "hidden_existing_reality",
            "retrospective_calibration",
            "clean prospective denominator",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)

    def test_committed_distribution_matches_official_generator(self):
        expected = build_ai_distribution.render_distribution(ROOT)
        for name, content in expected.items():
            self.assertEqual((DIST / name).read_bytes(), content, name)

    def test_bundled_runtime_exposes_validation_actions(self):
        module = self._load_bundle()
        info = module.dispatch("runtime_info", {})
        self.assertTrue(info["ok"], info)
        self.assertIn("classify_validation_context", info["data"]["supported_actions"])
        self.assertIn("build_validation_summary", info["data"]["supported_actions"])

    def test_classifier_output_has_complete_modular_bundle_parity(self):
        payload = self._context_payload()
        modular = dispatch("classify_validation_context", payload)
        bundled = self._load_bundle().dispatch("classify_validation_context", payload)
        self.assertEqual(bundled, modular)


if __name__ == "__main__":
    unittest.main()
