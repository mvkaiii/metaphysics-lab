from __future__ import annotations

from enum import Enum


class ReconciliationStatus(str, Enum):
    MATCH = "MATCH"
    EQUIVALENT = "EQUIVALENT"
    CONFLICT = "CONFLICT"
    NOT_COMPARABLE = "NOT_COMPARABLE"


class ConflictSeverity(str, Enum):
    INFO = "INFO"
    CAUTION = "CAUTION"
    BLOCKING = "BLOCKING"
