import copy
import json
import unittest

from engine.distribution.structural_interpretation import interpret_structural_evidence
from engine.distribution.runtime import dispatch


class StructuralInterpretationTests(unittest.TestCase):
    def context(self, *, cross_system_career=False):
        yearly_palace = "官祿宮" if cross_system_career else "財帛宮"
        return {
            "bazi": {
                "engine": "Project Bazi Calendar Engine",
                "version": "1.0.0",
                "classification": "Project 推導盤面",
                "reference_engine": "synthetic",
                "datetime": "2026-09-15T14:30:00+08:00",
                "timezone": "Asia/Taipei",
                "year": "甲子",
                "month": "乙酉",
                "day": "丁亥",
                "time": "丁未",
                "ten_gods": {
                    "year": "正官",
                    "month": "偏財",
                    "day": "正官",
                    "time": "正印",
                },
                "boundary_warning": None,
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
            "calendar_context_summary": {},
            "ziwei": {
                "yearly": {
                    "scope": "yearly",
                    "reference": "甲子",
                    "classification": "Project 推導盤面",
                    "maturity": "experimental",
                    "flowing_star_layer": {
                        "placements": [
                            {
                                "base_star": "天魁",
                                "category": "soft",
                                "scope": "yearly",
                                "target_branch": "午",
                                "sequence": 1,
                            }
                        ],
                        "validation": "validated",
                        "maturity": "experimental",
                        "source": {
                            "reference": "甲子",
                            "validation_status": "validated",
                        },
                    },
                    "materialized_flowing_stars": [
                        {
                            "base_star": "天魁",
                            "display_name": "流天魁",
                            "target_branch": "午",
                            "natal_palace": yearly_palace,
                            "scope_palace": yearly_palace,
                            "scope": "yearly",
                            "source_reference": "甲子",
                        }
                    ],
                    "source_resolution_count": 1,
                }
            },
            "provenance": {
                "classification": "Project 推導盤面",
                "orchestrated_by": "synthetic-test",
            },
            "confidence_constraints": {
                "blocking_conflict_count": 0,
                "project_natal_maturity": "stable",
                "ziwei_requested_scopes": ["yearly"],
                "experimental_time_layers_must_be_downweighted": True,
            },
        }

    def test_combined_output_is_byte_deterministic_and_v2_only(self):
        context = self.context()
        first = interpret_structural_evidence(context, "yearly")
        second = interpret_structural_evidence(copy.deepcopy(context), "yearly")
        self.assertEqual(
            json.dumps(first, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            json.dumps(second, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        )
        self.assertEqual(first["mapping_profile_version"], "lin_tianji_domain_v2-exp")
        self.assertTrue(first["features"])
        self.assertEqual(len(first["interpretation_digest"]), 64)

    def test_runtime_rejects_history_material_in_phase35_payload(self):
        result = dispatch(
            "interpret_structural_evidence",
            {
                "forecast_context": self.context(),
                "target_scope": "yearly",
                "historical_records": [{"actual_event": "forbidden"}],
            },
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "invalid_structural_interpretation_payload")

    def test_bazi_and_ziwei_same_domain_remain_independent_features(self):
        result = interpret_structural_evidence(self.context(cross_system_career=True), "yearly")
        career = [
            item
            for item in result["features"]
            if item["scope"] == "yearly" and item["primary_domain"] == "career"
        ]
        self.assertEqual({item["system"] for item in career}, {"bazi", "ziwei"})
        self.assertEqual(len({item["dependency_family"] for item in career}), 2)


if __name__ == "__main__":
    unittest.main()
