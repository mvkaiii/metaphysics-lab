"""Pure projection of an allowlisted Bazi engine view into chart v1."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import hashlib
import json
import math
import re
from typing import Any, Mapping, Optional

from engine.distribution.manifest import capability_manifest_digest
from .contract import validate_chart


PROJECTION_VERSION = "1.0-exp"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_ROOT_FIELDS = {"schema_version", "input_status", "resolved_candidate_count", "project_natal", "source_capabilities", "provenance"}
_BAZI_FIELDS = {"profile", "timezone", "decadal_direction", "decadal_periods"}
_PROFILE_FIELDS = {"profile_id", "rule_version", "age_basis", "interval_semantics"}
_PERIOD_FIELDS = {"index", "pillar", "start_age_years", "end_age_years", "start_datetime", "end_datetime", "ten_god", "elements"}


def canonical_json_bytes(value: Any) -> bytes:
    """Return the contract's deterministic JSON bytes."""

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _forbidden_input(value: Any, path: str = "input") -> Optional[str]:
    forbidden = {
        "case",
        "freeform_case",
        "known_reality_context",
        "historical_event_ledger",
        "verified_event_payload",
        "current_real_world_context",
    }
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key in forbidden:
                return f"{path}: forbidden field {key!r}"
            found = _forbidden_input(child, f"{path}.{key}")
            if found:
                return found
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found = _forbidden_input(child, f"{path}[{index}]")
            if found:
                return found
    return None


def _iso(value: Any, path: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{path} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{path} is not a valid ISO datetime") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{path} must include an explicit offset")
    return parsed


def _number(value: Any, path: str) -> float | int:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{path} must be a finite number")
    return value


def _base_provenance(input_view: Mapping[str, Any]) -> dict:
    source = input_view.get("provenance")
    if not isinstance(source, Mapping):
        raise ValueError("provenance must be an object")
    required = {
        "repo",
        "source_commit",
        "release_version",
        "distribution_runtime_version",
        "manifest_sha256",
        "source_payload_sha256",
        "projection_version",
    }
    if set(source) != required:
        raise ValueError("provenance fields do not match the allowlist")
    if not isinstance(source.get("repo"), str) or not source["repo"]:
        raise ValueError("provenance.repo must be non-empty")
    if not isinstance(source.get("source_commit"), str) or not source["source_commit"]:
        raise ValueError("provenance.source_commit must be non-empty")
    for key in ("release_version", "distribution_runtime_version", "projection_version"):
        if not isinstance(source.get(key), str) or not source[key]:
            raise ValueError(f"provenance.{key} must be non-empty")
    for key in ("manifest_sha256", "source_payload_sha256"):
        if not isinstance(source.get(key), str) or not _SHA256.fullmatch(source[key]):
            raise ValueError(f"provenance.{key} must be a lowercase SHA256")
    return dict(source)


def _unsupported(input_view: Mapping[str, Any], as_of: str, timezone: str, visibility_mode: str, reason: str) -> dict:
    provenance = _base_provenance(input_view)
    chart = {
        "chart_type": "bazi_decadal_timeline",
        "schema_version": "1.0",
        "status": "unsupported",
        "reason_codes": [reason],
        "view_context": {"as_of": as_of, "timezone": timezone, "visibility_mode": visibility_mode, "locale": "zh-TW"},
        "source_capabilities": [],
        "data": None,
        "annotations": [],
        "authorities": {},
        "provenance": {
            **provenance,
            "release_version": None,
            "distribution_runtime_version": None,
            "manifest_sha256": None,
            "source_payload_sha256": None,
        },
        "limitations": [{"code": reason, "message": reason, "scope": "chart"}],
    }
    errors = validate_chart(chart)
    if errors:
        raise ValueError("unsupported projection violated chart contract: %s" % "; ".join(errors))
    return chart


def _validate_root(input_view: Mapping[str, Any]) -> None:
    unknown = sorted(set(input_view) - _ROOT_FIELDS)
    if unknown:
        raise ValueError("input contains unknown fields: %s" % ", ".join(unknown))
    if input_view.get("schema_version") != "1.0":
        raise ValueError("input schema_version must be 1.0")
    if input_view.get("input_status") not in {"resolved_unique", "unresolved"}:
        raise ValueError("input_status must be resolved_unique or unresolved")
    if isinstance(input_view.get("resolved_candidate_count"), bool) or not isinstance(input_view.get("resolved_candidate_count"), int):
        raise ValueError("resolved_candidate_count must be an integer")
    if not isinstance(input_view.get("project_natal"), Mapping):
        raise ValueError("project_natal must be an object")
    if not isinstance(input_view.get("source_capabilities"), list):
        raise ValueError("source_capabilities must be a list")


