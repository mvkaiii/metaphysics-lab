import unittest
from pathlib import Path

from tools import build_ai_distribution


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist" / "ai"
EXPECTED_ARTIFACTS = {
    "metaphysics_lab.py",
    "metaphysics_core.md",
    "project_instructions.md",
}
PUBLIC_DOCS = (
    ROOT / "README.md",
    ROOT / "docs" / "快速開始.md",
    ROOT / "docs" / "安裝到ChatGPT-Project.md",
    ROOT / "docs" / "發布說明-v1.3.0.md",
    ROOT / "docs" / "更新與版本同步.md",
)
LEGACY_FILENAMES = (
    "METAPHYSICS_CORE.md",
    "PROJECT_INSTRUCTIONS.md",
)


class DistributionFilenameMigrationTests(unittest.TestCase):
    def test_builder_and_committed_distribution_use_lowercase_snake_case_names(self):
        rendered = build_ai_distribution.render_distribution(ROOT)
        self.assertEqual(set(rendered), EXPECTED_ARTIFACTS)
        self.assertEqual({path.name for path in DIST.iterdir() if path.is_file()}, EXPECTED_ARTIFACTS)

    def test_public_docs_use_lowercase_distribution_filenames(self):
        combined = "\n".join(path.read_text(encoding="utf-8") for path in PUBLIC_DOCS)
        self.assertIn("metaphysics_core.md", combined)
        self.assertIn("project_instructions.md", combined)
        for legacy in LEGACY_FILENAMES:
            self.assertNotIn(legacy, combined)

    def test_distributed_markdown_self_references_use_lowercase_filenames(self):
        rendered = build_ai_distribution.render_distribution(ROOT)
        combined = (
            rendered["metaphysics_core.md"].decode("utf-8")
            + "\n"
            + rendered["project_instructions.md"].decode("utf-8")
        )
        self.assertIn("metaphysics_core.md", combined)
        for legacy in LEGACY_FILENAMES:
            self.assertNotIn(legacy, combined)


if __name__ == "__main__":
    unittest.main()
