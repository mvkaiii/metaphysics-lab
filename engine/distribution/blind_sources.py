"""Purpose-specific validation for Stage 1 blind Case sources.

This validator intentionally inspects only the supplied Base Case content (00-04).
The 00 manifest may truthfully record later progressive files as materialized, but
05-08 content must never be supplied to the blind Stage 1 input.
"""

from __future__ import annotations

from typing import Mapping

from .case_identity import parse_case_filename
from .case_pack import (
    BASE_CASE_FILES,
    CASE_FILES,
    PROGRESSIVE_CASE_FILES,
    _RECORD_TYPES,
    _REQUIRED_FRONT_MATTER,
    _identity_from_metadata,
    _manifest_expected_line,
    canonical_case_filename,
    parse_front_matter,
)
from .constants import CASE_SCHEMA_VERSION, PROJECT_CONTRACT_VERSION
from .errors import DistributionError


def validate_blind_source_case(case_files: Mapping[str, object], subject_id: str) -> dict:
    """Validate exactly the subject-aware 00-04 content allowed in blind Stage 1."""
    if not isinstance(case_files, Mapping):
        raise DistributionError(
            "blind_source_violation",
            "subject-aware blind sources require a mapping of Base Case file contents",
        )

    files = {}
    actual_by_canonical = {}
    parsed_by_canonical = {}
    for actual, content in case_files.items():
        if not isinstance(actual, str) or not isinstance(content, str):
            raise DistributionError(
                "invalid_case_markdown",
                "Case filenames and contents must be text",
            )
        try:
            parsed = parse_case_filename(actual, CASE_FILES)
        except ValueError as exc:
            raise DistributionError(
                "case_file_set_mismatch",
                str(exc),
                {"filename": actual},
            ) from exc
        canonical = parsed["canonical_filename"]
        if canonical in PROGRESSIVE_CASE_FILES:
            raise DistributionError(
                "blind_source_violation",
                "first-stage blind forecast cannot receive progressive Case file content",
                {"filename": actual, "canonical_filename": canonical},
            )
        if parsed["legacy"]:
            raise DistributionError(
                "blind_source_violation",
                "subject-aware blind validation cannot use legacy Case filenames",
                {"filename": actual},
            )
        if canonical in files:
            raise DistributionError(
                "case_file_set_mismatch",
                "blind source Case contains duplicate canonical slots",
                {"canonical_filename": canonical},
            )
        files[canonical] = content
        actual_by_canonical[canonical] = actual
        parsed_by_canonical[canonical] = parsed

    missing = set(BASE_CASE_FILES) - set(files)
    extra = set(files) - set(BASE_CASE_FILES)
    if missing or extra or len(files) != len(BASE_CASE_FILES):
        raise DistributionError(
            "blind_source_violation",
            "first-stage blind forecast requires exactly Base Case slots 00-04",
            {"missing_base": sorted(missing), "extra_slots": sorted(extra)},
        )

    versions = set()
    contracts = set()
    identity = None
    display_name = None
    resolved_subject = str(subject_id or "")

    for canonical in BASE_CASE_FILES:
        metadata, _ = parse_front_matter(files[canonical])
        missing_meta = [key for key in _REQUIRED_FRONT_MATTER if key not in metadata]
        if missing_meta:
            raise DistributionError(
                "invalid_case_metadata",
                "Case file is missing required metadata",
                {"filename": actual_by_canonical[canonical], "missing_fields": missing_meta},
            )
        if metadata["record_type"] != _RECORD_TYPES[canonical]:
            raise DistributionError(
                "case_record_type_mismatch",
                "Case filename and record_type do not match",
                {"filename": actual_by_canonical[canonical], "record_type": metadata["record_type"]},
            )

        versions.add(metadata["case_schema_version"])
        contracts.add(metadata["project_contract_version"])
        current_identity = _identity_from_metadata(metadata)
        parsed = parsed_by_canonical[canonical]
        if (
            parsed["filename_label"] != current_identity["filename_label"]
            or parsed["subject_short_id"] != current_identity["subject_short_id"]
        ):
            raise DistributionError(
                "case_subject_filename_mismatch",
                "Case filename identity does not match front matter",
                {"filename": actual_by_canonical[canonical]},
            )
        if identity is None:
            identity = current_identity
            display_name = current_identity["subject_display_name"]
        elif current_identity != identity:
            raise DistributionError(
                "case_subject_mismatch",
                "all blind Base Case files must use identical subject identity metadata",
                {"filename": actual_by_canonical[canonical]},
            )

    if len(versions) != 1 or len(contracts) != 1:
        raise DistributionError(
            "case_version_mismatch",
            "all blind Base Case files must use one schema and contract version",
            {"case_schema_versions": sorted(versions), "project_contract_versions": sorted(contracts)},
        )
    schema = next(iter(versions))
    contract = next(iter(contracts))
    if schema != CASE_SCHEMA_VERSION:
        raise DistributionError(
            "case_schema_incompatible",
            "blind subject-aware Case schema version is not supported by this runtime",
            {"case_schema_version": schema},
        )
    if contract != PROJECT_CONTRACT_VERSION:
        raise DistributionError(
            "case_contract_incompatible",
            "blind subject-aware Case Project Contract version is not supported by this runtime",
            {"project_contract_version": contract},
        )
    if identity is None:
        raise DistributionError(
            "invalid_case_metadata",
            "blind subject-aware Case requires subject identity metadata",
        )
    if identity["subject_id"] != resolved_subject:
        raise DistributionError(
            "blind_source_violation",
            "subject-aware blind sources must match the full payload subject_id",
            {"subject_id": resolved_subject, "source_subject_id": identity["subject_id"]},
        )

    _, index_body = parse_front_matter(files["00_專案索引.md"])
    for canonical in BASE_CASE_FILES:
        actual = actual_by_canonical[canonical]
        expected = _manifest_expected_line(canonical, actual, True)
        if expected not in index_body:
            raise DistributionError(
                "case_manifest_mismatch",
                "00 Case manifest must mark all blind Base Case files as materialized",
                {"filename": actual, "expected_line": expected},
            )

    progressive_state = {}
    for canonical in PROGRESSIVE_CASE_FILES:
        actual = canonical_case_filename(identity, canonical)
        present_line = _manifest_expected_line(canonical, actual, True)
        absent_line = _manifest_expected_line(canonical, actual, False)
        present = present_line in index_body
        absent = absent_line in index_body
        if present == absent:
            raise DistributionError(
                "case_manifest_mismatch",
                "00 Case manifest must record exactly one progressive-file state",
                {"filename": actual},
            )
        progressive_state[canonical] = present

    return {
        "status": "compatible",
        "subject_id": identity["subject_id"],
        "subject_display_name": display_name,
        "subject": identity,
        "case_schema_version": schema,
        "project_contract_version": contract,
        "validated_files": [actual_by_canonical[name] for name in BASE_CASE_FILES],
        "canonical_slots": list(BASE_CASE_FILES),
        "manifest_progressive_state": progressive_state,
    }
