import hashlib
import importlib
import importlib.util
import json
import unittest

from engine.distribution.errors import DistributionError


class DistributionProspectiveWindowScopeTests(unittest.TestCase):
    def _module(self):
        spec = importlib.util.find_spec("engine.distribution.prospective_window_scope")
        self.assertIsNotNone(
            spec,
            "prospective window scope governance requires engine.distribution.prospective_window_scope",
        )
        return importlib.import_module("engine.distribution.prospective_window_scope")

    @staticmethod
    def _q4(**overrides):
        payload = {
            "window_start": "2026-10-01T00:00:00+08:00",
            "window_end": "2026-12-31T23:59:59+08:00",
            "timezone": "Asia/Taipei",
        }
        payload.update(overrides)
        return payload

    @staticmethod
    def _h2(**overrides):
        payload = {
            "window_start": "2027-07-01T00:00:00+08:00",
            "window_end": "2027-12-31T23:59:59+08:00",
            "timezone": "Asia/Taipei",
        }
        payload.update(overrides)
        return payload

    def test_q4_resolves_to_yearly_authority_with_monthly_timing(self):
        module = self._module()
        result = module.resolve_prospective_window_scope(self._q4())

        self.assertEqual(result["schema_version"], "v1.6-prospective-window-scope-policy.v1")
        self.assertEqual(result["policy_profile"], "lin_tianji_prospective_window_scope_v1")
        self.assertEqual(result["window_class"], "calendar_aligned_same_year_multi_month")
        self.assertEqual(result["window_start"], "2026-10-01T00:00:00+08:00")
        self.assertEqual(result["window_end"], "2026-12-31T23:59:59+08:00")
        self.assertEqual(result["timezone"], "Asia/Taipei")
        self.assertEqual(result["claim_target_scope"], "yearly")
        self.assertEqual(result["timing_scopes"], ["monthly"])
        self.assertEqual(result["child_opening_scope"], "yearly")
        self.assertIs(result["promotion_allowed"], False)

    def test_h2_uses_the_same_structural_scope_contract(self):
        module = self._module()
        result = module.resolve_prospective_window_scope(self._h2())

        self.assertEqual(result["window_class"], "calendar_aligned_same_year_multi_month")
        self.assertEqual(result["claim_target_scope"], "yearly")
        self.assertEqual(result["timing_scopes"], ["monthly"])
        self.assertEqual(result["child_opening_scope"], "yearly")

    def test_cross_year_window_fails_closed(self):
        module = self._module()
        with self.assertRaises(DistributionError) as caught:
            module.resolve_prospective_window_scope(
                self._q4(window_end="2027-01-31T23:59:59+08:00")
            )
        self.assertEqual(caught.exception.code, "invalid_prospective_window_scope")

    def test_single_month_window_fails_closed(self):
        module = self._module()
        with self.assertRaises(DistributionError) as caught:
            module.resolve_prospective_window_scope(
                self._q4(
                    window_start="2026-10-01T09:00:00+08:00",
                    window_end="2026-10-31T18:00:00+08:00",
                )
            )
        self.assertEqual(caught.exception.code, "invalid_prospective_window_scope")

    def test_partial_cross_month_window_fails_closed(self):
        module = self._module()
        invalid = (
            self._q4(window_start="2026-10-02T00:00:00+08:00"),
            self._q4(window_end="2026-12-30T23:59:59+08:00"),
        )
        for payload in invalid:
            with self.subTest(payload=payload):
                with self.assertRaises(DistributionError) as caught:
                    module.resolve_prospective_window_scope(payload)
                self.assertEqual(caught.exception.code, "invalid_prospective_window_scope")

    def test_non_positive_range_fails_closed(self):
        module = self._module()
        with self.assertRaises(DistributionError) as caught:
            module.resolve_prospective_window_scope(
                self._q4(
                    window_start="2026-12-31T23:59:59+08:00",
                    window_end="2026-10-01T00:00:00+08:00",
                )
            )
        self.assertEqual(caught.exception.code, "invalid_prospective_window_scope")

    def test_invalid_timezone_fails_closed(self):
        module = self._module()
        with self.assertRaises(DistributionError) as caught:
            module.resolve_prospective_window_scope(self._q4(timezone="Mars/Olympus"))
        self.assertEqual(caught.exception.code, "invalid_prospective_window_scope")

    def test_offset_must_match_declared_timezone(self):
        module = self._module()
        for field in ("window_start", "window_end"):
            with self.subTest(field=field):
                payload = self._q4()
                payload[field] = payload[field].replace("+08:00", "+00:00")
                with self.assertRaises(DistributionError) as caught:
                    module.resolve_prospective_window_scope(payload)
                self.assertEqual(caught.exception.code, "invalid_prospective_window_scope")

    def test_unknown_and_outcome_like_fields_are_rejected(self):
        module = self._module()
        for key, value in (
            ("outcome", "supported"),
            ("verified_event", "known"),
            ("oracle", {}),
            ("candidate_output", {}),
            ("legacy_output", {}),
            ("q1_result", {}),
            ("t1_result", {}),
        ):
            with self.subTest(key=key):
                with self.assertRaises(DistributionError) as caught:
                    module.resolve_prospective_window_scope(self._q4(**{key: value}))
                self.assertEqual(caught.exception.code, "invalid_prospective_window_scope")

    def test_repeated_normalized_input_is_byte_deterministic_and_digest_valid(self):
        module = self._module()
        first = module.resolve_prospective_window_scope(self._q4())
        second = module.resolve_prospective_window_scope(self._q4())

        first_bytes = json.dumps(
            first,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        second_bytes = json.dumps(
            second,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        self.assertEqual(first_bytes, second_bytes)

        body = dict(first)
        supplied = body.pop("policy_digest")
        expected = hashlib.sha256(
            json.dumps(
                body,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
        ).hexdigest()
        self.assertEqual(supplied, expected)


if __name__ == "__main__":
    unittest.main()
