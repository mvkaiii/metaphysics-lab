import unittest

from engine.bazi.structural_relations import detect_structural_relations


class BaziStructuralRelationTests(unittest.TestCase):
    def test_full_repeat_suppresses_lower_repeat_for_same_natal_component(self):
        rows = detect_structural_relations(
            scope="yearly",
            target_pillar="甲子",
            natal_pillars={
                "year": "甲子",
                "month": "丁卯",
                "day": "庚午",
                "hour": "辛酉",
            },
            decadal_pillar="丙寅",
        )
        families = [row.relation_family for row in rows]
        self.assertIn("natal_pillar_repeat", families)
        repeated_year = [
            row
            for row in rows
            if row.target_layer == "natal" and row.target_component == "year"
        ]
        self.assertFalse(any(row.relation_family == "branch_repeat" for row in repeated_year))
        self.assertFalse(any(row.relation_family == "stem_repeat" for row in repeated_year))

    def test_yearly_scope_can_emit_sui_yun_bing_lin_but_monthly_cannot(self):
        natal = {
            "year": "甲子",
            "month": "乙丑",
            "day": "丙寅",
            "hour": "丁卯",
        }
        yearly = detect_structural_relations(
            scope="yearly",
            target_pillar="戊辰",
            natal_pillars=natal,
            decadal_pillar="戊辰",
        )
        monthly = detect_structural_relations(
            scope="monthly",
            target_pillar="戊辰",
            natal_pillars=natal,
            decadal_pillar="戊辰",
        )
        self.assertIn("sui_yun_bing_lin", {row.relation_family for row in yearly})
        self.assertNotIn("sui_yun_bing_lin", {row.relation_family for row in monthly})

    def test_decadal_boundary_is_yearly_only(self):
        natal = {
            "year": "甲子",
            "month": "乙丑",
            "day": "丙寅",
            "hour": "丁卯",
        }
        yearly = detect_structural_relations(
            scope="yearly",
            target_pillar="庚午",
            natal_pillars=natal,
            decadal_pillar="辛未",
            decadal_boundary=True,
        )
        daily = detect_structural_relations(
            scope="daily",
            target_pillar="庚午",
            natal_pillars=natal,
            decadal_pillar="辛未",
            decadal_boundary=True,
        )
        self.assertIn("decadal_boundary", {row.relation_family for row in yearly})
        self.assertNotIn("decadal_boundary", {row.relation_family for row in daily})

    def test_output_order_is_canonical_when_natal_mapping_order_changes(self):
        natal = {
            "hour": "乙亥",
            "day": "甲寅",
            "month": "戊午",
            "year": "丙申",
        }
        first = detect_structural_relations(
            scope="yearly",
            target_pillar="庚申",
            natal_pillars=natal,
            decadal_pillar="壬子",
        )
        second = detect_structural_relations(
            scope="yearly",
            target_pillar="庚申",
            natal_pillars=dict(reversed(list(natal.items()))),
            decadal_pillar="壬子",
        )
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
