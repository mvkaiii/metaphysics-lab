import unittest

from engine.distribution.runtime import dispatch


IDENTITY = {
    "subject_id": "subj_7f3a2c91d4e8",
    "subject_display_name": "Kai",
    "subject_short_id": "7F3A2C",
    "filename_label": "Kai",
}

ENVELOPE = {
    "profile_id": "natal-candidate-envelope-v1",
    "rule_version": "1.0-exp",
    "natal_precision_state": "unknown_time",
    "candidate_time_basis": "material_timing_state",
    "candidate_count": 2,
    "known_facts": {
        "sex": "male",
        "birth_date": "1984-03-13",
        "birth_place": "台北市",
        "resolved_place_label": "Taipei City, Taiwan",
        "timezone": "Asia/Taipei",
        "reported_birth_time": None,
        "reported_birth_time_range": None,
    },
    "invariant_bazi_facts": {"day_master": "丙", "pillars": {"year": "甲子", "month": "丁卯", "day": "丙辰"}},
    "variant_bazi_facts": {"pillars": {"hour": {"candidate-01": "甲子", "candidate-02": "乙丑"}}},
    "invariant_ziwei_facts": {"life_master": "祿存"},
    "variant_ziwei_facts": {"ming_palace": {"candidate-01": "辰", "candidate-02": "巳"}},
    "candidates": [
        {"candidate_id": "candidate-01", "reported_time_start": "00:00", "reported_time_end": "00:59", "bazi": {"pillars": {"hour": "甲子"}}, "ziwei": {"ming_palace": "辰"}},
        {"candidate_id": "candidate-02", "reported_time_start": "01:00", "reported_time_end": "02:59", "bazi": {"pillars": {"hour": "乙丑"}}, "ziwei": {"ming_palace": "巳"}},
    ],
    "boundary_ambiguities": [],
    "allowed_analysis": ["invariant_natal_structure", "candidate_comparison"],
    "blocked_analysis": [
        "unique_birth_time_claim",
        "unique_hour_pillar_conclusion",
        "unique_ziwei_natal_conclusion",
        "single_chart_personalized_forecast",
    ],
    "provenance": {"classification": "Project 原生盤面候選集合", "midpoint_used": False, "default_time_used": False},
}


class PartialCaseTests(unittest.TestCase):
    def export(self, **extra):
        payload = {
            "candidate_envelope": ENVELOPE,
            **IDENTITY,
            "generated_at": "2026-08-23T00:00:00+08:00",
            "last_modified_by": "ai",
        }
        payload.update(extra)
        return dispatch("export_case_markdown", payload)

    def test_unknown_time_envelope_exports_subject_aware_base_case(self):
        result = self.export()
        self.assertTrue(result["ok"], result)
        files = result["data"]["files"]
        self.assertEqual(len(files), 5)
        self.assertIn("Kai_7F3A2C_00_專案索引.md", files)
        index = files["Kai_7F3A2C_00_專案索引.md"]
        self.assertIn("Natal Status: `partial`", index)
        self.assertIn("Birth Time Status: `unknown_time`", index)
        self.assertIn("Candidate Count: `2`", index)
        core = files["Kai_7F3A2C_01_命盤核心摘要.md"]
        self.assertIn("【已確定盤面】", core)
        self.assertIn("【候選依賴盤面】", core)
        self.assertIn("【目前不可唯一判定】", core)
        bazi = files["Kai_7F3A2C_03_八字結構化資料包.md"]
        self.assertIn("Invariant Facts", bazi)
        self.assertIn("Candidate-dependent Facts", bazi)
        ziwei = files["Kai_7F3A2C_04_紫微基礎資料包.md"]
        self.assertIn("Invariant Across Candidates", ziwei)
        self.assertIn("Candidate Summaries", ziwei)
        validation = dispatch("validate_case", {"case_files": files})
        self.assertTrue(validation["ok"], validation)

    def test_export_rejects_both_full_natal_and_candidate_envelope(self):
        result = self.export(normalized_natal={"project": {}})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "ambiguous_case_natal_source")

    def test_partial_case_keeps_unique_chart_forecast_blocked(self):
        files = self.export()["data"]["files"]
        self.assertIn("single_chart_personalized_forecast", files["Kai_7F3A2C_00_專案索引.md"])

    def test_partial_case_rejects_envelope_that_omits_mandatory_unique_chart_blocks(self):
        tampered = dict(ENVELOPE)
        tampered["blocked_analysis"] = []
        result = self.export(candidate_envelope=tampered)
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "invalid_candidate_envelope")


if __name__ == "__main__":
    unittest.main()
