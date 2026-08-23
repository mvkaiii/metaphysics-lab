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

    Path(".stabilization-commit-message").write_text(
        "test: bind blind Base5 to payload subject (#162)\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
