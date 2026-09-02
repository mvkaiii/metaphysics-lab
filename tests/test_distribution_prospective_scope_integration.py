import hashlib
import json
import unittest

from engine.distribution.bazi_structural_interpretation import (
    interpret_bazi_structural_features,
)
from engine.distribution.errors import DistributionError
from engine.distribution.event_family_attribution import (
    build_event_family_attribution_bundle,
)
from engine.distribution.evidence_models import EvidenceFeature
from engine.distribution.evidence_ranker import rank_evidence
from engine.distribution.prospective_window_scope import (
    resolve_prospective_window_scope,
)
from engine.distribution.structural_policy import role_for_scope


def _digest(payload):
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _context():
    return {
        "bazi": {
            "datetime": "2026-10-15T12:00:00+08:00",
            "year": "丙午",
            "month": "戊戌",
            "ten_gods": {
                "year": "比肩",
                "month": "食神",
            },
            "boundary_warning": False,
            "structural_context": {
                "natal_pillars": {
                    "year": "甲子",
                    "month": "丁卯",
                    "day": "丙午",
                    "hour": "戊戌",
                },
                "current_decadal": {
                    "pillar": "辛未",
                    "ten_god": "正財",
                },
                "decadal_boundaries_in_flow_year": [],
            },
        },
        "calendar_context_summary": {},
        "ziwei": {},
        "provenance": {},
        "confidence_constraints": {
            "ziwei_requested_scopes": ["yearly", "monthly"],
        },
    }


def _structural_bundle(features, target_scope):
    body = {
        "structural_profile_version": "test-structural-integration",
        "mapping_profile_version": "lin_tianji_domain_v2-exp",
        "target_scope": target_scope,
        "source_context_digest": "a" * 64,
        "features": [feature.to_dict() for feature in features],
    }
    return {**body, "interpretation_digest": _digest(body)}


def _efa_from_features(features, target_scope):
    ranking = rank_evidence(list(features), target_scope=target_scope)
    structural = _structural_bundle(features, target_scope)
    return ranking, build_event_family_attribution_bundle(
        base_ranking=ranking,
        structural_interpretation=structural,
    )


def _feature(feature_id, scope, domain, family, role):
    return EvidenceFeature(
        feature_id=feature_id,
        system="bazi",
        scope=scope,
        reference_window={"scope": scope},
        primary_domain=domain,
        event_family_support=(family,),
        strength_class="moderate",
        maturity="experimental",
        qualification_status="qualified",
        source_family="test.prospective_scope_integration",
        dependency_family="dep:%s" % feature_id,
        role=role,
        provenance={"fixture": "outcome_free"},
    )


class DistributionProspectiveScopeIntegrationTests(unittest.TestCase):
    @staticmethod
    def _q4():
        return resolve_prospective_window_scope(
            {
                "window_start": "2026-10-01T00:00:00+08:00",
                "window_end": "2026-12-31T23:59:59+08:00",
                "timezone": "Asia/Taipei",
            }
        )

    @staticmethod
    def _h2():
        return resolve_prospective_window_scope(
            {
                "window_start": "2027-07-01T00:00:00+08:00",
                "window_end": "2027-12-31T23:59:59+08:00",
                "timezone": "Asia/Taipei",
            }
        )

    def test_policy_selected_yearly_is_identical_to_explicit_yearly_through_bazi_rank_and_efa(self):
        context = _context()
        selected_scope = self._q4()["claim_target_scope"]
        explicit_scope = "yearly"

        selected_features = interpret_bazi_structural_features(
            context,
            selected_scope,
            "a" * 64,
        )
        explicit_features = interpret_bazi_structural_features(
            context,
            explicit_scope,
            "a" * 64,
        )
        self.assertEqual(
            [item.to_dict() for item in selected_features],
            [item.to_dict() for item in explicit_features],
        )

        selected_ranking, selected_efa = _efa_from_features(
            selected_features,
            selected_scope,
        )
        explicit_ranking, explicit_efa = _efa_from_features(
            explicit_features,
            explicit_scope,
        )
        self.assertEqual(selected_ranking, explicit_ranking)
        self.assertEqual(selected_efa, explicit_efa)

    def test_monthly_scope_is_timing_trigger_and_cannot_open_absent_yearly_domain(self):
        self.assertEqual(role_for_scope("monthly", "yearly"), "timing_trigger")
        features = (
            _feature(
                "year-career",
                "yearly",
                "career",
                "career_role",
                role_for_scope("yearly", "yearly"),
            ),
            _feature(
                "month-finance",
                "monthly",
                "finance",
                "earned_income",
                role_for_scope("monthly", "yearly"),
            ),
        )
        ranking, efa = _efa_from_features(features, "yearly")

        self.assertEqual(ranking["opened_domains"], ["career"])
        self.assertEqual(
            [row["primary_domain"] for row in efa["children"]],
            ["career"],
        )
        self.assertNotIn(
            "child:yearly:finance:earned_income",
            [row["child_claim_id"] for row in efa["children"]],
        )

    def test_q4_and_h2_window_labels_do_not_rename_yearly_child_ids(self):
        q4_scope = self._q4()["claim_target_scope"]
        h2_scope = self._h2()["claim_target_scope"]
        self.assertEqual(q4_scope, "yearly")
        self.assertEqual(h2_scope, "yearly")

        features = (
            _feature(
                "year-career",
                "yearly",
                "career",
                "career_role",
                role_for_scope("yearly", "yearly"),
            ),
        )
        _, q4_efa = _efa_from_features(features, q4_scope)
        _, h2_efa = _efa_from_features(features, h2_scope)

        q4_ids = [row["child_claim_id"] for row in q4_efa["children"]]
        h2_ids = [row["child_claim_id"] for row in h2_efa["children"]]
        self.assertEqual(q4_ids, h2_ids)
        self.assertEqual(q4_ids, ["child:yearly:career:career_role"])
        self.assertFalse(any("q4" in child_id.lower() for child_id in q4_ids))
        self.assertFalse(any("h2" in child_id.lower() for child_id in h2_ids))

    def test_scope_resolver_rejects_forecast_or_post_lock_objects(self):
        base = {
            "window_start": "2026-10-01T00:00:00+08:00",
            "window_end": "2026-12-31T23:59:59+08:00",
            "timezone": "Asia/Taipei",
        }
        for field in (
            "forecast_context",
            "features",
            "historical_records",
            "outcome",
            "oracle",
            "legacy_output",
            "candidate_output",
            "q1_result",
            "t1_result",
        ):
            with self.subTest(field=field):
                payload = dict(base)
                payload[field] = {}
                with self.assertRaises(DistributionError) as caught:
                    resolve_prospective_window_scope(payload)
                self.assertEqual(caught.exception.code, "invalid_prospective_window_scope")


if __name__ == "__main__":
    unittest.main()
