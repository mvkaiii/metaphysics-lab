import unittest
from pathlib import Path


WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "v17-artifact-inventory.yml"


class ArtifactInventoryWorkflowTests(unittest.TestCase):
    def test_inventory_workflow_is_read_only_and_does_not_upload(self):
        content = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", content)
        self.assertIn("actions: read", content)
        self.assertIn("contents: read", content)
        self.assertIn("tools/v17_artifact_inventory.py", content)
        self.assertNotIn("upload-artifact", content)
        self.assertNotIn("actions: write", content)


if __name__ == "__main__":
    unittest.main()
