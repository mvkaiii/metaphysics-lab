"""Partial Base Case renderer for natal candidate envelopes.

Candidate envelopes are not converted into a fake NormalizedNatalChart. This module
renders the same Case Schema 1.1 identity/filename contract while keeping invariant,
variant, and blocked conclusions explicit.
"""

from __future__ import annotations

import json
import re
from typing import Mapping

from engine.natal.candidates import classify_candidate_facts

from .case_pack import (
    BASE_CASE_FILES,
    CASE_FILES,
    _identity_from_payload,
    _manifest_expected_line,
    _metadata,
    _render_case_file,
    _text,
    _timestamp,
    canonical_case_filename,
)
from .errors import DistributionError


_REQUIRED_PARTIAL_BLOCKS = frozenset((
    "unique_birth_time_claim",
    "unique_hour_pillar_conclusion",
    "unique_ziwei_natal_conclusion",
    "single_chart_personalized_forecast",
))

_KNOWN_FACT_FIELDS = frozenset((
    "sex",
    "birth_date",
    "birth_place",
    "resolved_place_label",
    "timezone",
    "reported_birth_time",
    "reported_birth_time_range",
))
_TEXT_KNOWN_FACT_FIELDS = frozenset((
    "sex", "birth_date", "birth_place", "resolved_place_label", "timezone",
))
_TIME_TEXT_PATTERN = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


def _valid_time_text(value: object) -> bool:
    return isinstance(value, str) and bool(_TIME_TEXT_PATTERN.fullmatch(value))


def _time_minutes(value: str) -> int:
    hour, minute = value.split(":", 1)
    return int(hour) * 60 + int(minute)


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise DistributionError("invalid_case_payload", "%s must be a structured mapping" % field, {"field": field})
    return value


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)


def _list_lines(values) -> list:
    if not isinstance(values, (list, tuple)):
        return ["- none"]
    return ["- `%s`" % str(item) for item in values] or ["- none"]


def _validate_envelope(value: object) -> dict:
    raw = dict(_mapping(value, "candidate_envelope"))
    precision = raw.get("natal_precision_state")
    if precision not in ("bounded", "unknown_time"):
        raise DistributionError(
            "invalid_candidate_envelope",
            "partial Case requires a bounded or unknown_time candidate envelope",
            {"natal_precision_state": precision},
        )
    candidate_count = raw.get("candidate_count")
    candidates = raw.get("candidates")
    if type(candidate_count) is not int or candidate_count < 1 or not isinstance(candidates, list) or len(candidates) != candidate_count:
        raise DistributionError("invalid_candidate_envelope", "candidate_count must be a true integer matching the candidate list")
    for field in (
        "known_facts", "invariant_bazi_facts", "variant_bazi_facts",
        "invariant_ziwei_facts", "variant_ziwei_facts", "provenance",
    ):
        if not isinstance(raw.get(field), Mapping):
            raise DistributionError("invalid_candidate_envelope", "%s must be a mapping" % field, {"field": field})
    known = raw["known_facts"]
    unexpected_known = sorted(set(known) - _KNOWN_FACT_FIELDS)
    if unexpected_known:
        raise DistributionError(
            "invalid_candidate_envelope",
            "known_facts contains candidate-dependent or unsupported fields",
            {"unexpected_known_facts": unexpected_known},
        )
    for field in _TEXT_KNOWN_FACT_FIELDS:
        if field in known:
            item = known[field]
            if not isinstance(item, str) or not item.strip():
                raise DistributionError(
                    "invalid_candidate_envelope",
                    "known_facts text fields must contain non-empty text",
                    {"field": field},
                )
    reported_time = known.get("reported_birth_time")
    if reported_time is not None and not _valid_time_text(reported_time):
        raise DistributionError(
            "invalid_candidate_envelope",
            "reported_birth_time must be valid HH:MM text or null",
            {"reported_birth_time": reported_time},
        )
    if reported_time is not None:
        raise DistributionError(
            "invalid_candidate_envelope",
            "partial Case cannot claim one exact reported birth time",
            {"reported_birth_time": reported_time},
        )
    reported_range = known.get("reported_birth_time_range")
    if reported_range is not None:
        if not isinstance(reported_range, (list, tuple)) or len(reported_range) != 2 or any(
            not _valid_time_text(item) for item in reported_range
        ):
            raise DistributionError(
                "invalid_candidate_envelope",
                "reported_birth_time_range must be two valid HH:MM values or null",
            )
        if _time_minutes(reported_range[1]) < _time_minutes(reported_range[0]):
            raise DistributionError(
                "invalid_candidate_envelope",
                "reported_birth_time_range cannot cross the civil-date boundary in v1",
            )
    if precision == "unknown_time" and reported_range is not None:
        raise DistributionError(
            "invalid_candidate_envelope",
            "unknown_time candidate envelope cannot claim a reported birth-time range",
        )
    if precision == "bounded" and reported_range is None:
        raise DistributionError(
            "invalid_candidate_envelope",
            "bounded candidate envelope requires a two-value reported birth-time range",
        )
    for field in ("allowed_analysis", "blocked_analysis", "boundary_ambiguities"):
        if not isinstance(raw.get(field), list):
            raise DistributionError("invalid_candidate_envelope", "%s must be a list" % field, {"field": field})
    allowed = raw["allowed_analysis"]
    blocked = raw["blocked_analysis"]
    for field, scopes in (("allowed_analysis", allowed), ("blocked_analysis", blocked)):
        if any(not isinstance(item, str) or not item.strip() or item != item.strip() for item in scopes):
            raise DistributionError(
                "invalid_candidate_envelope",
                "%s must contain canonical non-empty string scope identifiers" % field,
                {"field": field},
            )
    overlap = sorted(set(allowed) & set(blocked))
    if overlap:
        raise DistributionError(
            "invalid_candidate_envelope",
            "allowed_analysis and blocked_analysis must be mutually exclusive",
            {"overlapping_analysis": overlap},
        )
    missing_blocks = sorted(_REQUIRED_PARTIAL_BLOCKS - set(blocked))
    if missing_blocks:
        raise DistributionError(
            "invalid_candidate_envelope",
            "partial Case candidate envelope must keep unique-chart scopes blocked",
            {"missing_blocked_analysis": missing_blocks},
        )
    if raw["provenance"].get("midpoint_used") is not False or raw["provenance"].get("default_time_used") is not False:
        raise DistributionError("invalid_candidate_envelope", "partial Case cannot accept midpoint/default-time candidate provenance")
    if any(not isinstance(item, Mapping) for item in candidates):
        raise DistributionError("invalid_candidate_envelope", "candidate entries must be structured mappings")
    try:
        classified = classify_candidate_facts(candidates)
    except (KeyError, TypeError, ValueError) as exc:
        raise DistributionError("invalid_candidate_envelope", "candidate facts cannot be classified") from exc
    for field in (
        "invariant_bazi_facts", "variant_bazi_facts",
        "invariant_ziwei_facts", "variant_ziwei_facts",
    ):
        if raw[field] != classified[field]:
            raise DistributionError(
                "invalid_candidate_envelope",
                "candidate classification does not match candidate facts",
                {"field": field},
            )
    return raw


