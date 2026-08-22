from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import date
from pathlib import Path
from typing import Any, Iterable, List, Tuple

from engine.ziwei.common import PALACE_NAMES
from engine.ziwei.star_catalog import AUXILIARY_STARS, MAJOR_STARS

from .errors import NatalFoundationError
from .models import NatalSource, NormalizedNatalChart, ResolvedField


_TEMPLATE_ROOT = Path(__file__).resolve().parents[2] / "templates" / "natal"
_PILLAR_ORDER = ("year", "month", "day", "hour")
_STAR_ORDER = MAJOR_STARS + AUXILIARY_STARS
_TRANSFORMATION_ORDER = ("祿", "權", "科", "忌")


def _invalid(message: str) -> NatalFoundationError:
    return NatalFoundationError("invalid_natal_export", message)


def _jsonable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return [_jsonable(item) for item in sorted(value, key=repr)]
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return _jsonable(to_dict())
    return value


def _format_value(value: Any) -> str:
    if isinstance(value, str):
        rendered = value
    elif value is None:
        rendered = "null"
    elif isinstance(value, (int, float, bool)):
        rendered = json.dumps(value, ensure_ascii=False, sort_keys=True)
    else:
        rendered = json.dumps(_jsonable(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return rendered.replace("|", "\\|").replace("\n", " ")


def _index_or_tail(values: Tuple[str, ...], value: str) -> int:
    try:
        return values.index(value)
    except ValueError:
        return len(values)


def _field_sort_key(field: ResolvedField) -> Tuple[Any, ...]:
    path = field.path
    parts = path.split(".")
    domain = parts[0] if parts else ""
    domain_rank = {"birth": 0, "bazi": 1, "ziwei": 2}.get(domain, 9)

    if domain == "bazi":
        if len(parts) >= 3 and parts[1] == "pillars":
            return (domain_rank, 0, _index_or_tail(_PILLAR_ORDER, parts[2]), tuple(parts[3:]))
        return (domain_rank, 9, path)

    if domain == "ziwei":
        if len(parts) == 2 and parts[1] in ("ming_palace", "body_palace", "five_element_bureau"):
            core_order = ("ming_palace", "body_palace", "five_element_bureau")
            return (domain_rank, 0, core_order.index(parts[1]))
        if len(parts) >= 4 and parts[1] == "palaces":
            palace = parts[2]
            return (domain_rank, 1, _index_or_tail(PALACE_NAMES, palace), palace, tuple(parts[3:]))
        if len(parts) >= 4 and parts[1] == "stars":
            star = parts[2]
            return (domain_rank, 2, _index_or_tail(_STAR_ORDER, star), star, tuple(parts[3:]))
        if len(parts) >= 3 and parts[1] == "birth_transformations":
            kind = parts[2]
            return (domain_rank, 3, _index_or_tail(_TRANSFORMATION_ORDER, kind), kind, tuple(parts[3:]))
        return (domain_rank, 9, path)

    return (domain_rank, path)


def _ordered_fields(fields: Iterable[ResolvedField]) -> List[ResolvedField]:
    return sorted(fields, key=_field_sort_key)


def _source_summary(source: NatalSource) -> str:
    return (
        "- {source_type}｜{source_name}｜version={source_version}｜"
        "profile={rule_profile}｜rule={rule_version}｜maturity={maturity}｜validation={validation_status}"
    ).format(**source.to_dict())


def _render_sources(chart: NormalizedNatalChart) -> str:
    lines = []
    if chart.external is not None:
        lines.append(_source_summary(chart.external.source))
    if chart.project is not None:
        lines.append(_source_summary(chart.project.source))
    if not lines:
        return "- 未提供來源。"
    return "\n".join(lines)


def _render_classification(chart: NormalizedNatalChart) -> str:
    classification = chart.provenance.get("classification")
    if classification is None:
        return "- 未提供資料分類。"
    return "- %s" % _format_value(classification)


def _render_engine_profile(chart: NormalizedNatalChart) -> str:
    lines = []
    if chart.external is not None:
        source = chart.external.source
        lines.append(
            "- External：{name}｜Profile={profile}｜Rule Version={rule}".format(
                name=source.source_name,
                profile=source.rule_profile,
                rule=source.rule_version,
            )
        )
    if chart.project is not None:
        source = chart.project.source
        lines.append(
            "- Project：{name}｜Profile={profile}｜Rule Version={rule}".format(
                name=source.source_name,
                profile=source.rule_profile,
                rule=source.rule_version,
            )
        )
    if not lines:
        return "- 未提供 Engine / Profile / Rule Version。"
    return "\n".join(lines)


def _render_birth_data(chart: NormalizedNatalChart) -> str:
    fields = _ordered_fields(field for field in chart.resolved.fields if field.path.startswith("birth."))
    if not fields:
        return "無可輸出的出生欄位。"
    lines = ["| Path | Value | Source |", "| --- | --- | --- |"]
    for field in fields:
        lines.append(
            "| {path} | {value} | {source} |".format(
                path=field.path,
                value=_format_value(field.selected_value),
                source=field.selected_source,
            )
        )
    return "\n".join(lines)


def _has_blocking_time_conflict(chart: NormalizedNatalChart) -> bool:
    validation_status = chart.validation.get("time_profile_status")
    validation_severity = chart.validation.get("time_profile_severity")
    if validation_status == "CONFLICT" and validation_severity == "BLOCKING":
        return True
    return any(
        field.path.startswith("birth.")
        and field.status == "CONFLICT"
        and field.severity == "BLOCKING"
        for field in chart.resolved.fields
    )


def _has_time_basis(chart: NormalizedNatalChart) -> bool:
    if chart.project is not None and bool(chart.project.time_basis):
        return True
    return any(
        token in field.path
        for field in chart.resolved.fields
        for token in ("time", "hour_branch", "adjustment_minutes")
        if field.path.startswith("birth.")
    )


def _render_time_summary(chart: NormalizedNatalChart) -> str:
    if _has_blocking_time_conflict(chart):
        return "出生時間校正跨越命理邊界；請查看「排盤差異」區塊。"
    if _has_time_basis(chart):
        return "已完成出生地時間校正，未造成時辰／核心盤面變更。"
    return "未提供時間校正資料。"


def _render_reconciliation(chart: NormalizedNatalChart) -> str:
    fields = _ordered_fields(chart.resolved.fields)
    if not fields:
        return "無可比較欄位。"
    lines = [
        "| Path | Status | Severity | Selected | Reason |",
        "| --- | --- | --- | --- | --- |",
    ]
    for field in fields:
        lines.append(
            "| {path} | {status} | {severity} | {selected} | {reason} |".format(
                path=field.path,
                status=field.status,
                severity=field.severity,
                selected=field.selected_source,
                reason=field.reason,
            )
        )
    return "\n".join(lines)


def _render_formal_fields(chart: NormalizedNatalChart, scope: str) -> str:
    if scope == "bazi":
        selected = [field for field in chart.resolved.fields if field.path.startswith("bazi.")]
    elif scope == "ziwei":
        selected = [field for field in chart.resolved.fields if field.path.startswith("ziwei.")]
    elif scope == "calibration":
        selected = list(chart.resolved.fields)
    else:
        raise _invalid("unknown export scope: %s" % scope)

    fields = _ordered_fields(selected)
    if not fields:
        return "無可輸出的正式欄位。"
    lines = ["| Path | Resolved Value | Source |", "| --- | --- | --- |"]
    for field in fields:
        lines.append(
            "| {path} | {value} | {source} |".format(
                path=field.path,
                value=_format_value(field.selected_value),
                source=field.selected_source,
            )
        )
    return "\n".join(lines)


def _render_provenance(chart: NormalizedNatalChart) -> str:
    if not chart.provenance:
        return "- 未提供 provenance。"
    lines = []
    for key in sorted(chart.provenance.keys(), key=str):
        lines.append("- %s: %s" % (key, _format_value(chart.provenance[key])))
    return "\n".join(lines)


def _load_template(filename: str) -> str:
    path = _TEMPLATE_ROOT / filename
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise _invalid("canonical natal template unavailable: %s" % filename) from exc


def _export(chart: NormalizedNatalChart, generated_date: date, *, scope: str, template_name: str) -> str:
    if not isinstance(chart, NormalizedNatalChart):
        raise _invalid("chart must be NormalizedNatalChart")
    if not isinstance(generated_date, date):
        raise _invalid("generated_date must be datetime.date")

    template = _load_template(template_name)
    rendered = template.format(
        generated_date=generated_date.isoformat(),
        identity=chart.identity,
        sources=_render_sources(chart),
        classification=_render_classification(chart),
        engine_profile=_render_engine_profile(chart),
        birth_data=_render_birth_data(chart),
        time_summary=_render_time_summary(chart),
        reconciliation=_render_reconciliation(chart),
        formal_fields=_render_formal_fields(chart, scope),
        provenance=_render_provenance(chart),
    )
    return rendered.rstrip() + "\n"


def export_bazi_markdown(chart: NormalizedNatalChart, generated_date: date) -> str:
    return _export(chart, generated_date, scope="bazi", template_name="bazi_data_pack.md.tmpl")


def export_ziwei_markdown(chart: NormalizedNatalChart, generated_date: date) -> str:
    return _export(chart, generated_date, scope="ziwei", template_name="ziwei_data_pack.md.tmpl")


def export_calibration_markdown(chart: NormalizedNatalChart, generated_date: date) -> str:
    return _export(chart, generated_date, scope="calibration", template_name="calibration_record.md.tmpl")
