"""Candidate-envelope construction for bounded or unknown birth time.

The engine scans every civil minute in the uncertainty interval so no midpoint or
default time is invented. Adjacent minutes that yield the same discrete Bazi and
Ziwei chart structure are then collapsed into one material timing state. Continuous
Bazi luck-start timing remains a range rather than creating one fake chart per minute.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from typing import Mapping, Optional

from engine.birth.errors import BirthFoundationError
from engine.birth.input_resolution import resolve_birth_input
from engine.birth.models import ResolvedBirthPlace

from .errors import NatalFoundationError
from .orchestration import build_project_natal


_PROFILE_ID = "natal-candidate-envelope-v1"
_RULE_VERSION = "1.0-exp"
_CONTINUOUS_BAZI_KEYS = frozenset(("decadal_start",))
_CONTINUOUS_PERIOD_KEYS = frozenset(("start_age_years", "end_age_years", "start_datetime", "end_datetime"))
_MISSING = object()
_CANDIDATE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def _candidate_id(value: object) -> str:
    if not isinstance(value, str) or value != value.strip() or not _CANDIDATE_ID_PATTERN.fullmatch(value):
        raise ValueError("candidate_id must be a canonical single-line identifier")
    return value


def _minute_text(value: int) -> str:
    return "%02d:%02d" % (value // 60, value % 60)


def _parse_minute(value: object) -> int:
    if not isinstance(value, str):
        raise NatalFoundationError("ambiguous_birth_time", "birth time must be HH:MM")
    try:
        parsed = datetime.strptime(value, "%H:%M")
    except ValueError as exc:
        raise NatalFoundationError("ambiguous_birth_time", "birth time must be valid HH:MM text") from exc
    return parsed.hour * 60 + parsed.minute


def _uncertainty_minutes(birth_payload: Mapping[str, object]):
    if birth_payload.get("birth_time") not in (None, ""):
        minute = _parse_minute(birth_payload.get("birth_time"))
        return "exact", range(minute, minute + 1)
    raw_range = birth_payload.get("birth_time_range")
    if raw_range is not None:
        if not isinstance(raw_range, (list, tuple)) or len(raw_range) != 2:
            raise NatalFoundationError("ambiguous_birth_time", "birth_time_range must contain start and end HH:MM")
        start = _parse_minute(raw_range[0])
        end = _parse_minute(raw_range[1])
        if end < start:
            raise NatalFoundationError("ambiguous_birth_time", "birth_time_range cannot cross the civil-date boundary in v1")
        return "bounded", range(start, end + 1)
    return "unknown_time", range(0, 1440)


def _discrete_bazi(value: Mapping[str, object]) -> dict:
    result = {}
    for key, item in value.items():
        if key in _CONTINUOUS_BAZI_KEYS:
            continue
        if key == "decadal_periods" and isinstance(item, list):
            result[key] = [
                {k: v for k, v in period.items() if k not in _CONTINUOUS_PERIOD_KEYS}
                if isinstance(period, Mapping) else period
                for period in item
            ]
        else:
            result[key] = item
    return result


def _signature(bazi: Mapping[str, object], ziwei: Mapping[str, object]) -> str:
    payload = json.dumps({"bazi": bazi, "ziwei": ziwei}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def partition_material_states(minute_rows):
    if not isinstance(minute_rows, (list, tuple)):
        raise ValueError("minute_rows must be a list")
    states = []
    current = None
    for raw in minute_rows:
        row = dict(raw)
        minute = int(row["minute"])
        signature = str(row["signature"])
        if current is None or signature != current["_signature"] or minute != current["_last_minute"] + 1:
            if current is not None:
                states.append(_finalize_state(current, len(states) + 1))
            current = {
                "_signature": signature,
                "_first_minute": minute,
                "_last_minute": minute,
                "_decadal_starts": [row.get("decadal_start")],
                "bazi": row.get("bazi", {}),
                "ziwei": row.get("ziwei", {}),
                "time_basis": row.get("time_basis", {}),
            }
        else:
            current["_last_minute"] = minute
            current["_decadal_starts"].append(row.get("decadal_start"))
    if current is not None:
        states.append(_finalize_state(current, len(states) + 1))
    return states


def _finalize_state(current, index: int) -> dict:
    values = [item for item in current["_decadal_starts"] if isinstance(item, str)]
    decadal_range = [min(values), max(values)] if values else [None, None]
    return {
        "candidate_id": "candidate-%02d" % index,
        "reported_time_start": _minute_text(current["_first_minute"]),
        "reported_time_end": _minute_text(current["_last_minute"]),
        "sample_reported_time": _minute_text(current["_first_minute"]),
        "bazi": current["bazi"],
        "ziwei": current["ziwei"],
        "time_basis": current["time_basis"],
        "bazi_decadal_start_range": decadal_range,
    }


def _serialized(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _classify_mapping(rows):
    """Recursively split common and candidate-dependent JSON facts.

    A nested leaf is invariant only when every candidate contains the path and
    every value is identical. Mapping siblings are classified independently so,
    for example, a stable day pillar remains invariant even when the hour pillar
    varies. No majority value is ever promoted to invariant.
    """
    keys = set()
    for _, value in rows:
        if isinstance(value, Mapping):
            keys.update(value)

    invariant = {}
    variant = {}
    for field in sorted(keys):
        values = []
        all_present = True
        all_mappings = True
        for candidate_id, mapping in rows:
            if not isinstance(mapping, Mapping) or field not in mapping:
                value = _MISSING
                all_present = False
                all_mappings = False
            else:
                value = mapping[field]
                if not isinstance(value, Mapping):
                    all_mappings = False
            values.append((candidate_id, value))

        if all_present and all_mappings:
            child_invariant, child_variant = _classify_mapping(values)
            if child_invariant:
                invariant[field] = child_invariant
            if child_variant:
                variant[field] = child_variant
            if not child_invariant and not child_variant:
                invariant[field] = {}
            continue

        if all_present:
            serialized = [_serialized(value) for _, value in values]
            if serialized and all(item == serialized[0] for item in serialized[1:]):
                invariant[field] = values[0][1]
                continue

        variant[field] = {
            candidate_id: None if value is _MISSING else value
            for candidate_id, value in values
        }
    return invariant, variant


def _classify_tree(candidates, key: str):
    rows = []
    for candidate in candidates:
        candidate_id = candidate["candidate_id"]
        value = candidate.get(key, {})
        rows.append((candidate_id, value if isinstance(value, Mapping) else {}))
    return _classify_mapping(rows)


def classify_candidate_facts(candidates) -> dict:
    if not isinstance(candidates, (list, tuple)) or not candidates:
        raise ValueError("candidate list must not be empty")
    candidate_ids = set()
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            raise ValueError("candidate entries must be mappings")
        candidate_id = _candidate_id(candidate.get("candidate_id"))
        if candidate_id in candidate_ids:
            raise ValueError("candidate_id values must be unique")
        candidate_ids.add(candidate_id)
    invariant_bazi, variant_bazi = _classify_tree(candidates, "bazi")
    invariant_ziwei, variant_ziwei = _classify_tree(candidates, "ziwei")
    return {
        "invariant_bazi_facts": invariant_bazi,
        "variant_bazi_facts": variant_bazi,
        "invariant_ziwei_facts": invariant_ziwei,
        "variant_ziwei_facts": variant_ziwei,
    }


def _build_minute_candidate(birth_payload: Mapping[str, object], location: ResolvedBirthPlace, minute: int) -> dict:
    exact = dict(birth_payload)
    exact.pop("birth_time_range", None)
    exact["birth_time"] = _minute_text(minute)
    resolution = resolve_birth_input(exact, target="ziwei_natal")
    if not resolution.ok or resolution.input is None:
        raise NatalFoundationError(
            resolution.error_code or "birth_input_unresolved",
            "candidate minute could not resolve to an exact birth input",
            resolution.to_dict(),
        )
    project = build_project_natal(resolution.input, resolved_location=location).to_dict()
    bazi = _discrete_bazi(project["bazi"])
    ziwei = dict(project["ziwei"])
    time_basis = project.get("time_basis", {})
    return {
        "minute": minute,
        "signature": _signature(bazi, ziwei),
        "bazi": bazi,
        "ziwei": ziwei,
        "decadal_start": project["bazi"].get("decadal_start"),
        "time_basis": {
            "effective_hour_branch": time_basis.get("effective_hour_branch"),
            "bazi_effective_time": time_basis.get("bazi_effective_time"),
            "ziwei_effective_time": time_basis.get("ziwei_effective_time"),
            "true_solar_time": time_basis.get("true_solar_time"),
        },
    }


def build_candidate_envelope(birth_payload: Mapping[str, object], resolved_location: ResolvedBirthPlace) -> dict:
    if not isinstance(birth_payload, Mapping):
        raise NatalFoundationError("invalid_natal_input", "birth payload must be a mapping")
    if not isinstance(resolved_location, ResolvedBirthPlace):
        raise NatalFoundationError("missing_candidate_location_basis", "candidate envelope requires a resolved birth location")
    for field in ("sex", "birth_date", "birth_place"):
        if birth_payload.get(field) in (None, ""):
            raise NatalFoundationError("missing_required_birth_field", "candidate envelope is missing required birth basis", {"missing_fields": [field]})
    precision_state, minutes = _uncertainty_minutes(birth_payload)
    rows = []
    failures = []
    for minute in minutes:
        try:
            rows.append(_build_minute_candidate(birth_payload, resolved_location, minute))
        except (NatalFoundationError, BirthFoundationError) as exc:
            failures.append({
                "reported_time": _minute_text(minute),
                "error_code": getattr(exc, "code", "candidate_build_failed"),
                "message": str(exc),
            })
    if not rows:
        raise NatalFoundationError("candidate_envelope_empty", "no qualified candidate timing state could be built", {"failures": failures})
    candidates = partition_material_states(rows)
    classified = classify_candidate_facts(candidates)
    unresolved_time = precision_state in ("bounded", "unknown_time")
    return {
        "profile_id": _PROFILE_ID,
        "rule_version": _RULE_VERSION,
        "natal_precision_state": precision_state,
        "candidate_time_basis": "material_timing_state",
        "candidate_count": len(candidates),
        "known_facts": {
            "sex": birth_payload.get("sex"),
            "birth_date": birth_payload.get("birth_date"),
            "birth_place": birth_payload.get("birth_place"),
            "resolved_place_label": resolved_location.canonical_name,
            "timezone": resolved_location.timezone,
            "reported_birth_time": birth_payload.get("birth_time"),
            "reported_birth_time_range": birth_payload.get("birth_time_range"),
        },
        "candidates": candidates,
        **classified,
        "boundary_ambiguities": failures,
        "allowed_analysis": ["invariant_natal_structure", "candidate_comparison"],
        "blocked_analysis": [
            "unique_birth_time_claim",
            "unique_hour_pillar_conclusion",
            "unique_ziwei_natal_conclusion",
            "single_chart_personalized_forecast",
        ] if unresolved_time else [],
        "provenance": {
            "classification": "Project 原生盤面候選集合",
            "candidate_selection": "all civil minutes in declared uncertainty interval; contiguous identical discrete charts collapsed",
            "midpoint_used": False,
            "default_time_used": False,
        },
    }
