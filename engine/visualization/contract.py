"""Semantic validation for the versioned visualization chart contract.

This module validates serialized chart data only.  It does not calculate a
natal chart, resolve a case, access the filesystem, or fetch external data.
"""

from __future__ import annotations

from datetime import datetime
import math
import re
from typing import Any, Mapping


CHART_TYPE = "bazi_decadal_timeline"
SCHEMA_VERSION = "1.0"
AUTHORITY_CLASSIFICATIONS = {
    "original_chart_fact",
    "verified_data",
    "project_derived",
    "verified_event",
    "metaphysical_inference",
    "research_hypothesis",
    "current_real_world_context",
}
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40,64}$")
_FORBIDDEN_KEYS = {
    "case",
    "freeform_case",
    "known_reality_context",
    "historical_event_ledger",
    "verified_event_payload",
    "current_real_world_context",
}

_TOP_LEVEL = {
    "chart_type", "schema_version", "status", "reason_codes", "view_context",
    "source_capabilities", "data", "annotations", "authorities", "provenance",
    "limitations",
}
_VIEW_CONTEXT = {"as_of", "timezone", "visibility_mode", "locale"}
_CAPABILITY = {"capability_id", "scope", "profile_id", "rule_version", "maturity", "routing"}
_DATA = {"age_basis", "time_basis", "direction", "periods", "current_period_id", "year_overlays"}
_AGE_BASIS = {"id", "description", "rounding_policy"}
_TIME_BASIS = {"calendar", "boundary_policy", "interval_convention", "source_timezone"}
_PERIOD = {
    "id", "index", "pillar", "age_start_years", "age_end_years", "start_at", "end_at",
    "ten_god", "elements", "optional_reasons", "authority_refs",
}
_AUTHORITY = {"classification", "source_refs", "transformation", "confidence"}
_PROVENANCE = {
    "repo", "source_commit", "release_version", "distribution_runtime_version",
    "manifest_sha256", "source_payload_sha256", "projection_version",
}
_LIMITATION = {"code", "message", "scope"}
_ANNOTATION = {"target_id", "text", "authority_refs", "visibility", "evidence_refs"}


def _unknown_fields(value: Mapping[str, Any], allowed: set[str], path: str, errors: list[str]) -> None:
    for key in sorted(set(value) - allowed):
        errors.append(f"{path}: unknown field {key!r}")


