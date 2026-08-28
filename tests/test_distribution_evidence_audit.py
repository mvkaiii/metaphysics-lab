import copy
import unittest

from engine.distribution.evidence import build_evidence_features


class DistributionEvidenceAuditRegressionTests(unittest.TestCase):
    def context(self):
        decadal_reference = "flow-decadal:4:官祿宮:庚午"
        yearly_reference = "flow-year:2026:丙午"
        return {
            "bazi": {
                "engine": "Project Bazi Calendar Engine",
                "version": "1.0.0",
                "classification": "Project 推導盤面",
                "reference_engine": "6tail/lunar-python v1.4.8",
                "datetime": "2026-09-15T14:30:00+08:00",
                "timezone": "Asia/Taipei",
                "day_rollover": "23:00 子初換日",
                "year": "丙午",
                "month": "甲申",
                "day": "己亥",
                "time": "壬辰",
                "solar_term_boundary_caution_minutes": 120,
                "boundary_warning": None,
                "ten_gods": {
                    "year": "正官",
                    "month": "正財",
                    "day": "偏印",
                    "time": "傷官",
                },
                "structural_context": {
                    "day_master": "辛",
                    "natal_pillars": {
                        "year": "甲子",
                        "month": "戊午",
                        "day": "辛酉",
                        "hour": "壬子",
                    },
                    "current_decadal": {
                        "index": 4,
                        "pillar": "丙寅",
                        "start_datetime": "2020-01-01T00:00:00+08:00",
                        "end_datetime": "2030-01-01T00:00:00+08:00",
                        "ten_god": "正官",
                    },
                    "decadal_boundaries_in_flow_year": [],
                },
            },
            "ziwei": {
                "decadal": {
                    "scope": "decadal",
                    "reference": decadal_reference,
                    "classification": "Project 推導盤面",
                    "maturity": "experimental",
                    "flowing_star_layer": {
                        "placements": [
                            {
                                "base_star": "祿存",
                                "category": "lucun",
                                "scope": "decadal",
                                "target_branch": "午",
                                "sequence": 1,
                            }
                        ],
                        "validation": "validated",
                        "maturity": "experimental",
                        "source": {
                            "reference": decadal_reference,
                            "validation_status": "validated",
                            "source_profile": "flowing-star-v1",
                            "rule_version": "1-exp",
                        },
                    },
                    "materialized_flowing_stars": [
                        {
                            "base_star": "祿存",
                            "display_name": "大限祿存",
                            "target_branch": "午",
                            "natal_palace": "官祿宮",
                            "scope_palace": None,
                            "scope": "decadal",
                            "source_reference": decadal_reference,
                        }
                    ],
                },
                "yearly": {
                    "scope": "yearly",
                    "reference": yearly_reference,
                    "classification": "Project 推導盤面",
                    "maturity": "experimental",
                    "flowing_star_layer": {
                        "placements": [
                            {
                                "base_star": "天魁",
                                "category": "soft",
                                "scope": "yearly",
                                "target_branch": "子",
                                "sequence": 1,
                            }
                        ],
                        "validation": "validated",
                        "maturity": "experimental",
                        "source": {
                            "reference": yearly_reference,
                            "validation_status": "validated",
                            "source_profile": "flowing-star-v1",
                            "rule_version": "1-exp",
                        },
                    },
                    "materialized_flowing_stars": [
                        {
                            "base_star": "天魁",
                            "display_name": "流魁",
                            "target_branch": "子",
                            "natal_palace": "官祿宮",
                            "scope_palace": None,
                            "scope": "yearly",
                            "source_reference": yearly_reference,
                        }
                    ],
                },
            },
            "provenance": {
                "classification": "Project 推導盤面",
                "orchestrated_by": "engine.distribution.forecast",
                "target_calendar_resolutions": 1,
            },
            "confidence_constraints": {
                "blocking_conflict_count": 0,
                "project_natal_maturity": "experimental",
                "ziwei_requested_scopes": ["decadal", "yearly"],
                "experimental_time_layers_must_be_downweighted": True,
            },
        }

    def test_bazi_structural_provenance_is_traceable_and_output_is_detached(self):
        source = self.context()
        before = copy.deepcopy(source)

        result = build_evidence_features(source, target_scope="yearly")
        yearly = next(
            item
            for item in result["features"]
            if item["system"] == "bazi" and item["scope"] == "yearly"
        )

        provenance = yearly["provenance"]
        self.assertEqual(provenance["structural_profile"], "lin_tianji_bazi_structural_v1-exp")
        self.assertEqual(provenance["semantic_profile"], "lin_tianji_domain_v2-exp")
        self.assertEqual(provenance["source_context_digest"], result["source_context_digest"])
        self.assertIsInstance(provenance["canonical_relations"], list)
        self.assertNotIn("source_record", provenance)

        yearly["reference_window"]["pillar"] = "mutated-output"
        self.assertEqual(source, before)
        self.assertEqual(source["bazi"]["year"], "丙午")

    def test_decadal_ziwei_evidence_is_modifier_for_yearly_target(self):
        result = build_evidence_features(self.context(), target_scope="yearly")
        decadal = [
            item
            for item in result["features"]
            if item["system"] == "ziwei" and item["scope"] == "decadal"
        ]

        self.assertEqual(len(decadal), 1)
        self.assertEqual(decadal[0]["role"], "modifier")
        self.assertEqual(decadal[0]["qualification_status"], "qualified")
        self.assertEqual(decadal[0]["primary_domain"], "career")
        self.assertIn("resource_accumulation", decadal[0]["event_family_support"])


if __name__ == "__main__":
    unittest.main()
