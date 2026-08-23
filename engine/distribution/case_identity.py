"""Canonical Case slot <-> subject-aware filename helpers."""

from __future__ import annotations

import re
from typing import Iterable


_SHORT_ID_RE = re.compile(r"^[0-9A-F]{6,}$")


def build_case_filename(filename_label: str, subject_short_id: str, canonical_filename: str) -> str:
    if not isinstance(filename_label, str) or not filename_label:
        raise ValueError("filename_label must be non-empty text")
    if not isinstance(subject_short_id, str) or not _SHORT_ID_RE.fullmatch(subject_short_id):
        raise ValueError("subject_short_id must be uppercase hexadecimal text")
    if not isinstance(canonical_filename, str) or not canonical_filename:
        raise ValueError("canonical_filename must be non-empty text")
    return "%s_%s_%s" % (filename_label, subject_short_id, canonical_filename)


def parse_case_filename(filename: str, canonical_filenames: Iterable[str]) -> dict:
    allowed = tuple(canonical_filenames)
    if filename in allowed:
        return {
            "actual_filename": filename,
            "canonical_filename": filename,
            "filename_label": None,
            "subject_short_id": None,
            "legacy": True,
        }
    if not isinstance(filename, str) or not filename:
        raise ValueError("Case filename must be non-empty text")
    for canonical in allowed:
        suffix = "_" + canonical
        if not filename.endswith(suffix):
            continue
        prefix = filename[:-len(suffix)]
        if "_" not in prefix:
            break
        label, short_id = prefix.rsplit("_", 1)
        if not label or not _SHORT_ID_RE.fullmatch(short_id):
            break
        return {
            "actual_filename": filename,
            "canonical_filename": canonical,
            "filename_label": label,
            "subject_short_id": short_id,
            "legacy": False,
        }
    raise ValueError("Case filename does not match a canonical Case slot")
