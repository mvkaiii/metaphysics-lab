import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "release-v1.8.yml"
EXPECTED_PACKAGE_SHA256 = "f9b22d4b97949b873261793c404d2530a0bc384d77e970e1bba7aec35edc82cf"


class V18ReleaseWorkflowTests(unittest.TestCase):
    def test_release_workflow_is_fail_closed_and_publishes_only_after_merged_sha_validation(self):
        self.assertTrue(WORKFLOW.is_file())
        text = WORKFLOW.read_text(encoding="utf-8")
        for required in (
            "name: Release v1.8.0",
            "branches: [main]",
            "permissions:\n  contents: write",
            "Checkout exact merged release target",
            'test "$(git rev-parse HEAD)" = "$GITHUB_SHA"',
            "tests.test_v18_visualization_runtime",
            "tests.test_v18_compact_presentation_policy",
            "python tools/build_ai_distribution.py --check",
            "python tools/run_v17_release_surface_validation.py --json",
            "python -m unittest discover -s tests -p 'test_*.py' -v",
            "Private outcome contamination scan",
            "Build deterministic v1.8.0 User Package twice and verify frozen digest",
            EXPECTED_PACKAGE_SHA256,
            'assert bazi["maturity"] == "experimental"',
            'assert bazi["routing"] == "on_demand"',
            "gh release create v1.8.0",
            '--target "$GITHUB_SHA"',
            "Verify published target and assets",
            "git rev-list -n 1 v1.8.0",
            "Metaphysics-Lab-v1.8.0-User-Package.zip",
        ):
            self.assertIn(required, text)

    def test_release_workflow_does_not_promote_or_switch_defaults(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        for forbidden in (
            "stable_promotion=true",
            "default_switch=true",
            "promote_to_stable",
            "switch_default",
        ):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
