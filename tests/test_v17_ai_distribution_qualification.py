from pathlib import Path
import types
import unittest

from engine.distribution.runtime import dispatch


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist" / "ai"


class V17AIDistributionQualificationTests(unittest.TestCase):
    @staticmethod
    def _load_bundle():
        path = DIST / "metaphysics_lab.py"
        module = types.ModuleType("v17_qualification_bundle")
        module.__file__ = str(path)
        exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), module.__dict__)
        return module

    @staticmethod
    def _context_payload():
        return {
            "forecast_id": "PV2-distribution-summary",
            "locked_at": "2026-09-09T09:30:00+08:00",
            "knowledge_cutoff_at": "2026-09-09T09:20:00+08:00",
            "question_mode": "future_forecast",
            "knowledge_state_at_lock": "unknown",
            "prediction_window": {
                "start": "2026-10-01T00:00:00+08:00",
                "end": "2026-10-31T23:59:59+08:00",
            },
        }

    def test_project_instructions_fit_chatgpt_project_character_limit(self):
        text = (DIST / "project_instructions.txt").read_text(encoding="utf-8")
        self.assertLessEqual(len(text), 8000)

    def test_validation_summary_has_modular_bundle_parity(self):
        classified = dispatch("classify_validation_context", self._context_payload())
        self.assertTrue(classified["ok"], classified)
        payload = {
            "records": [
                {
                    "validation_context": classified["data"],
                    "verification_state": "matched",
                }
            ]
        }
        modular = dispatch("build_validation_summary", payload)
        self.assertTrue(modular["ok"], modular)
        bundled = self._load_bundle().dispatch("build_validation_summary", payload)
        self.assertEqual(bundled, modular)
        self.assertEqual(modular["data"]["clean_denominator"]["scorable_count"], 1)


if __name__ == "__main__":
    unittest.main()
