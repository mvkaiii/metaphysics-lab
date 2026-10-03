import re
import unittest
from pathlib import Path

from engine.distribution.constants import (
    CASE_SCHEMA_VERSION,
    DISTRIBUTION_RUNTIME_VERSION,
    PROJECT_CONTRACT_VERSION,
    RELEASE_VERSION,
    RUNTIME_SCHEMA_VERSION,
)
from tools import build_release_package


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "release-v1.9.yml"
RELEASE_NOTES = ROOT / "docs" / "發布說明-v1.9.0.md"
EXPECTED_PACKAGE_SHA256 = "e263c25ea6efb8184a2d66c2bc2ce3edf31b29324152b2bccb9f96333aa504fa"


class V19ReleaseExecutionContractTests(unittest.TestCase):
    def test_release_identity_is_exact_and_package_digest_stays_frozen(self):
        self.assertEqual(RELEASE_VERSION, "1.9.0")
        self.assertEqual(DISTRIBUTION_RUNTIME_VERSION, "1.5-exp")
        self.assertEqual(PROJECT_CONTRACT_VERSION, "1.3")
        self.assertEqual(RUNTIME_SCHEMA_VERSION, "1.1")
        self.assertEqual(CASE_SCHEMA_VERSION, "1.1")
        self.assertEqual(
            build_release_package.USER_PACKAGE_NAME,
            "Metaphysics-Lab-v1.9.0-User-Package.zip",
        )

    def test_release_workflow_publishes_only_from_verified_merged_main_sha(self):
        self.assertTrue(WORKFLOW.is_file(), "v1.9 release workflow is missing")
        text = WORKFLOW.read_text(encoding="utf-8")
        for required in (
            "name: Release v1.9.0",
            "branches: [main]",
            "permissions:\n  contents: write",
            "Checkout exact merged release target",
            'test "$(git rev-parse HEAD)" = "$GITHUB_SHA"',
            "tests.test_v19_release_execution",
            "tests.test_v19_release_candidate_contract",
            "tests.test_v19_visualization_p1_candidate_envelope",
            "python tools/build_ai_distribution.py --check",
            "python tools/run_v17_release_surface_validation.py --json",
            "python -m unittest discover -s tests -p 'test_*.py' -v",
            "Private outcome contamination scan",
            "Run merged-package python -S smoke",
            "Build deterministic v1.9.0 User Package twice and verify frozen digest",
            EXPECTED_PACKAGE_SHA256,
            "gh release create v1.9.0",
            '--target "$GITHUB_SHA"',
            "Verify published target and assets",
            "git rev-list -n 1 v1.9.0",
            "Metaphysics-Lab-v1.9.0-User-Package.zip",
        ):
            self.assertIn(required, text)

        publish = text.index("gh release create v1.9.0")
        full = text.index("Full repository regression")
        package = text.index(
            "Build deterministic v1.9.0 User Package twice and verify frozen digest"
        )
        smoke = text.index("Run merged-package python -S smoke")
        self.assertLess(full, publish)
        self.assertLess(package, publish)
        self.assertLess(smoke, publish)

        for forbidden in (
            "stable_promotion=true",
            "default_switch=true",
            "promote_to_stable",
            "switch_default",
        ):
            self.assertNotIn(forbidden, text)

    def test_public_docs_switch_latest_release_to_v19_without_claiming_stable(self):
        paths = (
            ROOT / "README.md",
            ROOT / "docs" / "快速開始.md",
            ROOT / "docs" / "安裝到ChatGPT-Project.md",
            ROOT / "docs" / "更新與版本同步.md",
            ROOT / "VERSION.md",
            ROOT / "CHANGELOG.md",
        )
        for path in paths:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertIn("v1.9.0", text)
                self.assertIn("2026-10-03", text)

        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(
            "https://github.com/mvkaiii/metaphysics-lab/releases/tag/v1.9.0",
            readme,
        )
        self.assertIn("Metaphysics-Lab-v1.9.0-User-Package.zip", readme)

        version = (ROOT / "VERSION.md").read_text(encoding="utf-8")
        self.assertIn("## v1.9.0 Release Snapshot", version)
        self.assertIn("Project Contract           1.3", version)
        self.assertIn("AI Distribution Runtime    1.5-exp", version)
        self.assertIn(EXPECTED_PACKAGE_SHA256, version)

        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertRegex(changelog, r"## v1\.9\.0｜2026-10-03")
        self.assertIn("Candidate Envelope v2", changelog)
        self.assertIn("Lock Provenance v2", changelog)
        self.assertIn("Guided Natal Build", changelog)
        self.assertIn("Visualization P1", changelog)

        combined = "\n".join(path.read_text(encoding="utf-8") for path in paths)
        self.assertNotIn("v1.9.0 將", combined)
        self.assertNotRegex(combined, re.compile(r"v1\.9\.0.{0,40}(?:Stable|穩定功能)", re.S))

    def test_release_notes_state_upgrade_and_compatibility_boundaries(self):
        self.assertTrue(RELEASE_NOTES.is_file(), "v1.9 release notes are missing")
        text = RELEASE_NOTES.read_text(encoding="utf-8")
        for required in (
            "# Metaphysics Lab v1.9.0｜發布說明",
            "2026-10-03",
            "Project Contract",
            "1.3",
            "Case Schema",
            "1.1",
            "Candidate Envelope v2",
            "Case Revision Integrity",
            "Lock Provenance v2",
            "Guided Natal Build",
            "Visualization P1",
            "Metaphysics-Lab-v1.9.0-User-Package.zip",
            EXPECTED_PACKAGE_SHA256,
            "既有 1.2 Case",
            "舊 lock",
            "不回填",
            "不重簽",
            "selector v1",
            "interpretation v1",
            "Experimental",
        ):
            self.assertIn(required, text)

        for forbidden in (
            "Stable promotion included",
            "selector v2 is default",
            "interpretation v2 is default",
        ):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
