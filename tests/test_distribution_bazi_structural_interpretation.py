import unittest

from engine.distribution.bazi_structural_interpretation import interpret_bazi_structural_features


class BaziStructuralInterpretationTests(unittest.TestCase):
    def context(
        self,
        *,
        year="庚午",
        year_ten_god="七殺",
        natal_pillars=None,
        current_decadal="丙寅",
        boundary_warning=None,
        requested_scopes=None,
    ):
        natal = natal_pillars or {
            "year": "乙丑",
            "month": "丁卯",
            "day": "辛酉",
            "hour": "壬子",
        }
        scopes = list(requested_scopes or ["yearly"])
        current = None
        if current_decadal is not None:
            current = {
                "index": 4,
                "pillar": current_decadal,
                "start_datetime": "2020-01-01T00:00:00+08:00",
                "end_datetime": "2030-01-01T00:00:00+08:00",
                "ten_god": "正官",
            }
        return {
            "bazi": {
                "datetime": "2026-09-15T14:30:00+08:00",
                "year": year,
                "month": "乙酉",
                "day": "丁亥",
                "time": "丁未",
                "ten_gods": {
                    "year": year_ten_god,
                    "month": "偏財",
                    "day": "正官",
                    "time": "正印",
                },
                "boundary_warning": boundary_warning,
                "structural_context": {
                    "day_master": "辛",
                    "natal_pillars": natal,
                    "current_decadal": current,
                    "decadal_boundaries_in_flow_year": [],
                },
            },
            "ziwei": {},
            "confidence_constraints": {
                "blocking_conflict_count": 0,
                "project_natal_maturity": "stable",
                "ziwei_requested_scopes": scopes,
                "experimental_time_layers_must_be_downweighted": True,
            },
        }

    def test_yearly_target_is_one_aggregate_feature_even_with_multiple_natal_relations(self):
        context = self.context(
            year="甲子",
            year_ten_god="正官",
            natal_pillars={
                "year": "甲子",
                "month": "戊午",
                "day": "辛酉",
                "hour": "壬子",
            },
            current_decadal="丙寅",
        )
        features = interpret_bazi_structural_features(context, "yearly", "a" * 64)
        yearly = [item for item in features if item.scope == "yearly"]
        self.assertEqual(len(yearly), 1)
        self.assertEqual(yearly[0].primary_domain, "career")
        self.assertEqual(yearly[0].strength_class, "strong")
        self.assertIn("formal_role", yearly[0].event_family_support)
        self.assertIn("recurrence_or_reactivation", yearly[0].event_family_support)
        self.assertNotIn("resignation", yearly[0].event_family_support)
        self.assertEqual(yearly[0].dependency_family, "bazi.structural:yearly:甲子:career")

    def test_current_decadal_is_modifier_not_extra_target_vote_for_yearly_question(self):
        features = interpret_bazi_structural_features(self.context(), "yearly", "b" * 64)
        decadal = [item for item in features if item.scope == "decadal"]
        self.assertEqual(len(decadal), 1)
        self.assertEqual(decadal[0].role, "modifier")
        self.assertNotEqual(decadal[0].role, "target_evidence")

    def test_history_fields_are_not_part_of_bazi_interpreter_contract(self):
        context = self.context()
        context["historical_records"] = [{"actual_event": "synthetic forbidden input"}]
        with self.assertRaises(Exception):
            interpret_bazi_structural_features(context, "yearly", "c" * 64)

    def test_boundary_warning_marks_bazi_feature_needs_verification(self):
        context = self.context(boundary_warning={"needs_external_verification": True})
        features = interpret_bazi_structural_features(context, "yearly", "d" * 64)
        yearly = next(item for item in features if item.scope == "yearly")
        self.assertEqual(yearly.qualification_status, "needs_verification")


if __name__ == "__main__":
    unittest.main()
