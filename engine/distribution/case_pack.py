"""Portable progressive Markdown Case Pack.

Case schema 1.1 uses subject-aware filenames while keeping canonical record slots
internally. New Cases start with 00-04 only; 05-08 materialize on first record.
Legacy schema 1.0 bare nine-file packs remain readable and explicitly migratable.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Optional, Tuple

from engine.natal.export import export_bazi_markdown, export_calibration_markdown, export_ziwei_markdown
from engine.natal.models import ExternalNatalView
from engine.natal.orchestration import build_normalized_natal

from .case_identity import build_case_filename, parse_case_filename
from .constants import CASE_SCHEMA_VERSION, DISTRIBUTION_RUNTIME_VERSION, PROJECT_CONTRACT_VERSION
from .errors import DistributionError
from .natal import _source_from_payload, project_natal_from_payload
from .subjects import create_subject_identity, normalize_filename_label


_TEMPLATE_ROOT = Path(__file__).resolve().parents[2] / "templates" / "case"

CASE_FILES = (
    "00_專案索引.md",
    "01_命盤核心摘要.md",
    "02_命盤資料校驗紀錄.md",
    "03_八字結構化資料包.md",
    "04_紫微基礎資料包.md",
    "05_驗證事件紀錄.md",
    "06_流年追蹤紀錄.md",
    "07_問事追蹤紀錄.md",
    "08_重大決策紀錄.md",
)
BASE_CASE_FILES = CASE_FILES[:5]
PROGRESSIVE_CASE_FILES = CASE_FILES[5:]

_RECORD_TYPES = {
    "00_專案索引.md": "project_index",
    "01_命盤核心摘要.md": "natal_core_summary",
    "02_命盤資料校驗紀錄.md": "natal_calibration",
    "03_八字結構化資料包.md": "bazi_structured_facts",
    "04_紫微基礎資料包.md": "ziwei_structured_facts",
    "05_驗證事件紀錄.md": "verified_events",
    "06_流年追蹤紀錄.md": "annual_forecasts",
    "07_問事追蹤紀錄.md": "forecast_questions",
    "08_重大決策紀錄.md": "major_decisions",
}
_SOURCE_CLASSIFICATION = {
    "00_專案索引.md": "Case metadata",
    "01_命盤核心摘要.md": "Resolved natal summary",
    "02_命盤資料校驗紀錄.md": "已校驗資料",
    "03_八字結構化資料包.md": "Structured natal facts",
    "04_紫微基礎資料包.md": "Structured natal facts",
    "05_驗證事件紀錄.md": "Verification ledger",
    "06_流年追蹤紀錄.md": "Forecast tracking",
    "07_問事追蹤紀錄.md": "Forecast tracking",
    "08_重大決策紀錄.md": "Decision tracking",
}
_MUTATION_POLICY = {
    "00_專案索引.md": "schema_subject_manifest_calibration_state",
    "01_命盤核心摘要.md": "material_natal_change_only",
    "02_命盤資料校驗紀錄.md": "reconciliation_change_only",
    "03_八字結構化資料包.md": "material_natal_or_schema_change_only",
    "04_紫微基礎資料包.md": "material_natal_or_schema_change_only",
    "05_驗證事件紀錄.md": "append_first_correction_records",
    "06_流年追蹤紀錄.md": "append_outcome_blind_forecast_immutable",
    "07_問事追蹤紀錄.md": "append_outcome_blind_forecast_immutable",
    "08_重大決策紀錄.md": "append_first_with_review",
}
_REQUIRED_FRONT_MATTER = (
    "case_schema_version", "project_contract_version", "record_type", "subject_id",
    "created_at", "last_updated_at", "last_modified_by", "runtime_version_if_applicable",
    "source_classification", "mutation_policy",
)
_REQUIRED_IDENTITY_FRONT_MATTER = ("subject_display_name", "subject_short_id", "filename_label")
_TRACKING_FILES = frozenset(PROGRESSIVE_CASE_FILES)
_RECORDS_START = "<!-- records:start -->"
_RECORDS_END = "<!-- records:end -->"
_EMPTY_RECORDS = "目前沒有已記錄項目。"
_LEGACY_SUBJECT_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
_OPAQUE_SUBJECT_PATTERN = re.compile(r"^subj_[0-9a-f]{12,}$")
_SHORT_ID_PATTERN = re.compile(r"^[0-9A-F]{6,}$")
_CALIBRATION_STATES = frozenset(("uncalibrated", "basic", "calibrated"))
_RESERVED_INTERNAL_RECORD_TYPES = frozenset(("historical_calibration_lock",))


def _mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise DistributionError("invalid_case_payload", "%s must be a structured mapping" % field_name, {"field": field_name})
    return value


def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DistributionError("invalid_case_payload", "%s must be a non-empty string" % field_name, {"field": field_name})
    return value.strip()


def _timestamp(value: object, field_name: str) -> str:
    text = _text(value, field_name)
    try:
        datetime.fromisoformat(text)
    except ValueError as exc:
        raise DistributionError("invalid_case_timestamp", "%s must be an ISO datetime" % field_name, {"field": field_name, "value": text}) from exc
    return text


def _subject_id(value: object, *, opaque: bool = False) -> str:
    subject = _text(value, "subject_id")
    pattern = _OPAQUE_SUBJECT_PATTERN if opaque else _LEGACY_SUBJECT_PATTERN
    if not pattern.fullmatch(subject):
        raise DistributionError("invalid_subject_id", "subject_id does not match the required Case identity format")
    return subject


def _identity_from_payload(payload: Mapping[str, object]) -> dict:
    subject_id = _subject_id(payload.get("subject_id"), opaque=True)
    display = _text(payload.get("subject_display_name"), "subject_display_name")
    short_id = _text(payload.get("subject_short_id"), "subject_short_id")
    label = _text(payload.get("filename_label", normalize_filename_label(display)), "filename_label")
    if not _SHORT_ID_PATTERN.fullmatch(short_id):
        raise DistributionError("invalid_subject_id", "subject_short_id must be uppercase hexadecimal text")
    if not subject_id[5:].upper().startswith(short_id):
        raise DistributionError("invalid_subject_id", "subject_short_id must be derived from subject_id")
    expected_label = normalize_filename_label(display)
    if label != expected_label:
        raise DistributionError(
            "subject_identity_mismatch",
            "filename_label must equal normalized subject_display_name",
            {"filename_label": label, "expected_filename_label": expected_label},
        )
    return {"subject_id": subject_id, "subject_display_name": display, "subject_short_id": short_id, "filename_label": label}


def _identity_from_metadata(metadata: Mapping[str, str]) -> dict:
    missing = [field for field in _REQUIRED_IDENTITY_FRONT_MATTER if not metadata.get(field)]
    if missing:
        raise DistributionError("invalid_case_metadata", "Case identity metadata is missing", {"missing_fields": missing})
    return _identity_from_payload({
        "subject_id": metadata.get("subject_id"), "subject_display_name": metadata.get("subject_display_name"),
        "subject_short_id": metadata.get("subject_short_id"), "filename_label": metadata.get("filename_label"),
    })


def canonical_case_filename(identity: Mapping[str, str], canonical: str) -> str:
    return build_case_filename(identity["filename_label"], identity["subject_short_id"], canonical)


def _load_template(name: str) -> str:
    path = _TEMPLATE_ROOT / name
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise DistributionError("case_template_unavailable", "canonical Case template is unavailable", {"template": name}) from exc


def _front_matter_value(value: object) -> str:
    if value is None:
        return "null"
    text = str(value)
    if "\n" in text or "\r" in text:
        raise DistributionError("invalid_case_metadata", "front matter values must be one line")
    return text


def render_front_matter(metadata: Mapping[str, object]) -> str:
    lines = ["---"]
    for key in _REQUIRED_FRONT_MATTER:
        if key not in metadata:
            raise DistributionError("invalid_case_metadata", "required Case metadata is missing", {"missing_field": key})
        lines.append("%s: %s" % (key, _front_matter_value(metadata[key])))
    for key in sorted(set(metadata) - set(_REQUIRED_FRONT_MATTER)):
        lines.append("%s: %s" % (key, _front_matter_value(metadata[key])))
    lines.append("---")
    return "\n".join(lines) + "\n"


def parse_front_matter(text: object) -> Tuple[dict, str]:
    if not isinstance(text, str):
        raise DistributionError("invalid_case_markdown", "Case file content must be text")
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        raise DistributionError("invalid_case_markdown", "Case file is missing front matter")
    metadata = {}
    body_start = None
    for index, line in enumerate(lines[1:], start=1):
        stripped = line.rstrip("\r\n")
        if stripped == "---":
            body_start = index + 1
            break
        if ": " not in stripped:
            raise DistributionError("invalid_case_markdown", "Case front matter must use 'key: value' lines", {"line": stripped})
        key, value = stripped.split(": ", 1)
        if not key or key in metadata:
            raise DistributionError("invalid_case_markdown", "Case front matter contains an invalid or duplicate key", {"key": key})
        metadata[key] = value
    if body_start is None:
        raise DistributionError("invalid_case_markdown", "Case front matter is not terminated")
    return metadata, "".join(lines[body_start:])


def _metadata(canonical: str, identity: Mapping[str, str], created_at: str, modified_by: str) -> dict:
    return {
        "case_schema_version": CASE_SCHEMA_VERSION, "project_contract_version": PROJECT_CONTRACT_VERSION,
        "record_type": _RECORD_TYPES[canonical], "subject_id": identity["subject_id"],
        "subject_display_name": identity["subject_display_name"], "subject_short_id": identity["subject_short_id"],
        "filename_label": identity["filename_label"], "created_at": created_at, "last_updated_at": created_at,
        "last_modified_by": modified_by, "runtime_version_if_applicable": DISTRIBUTION_RUNTIME_VERSION,
        "source_classification": _SOURCE_CLASSIFICATION[canonical], "mutation_policy": _MUTATION_POLICY[canonical],
    }


def _external_from_payload(value: object) -> Optional[ExternalNatalView]:
    if value is None:
        return None
    raw = _mapping(value, "normalized_natal.external")
    return ExternalNatalView(
        birth=_mapping(raw.get("birth", {}), "normalized_natal.external.birth"),
        bazi=_mapping(raw.get("bazi", {}), "normalized_natal.external.bazi"),
        ziwei=_mapping(raw.get("ziwei", {}), "normalized_natal.external.ziwei"),
        source=_source_from_payload(raw.get("source"), "normalized_natal.external.source"),
    )


def _normalized_model(value: object):
    raw = _mapping(value, "normalized_natal")
    project_raw = raw.get("project")
    external_raw = raw.get("external")
    project = None if project_raw is None else project_natal_from_payload(project_raw)
    external = _external_from_payload(external_raw)
    if project is None and external is None:
        raise DistributionError("invalid_case_payload", "Case export requires at least one natal source")
    return build_normalized_natal(project=project, external=external)


def _analysis_section(value: object) -> str:
    if value is None:
        return ""
    raw = _mapping(value, "analysis_sections")
    if not raw:
        return ""
    lines = ["## 命理推論", "", "以下內容由 AI／分析者提供，分類為命理推論，不是盤面事實或已驗證事件。", ""]
    for label in sorted(raw, key=str):
        body = raw[label]
        if not isinstance(label, str) or not label.strip() or not isinstance(body, str) or not body.strip():
            raise DistributionError("invalid_case_payload", "analysis_sections must map non-empty labels to non-empty text")
        lines.extend(["### %s" % label.strip(), "", body.strip(), ""])
    return "\n".join(lines).rstrip() + "\n"


def _prefix_title(body: str, display_name: str) -> str:
    lines = body.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("# "):
            if not line.startswith("# %s｜" % display_name):
                lines[index] = "# %s｜%s" % (display_name, line[2:])
            break
    return "\n".join(lines).rstrip() + "\n"


def _rename_title(body: str, old_display_name: str, new_display_name: str) -> str:
    lines = body.splitlines()
    old_prefix = "# %s｜" % old_display_name
    for index, line in enumerate(lines):
        if line.startswith(old_prefix):
            lines[index] = "# %s｜%s" % (new_display_name, line[len(old_prefix):])
            break
    return "\n".join(lines).rstrip() + "\n"


def _core_summary(chart, identity: Mapping[str, str], analysis: str) -> str:
    project = None if chart.project is None else chart.project.to_dict()
    external = None if chart.external is None else chart.external.to_dict()
    lines = [
        "# %s｜命盤核心摘要" % identity["subject_display_name"], "", "- 命主：%s" % identity["subject_display_name"],
        "- Subject ID: `%s`" % identity["subject_id"], "- Normalized Natal Identity: `%s`" % chart.identity,
        "- Validation: `%s`" % chart.validation.get("overall_status", "unknown"),
    ]
    if project is not None:
        birth, bazi, ziwei = project.get("birth", {}), project.get("bazi", {}), project.get("ziwei", {})
        pillars = bazi.get("pillars", {})
        lines.extend([
            "- Project source: `%s` / maturity=`%s`" % (project["source"].get("source_name"), project["source"].get("maturity")),
            "- 出生基礎: `%s`｜`%s`" % (birth.get("reported_datetime"), birth.get("resolved_place_label")),
            "- 八字四柱: `%s %s %s %s`" % (pillars.get("year", "?"), pillars.get("month", "?"), pillars.get("day", "?"), pillars.get("hour", "?")),
            "- 日主: `%s`" % bazi.get("day_master", "?"),
            "- 紫微命宮／身宮／五行局: `%s` / `%s` / `%s`" % (ziwei.get("ming_palace", "?"), ziwei.get("body_palace", "?"), ziwei.get("five_element_bureau", "?")),
        ])
    if external is not None:
        lines.append("- External source: `%s`" % external["source"].get("source_name"))
    lines.append("")
    if analysis:
        lines.extend([analysis.rstrip(), ""])
    return "\n".join(lines).rstrip() + "\n"


def _tracking_body(title: str, display_name: str) -> str:
    return "# %s｜%s\n\n## 紀錄\n\n%s\n%s\n%s\n" % (display_name, title, _RECORDS_START, _EMPTY_RECORDS, _RECORDS_END)


def _render_case_file(canonical: str, metadata: Mapping[str, object], body: str) -> str:
    template_name = {
        "00_專案索引.md": "00_project_index.md.tmpl", "01_命盤核心摘要.md": "01_natal_core_summary.md.tmpl",
        "02_命盤資料校驗紀錄.md": "02_natal_calibration.md.tmpl", "03_八字結構化資料包.md": "03_bazi_structured_facts.md.tmpl",
        "04_紫微基礎資料包.md": "04_ziwei_structured_facts.md.tmpl", "05_驗證事件紀錄.md": "05_verified_events.md.tmpl",
        "06_流年追蹤紀錄.md": "06_annual_forecasts.md.tmpl", "07_問事追蹤紀錄.md": "07_forecast_questions.md.tmpl",
        "08_重大決策紀錄.md": "08_major_decisions.md.tmpl",
    }[canonical]
    template = _load_template(template_name)
    return render_front_matter(metadata) + template.format(body=body.rstrip()).rstrip() + "\n"


def _rewrite_case_file(metadata: Mapping[str, object], body: str) -> str:
    """Rewrite an already-rendered Case without nesting the canonical template again."""
    return render_front_matter(metadata) + body.rstrip() + "\n"


def _manifest_expected_line(canonical: str, actual: str, present: bool) -> str:
    labels = {"00": "專案索引", "01": "命盤核心摘要", "02": "命盤資料校驗紀錄", "03": "八字結構化資料包", "04": "紫微基礎資料包", "05": "驗證事件紀錄", "06": "流年追蹤紀錄", "07": "問事追蹤紀錄", "08": "重大決策紀錄"}
    return "- %s %s %s｜`%s`" % ("✓" if present else "○", canonical[:2], labels[canonical[:2]], actual)


def _index_body(chart, identity: Mapping[str, str], materialized, calibration_status: str) -> str:
    project_name = None if chart.project is None else chart.project.source.source_name
    external_name = None if chart.external is None else chart.external.source.source_name
    lines = [
        "# %s｜Metaphysics Lab Case｜專案索引" % identity["subject_display_name"], "", "- 命主：%s" % identity["subject_display_name"],
        "- Subject ID: `%s`" % identity["subject_id"], "- Normalized Natal Identity: `%s`" % chart.identity,
        "- Project source: `%s`" % (project_name or "none"), "- External source: `%s`" % (external_name or "none"),
        "- Case lifecycle: `progressive`", "", "## Case Files", "",
    ]
    present = set(materialized)
    for canonical in CASE_FILES:
        lines.append(_manifest_expected_line(canonical, canonical_case_filename(identity, canonical), canonical in present))
    lines.extend(["", "## Historical Calibration", "", "Historical Calibration: `%s`" % calibration_status, ""])
    return "\n".join(lines)


def export_case_markdown(payload: Mapping[str, object]) -> dict:
    payload = _mapping(payload, "payload")
    chart = _normalized_model(payload.get("normalized_natal"))
    identity = _identity_from_payload(payload)
    generated_at = _timestamp(payload.get("generated_at"), "generated_at")
    modified_by = _text(payload.get("last_modified_by", "ai"), "last_modified_by")
    generated_date = datetime.fromisoformat(generated_at).date()
    analysis = _analysis_section(payload.get("analysis_sections"))
    bodies = {
        "00_專案索引.md": _index_body(chart, identity, BASE_CASE_FILES, "uncalibrated"),
        "01_命盤核心摘要.md": _core_summary(chart, identity, analysis),
        "02_命盤資料校驗紀錄.md": _prefix_title(export_calibration_markdown(chart, generated_date), identity["subject_display_name"]),
        "03_八字結構化資料包.md": _prefix_title(export_bazi_markdown(chart, generated_date), identity["subject_display_name"]),
        "04_紫微基礎資料包.md": _prefix_title(export_ziwei_markdown(chart, generated_date), identity["subject_display_name"]),
    }
    files = {}
    for canonical in BASE_CASE_FILES:
        actual = canonical_case_filename(identity, canonical)
        files[actual] = _render_case_file(canonical, _metadata(canonical, identity, generated_at, modified_by), bodies[canonical])
    return {"subject_id": identity["subject_id"], "subject": identity, "files": files}


def _case_files(value: object):
    raw = _mapping(value, "case_files")
    canonical_files, actual_by_canonical, parsed_by_canonical = {}, {}, {}
    for actual, content in raw.items():
        if not isinstance(actual, str) or not isinstance(content, str):
            raise DistributionError("invalid_case_markdown", "Case filenames and contents must be text")
        try:
            parsed = parse_case_filename(actual, CASE_FILES)
        except ValueError as exc:
            raise DistributionError("case_file_set_mismatch", str(exc), {"filename": actual}) from exc
        canonical = parsed["canonical_filename"]
        if canonical in canonical_files:
            raise DistributionError("case_file_set_mismatch", "Case pack contains duplicate canonical slots", {"canonical_filename": canonical})
        canonical_files[canonical] = content
        actual_by_canonical[canonical] = actual
        parsed_by_canonical[canonical] = parsed
    missing_base = set(BASE_CASE_FILES) - set(canonical_files)
    if missing_base:
        raise DistributionError("case_file_set_mismatch", "Case pack must contain all base files", {"missing_base": sorted(missing_base)})
    return canonical_files, actual_by_canonical, parsed_by_canonical


def _validate_manifest(files: Mapping[str, str], actual_by_canonical: Mapping[str, str], identity: Mapping[str, str]) -> None:
    _, body = parse_front_matter(files["00_專案索引.md"])
    for canonical in CASE_FILES:
        actual = actual_by_canonical.get(canonical, canonical_case_filename(identity, canonical))
        expected = _manifest_expected_line(canonical, actual, canonical in files)
        if expected not in body:
            raise DistributionError("case_manifest_mismatch", "00 Case manifest does not match materialized files", {"filename": actual, "expected_line": expected})


def validate_case(payload: Mapping[str, object]) -> dict:
    payload = _mapping(payload, "payload")
    files, actual_by_canonical, parsed_by_canonical = _case_files(payload.get("case_files"))
    subject = display_name = identity = None
    versions, contracts = set(), set()
    for canonical in CASE_FILES:
        if canonical not in files:
            continue
        metadata, _ = parse_front_matter(files[canonical])
        missing = [key for key in _REQUIRED_FRONT_MATTER if key not in metadata]
        if missing:
            raise DistributionError("invalid_case_metadata", "Case file is missing required metadata", {"filename": actual_by_canonical[canonical], "missing_fields": missing})
        if metadata["record_type"] != _RECORD_TYPES[canonical]:
            raise DistributionError("case_record_type_mismatch", "Case filename and record_type do not match", {"filename": actual_by_canonical[canonical], "record_type": metadata["record_type"]})
        versions.add(metadata["case_schema_version"])
        contracts.add(metadata["project_contract_version"])
        current_subject = metadata["subject_id"]
        if subject is None:
            subject = current_subject
        elif current_subject != subject:
            raise DistributionError("case_subject_mismatch", "all Case files must belong to the same subject_id", {"filename": actual_by_canonical[canonical], "expected_subject_id": subject, "actual_subject_id": current_subject})
        if metadata["case_schema_version"] == CASE_SCHEMA_VERSION:
            current_identity = _identity_from_metadata(metadata)
            parsed = parsed_by_canonical[canonical]
            if parsed["legacy"]:
                raise DistributionError("case_subject_filename_mismatch", "Case schema 1.1 requires subject-aware filenames", {"filename": actual_by_canonical[canonical]})
            if parsed["filename_label"] != current_identity["filename_label"] or parsed["subject_short_id"] != current_identity["subject_short_id"]:
                raise DistributionError("case_subject_filename_mismatch", "Case filename identity does not match front matter", {"filename": actual_by_canonical[canonical]})
            if identity is None:
                identity, display_name = current_identity, current_identity["subject_display_name"]
            elif current_identity != identity:
                raise DistributionError("case_subject_mismatch", "all Case files must use identical subject identity metadata", {"filename": actual_by_canonical[canonical]})
    if len(versions) != 1 or len(contracts) != 1:
        raise DistributionError("case_version_mismatch", "all Case files must use one schema and contract version", {"case_schema_versions": sorted(versions), "project_contract_versions": sorted(contracts)})
    schema, contract = next(iter(versions)), next(iter(contracts))
    if schema == "1.0":
        if set(files) != set(CASE_FILES) or contract != "1.0" or any(not parsed_by_canonical[name]["legacy"] for name in CASE_FILES):
            raise DistributionError("case_schema_incompatible", "legacy Case schema 1.0 requires the complete bare nine-file contract 1.0 pack")
    elif schema == CASE_SCHEMA_VERSION:
        if contract != PROJECT_CONTRACT_VERSION:
            raise DistributionError("case_contract_incompatible", "Case Project Contract version is not supported by this runtime", {"project_contract_version": contract})
        if identity is None:
            raise DistributionError("invalid_case_metadata", "Case schema 1.1 requires subject identity metadata")
        _validate_manifest(files, actual_by_canonical, identity)
    else:
        raise DistributionError("case_schema_incompatible", "Case schema version is not supported by this runtime", {"case_schema_version": schema})
    return {
        "status": "compatible", "subject_id": subject, "subject_display_name": display_name, "subject": identity,
        "case_schema_version": schema, "project_contract_version": contract,
        "validated_files": [actual_by_canonical[name] for name in CASE_FILES if name in files],
        "canonical_slots": [name for name in CASE_FILES if name in files],
    }


def _replace_manifest_lines(body: str, identity: Mapping[str, str], materialized) -> str:
    lines, output = body.splitlines(), []
    by_prefix = {canonical[:2]: canonical for canonical in CASE_FILES}
    for line in lines:
        matched = re.match(r"^- [✓○] (0[0-8]) ", line)
        if matched and matched.group(1) in by_prefix:
            canonical = by_prefix[matched.group(1)]
            output.append(_manifest_expected_line(canonical, canonical_case_filename(identity, canonical), canonical in materialized))
        else:
            output.append(line)
    return "\n".join(output).rstrip() + "\n"


def migrate_case(payload: Mapping[str, object]) -> dict:
    payload = _mapping(payload, "payload")
    files, actual_by_canonical, _ = _case_files(payload.get("case_files"))
    validation = validate_case({"case_files": payload.get("case_files")})
    if validation["case_schema_version"] == CASE_SCHEMA_VERSION:
        return {"status": validation["status"], "migration": "no_change", "changed_files": {}, "subject_id": validation["subject_id"], "case_schema_version": validation["case_schema_version"]}
    display_name = _text(payload.get("subject_display_name"), "subject_display_name")
    created = create_subject_identity({"subject_display_name": display_name, "registry_markdown": payload.get("registry_markdown")})
    identity = created["identity"]
    changed, renamed = {}, {}
    for canonical in CASE_FILES:
        metadata, body = parse_front_matter(files[canonical])
        old_subject = metadata.get("subject_id")
        metadata.update(_metadata(canonical, identity, metadata["created_at"], metadata.get("last_modified_by", "ai")))
        metadata["last_updated_at"] = _timestamp(payload.get("updated_at"), "updated_at")
        metadata["legacy_subject_id"] = old_subject
        body = _prefix_title(body, identity["subject_display_name"])
        if canonical == "00_專案索引.md":
            body = _replace_manifest_lines(body, identity, CASE_FILES)
        actual = canonical_case_filename(identity, canonical)
        changed[actual] = _rewrite_case_file(metadata, body)
        renamed[actual_by_canonical[canonical]] = actual
    return {
        "status": "compatible", "migration": "legacy_1_0_to_subject_aware_1_1", "changed_files": changed,
        "renamed_files": renamed, "subject_id": identity["subject_id"], "subject": identity,
        "registry_markdown": created["registry_markdown"], "case_schema_version": CASE_SCHEMA_VERSION,
    }


def rename_case_subject_files(case_files: Mapping[str, object], new_subject_display_name: str, updated_at: str, modified_by: str = "ai") -> dict:
    """Rename display metadata and every materialized Case filename atomically in one result."""
    validation = validate_case({"case_files": case_files})
    if validation["case_schema_version"] != CASE_SCHEMA_VERSION or validation.get("subject") is None:
        raise DistributionError("case_schema_incompatible", "subject rename requires a subject-aware Case schema 1.1 pack")
    files, actual_by_canonical, _ = _case_files(case_files)
    old_identity = dict(validation["subject"])
    new_display = _text(new_subject_display_name, "new_subject_display_name")
    new_identity = dict(old_identity)
    new_identity["subject_display_name"] = new_display
    new_identity["filename_label"] = normalize_filename_label(new_display)
    when = _timestamp(updated_at, "updated_at")
    actor = _text(modified_by, "last_modified_by")
    changed, renamed = {}, {}
    materialized = set(files)
    for canonical in CASE_FILES:
        if canonical not in files:
            continue
        metadata, body = parse_front_matter(files[canonical])
        metadata["subject_display_name"] = new_identity["subject_display_name"]
        metadata["filename_label"] = new_identity["filename_label"]
        metadata["last_updated_at"] = when
        metadata["last_modified_by"] = actor
        body = _rename_title(body, old_identity["subject_display_name"], new_identity["subject_display_name"])
        if canonical == "00_專案索引.md":
            body = _replace_manifest_lines(body, new_identity, materialized)
            body = body.replace("- 命主：%s" % old_identity["subject_display_name"], "- 命主：%s" % new_identity["subject_display_name"], 1)
        elif canonical == "01_命盤核心摘要.md":
            body = body.replace("- 命主：%s" % old_identity["subject_display_name"], "- 命主：%s" % new_identity["subject_display_name"], 1)
        new_actual = canonical_case_filename(new_identity, canonical)
        old_actual = actual_by_canonical[canonical]
        changed[new_actual] = _rewrite_case_file(metadata, body)
        renamed[old_actual] = new_actual
    return {
        "subject_id": new_identity["subject_id"], "subject": new_identity, "changed_files": changed,
        "renamed_files": renamed, "removed_filenames": [old for old, new in renamed.items() if old != new],
    }


def _render_entry(entry: Mapping[str, object]) -> str:
    record_id = _text(entry.get("record_id"), "entry.record_id")
    payload = json.dumps(dict(entry), ensure_ascii=False, sort_keys=True, indent=2)
    return "### %s\n\n```json\n%s\n```" % (record_id, payload)


def _record_entries(body: str) -> dict:
    start, end = body.find(_RECORDS_START), body.find(_RECORDS_END)
    if start < 0 or end < 0 or end <= start:
        raise DistributionError("invalid_case_markdown", "tracking Case file is missing record boundary markers")
    content_start = start + len(_RECORDS_START)
    current = body[content_start:end].strip()
    if current == _EMPTY_RECORDS or not current:
        return {}
    records = {}
    for chunk in re.split(r"\n\n(?=### )", current):
        first_line, marker, rest = chunk.partition("\n\n```json\n")
        if not marker or not first_line.startswith("### ") or not rest.endswith("\n```"):
            raise DistributionError("invalid_case_markdown", "tracking record block is malformed")
        record_id = first_line[4:].strip()
        try:
            parsed = json.loads(rest[:-4])
        except (TypeError, ValueError) as exc:
            raise DistributionError("invalid_case_markdown", "tracking record JSON cannot be parsed") from exc
        if not isinstance(parsed, Mapping) or parsed.get("record_id") != record_id:
            raise DistributionError("invalid_case_markdown", "tracking record heading does not match payload record_id")
        if record_id in records:
            raise DistributionError("invalid_case_markdown", "tracking file contains duplicate record_id", {"record_id": record_id})
        records[record_id] = dict(parsed)
    return records


def _append_record(body: str, entry_text: str) -> str:
    start, end = body.find(_RECORDS_START), body.find(_RECORDS_END)
    if start < 0 or end < 0 or end <= start:
        raise DistributionError("invalid_case_markdown", "tracking Case file is missing record boundary markers")
    content_start = start + len(_RECORDS_START)
    current = body[content_start:end].strip()
    updated = entry_text if current == _EMPTY_RECORDS or not current else current + "\n\n" + entry_text
    return body[:content_start] + "\n" + updated + "\n" + body[end:]


def _set_index_materialized(index_text: str, canonical: str, actual_target: str, updated_at: str, modified_by: str) -> str:
    metadata, body = parse_front_matter(index_text)
    absent, present = _manifest_expected_line(canonical, actual_target, False), _manifest_expected_line(canonical, actual_target, True)
    if present not in body:
        if absent not in body:
            raise DistributionError("case_manifest_mismatch", "00 Case manifest is missing target file state", {"target": actual_target})
        body = body.replace(absent, present, 1)
    metadata["last_updated_at"], metadata["last_modified_by"] = updated_at, modified_by
    return render_front_matter(metadata) + body.rstrip() + "\n"


def set_case_calibration_status(index_text: str, status: str, updated_at: str, modified_by: str) -> str:
    if status not in _CALIBRATION_STATES:
        raise DistributionError("invalid_calibration_status", "unsupported historical calibration status", {"status": status})
    metadata, body = parse_front_matter(index_text)
    body, count = re.subn(r"Historical Calibration: `(?:uncalibrated|basic|calibrated)`", "Historical Calibration: `%s`" % status, body, count=1)
    if count != 1:
        raise DistributionError("case_manifest_mismatch", "00 Case manifest is missing calibration status")
    metadata["last_updated_at"], metadata["last_modified_by"] = updated_at, modified_by
    return render_front_matter(metadata) + body.rstrip() + "\n"


def _validate_05_entry(entry: Mapping[str, object]) -> None:
    if entry.get("status") == "verified":
        return
    if entry.get("record_type") != "historical_calibration":
        raise DistributionError("invalid_verified_event", "05 accepts verified events or historical calibration ledger records only")
    blind, evaluation = entry.get("blind_prediction"), entry.get("evaluation")
    if not isinstance(blind, Mapping) or blind.get("classification") != "命理推論":
        raise DistributionError("invalid_verified_event", "historical calibration blind prediction classification is invalid")
    if not isinstance(evaluation, Mapping) or evaluation.get("classification") != "已校驗資料":
        raise DistributionError("invalid_verified_event", "historical calibration evaluation classification is invalid")
    actual = entry.get("user_confirmed_actual")
    if actual is not None and (not isinstance(actual, Mapping) or actual.get("classification") != "已驗證事件"):
        raise DistributionError("invalid_verified_event", "historical calibration actual-event classification is invalid")


def _resolve_requested_canonical(filename: str) -> str:
    if filename in CASE_FILES:
        return filename
    try:
        return parse_case_filename(filename, CASE_FILES)["canonical_filename"]
    except ValueError as exc:
        raise DistributionError("case_file_set_mismatch", str(exc), {"filename": filename}) from exc


def _update_case_record(payload: Mapping[str, object], *, allow_reserved_internal: bool = False) -> dict:
    payload = _mapping(payload, "payload")
    files, actual_by_canonical, _ = _case_files(payload.get("case_files"))
    validation = validate_case({"case_files": payload.get("case_files")})
    legacy = validation["case_schema_version"] == "1.0"
    requested_filename = _text(payload.get("filename"), "filename")
    canonical = _resolve_requested_canonical(requested_filename)
    if canonical not in _TRACKING_FILES:
        raise DistributionError("immutable_case_record", "incremental Case updates are allowed only for tracking files 05-08", {"filename": requested_filename})
    operation = _text(payload.get("operation"), "operation")
    if operation == "replace_blind_forecast" and canonical in ("06_流年追蹤紀錄.md", "07_問事追蹤紀錄.md"):
        raise DistributionError("immutable_blind_forecast", "recorded first-version blind forecast cannot be replaced", {"filename": requested_filename})
    if operation != "append":
        raise DistributionError("unsupported_case_mutation", "unsupported Case mutation operation", {"operation": operation})
    entry = _mapping(payload.get("entry"), "entry")
    if entry.get("record_type") in _RESERVED_INTERNAL_RECORD_TYPES and not allow_reserved_internal:
        raise DistributionError(
            "immutable_case_record",
            "reserved internal Case record types cannot be appended through the public mutation API",
            {"filename": requested_filename, "record_type": entry.get("record_type")},
        )
    if canonical == "05_驗證事件紀錄.md":
        _validate_05_entry(entry)
    updated_at = _timestamp(payload.get("updated_at"), "updated_at")
    modified_by = _text(payload.get("last_modified_by", "ai"), "last_modified_by")
    changed = {}
    existing = canonical in files
    if existing:
        metadata, body = parse_front_matter(files[canonical])
        actual_target = actual_by_canonical[canonical]
    else:
        if legacy:
            raise DistributionError("case_file_set_mismatch", "legacy Case is missing required tracking file")
        index_metadata, _ = parse_front_matter(files["00_專案索引.md"])
        identity = _identity_from_metadata(index_metadata)
        actual_target = canonical_case_filename(identity, canonical)
        metadata = _metadata(canonical, identity, index_metadata["created_at"], modified_by)
        body = _tracking_body({"05_驗證事件紀錄.md": "驗證事件紀錄", "06_流年追蹤紀錄.md": "流年追蹤紀錄", "07_問事追蹤紀錄.md": "問事追蹤紀錄", "08_重大決策紀錄.md": "重大決策紀錄"}[canonical], identity["subject_display_name"])
        index_actual = actual_by_canonical["00_專案索引.md"]
        changed[index_actual] = _set_index_materialized(files["00_專案索引.md"], canonical, actual_target, updated_at, modified_by)
    record_id = _text(entry.get("record_id"), "entry.record_id")
    existing_records = _record_entries(body)
    if record_id in existing_records:
        if existing_records[record_id] == dict(entry):
            return {"subject_id": validation["subject_id"], "changed_files": {}}
        raise DistributionError(
            "duplicate_record_id",
            "record_id already exists in this Case slot with different content",
            {"filename": requested_filename, "record_id": record_id},
        )
    metadata["last_updated_at"], metadata["last_modified_by"] = updated_at, modified_by
    updated_body = _append_record(body, _render_entry(entry))
    changed[actual_target] = _rewrite_case_file(metadata, updated_body) if existing else _render_case_file(canonical, metadata, updated_body)
    return {"subject_id": validation["subject_id"], "changed_files": changed}


def update_case_record(payload: Mapping[str, object]) -> dict:
    """Public progressive Case mutation entry point; reserved authority records are blocked."""
    return _update_case_record(payload, allow_reserved_internal=False)


def _append_internal_case_record(payload: Mapping[str, object]) -> dict:
    """Internal-only append path for runtime-owned immutable authority records."""
    return _update_case_record(payload, allow_reserved_internal=True)
