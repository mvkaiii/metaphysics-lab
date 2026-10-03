import copy
import json
import unittest

from engine.distribution.runtime import dispatch


LOCATION = {
    "canonical_name": "Taipei City, Taiwan",
    "latitude": 25.033,
    "longitude": 121.5654,
    "timezone": "Asia/Taipei",
    "provider_name": "fixture",
    "provider_version": "v1",
    "provider_reference": "fixture:taipei",
}

BOUNDED_BIRTH = {
    "sex": "male",
    "birth_date": "1984-03-13",
    "birth_time_precision": "bounded",
    "birth_time_range": ["19:20", "19:21"],
    "birth_place": "台北市",
}


class V19VisualizationP1CandidateEnvelopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        result = dispatch(
            "natal.candidate_envelope",
            {"birth": BOUNDED_BIRTH, "resolved_location": LOCATION},
        )
        if not result.get("ok"):
            raise AssertionError(result)
        cls.envelope = result["data"]["candidate_envelope"]

    def render(self, envelope=None, **extra):
        payload = {"candidate_envelope": copy.deepcopy(envelope or self.envelope)}
        payload.update(extra)
        return dispatch("render_candidate_envelope_summary", payload)

    def test_public_action_and_capability_are_experimental_on_demand(self):
        info = dispatch("runtime_info", {})
        self.assertTrue(info["ok"], info)
        data = info["data"]
        self.assertIn("render_candidate_envelope_summary", data["supported_actions"])
        cap = data["capabilities"]["distribution.candidate_envelope_visualization"]
        self.assertEqual(cap["implementation"], "implemented")
        self.assertEqual(cap["maturity"], "experimental")
        self.assertEqual(cap["routing"], "on_demand")
        self.assertEqual(cap["rule_version"], "1.0-exp")
        self.assertEqual(cap["dependencies"], ["natal.candidate_envelope"])
        self.assertFalse(cap["ranking_authority"])

    def test_v2_envelope_returns_deterministic_svg_text_and_structured_summary(self):
        first = self.render()
        second = self.render()
        self.assertTrue(first["ok"], first)
        self.assertEqual(first, second)

        data = first["data"]
        chart = data["chart"]
        self.assertEqual(chart["chart_type"], "candidate_envelope_summary")
        self.assertEqual(chart["schema_version"], "1.0")
        self.assertEqual(chart["status"], "ready")
        self.assertEqual(chart["source_profile_id"], "natal-candidate-envelope-v2")
        self.assertEqual(chart["source_rule_version"], "2.0-exp")
        self.assertEqual(chart["natal_precision_state"], "bounded")
        self.assertEqual(chart["coverage"]["status"], "complete")
        self.assertEqual(
            chart["coverage"]["material_state_count"],
            self.envelope["candidate_count"],
        )
        self.assertEqual(
            chart["coverage"]["legal_occurrence_count"],
            self.envelope["candidate_coverage"]["legal_occurrence_count"],
        )
        self.assertEqual(len(chart["candidate_spans"]), self.envelope["candidate_count"])
        self.assertIn("<svg", data["svg"])
        self.assertIn("Candidate Envelope", data["svg"])
        self.assertIn("候選盤", data["text"])

        serialized = json.dumps(data, ensure_ascii=False, sort_keys=True)
        self.assertNotIn('"probability"', serialized.lower())
        self.assertNotIn('"ranking"', serialized.lower())
        self.assertNotIn('"selected_candidate"', serialized.lower())

        presentation = data["presentation"]
        self.assertEqual(presentation["surface"], "experimental")
        self.assertFalse(presentation["ranking_authority"])
        self.assertFalse(presentation["predictive_evidence"])
        self.assertFalse(presentation["candidate_selection_authority"])

    def test_summary_preserves_chronological_candidate_spans_without_ranking(self):
        result = self.render()
        self.assertTrue(result["ok"], result)
        spans = result["data"]["chart"]["candidate_spans"]
        expected = [
            (
                row["candidate_id"],
                row["reported_time_start"],
                row["reported_time_end"],
            )
            for row in self.envelope["candidates"]
        ]
        actual = [
            (row["candidate_id"], row["reported_time_start"], row["reported_time_end"])
            for row in spans
        ]
        self.assertEqual(actual, expected)
        self.assertTrue(all("rank" not in row for row in spans))
        self.assertTrue(all("score" not in row for row in spans))
        self.assertTrue(all("probability" not in row for row in spans))

    def test_fact_summary_keeps_invariant_variant_and_undetermined_separate(self):
        envelope = copy.deepcopy(self.envelope)
        envelope["candidate_coverage"]["status"] = "partial"
        envelope["candidate_coverage"]["materialized_occurrence_count"] = max(
            0, envelope["candidate_coverage"]["legal_occurrence_count"] - 1
        )
        envelope["candidate_coverage"]["unresolved_occurrence_count"] = 1
        envelope["undetermined_bazi_facts"] = {"day_master": "丙"}
        envelope["invariant_bazi_facts"] = {}
        envelope["undetermined_ziwei_facts"] = copy.deepcopy(
            envelope["invariant_ziwei_facts"]
        )
        envelope["invariant_ziwei_facts"] = {}

        result = self.render(envelope)
        self.assertTrue(result["ok"], result)
        chart = result["data"]["chart"]
        self.assertEqual(chart["coverage"]["status"], "partial")
        self.assertIn("PARTIAL_CANDIDATE_COVERAGE", chart["reason_codes"])
        self.assertEqual(chart["fact_counts"]["invariant"]["bazi"], 0)
        self.assertGreater(chart["fact_counts"]["undetermined"]["bazi"], 0)
        self.assertNotEqual(
            chart["fact_counts"]["undetermined"]["bazi"],
            chart["fact_counts"]["invariant"]["bazi"],
        )

    def test_coverage_semantics_fail_closed_before_presentation(self):
        complete_with_unresolved = copy.deepcopy(self.envelope)
        legal = complete_with_unresolved["candidate_coverage"]["legal_occurrence_count"]
        complete_with_unresolved["candidate_coverage"]["materialized_occurrence_count"] = legal - 1
        complete_with_unresolved["candidate_coverage"]["unresolved_occurrence_count"] = 1
        result = self.render(complete_with_unresolved)
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error"]["code"], "invalid_candidate_visualization_source")

        partial_with_invariant = copy.deepcopy(self.envelope)
        partial_with_invariant["candidate_coverage"]["status"] = "partial"
        partial_with_invariant["candidate_coverage"]["materialized_occurrence_count"] = legal - 1
        partial_with_invariant["candidate_coverage"]["unresolved_occurrence_count"] = 1
        partial_with_invariant["invariant_bazi_facts"] = {"day_master": "丙"}
        result = self.render(partial_with_invariant)
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error"]["code"], "invalid_candidate_visualization_source")

    def test_v1_candidate_envelope_is_not_silently_upgraded(self):
        envelope = copy.deepcopy(self.envelope)
        envelope["profile_id"] = "natal-candidate-envelope-v1"
        envelope["rule_version"] = "1.0-exp"
        result = self.render(envelope)
        self.assertFalse(result["ok"], result)
        self.assertEqual(
            result["error"]["code"],
            "visualization_candidate_envelope_v2_required",
        )

    def test_candidate_count_mismatch_fails_closed(self):
        envelope = copy.deepcopy(self.envelope)
        envelope["candidate_count"] += 1
        result = self.render(envelope)
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error"]["code"], "invalid_candidate_visualization_source")

    def test_unknown_or_reality_context_fields_are_rejected(self):
        result = self.render(
            current_real_world_context={"job": "known"},
            verified_events=[{"year": 2020}],
        )
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error"]["code"], "invalid_visualization_payload")
        self.assertEqual(
            result["error"]["details"]["unknown_fields"],
            ["current_real_world_context", "verified_events"],
        )

    def test_candidate_time_labels_are_validated_before_svg_render(self):
        envelope = copy.deepcopy(self.envelope)
        envelope["candidates"][0]["reported_time_start"] = '<script>alert("x")</script>'
        result = self.render(envelope)
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error"]["code"], "invalid_candidate_visualization_source")

    def test_source_digest_changes_when_envelope_changes_without_mutating_source(self):
        original = copy.deepcopy(self.envelope)
        first = self.render(original)
        self.assertTrue(first["ok"], first)

        changed = copy.deepcopy(original)
        changed["blocked_analysis"] = list(changed["blocked_analysis"]) + ["fixture_block"]
        second = self.render(changed)
        self.assertTrue(second["ok"], second)
        self.assertNotEqual(
            first["data"]["chart"]["provenance"]["source_envelope_sha256"],
            second["data"]["chart"]["provenance"]["source_envelope_sha256"],
        )
        self.assertEqual(original, self.envelope)


if __name__ == "__main__":
    unittest.main()
