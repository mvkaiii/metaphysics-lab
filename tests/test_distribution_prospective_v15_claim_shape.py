import unittest

from engine.distribution.errors import DistributionError
from engine.distribution.prospective import METHOD_VERSION, lock_prospective_forecast, resolve_query_anchor


class V15ProspectiveClaimShapeTests(unittest.TestCase):
    def anchor(self):
        return resolve_query_anchor({
            "query_anchor_at": "2026-08-29T00:10:00+08:00",
            "query_timezone": "Asia/Taipei",
            "target_start": "2026-09-01T00:00:00+08:00",
            "target_end": "2026-12-31T23:59:59+08:00",
            "question_reference": "synthetic-v15-claim-contract",
        })

    def claim(self, claim_id, priority="primary"):
        anchor = self.anchor()
        return {
            "claim_id": claim_id,
            "priority": priority,
            "forecast_window": {
                "start": "2026-09-01T00:00:00+08:00",
                "end": "2026-09-30T23:59:59+08:00",
            },
            "primary_domain": "career",
            "event_family": "role_change",
            "prediction": "synthetic bounded event-family forecast",
            "matched_if": "formal responsibility or role changes inside the window",
            "partial_if": "responsibility changes materially but without formal title change",
            "not_matched_if": "no material responsibility or role change occurs inside the window",
            "evidence_layers": ["bazi"],
            "evidence_time_scales": ["yearly", "monthly"],
            "capability_maturity": "stable",
            "confidence": "medium",
            "knowledge_cutoff_at": anchor["knowledge_cutoff_at"],
            "evaluation_eligibility": "clean_scorable",
            "contamination_state": "clean_prospective",
            "method_version": METHOD_VERSION,
        }

    def test_lock_preserves_priority_and_partial_boundary(self):
        anchor = self.anchor()
        locked = lock_prospective_forecast({"anchor": anchor, "claims": [self.claim("C1")]})
        claim = locked["claims"][0]
        self.assertEqual(claim["priority"], "primary")
        self.assertIn("without formal title change", claim["partial_if"])

    def test_priority_and_partial_if_are_required_and_fail_closed(self):
        anchor = self.anchor()
        for missing in ("priority", "partial_if"):
            claim = self.claim("C1")
            claim.pop(missing)
            with self.assertRaises(DistributionError):
                lock_prospective_forecast({"anchor": anchor, "claims": [claim]})

    def test_locked_claim_volume_is_bounded_to_three_primary_two_secondary(self):
        anchor = self.anchor()
        allowed = [self.claim("P%d" % index) for index in range(1, 4)] + [
            self.claim("S%d" % index, priority="secondary") for index in range(1, 3)
        ]
        locked = lock_prospective_forecast({"anchor": anchor, "claims": allowed})
        self.assertEqual(len(locked["claims"]), 5)

        too_many_primary = allowed + [self.claim("P4")]
        with self.assertRaises(DistributionError):
            lock_prospective_forecast({"anchor": anchor, "claims": too_many_primary})

        too_many_secondary = allowed + [self.claim("S3", priority="secondary")]
        with self.assertRaises(DistributionError):
            lock_prospective_forecast({"anchor": anchor, "claims": too_many_secondary})

    def test_unsupported_priority_is_rejected(self):
        anchor = self.anchor()
        claim = self.claim("C1", priority="tertiary")
        with self.assertRaises(DistributionError):
            lock_prospective_forecast({"anchor": anchor, "claims": [claim]})


if __name__ == "__main__":
    unittest.main()
