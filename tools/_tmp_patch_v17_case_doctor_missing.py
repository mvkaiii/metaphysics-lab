from pathlib import Path


path = Path("engine/distribution/case_doctor.py")
text = path.read_text(encoding="utf-8")
marker = "\n\ndef diagnose_case(payload: Mapping[str, object]) -> dict:\n"
helper = '''


def _missing_record_findings(records) -> list:
    findings = []
    canonical_by_slot = {}
    legacy_records = []
    for row in records:
        if row["source_kind"] == "canonical":
            canonical_by_slot.setdefault(row["slot"], []).append(row)
        else:
            legacy_records.append(row)
    seen = set()
    for legacy in legacy_records:
        candidates = canonical_by_slot.get(legacy["slot"], [])
        if any(candidate["fingerprint"] == legacy["fingerprint"] for candidate in candidates):
            continue
        ambiguous = False
        for candidate in candidates:
            left_time = _first_explicit(candidate["record"], _TIME_KEYS)
            right_time = _first_explicit(legacy["record"], _TIME_KEYS)
            left_category = _first_explicit(candidate["record"], _CATEGORY_KEYS)
            right_category = _first_explicit(legacy["record"], _CATEGORY_KEYS)
            if (
                left_time is not None
                and right_time is not None
                and left_time == right_time
                and left_category is not None
                and right_category is not None
                and left_category == right_category
            ):
                ambiguous = True
                break
        if ambiguous:
            continue
        key = (legacy["slot"], legacy["file"], legacy["fingerprint"])
        if key in seen:
            continue
        seen.add(key)
        findings.append(
            _finding(
                "legacy_record_missing_from_canonical",
                "WARN",
                [legacy["file"]],
                "A structured legacy tracking record is not present in the canonical Case.",
                {
                    "slot": legacy["slot"],
                    "record_id": legacy["record_id"],
                    "fingerprint": legacy["fingerprint"],
                },
            )
        )
    return findings
'''
if "def _missing_record_findings(records)" not in text:
    if marker not in text:
        raise SystemExit("diagnose_case marker not found")
    text = text.replace(marker, helper + marker, 1)
old = "    else:\n        findings.extend(_duplicate_findings(structured_records))\n"
new = old + "        findings.extend(_missing_record_findings(structured_records))\n"
if "findings.extend(_missing_record_findings(structured_records))" not in text:
    if old not in text:
        raise SystemExit("duplicate findings call marker not found")
    text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
