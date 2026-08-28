"""Compatibility exports for historical Bazi relation tables.

Canonical deterministic relation truth lives in ``engine.bazi.structural_relations``
so historical and prospective consumers cannot silently drift apart.
"""

from engine.bazi.structural_relations import (
    BREAK_PAIRS,
    CLASH_PAIRS,
    COMBINATION_PAIRS,
    FULL_PUNISHMENT_SETS,
    HARM_PAIRS,
    PAIR_PUNISHMENTS,
    SELF_PUNISHMENTS,
    STEM_COMBINATION_PAIRS,
    THREE_HARMONY_SETS,
    THREE_MEETING_SETS,
)


__all__ = (
    "BREAK_PAIRS",
    "CLASH_PAIRS",
    "COMBINATION_PAIRS",
    "FULL_PUNISHMENT_SETS",
    "HARM_PAIRS",
    "PAIR_PUNISHMENTS",
    "SELF_PUNISHMENTS",
    "STEM_COMBINATION_PAIRS",
    "THREE_HARMONY_SETS",
    "THREE_MEETING_SETS",
)
