"""Closed deterministic policy for Phase 4 historical personalization."""

from __future__ import annotations

from typing import Optional

from .structural_policy import (
    BAZI_TEN_GOD_MAPPING,
    FLOWING_STAR_CATEGORY_FAMILY,
    RELATION_EVENT_FAMILY,
    TRANSFORMATION_FAMILY,
    ZIWEI_PALACE_MAPPING,
)


PERSONALIZATION_PROFILE_VERSION = "lin_tianji_historical_personalization_v1-exp"
BASE_RANKING_POLICY_VERSION = "lin_tianji_rank_v1-exp"
MIN_ELIGIBLE_SAMPLES = 2
MODIFIER_MIN = -2
MODIFIER_MAX = 2

_DOMAIN_ALIASES = {
    "工作／職責": "career",
}
_EVENT_FAMILY_ALIASES = {}
_STATUS_UNITS = {
    "matched": 2,
    "partial": 1,
    "missed": -2,
    "unscorable": None,
}

CANONICAL_DOMAIN_IDS = frozenset(
    [row["primary_domain"] for row in BAZI_TEN_GOD_MAPPING.values()]
    + [row["primary_domain"] for row in ZIWEI_PALACE_MAPPING.values()]
)

CANONICAL_EVENT_FAMILY_IDS = frozenset(
    family
    for row in BAZI_TEN_GOD_MAPPING.values()
    for family in row["event_family_support"]
) | frozenset(
    family
    for row in ZIWEI_PALACE_MAPPING.values()
    for family in row["event_family_support"]
) | frozenset(FLOWING_STAR_CATEGORY_FAMILY.values()) | frozenset(
    TRANSFORMATION_FAMILY.values()
) | frozenset(RELATION_EVENT_FAMILY.values())


def normalize_domain_id(value: object) -> Optional[str]:
    """Return an exact canonical/legacy domain identity, never a fuzzy guess."""

    if not isinstance(value, str) or not value:
        return None
    if value in CANONICAL_DOMAIN_IDS:
        return value
    return _DOMAIN_ALIASES.get(value)


def normalize_event_family_id(value: object) -> Optional[str]:
    """Return an exact canonical/legacy family identity, never a semantic guess."""

    if not isinstance(value, str) or not value:
        return None
    if value in CANONICAL_EVENT_FAMILY_IDS:
        return value
    return _EVENT_FAMILY_ALIASES.get(value)


def evidence_unit(status: object) -> Optional[int]:
    """Return the fixed ordinal evidence unit for a finalized status."""

    if status not in _STATUS_UNITS:
        raise ValueError("unsupported historical evidence status: %r" % (status,))
    return _STATUS_UNITS[status]


def bounded_modifier(units: int, eligible_count: int) -> int:
    """Map aggregate ordinal support into the bounded Phase 4 modifier."""

    if eligible_count < MIN_ELIGIBLE_SAMPLES:
        return 0
    if units >= 3:
        return MODIFIER_MAX
    if units >= 1:
        return 1
    if units == 0:
        return 0
    if units >= -2:
        return -1
    return MODIFIER_MIN


def support_class(modifier: int, eligible_count: int) -> str:
    """Return the non-probabilistic audit class for a bounded modifier."""

    if eligible_count < MIN_ELIGIBLE_SAMPLES:
        return "insufficient"
    if modifier == -2:
        return "contradicted"
    if modifier in (-1, 0):
        return "mixed"
    if modifier == 1:
        return "supported"
    if modifier == 2:
        return "strongly_supported"
    raise ValueError("historical modifier must be within -2..2")
