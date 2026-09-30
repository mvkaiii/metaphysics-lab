import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "v18-release-candidate-validation.yml"


class V18ReleaseCandidateWorkflowTests(unittest.TestCase):
    def test_workflow_is_release_candidate_only_and_fail_closed(self):
        self.assertTrue(WORKFLOW.is_file())
        text = WORKFLOW.read_text(encoding="utf-8")
        for required in (
            "Metaphysics Lab v1.8 Release Candidate Validation",
            "permissions:\n  contents: read",
            "Checkout exact candidate",
            'test "$(git rev-parse HEAD)" = "$CANDIDATE_SHA"',
            "python-version: '3.9'",
            "tests.test_v18_release_candidate_contract",
            "python tools/build_ai_distribution.py --check",
            "Metaphysics-Lab-v1.8.0-User-Package.zip",
            "cmp \\",
            '"release_authorized": False',
            '"stable_promotion": False',
            '"default_switch": False',
            "git diff --exit-code",
            "actions/upload-artifact@v4",
        ):
            self.assertIn(required, text)

        for forbidden in (
            "contents: write",
            "git push",
            "gh release",
            "create-release",
            "git tag",
            "merge_pull_request",
        ):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
