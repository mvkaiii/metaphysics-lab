"""Deterministic portable forecast-context orchestration.

The forecast adapter materializes only requested time scopes. It reuses the
canonical Bazi calendar, Calendar Resolver, Ziwei fine-cycle and flowing-star
engines and never performs metaphysical interpretation.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import fields, is_dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any, Mapping, Sequence

from engine.bazi.calendar import project_derived
from engine.calendar import resolve_calendar
from engine.ziwei.fine_cycle import build_fine_cycle_layer
from engine.ziwei.fine_cycle_stems import (
    resolve_day_stem,
    resolve_hour_stem,
    resolve_month_stem,
)
from engine.ziwei.flowing_star_sources import (
    source_from_daily,
    source_from_decadal,
    source_from_hourly,
    source_from_monthly,
    source_from_yearly,
)
from engine.ziwei.flowing_star_view import materialize_flowing_star_layer
from engine.ziwei.flowing_stars import build_flowing_star_layer
from engine.ziwei.models import ChartIdentity, LayerProvenance, StarLocationIndex
from engine.ziwei.natal_models import ZiweiDecadalPeriod, ZiweiPalaceRecord

from .errors import DistributionError


_ALLOWED_SCOPES = ("decadal", "yearly", "monthly", "daily", "hourly")
_FINE_RESOLVERS = {
    "monthly": resolve_month_stem,
    "daily": resolve_day_stem,
    "hourly": resolve_hour_stem,
}
_FINE_SOURCE_ADAPTERS = {
    "monthly": source_from_monthly,
    "daily": source_from_daily,
    "hourly": source_from_hourly,
}


def _mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise DistributionError(
            "invalid_forecast_payload",
            "%s must be a structured mapping" % field_name,
            {"field": field_name},
        )
    return value


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return [_json_safe(item) for item in sorted(value, key=repr)]
    if is_dataclass(value):
        return {field.name: _json_safe(getattr(value, field.name)) for field in fields(value)}
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return _json_safe(to_dict())
    raise TypeError("value is not JSON-safe: %r" % (type(value),))


def _canonical_digest(value: object) -> str:
    encoded = json.dumps(
        _json_safe(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_scopes(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or not value:
        raise DistributionError(
            "invalid_requested_scopes",
            "requested_scopes must be a non-empty list",
            {"allowed_scopes": list(_ALLOWED_SCOPES)},
        )
    scopes = tuple(value)
    if any(not isinstance(scope, str) or scope not in _ALLOWED_SCOPES for scope in scopes):
        raise DistributionError(
            "invalid_requested_scopes",
            "requested_scopes contains an unsupported scope",
            {"requested_scopes": list(scopes), "allowed_scopes": list(_ALLOWED_SCOPES)},
        )
    if len(set(scopes)) != len(scopes):
        raise DistributionError(
            "invalid_requested_scopes",
            "requested_scopes must not contain duplicates",
            {"requested_scopes": list(scopes)},
        )
    return scopes


def _project_basis(normalized: Mapping[str, Any]) -> Mapping[str, Any]:
    validation = _mapping(normalized.get("validation", {}), "normalized_natal.validation")
    blocking = validation.get("blocking_conflict_count", 0)
    if isinstance(blocking, bool) or not isinstance(blocking, int):
        raise DistributionError(
            "invalid_forecast_payload",
            "blocking_conflict_count must be an integer",
        )
    if blocking > 0:
        raise DistributionError(
            "forecast_basis_blocked",
            "forecast context cannot use a natal basis with BLOCKING conflicts",
            {"reason": "blocking_natal_conflict", "blocking_conflict_count": blocking},
        )

    project = normalized.get("project")
    if not isinstance(project, Mapping):
        raise DistributionError(
            "forecast_basis_blocked",
            "forecast context requires Project natal facts",
            {"reason": "missing_project_natal"},
        )
    ziwei = project.get("ziwei")
    required_ziwei = ("palaces", "stars", "decadal_cycles")
    if (
        not isinstance(ziwei, Mapping)
        or any(not ziwei.get(field) for field in required_ziwei[:2])
        or "decadal_cycles" not in ziwei
    ):
        raise DistributionError(
            "forecast_basis_blocked",
            "forecast context requires deterministic Project Ziwei natal facts",
            {"reason": "missing_project_ziwei_facts", "required_fields": list(required_ziwei)},
        )
    bazi = project.get("bazi")
    if not isinstance(bazi, Mapping) or not isinstance(bazi.get("day_master"), str):
        raise DistributionError(
            "forecast_basis_blocked",
            "forecast context requires deterministic Project Bazi natal facts",
            {"reason": "missing_project_bazi_facts", "required_fields": ["day_master"]},
        )
    return project


def _reconstruct_ziwei_basis(project: Mapping[str, Any]):
    ziwei = _mapping(project.get("ziwei"), "normalized_natal.project.ziwei")
    source = _mapping(project.get("source"), "normalized_natal.project.source")
    palace_rows = ziwei.get("palaces")
    star_rows = ziwei.get("stars")
    if not isinstance(palace_rows, (list, tuple)) or not isinstance(star_rows, (list, tuple)):
        raise DistributionError(
            "forecast_basis_blocked",
            "Project Ziwei palace/star facts have invalid shape",
            {"reason": "missing_project_ziwei_facts"},
        )
    try:
        palaces = tuple(
            ZiweiPalaceRecord(
                name=str(row["name"]),
                branch=str(row["branch"]),
                heavenly_stem=str(row["heavenly_stem"]),
                stem_branch=str(row["stem_branch"]),
            )
            for row in palace_rows
            if isinstance(row, Mapping)
        )
        if len(palaces) != len(palace_rows):
            raise ValueError("palace row must be mapping")
        locations = {
            str(row["star"]): str(row["palace"])
            for row in star_rows
            if isinstance(row, Mapping)
        }
        if len(locations) != len(star_rows):
            raise ValueError("star row must be mapping with unique star")
    except (KeyError, TypeError, ValueError) as exc:
        raise DistributionError(
            "forecast_basis_blocked",
            "Project Ziwei natal facts cannot be reconstructed",
            {"reason": "invalid_project_ziwei_facts", "error": str(exc)},
        ) from exc

    identity_facts = {
        "source": _json_safe(source),
        "palaces": _json_safe(palace_rows),
        "stars": _json_safe(star_rows),
    }
    digest = _canonical_digest(identity_facts)
    identity = ChartIdentity(
        chart_id="portable-natal-%s" % digest[:24],
        chart_basis="portable_reconstructed_project_natal",
        source_profile=str(source.get("rule_profile", "unknown")),
    )
    provenance = LayerProvenance(
        classification="project_native_reconstructed",
        source_name=str(source.get("source_name", "Metaphysics Lab")),
        source_version=str(source.get("source_version", "unknown")),
        rule_profile=str(source.get("rule_profile", "unknown")),
        rule_version=str(source.get("rule_version", "unknown")),
        derived_by="engine.distribution.forecast",
    )
    star_locations = StarLocationIndex(
        chart_identity=identity,
        locations=locations,
        validation_status=str(source.get("validation_status", "unknown")),
        provenance=provenance,
    )
    return identity, palaces, star_locations, digest


def _resolve_target(payload: Mapping[str, Any]):
    target = _mapping(payload.get("target"), "target")
    civil_datetime = target.get("civil_datetime")
    timezone = target.get("timezone")
    if not isinstance(civil_datetime, str) or not civil_datetime.strip():
        raise DistributionError(
            "invalid_forecast_target",
            "target.civil_datetime must be a non-empty ISO local datetime",
        )
    if not isinstance(timezone, str) or not timezone.strip():
        raise DistributionError(
            "invalid_forecast_target",
            "target.timezone must be a non-empty IANA timezone",
        )
    resolution = resolve_calendar(civil_datetime.strip(), timezone.strip(), target.get("utc_offset_hint"))
    if not resolution.ok or resolution.context is None:
        error = resolution.error
        raise DistributionError(
            "forecast_target_unresolved" if error is None else error.code,
            "target calendar resolution failed" if error is None else error.message,
            {} if error is None else error.details,
        )
    return resolution.context


def _materialized_scope(flowing_layer, palaces: Sequence[ZiweiPalaceRecord]) -> list[dict]:
    records = materialize_flowing_star_layer(flowing_layer, palaces)
    return _json_safe(records)


def _scope_envelope(
    *,
    scope: str,
    flowing_layer,
    palaces,
    resolved_cycle=None,
    transformation_layer=None,
    decadal_period=None,
) -> dict:
    payload = {
        "scope": scope,
        "reference": flowing_layer.identity.reference,
        "classification": flowing_layer.classification,
        "maturity": flowing_layer.maturity,
        "flowing_star_layer": _json_safe(flowing_layer),
        "materialized_flowing_stars": _materialized_scope(flowing_layer, palaces),
        "source_resolution_count": 1,
    }
    if resolved_cycle is not None:
        payload["resolved_cycle"] = _json_safe(resolved_cycle)
    if transformation_layer is not None:
        payload["transformation_layer"] = _json_safe(transformation_layer)
    if decadal_period is not None:
        payload["decadal_period"] = _json_safe(decadal_period)
    return payload


def _fine_scope(scope, context, identity, palaces, star_locations):
    resolution = _FINE_RESOLVERS[scope](context)
    transformation = build_fine_cycle_layer(resolution, identity, star_locations)
    source = _FINE_SOURCE_ADAPTERS[scope](resolution, identity)
    flowing = build_flowing_star_layer(source)
    return _scope_envelope(
        scope=scope,
        flowing_layer=flowing,
        palaces=palaces,
        resolved_cycle=resolution,
        transformation_layer=transformation,
    )


def _yearly_scope(context, identity, palaces):
    source = source_from_yearly(context, identity)
    flowing = build_flowing_star_layer(source)
    return _scope_envelope(
        scope="yearly",
        flowing_layer=flowing,
        palaces=palaces,
    )


def _decadal_period(project: Mapping[str, Any], requested_index: object) -> ZiweiDecadalPeriod:
    if not isinstance(requested_index, int) or isinstance(requested_index, bool) or requested_index < 1:
        raise DistributionError(
            "missing_decadal_index",
            "decadal forecast scope requires ziwei_decadal_index",
        )
    ziwei = _mapping(project.get("ziwei"), "normalized_natal.project.ziwei")
    rows = ziwei.get("decadal_cycles")
    if not isinstance(rows, (list, tuple)):
        raise DistributionError(
            "forecast_basis_blocked",
            "Project Ziwei decadal facts are missing",
            {"reason": "missing_project_ziwei_facts"},
        )
    selected = None
    for row in rows:
        if isinstance(row, Mapping) and row.get("index") == requested_index:
            selected = row
            break
    if selected is None:
        raise DistributionError(
            "invalid_decadal_index",
            "requested Ziwei decadal index is not stored in the natal facts",
            {"ziwei_decadal_index": requested_index},
        )
    try:
        return ZiweiDecadalPeriod(
            index=int(selected["index"]),
            age_start=int(selected["start_age"]),
            age_end=int(selected["end_age"]),
            palace=str(selected["palace"]),
            stem_branch=str(selected["stem_branch"]),
            direction=str(selected["direction"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise DistributionError(
            "forecast_basis_blocked",
            "stored Ziwei decadal period is invalid",
            {"reason": "invalid_project_ziwei_facts", "error": str(exc)},
        ) from exc


def _decadal_scope(project, requested_index, identity, palaces):
    period = _decadal_period(project, requested_index)
    source = source_from_decadal(period, identity)
    flowing = build_flowing_star_layer(source)
    return _scope_envelope(
        scope="decadal",
        flowing_layer=flowing,
        palaces=palaces,
        decadal_period=period,
    )


def resolve_forecast_context(payload: Mapping[str, object]) -> dict:
    payload = _mapping(payload, "payload")
    normalized = _mapping(payload.get("normalized_natal"), "normalized_natal")
    scopes = _validate_scopes(payload.get("requested_scopes"))
    project = _project_basis(normalized)
    if "decadal" in scopes and payload.get("ziwei_decadal_index") is None:
        raise DistributionError(
            "missing_decadal_index",
            "decadal forecast scope requires ziwei_decadal_index",
        )

    context = _resolve_target(payload)
    identity, palaces, star_locations, basis_digest = _reconstruct_ziwei_basis(project)

    bazi = _mapping(project.get("bazi"), "normalized_natal.project.bazi")
    try:
        bazi_context = project_derived(
            context.normalized_time.local_datetime,
            str(bazi["day_master"]),
        )
        ziwei = {}
        for scope in scopes:
            if scope in _FINE_RESOLVERS:
                ziwei[scope] = _fine_scope(scope, context, identity, palaces, star_locations)
            elif scope == "yearly":
                ziwei[scope] = _yearly_scope(context, identity, palaces)
            elif scope == "decadal":
                ziwei[scope] = _decadal_scope(
                    project,
                    payload.get("ziwei_decadal_index"),
                    identity,
                    palaces,
                )
    except DistributionError:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        code = getattr(exc, "code", "forecast_context_unavailable")
        details = getattr(exc, "details", {})
        raise DistributionError(str(code), str(exc), details) from exc

    return {
        "bazi": _json_safe(bazi_context),
        "calendar_context_summary": context.to_dict(),
        "ziwei": ziwei,
        "provenance": {
            "classification": "Project 推導盤面",
            "orchestrated_by": "engine.distribution.forecast",
            "target_calendar_resolutions": 1,
            "chart_identity": _json_safe(identity),
            "reconstructed_basis_digest": basis_digest,
            "chart_identity_note": "portable reconstruction from stored Project natal deterministic facts; not the original in-memory chart object",
        },
        "confidence_constraints": {
            "blocking_conflict_count": 0,
            "project_natal_maturity": _mapping(project.get("source"), "normalized_natal.project.source").get("maturity"),
            "ziwei_requested_scopes": list(scopes),
            "experimental_time_layers_must_be_downweighted": True,
        },
    }
