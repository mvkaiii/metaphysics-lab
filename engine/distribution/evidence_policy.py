"""Versioned non-probabilistic evidence policy for 林氏天機 v1.5 Phase 3.

This module freezes ordinal policy constants only. It performs no I/O and
contains no claim probability semantics or ranking implementation.
"""

POLICY_VERSION = "lin_tianji_rank_v1-exp"

SPECIFICITY_LEVELS = (
    "domain",
    "event_family",
    "concrete_event",
    "highly_specific_event",
)

ROLE_CONTRIBUTION_ORDER = (
    "target_evidence",
    "modifier",
    "timing_trigger",
)

# Ordinal policy constants for deterministic ordering. These values are not
# probabilities and were not tuned against Kai 2026 outcomes.
TARGET_SCOPE_BASE = 4
INDEPENDENT_CONVERGENCE_BONUS = 2
MODIFIER_CAP = 1
TIMING_TRIGGER_CAP = 1
STABLE_FACTOR_NUM = 2
STABLE_FACTOR_DEN = 2
EXPERIMENTAL_FACTOR_NUM = 1
EXPERIMENTAL_FACTOR_DEN = 2
