import unittest
from pathlib import Path

from engine.distribution.runtime import dispatch


class ZiweiPhase2BDocumentationTests(unittest.TestCase):
    def setUp(self):
        self.readme = Path('README.md').read_text(encoding='utf-8')
        self.arch = Path('docs/架構說明.md').read_text(encoding='utf-8')
        self.rules = Path('core/命理推導計算規則.md').read_text(encoding='utf-8')
        self.changelog = Path('CHANGELOG.md').read_text(encoding='utf-8')
        self.version = Path('VERSION.md').read_text(encoding='utf-8')
        self.capabilities = dispatch('runtime_info', {})['data']['capabilities']

    def test_phase2b_profile_and_day_boundary_are_documented_in_rule_history(self):
        historical = self.arch + '\n' + self.rules + '\n' + self.changelog
        self.assertIn('ziwei-fine-cycle-lunar-late-zi-v1', historical)
        self.assertIn('late_zi_forward-v1', historical)
        self.assertIn('Fine Cycle', historical)

    def test_capability_state_is_experimental_on_demand_not_stable_default(self):
        for capability_id in (
            'ziwei.flow_month_stem',
            'ziwei.flow_day_stem',
            'ziwei.flow_hour_stem',
            'ziwei.flow_month_transformations',
            'ziwei.flow_day_transformations',
            'ziwei.flow_hour_transformations',
            'ziwei.flow_month_flying',
            'ziwei.flow_day_flying',
            'ziwei.flow_hour_flying',
        ):
            cap = self.capabilities[capability_id]
            self.assertEqual(cap['implementation'], 'implemented')
            self.assertEqual(cap['maturity'], 'experimental')
            self.assertEqual(cap['routing'], 'on_demand')
        self.assertNotIn('Fine Cycle Stem Resolver = implemented / stable / default', self.readme)
        self.assertIn('runtime_info', self.readme)

    def test_calendar_boundary_ownership_is_explicit_in_canonical_rules(self):
        canonical = self.arch + '\n' + self.rules
        self.assertIn('Calendar Resolver', canonical)
        self.assertIn('23:00', canonical)
        self.assertIn('neutral', canonical.lower())
        self.assertIn('fine-cycle profile', canonical)
        self.assertIn('late_zi_forward-v1', canonical)

    def test_qualification_state_is_documented_without_overclaim(self):
        historical = self.arch + '\n' + self.rules + '\n' + self.changelog
        for needle in ('lunar-lite', '18/18 PASS', 'iztro', 'Astralium', 'PENDING'):
            self.assertIn(needle, historical)
        self.assertIn('leap_twelfth_month_second_half', historical)
        self.assertIn('not externally qualified', historical)
        self.assertIn('86 month-oracle checks', self.rules)
        self.assertIn('0 mismatch', self.rules)
        self.assertNotIn('Astralium fine-cycle             PASS', historical)

    def test_readme_delegates_dynamic_phase2b_state_to_runtime(self):
        self.assertIn('runtime_info', self.readme)
        self.assertIn('CHANGELOG.md', self.readme)
        self.assertNotIn('ziwei-fine-cycle-lunar-late-zi-v1', self.readme)
        self.assertNotIn('18/18 PASS', self.readme)

    def test_project_derived_is_classification_not_capability_prefix(self):
        self.assertIn('Project 推導盤面', self.readme)
        self.assertIn('資料分類', self.arch)
        self.assertIn('不是 capability prefix', self.arch)

    def test_changelog_has_phase2b_inside_v130_before_v120(self):
        self.assertIn('### Phase 2B｜Ziwei Fine Cycle Stem Resolver v1', self.changelog)
        self.assertIn('## v1.3.0｜2026-08-23', self.changelog)
        self.assertLess(self.changelog.index('### Phase 2B｜Ziwei Fine Cycle Stem Resolver v1', self.changelog.index('## v1.3.0｜2026-08-23')), self.changelog.index('## v1.2.0｜2026-08-21'))
        self.assertNotIn('## Unreleased｜Phase 2B', self.changelog)

    def test_current_release_is_v150_without_phase2b_promotion(self):
        self.assertIn('Metaphysics Lab Core：**v1.5.0**', self.version)
        self.assertIn('Ziwei Fine Cycle：v1.0-exp', self.version)
        self.assertIn('紫微流月／流日／流時 stem | implemented | experimental | on_demand', self.version)
        self.assertNotIn('Fine Cycle Stem Resolver = implemented / stable / default', self.version)


if __name__ == '__main__':
    unittest.main()
