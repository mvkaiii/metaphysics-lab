import copy
import unittest

from engine.historical.models import ActivationEvidence, ActivationRankVector
from engine.historical.selector import (
    build_year_evidence,
    completed_flow_year_periods,
    rank_evidence,
    select_historical_activation,
)


NATAL = {
    "validation": {"blocking_conflict_count": 0},
    "project": {
        "birth": {"timezone": "Asia/Taipei"},
        "bazi": {
            "pillars": {
                "year": "庚子",
                "month": "甲申",
                "day": "丙午",
                "hour": "戊辰",
            },
            "day_master": "丙",
            "decadal_periods": [
                {
                    "index": 3,
                    "pillar": "己亥",
                    "start_datetime": "2005-06-01T00:00:00+08:00",
                    "end_datetime": "2015-06-01T00:00:00+08:00",
                },
                {
                    "index": 4,
                    "pillar": "庚子",
                    "start_datetime": "2015-06-01T00:00:00+08:00",
                    "end_datetime": "2025-06-01T00:00:00+08:00",
                },
                {
                    "index": 5,
                    "pillar": "辛丑",
                    "start_datetime": "2025-06-01T00:00:00+08:00",
                    "end_datetime": "2035-06-01T00:00:00+08:00",
                },
            ],
        },
    },
}


