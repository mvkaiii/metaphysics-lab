import unittest

from engine.distribution.evidence_policy import (
    EXPERIMENTAL_FACTOR_DEN,
    EXPERIMENTAL_FACTOR_NUM,
    INDEPENDENT_CONVERGENCE_BONUS,
    MODIFIER_CAP,
    POLICY_VERSION,
    ROLE_CONTRIBUTION_ORDER,
    SPECIFICITY_LEVELS,
    STABLE_FACTOR_DEN,
    STABLE_FACTOR_NUM,
    TARGET_SCOPE_BASE,
    TIMING_TRIGGER_CAP,
)


class EvidencePolicyProfileTests(unittest.TestCase):
    def test_policy_version_and_specificity_levels_are_frozen(self):
        self.assertEqual(POLICY_VERSION, "lin_tianji_rank_v1-exp")
        self.assertEqual(
            SPECIFICITY_LEVELS,
            ("domain", "event_family", "concrete_event", "highly_specific_event"),
        )
        self.assertEqual(
            ROLE_CONTRIBUTION_ORDER,
            ("target_evidence", "modifier", "timing_trigger"),
        )

    def test_initial_ordinal_policy_constants_match_approved_profile(self):
        self.assertEqual(TARGET_SCOPE_BASE, 4)
        self.assertEqual(INDEPENDENT_CONVERGENCE_BONUS, 2)
        self.assertEqual(MODIFIER_CAP, 1)
        self.assertEqual(TIMING_TRIGGER_CAP, 1)
        self.assertEqual((STABLE_FACTOR_NUM, STABLE_FACTOR_DEN), (2, 2))
        self.assertEqual((EXPERIMENTAL_FACTOR_NUM, EXPERIMENTAL_FACTOR_DEN), (1, 2))

    def test_policy_profile_contains_no_probability_semantics(self):
        exported_names = {
            name.lower()
            for name in (
                "POLICY_VERSION",
                "SPECIFICITY_LEVELS",
                "ROLE_CONTRIBUTION_ORDER",
                "TARGET_SCOPE_BASE",
                "INDEPENDENT_CONVERGENCE_BONUS",
                "MODIFIER_CAP",
                "TIMING_TRIGGER_CAP",
                "STABLE_FACTOR_NUM",
                "STABLE_FACTOR_DEN",
                "EXPERIMENTAL_FACTOR_NUM",
                "EXPERIMENTAL_FACTOR_DEN",
            )
        }
        for forbidden in ("probability", "likelihood", "chance", "percent"):
            self.assertFalse(any(forbidden in name for name in exported_names))


if __name__ == "__main__":
    unittest.main()
