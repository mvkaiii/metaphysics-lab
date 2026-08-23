"""Temporary deterministic patch helper for PR #166.

Every replacement is exact, asserted, and idempotent. Remove this helper before
PR #166 is marked ready for review.
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
    replace_once(
        "engine/distribution/calibration.py",
        'solar_term_time(actual.year, "立月", zone)',
        'solar_term_time(actual.year, "立春", zone)',
    )

    marker = "    def test_historical_lock_binds_exact_selector_selection(self):\n"
    new_test = '''    def test_blind_forecast_rejects_subject_id_short_id_mismatch(self):
        payload = {
            "blind_forecast_id": "bf-subject-mismatch",
            "subject_id": "subj_aaaaaaaaaaaa",
            "question_type": "flow-year",
            "question_reference": "2027-work",
            "locked_at": "2026-08-23T10:30:00+08:00",
            "source_files_used": [
                "Kai_BBBBBB_00_\u5c08\u6848\u7d22\u5f15.md",
                "Kai_BBBBBB_01_\u547d\u76e4\u6838\u5fc3\u6458\u8981.md",
                "Kai_BBBBBB_02_\u547d\u76e4\u8cc7\u6599\u6821\u9a57\u7d00\u9304.md",
                "Kai_BBBBBB_03_\u516b\u5b57\u7d50\u69cb\u5316\u8cc7\u6599\u5305.md",
                "Kai_BBBBBB_04_\u7d2b\u5fae\u57fa\u790e\u8cc7\u6599\u5305.md",
            ],
            "blind_forecast_payload": {"summary": "active"},
        }
        with self.assertRaises(ValueError):
            lock_blind_forecast(payload)

'''
    replace_once(
        "tests/test_distribution_historical_calibration.py",
        marker,
        new_test + marker,
    )

    replace_once(
        "engine/distribution/calibration.py",
        "def _canonical_case_sources(sources) -> Tuple[list, list]:\n",
        "def _canonical_case_sources(sources, subject_id=None) -> Tuple[list, list]:\n",
    )
    source_return = "    return canonical, actual\n\n\ndef _actual_case_filename"
    source_binding = '''    if subject_short_ids:
        resolved_subject = str(subject_id or "")
        subject_hex = resolved_subject[5:] if resolved_subject.startswith("subj_") else ""
        is_hex = len(subject_hex) >= 12 and all(ch in "0123456789abcdef" for ch in subject_hex.lower())
        short_id = next(iter(subject_short_ids))
        if not is_hex or not subject_hex.upper().startswith(short_id):
            raise DistributionError(
                "blind_source_violation",
                "subject-aware blind sources must match payload subject_id",
                {"subject_id": resolved_subject, "subject_short_id": short_id, "actual_sources": actual},
            )
    return canonical, actual


def _actual_case_filename'''
    replace_once(
        "engine/distribution/calibration.py",
        source_return,
        source_binding,
    )
    replace_once(
        "engine/distribution/calibration.py",
        '''    payload = _mapping(payload, "payload")
    canonical_sources, actual_sources = _canonical_case_sources(payload.get("source_files_used"))
''',
        '''    payload = _mapping(payload, "payload")
    subject_id = _text(payload.get("subject_id"), "subject_id")
    canonical_sources, actual_sources = _canonical_case_sources(payload.get("source_files_used"), subject_id)
''',
    )

    Path(".stabilization-commit-message").write_text(
        "fix: bind blind Base5 to payload subject (#162)\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
