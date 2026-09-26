import copy
import json
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from engine.distribution.manifest import load_capability_manifest
from engine.visualization.bazi_decadal import project_bazi_decadal
from renderers.svg.bazi_decadal import render_bazi_decadal_svg, render_bazi_decadal_text


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "visualization" / "bazi-decadal-engine-view.v1.json"


def _chart():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    return project_bazi_decadal(
        fixture,
        load_capability_manifest(),
        as_of="2005-01-01T00:00:00+08:00",
        timezone="Asia/Taipei",
        visibility_mode="blind",
    )


def _unsupported_chart():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    fixture["resolved_candidate_count"] = 2
    return project_bazi_decadal(
        fixture,
        load_capability_manifest(),
        as_of="2005-01-01T00:00:00+08:00",
        timezone="Asia/Taipei",
        visibility_mode="blind",
    )


class VisualizationSvgTests(unittest.TestCase):
    def test_svg_has_same_labels_and_current_period_as_contract(self):
        chart = _chart()
        svg = render_bazi_decadal_svg(chart)
        self.assertIn("戊辰", svg)
        self.assertIn("period-2", svg)
        self.assertIn("2005-01-01T00:00:00+08:00", svg)

    def test_experimental_and_authority_labels_visible(self):
        svg = render_bazi_decadal_svg(_chart())
        self.assertIn("Experimental", svg)
        self.assertIn("Project-derived", svg)

    def test_text_alternative_preserves_limitations(self):
        text = render_bazi_decadal_text(_chart())
        self.assertIn("EXPERIMENTAL_CAPABILITY", text)
        self.assertIn("OPTIONAL_FIELDS_UNAVAILABLE", text)
        self.assertIn("continuous_years_from_jie_interval", text)

    def test_unsupported_renders_no_fake_timeline(self):
        svg = render_bazi_decadal_svg(_unsupported_chart())
        text = render_bazi_decadal_text(_unsupported_chart())
        self.assertIn("AMBIGUOUS_NATAL_CANDIDATE", svg)
        self.assertNotIn("class=\"period\"", svg)
        self.assertNotIn("period-1", text)

    def test_script_and_external_href_cannot_be_injected(self):
        chart = _chart()
        chart["data"]["periods"][0]["pillar"] = '<script>alert("x")</script>&href="bad"'
        svg = render_bazi_decadal_svg(chart)
        self.assertNotIn("<script", svg.lower())
        self.assertNotIn('href="', svg.lower())
        self.assertIn("&lt;script&gt;", svg)

    def test_renderer_has_no_engine_algorithm_imports(self):
        source = (ROOT / "renderers" / "svg" / "bazi_decadal.py").read_text(encoding="utf-8")
        for forbidden in ("engine.bazi", "engine.ziwei", "engine.calendar", "case_doctor", "parse_case"):
            self.assertNotIn(forbidden, source)

    def test_svg_bytes_deterministic(self):
        chart = _chart()
        self.assertEqual(render_bazi_decadal_svg(chart), render_bazi_decadal_svg(copy.deepcopy(chart)))

    def test_svg_is_well_formed_and_has_no_external_reference_attributes(self):
        root = ET.fromstring(render_bazi_decadal_svg(_chart()))
        self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
        self.assertFalse(any("href" in key.lower() for element in root.iter() for key in element.attrib))
        self.assertFalse(any(element.tag.endswith("script") for element in root.iter()))

    def test_long_labels_do_not_hide_authority(self):
        chart = _chart()
        chart["limitations"][0]["message"] = "很長的限制說明" * 80
        svg = render_bazi_decadal_svg(chart)
        self.assertIn("很長的限制說明", svg)
        self.assertIn("Project-derived", svg)

    def test_existing_output_requires_explicit_overwrite(self):
        chart = _chart()
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "chart.json"
            output_path = Path(directory) / "chart.svg"
            input_path.write_text(json.dumps(chart, ensure_ascii=False), encoding="utf-8")
            output_path.write_text("sentinel", encoding="utf-8")
            command = [sys.executable, "tools/render_visualization.py", "--input", str(input_path), "--output", str(output_path)]
            refused = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(refused.returncode, 0)
            self.assertEqual(output_path.read_text(encoding="utf-8"), "sentinel")
            allowed = subprocess.run(command + ["--overwrite"], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(allowed.returncode, 0, allowed.stderr)
            self.assertIn("<svg", output_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
