"""Deterministic SVG/text renderer for Candidate Envelope summary charts."""

from __future__ import annotations

from html import escape
from typing import Mapping


def _text(value: object) -> str:
    return escape(str(value), quote=True)


def render_candidate_envelope_svg(chart: Mapping[str, object]) -> str:
    if not isinstance(chart, Mapping) or chart.get("chart_type") != "candidate_envelope_summary":
        raise ValueError("candidate envelope summary chart is required")
    spans = chart.get("candidate_spans")
    coverage = chart.get("coverage")
    if not isinstance(spans, list) or not isinstance(coverage, Mapping):
        raise ValueError("candidate envelope summary chart is malformed")

    row_height = 34
    height = 250 + row_height * len(spans)
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="%d" viewBox="0 0 960 %d">' % (height, height),
        '<rect x="0" y="0" width="960" height="%d" fill="white"/>' % height,
        '<text x="32" y="42" font-size="24" font-family="sans-serif">Candidate Envelope｜候選盤摘要</text>',
        '<text x="32" y="72" font-size="14" font-family="sans-serif">Experimental presentation only · no candidate ranking or probability</text>',
        '<text x="32" y="104" font-size="16" font-family="sans-serif">precision: %s · local-time: %s</text>' % (
            _text(chart.get("natal_precision_state")),
            _text(chart.get("local_time_resolution")),
        ),
        '<text x="32" y="132" font-size="16" font-family="sans-serif">coverage: %s · legal %s · materialized %s · unresolved %s · states %s</text>' % (
            _text(coverage.get("status")),
            _text(coverage.get("legal_occurrence_count")),
            _text(coverage.get("materialized_occurrence_count")),
            _text(coverage.get("unresolved_occurrence_count")),
            _text(coverage.get("material_state_count")),
        ),
        '<text x="32" y="168" font-size="16" font-family="sans-serif">候選盤時間區間（僅時間順序，不代表優先級）</text>',
    ]
    y = 198
    for span in spans:
        if not isinstance(span, Mapping):
            raise ValueError("candidate span must be an object")
        label = "%s  %s–%s  occurrences=%s" % (
            span.get("candidate_id"),
            span.get("reported_time_start"),
            span.get("reported_time_end"),
            span.get("occurrence_count"),
        )
        lines.append(
            '<text class="candidate-span" x="48" y="%d" font-size="15" font-family="monospace">%s</text>'
            % (y, _text(label))
        )
        y += row_height

    fact_counts = chart.get("fact_counts")
    if isinstance(fact_counts, Mapping):
        y += 4
        inv = fact_counts.get("invariant", {})
        var = fact_counts.get("variant", {})
        und = fact_counts.get("undetermined", {})
        lines.append(
            '<text x="32" y="%d" font-size="14" font-family="sans-serif">facts · invariant Bazi/Ziwei %s/%s · variant %s/%s · undetermined %s/%s</text>'
            % (
                y,
                _text(inv.get("bazi") if isinstance(inv, Mapping) else None),
                _text(inv.get("ziwei") if isinstance(inv, Mapping) else None),
                _text(var.get("bazi") if isinstance(var, Mapping) else None),
                _text(var.get("ziwei") if isinstance(var, Mapping) else None),
                _text(und.get("bazi") if isinstance(und, Mapping) else None),
                _text(und.get("ziwei") if isinstance(und, Mapping) else None),
            )
        )

    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def render_candidate_envelope_text(chart: Mapping[str, object]) -> str:
    if not isinstance(chart, Mapping) or chart.get("chart_type") != "candidate_envelope_summary":
        raise ValueError("candidate envelope summary chart is required")
    coverage = chart.get("coverage")
    spans = chart.get("candidate_spans")
    if not isinstance(coverage, Mapping) or not isinstance(spans, list):
        raise ValueError("candidate envelope summary chart is malformed")

    lines = [
        "Candidate Envelope｜候選盤摘要",
        "Experimental presentation only; no candidate ranking, probability, or selection authority.",
        "出生時間狀態：%s" % chart.get("natal_precision_state"),
        "本地時間解析：%s" % chart.get("local_time_resolution"),
        "覆蓋：%s；legal=%s；materialized=%s；unresolved=%s；material_states=%s"
        % (
            coverage.get("status"),
            coverage.get("legal_occurrence_count"),
            coverage.get("materialized_occurrence_count"),
            coverage.get("unresolved_occurrence_count"),
            coverage.get("material_state_count"),
        ),
        "候選盤時間區間（僅時間順序，不代表優先級）：",
    ]
    for span in spans:
        if not isinstance(span, Mapping):
            raise ValueError("candidate span must be an object")
        lines.append(
            "- %s｜%s–%s｜occurrences=%s"
            % (
                span.get("candidate_id"),
                span.get("reported_time_start"),
                span.get("reported_time_end"),
                span.get("occurrence_count"),
            )
        )

    reasons = chart.get("reason_codes", [])
    if reasons:
        lines.append("限制碼：" + ", ".join(str(item) for item in reasons))
    blocked = chart.get("blocked_analysis", [])
    if blocked:
        lines.append("目前阻塞：" + ", ".join(str(item) for item in blocked))
    return "\n".join(lines) + "\n"
