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
                "month": "丁酉",
                "day": "庚寅",
                "time": "癸未",
                "solar_term_boundary_caution_minutes": 120,
                "boundary_warning": None,
                "ten_gods": {
                    "year": "正官",
                    "month": "正財",
                    "day": "偏印",
                    "time": "傷官",
                },
            },
            "ziwei": {
                "decadal": {
                    "scope": "decadal",
                    "reference": decadal_reference,
                    "classification": "Project 推導盤面",
                    "maturity": "stable",
                    "flowing_star_layer": {
                        "source": {
                            "reference": decadal_reference,
                            "validation_status": "validated",
                            "source_profile": "flowing-star-v1",
                            "rule_version": "1-exp",
                        }
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
                        "source": {
                            "reference": yearly_reference,
                            "validation_status": "validated",
                            "source_profile": "flowing-star-v1",
                            "rule_version": "1-exp",
                        }
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

    def test_bazi_provenance_preserves_detached_raw_source_record(self):
        source = self.context()
        before = copy.deepcopy(source["bazi"])

        result = build_evidence_features(source, target_scope="yearly")
        yearly = next(
            item
            for item in result["features"]
            if item["system"] == "bazi" and item["scope"] == "yearly"
        )

        raw_record = yearly["provenance"]["source_record"]
        self.assertEqual(raw_record, before)
        self.assertEqual(raw_record["day_rollover"], "23:00 子初換日")
        self.assertEqual(raw_record["solar_term_boundary_caution_minutes"], 120)

        raw_record["day_rollover"] = "mutated-output"
        self.assertEqual(source["bazi"]["day_rollover"], "23:00 子初換日")

    def test_decadal_evidence_is_modifier_for_yearly_target(self):
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


if __name__ == "__main__":
    unittest.main()
