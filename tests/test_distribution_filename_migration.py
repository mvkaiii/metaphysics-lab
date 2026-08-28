import unittest
from pathlib import Path

from tools import build_ai_distribution


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist" / "ai"
EXPECTED_ARTIFACTS = {
    "metaphysics_lab.py",
    "metaphysics_core.md",
    "project_instructions.txt",
}
CURRENT_PUBLIC_DOCS = (
    ROOT / "README.md",
    ROOT / "docs" / "快速開始.md",
    ROOT / "docs" / "安裝到ChatGPT-Project.md",
    ROOT / "docs" / "更新與版本同步.md",
    ROOT / "docs" / "發布說明-v1.5.0.md",
)
HISTORICAL_RELEASE_DOCS = (
    ROOT / "docs" / "發布說明-v1.3.0.md",
    ROOT / "docs" / "發布說明-v1.4.0.md",
)
LEGACY_FILENAMES = (
    "METAPHYSICS_CORE.md",
    "PROJECT_INSTRUCTIONS.md",
)


class DistributionFilenameMigrationTests(unittest.TestCase):
    def test_builder_and_committed_distribution_use_current_lowercase_names(self):
        rendered = build_ai_distribution.render_distribution(ROOT)
        self.assertEqual(set(rendered), EXPECTED_ARTIFACTS)
        self.assertEqual({path.name for path in DIST.iterdir() if path.is_file()}, EXPECTED_ARTIFACTS)

    def test_current_public_docs_use_txt_project_instructions_surface(self):
        combined = "\n".join(path.read_text(encoding="utf-8") for path in CURRENT_PUBLIC_DOCS)
        self.assertIn("metaphysics_core.md", combined)
        self.assertIn("project_instructions.txt", combined)
        for legacy in LEGACY_FILENAMES:
            self.assertNotIn(legacy, combined)

    def test_historical_release_docs_preserve_md_project_instructions_snapshot(self):
        for path in HISTORICAL_RELEASE_DOCS:
            text = path.read_text(encoding="utf-8")
            self.assertIn("metaphysics_core.md", text, str(path))
            self.assertIn("project_instructions.md", text, str(path))
            for legacy in LEGACY_FILENAMES:
                self.assertNotIn(legacy, text, str(path))

    def test_distributed_assets_self_reference_current_lowercase_filenames(self):
        rendered = build_ai_distribution.render_distribution(ROOT)
        combined = (
            rendered["metaphysics_core.md"].decode("utf-8")
            + "\n"
            + rendered["project_instructions.txt"].decode("utf-8")
        )
        self.assertIn("metaphysics_core.md", combined)
        self.assertIn("project_instructions.txt", combined)
        for legacy in LEGACY_FILENAMES:
            self.assertNotIn(legacy, combined)


if __name__ == "__main__":
    unittest.main()
