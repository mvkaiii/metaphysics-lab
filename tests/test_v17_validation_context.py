import unittest

from engine.distribution.errors import DistributionError
from engine.distribution import prospective


class ValidationContextClassifierTests(unittest.TestCase):
    @staticmethod
    def _payload(**overrides):
        payload = {
            "target_time_relation_to_cutoff": "future",
            "known_arrangement_before_lock": False,
            "claim_describes_known_fact": False,
            "claim_depends_on_known_arrangement": False,
            "outcome_known_before_lock": False,
        }
        payload.update(overrides)
        return payload

    def test_pv2_01_future_unknown_is_clean_prospective(self):
        result = prospective.classify_validation_context(self._payload())
        self.assertEqual(result["context_class"], "clean_prospective")
        self.assertTrue(result["clean_accuracy_eligible"])
        self.assertFalse(result["conditional_accuracy_eligible"])
        self.assertTrue(result["prospective_lock_eligible"])
        self.assertIsInstance(result["reason_code"], str)
        self.assertTrue(result["reason_code"])

    def test_pv2_02_known_future_arrangement_is_conditional(self):
        result = prospective.classify_validation_context(
            self._payload(
                known_arrangement_before_lock=True,
                claim_depends_on_known_arrangement=True,
            )
        )
        self.assertEqual(result["context_class"], "conditional_prospective")
        self.assertFalse(result["clean_accuracy_eligible"])
        self.assertTrue(result["conditional_accuracy_eligible"])
        self.assertTrue(result["prospective_lock_eligible"])

    def test_pv2_03_known_fact_is_hidden_existing_reality(self):
        result = prospective.classify_validation_context(
            self._payload(
                known_arrangement_before_lock=True,
                claim_describes_known_fact=True,
            )
        )
        self.assertEqual(result["context_class"], "hidden_existing_reality")
        self.assertFalse(result["clean_accuracy_eligible"])
        self.assertFalse(result["conditional_accuracy_eligible"])
        self.assertTrue(result["prospective_lock_eligible"])

    def test_pv2_04_past_or_present_is_retrospective_calibration(self):
        result = prospective.classify_validation_context(
            self._payload(target_time_relation_to_cutoff="past_or_present")
        )
        self.assertEqual(result["context_class"], "retrospective_calibration")
        self.assertFalse(result["clean_accuracy_eligible"])
        self.assertFalse(result["conditional_accuracy_eligible"])
        self.assertFalse(result["prospective_lock_eligible"])

    def test_dependent_claim_requires_known_arrangement(self):
        with self.assertRaises(DistributionError) as caught:
            prospective.classify_validation_context(
                self._payload(claim_depends_on_known_arrangement=True)
            )
        self.assertEqual(caught.exception.code, "invalid_validation_context")

    def test_known_fact_requires_known_arrangement_or_known_outcome(self):
        with self.assertRaises(DistributionError) as caught:
            prospective.classify_validation_context(
                self._payload(claim_describes_known_fact=True)
            )
        self.assertEqual(caught.exception.code, "invalid_validation_context")

    def test_unknown_time_relation_fails_closed(self):
        with self.assertRaises(DistributionError) as caught:
            prospective.classify_validation_context(
                self._payload(target_time_relation_to_cutoff="uncertain")
            )
        self.assertEqual(caught.exception.code, "invalid_validation_context")

    def test_non_boolean_epistemic_field_fails_closed(self):
        for field in (
            "known_arrangement_before_lock",
            "claim_describes_known_fact",
            "claim_depends_on_known_arrangement",
            "outcome_known_before_lock",
        ):
            with self.subTest(field=field):
                with self.assertRaises(DistributionError) as caught:
                    prospective.classify_validation_context(
                        self._payload(**{field: "false"})
                    )
                self.assertEqual(caught.exception.code, "invalid_validation_context")

    def test_unknown_or_missing_fields_fail_closed(self):
        with self.assertRaises(DistributionError) as caught:
            prospective.classify_validation_context(
                {**self._payload(), "extra": True}
            )
        self.assertEqual(caught.exception.code, "invalid_validation_context")

        missing = self._payload()
        missing.pop("outcome_known_before_lock")
        with self.assertRaises(DistributionError) as caught:
            prospective.classify_validation_context(missing)
        self.assertEqual(caught.exception.code, "invalid_validation_context")


if __name__ == "__main__":
    unittest.main()
