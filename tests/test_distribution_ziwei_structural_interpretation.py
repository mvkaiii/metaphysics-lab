import unittest

from engine.distribution.ziwei_structural_interpretation import interpret_ziwei_structural_features


class ZiweiStructuralInterpretationTests(unittest.TestCase):
    def context(self, *, two_career_stars=False, with_transformation=False):
        yearly_placements = [
            {
                "base_star": "天魁",
                "category": "soft",
                "scope": "yearly",
                "target_branch": "午",
                "sequence": 1,
            },
            {
                "base_star": "紅鸞",
                "category": "flower",
                "scope": "yearly",
                "target_branch": "卯",
                "sequence": 2,
            },
        ]
        yearly_materialized = [
            {
                "base_star": "天魁",
                "display_name": "流天魁",
                "target_branch": "午",
                "natal_palace": "財帛宮",
                "scope_palace": "官祿宮",
                "scope": "yearly",
                "source_reference": "庚午",
            },
            {
                "base_star": "紅鸞",
                "display_name": "流紅鸞",
                "target_branch": "卯",
                "natal_palace": "夫妻宮",
                "scope_palace": "夫妻宮",
                "scope": "yearly",
                "source_reference": "庚午",
            },
        ]
        if two_career_stars:
            yearly_placements.append(
                {
                    "base_star": "天鉞",
                    "category": "helper",
                    "scope": "yearly",
                    "target_branch": "申",
                    "sequence": 3,
                }
            )
            yearly_materialized.append(
                {
                    "base_star": "天鉞",
                    "display_name": "流天鉞",
                    "target_branch": "申",
                    "natal_palace": "遷移宮",
                    "scope_palace": "官祿宮",
                    "scope": "yearly",
                    "source_reference": "庚午",
                }
            )

        monthly = {
            "scope": "monthly",
            "reference": "乙酉",
            "classification": "Project 推導盤面",
            "maturity": "experimental",
            "flowing_star_layer": {
                "placements": [
                    {
                        "base_star": "左輔",
                        "category": "soft",
                        "scope": "monthly",
                        "target_branch": "酉",
                        "sequence": 1,
                    }
                ],
                "validation": "validated",
                "maturity": "experimental",
                "source": {"validation_status": "validated"},
            },
            "materialized_flowing_stars": [
                {
                    "base_star": "左輔",
                    "display_name": "流左輔",
                    "target_branch": "酉",
                    "natal_palace": "田宅宮",
                    "scope_palace": "財帛宮",
                    "scope": "monthly",
                    "source_reference": "乙酉",
                }
            ],
            "source_resolution_count": 1,
        }
        if with_transformation:
            monthly["transformation_layer"] = {
                "validation": "validated",
                "flying_edges": [
                    {
                        "edge_id": "monthly-乙酉-忌-武曲",
                        "transformation_type": "忌",
                        "star": "武曲",
                        "target_palace": "財帛宮",
                        "geometric_relation": "same_palace",
                    }
                ],
            }

        return {
            "bazi": {},
            "calendar_context_summary": {},
            "ziwei": {
                "yearly": {
                    "scope": "yearly",
                    "reference": "庚午",
                    "classification": "Project 推導盤面",
                    "maturity": "experimental",
                    "flowing_star_layer": {
                        "placements": yearly_placements,
                        "validation": "validated",
                        "maturity": "experimental",
                        "source": {"validation_status": "validated"},
                    },
                    "materialized_flowing_stars": yearly_materialized,
                    "source_resolution_count": 1,
                },
                "monthly": monthly,
            },
            "provenance": {},
            "confidence_constraints": {
                "ziwei_requested_scopes": ["yearly", "monthly"],
            },
        }

    def test_flowing_star_category_modifies_only_its_materialized_palace_domain(self):
        features = interpret_ziwei_structural_features(self.context(), "yearly", "d" * 64)
        career = next(item for item in features if item.scope == "yearly" and item.primary_domain == "career")
        self.assertIn("support_or_coordination", career.event_family_support)
        self.assertNotIn("relationship_visibility", career.event_family_support)

    def test_same_source_multiple_stars_are_one_dependency_vote_per_domain(self):
        features = interpret_ziwei_structural_features(self.context(two_career_stars=True), "yearly", "e" * 64)
        career = [item for item in features if item.primary_domain == "career"]
        self.assertEqual(len(career), 1)
        self.assertTrue(career[0].dependency_family.startswith("ziwei.structural:yearly:"))

    def test_transformation_target_palace_owns_domain_and_keeps_generic_family(self):
        features = interpret_ziwei_structural_features(self.context(with_transformation=True), "monthly", "f" * 64)
        finance = next(item for item in features if item.primary_domain == "finance")
        self.assertIn("constraint_or_friction", finance.event_family_support)
        self.assertNotIn("bankruptcy", finance.event_family_support)

    def test_flowing_plus_transformation_same_domain_can_be_strong_but_stays_experimental(self):
        features = interpret_ziwei_structural_features(self.context(with_transformation=True), "monthly", "0" * 64)
        finance = next(item for item in features if item.primary_domain == "finance")
        self.assertEqual(finance.strength_class, "strong")
        self.assertEqual(finance.maturity, "experimental")


if __name__ == "__main__":
    unittest.main()
