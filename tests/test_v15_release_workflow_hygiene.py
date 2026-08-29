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


if __name__ == "__main__":
    unittest.main()
