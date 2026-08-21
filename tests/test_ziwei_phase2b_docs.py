import unittest
from pathlib import Path


class ZiweiPhase2BDocumentationTests(unittest.TestCase):
    def setUp(self):
        self.readme = Path('README.md').read_text(encoding='utf-8')
        self.arch = Path('docs/架構說明.md').read_text(encoding='utf-8')
        self.rules = Path('core/命理推導計算規則.md').read_text(encoding='utf-8')
        self.changelog = Path('CHANGELOG.md').read_text(encoding='utf-8')
        self.version = Path('VERSION.md').read_text(encoding='utf-8')

    def test_phase2b_profile_and_day_boundary_are_documented(self):
        for text in (self.readme, self.arch, self.rules):
            self.assertIn('ziwei-fine-cycle-lunar-late-zi-v1', text)
            self.assertIn('late_zi_forward-v1', text)

    def test_capability_state_is_experimental_on_demand_not_stable_default(self):
        for text in (self.readme, self.arch, self.rules):
            self.assertIn('implemented / experimental / on_demand', text)
        self.assertNotIn('紫微流月／流日／流時四化與飛化 | planned', self.readme)
        self.assertNotIn('紫微流月／流日／流時四化與飛化     planned', self.arch)
        self.assertNotIn('Fine Cycle Stem Resolver（紫微流月／流日／流時天干）', self.readme.split('## 目前仍未實作', 1)[-1])

    def test_calendar_boundary_ownership_is_explicit(self):
        for text in (self.readme, self.arch, self.rules):
            self.assertIn('Calendar Resolver', text)
            self.assertIn('23:00', text)
        self.assertIn('neutral', self.readme.lower())
        self.assertIn('fine-cycle profile', self.arch)

    def test_qualification_state_is_documented_without_overclaim(self):
        extra = (
            Path("docs/快速開始.md").read_text(encoding="utf-8"),
            Path("docs/安裝到ChatGPT-Project.md").read_text(encoding="utf-8"),
            Path("docs/更新與版本同步.md").read_text(encoding="utf-8"),
        )
        for text in (self.readme, self.arch, self.rules, self.changelog, *extra):
            self.assertIn('lunar-lite', text)
            self.assertIn('18/18 PASS', text)
            self.assertIn('iztro', text)
            self.assertIn('Astralium', text)
            self.assertIn('PENDING', text)
        self.assertIn('leap_twelfth_month_second_half', self.arch)
        self.assertIn('not externally qualified', self.readme)

    def test_project_derived_is_classification_not_capability_prefix(self):
        self.assertIn('Project 推導盤面', self.readme)
        self.assertIn('資料分類', self.arch)
        self.assertIn('不是 capability prefix', self.arch)

    def test_changelog_has_unreleased_phase2b_before_v120(self):
        self.assertIn('## Unreleased｜Phase 2B', self.changelog)
        self.assertLess(self.changelog.index('## Unreleased｜Phase 2B'), self.changelog.index('## v1.2.0｜2026-08-21'))

    def test_version_release_identity_remains_v120(self):
        self.assertIn('Metaphysics Lab Core：**v1.2.0**', self.version)
        self.assertNotIn('v1.3.0', self.version)
        self.assertNotIn('Phase 2B', self.version)


if __name__ == '__main__':
    unittest.main()
