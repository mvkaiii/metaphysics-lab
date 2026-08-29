import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class V15PostReleaseStatusTests(unittest.TestCase):
    def test_active_current_state_docs_are_post_release(self):
        active_files = (
            "README.md",
            "VERSION.md",
            "CHANGELOG.md",
            "docs/快速開始.md",
            "docs/安裝到ChatGPT-Project.md",
            "docs/更新與版本同步.md",
            "docs/架構說明.md",
            "docs/release/v1.5.0-qualification.md",
            "docs/release/v1.5.0-terminology-audit.md",
        )
        stale_tokens = (
            "v1.5.0 Release Candidate",
            "PENDING_FINAL_QUALIFICATION",
            "PENDING_FINAL_EVIDENCE",
            "ACTIVE_TERMINOLOGY_CLEAN_PENDING_FULL_CI",
            "v1.5.0 正式發布後",
        )
        for relative in active_files:
            text = (ROOT / relative).read_text(encoding="utf-8")
            for token in stale_tokens:
                self.assertNotIn(token, text, f"{relative} still contains stale post-release state {token!r}")

    def test_primary_status_docs_name_v15_as_latest_formal_release(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        version = (ROOT / "VERSION.md").read_text(encoding="utf-8")
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        update = (ROOT / "docs/更新與版本同步.md").read_text(encoding="utf-8")
        architecture = (ROOT / "docs/架構說明.md").read_text(encoding="utf-8")

        self.assertIn("目前正式版本為 **v1.5.0（2026-08-29）**", readme)
        self.assertIn("Metaphysics Lab Core：**v1.5.0**", version)
        self.assertIn("發布日期：**2026-08-29**", version)
        self.assertIn("## v1.5.0｜2026-08-29", changelog)
        self.assertIn("目前正式版本為 **v1.5.0｜2026-08-29**", update)
        self.assertIn("目前正式版本為 **v1.5.0｜2026-08-29**", architecture)

    def test_final_release_evidence_is_recorded_without_moving_release_identity(self):
        qualification = (ROOT / "docs/release/v1.5.0-qualification.md").read_text(encoding="utf-8")
        terminology = (ROOT / "docs/release/v1.5.0-terminology-audit.md").read_text(encoding="utf-8")
        rules = (ROOT / "core/命理推導計算規則.md").read_text(encoding="utf-8")

        self.assertIn("狀態：`RELEASED`", qualification)
        self.assertIn("66f604222caadac0209125a78674c3f4491c4b99", qualification)
        self.assertIn("a7fe693a8bd91f6b720409e5e23e655cc3bf13396e21c8b7f99f79bc2b23cbfc", qualification)
        self.assertIn("status: RELEASED", terminology)
        self.assertIn("正式軟體 release：v1.5.0", rules)
        self.assertIn("文件版本：v1.4", rules)


if __name__ == "__main__":
    unittest.main()