def _index_body(identity: Mapping[str, str], envelope: Mapping[str, object]) -> str:
    lines = [
        "# %s｜Metaphysics Lab Case｜專案索引" % identity["subject_display_name"],
        "",
        "- 命主：%s" % identity["subject_display_name"],
        "- Subject ID: `%s`" % identity["subject_id"],
        "- Case lifecycle: `progressive`",
        "- Natal Status: `partial`",
        "- Birth Time Status: `%s`" % envelope["natal_precision_state"],
        "- Candidate Count: `%s`" % envelope["candidate_count"],
        "",
        "## Case Files",
        "",
    ]
    for canonical in CASE_FILES:
        actual = canonical_case_filename(identity, canonical)
        lines.append(_manifest_expected_line(canonical, actual, canonical in BASE_CASE_FILES))
    lines.extend([
        "",
        "## Allowed Analysis",
        "",
        *_list_lines(envelope.get("allowed_analysis")),
        "",
        "## Blocked Analysis",
        "",
        *_list_lines(envelope.get("blocked_analysis")),
        "",
        "## Historical Calibration",
        "",
        "Historical Calibration: `uncalibrated`",
        "",
    ])
    return "\n".join(lines)


def _core_body(identity: Mapping[str, str], envelope: Mapping[str, object]) -> str:
    known = envelope.get("known_facts", {})
    invariant = {
        "bazi": envelope.get("invariant_bazi_facts", {}),
        "ziwei": envelope.get("invariant_ziwei_facts", {}),
    }
    variant = {
        "bazi": envelope.get("variant_bazi_facts", {}),
        "ziwei": envelope.get("variant_ziwei_facts", {}),
    }
    lines = [
        "# %s｜命盤核心摘要" % identity["subject_display_name"], "",
        "- 命主：%s" % identity["subject_display_name"],
        "- Subject ID: `%s`" % identity["subject_id"],
        "- Natal Status: `partial`",
        "- Birth Time Status: `%s`" % envelope["natal_precision_state"],
        "- Candidate Count: `%s`" % envelope["candidate_count"],
        "",
        "## 【已確定盤面】", "",
        "```json", _json({"known_facts": known, "invariant_facts": invariant}), "```", "",
        "## 【候選依賴盤面】", "",
        "```json", _json(variant), "```", "",
        "## 【目前不可唯一判定】", "",
        *_list_lines(envelope.get("blocked_analysis")), "",
    ]
    return "\n".join(lines)


