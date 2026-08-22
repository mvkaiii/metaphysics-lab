import unittest
from datetime import date

from engine.natal.export import (
    export_bazi_markdown,
    export_calibration_markdown,
    export_ziwei_markdown,
)
from engine.natal.models import NatalSource, NormalizedNatalChart, ProjectNatalView
from engine.natal.reconciliation import reconcile_natal


class NatalExportTests(unittest.TestCase):
    def setUp(self):
        self.project_source = NatalSource(
            source_type="project",
            source_name="Metaphysics Lab",
            source_version="2C0-exp",
            rule_profile="natal-foundation-v1",
            rule_version="1.0-exp",
            maturity="experimental",
            validation_status="qualified_candidate",
        )

    def chart(self, *, blocking_time_conflict=False):
        project = ProjectNatalView(
            birth={
                "reported_datetime": "2000-01-01T19:20:00+08:00",
                "place_label": "Public Fixture City",
            },
            time_basis={
                "normalized_civil_time": "2000-01-01T19:20:00+08:00",
                "true_solar_time": "2000-01-01T19:16:00+08:00",
                "effective_hour_branch": "戌",
                "adjustment_minutes": -4.0,
                "profile_id": "true-solar-noaa-gamma-v1",
                "rule_version": "1.0-exp",
            },
            bazi={
                "pillars": {
                    "hour": "戊戌",
                    "day": "丙辰",
                    "month": "丁卯",
                    "year": "甲子",
                },
                "day_master": "丙",
                "decadal_direction": "forward",
            },
            ziwei={
                "ming_palace": "命宮",
                "body_palace": "夫妻宮",
                "five_element_bureau": "水二局",
                "palaces": [
                    {"name": "父母宮", "branch": "亥", "heavenly_stem": "乙"},
                    {"name": "夫妻宮", "branch": "辰", "heavenly_stem": "庚"},
                    {"name": "命宮", "branch": "戌", "heavenly_stem": "甲"},
                ],
                "stars": [
                    {"star": "天機", "palace": "命宮", "brightness": "平"},
                    {"star": "紫微", "palace": "夫妻宮", "brightness": "旺"},
                    {"star": "左輔", "palace": "父母宮", "brightness": None},
                ],
                "birth_transformations": {
                    "忌": "太陽",
                    "科": "武曲",
                    "權": "破軍",
                    "祿": "廉貞",
                },
            },
            source=self.project_source,
        )
        resolved = reconcile_natal(None, project, project_maturity="experimental")
        validation = {
            "overall_status": "qualified_candidate",
            "time_profile_status": "CONFLICT" if blocking_time_conflict else "EQUIVALENT",
            "time_profile_severity": "BLOCKING" if blocking_time_conflict else "INFO",
        }
        return NormalizedNatalChart(
            identity="public-natal-fixture",
            external=None,
            project=project,
            resolved=resolved,
            validation=validation,
            provenance={
                "classification": "Project 原生盤面",
                "engine": "Metaphysics Lab",
                "profile_id": "natal-foundation-v1",
                "rule_version": "1.0-exp",
            },
        )

    def test_all_exporters_have_required_fact_only_sections(self):
        required = (
            "## 資料來源",
            "## 資料分類",
            "## Engine / Profile / Rule Version",
            "## 出生資料",
            "## 時間校正摘要",
            "## Validation / Reconciliation",
            "## 正式盤面欄位",
            "## Provenance 摘要",
        )
        forbidden = ("AI判斷", "身強弱", "喜用神", "人生結論")
        for exporter in (export_bazi_markdown, export_ziwei_markdown, export_calibration_markdown):
            with self.subTest(exporter=exporter.__name__):
                text = exporter(self.chart(), date(2026, 8, 22))
                for heading in required:
                    self.assertIn(heading, text)
                for heading in forbidden:
                    self.assertNotIn(heading, text)

    def test_same_input_and_generated_date_are_byte_identical(self):
        chart = self.chart()
        generated_date = date(2026, 8, 22)
        for exporter in (export_bazi_markdown, export_ziwei_markdown, export_calibration_markdown):
            first = exporter(chart, generated_date)
            second = exporter(chart, generated_date)
            self.assertEqual(first.encode("utf-8"), second.encode("utf-8"))

    def test_bazi_pillar_order_is_year_month_day_hour(self):
        text = export_bazi_markdown(self.chart(), date(2026, 8, 22))
        positions = [text.index("bazi.pillars.%s" % key) for key in ("year", "month", "day", "hour")]
        self.assertEqual(positions, sorted(positions))

    def test_ziwei_order_is_canonical_palace_star_and_transformation_order(self):
        text = export_ziwei_markdown(self.chart(), date(2026, 8, 22))
        palace_positions = [
            text.index("ziwei.palaces.%s.branch" % name)
            for name in ("命宮", "夫妻宮", "父母宮")
        ]
        self.assertEqual(palace_positions, sorted(palace_positions))

        star_positions = [
            text.index("ziwei.stars.%s.palace" % star)
            for star in ("紫微", "天機", "左輔")
        ]
        self.assertEqual(star_positions, sorted(star_positions))

        transformation_positions = [
            text.index("ziwei.birth_transformations.%s" % kind)
            for kind in ("祿", "權", "科", "忌")
        ]
        self.assertEqual(transformation_positions, sorted(transformation_positions))

    def test_time_summary_is_plain_language_and_boundary_sensitive(self):
        equivalent = export_calibration_markdown(self.chart(), date(2026, 8, 22))
        self.assertIn("已完成出生地時間校正，未造成時辰／核心盤面變更。", equivalent)

        conflict = export_calibration_markdown(
            self.chart(blocking_time_conflict=True), date(2026, 8, 22)
        )
        self.assertIn("出生時間校正跨越命理邊界；請查看「排盤差異」區塊。", conflict)

    def test_exporter_does_not_recalculate_or_invent_missing_facts(self):
        project = ProjectNatalView(
            birth={}, time_basis={}, bazi={}, ziwei={}, source=self.project_source
        )
        chart = NormalizedNatalChart(
            identity="empty-public-fixture",
            external=None,
            project=project,
            resolved=reconcile_natal(None, project, project_maturity="experimental"),
            validation={"overall_status": "partial"},
            provenance={"classification": "Project 原生盤面"},
        )
        text = export_bazi_markdown(chart, date(2026, 8, 22))
        self.assertNotIn("bazi.pillars.year", text)
        self.assertNotIn("甲子", text)
        self.assertIn("無可輸出的正式欄位。", text)


if __name__ == "__main__":
    unittest.main()
