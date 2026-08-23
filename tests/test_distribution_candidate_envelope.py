import unittest
from unittest import mock

from engine.distribution.runtime import dispatch


LOCATION = {
    "canonical_name": "Taipei City, Taiwan",
    "latitude": 25.033,
    "longitude": 121.5654,
    "timezone": "Asia/Taipei",
    "provider_name": "ai_host",
    "provider_version": "user-confirmed",
    "provider_reference": None,
}


class DistributionCandidateEnvelopeTests(unittest.TestCase):
    def test_bounded_range_builds_candidate_envelope_without_midpoint(self):
        result = dispatch(
            "natal.candidate_envelope",
            {
                "birth": {
                    "sex": "male",
                    "birth_date": "1984-03-13",
                    "birth_time_range": ["18:55", "19:05"],
                    "birth_place": "台北市",
                },
                "resolved_location": LOCATION,
            },
        )
        self.assertTrue(result["ok"], result)
        envelope = result["data"]["candidate_envelope"]
        self.assertEqual(envelope["natal_precision_state"], "bounded")
        self.assertFalse(envelope["provenance"]["midpoint_used"])
        self.assertFalse(envelope["provenance"]["default_time_used"])
        self.assertGreaterEqual(envelope["candidate_count"], 1)

    def test_unknown_time_bypasses_full_natal_precision_gate(self):
        fake = {
            "profile_id": "natal-candidate-envelope-v1",
            "rule_version": "1.0-exp",
            "natal_precision_state": "unknown_time",
            "candidate_count": 12,
        }
        with mock.patch("engine.distribution.natal.build_candidate_envelope", return_value=fake) as builder:
            result = dispatch(
                "natal.candidate_envelope",
                {
                    "birth": {"sex": "female", "birth_date": "1990-01-01", "birth_place": "台北市"},
                    "resolved_location": LOCATION,
                },
            )
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["data"]["candidate_envelope"]["natal_precision_state"], "unknown_time")
        builder.assert_called_once()

    def test_missing_location_basis_fails_closed(self):
        result = dispatch(
            "natal.candidate_envelope",
            {"birth": {"sex": "male", "birth_date": "1984-03-13", "birth_place": "台北市"}},
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "missing_candidate_location_basis")


if __name__ == "__main__":
    unittest.main()