def _calibration_body(identity: Mapping[str, str], envelope: Mapping[str, object]) -> str:
    known = envelope.get("known_facts", {})
    time_source = "unknown" if envelope["natal_precision_state"] == "unknown_time" else "approximate"
    facts = {
        "birth_time_source": time_source,
        "birth_time_precision": envelope["natal_precision_state"],
        "reported_birth_time": known.get("reported_birth_time"),
        "reported_birth_time_range": known.get("reported_birth_time_range"),
        "candidate_count": envelope["candidate_count"],
        "candidate_profile": envelope.get("profile_id"),
        "candidate_rule_version": envelope.get("rule_version"),
        "confirmed_by_external_record": False,
        "candidate_rectification_used": False,
        "boundary_ambiguities": envelope.get("boundary_ambiguities", []),
    }
    return "\n".join([
        "# %s｜命盤資料校驗紀錄" % identity["subject_display_name"], "",
        "本檔記錄出生時間精度與 Candidate Envelope 狀態；候選不是已驗證出生時間。", "",
        "```json", _json(facts), "```", "",
    ])


def _bazi_body(identity: Mapping[str, str], envelope: Mapping[str, object]) -> str:
    candidate_set = [
        {
            "candidate_id": item.get("candidate_id"),
            "reported_time_start": item.get("reported_time_start"),
            "reported_time_end": item.get("reported_time_end"),
            "bazi": item.get("bazi", {}),
            "bazi_decadal_start_range": item.get("bazi_decadal_start_range"),
        }
        for item in envelope.get("candidates", []) if isinstance(item, Mapping)
    ]
    return "\n".join([
        "# %s｜八字結構化資料包" % identity["subject_display_name"], "",
        "## Invariant Facts", "", "```json", _json(envelope.get("invariant_bazi_facts", {})), "```", "",
        "## Candidate-dependent Facts", "", "```json", _json(envelope.get("variant_bazi_facts", {})), "```", "",
        "## Candidate Set", "", "```json", _json(candidate_set), "```", "",
        "## Blocked Conclusions", "", *_list_lines(envelope.get("blocked_analysis")), "",
    ])


def _ziwei_body(identity: Mapping[str, str], envelope: Mapping[str, object]) -> str:
    candidate_summaries = [
        {
            "candidate_id": item.get("candidate_id"),
            "reported_time_start": item.get("reported_time_start"),
            "reported_time_end": item.get("reported_time_end"),
            "ziwei": item.get("ziwei", {}),
        }
        for item in envelope.get("candidates", []) if isinstance(item, Mapping)
    ]
    return "\n".join([
        "# %s｜紫微基礎資料包" % identity["subject_display_name"], "",
        "## Invariant Across Candidates", "", "```json", _json(envelope.get("invariant_ziwei_facts", {})), "```", "",
        "## Candidate-dependent Facts", "", "```json", _json(envelope.get("variant_ziwei_facts", {})), "```", "",
        "## Candidate Summaries", "", "```json", _json(candidate_summaries), "```", "",
        "## Blocked Conclusions", "", *_list_lines(envelope.get("blocked_analysis")), "",
    ])


def export_partial_case_markdown(payload: Mapping[str, object]) -> dict:
    payload = _mapping(payload, "payload")
    envelope = _validate_envelope(payload.get("candidate_envelope"))
    identity = _identity_from_payload(payload)
    generated_at = _timestamp(payload.get("generated_at"), "generated_at")
    modified_by = _text(payload.get("last_modified_by", "ai"), "last_modified_by")
    bodies = {
        "00_專案索引.md": _index_body(identity, envelope),
        "01_命盤核心摘要.md": _core_body(identity, envelope),
        "02_命盤資料校驗紀錄.md": _calibration_body(identity, envelope),
        "03_八字結構化資料包.md": _bazi_body(identity, envelope),
        "04_紫微基礎資料包.md": _ziwei_body(identity, envelope),
    }
    files = {}
    for canonical in BASE_CASE_FILES:
        actual = canonical_case_filename(identity, canonical)
        files[actual] = _render_case_file(
            canonical,
            _metadata(canonical, identity, generated_at, modified_by),
            bodies[canonical],
        )
    return {
        "subject_id": identity["subject_id"],
        "subject": identity,
        "natal_status": "partial",
        "candidate_envelope_profile": envelope.get("profile_id"),
        "files": files,
    }
