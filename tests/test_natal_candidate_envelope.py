import unittest
from datetime import time

from engine.natal.candidates import classify_candidate_facts, partition_material_states


class NatalCandidateEnvelopeCoreTests(unittest.TestCase):
    def test_partition_groups_contiguous_minutes_with_same_discrete_chart(self):
        minute_rows = [
            {"minute": 60, "signature": "A", "bazi": {"pillars": {"hour": "甲子"}}, "ziwei": {"ming_palace": "命A"}, "decadal_start": "2000-01-01T00:00:00+08:00"},
            {"minute": 61, "signature": "A", "bazi": {"pillars": {"hour": "甲子"}}, "ziwei": {"ming_palace": "命A"}, "decadal_start": "2000-01-01T00:01:00+08:00"},
            {"minute": 62, "signature": "B", "bazi": {"pillars": {"hour": "乙丑"}}, "ziwei": {"ming_palace": "命B"}, "decadal_start": "2000-01-01T00:02:00+08:00"},
        ]
        states = partition_material_states(minute_rows)
        self.assertEqual(len(states), 2)
        self.assertEqual(states[0]["reported_time_start"], "01:00")
        self.assertEqual(states[0]["reported_time_end"], "01:01")
        self.assertEqual(states[0]["bazi_decadal_start_range"][0], "2000-01-01T00:00:00+08:00")
        self.assertEqual(states[0]["bazi_decadal_start_range"][1], "2000-01-01T00:01:00+08:00")

    def test_invariant_requires_all_candidates_to_match(self):
        candidates = [
            {"candidate_id": "c1", "bazi": {"day_master": "丙", "pillars": {"day": "丙辰", "hour": "甲子"}}, "ziwei": {"life_master": "祿存", "ming_palace": "辰"}},
            {"candidate_id": "c2", "bazi": {"day_master": "丙", "pillars": {"day": "丙辰", "hour": "乙丑"}}, "ziwei": {"life_master": "祿存", "ming_palace": "巳"}},
        ]
        result = classify_candidate_facts(candidates)
        self.assertEqual(result["invariant_bazi_facts"]["day_master"], "丙")
        self.assertIn("pillars", result["variant_bazi_facts"])
        self.assertEqual(result["invariant_ziwei_facts"]["life_master"], "祿存")
        self.assertIn("ming_palace", result["variant_ziwei_facts"])

    def test_no_majority_rule_promotes_variant(self):
        candidates = [
            {"candidate_id": "c1", "bazi": {"x": 1}, "ziwei": {}},
            {"candidate_id": "c2", "bazi": {"x": 1}, "ziwei": {}},
            {"candidate_id": "c3", "bazi": {"x": 2}, "ziwei": {}},
        ]
        result = classify_candidate_facts(candidates)
        self.assertNotIn("x", result["invariant_bazi_facts"])
        self.assertEqual(result["variant_bazi_facts"]["x"], {"c1": 1, "c2": 1, "c3": 2})


if __name__ == "__main__":
    unittest.main()
