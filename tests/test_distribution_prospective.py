import importlib
import importlib.util
import unittest
from datetime import datetime, timedelta

from engine.distribution.errors import DistributionError


class DistributionProspectiveQueryAnchorTests(unittest.TestCase):
    def _prospective(self):
        spec = importlib.util.find_spec("engine.distribution.prospective")
        self.assertIsNotNone(
            spec,
            "Phase 1 requires engine.distribution.prospective before Query Anchor can resolve",
        )
        return importlib.import_module("engine.distribution.prospective")

    @staticmethod
    def _payload(**overrides):
        payload = {
            "query_anchor_at": "2026-08-26T17:00:00+08:00",
            "query_timezone": "Asia/Taipei",
            "target_start": "2026-08-01T00:00:00+08:00",
            "target_end": "2026-12-31T23:59:59+08:00",
            "question_reference": "kai-2026-second-half",
        }
        payload.update(overrides)
        return payload

    def test_anchor_inside_target_truncates_window_to_immediately_after_cutoff(self):
        prospective = self._prospective()
        result = prospective.resolve_query_anchor(self._payload())

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["query_anchor_at"], "2026-08-26T17:00:00+08:00")
        self.assertEqual(result["query_timezone"], "Asia/Taipei")
        self.assertEqual(result["knowledge_cutoff_at"], result["query_anchor_at"])
        self.assertEqual(result["question_reference"], "kai-2026-second-half")
        self.assertEqual(
            datetime.fromisoformat(result["prospective_window_start"]),
            datetime.fromisoformat(result["knowledge_cutoff_at"]) + timedelta(microseconds=1),
        )
        self.assertEqual(
            result["prospective_window_end"],
            "2026-12-31T23:59:59+08:00",
        )

    def test_anchor_before_target_preserves_full_target_window(self):
        prospective = self._prospective()
        result = prospective.resolve_query_anchor(
            self._payload(
                query_anchor_at="2026-07-15T09:30:00+08:00",
                target_start="2026-08-01T00:00:00+08:00",
            )
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["prospective_window_start"], "2026-08-01T00:00:00+08:00")
        self.assertEqual(result["prospective_window_end"], "2026-12-31T23:59:59+08:00")

    def test_anchor_at_or_after_target_end_has_no_prospective_window(self):
        prospective = self._prospective()
        for anchor in (
            "2026-12-31T23:59:59+08:00",
            "2027-01-01T00:00:00+08:00",
        ):
            with self.subTest(anchor=anchor):
                result = prospective.resolve_query_anchor(self._payload(query_anchor_at=anchor))
                self.assertEqual(result["status"], "no_prospective_window")
                self.assertIsNone(result["prospective_window_start"])
                self.assertIsNone(result["prospective_window_end"])
                self.assertEqual(result["knowledge_cutoff_at"], anchor)

    def test_query_anchor_rejects_naive_datetimes_instead_of_guessing_timezone(self):
        prospective = self._prospective()
        for field in ("query_anchor_at", "target_start", "target_end"):
            with self.subTest(field=field):
                payload = self._payload()
                payload[field] = payload[field].split("+")[0]
                with self.assertRaises(DistributionError) as caught:
                    prospective.resolve_query_anchor(payload)
                self.assertEqual(caught.exception.code, "invalid_query_anchor")

    def test_query_anchor_rejects_offset_that_does_not_match_declared_timezone(self):
        prospective = self._prospective()
        for field in ("query_anchor_at", "target_start", "target_end"):
            with self.subTest(field=field):
                payload = self._payload()
                payload[field] = "2026-08-26T17:00:00+00:00"
                with self.assertRaises(DistributionError) as caught:
                    prospective.resolve_query_anchor(payload)
                self.assertEqual(caught.exception.code, "invalid_query_anchor")

    def test_query_anchor_rejects_invalid_range_or_blank_reference(self):
        prospective = self._prospective()
        invalid_payloads = (
            self._payload(
                target_start="2026-12-31T23:59:59+08:00",
                target_end="2026-08-01T00:00:00+08:00",
            ),
            self._payload(question_reference="   "),
        )
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                with self.assertRaises(DistributionError) as caught:
                    prospective.resolve_query_anchor(payload)
                self.assertEqual(caught.exception.code, "invalid_query_anchor")

    def test_query_anchor_does_not_accept_activation_or_change_metaphysical_strength(self):
        prospective = self._prospective()
        payload = self._payload(activation="high")
        with self.assertRaises(DistributionError) as caught:
            prospective.resolve_query_anchor(payload)
        self.assertEqual(caught.exception.code, "invalid_query_anchor")


if __name__ == "__main__":
    unittest.main()
