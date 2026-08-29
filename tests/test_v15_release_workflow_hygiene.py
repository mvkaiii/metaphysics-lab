import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RELEASE_WORKFLOW = ROOT / ".github" / "workflows" / "release-v1.5.yml"


class V15ReleaseWorkflowHygieneTests(unittest.TestCase):
    def test_compile_check_does_not_materialize_bytecode_inside_distribution(self):
        text = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("python -m compileall -q engine tools tests", text)
        self.assertNotIn("python -m compileall -q engine tools tests dist/ai/metaphysics_lab.py", text)
        self.assertIn("compile(open('dist/ai/metaphysics_lab.py'", text)

    def test_existing_release_syncs_notes_without_replacing_release_identity(self):
        text = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("gh release edit v1.5.0 --notes-file docs/發布說明-v1.5.0.md", text)
        self.assertIn("gh release view v1.5.0 --json tagName,targetCommitish,isDraft,isPrerelease", text)
        self.assertNotIn("gh release delete v1.5.0", text)


if __name__ == "__main__":
    unittest.main()
