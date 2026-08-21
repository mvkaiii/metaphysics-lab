import json
import unittest
from pathlib import Path

from engine.ziwei.errors import ZiweiFineCycleError
from tools.qualify_ziwei_phase2b_public import parse_lunar_lite_contract, qualify_lunar_lite


class ZiweiPhase2BLunarLiteQualificationTests(unittest.TestCase):
    def test_contract_parser_requires_normal_month_and_exact_day_time_sources(self):
        good = '''
        if (monthlyDivide === "exact") lunar.getMonthGanExact();
        const fixLeap = lunar.getMonth() < 0 && lunar.getDay() > 15 ? 1 : 0;
        FIVE_TIGER[HEAVENLY_STEMS.indexOf(yearlyGan)]
        Math.abs(lunar.getMonth()) - 1 + fixLeap
        lunar.getDayGanExact()
        lunar.getDayZhiExact()
        lunar.getTimeGan()
        lunar.getTimeZhi()
        '''
        parsed = parse_lunar_lite_contract(good)
        self.assertTrue(all(parsed.values()))
        with self.assertRaises(ZiweiFineCycleError) as cm:
            parse_lunar_lite_contract(good.replace('Math.abs(lunar.getMonth()) - 1 + fixLeap', ''))
        self.assertEqual(cm.exception.code, 'qualification_mismatch')

    def test_qualifier_detects_mismatch(self):
        payload = {'lunar': [{
            'id': 'bad-month', 'date': '2023-6-13', 'time_index': 1,
            'is_leap': False, 'result': '癸卯 戊午 己丑 乙丑'
        }], 'solar': []}
        report = qualify_lunar_lite(payload, 'rev', '0.2.8', {})
        self.assertEqual(report['status'], 'FAIL')
        self.assertEqual(report['cases_checked'], 2)
        self.assertEqual(len(report['mismatches']), 1)

    def test_synthetic_leap_twelfth_gap_stays_explicit(self):
        payload = {'lunar': [{
            'id': 'normal-month', 'date': '2023-6-13', 'time_index': 1,
            'is_leap': False, 'result': '癸卯 己未 己丑 乙丑'
        }], 'solar': []}
        report = qualify_lunar_lite(payload, 'rev', '0.2.8', {})
        self.assertEqual(report['status'], 'PASS')
        self.assertIn('leap_twelfth_month_second_half', report['not_externally_covered'])

    def test_committed_lunar_report_contract(self):
        path = Path('qualification/ziwei/phase2b/public-lunar-lite-1d104fff.json')
        payload = json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(payload['source_name'], 'SylarLong/lunar-lite')
        self.assertEqual(payload['source_revision'], '1d104fffa31609e9f112898cc57545827e8d57ae')
        self.assertEqual(payload['package_version'], '0.2.8')
        self.assertEqual(payload['status'], 'PASS')
        self.assertEqual(payload['mismatches'], [])
        self.assertEqual(payload['cases_checked'], 18)
        self.assertEqual(payload['cases_matched'], 18)
        for marker in ('lunar_month_normal', 'leap_month_first_half', 'leap_month_second_half', 'regular_day_hour', 'late_zi_day_hour'):
            self.assertIn(marker, payload['external_coverage'])
        self.assertIn('leap_twelfth_month_second_half', payload['not_externally_covered'])
        self.assertTrue(all(payload['source_contract'].values()))
        self.assertNotIn('Astralium', path.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()

from tools.qualify_ziwei_phase2b_public import qualify_iztro_source


class ZiweiPhase2BIztroQualificationTests(unittest.TestCase):
    def test_iztro_requires_each_fine_scope_mutagen_link(self):
        bad = '''monthly: { mutagen: getMutagensByHeavenlyStem(monthly[0]) }'''
        with self.assertRaises(ZiweiFineCycleError) as cm:
            qualify_iztro_source(bad, '814b77e6', '2026-08-21T00:00:00Z')
        self.assertEqual(cm.exception.code, 'qualification_mismatch')

    def test_iztro_source_links_each_scope_to_its_own_stem(self):
        good = '''
        monthly: { index: 1, mutagen: getMutagensByHeavenlyStem(monthly[0]), stars: x },
        daily: { index: 2, mutagen: getMutagensByHeavenlyStem(daily[0]), stars: y },
        hourly: { index: 3, mutagen: getMutagensByHeavenlyStem(hourly[0]), stars: z },
        '''
        report = qualify_iztro_source(good, '814b77e6', '2026-08-21T00:00:00Z')
        self.assertEqual(report['status'], 'PASS')
        self.assertTrue(report['monthly_mutagen_uses_monthly_stem'])
        self.assertTrue(report['daily_mutagen_uses_daily_stem'])
        self.assertTrue(report['hourly_mutagen_uses_hourly_stem'])
        self.assertEqual(report['project_sample_transformations_each'], 4)

    def test_committed_iztro_report_contract(self):
        path = Path('qualification/ziwei/phase2b/public-iztro-814b77e6.json')
        payload = json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(payload['source_name'], 'SylarLong/iztro')
        self.assertEqual(payload['source_revision'], '814b77e6371e1050cac31bbf674db3c3138fcfde')
        self.assertEqual(payload['package_version'], '2.6.0')
        self.assertEqual(payload['status'], 'PASS')
        self.assertTrue(payload['monthly_mutagen_uses_monthly_stem'])
        self.assertTrue(payload['daily_mutagen_uses_daily_stem'])
        self.assertTrue(payload['hourly_mutagen_uses_hourly_stem'])
        self.assertEqual(payload['project_sample_transformations_each'], 4)
        self.assertEqual(set(payload['project_sample_scopes']), {'monthly', 'daily', 'hourly'})
        self.assertNotIn('Astralium', path.read_text(encoding='utf-8'))
