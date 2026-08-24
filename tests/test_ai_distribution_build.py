import importlib
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_ARTIFACTS = [
    "metaphysics_core.md",
    "metaphysics_lab.py",
    "project_instructions.md",
]
FORBIDDEN_FIXED_MD = (
    "Phase 2C",
    "600/600",
    "814b77e6",
    "ziwei.flowing_stars =",
)


class AIDistributionBuildTests(unittest.TestCase):
    @staticmethod
    def builder():
        spec = importlib.util.find_spec("tools.build_ai_distribution")
        if spec is None:
            raise AssertionError("tools.build_ai_distribution must exist")
        return importlib.import_module("tools.build_ai_distribution")

    def test_same_source_tree_builds_byte_identical_three_artifacts(self):
        builder = self.builder()
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first = Path(first_dir)
            second = Path(second_dir)
            builder.build_distribution(ROOT, first)
            builder.build_distribution(ROOT, second)
            self.assertEqual(sorted(path.name for path in first.iterdir()), EXPECTED_ARTIFACTS)
            self.assertEqual(sorted(path.name for path in second.iterdir()), EXPECTED_ARTIFACTS)
            for name in EXPECTED_ARTIFACTS:
                self.assertEqual((first / name).read_bytes(), (second / name).read_bytes(), name)

    def test_project_instructions_is_normalized_exact_core_prompt(self):
        builder = self.builder()
        with tempfile.TemporaryDirectory() as output_dir:
            output = Path(output_dir)
            builder.build_distribution(ROOT, output)
            expected = (ROOT / "core" / "核心提示詞.md").read_text(encoding="utf-8").replace("\r\n", "\n").rstrip() + "\n"
            actual = (output / "project_instructions.md").read_text(encoding="utf-8")
            self.assertEqual(actual, expected)

    def test_fixed_markdown_contains_stable_source_markers_but_no_dynamic_snapshot(self):
        builder = self.builder()
        with tempfile.TemporaryDirectory() as output_dir:
            output = Path(output_dir)
            builder.build_distribution(ROOT, output)
            core = (output / "metaphysics_core.md").read_text(encoding="utf-8")
            instructions = (output / "project_instructions.md").read_text(encoding="utf-8")
            self.assertIn("Source: core/AI工作流程.md", core)
            self.assertIn("Source: core/命理分析作業規範.md", core)
            combined = core + "\n" + instructions
            for forbidden in FORBIDDEN_FIXED_MD:
                self.assertNotIn(forbidden, combined)
            self.assertNotIn("命理推導計算規則.md", core)

    def test_bundle_has_generated_marker_digest_and_no_absolute_builder_path(self):
        builder = self.builder()
        with tempfile.TemporaryDirectory() as output_dir:
            output = Path(output_dir)
            builder.build_distribution(ROOT, output)
            text = (output / "metaphysics_lab.py").read_text(encoding="utf-8")
            self.assertIn("GENERATED FILE - DO NOT EDIT", text)
            self.assertIn("SOURCE_DIGEST =", text)
            self.assertIn("BUILD_FORMAT_VERSION =", text)
            self.assertNotIn(str(ROOT), text)
            self.assertNotIn("/home/runner/", text)
            self.assertNotIn("qualification/", text)
            self.assertNotIn("tests/", text)

    def test_source_discovery_is_owned_runtime_only(self):
        builder = self.builder()
        paths = builder.discover_owned_sources(ROOT)
        self.assertIn("engine/distribution/runtime.py", paths)
        self.assertIn("templates/case/00_project_index.md.tmpl", paths)
        self.assertTrue(all(path.startswith("engine/") or path.startswith("templates/") for path in paths))
        self.assertTrue(all(not path.startswith("tests/") for path in paths))
        self.assertTrue(all(not path.startswith("qualification/") for path in paths))
        self.assertTrue(all(not path.startswith("docs/") for path in paths))

    def test_check_mode_detects_drift(self):
        self.builder()
        with tempfile.TemporaryDirectory() as output_dir:
            output = Path(output_dir)
            subprocess.run(
                [sys.executable, "tools/build_ai_distribution.py", "--output-dir", str(output)],
                cwd=str(ROOT),
                check=True,
                text=True,
                capture_output=True,
            )
            clean = subprocess.run(
                [sys.executable, "tools/build_ai_distribution.py", "--output-dir", str(output), "--check"],
                cwd=str(ROOT),
                text=True,
                capture_output=True,
            )
            self.assertEqual(clean.returncode, 0, clean.stdout + clean.stderr)
            with (output / "project_instructions.md").open("a", encoding="utf-8") as handle:
                handle.write("drift\n")
            drift = subprocess.run(
                [sys.executable, "tools/build_ai_distribution.py", "--output-dir", str(output), "--check"],
                cwd=str(ROOT),
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(drift.returncode, 0)
            self.assertIn("project_instructions.md", drift.stdout + drift.stderr)


if __name__ == "__main__":
    unittest.main()
