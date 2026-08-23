"""Temporary deterministic patch helper for PR #166.

This exists because the execution environment can validate a full GitHub checkout but
cannot push local filesystem edits directly. Every replacement is exact, asserted,
and idempotent. Remove this helper before PR #166 is marked ready for review.
"""

from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    if new in text:
        return
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected exactly one patch target in {path}, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    # Repair an accidental transport-only character corruption introduced while
    # moving the #162 edit through the GitHub connector. This is not a behavior
    # change and restores the original Li Chun term literal.
    replace_once(
        "engine/distribution/calibration.py",
        'solar_term_time(actual.year, "立月", zone)',
        'solar_term_time(actual.year, "立春", zone)',
    )


if __name__ == "__main__":
    main()
