import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from engine.project_bazi_calendar import (
    bazi_pillars,
    day_pillar,
    time_pillar,
    flow_year_pillar,
    flow_month_pillar,
    solar_term_time,
    ten_god,
    project_derived,
)

TZ = ZoneInfo('Asia/Taipei')


class ProjectBaziCalendarTests(unittest.TestCase):
    def test_known_public_calendar_case_2026_08_20_1712(self):
        dt = datetime(2026, 8, 20, 17, 12, tzinfo=TZ)
        self.assertEqual(bazi_pillars(dt), ('丙午', '丙申', '丙寅', '丁酉'))

    def test_23_rollover_changes_day(self):
        before = datetime(2026, 8, 20, 22, 59, tzinfo=TZ)
        after = datetime(2026, 8, 20, 23, 0, tzinfo=TZ)
        self.assertEqual(day_pillar(before), '丙寅')
        self.assertEqual(day_pillar(after), '丁卯')
        self.assertEqual(time_pillar(after), '庚子')

    def test_2026_flow_year(self):
        dt = datetime(2026, 8, 20, 17, 12, tzinfo=TZ)
        self.assertEqual(flow_year_pillar(dt), '丙午')

    def test_2026_august_is_bingshen_month(self):
        dt = datetime(2026, 8, 20, 17, 12, tzinfo=TZ)
        self.assertEqual(flow_month_pillar(dt), '丙申')

    def test_2026_after_bailu_is_dingyou_month(self):
        dt = datetime(2026, 9, 8, 12, 0, tzinfo=TZ)
        self.assertEqual(flow_month_pillar(dt), '丁酉')

    def test_ten_god_for_bing_day_master(self):
        expected = {
            '丙': '比肩', '丁': '劫財', '戊': '食神', '己': '傷官',
            '庚': '偏財', '辛': '正財', '壬': '七殺', '癸': '正官',
            '甲': '偏印', '乙': '正印',
        }
        for stem, god in expected.items():
            self.assertEqual(ten_god('丙', stem), god)

    def test_boundary_warning_is_emitted_near_jie(self):
        boundary = solar_term_time(2026, '立秋', 'Asia/Taipei')
        result = project_derived(boundary, '丙')
        self.assertTrue(result['boundary_warning']['needs_external_verification'])
        self.assertEqual(result['boundary_warning']['term'], '立秋')

    def test_no_boundary_warning_on_ordinary_date(self):
        dt = datetime(2026, 8, 20, 17, 12, tzinfo=TZ)
        result = project_derived(dt, '丙')
        self.assertIsNone(result['boundary_warning'])

    def test_1984_lichun_close_to_reference(self):
        got = solar_term_time(1984, '立春', 'Asia/Taipei')
        ref = datetime(1984, 2, 4, 23, 21, tzinfo=TZ)
        self.assertLess(abs((got - ref).total_seconds()), 10 * 60)

    def test_2026_lichun_close_to_naoj_reference(self):
        got = solar_term_time(2026, '立春', 'Asia/Taipei')
        ref = datetime(2026, 2, 4, 4, 2, tzinfo=TZ)
        self.assertLess(abs((got - ref).total_seconds()), 10 * 60)


if __name__ == '__main__':
    unittest.main()
