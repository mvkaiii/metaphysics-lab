import copy
import unittest

from engine.distribution.errors import DistributionError
from engine.distribution.evidence_ranker import detect_local_spike, rank_evidence
from engine.distribution.interpretation_contract import build_interpretation_contract
from engine.distribution.prospective import resolve_query_anchor


def feature(feature_id, domain="career", scope="yearly", **overrides):
    payload = {
        "feature_id": feature_id,
        "system": "bazi",
        "scope": scope,
        "reference_window": {"scope": scope, "reference": "phase5-review"},
        "primary_domain": domain,
        "event_family_support": ["role_change"],
        "strength_class": "moderate",
        "maturity": "stable",
        "qualification_status": "qualified",
        "source_family": "fixture.bazi",
        "dependency_family": "dep:" + feature_id,
        "role": "target_evidence",
        "provenance": {"fixture": feature_id},
    }
    payload.update(overrides)
    return payload


def anchor():
    return resolve_query_anchor({
        "query_anchor_at": "2026-08-28T16:00:00+08:00",
        "query_timezone": "Asia/Taipei",
        "target_start": "2026-08-01T00:00:00+08:00",
        "target_end": "2026-12-31T23:59:59+08:00",
        "question_reference": "phase5-review-local-window-validation",
    })


def local_spike_fixture():
    parent = rank_evidence([
        feature("parent-finance", domain="finance", scope="yearly")
    ], target_scope="yearly")
    child = rank_evidence([
        feature(
            "daily-career-a",
            scope="daily",
            strength_class="strong",
            dependency_family="daily-a",
        ),
        feature(
            "daily-career-b",
            scope="daily",
            strength_class="strong",
            system="ziwei",
            source_family="fixture.ziwei",
            dependency_family="daily-b",
        ),
    ], target_scope="daily")
    windows = detect_local_spike(parent, child)
    if len(windows) != 1:
        raise AssertionError("fixture must produce exactly one local window")
    return parent, child, windows


class InterpretationContractLocalWindowValidationTests(unittest.TestCase):
    def test_parent_digest_must_be_sha256_shaped(self):
        _parent, child, windows = local_spike_fixture()
        forged = copy.deepcopy(windows)
        forged[0]["parent_ranking_digest"] = "not-a-digest"
        with self.assertRaises(DistributionError):
            build_interpretation_contract(child, anchor(), local_windows=forged)

    def test_child_scope_must_match_supplied_base_target_scope(self):
        _parent, child, windows = local_spike_fixture()
        forged = copy.deepcopy(windows)
        forged[0]["child_scope"] = "monthly"
        with self.assertRaises(DistributionError):
            build_interpretation_contract(child, anchor(), local_windows=forged)

    def test_parent_scope_must_be_coarser_than_child_scope(self):
        _parent, child, windows = local_spike_fixture()
        forged = copy.deepcopy(windows)
        forged[0]["parent_scope"] = forged[0]["child_scope"]
        with self.assertRaises(DistributionError):
            build_interpretation_contract(child, anchor(), local_windows=forged)

    def test_source_specificity_must_match_child_base_domain(self):
        _parent, child, windows = local_spike_fixture()
        self.assertEqual(child["domains"][0]["allowed_specificity"], "concrete_event")
        forged = copy.deepcopy(windows)
        forged[0]["source_allowed_specificity"] = "event_family"
        forged[0]["allowed_specificity"] = "event_family"
        forged[0]["specificity_capped"] = False
        with self.assertRaises(DistributionError):
            build_interpretation_contract(child, anchor(), local_windows=forged)

    def test_specificity_capped_flag_must_match_source_and_allowed_values(self):
        _parent, child, windows = local_spike_fixture()
        self.assertTrue(windows[0]["specificity_capped"])
        forged = copy.deepcopy(windows)
        forged[0]["specificity_capped"] = False
        with self.assertRaises(DistributionError):
            build_interpretation_contract(child, anchor(), local_windows=forged)


if __name__ == "__main__":
    unittest.main()
