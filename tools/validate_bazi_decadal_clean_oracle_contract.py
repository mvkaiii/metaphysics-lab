"""Fail closed if the v2.1 oracle execution contract contains result leakage."""

from __future__ import annotations

from pathlib import Path

FORBIDDEN_RESULT_MARKERS = (
    "dry-run",
    "dryrun",
    "benchmark passed",
    "48/48",
    "48 match",
    "36 mismatch",
    "missing_reference",
    "repository regressions",
    "production timing is fixed",
    "lunar-python",
    "needs_evidence",
    "domain_review_approved",
    "completed engineering prerequisites",
    "production candidate sha",
)


def find_result_leakage(text: str) -> list[str]:
    lowered = text.lower()
    return sorted(marker for marker in FORBIDDEN_RESULT_MARKERS if marker in lowered)


def validate_clean_oracle_contract(path: Path) -> list[str]:
    return find_result_leakage(path.read_text(encoding="utf-8"))
