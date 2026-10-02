"""Project Contract 1.3 natal-revision and Base Case integrity helpers.

These helpers version semantic natal revision identity separately from exact rendered
Case bytes. They do not persist files or interpret metaphysical meaning.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Mapping

from .case_identity import parse_case_filename
from .errors import DistributionError


PROJECT_CONTRACT_V13 = "1.3"
NATAL_REVISION_PROFILE = "natal-revision-v1"
BASE_CASE_DIGEST_PROFILE = "base-case-digest-v1"
_NATAL_REVISION_RE = re.compile(r"^nrev_[0-9a-f]{64}$")
_BASE_CASE_DIGEST_RE = re.compile(r"^bcase_[0-9a-f]{64}$")
_CORRECTION_CLASSES = frozenset((
    "birth_basis_change",
    "source_correction",
    "external_refresh",
    "rule_upgrade",
))


def _canonical_bytes(value: object, error_code: str = "invalid_case_revision") -> bytes:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        return encoded.encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise DistributionError(
            error_code,
            "revision authority payload must contain only standard JSON values",
        ) from exc


def natal_revision_id(kind: str, value: Mapping[str, object]) -> str:
    if kind not in ("normalized_natal", "candidate_envelope"):
        raise DistributionError(
            "invalid_case_revision",
            "unsupported natal revision kind",
            {"kind": kind},
        )
    if not isinstance(value, Mapping):
        raise DistributionError(
            "invalid_case_revision",
            "natal revision source must be a structured mapping",
            {"kind": kind},
        )
    payload = {
        "profile": NATAL_REVISION_PROFILE,
        "kind": kind,
        "value": value,
    }
    return "nrev_" + hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def validate_natal_revision_id(value: object) -> str:
    if not isinstance(value, str) or not _NATAL_REVISION_RE.fullmatch(value):
        raise DistributionError(
            "invalid_case_metadata",
            "natal_revision_id is malformed",
            {"natal_revision_id": value},
        )
    return value


def validate_base_case_digest(value: object) -> str:
    if not isinstance(value, str) or not _BASE_CASE_DIGEST_RE.fullmatch(value):
        raise DistributionError(
            "invalid_case_revision",
            "base_case_digest is malformed",
            {"base_case_digest": value},
        )
    return value


def _length_prefix(value: bytes) -> bytes:
    return len(value).to_bytes(8, "big") + value


def base_case_digest(case_files: Mapping[str, object]) -> str:
    """Bind exact 00-04 filenames and UTF-8 bytes in canonical slot order."""

    if not isinstance(case_files, Mapping):
        raise DistributionError(
            "invalid_case_payload",
            "case_files must be a structured mapping",
        )

    from .case_pack import BASE_CASE_FILES, CASE_FILES

    by_canonical = {}
    for actual, content in case_files.items():
        if not isinstance(actual, str) or not isinstance(content, str):
            raise DistributionError(
                "invalid_case_markdown",
                "Case filenames and contents must be text",
            )
        try:
            parsed = parse_case_filename(actual, CASE_FILES)
        except ValueError:
            # External reference files are intentionally outside the Base Case digest.
            continue
        canonical = parsed["canonical_filename"]
        if canonical not in BASE_CASE_FILES:
            continue
        if canonical in by_canonical:
            raise DistributionError(
                "case_file_set_mismatch",
                "Base Case digest received duplicate canonical slots",
                {"canonical_filename": canonical},
            )
        by_canonical[canonical] = (actual, content)

    missing = [name for name in BASE_CASE_FILES if name not in by_canonical]
    if missing:
        raise DistributionError(
            "case_file_set_mismatch",
            "Base Case digest requires all 00-04 files",
            {"missing_base": missing},
        )

    digest = hashlib.sha256()
    digest.update((BASE_CASE_DIGEST_PROFILE + "\0").encode("utf-8"))
    for canonical in BASE_CASE_FILES:
        actual, content = by_canonical[canonical]
        digest.update(_length_prefix(canonical.encode("utf-8")))
        digest.update(_length_prefix(actual.encode("utf-8")))
        digest.update(_length_prefix(content.encode("utf-8")))
    return "bcase_" + digest.hexdigest()


def correction_class(value: object) -> str:
    if not isinstance(value, str) or value not in _CORRECTION_CLASSES:
        raise DistributionError(
            "invalid_case_revision",
            "unsupported correction_class",
            {
                "correction_class": value,
                "allowed": sorted(_CORRECTION_CLASSES),
            },
        )
    return value


def correction_reason(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DistributionError(
            "invalid_case_revision",
            "correction_reason must be non-empty text",
        )
    return value.strip()