def _source_capability(input_view: Mapping[str, Any], manifest: Mapping[str, Any]) -> Optional[dict]:
    capabilities = input_view["source_capabilities"]
    if len(capabilities) != 1 or not isinstance(capabilities[0], Mapping):
        return None
    source = capabilities[0]
    required = {"capability_id", "scope", "profile_id", "rule_version", "maturity", "routing"}
    if set(source) != required:
        return None
    if source.get("capability_id") != "bazi.natal_chart" or source.get("scope") != "decadal_periods":
        return None
    canonical = manifest.get("capabilities", {}).get("bazi.natal_chart") if isinstance(manifest, Mapping) else None
    if not isinstance(canonical, Mapping):
        return None
    for key in ("rule_version", "maturity", "routing"):
        if source.get(key) != canonical.get(key):
            return None
    if not isinstance(source.get("profile_id"), str) or not source["profile_id"]:
        return None
    return dict(source)


def _bazi_view(input_view: Mapping[str, Any]) -> Mapping[str, Any]:
    natal = input_view["project_natal"]
    if set(natal) != {"bazi"} or not isinstance(natal.get("bazi"), Mapping):
        raise ValueError("project_natal must contain only bazi")
    bazi = natal["bazi"]
    unknown = sorted(set(bazi) - _BAZI_FIELDS)
    if unknown:
        raise ValueError("project_natal.bazi contains unknown fields: %s" % ", ".join(unknown))
    if not isinstance(bazi.get("profile"), Mapping) or set(bazi["profile"]) != _PROFILE_FIELDS:
        raise ValueError("project_natal.bazi.profile fields do not match the allowlist")
    return bazi