def _scan_forbidden(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key in _FORBIDDEN_KEYS:
                errors.append(f"{path}: forbidden contamination field {key!r}")
            _scan_forbidden(child, f"{path}.{key}", errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_forbidden(child, f"{path}[{index}]", errors)
    elif isinstance(value, float) and not math.isfinite(value):
        errors.append(f"{path}: number must be finite")


def _require_string(value: Any, path: str, errors: list[str], *, nonempty: bool = True) -> bool:
    if not isinstance(value, str) or (nonempty and not value):
        errors.append(f"{path}: expected a string")
        return False
    return True


def _require_list(value: Any, path: str, errors: list[str]) -> bool:
    if not isinstance(value, list):
        errors.append(f"{path}: expected a list")
        return False
    return True


def _validate_iso_offset(value: Any, path: str, errors: list[str]) -> None:
    if not _require_string(value, path, errors):
        return
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        errors.append(f"{path}: invalid ISO-8601 datetime")
        return
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        errors.append(f"{path}: datetime must include an explicit offset")


def _validate_authority_refs(
    refs: Any,
    path: str,
    authorities: Mapping[str, Any],
    errors: list[str],
    *,
    project_derived_only: bool = False,
) -> None:
    if not isinstance(refs, Mapping) or not refs:
        errors.append(f"{path}: authority_refs must be a non-empty object")
        return
    for field, ids in sorted(refs.items()):
        field_path = f"{path}.{field}"
        if not isinstance(field, str) or not isinstance(ids, list) or not ids:
            errors.append(f"{field_path}: authority_refs value must be a non-empty list")
            continue
        for authority_id in ids:
            if not isinstance(authority_id, str) or not authority_id:
                errors.append(f"{field_path}: authority id must be a non-empty string")
                continue
            authority = authorities.get(authority_id)
            if not isinstance(authority, Mapping):
                errors.append(f"{field_path}: unknown authority {authority_id!r}")
                continue
            if project_derived_only and authority.get("classification") != "project_derived":
                errors.append(f"{field_path}: semantic engine field must use project_derived authority")


def _validate_provenance(value: Any, errors: list[str], *, ready: bool) -> None:
    path = "provenance"
    if not isinstance(value, Mapping):
        errors.append(f"{path}: expected an object")
        return
    _unknown_fields(value, _PROVENANCE, path, errors)
    for key in sorted(_PROVENANCE):
        if key not in value:
            errors.append(f"{path}: missing field {key}")
    _require_string(value.get("repo"), f"{path}.repo", errors)
    source_commit = value.get("source_commit")
    if source_commit is not None and (not isinstance(source_commit, str) or not _COMMIT.fullmatch(source_commit)):
        errors.append(f"{path}.source_commit: expected a 40 to 64 character hex SHA")
    for key in ("manifest_sha256", "source_payload_sha256"):
        digest = value.get(key)
        if digest is not None and (not isinstance(digest, str) or not _SHA256.fullmatch(digest)):
            errors.append(f"{path}.{key}: expected a 64 character lowercase hex SHA256")
    for key in ("release_version", "distribution_runtime_version", "projection_version"):
        if value.get(key) is not None:
            _require_string(value.get(key), f"{path}.{key}", errors)
    if ready:
        for key in ("source_commit", "release_version", "distribution_runtime_version", "manifest_sha256", "source_payload_sha256"):
            if value.get(key) is None:
                errors.append(f"{path}.{key}: ready chart requires a bound value")


def _validate_authorities(value: Any, errors: list[str], visibility_mode: Any) -> None:
    if not isinstance(value, Mapping):
        errors.append("authorities: expected an object")
        return
    for authority_id in sorted(value):
        authority = value[authority_id]
        path = f"authorities.{authority_id}"
        if not isinstance(authority, Mapping):
            errors.append(f"{path}: expected an object")
            continue
        _unknown_fields(authority, _AUTHORITY, path, errors)
        if not _require_string(authority.get("classification"), f"{path}.classification", errors):
            continue
        classification = authority["classification"]
        if classification not in AUTHORITY_CLASSIFICATIONS:
            errors.append(f"{path}.classification: unknown authority {classification!r}")
        if visibility_mode == "blind" and classification in {"verified_event", "current_real_world_context"}:
            errors.append(f"{path}.classification: blind chart cannot use {classification}")
        if not _require_list(authority.get("source_refs"), f"{path}.source_refs", errors):
            continue
        if any(not isinstance(item, str) or not item for item in authority["source_refs"]):
            errors.append(f"{path}.source_refs: entries must be non-empty strings")
        _require_string(authority.get("transformation"), f"{path}.transformation", errors)
        confidence = authority.get("confidence")
        if confidence is not None and (isinstance(confidence, bool) or not isinstance(confidence, (int, float))):
            errors.append(f"{path}.confidence: expected a finite number or null")
        elif isinstance(confidence, float) and not math.isfinite(confidence):
            errors.append(f"{path}.confidence: number must be finite")


def _validate_chart(chart: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    _unknown_fields(chart, _TOP_LEVEL, "chart", errors)
    for key in sorted(_TOP_LEVEL):
        if key not in chart:
            errors.append(f"chart: missing field {key}")
    _scan_forbidden(chart, "chart", errors)
    if chart.get("chart_type") != CHART_TYPE:
        errors.append(f"chart.chart_type: expected {CHART_TYPE!r}")
    if chart.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"chart.schema_version: unknown schema_version {chart.get('schema_version')!r}")
    status = chart.get("status")
    if status not in {"ready", "unsupported"}:
        errors.append("chart.status: expected ready or unsupported")
    reason_codes = chart.get("reason_codes")
    if _require_list(reason_codes, "chart.reason_codes", errors):
        if any(not isinstance(code, str) or not code for code in reason_codes):
            errors.append("chart.reason_codes: entries must be non-empty strings")
        if len(set(reason_codes)) != len(reason_codes):
            errors.append("chart.reason_codes: entries must be unique")
        if status == "ready" and reason_codes:
            errors.append("chart.reason_codes: ready chart must not carry reason codes")
        if status == "unsupported" and not reason_codes:
            errors.append("chart.reason_codes: unsupported chart requires a reason code")

    context = chart.get("view_context")
    if not isinstance(context, Mapping):
        errors.append("view_context: expected an object")
        context = {}
    else:
        _unknown_fields(context, _VIEW_CONTEXT, "view_context", errors)
        for key in sorted(_VIEW_CONTEXT):
            if key not in context:
                errors.append(f"view_context: missing field {key}")
        _validate_iso_offset(context.get("as_of"), "view_context.as_of", errors)
        _require_string(context.get("timezone"), "view_context.timezone", errors)
        if context.get("visibility_mode") not in {"blind", "identified"}:
            errors.append("view_context.visibility_mode: expected blind or identified")
        if context.get("locale") != "zh-TW":
            errors.append("view_context.locale: only zh-TW is supported")

    source_capabilities = chart.get("source_capabilities")
    if _require_list(source_capabilities, "source_capabilities", errors):
        for index, capability in enumerate(source_capabilities):
            path = f"source_capabilities[{index}]"
            if not isinstance(capability, Mapping):
                errors.append(f"{path}: expected an object")
                continue
            _unknown_fields(capability, _CAPABILITY, path, errors)
            for key in sorted(_CAPABILITY):
                if key not in capability:
                    errors.append(f"{path}: missing field {key}")
                else:
                    _require_string(capability[key], f"{path}.{key}", errors)
            if capability.get("maturity") not in {"stable", "experimental"}:
                errors.append(f"{path}.maturity: expected stable or experimental")
            if capability.get("routing") not in {"default", "on_demand"}:
                errors.append(f"{path}.routing: expected default or on_demand")

    _validate_authorities(chart.get("authorities"), errors, context.get("visibility_mode"))
    _validate_provenance(chart.get("provenance"), errors, ready=status == "ready")
    limitations = chart.get("limitations")
    limitation_codes: set[Any] = set()
    if _require_list(limitations, "limitations", errors):
        for index, limitation in enumerate(limitations):
            path = f"limitations[{index}]"
            if not isinstance(limitation, Mapping):
                errors.append(f"{path}: expected an object")
                continue
            _unknown_fields(limitation, _LIMITATION, path, errors)
            for key in sorted(_LIMITATION):
                if key not in limitation:
                    errors.append(f"{path}: missing field {key}")
                else:
                    _require_string(limitation[key], f"{path}.{key}", errors)
            limitation_codes.add(limitation.get("code"))

    data = chart.get("data")
    if status == "unsupported":
        if data is not None:
            errors.append("data: unsupported chart must have data=null")
        if source_capabilities != []:
            errors.append("source_capabilities: unsupported chart must have an empty list")
        if chart.get("authorities") != {}:
            errors.append("authorities: unsupported chart must have an empty object")
        if chart.get("annotations") != []:
            errors.append("annotations: unsupported chart must have an empty list")
    elif status == "ready":
        if not isinstance(data, Mapping):
            errors.append("data: ready chart requires an object")
        else:
            _unknown_fields(data, _DATA, "data", errors)
            for key in sorted(_DATA):
                if key not in data:
                    errors.append(f"data: missing field {key}")
            age_basis = data.get("age_basis")
            if not isinstance(age_basis, Mapping):
                errors.append("data.age_basis: expected an object")
            else:
                _unknown_fields(age_basis, _AGE_BASIS, "data.age_basis", errors)
                for key in sorted(_AGE_BASIS):
                    _require_string(age_basis.get(key), f"data.age_basis.{key}", errors)
                if age_basis.get("id") != "continuous_years_from_jie_interval":
                    errors.append("data.age_basis.id: must be continuous_years_from_jie_interval")
            time_basis = data.get("time_basis")
            if not isinstance(time_basis, Mapping):
                errors.append("data.time_basis: expected an object")
            else:
                _unknown_fields(time_basis, _TIME_BASIS, "data.time_basis", errors)
                for key in sorted(_TIME_BASIS):
                    _require_string(time_basis.get(key), f"data.time_basis.{key}", errors)
                if time_basis.get("interval_convention") != "[start_at,end_at)":
                    errors.append("data.time_basis.interval_convention: expected [start_at,end_at)")
            if data.get("direction") not in {"forward", "reverse", None}:
                errors.append("data.direction: expected forward, reverse, or null")
            periods = data.get("periods")
            period_ids: list[str] = []
            if not isinstance(periods, list) or not periods:
                errors.append("data.periods: ready chart requires a non-empty list")
                periods = []
            for index, period in enumerate(periods):
                path = f"data.periods[{index}]"
                if not isinstance(period, Mapping):
                    errors.append(f"{path}: expected an object")
                    continue
                _unknown_fields(period, _PERIOD, path, errors)
                required = {"id", "index", "pillar", "age_start_years", "age_end_years", "start_at", "end_at", "authority_refs"}
                for key in sorted(required):
                    if key not in period:
                        errors.append(f"{path}: missing field {key}")
                period_id = period.get("id")
                if _require_string(period_id, f"{path}.id", errors):
                    period_ids.append(period_id)
                if isinstance(period.get("index"), bool) or not isinstance(period.get("index"), int):
                    errors.append(f"{path}.index: expected an integer")
                _require_string(period.get("pillar"), f"{path}.pillar", errors)
                for key in ("age_start_years", "age_end_years"):
                    number = period.get(key)
                    if isinstance(number, bool) or not isinstance(number, (int, float)):
                        errors.append(f"{path}.{key}: expected a finite number")
                    elif isinstance(number, float) and not math.isfinite(number):
                        errors.append(f"{path}.{key}: number must be finite")
                _validate_iso_offset(period.get("start_at"), f"{path}.start_at", errors)
                _validate_iso_offset(period.get("end_at"), f"{path}.end_at", errors)
                for optional in ("ten_god", "elements"):
                    if optional not in period:
                        errors.append(f"{path}: missing optional field {optional}")
                    elif period[optional] is not None and not isinstance(period[optional], Mapping):
                        errors.append(f"{path}.{optional}: expected an object or null")
                reasons = period.get("optional_reasons")
                if not isinstance(reasons, Mapping):
                    errors.append(f"{path}.optional_reasons: expected an object")
                else:
                    for optional in ("ten_god", "elements"):
                        if period.get(optional) is None and not isinstance(reasons.get(optional), str):
                            errors.append(f"{path}.optional_reasons.{optional}: required when value is null")
                _validate_authority_refs(
                    period.get("authority_refs"), f"{path}.authority_refs",
                    chart.get("authorities") if isinstance(chart.get("authorities"), Mapping) else {},
                    errors, project_derived_only=True,
                )
            current = data.get("current_period_id")
            if current is not None and current not in period_ids:
                errors.append("data.current_period_id: must reference a period or be null")
            if not isinstance(data.get("year_overlays"), list):
                errors.append("data.year_overlays: expected a list")
            if any(cap.get("maturity") == "experimental" for cap in source_capabilities if isinstance(cap, Mapping)) and "EXPERIMENTAL_CAPABILITY" not in limitation_codes:
                errors.append("limitations: Experimental capability requires an Experimental limitation badge")

    annotations = chart.get("annotations")
    if not isinstance(annotations, list):
        errors.append("annotations: expected a list")
    elif context.get("visibility_mode") == "blind" and annotations:
        errors.append("annotations: blind chart cannot contain annotations or contamination")
    else:
        for index, annotation in enumerate(annotations):
            path = f"annotations[{index}]"
            if not isinstance(annotation, Mapping):
                errors.append(f"{path}: expected an object")
                continue
            _unknown_fields(annotation, _ANNOTATION, path, errors)
    return sorted(set(errors))


def validate_chart(chart: Mapping[str, Any]) -> list[str]:
    """Return deterministic semantic validation errors for a chart contract."""

    if not isinstance(chart, Mapping):
        return ["chart: expected an object"]
    try:
        return _validate_chart(chart)
    except (AttributeError, TypeError, ValueError, OverflowError) as exc:
        return [f"chart: malformed input ({exc.__class__.__name__})"]
