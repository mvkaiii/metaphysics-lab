from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class TimePrecision(IntEnum):
    YEAR = 1
    MONTH = 2
    DAY = 3
    HOUR = 4


@dataclass(frozen=True)
class PrecisionAssessment:
    required: TimePrecision
    available: TimePrecision
    is_unique: bool
    can_execute: bool
    reason: str | None
    allowed_actions: tuple[str, ...]


def assess_precision(
    required: TimePrecision,
    available: TimePrecision,
    *,
    is_unique: bool = True,
) -> PrecisionAssessment:
    if available < required:
        return PrecisionAssessment(
            required=required,
            available=available,
            is_unique=is_unique,
            can_execute=False,
            reason="insufficient_precision",
            allowed_actions=("ask", "keep_candidates", "downgrade"),
        )
    if not is_unique:
        return PrecisionAssessment(
            required=required,
            available=available,
            is_unique=False,
            can_execute=False,
            reason="ambiguous_input",
            allowed_actions=("ask", "keep_candidates", "downgrade"),
        )
    return PrecisionAssessment(
        required=required,
        available=available,
        is_unique=True,
        can_execute=True,
        reason=None,
        allowed_actions=(),
    )
