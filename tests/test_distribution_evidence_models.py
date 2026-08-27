import json
import unittest

from engine.distribution.evidence_models import (
    EvidenceFeature,
    MATURITY_STATES,
    QUALIFICATION_STATES,
    ROLES,
    SCOPES,
    STRENGTH_CLASSES,
    SYSTEMS,
    evidence_feature_from_dict,
)
from engine.distribution.errors import DistributionError


VALID = {
    "feature_id": "ziwei:yearly:career:001",
    "system": "ziwei",
    "scope": "yearly",
    "reference_window": {
        "reference": "2026",
        "start": "2026-02-04T04:02:00+08:00",
        "end": "2027-02-04T09:46:00+08:00",
    },
    "primary_domain": "career",
    "event_family_support": ["role_change", "authority_change"],
    "strength_class": "moderate",
    "maturity": "experimental",
    "qualification_status": "qualified",
    "source_family": "ziwei.flowing_stars",
    "dependency_family": "ziwei:yearly:2026",
    "role": "target_evidence",
    "provenance": {
        "classification": "Project 推導盤面",
        "source_reference": "ziwei:yearly:2026",
        "raw": {"star": "流魁", "palace": "官祿宮"},
    },
}


class EvidenceFeatureModelTests(unittest.TestCase):
    def test_contract_constant_sets_are_explicit_and_version_safe(self):
        self.assertEqual(SYSTEMS, ("bazi", "ziwei", "qimen", "historical", "reality"))
        self.assertEqual(
            SCOPES,
            ("natal", "major_cycle", "decadal", "yearly", "monthly", "daily", "hourly"),
        )
        self.assertEqual(
            ROLES,
            ("target_evidence", "modifier", "timing_trigger", "personalization", "reality_constraint"),
        )
        self.assertEqual(MATURITY_STATES, ("stable", "experimental"))
        self.assertEqual(
            QUALIFICATION_STATES,
            ("qualified", "needs_verification", "unqualified"),
        )
        self.assertEqual(STRENGTH_CLASSES, ("unspecified", "weak", "moderate", "strong"))

    def test_round_trip_is_deterministic_and_json_safe(self):
        feature = evidence_feature_from_dict(VALID)
        self.assertIsInstance(feature, EvidenceFeature)
        self.assertEqual(feature.event_family_support, ("role_change", "authority_change"))
        first = feature.to_dict()
        second = evidence_feature_from_dict(first).to_dict()
        self.assertEqual(first, second)
        self.assertEqual(
            list(first),
            [
                "feature_id",
                "system",
                "scope",
                "reference_window",
                "primary_domain",
                "event_family_support",
                "strength_class",
                "maturity",
                "qualification_status",
                "source_family",
                "dependency_family",
                "role",
                "provenance",
            ],
        )
        self.assertEqual(
            json.dumps(first, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False),
            json.dumps(second, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False),
        )

    def test_normalized_nested_payload_is_immutable(self):
        feature = evidence_feature_from_dict(VALID)
        with self.assertRaises(TypeError):
            feature.reference_window["reference"] = "mutated"
        with self.assertRaises(TypeError):
            feature.provenance["raw"]["star"] = "mutated"
        detached = feature.to_dict()
        detached["reference_window"]["reference"] = "detached-change"
        detached["provenance"]["raw"]["star"] = "detached-change"
        self.assertEqual(feature.reference_window["reference"], "2026")
        self.assertEqual(feature.provenance["raw"]["star"], "流魁")

    def test_invalid_enums_are_rejected(self):
        for field, value in (
            ("system", "tarot"),
            ("scope", "weekly"),
            ("role", "ranking_vote"),
            ("maturity", "stable-ish"),
            ("qualification_status", "maybe"),
            ("strength_class", "extreme"),
        ):
            with self.subTest(field=field):
                payload = dict(VALID)
                payload[field] = value
                with self.assertRaises(DistributionError) as caught:
                    evidence_feature_from_dict(payload)
                self.assertEqual(caught.exception.code, "invalid_evidence_feature")
                self.assertEqual(caught.exception.details.get("field"), field)

    def test_empty_domain_is_rejected(self):
        payload = dict(VALID)
        payload["primary_domain"] = "   "
        with self.assertRaises(DistributionError) as caught:
            evidence_feature_from_dict(payload)
        self.assertEqual(caught.exception.code, "invalid_evidence_feature")
        self.assertEqual(caught.exception.details.get("field"), "primary_domain")

    def test_non_json_reference_or_provenance_is_rejected(self):
        for field, value in (
            ("reference_window", {"start": object()}),
            ("provenance", {"raw": {1, 2, 3}}),
            ("provenance", {"strength": float("nan")}),
        ):
            with self.subTest(field=field):
                payload = dict(VALID)
                payload[field] = value
                with self.assertRaises(DistributionError) as caught:
                    evidence_feature_from_dict(payload)
                self.assertEqual(caught.exception.code, "invalid_evidence_feature")
                self.assertEqual(caught.exception.details.get("field"), field)

    def test_required_identity_and_event_family_shape_are_fail_closed(self):
        for field in ("feature_id", "source_family", "dependency_family"):
            with self.subTest(field=field):
                payload = dict(VALID)
                payload[field] = ""
                with self.assertRaises(DistributionError) as caught:
                    evidence_feature_from_dict(payload)
                self.assertEqual(caught.exception.details.get("field"), field)
        payload = dict(VALID)
        payload["event_family_support"] = "role_change"
        with self.assertRaises(DistributionError) as caught:
            evidence_feature_from_dict(payload)
        self.assertEqual(caught.exception.details.get("field"), "event_family_support")

    def test_unknown_or_missing_fields_are_rejected(self):
        missing = dict(VALID)
        del missing["role"]
        with self.assertRaises(DistributionError) as caught:
            evidence_feature_from_dict(missing)
        self.assertEqual(caught.exception.code, "invalid_evidence_feature")

        extra = dict(VALID)
        extra["score"] = 99
        with self.assertRaises(DistributionError) as caught:
            evidence_feature_from_dict(extra)
        self.assertEqual(caught.exception.code, "invalid_evidence_feature")
        self.assertIn("score", caught.exception.details.get("unknown_fields", []))


if __name__ == "__main__":
    unittest.main()
