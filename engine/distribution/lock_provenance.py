"""Revision-bound provenance for new Project Contract 1.3 lock serialization."""

from __future__ import annotations

from typing import Mapping, Sequence

from .blind_sources import validate_blind_source_case
from .case_identity import parse_case_filename
from .case_pack import BASE_CASE_FILES, CASE_FILES
from .case_revision import PROJECT_CONTRACT_V13
from .errors import DistributionError


PROFILE_ID = "lock-provenance-v2"
RULE_VERSION = "2.0-exp"
_REQUIRED_FIELDS = frozenset(("subject_id", "source_files_used", "source_case_files"))


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DistributionError(
            "invalid_lock_provenance",
            "%s must be non-empty text" % field,
            {"field": field},
        )
    return value.strip()


def build_lock_provenance(payload: Mapping[str, object], method_version: str) -> dict:
    """Bind a new lock to one validated Project Contract 1.3 Base Case revision."""

    if not isinstance(payload, Mapping):
        raise DistributionError(
            "invalid_lock_provenance",
            "case_provenance must be a structured mapping",
        )
    missing = sorted(_REQUIRED_FIELDS - set(payload))
    unknown = sorted(set(payload) - _REQUIRED_FIELDS)
    if missing or unknown:
        raise DistributionError(
            "invalid_lock_provenance",
            "case_provenance fields do not match the fixed v2 contract",
            {"missing_fields": missing, "unknown_fields": unknown},
        )

    subject_id = _text(payload.get("subject_id"), "subject_id")
    method = _text(method_version, "method_version")
    source_case_files = payload.get("source_case_files")
    validation = validate_blind_source_case(source_case_files, subject_id)

    if validation.get("project_contract_version") != PROJECT_CONTRACT_V13:
        raise DistributionError(
            "lock_provenance_requires_revision_bound_case",
            "new lock provenance requires Project Contract 1.3 Base Case authority",
            {
                "project_contract_version": validation.get("project_contract_version"),
                "required_project_contract_version": PROJECT_CONTRACT_V13,
            },
        )

    source_files = payload.get("source_files_used")
    if isinstance(source_files, (str, bytes)) or not isinstance(source_files, Sequence):
        raise DistributionError(
            "blind_source_violation",
            "source_files_used must be a list of Base Case files",
        )

    actual_by_canonical = {}
    for source in source_files:
        if not isinstance(source, str):
            raise DistributionError(
                "blind_source_violation",
                "source_files_used entries must be text",
            )
        try:
            parsed = parse_case_filename(source, CASE_FILES)
        except ValueError as exc:
            raise DistributionError(
                "blind_source_violation",
                "lock provenance source is not a canonical Case file",
                {"source": source},
            ) from exc
        if parsed["legacy"]:
            raise DistributionError(
                "blind_source_violation",
                "revision-bound lock provenance requires subject-aware filenames",
                {"source": source},
            )
        canonical = parsed["canonical_filename"]
        if canonical in actual_by_canonical:
            raise DistributionError(
                "blind_source_violation",
                "lock provenance cannot contain duplicate Base Case slots",
                {"canonical_filename": canonical},
            )
        actual_by_canonical[canonical] = source

    if set(actual_by_canonical) != set(BASE_CASE_FILES):
        raise DistributionError(
            "blind_source_violation",
            "lock provenance requires exactly Base Case slots 00-04",
            {
                "required_sources": list(BASE_CASE_FILES),
                "canonical_sources": sorted(actual_by_canonical),
            },
        )
    if not isinstance(source_case_files, Mapping) or set(source_case_files) != set(source_files):
        raise DistributionError(
            "blind_source_violation",
            "source_case_files must contain exactly the selected lock source files",
            {
                "source_files_used": sorted(str(item) for item in source_files),
                "provided_sources": sorted(str(item) for item in source_case_files)
                if isinstance(source_case_files, Mapping)
                else [],
            },
        )

    revision = validation.get("natal_revision_id")
    digest = validation.get("base_case_digest")
    if not isinstance(revision, str) or not revision or not isinstance(digest, str) or not digest:
        raise DistributionError(
            "lock_provenance_requires_revision_bound_case",
            "Project Contract 1.3 Case did not expose revision-bound Base Case authority",
        )

    canonical_files = [actual_by_canonical[name] for name in BASE_CASE_FILES]
    return {
        "profile_id": PROFILE_ID,
        "rule_version": RULE_VERSION,
        "project_contract_version": PROJECT_CONTRACT_V13,
        "subject_id": subject_id,
        "natal_revision_id": revision,
        "base_case_digest": digest,
        "source_slots_used": list(BASE_CASE_FILES),
        "source_files_used": canonical_files,
        "method_version": method,
    }
