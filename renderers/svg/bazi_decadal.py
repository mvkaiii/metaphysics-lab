"""Static, deterministic renderers for the validated Bazi decadal chart."""

from __future__ import annotations

from html import escape
import textwrap
from typing import Any, Mapping

from engine.visualization.contract import validate_chart


_AUTHORITY_LABELS = {
    "original_chart_fact": "Original chart fact",
    "verified_data": "Verified data",
    "project_derived": "Project-derived",
    "verified_event": "Verified event",
    "metaphysical_inference": "Metaphysical inference",
    "research_hypothesis": "Research hypothesis",
    "current_real_world_context": "Current real-world context",
}


def _validated(chart: Mapping[str, Any]) -> dict:
    errors = validate_chart(chart)
    if errors:
        raise ValueError("chart failed validation: %s" % "; ".join(errors))
    return dict(chart)


def _xml_text(value: Any) -> str:
    return escape(str(value), quote=True)


def _xml_attr(value: Any) -> str:
    return escape(str(value), quote=True)


def _lines(value: Any, width: int = 120) -> list[str]:
    return textwrap.wrap(str(value), width=width, break_long_words=False, break_on_hyphens=False) or [""]


def _experimental(chart: Mapping[str, Any]) -> bool:
    return any(
        isinstance(capability, Mapping) and capability.get("maturity") == "experimental"
        for capability in chart.get("source_capabilities", [])
    )


def _authority_label(chart: Mapping[str, Any], refs: Mapping[str, Any]) -> str:
    labels = []
    authorities = chart.get("authorities", {})
    for field in sorted(refs):
        for authority_id in refs[field]:
            authority = authorities.get(authority_id, {})
            label = _AUTHORITY_LABELS.get(authority.get("classification"), "Unknown authority")
            if label not in labels:
                labels.append(label)
    return ", ".join(labels) or "No authority reference"


def render_bazi_decadal_svg(chart: Mapping[str, Any]) -> str:
    """Render a validated chart without recalculating or fetching anything."""

    chart = _validated(chart)
    context = chart["view_context"]
    status = chart["status"]
    periods = chart["data"]["periods"] if status == "ready" else []
    height = 220 + max(len(periods), 1) * 76 + len(chart["limitations"]) * 24
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="chart-title chart-desc" '
        'width="1200" height="%s" viewBox="0 0 1200 %s">' % (height, height),
        '<title id="chart-title">Bazi decadal timeline</title>',
        '<desc id="chart-desc">Validated Metaphysics Lab visualization contract output.</desc>',
        '<rect x="0" y="0" width="1200" height="%s" fill="white" />' % height,
        '<text x="32" y="38" class="title">Bazi decadal timeline</text>',
        '<text x="32" y="64" class="status">Status: %s</text>' % _xml_text(status),
    ]
    if _experimental(chart):
        parts.append('<text x="240" y="64" class="maturity">E / Experimental</text>')
    parts.append(
        '<text x="32" y="90" class="context">as_of: %s | timezone: %s | visibility: %s</text>'
        % (_xml_text(context["as_of"]), _xml_text(context["timezone"]), _xml_text(context["visibility_mode"]))
    )
    if status == "unsupported":
        parts.append('<text x="32" y="126" class="reason">Unsupported reason_codes: %s</text>' % _xml_text(", ".join(chart["reason_codes"])))
        y = 158
    else:
        data = chart["data"]
        parts.append('<text x="32" y="126" class="basis">Age basis: %s | interval: %s</text>' % (_xml_text(data["age_basis"]["id"]), _xml_text(data["time_basis"]["interval_convention"])))
        parts.append('<text x="32" y="150" class="current">Current period: %s</text>' % _xml_text(data["current_period_id"] or "none in range"))
        y = 184
        for period in periods:
            current = period["id"] == chart["data"]["current_period_id"]
            marker = "CURRENT" if current else ""
            parts.extend(
                [
                    '<g id="%s" class="period">' % _xml_attr(period["id"]),
                    '<rect x="32" y="%s" width="1136" height="64" fill="%s" stroke="#666" />' % (y, "#eef6ff" if current else "#fafafa"),
                    '<text x="48" y="%s" class="period-label">Period %s: %s %s</text>' % (y + 20, _xml_text(period["index"]), _xml_text(period["pillar"]), _xml_text(marker)),
                    '<text x="48" y="%s" class="period-range">age %s–%s | %s → %s</text>' % (y + 39, _xml_text(period["age_start_years"]), _xml_text(period["age_end_years"]), _xml_text(period["start_at"]), _xml_text(period["end_at"])),
                    '<text x="760" y="%s" class="authority">Authority: %s</text>' % (y + 29, _xml_text(_authority_label(chart, period["authority_refs"]))),
                    '</g>',
                ]
            )
            y += 76
    for limitation in chart["limitations"]:
        for line in _lines("%s: %s" % (limitation["code"], limitation["message"])):
            parts.append('<text x="32" y="%s" class="limitation">%s</text>' % (y, _xml_text(line)))
            y += 22
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def render_bazi_decadal_text(chart: Mapping[str, Any]) -> str:
    """Render a plain-text alternative preserving status and limitations."""

    chart = _validated(chart)
    context = chart["view_context"]
    lines = [
        "Bazi decadal timeline",
        "Status: %s" % chart["status"],
        "as_of: %s | timezone: %s | visibility: %s" % (context["as_of"], context["timezone"], context["visibility_mode"]),
    ]
    if _experimental(chart):
        lines.append("Maturity: E / Experimental")
    if chart["status"] == "unsupported":
        lines.append("Reason codes: %s" % ", ".join(chart["reason_codes"]))
    else:
        data = chart["data"]
        lines.extend(
            [
                "Age basis: %s" % data["age_basis"]["id"],
                "Interval: %s" % data["time_basis"]["interval_convention"],
                "Current period: %s" % (data["current_period_id"] or "none in range"),
            ]
        )
        for period in data["periods"]:
            lines.append(
                "Period %s: %s | age %s-%s | %s -> %s | Authority: %s"
                % (
                    period["index"], period["pillar"], period["age_start_years"], period["age_end_years"],
                    period["start_at"], period["end_at"], _authority_label(chart, period["authority_refs"]),
                )
            )
    lines.append("Limitations:")
    for limitation in chart["limitations"]:
        lines.append("- %s: %s" % (limitation["code"], limitation["message"]))
    return "\n".join(lines) + "\n"