def project_bazi_decadal(
    engine_view: Mapping[str, Any],
    manifest: Mapping[str, Any],
    *,
    as_of: str,
    timezone: str,
    visibility_mode: str,
) -> dict:
    """Project one resolved deterministic engine view into chart v1."""

    if not isinstance(engine_view, Mapping) or not isinstance(manifest, Mapping):
        raise ValueError("engine_view and manifest must be objects")
    contamination = _forbidden_input(engine_view)
    if contamination:
        raise ValueError(contamination)
    _validate_root(engine_view)
    if visibility_mode not in {"blind", "identified"}:
        raise ValueError("visibility_mode must be blind or identified")
    as_of_dt = _iso(as_of, "as_of")
    if not isinstance(timezone, str) or not timezone:
        raise ValueError("timezone must be non-empty")
    provenance = _base_provenance(engine_view)
    expected_manifest_digest = capability_manifest_digest(manifest)
    if provenance["manifest_sha256"] != expected_manifest_digest:
        return _unsupported(engine_view, as_of, timezone, visibility_mode, "MANIFEST_DIGEST_MISMATCH")
    source_payload = engine_view["project_natal"]
    if provenance["source_payload_sha256"] != _sha256(source_payload):
        return _unsupported(engine_view, as_of, timezone, visibility_mode, "SOURCE_PAYLOAD_DIGEST_MISMATCH")
    if engine_view["input_status"] != "resolved_unique" or engine_view["resolved_candidate_count"] != 1:
        return _unsupported(engine_view, as_of, timezone, visibility_mode, "AMBIGUOUS_NATAL_CANDIDATE")
    source_capability = _source_capability(engine_view, manifest)
    if source_capability is None:
        return _unsupported(engine_view, as_of, timezone, visibility_mode, "SOURCE_MATURITY_MISMATCH")
    bazi = _bazi_view(engine_view)
    profile = bazi["profile"]
    if profile["age_basis"] != "continuous_years_from_jie_interval":
        return _unsupported(engine_view, as_of, timezone, visibility_mode, "AGE_BASIS_UNSUPPORTED")
    if profile["interval_semantics"] != "[start_at,end_at)":
        return _unsupported(engine_view, as_of, timezone, visibility_mode, "UNKNOWN_INTERVAL_SEMANTICS")
    if profile["profile_id"] != source_capability["profile_id"] or profile["rule_version"] != source_capability["rule_version"]:
        return _unsupported(engine_view, as_of, timezone, visibility_mode, "PROFILE_RULE_MISMATCH")
    if bazi["timezone"] != timezone:
        return _unsupported(engine_view, as_of, timezone, visibility_mode, "SOURCE_TIMEZONE_MISMATCH")
    direction = bazi["decadal_direction"]
    if direction not in {"forward", "reverse"}:
        raise ValueError("decadal_direction must be forward or reverse")
    periods = bazi["decadal_periods"]
    if not isinstance(periods, list) or not periods:
        raise ValueError("decadal_periods must be a non-empty list")

    projected_periods = []
    authorities = {}
    previous_end = None
    current_period_id = None
    for offset, source_period in enumerate(periods):
        if not isinstance(source_period, Mapping) or not set(source_period).issubset(_PERIOD_FIELDS):
            raise ValueError("decadal period contains unknown or malformed fields")
        required = {"index", "pillar", "start_age_years", "end_age_years", "start_datetime", "end_datetime"}
        if not required.issubset(source_period):
            raise ValueError("decadal period is missing a required field")
        index = source_period["index"]
        if isinstance(index, bool) or not isinstance(index, int) or index != offset + 1:
            raise ValueError("decadal period indexes must be sequential from 1")
        if not isinstance(source_period["pillar"], str) or not source_period["pillar"]:
            raise ValueError("decadal period pillar must be non-empty text")
        start_dt = _iso(source_period["start_datetime"], f"period[{offset}].start_datetime")
        end_dt = _iso(source_period["end_datetime"], f"period[{offset}].end_datetime")
        if end_dt <= start_dt:
            raise ValueError("decadal period end must be after start")
        if previous_end is not None and start_dt != previous_end:
            raise ValueError("decadal period intervals must be contiguous")
        previous_end = end_dt
        start_age = _number(source_period["start_age_years"], f"period[{offset}].start_age_years")
        end_age = _number(source_period["end_age_years"], f"period[{offset}].end_age_years")
        if end_age <= start_age:
            raise ValueError("decadal period end age must be after start age")
        period_id = f"period-{index}"
        authority_id = f"{period_id}-derived"
        authorities[authority_id] = {
            "classification": "project_derived",
            "source_refs": [f"/project_natal/bazi/decadal_periods/{offset}"],
            "transformation": "field_mapping_only",
            "confidence": None,
        }
        ten_god = deepcopy(source_period.get("ten_god")) if "ten_god" in source_period else None
        elements = deepcopy(source_period.get("elements")) if "elements" in source_period else None
        period = {
            "id": period_id,
            "index": index,
            "pillar": source_period["pillar"],
            "age_start_years": start_age,
            "age_end_years": end_age,
            "start_at": source_period["start_datetime"],
            "end_at": source_period["end_datetime"],
            "ten_god": ten_god,
            "elements": elements,
            "optional_reasons": {
                "ten_god": "NO_QUALIFIED_SOURCE" if ten_god is None else "SOURCE_ENGINE_OUTPUT",
                "elements": "NO_QUALIFIED_SOURCE" if elements is None else "SOURCE_ENGINE_OUTPUT",
            },
            "authority_refs": {
                "/pillar": [authority_id],
                "/age_start_years": [authority_id],
                "/age_end_years": [authority_id],
                "/start_at": [authority_id],
                "/end_at": [authority_id],
            },
        }
        projected_periods.append(period)
        if start_dt <= as_of_dt < end_dt:
            current_period_id = period_id

    chart = {
        "chart_type": "bazi_decadal_timeline",
        "schema_version": "1.0",
        "status": "ready",
        "reason_codes": [],
        "view_context": {"as_of": as_of, "timezone": timezone, "visibility_mode": visibility_mode, "locale": "zh-TW"},
        "source_capabilities": [source_capability],
        "data": {
            "age_basis": {
                "id": profile["age_basis"],
                "description": "Continuous years from the jie interval; source precision is preserved.",
                "rounding_policy": "preserve_source_precision",
            },
            "time_basis": {
                "calendar": "gregorian",
                "boundary_policy": "source_interval_only",
                "interval_convention": "[start_at,end_at)",
                "source_timezone": bazi["timezone"],
            },
            "direction": direction,
            "periods": projected_periods,
            "current_period_id": current_period_id,
            "year_overlays": [],
        },
        "annotations": [],
        "authorities": authorities,
        "provenance": {**provenance, "projection_version": PROJECTION_VERSION},
        "limitations": [
            {"code": "EXPERIMENTAL_CAPABILITY", "message": "E：大運視覺化維持Experimental。", "scope": "chart"},
            {"code": "OPTIONAL_FIELDS_UNAVAILABLE", "message": "十神與五行只在engine已提供合格來源時映射。", "scope": "periods"},
        ],
    }
    errors = validate_chart(chart)
    if errors:
        raise ValueError("projection generated invalid chart: %s" % "; ".join(errors))
    return chart