class HistoricalActivationSelectorTests(unittest.TestCase):
    def test_models_validate_tiers_and_rank_priority(self):
        with self.assertRaises(ValueError):
            ActivationEvidence(
                evidence_id="x", tier=0, relation_family="bad", target_layer="natal",
                target_component="day", participants=("子",), metadata={},
            )
        tier1 = ActivationRankVector(1, 1, False, 0, 0, 0, 0)
        many_tier2 = ActivationRankVector(0, 0, False, 9, 99, 99, 99)
        self.assertGreater(tier1.as_sort_key(2020), many_tier2.as_sort_key(2025))

    def test_completed_window_uses_last_ten_finished_lichun_periods(self):
        periods = completed_flow_year_periods("2026-08-23T10:27:00+08:00", "Asia/Taipei")
        self.assertEqual([item["label_year"] for item in periods], list(range(2016, 2026)))
        self.assertTrue(all(item["period_start"] < item["period_end"] for item in periods))
        self.assertTrue(all("T" in item["period_start"] for item in periods))

    def test_january_as_of_excludes_unfinished_current_flow_year(self):
        periods = completed_flow_year_periods("2026-01-15T12:00:00+08:00", "Asia/Taipei")
        self.assertEqual([item["label_year"] for item in periods], list(range(2015, 2025)))

    def test_tier1_detects_sui_yun_and_suppresses_lower_repeats(self):
        evidence = build_year_evidence(
            label_year=2020,
            flow_year_pillar="庚子",
            natal_pillars=NATAL["project"]["bazi"]["pillars"],
            decadal_pillar="庚子",
            decadal_boundary=False,
        )
        families = [item.relation_family for item in evidence]
        self.assertIn("sui_yun_bing_lin", families)
        self.assertIn("natal_pillar_repeat", families)
        self.assertNotIn(
            ("branch_repeat", "decadal"),
            [(item.relation_family, item.target_layer) for item in evidence],
        )
        self.assertNotIn(
            ("stem_repeat", "decadal"),
            [(item.relation_family, item.target_layer) for item in evidence],
        )

    def test_tier1_completes_three_harmony_only_once(self):
        evidence = build_year_evidence(
            label_year=2024,
            flow_year_pillar="甲辰",
            natal_pillars={"year": "庚申", "month": "壬子", "day": "丙申", "hour": "戊午"},
            decadal_pillar="乙卯",
            decadal_boundary=False,
        )
        completed = [item for item in evidence if item.relation_family == "completes_three_harmony"]
        self.assertEqual(len(completed), 1)
        self.assertEqual(set(completed[0].participants), {"申", "子", "辰"})

    def test_full_pattern_suppresses_partial_pattern(self):
        evidence = build_year_evidence(
            label_year=2024,
            flow_year_pillar="甲辰",
            natal_pillars={"year": "庚申", "month": "壬子", "day": "丙午", "hour": "戊戌"},
            decadal_pillar="乙卯",
            decadal_boundary=False,
        )
        families = [item.relation_family for item in evidence]
        self.assertIn("completes_three_harmony", families)
        self.assertNotIn("partial_three_harmony", families)

    def test_cross_layer_tier1_is_metadata_not_extra_evidence(self):
        evidence = build_year_evidence(
            label_year=2020,
            flow_year_pillar="庚子",
            natal_pillars={"year": "甲午", "month": "乙卯", "day": "丙辰", "hour": "丁巳"},
            decadal_pillar="戊午",
            decadal_boundary=False,
        )
        vector = rank_evidence(evidence)
        self.assertTrue(vector.cross_layer_tier1)
        self.assertGreaterEqual(vector.tier1_family_count, 1)

    def test_selector_returns_true_top_four_and_bottom_one_deterministically(self):
        first = select_historical_activation(
            {
                "normalized_natal": NATAL,
                "as_of_datetime": "2026-08-23T10:27:00+08:00",
                "timezone": "Asia/Taipei",
            }
        )
        second = select_historical_activation(
            {
                "normalized_natal": NATAL,
                "as_of_datetime": "2026-08-23T10:27:00+08:00",
                "timezone": "Asia/Taipei",
            }
        )
        self.assertEqual(first, second)
        self.assertEqual(len(first["ranked_periods"]), 10)
        self.assertEqual(len(first["high_years"]), 4)
        self.assertNotIn(first["control_year"]["label_year"], [item["label_year"] for item in first["high_years"]])
        self.assertEqual(
            [item["label_year"] for item in first["high_years"]],
            [item["label_year"] for item in first["ranked_periods"][:4]],
        )
        self.assertEqual(first["control_year"]["label_year"], first["ranked_periods"][-1]["label_year"])
        self.assertEqual(len(first["selection_digest"]), 64)

    def test_selector_rejects_history_based_ranking_hints(self):
        for forbidden in ("preferred_years", "known_event_years", "event_keywords", "manual_rank_override"):
            payload = {
                "normalized_natal": NATAL,
                "as_of_datetime": "2026-08-23T10:27:00+08:00",
                "timezone": "Asia/Taipei",
                forbidden: [2020],
            }
            with self.subTest(forbidden=forbidden), self.assertRaises(ValueError):
                select_historical_activation(payload)

    def test_selection_digest_changes_when_natal_basis_changes(self):
        first = select_historical_activation(
            {"normalized_natal": NATAL, "as_of_datetime": "2026-08-23T10:27:00+08:00", "timezone": "Asia/Taipei"}
        )
        changed = copy.deepcopy(NATAL)
        changed["project"]["bazi"]["pillars"]["day"] = "丙寅"
        second = select_historical_activation(
            {"normalized_natal": changed, "as_of_datetime": "2026-08-23T10:27:00+08:00", "timezone": "Asia/Taipei"}
        )
        self.assertNotEqual(first["selection_digest"], second["selection_digest"])

    def test_control_quality_follows_bottom_rank_tiers(self):
        result = select_historical_activation(
            {"normalized_natal": NATAL, "as_of_datetime": "2026-08-23T10:27:00+08:00", "timezone": "Asia/Taipei"}
        )
        bottom = result["control_year"]["rank_vector"]
        if bottom["tier1_family_count"] > 0:
            self.assertEqual(result["control_quality"], "relative_low")
        elif bottom["tier2_family_count"] > 0:
            self.assertEqual(result["control_quality"], "acceptable_control")
        else:
            self.assertEqual(result["control_quality"], "strong_control")


if __name__ == "__main__":
    unittest.main()
