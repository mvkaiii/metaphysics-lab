import unittest

from engine.distribution.historical_personalization_policy import (
    BASE_RANKING_POLICY_VERSION,
    PERSONALIZATION_PROFILE_VERSION,
    bounded_modifier,
    evidence_unit,
    normalize_domain_id,
    normalize_event_family_id,
    support_class,
)


class HistoricalPersonalizationPolicyTests(unittest.TestCase):
    def test_profile_and_base_policy_ids_are_locked(self):
        self.assertEqual(
            PERSONALIZATION_PROFILE_VERSION,
            "lin_tianji_historical_personalization_v1-exp",
        )
        self.assertEqual(BASE_RANKING_POLICY_VERSION, "lin_tianji_rank_v1-exp")

    def test_evidence_units_are_ordinal_not_probabilities(self):
        self.assertEqual(evidence_unit("matched"), 2)
        self.assertEqual(evidence_unit("partial"), 1)
        self.assertEqual(evidence_unit("missed"), -2)
        self.assertIsNone(evidence_unit("unscorable"))

    def test_evidence_unit_rejects_unknown_status(self):
        with self.assertRaises(ValueError):
            evidence_unit("likely")

    def test_modifier_threshold_and_caps_are_locked(self):
        self.assertEqual(bounded_modifier(100, 1), 0)
        self.assertEqual(bounded_modifier(100, 2), 2)
        self.assertEqual(bounded_modifier(-100, 2), -2)
        self.assertEqual(bounded_modifier(2, 2), 1)
        self.assertEqual(bounded_modifier(-2, 2), -1)
        self.assertEqual(bounded_modifier(0, 2), 0)

    def test_support_class_is_non_probability_language(self):
        self.assertEqual(support_class(0, 1), "insufficient")
        self.assertEqual(support_class(-2, 2), "contradicted")
        self.assertEqual(support_class(-1, 2), "mixed")
        self.assertEqual(support_class(0, 2), "mixed")
        self.assertEqual(support_class(1, 2), "supported")
        self.assertEqual(support_class(2, 2), "strongly_supported")

    def test_domain_legacy_alias_is_closed_and_exact(self):
        self.assertEqual(normalize_domain_id("career"), "career")
        self.assertEqual(normalize_domain_id("工作／職責"), "career")
        self.assertIsNone(normalize_domain_id("工作 職責"))
        self.assertIsNone(normalize_domain_id("職涯"))
        self.assertIsNone(normalize_domain_id(None))

    def test_legacy_event_family_is_not_semantically_guessed(self):
        self.assertEqual(normalize_event_family_id("role_change"), "role_change")
        self.assertEqual(normalize_event_family_id("responsibility"), "responsibility")
        self.assertIsNone(normalize_event_family_id("職務或責任結構改變"))
        self.assertIsNone(normalize_event_family_id("工作改變"))
        self.assertIsNone(normalize_event_family_id(None))


if __name__ == "__main__":
    unittest.main()
