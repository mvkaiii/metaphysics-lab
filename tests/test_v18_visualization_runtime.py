import json
import subprocess
import sys
import unittest
from pathlib import Path

from engine.distribution.constants import DISTRIBUTION_RUNTIME_VERSION, SUPPORTED_ACTIONS
from engine.distribution.runtime import dispatch


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "dist" / "ai" / "metaphysics_lab.py"
BIRTH = {
    "sex": "male",
    "birth_date": "1984-03-13",
    "birth_time": "19:20",
    "birth_place": "台北市",
}
LOCATION = {
    "canonical_name": "Taipei City, Taiwan",
    "latitude": 25.033,
    "longitude": 121.5654,
    "timezone": "Asia/Taipei",
    "provider_name": "ai_host",
    "provider_version": "synthetic-test",
    "provider_reference": None,
}


class V18VisualizationRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        built = dispatch("build_natal", {"birth": BIRTH, "resolved_location": LOCATION})
        if not built.get("ok"):
            raise AssertionError(built)
        cls.project_natal = built["data"]["project_natal"]
        cls.normalized_natal = built["data"]["normalized_natal"]

    def _payload(self, **updates):
        payload = {
            "project_natal": self.project_natal,
            "as_of": "2026-09-30T17:00:00+08:00",
            "visibility_mode": "identified",
        }
        payload.update(updates)
        return payload

    def test_action_is_public_and_returns_deterministic_svg_and_text(self):
        self.assertIn("render_bazi_decadal_timeline", SUPPORTED_ACTIONS)
        first = dispatch("render_bazi_decadal_timeline", self._payload())
        second = dispatch("render_bazi_decadal_timeline", self._payload())
        self.assertTrue(first["ok"], first)
        self.assertEqual(first, second)
        data = first["data"]
        self.assertEqual(data["chart"]["status"], "ready")
        self.assertEqual(data["chart"]["provenance"]["source_commit"], None)
        self.assertEqual(data["chart"]["provenance"]["distribution_runtime_version"], DISTRIBUTION_RUNTIME_VERSION)
        self.assertIn("<svg", data["svg"])
        self.assertIn("Bazi decadal timeline", data["text"])
        self.assertEqual(data["artifact"]["suggested_filename"], "bazi-decadal-timeline.svg")
        self.assertEqual(data["presentation"]["surface"], "experimental")
        self.assertFalse(data["presentation"]["ranking_authority"])
        self.assertFalse(data["presentation"]["predictive_evidence"])
        self.assertIn(
            "SOURCE_COMMIT_UNAVAILABLE",
            [row["code"] for row in data["chart"]["limitations"]],
        )

    def test_normalized_natal_input_uses_same_project_view(self):
        project = dispatch("render_bazi_decadal_timeline", self._payload())
        normalized_payload = self._payload()
        normalized_payload.pop("project_natal")
        normalized_payload["normalized_natal"] = self.normalized_natal
        normalized = dispatch("render_bazi_decadal_timeline", normalized_payload)
        self.assertTrue(normalized["ok"], normalized)
        self.assertEqual(project["data"], normalized["data"])

    def test_blind_mode_stays_blind_and_unknown_fields_fail_closed(self):
        blind = dispatch(
            "render_bazi_decadal_timeline",
            self._payload(visibility_mode="blind"),
        )
        self.assertTrue(blind["ok"], blind)
        self.assertEqual(blind["data"]["chart"]["view_context"]["visibility_mode"], "blind")
        bad = self._payload(verified_event_payload={"secret": True})
        refused = dispatch("render_bazi_decadal_timeline", bad)
        self.assertFalse(refused["ok"])
        self.assertEqual(refused["error"]["code"], "invalid_visualization_payload")

    def test_portable_bundle_has_modular_parity(self):
        payload = self._payload()
        modular = dispatch("render_bazi_decadal_timeline", payload)
        request = json.dumps(
            {"action": "render_bazi_decadal_timeline", "payload": payload},
            ensure_ascii=False,
        )
        completed = subprocess.run(
            [sys.executable, str(BUNDLE), "request", "--input", "-"],
            cwd=str(ROOT),
            input=request,
            text=True,
            capture_output=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        bundled = json.loads(completed.stdout)
        self.assertEqual(bundled, modular)


if __name__ == "__main__":
    unittest.main()
