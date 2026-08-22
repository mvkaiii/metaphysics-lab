import json
import tempfile
import unittest
from pathlib import Path

from tools.qualify_natal_phase2c0 import FORBIDDEN_KEYS, build_phase2c0_summary, find_forbidden_keys


class NatalPrivacyTests(unittest.TestCase):
    def test_forbidden_key_scanner_is_recursive_and_exact(self):
        self.assertEqual(
            FORBIDDEN_KEYS,
            frozenset((
                "name",
                "full_name",
                "full_address",
                "hospital",
                "birth_datetime",
                "raw_birth_input",
                "raw_chart",
                "raw_payload",
                "external_raw",
            )),
        )
        payload = {
            "safe": {"case_id": "public-1"},
            "nested": [{"raw_chart": {"stars": []}}, {"deeper": {"full_address": "secret"}}],
            "provider_name": "allowed-because-key-is-not-exactly-name",
        }
        self.assertEqual(
            find_forbidden_keys(payload),
            ("nested.0.raw_chart", "nested.1.deeper.full_address"),
        )

    def test_committed_phase_summary_contains_no_forbidden_keys(self):
        path = Path("qualification/natal/phase2c0-summary.json")
        summary = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(find_forbidden_keys(summary), ())

    def test_optional_private_summary_is_reduced_to_safe_aggregate_only(self):
        private_payload = {
            "status": "PASS",
            "case_count": 3,
            "match_count": 120,
            "conflict_count": 2,
            "promotion_allowed": False,
            "raw_chart": {"secret-star": "secret-palace"},
            "birth_datetime": "1984-03-13T19:20:00+08:00",
            "full_address": "PRIVATE STREET ADDRESS",
            "notes": "PRIVATE FREE TEXT",
        }
        with tempfile.TemporaryDirectory() as directory:
            private_path = Path(directory) / "private-astralium-local.json"
            private_path.write_text(json.dumps(private_payload, ensure_ascii=False), encoding="utf-8")
            summary = build_phase2c0_summary(private_summary_path=private_path)

        serialized = json.dumps(summary, ensure_ascii=False, sort_keys=True)
        self.assertNotIn(str(private_path), serialized)
        self.assertNotIn("PRIVATE STREET ADDRESS", serialized)
        self.assertNotIn("PRIVATE FREE TEXT", serialized)
        self.assertNotIn("secret-star", serialized)
        self.assertEqual(find_forbidden_keys(summary), ())

        private = summary["privacy"]["private_runtime_aggregate"]
        self.assertEqual(private["status"], "PASS")
        self.assertEqual(private["case_count"], 3)
        self.assertEqual(private["match_count"], 120)
        self.assertEqual(private["conflict_count"], 2)
        self.assertFalse(private["promotion_allowed"])
        self.assertRegex(private["source_digest"], r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(
            set(private),
            {
                "status",
                "case_count",
                "match_count",
                "conflict_count",
                "promotion_allowed",
                "source_digest",
            },
        )


if __name__ == "__main__":
    unittest.main()
