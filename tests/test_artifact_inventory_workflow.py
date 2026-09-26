import unittest
import subprocess
import sys
from pathlib import Path


WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "artifact-inventory.yml"
ROOT = Path(__file__).parents[1]


class ArtifactInventoryWorkflowTests(unittest.TestCase):
    def test_inventory_workflow_is_read_only_and_does_not_upload_or_delete(self):
        content = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", content)
        self.assertIn("actions: read", content)
        self.assertIn("contents: read", content)
        self.assertIn("tools/artifact_inventory.py", content)
        self.assertNotIn("upload-artifact", content)
        self.assertNotIn("actions: write", content)
        self.assertNotIn("DELETE", content)

    def test_direct_and_module_cli_entrypoints_load_without_network(self):
        direct = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "artifact_inventory.py"), "--help"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        module = subprocess.run(
            [sys.executable, "-m", "tools.artifact_inventory", "--help"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )

        self.assertEqual(direct.returncode, 0, direct.stderr)
        self.assertEqual(module.returncode, 0, module.stderr)


if __name__ == "__main__":
    unittest.main()
