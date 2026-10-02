"""Candidate-envelope construction for bounded or unknown birth time.

v2 expands the declared civil-time uncertainty interval into every legal local-time
occurrence under the pinned timezone authority before evaluating natal charts.
Nonexistent local labels are deterministic exclusions, while fold labels expand to
multiple legal occurrences. Coverage is established before material-state compression
or invariant claims are authorized.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, timedelta
from typing import Mapping, Optional

from engine.bazi.capabilities import BAZI_CAPABILITIES
from engine.birth.capabilities import BIRTH_CAPABILITIES
from engine.birth.errors import BirthFoundationError
from engine.birth.input_resolution import resolve_birth_input
from engine.birth.models import ResolvedBirthPlace
from engine.calendar.models import CalendarResolverException
from engine.calendar.timezone import (
    TIMEZONE_PROFILE,
    TIMEZONE_SOURCE_REVISION,
    enumerate_local_time_occurrences,
)
from engine.ziwei.capabilities import ZIWEI_CAPABILITIES

from .errors import NatalFoundationError
from .orchestration import build_project_natal


_PROFILE_ID = "natal-candidate-envelope-v2"
_RULE_VERSION = "2.0-exp"
_LEGACY_PROFILE_ID = "natal-candidate-envelope-v1"
_LEGACY_RULE_VERSION = "1.0-exp"
_DOMAIN_GENERATOR_VERSION = "candidate-domain-v1"
_APPLICABILITY_CONTRACT = "field-applicability-v1"
_CONTINUOUS_BAZI_KEYS = frozenset(("decadal_start",))
_CONTINUOUS_PERIOD_KEYS = frozenset(("start_age_years", "end_age_years", "start_datetime", "end_datetime"))
_MISSING = object()
_CANDIDATE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(prefix: str, value: object) -> str:
    return "%s-%s" % (
        prefix,
        hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest(),
    )


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
    """Return declared civil-minute labels without inventing a midpoint/default.

    Legacy callers that omit birth_time_precision remain accepted by inferring the
    state from birth_time / birth_time_range. New callers may provide the explicit
    v1.9 precision state.
    """

    precision = birth_payload.get("birth_time_precision")
    has_time = birth_payload.get("birth_time") not in (None, "")
    raw_range = birth_payload.get("birth_time_range")
    has_range = raw_range not in (None, "")

    if precision not in (None, "", "exact", "bounded", "unknown_time"):
        raise NatalFoundationError(
            "invalid_birth_time_precision_state",
            "birth_time_precision must be exact, bounded, or unknown_time",
        )

    if precision in (None, ""):
        if has_time and has_range:
            raise NatalFoundationError(
                "invalid_birth_time_precision_state",
                "birth_time and birth_time_range cannot both be supplied",
            )
        if has_time:
            precision = "exact"
        elif has_range:
            precision = "bounded"
        else:
            precision = "unknown_time"

    if precision == "exact":
        if not has_time or has_range:
            raise NatalFoundationError(
                "invalid_birth_time_precision_state",
                "exact precision requires birth_time and forbids birth_time_range",
            )
        minute = _parse_minute(birth_payload.get("birth_time"))
        return "exact", range(minute, minute + 1)

    if precision == "bounded":
        if has_time or not has_range:
            raise NatalFoundationError(
                "invalid_birth_time_precision_state",
                "bounded precision requires birth_time_range and forbids birth_time",
            )
        if not isinstance(raw_range, (list, tuple)) or len(raw_range) != 2:
            raise NatalFoundationError("ambiguous_birth_time", "birth_time_range must contain start and end HH:MM")
        start = _parse_minute(raw_range[0])
        end = _parse_minute(raw_range[1])
        if end < start:
            raise NatalFoundationError(
                "ambiguous_birth_time",
                "birth_time_range cannot cross the civil-date boundary in v2",
            )
        return "bounded", range(start, end + 1)

    if has_time or has_range:
        raise NatalFoundationError(
            "invalid_birth_time_precision_state",
            "unknown_time precision forbids birth_time and birth_time_range",
        )
    return "unknown_time", range(0, 1440)


def _birth_date(value: object) -> date:
    if not isinstance(value, str):
        raise NatalFoundationError("ambiguous_birth_date", "birth_date must be YYYY-MM-DD")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise NatalFoundationError("ambiguous_birth_date", "birth_date must be valid YYYY-MM-DD") from exc
    if parsed.isoformat() != value:
        raise NatalFoundationError("ambiguous_birth_date", "birth_date must use canonical YYYY-MM-DD text")
    return parsed


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
    return hashlib.sha256(
        _canonical_json({"bazi": bazi, "ziwei": ziwei}).encode("utf-8")
    ).hexdigest()


def _occurrence_id(item: Mapping[str, object]) -> str:
    return _digest(
        "occ",
        {
            "civil_datetime": item["civil_datetime"],
            "utc_datetime": item["utc_datetime"],
            "utc_offset": item["utc_offset"],
            "timezone": item["timezone"],
            "fold": item["fold"],
        },
    )[:4 + 24]


def _candidate_domain(
    birth_payload: Mapping[str, object],
    location: ResolvedBirthPlace,
    precision_state: str,
    minutes,
) -> dict:
    civil_date = _birth_date(birth_payload.get("birth_date"))
    minute_values = list(minutes)
    occurrences = []
    exclusions = []

    for minute in minute_values:
        reported_time = _minute_text(minute)
        civil_datetime = "%sT%s:00" % (civil_date.isoformat(), reported_time)
        try:
            legal = enumerate_local_time_occurrences(civil_datetime, location.timezone)
        except CalendarResolverException as exc:
            raise NatalFoundationError(
                exc.code,
                "candidate timezone domain could not be resolved",
                dict(exc.details),
            ) from exc
        if not legal:
            exclusions.append(
                {
                    "reported_time": reported_time,
                    "civil_datetime": civil_datetime,
                    "error_code": "nonexistent_local_time",
                    "category": "deterministic_exclusion",
                }
            )
            continue
        for item in legal:
            raw = {
                "minute": minute,
                "reported_time": reported_time,
                "civil_datetime": civil_datetime,
                "local_datetime": item.local_datetime.isoformat(),
                "utc_datetime": item.utc_datetime.isoformat(),
                "utc_offset": item.utc_offset,
                "timezone": item.timezone,
                "fold": item.fold,
            }
            raw["occurrence_id"] = _occurrence_id(raw)
            occurrences.append(raw)

    occurrences.sort(key=lambda item: (item["utc_datetime"], item["civil_datetime"], item["utc_offset"]))

    if precision_state == "exact":
        if not occurrences:
            local_time_resolution = "nonexistent"
        elif len(occurrences) == 1:
            local_time_resolution = "unique"
        else:
            local_time_resolution = "ambiguous_fold"
    elif precision_state == "bounded":
        local_time_resolution = "range"
    else:
        local_time_resolution = "unknown"

    interval = [
        _minute_text(minute_values[0]),
        _minute_text(minute_values[-1]),
    ] if minute_values else [None, None]

    digest_payload = {
        "generator_version": _DOMAIN_GENERATOR_VERSION,
        "birth_date": civil_date.isoformat(),
        "timezone": location.timezone,
        "uncertainty_kind": precision_state,
        "declared_interval": interval,
        "timezone_profile": TIMEZONE_PROFILE,
        "timezone_source_revision": TIMEZONE_SOURCE_REVISION,
        "occurrences": [
            {
                "occurrence_id": item["occurrence_id"],
                "civil_datetime": item["civil_datetime"],
                "utc_datetime": item["utc_datetime"],
                "utc_offset": item["utc_offset"],
                "fold": item["fold"],
            }
            for item in occurrences
        ],
        "deterministic_exclusions": exclusions,
    }

    return {
        "status": "ready" if occurrences else "unsupported",
        "uncertainty_kind": precision_state,
        "local_time_resolution": local_time_resolution,
        "generator_version": _DOMAIN_GENERATOR_VERSION,
        "declared_interval": interval,
        "declared_label_count": len(minute_values),
        "legal_occurrence_count": len(occurrences),
        "excluded_label_count": len(exclusions),
        "timezone": location.timezone,
        "timezone_profile": TIMEZONE_PROFILE,
        "timezone_source_revision": TIMEZONE_SOURCE_REVISION,
        "domain_digest": _digest("domain", digest_payload),
        "deterministic_exclusions": exclusions,
        "_occurrences": occurrences,
    }


def _evaluation_identity(location: ResolvedBirthPlace) -> str:
    payload = {
        "candidate_profile": _PROFILE_ID,
        "candidate_rule_version": _RULE_VERSION,
        "birth_input_rule_version": BIRTH_CAPABILITIES["birth.input_resolution"]["rule_version"],
        "true_solar_rule_version": BIRTH_CAPABILITIES["birth.true_solar_time"]["rule_version"],
        "bazi_rule_version": BAZI_CAPABILITIES["bazi.natal_chart"]["rule_version"],
        "ziwei_rule_version": ZIWEI_CAPABILITIES["ziwei.natal_chart"]["rule_version"],
        "location": {
            "canonical_name": location.canonical_name,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "timezone": location.timezone,
            "provider_name": location.provider_name,
            "provider_version": location.provider_version,
            "provider_reference": location.provider_reference,
        },
    }
    return _digest("evaluation", payload)


def _rows_contiguous(previous: Mapping[str, object], current: Mapping[str, object]) -> bool:
    previous_utc = previous.get("utc_datetime")
    current_utc = current.get("utc_datetime")
    if isinstance(previous_utc, str) and isinstance(current_utc, str):
        try:
            left = datetime.fromisoformat(previous_utc)
            right = datetime.fromisoformat(current_utc)
        except ValueError:
            return False
        return right - left == timedelta(minutes=1)
    return int(current["minute"]) == int(previous["minute"]) + 1


def partition_material_states(minute_rows):
    if not isinstance(minute_rows, (list, tuple)):
        raise ValueError("minute_rows must be a list")
    states = []
    current = None
    previous_row = None
    for raw in minute_rows:
        row = dict(raw)
        minute = int(row["minute"])
        signature = str(row["signature"])
        if (
            current is None
            or signature != current["_signature"]
            or previous_row is None
            or not _rows_contiguous(previous_row, row)
        ):
            if current is not None:
                states.append(_finalize_state(current, len(states) + 1))
            current = {
                "_signature": signature,
                "_first_minute": minute,
                "_last_minute": minute,
                "_first_occurrence": row.get("occurrence"),
                "_last_occurrence": row.get("occurrence"),
                "_occurrence_count": 1,
                "_decadal_starts": [row.get("decadal_start")],
                "bazi": row.get("bazi", {}),
                "ziwei": row.get("ziwei", {}),
                "time_basis": row.get("time_basis", {}),
            }
        else:
            current["_last_minute"] = minute
            current["_last_occurrence"] = row.get("occurrence")
            current["_occurrence_count"] += 1
            current["_decadal_starts"].append(row.get("decadal_start"))
        previous_row = row
    if current is not None:
        states.append(_finalize_state(current, len(states) + 1))
    return states


def _finalize_state(current, index: int) -> dict:
    values = [item for item in current["_decadal_starts"] if isinstance(item, str)]
    decadal_range = [min(values), max(values)] if values else [None, None]
    result = {
        "candidate_id": "candidate-%02d" % index,
        "reported_time_start": _minute_text(current["_first_minute"]),
        "reported_time_end": _minute_text(current["_last_minute"]),
        "sample_reported_time": _minute_text(current["_first_minute"]),
        "bazi": current["bazi"],
        "ziwei": current["ziwei"],
        "time_basis": current["time_basis"],
        "bazi_decadal_start_range": decadal_range,
    }
    if isinstance(current.get("_first_occurrence"), Mapping):
        result["occurrence_count"] = current["_occurrence_count"]
        result["occurrence_start"] = dict(current["_first_occurrence"])
        result["occurrence_end"] = dict(current["_last_occurrence"])
    return result


def _serialized(value: object) -> str:
    return _canonical_json(value)


def _classify_mapping(rows):
    """Recursively split common and candidate-dependent JSON facts."""

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


def classify_candidate_applicability(
    candidates,
    *,
    bazi_coverage_complete: bool,
    ziwei_coverage_complete: bool,
) -> dict:
    if not candidates:
        return {
            "invariant_bazi_facts": {},
            "variant_bazi_facts": {},
            "undetermined_bazi_facts": {},
            "unavailable_bazi_facts": {},
            "invariant_ziwei_facts": {},
            "variant_ziwei_facts": {},
            "undetermined_ziwei_facts": {},
            "unavailable_ziwei_facts": {},
        }

    observed = classify_candidate_facts(candidates)
    return {
        "invariant_bazi_facts": observed["invariant_bazi_facts"] if bazi_coverage_complete else {},
        "variant_bazi_facts": observed["variant_bazi_facts"],
        "undetermined_bazi_facts": {} if bazi_coverage_complete else observed["invariant_bazi_facts"],
        "unavailable_bazi_facts": {},
        "invariant_ziwei_facts": observed["invariant_ziwei_facts"] if ziwei_coverage_complete else {},
        "variant_ziwei_facts": observed["variant_ziwei_facts"],
        "undetermined_ziwei_facts": {} if ziwei_coverage_complete else observed["invariant_ziwei_facts"],
        "unavailable_ziwei_facts": {},
    }


def _build_minute_candidate(
    birth_payload: Mapping[str, object],
    location: ResolvedBirthPlace,
    minute: int,
) -> dict:
    """Legacy v1 candidate evaluator retained for v1 Case verification."""

    exact = dict(birth_payload)
    exact.pop("birth_time_range", None)
    exact["birth_time_precision"] = "exact"
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


def _build_occurrence_candidate(
    birth_payload: Mapping[str, object],
    location: ResolvedBirthPlace,
    occurrence: Mapping[str, object],
) -> dict:
    exact = dict(birth_payload)
    exact.pop("birth_time_range", None)
    exact["birth_time_precision"] = "exact"
    exact["birth_time"] = occurrence["reported_time"]
    resolution = resolve_birth_input(exact, target="ziwei_natal")
    if not resolution.ok or resolution.input is None:
        raise NatalFoundationError(
            resolution.error_code or "birth_input_unresolved",
            "candidate occurrence could not resolve to an exact birth input",
            resolution.to_dict(),
        )
    project = build_project_natal(
        resolution.input,
        resolved_location=location,
        utc_offset_hint=str(occurrence["utc_offset"]),
    ).to_dict()
    bazi = _discrete_bazi(project["bazi"])
    ziwei = dict(project["ziwei"])
    time_basis = project.get("time_basis", {})
    occurrence_view = {
        key: occurrence[key]
        for key in (
            "occurrence_id",
            "reported_time",
            "civil_datetime",
            "local_datetime",
            "utc_datetime",
            "utc_offset",
            "timezone",
            "fold",
        )
    }
    return {
        "minute": int(occurrence["minute"]),
        "utc_datetime": occurrence["utc_datetime"],
        "signature": _signature(bazi, ziwei),
        "bazi": bazi,
        "ziwei": ziwei,
        "decadal_start": project["bazi"].get("decadal_start"),
        "occurrence": occurrence_view,
        "time_basis": {
            "effective_hour_branch": time_basis.get("effective_hour_branch"),
            "bazi_effective_time": time_basis.get("bazi_effective_time"),
            "ziwei_effective_time": time_basis.get("ziwei_effective_time"),
            "true_solar_time": time_basis.get("true_solar_time"),
        },
    }


def _known_facts(
    normalized_birth: Mapping[str, object],
    resolved_location: ResolvedBirthPlace,
) -> dict:
    return {
        "sex": normalized_birth.get("sex"),
        "birth_date": normalized_birth.get("birth_date"),
        "birth_place": normalized_birth.get("birth_place"),
        "resolved_place_label": resolved_location.canonical_name,
        "timezone": resolved_location.timezone,
        "reported_birth_time": normalized_birth.get("birth_time"),
        "reported_birth_time_range": normalized_birth.get("birth_time_range"),
    }


def build_candidate_envelope_v1_legacy(
    birth_payload: Mapping[str, object],
    resolved_location: ResolvedBirthPlace,
) -> dict:
    """Reproduce legacy v1 semantics for old Case validation only."""

    if not isinstance(birth_payload, Mapping):
        raise NatalFoundationError("invalid_natal_input", "birth payload must be a mapping")
    if not isinstance(resolved_location, ResolvedBirthPlace):
        raise NatalFoundationError("missing_candidate_location_basis", "candidate envelope requires a resolved birth location")

    normalized_birth = dict(birth_payload)
    normalized_birth.pop("birth_time_precision", None)
    if normalized_birth.get("birth_time") == "":
        normalized_birth["birth_time"] = None
    for field in ("sex", "birth_date", "birth_place"):
        if normalized_birth.get(field) in (None, ""):
            raise NatalFoundationError(
                "missing_required_birth_field",
                "candidate envelope is missing required birth basis",
                {"missing_fields": [field]},
            )

    precision_state, minutes = _uncertainty_minutes(normalized_birth)
    rows = []
    failures = []
    for minute in minutes:
        try:
            rows.append(_build_minute_candidate(normalized_birth, resolved_location, minute))
        except (NatalFoundationError, BirthFoundationError) as exc:
            failures.append(
                {
                    "reported_time": _minute_text(minute),
                    "error_code": getattr(exc, "code", "candidate_build_failed"),
                    "message": str(exc),
                }
            )
    if not rows:
        raise NatalFoundationError(
            "candidate_envelope_empty",
            "no qualified candidate timing state could be built",
            {"failures": failures},
        )

    candidates = partition_material_states(rows)
    classified = classify_candidate_facts(candidates)
    unresolved_time = precision_state in ("bounded", "unknown_time")
    return {
        "profile_id": _LEGACY_PROFILE_ID,
        "rule_version": _LEGACY_RULE_VERSION,
        "natal_precision_state": precision_state,
        "candidate_time_basis": "material_timing_state",
        "candidate_count": len(candidates),
        "known_facts": _known_facts(normalized_birth, resolved_location),
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


def build_candidate_envelope(
    birth_payload: Mapping[str, object],
    resolved_location: ResolvedBirthPlace,
) -> dict:
    if not isinstance(birth_payload, Mapping):
        raise NatalFoundationError("invalid_natal_input", "birth payload must be a mapping")
    if not isinstance(resolved_location, ResolvedBirthPlace):
        raise NatalFoundationError("missing_candidate_location_basis", "candidate envelope requires a resolved birth location")

    normalized_birth = dict(birth_payload)
    if normalized_birth.get("birth_time") == "":
        normalized_birth["birth_time"] = None
    for field in ("sex", "birth_date", "birth_place"):
        if normalized_birth.get(field) in (None, ""):
            raise NatalFoundationError(
                "missing_required_birth_field",
                "candidate envelope is missing required birth basis",
                {"missing_fields": [field]},
            )

    precision_state, minutes = _uncertainty_minutes(normalized_birth)
    domain = _candidate_domain(normalized_birth, resolved_location, precision_state, minutes)
    occurrences = list(domain.pop("_occurrences"))
    evaluation_identity = _evaluation_identity(resolved_location)

    rows = []
    failures = []
    for occurrence in occurrences:
        try:
            rows.append(
                _build_occurrence_candidate(
                    normalized_birth,
                    resolved_location,
                    occurrence,
                )
            )
        except (NatalFoundationError, BirthFoundationError, CalendarResolverException) as exc:
            failures.append(
                {
                    "occurrence_id": occurrence["occurrence_id"],
                    "reported_time": occurrence["reported_time"],
                    "utc_offset": occurrence["utc_offset"],
                    "fold": occurrence["fold"],
                    "error_code": getattr(exc, "code", "candidate_build_failed"),
                    "message": str(exc),
                    "category": "candidate_build_error",
                }
            )

    candidates = partition_material_states(rows) if rows else []
    legal_count = domain["legal_occurrence_count"]
    evaluated_count = len(rows)
    if legal_count == 0:
        coverage_status = "unsupported"
    elif evaluated_count == legal_count:
        coverage_status = "complete"
    else:
        coverage_status = "partial"

    component_status = coverage_status
    unresolved_occurrences = [
        {
            "occurrence_id": failure["occurrence_id"],
            "reported_time": failure["reported_time"],
            "utc_offset": failure["utc_offset"],
            "fold": failure["fold"],
            "error_code": failure["error_code"],
        }
        for failure in failures
    ]

    coverage_payload = {
        "domain_digest": domain["domain_digest"],
        "evaluation_identity": evaluation_identity,
        "status": coverage_status,
        "materialized_occurrence_ids": [
            row["occurrence"]["occurrence_id"] for row in rows
        ],
        "unresolved_occurrences": unresolved_occurrences,
    }
    coverage = {
        "status": coverage_status,
        "evaluation_identity": evaluation_identity,
        "legal_occurrence_count": legal_count,
        "materialized_occurrence_count": evaluated_count,
        "unresolved_occurrence_count": max(0, legal_count - evaluated_count),
        "material_state_count": len(candidates),
        "components": {
            "bazi": {
                "status": component_status,
                "materialized_occurrence_count": evaluated_count,
            },
            "ziwei": {
                "status": component_status,
                "materialized_occurrence_count": evaluated_count,
            },
        },
        "failure_groups": failures,
        "unresolved_occurrences": unresolved_occurrences,
        "coverage_digest": _digest("coverage", coverage_payload),
    }

    classified = classify_candidate_applicability(
        candidates,
        bazi_coverage_complete=component_status == "complete",
        ziwei_coverage_complete=component_status == "complete",
    )

    ambiguous_exact = (
        precision_state == "exact"
        and domain["local_time_resolution"] == "ambiguous_fold"
    )
    unresolved_time = precision_state in ("bounded", "unknown_time") or ambiguous_exact
    complete_for_analysis = coverage_status == "complete" and bool(candidates)

    if coverage_status == "complete":
        allowed_analysis = ["invariant_natal_structure", "candidate_comparison"]
    elif coverage_status == "partial":
        allowed_analysis = ["observed_candidate_comparison"]
    else:
        allowed_analysis = []

    blocked_analysis = []
    if unresolved_time or not complete_for_analysis:
        blocked_analysis = [
            "unique_birth_time_claim",
            "unique_hour_pillar_conclusion",
            "unique_ziwei_natal_conclusion",
            "single_chart_personalized_forecast",
        ]

    boundary_ambiguities = [
        dict(item) for item in domain["deterministic_exclusions"]
    ] + [dict(item) for item in failures]

    return {
        "profile_id": _PROFILE_ID,
        "rule_version": _RULE_VERSION,
        "applicability_contract": _APPLICABILITY_CONTRACT,
        "natal_precision_state": precision_state,
        "local_time_resolution": domain["local_time_resolution"],
        "candidate_time_basis": "legal_occurrence_material_state",
        "candidate_count": len(candidates),
        "known_facts": _known_facts(normalized_birth, resolved_location),
        "candidate_domain": domain,
        "candidate_coverage": coverage,
        "candidates": candidates,
        **classified,
        "boundary_ambiguities": boundary_ambiguities,
        "allowed_analysis": allowed_analysis,
        "blocked_analysis": blocked_analysis,
        "provenance": {
            "classification": "Project 原生盤面候選集合",
            "candidate_selection": "legal local-time occurrences in declared uncertainty interval; contiguous identical discrete charts collapsed after coverage classification",
            "midpoint_used": False,
            "default_time_used": False,
            "coverage_before_compression": True,
            "candidate_probability_model": None,
        },
    }
