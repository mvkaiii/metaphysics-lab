import copy
import json
import unittest

from engine.distribution.evidence import (
    BAZI_TEN_GOD_MAPPING,
    MAPPING_PROFILE,
    ZIWEI_PALACE_MAPPING,
    build_evidence_features,
)
from engine.distribution.errors import DistributionError


class DistributionEvidenceTests(unittest.TestCase):
    def context(self):
        yearly_reference = "flow-year:2026:丙午"
        monthly_reference = "flow-month:2026-09:丁酉"
        return {
            "bazi": {
                "engine": "Project Bazi Calendar Engine",
                "version": "1.0.0",
                "classification": "Project 推導盤面",
                "reference_engine": "6tail/lunar-python v1.4.8",
                "datetime": "2026-09-15T14:30:00+08:00",
                "timezone": "Asia/Taipei",
                "year": "丙午",
                "month": "丁酉",
                "day": "庚寅",
                "time": "癸未",
                "ten_gods": {
                    "year": "正官",
                    "month": "正財",
                    "day": "偏印",
                    "time": "傷官",
                },
                "boundary_warning": None,
            },
            "ziwei": {
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
                        },
                        {
                            "base_star": "祿存",
                            "display_name": "流祿",
                            "target_branch": "丑",
                            "natal_palace": "財帛宮",
                            "scope_palace": None,
                            "scope": "yearly",
                            "source_reference": yearly_reference,
                        },
                    ],
                },
                "monthly": {
                    "scope": "monthly",
                    "reference": monthly_reference,
                    "classification": "Project 推導盤面",
                    "maturity": "experimental",
                    "flowing_star_layer": {
                        "source": {
                            "reference": monthly_reference,
                            "validation_status": "boundary_caution",
                            "source_profile": "flowing-star-v1",
                            "rule_version": "1-exp",
                        }
                    },
                    "materialized_flowing_stars": [
                        {
                            "base_star": "天馬",
                            "display_name": "月馬",
                            "target_branch": "寅",
                            "natal_palace": "遷移宮",
                            "scope_palace": None,
                            "scope": "monthly",
                            "source_reference": monthly_reference,
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
                "ziwei_requested_scopes": ["yearly", "monthly"],
                "experimental_time_layers_must_be_downweighted": True,
            },
        }

    @staticmethod
    def canonical_bytes(value):
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")

    def test_mapping_profile_uses_general_project_structural_labels(self):
        self.assertEqual(MAPPING_PROFILE, "lin_tianji_domain_v1-exp")
        self.assertEqual(
            set(BAZI_TEN_GOD_MAPPING),
            {"比肩", "劫財", "食神", "傷官", "偏財", "正財", "七殺", "正官", "偏印", "正印"},
        )
        self.assertEqual(BAZI_TEN_GOD_MAPPING["正官"]["primary_domain"], "career")
        self.assertIn("formal_role", BAZI_TEN_GOD_MAPPING["正官"]["event_family_support"])
        self.assertEqual(len(ZIWEI_PALACE_MAPPING), 12)
        self.assertEqual(ZIWEI_PALACE_MAPPING["官祿宮"]["primary_domain"], "career")
        self.assertEqual(ZIWEI_PALACE_MAPPING["夫妻宮"]["primary_domain"], "partnership")
        self.assertEqual(ZIWEI_PALACE_MAPPING["疾厄宮"]["primary_domain"], "health")

    def test_bazi_adapter_materializes_only_requested_scopes_with_roles(self):
        result = build_evidence_features(self.context(), target_scope="yearly")
        bazi = [item for item in result["features"] if item["system"] == "bazi"]

        self.assertEqual(result["target_scope"], "yearly")
        self.assertEqual(result["mapping_profile"], MAPPING_PROFILE)
        self.assertEqual([item["scope"] for item in bazi], ["yearly", "monthly"])
        self.assertEqual([item["role"] for item in bazi], ["target_evidence", "timing_trigger"])
        self.assertEqual([item["primary_domain"] for item in bazi], ["career", "finance"])
        self.assertTrue(all(item["maturity"] == "experimental" for item in bazi))
        self.assertTrue(all(item["strength_class"] == "unspecified" for item in bazi))
        self.assertNotIn("daily", {item["scope"] for item in bazi})
        self.assertNotIn("hourly", {item["scope"] for item in bazi})

    def test_ziwei_adapter_preserves_raw_record_and_shared_dependency_family(self):
        result = build_evidence_features(self.context(), target_scope="yearly")
        yearly = [
            item
            for item in result["features"]
            if item["system"] == "ziwei" and item["scope"] == "yearly"
        ]
        monthly = [
            item
            for item in result["features"]
            if item["system"] == "ziwei" and item["scope"] == "monthly"
        ]

        self.assertEqual([item["primary_domain"] for item in yearly], ["career", "finance"])
        self.assertEqual({item["role"] for item in yearly}, {"target_evidence"})
        self.assertEqual(len({item["dependency_family"] for item in yearly}), 1)
        self.assertEqual(monthly[0]["role"], "timing_trigger")
        self.assertEqual(monthly[0]["qualification_status"], "needs_verification")
        self.assertEqual(monthly[0]["primary_domain"], "mobility_external")
        self.assertEqual(
            yearly[0]["provenance"]["source_record"]["natal_palace"],
            "官祿宮",
        )
        self.assertEqual(
            yearly[0]["provenance"]["source_layer"]["source"]["reference"],
            "flow-year:2026:丙午",
        )

    def test_output_is_json_safe_traceable_and_contains_no_ranking_fields(self):
        source = self.context()
        before = copy.deepcopy(source)
        result = build_evidence_features(source, target_scope="yearly")

        encoded = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        self.assertTrue(encoded)
        self.assertEqual(source, before)
        self.assertEqual(len(result["source_context_digest"]), 64)
        for feature in result["features"]:
            self.assertNotIn("weight", feature)
            self.assertNotIn("score", feature)
            self.assertNotIn("rank", feature)
            self.assertNotIn("probability", feature)

    def test_builder_is_byte_deterministic_and_preserves_feature_order(self):
        source = self.context()
        first = build_evidence_features(source, target_scope="yearly")
        second = build_evidence_features(source, target_scope="yearly")

        self.assertEqual(self.canonical_bytes(first), self.canonical_bytes(second))
        self.assertEqual(
            [feature["feature_id"] for feature in first["features"]],
            [feature["feature_id"] for feature in second["features"]],
        )

    def test_missing_or_unsupported_scope_is_explicitly_blocked(self):
        missing_declaration = self.context()
        del missing_declaration["confidence_constraints"]["ziwei_requested_scopes"]
        with self.assertRaises(DistributionError) as caught:
            build_evidence_features(missing_declaration, target_scope="yearly")
        self.assertEqual(caught.exception.code, "evidence_scope_blocked")
        self.assertEqual(caught.exception.details["reason"], "missing_requested_scopes")

        with self.assertRaises(DistributionError) as caught:
            build_evidence_features(self.context(), target_scope="natal")
        self.assertEqual(caught.exception.code, "evidence_scope_blocked")
        self.assertEqual(caught.exception.details["target_scope"], "natal")

        missing_materialized_scope = self.context()
        del missing_materialized_scope["ziwei"]["monthly"]
        with self.assertRaises(DistributionError) as caught:
            build_evidence_features(missing_materialized_scope, target_scope="yearly")
        self.assertEqual(caught.exception.code, "evidence_scope_blocked")
        self.assertEqual(caught.exception.details["scope"], "monthly")


if __name__ == "__main__":
    unittest.main()
