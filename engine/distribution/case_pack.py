"""Portable progressive Markdown Case Pack.

Case files store private facts, provenance, analysis labels and append-first
tracking history. New Case schema 1.1 starts with 00-04 only; 05-08 are
materialized when the first real record exists. Legacy schema 1.0 nine-file
packs remain readable.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Optional, Tuple

from engine.natal.export import (
    export_bazi_markdown,
    export_calibration_markdown,
    export_ziwei_markdown,
)
from engine.natal.models import ExternalNatalView
from engine.natal.orchestration import build_normalized_natal

from .constants import (
    CASE_SCHEMA_VERSION,
    DISTRIBUTION_RUNTIME_VERSION,
    PROJECT_CONTRACT_VERSION,
)
from .errors import DistributionError
from .natal import _source_from_payload, project_natal_from_payload


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
    "case_schema_version",
    "project_contract_version",
    "record_type",
    "subject_id",
    "created_at",
    "last_updated_at",
    "last_modified_by",
    "runtime_version_if_applicable",
    "source_classification",
    "mutation_policy",
)

_TRACKING_FILES = frozenset(PROGRESSIVE_CASE_FILES)
_RECORDS_START = "<!-- records:start -->"
_RECORDS_END = "<!-- records:end -->"
_EMPTY_RECORDS = "目前沒有已記錄項目。"
_SUBJECT_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
_CALIBRATION_STATES = frozenset(("uncalibrated", "basic", "calibrated"))


def _mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise DistributionError(
            "invalid_case_payload",
            "%s must be a structured mapping" % field_name,
            {"field": field_name},
        )
    return value


def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DistributionError(
            "invalid_case_payload",
            "%s must be a non-empty string" % field_name,
            {"field": field_name},
        )
    return value.strip()


def _timestamp(value: object, field_name: str) -> str:
    text = _text(value, field_name)
    try:
        datetime.fromisoformat(text)
    except ValueError as exc:
        raise DistributionError(
            "invalid_case_timestamp",
            "%s must be an ISO datetime" % field_name,
            {"field": field_name, "value": text},
        ) from exc
    return text


def _subject_id(value: object) -> str:
    subject = _text(value, "subject_id")
    if not _SUBJECT_PATTERN.fullmatch(subject):
        raise DistributionError(
            "invalid_subject_id",
            "subject_id must be an opaque identifier using letters, digits, dot, underscore or hyphen",
        )
    return subject


def _load_template(name: str) -> str:
    path = _TEMPLATE_ROOT / name
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise DistributionError(
            "case_template_unavailable",
            "canonical Case template is unavailable",
            {"template": name},
        ) from exc


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
            raise DistributionError(
                "invalid_case_metadata",
                "required Case metadata is missing",
                {"missing_field": key},
            )
        lines.append("%s: %s" % (key, _front_matter_value(metadata[key])))
    extras = sorted(set(metadata) - set(_REQUIRED_FRONT_MATTER))
    for key in extras:
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
            raise DistributionError(
                "invalid_case_markdown",
                "Case front matter must use 'key: value' lines",
                {"line": stripped},
            )
        key, value = stripped.split(": ", 1)
        if not key or key in metadata:
            raise DistributionError(
                "invalid_case_markdown",
                "Case front matter contains an invalid or duplicate key",
                {"key": key},
            )
        metadata[key] = value
    if body_start is None:
        raise DistributionError("invalid_case_markdown", "Case front matter is not terminated")
    return metadata, "".join(lines[body_start:])


def _metadata(filename: str, subject: str, created_at: str, modified_by: str) -> dict:
    return {
        "case_schema_version": CASE_SCHEMA_VERSION,
        "project_contract_version": PROJECT_CONTRACT_VERSION,
        "record_type": _RECORD_TYPES[filename],
        "subject_id": subject,
        "created_at": created_at,
        "last_updated_at": created_at,
        "last_modified_by": modified_by,
        "runtime_version_if_applicable": DISTRIBUTION_RUNTIME_VERSION,
        "source_classification": _SOURCE_CLASSIFICATION[filename],
        "mutation_policy": _MUTATION_POLICY[filename],
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
            raise DistributionError(
                "invalid_case_payload",
                "analysis_sections must map non-empty labels to non-empty text",
            )
        lines.extend(["### %s" % label.strip(), "", body.strip(), ""])
    return "\n".join(lines).rstrip() + "\n"


def _core_summary(chart, subject: str, analysis: str) -> str:
    project = None if chart.project is None else chart.project.to_dict()
    external = None if chart.external is None else chart.external.to_dict()
    lines = [
        "# 命盤核心摘要",
        "",
        "- Subject ID: `%s`" % subject,
        "- Normalized Natal Identity: `%s`" % chart.identity,
        "- Validation: `%s`" % chart.validation.get("overall_status", "unknown"),
    ]
    if project is not None:
        birth = project.get("birth", {})
        bazi = project.get("bazi", {})
        ziwei = project.get("ziwei", {})
        pillars = bazi.get("pillars", {})
        lines.extend([
            "- Project source: `%s` / maturity=`%s`" % (
                project["source"].get("source_name"), project["source"].get("maturity")
            ),
            "- 出生基礎: `%s`｜`%s`" % (
                birth.get("reported_datetime"), birth.get("resolved_place_label")
            ),
            "- 八字四柱: `%s %s %s %s`" % (
                pillars.get("year", "?"), pillars.get("month", "?"),
                pillars.get("day", "?"), pillars.get("hour", "?"),
            ),
            "- 日主: `%s`" % bazi.get("day_master", "?"),
            "- 紫微命宮／身宮／五行局: `%s` / `%s` / `%s`" % (
                ziwei.get("ming_palace", "?"), ziwei.get("body_palace", "?"),
                ziwei.get("five_element_bureau", "?"),
            ),
        ])
    if external is not None:
        lines.append("- External source: `%s`" % external["source"].get("source_name"))
    lines.append("")
    if analysis:
        lines.append(analysis.rstrip())
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _tracking_body(title: str) -> str:
    return (
        "# %s\n\n"
        "## 紀錄\n\n"
        "%s\n%s\n%s\n" % (title, _RECORDS_START, _EMPTY_RECORDS, _RECORDS_END)
    )


def _render_case_file(filename: str, metadata: Mapping[str, object], body: str) -> str:
    template_name = {
        "00_專案索引.md": "00_project_index.md.tmpl",
        "01_命盤核心摘要.md": "01_natal_core_summary.md.tmpl",
        "02_命盤資料校驗紀錄.md": "02_natal_calibration.md.tmpl",
        "03_八字結構化資料包.md": "03_bazi_structured_facts.md.tmpl",
        "04_紫微基礎資料包.md": "04_ziwei_structured_facts.md.tmpl",
        "05_驗證事件紀錄.md": "05_verified_events.md.tmpl",
        "06_流年追蹤紀錄.md": "06_annual_forecasts.md.tmpl",
        "07_問事追蹤紀錄.md": "07_forecast_questions.md.tmpl",
        "08_重大決策紀錄.md": "08_major_decisions.md.tmpl",
    }[filename]
    template = _load_template(template_name)
    rendered_body = template.format(body=body.rstrip())
    return render_front_matter(metadata) + rendered_body.rstrip() + "\n"


def _index_body(chart, subject: str, materialized, calibration_status: str) -> str:
    project_name = None if chart.project is None else chart.project.source.source_name
    external_name = None if chart.external is None else chart.external.source.source_name
    labels = {
        "00": "專案索引",
        "01": "命盤核心摘要",
        "02": "命盤資料校驗紀錄",
        "03": "八字結構化資料包",
        "04": "紫微基礎資料包",
        "05": "驗證事件紀錄",
        "06": "流年追蹤紀錄",
        "07": "問事追蹤紀錄",
        "08": "重大決策紀錄",
    }
    lines = [
        "# Metaphysics Lab Case｜專案索引",
        "",
        "- Subject ID: `%s`" % subject,
        "- Normalized Natal Identity: `%s`" % chart.identity,
        "- Project source: `%s`" % (project_name or "none"),
        "- External source: `%s`" % (external_name or "none"),
        "- Case lifecycle: `progressive`",
        "",
        "## Case Files",
        "",
    ]
    present = set(materialized)
    for filename in CASE_FILES:
        prefix = filename[:2]
        marker = "✓" if filename in present else "○"
        lines.append("- %s %s %s" % (marker, prefix, labels[prefix]))
    lines.extend([
        "",
        "## Historical Calibration",
        "",
        "Historical Calibration: `%s`" % calibration_status,
        "",
    ])
    return "\n".join(lines)


def export_case_markdown(payload: Mapping[str, object]) -> dict:
    payload = _mapping(payload, "payload")
    chart = _normalized_model(payload.get("normalized_natal"))
    subject = _subject_id(payload.get("subject_id"))
    generated_at = _timestamp(payload.get("generated_at"), "generated_at")
    modified_by = _text(payload.get("last_modified_by", "ai"), "last_modified_by")
    generated_date = datetime.fromisoformat(generated_at).date()
    analysis = _analysis_section(payload.get("analysis_sections"))

    bodies = {
        "00_專案索引.md": _index_body(chart, subject, BASE_CASE_FILES, "uncalibrated"),
        "01_命盤核心摘要.md": _core_summary(chart, subject, analysis),
        "02_命盤資料校驗紀錄.md": export_calibration_markdown(chart, generated_date),
        "03_八字結構化資料包.md": export_bazi_markdown(chart, generated_date),
        "04_紫微基礎資料包.md": export_ziwei_markdown(chart, generated_date),
    }
    files = {}
    for filename in BASE_CASE_FILES:
        files[filename] = _render_case_file(
            filename,
            _metadata(filename, subject, generated_at, modified_by),
            bodies[filename],
        )
    return {"subject_id": subject, "files": files}


def _case_files(value: object) -> Mapping[str, str]:
    raw = _mapping(value, "case_files")
    keys = set(raw)
    unknown = keys - set(CASE_FILES)
    missing_base = set(BASE_CASE_FILES) - keys
    if unknown or missing_base:
        raise DistributionError(
            "case_file_set_mismatch",
            "Case pack must contain all base files and only canonical Case filenames",
            {"missing_base": sorted(missing_base), "unknown": sorted(str(item) for item in unknown)},
        )
    if any(not isinstance(raw[name], str) for name in raw):
        raise DistributionError("invalid_case_markdown", "all Case file contents must be text")
    return raw


def _manifest_expected_line(filename: str, present: bool) -> str:
    labels = {
        "00": "專案索引", "01": "命盤核心摘要", "02": "命盤資料校驗紀錄",
        "03": "八字結構化資料包", "04": "紫微基礎資料包", "05": "驗證事件紀錄",
        "06": "流年追蹤紀錄", "07": "問事追蹤紀錄", "08": "重大決策紀錄",
    }
    return "- %s %s %s" % ("✓" if present else "○", filename[:2], labels[filename[:2]])


def _validate_manifest(files: Mapping[str, str]) -> None:
    _, body = parse_front_matter(files["00_專案索引.md"])
    for filename in CASE_FILES:
        expected = _manifest_expected_line(filename, filename in files)
        if expected not in body:
            raise DistributionError(
                "case_manifest_mismatch",
                "00 Case manifest does not match materialized files",
                {"filename": filename, "expected_line": expected},
            )


def validate_case(payload: Mapping[str, object]) -> dict:
    payload = _mapping(payload, "payload")
    files = _case_files(payload.get("case_files"))
    subject = None
    versions = set()
    contracts = set()
    for filename in CASE_FILES:
        if filename not in files:
            continue
        metadata, _ = parse_front_matter(files[filename])
        missing = [key for key in _REQUIRED_FRONT_MATTER if key not in metadata]
        if missing:
            raise DistributionError(
                "invalid_case_metadata",
                "Case file is missing required metadata",
                {"filename": filename, "missing_fields": missing},
            )
        if metadata["record_type"] != _RECORD_TYPES[filename]:
            raise DistributionError(
                "case_record_type_mismatch",
                "Case filename and record_type do not match",
                {"filename": filename, "record_type": metadata["record_type"]},
            )
        versions.add(metadata["case_schema_version"])
        contracts.add(metadata["project_contract_version"])
        current_subject = metadata["subject_id"]
        if subject is None:
            subject = current_subject
        elif current_subject != subject:
            raise DistributionError(
                "case_subject_mismatch",
                "all Case files must belong to the same subject_id",
                {"filename": filename, "expected_subject_id": subject, "actual_subject_id": current_subject},
            )

    if len(versions) != 1 or len(contracts) != 1:
        raise DistributionError(
            "case_version_mismatch",
            "all Case files must use one schema and contract version",
            {"case_schema_versions": sorted(versions), "project_contract_versions": sorted(contracts)},
        )
    schema = next(iter(versions))
    contract = next(iter(contracts))
    if schema == "1.0":
        if set(files) != set(CASE_FILES) or contract != "1.0":
            raise DistributionError(
                "case_schema_incompatible",
                "legacy Case schema 1.0 requires the complete nine-file contract 1.0 pack",
            )
    elif schema == CASE_SCHEMA_VERSION:
        if contract != PROJECT_CONTRACT_VERSION:
            raise DistributionError(
                "case_contract_incompatible",
                "Case Project Contract version is not supported by this runtime",
                {"project_contract_version": contract},
            )
        _validate_manifest(files)
    else:
        raise DistributionError(
            "case_schema_incompatible",
            "Case schema version is not supported by this runtime",
            {"case_schema_version": schema},
        )
    return {
        "status": "compatible",
        "subject_id": subject,
        "case_schema_version": schema,
        "project_contract_version": contract,
        "validated_files": [name for name in CASE_FILES if name in files],
    }


def migrate_case(payload: Mapping[str, object]) -> dict:
    files = _case_files(_mapping(payload, "payload").get("case_files"))
    validation = validate_case({"case_files": files})
    return {
        "status": validation["status"],
        "migration": "no_change",
        "changed_files": {},
        "subject_id": validation["subject_id"],
        "case_schema_version": validation["case_schema_version"],
    }


def _render_entry(entry: Mapping[str, object]) -> str:
    record_id = _text(entry.get("record_id"), "entry.record_id")
    payload = json.dumps(dict(entry), ensure_ascii=False, sort_keys=True, indent=2)
    return "### %s\n\n```json\n%s\n```" % (record_id, payload)


def _append_record(body: str, entry_text: str) -> str:
    start = body.find(_RECORDS_START)
    end = body.find(_RECORDS_END)
    if start < 0 or end < 0 or end <= start:
        raise DistributionError(
            "invalid_case_markdown",
            "tracking Case file is missing record boundary markers",
        )
    content_start = start + len(_RECORDS_START)
    current = body[content_start:end].strip()
    updated = entry_text if current == _EMPTY_RECORDS or not current else current + "\n\n" + entry_text
    return body[:content_start] + "\n" + updated + "\n" + body[end:]


def _set_index_materialized(index_text: str, filename: str, updated_at: str, modified_by: str) -> str:
    metadata, body = parse_front_matter(index_text)
    absent = _manifest_expected_line(filename, False)
    present = _manifest_expected_line(filename, True)
    if present not in body:
        if absent not in body:
            raise DistributionError("case_manifest_mismatch", "00 Case manifest is missing target file state")
        body = body.replace(absent, present, 1)
    metadata["last_updated_at"] = updated_at
    metadata["last_modified_by"] = modified_by
    return render_front_matter(metadata) + body.rstrip() + "\n"


def set_case_calibration_status(
    index_text: str,
    status: str,
    updated_at: str,
    modified_by: str,
) -> str:
    if status not in _CALIBRATION_STATES:
        raise DistributionError(
            "invalid_calibration_status",
            "unsupported historical calibration status",
            {"status": status},
        )
    metadata, body = parse_front_matter(index_text)
    body, count = re.subn(
        r"Historical Calibration: `(?:uncalibrated|basic|calibrated)`",
        "Historical Calibration: `%s`" % status,
        body,
        count=1,
    )
    if count != 1:
        raise DistributionError("case_manifest_mismatch", "00 Case manifest is missing calibration status")
    metadata["last_updated_at"] = updated_at
    metadata["last_modified_by"] = modified_by
    return render_front_matter(metadata) + body.rstrip() + "\n"


def _validate_05_entry(entry: Mapping[str, object]) -> None:
    if entry.get("status") == "verified":
        return
    if entry.get("record_type") != "historical_calibration":
        raise DistributionError(
            "invalid_verified_event",
            "05 accepts verified events or historical calibration ledger records only",
        )
    blind = entry.get("blind_prediction")
    evaluation = entry.get("evaluation")
    if not isinstance(blind, Mapping) or blind.get("classification") != "命理推論":
        raise DistributionError("invalid_verified_event", "historical calibration blind prediction classification is invalid")
    if not isinstance(evaluation, Mapping) or evaluation.get("classification") != "已校驗資料":
        raise DistributionError("invalid_verified_event", "historical calibration evaluation classification is invalid")
    actual = entry.get("user_confirmed_actual")
    if actual is not None:
        if not isinstance(actual, Mapping) or actual.get("classification") != "已驗證事件":
            raise DistributionError("invalid_verified_event", "historical calibration actual-event classification is invalid")


def update_case_record(payload: Mapping[str, object]) -> dict:
    payload = _mapping(payload, "payload")
    files = _case_files(payload.get("case_files"))
    validation = validate_case({"case_files": files})
    if validation["case_schema_version"] == "1.0":
        legacy = True
    else:
        legacy = False
    filename = _text(payload.get("filename"), "filename")
    if filename not in _TRACKING_FILES:
        raise DistributionError(
            "immutable_case_record",
            "incremental Case updates are allowed only for tracking files 05-08",
            {"filename": filename},
        )
    operation = _text(payload.get("operation"), "operation")
    if operation == "replace_blind_forecast" and filename in (
        "06_流年追蹤紀錄.md",
        "07_問事追蹤紀錄.md",
    ):
        raise DistributionError(
            "immutable_blind_forecast",
            "recorded first-version blind forecast cannot be replaced",
            {"filename": filename},
        )
    if operation != "append":
        raise DistributionError(
            "unsupported_case_mutation",
            "unsupported Case mutation operation",
            {"operation": operation},
        )
    entry = _mapping(payload.get("entry"), "entry")
    if filename == "05_驗證事件紀錄.md":
        _validate_05_entry(entry)
    updated_at = _timestamp(payload.get("updated_at"), "updated_at")
    modified_by = _text(payload.get("last_modified_by", "ai"), "last_modified_by")

    changed = {}
    if filename in files:
        metadata, body = parse_front_matter(files[filename])
    else:
        if legacy:
            raise DistributionError("case_file_set_mismatch", "legacy Case is missing required tracking file")
        index_metadata, _ = parse_front_matter(files["00_專案索引.md"])
        metadata = _metadata(filename, validation["subject_id"], index_metadata["created_at"], modified_by)
        body = _tracking_body({
            "05_驗證事件紀錄.md": "驗證事件紀錄",
            "06_流年追蹤紀錄.md": "流年追蹤紀錄",
            "07_問事追蹤紀錄.md": "問事追蹤紀錄",
            "08_重大決策紀錄.md": "重大決策紀錄",
        }[filename])
        changed["00_專案索引.md"] = _set_index_materialized(
            files["00_專案索引.md"], filename, updated_at, modified_by
        )

    metadata["last_updated_at"] = updated_at
    metadata["last_modified_by"] = modified_by
    updated_body = _append_record(body, _render_entry(entry))
    changed[filename] = _render_case_file(filename, metadata, updated_body)
    return {"subject_id": validation["subject_id"], "changed_files": changed}
