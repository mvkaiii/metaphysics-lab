"""Portable high-level natal actions.

This adapter converts JSON-safe payloads into the canonical natal engine models.
It performs validation and serialization only; metaphysical interpretation stays
with the AI workflow layer.
"""

from __future__ import annotations

from typing import Mapping, Optional

from engine.birth.errors import BirthFoundationError
from engine.birth.models import ResolvedBirthPlace
from engine.natal.errors import NatalFoundationError
from engine.natal.external import import_external_natal
from engine.natal.models import NatalSource, ProjectNatalView
from engine.natal.orchestration import (
    build_normalized_natal,
    build_project_natal,
    resolve_mode_a_input,
)

from .errors import DistributionError


_REQUIRED_LOCATION_FIELDS = (
    "canonical_name",
    "latitude",
    "longitude",
    "timezone",
    "provider_name",
    "provider_version",
)


def _require_mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise DistributionError(
            "invalid_payload",
            "%s must be a structured mapping" % field,
            {"field": field},
        )
    return value


def _require_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DistributionError(
            "invalid_resolved_location",
            "%s must be a non-empty string" % field,
            {"field": field},
        )
    return value.strip()


def resolved_location_from_payload(value: object) -> ResolvedBirthPlace:
    raw = _require_mapping(value, "resolved_location")
    missing = [field for field in _REQUIRED_LOCATION_FIELDS if raw.get(field) in (None, "")]
    if missing:
        raise DistributionError(
            "invalid_resolved_location",
            "pre-resolved location is missing required fields",
            {"missing_fields": missing},
        )

    latitude = raw.get("latitude")
    longitude = raw.get("longitude")
    if (
        not isinstance(latitude, (int, float))
        or isinstance(latitude, bool)
        or not -90.0 <= float(latitude) <= 90.0
        or not isinstance(longitude, (int, float))
        or isinstance(longitude, bool)
        or not -180.0 <= float(longitude) <= 180.0
    ):
        raise DistributionError(
            "invalid_resolved_location",
            "pre-resolved location coordinates are out of range",
            {"latitude": latitude, "longitude": longitude},
        )

    provider_reference = raw.get("provider_reference")
    if provider_reference is not None and not isinstance(provider_reference, str):
        raise DistributionError(
            "invalid_resolved_location",
            "provider_reference must be text or null",
            {"field": "provider_reference"},
        )

    resolution_status = raw.get("resolution_status", "resolved")
    return ResolvedBirthPlace(
        canonical_name=_require_text(raw.get("canonical_name"), "canonical_name"),
        latitude=float(latitude),
        longitude=float(longitude),
        timezone=_require_text(raw.get("timezone"), "timezone"),
        provider_name=_require_text(raw.get("provider_name"), "provider_name"),
        provider_version=_require_text(raw.get("provider_version"), "provider_version"),
        resolution_status=_require_text(resolution_status, "resolution_status"),
        provider_reference=provider_reference,
    )


def _foundation_error(exc: Exception) -> DistributionError:
    code = getattr(exc, "code", "natal_runtime_error")
    details = getattr(exc, "details", {})
    return DistributionError(str(code), str(exc), details)


def _network_provider(payload: Mapping[str, object]):
    raw = payload.get("network_location")
    if not isinstance(raw, Mapping) or raw.get("enabled") is not True:
        return None
    user_agent = raw.get("user_agent")
    if not isinstance(user_agent, str) or not user_agent.strip():
        raise DistributionError(
            "invalid_network_location_config",
            "network location resolution requires a non-empty user_agent",
            {"required_fields": ["enabled", "user_agent"]},
        )
    try:
        from engine.birth.location import NominatimLocationProvider
    except (ImportError, ModuleNotFoundError) as exc:
        raise DistributionError(
            "location_dependency_unavailable",
            "network location resolution dependencies are unavailable",
        ) from exc
    return NominatimLocationProvider(user_agent=user_agent.strip())


def build_natal(payload: Mapping[str, object]) -> dict:
    payload = _require_mapping(payload, "payload")
    birth_payload = _require_mapping(payload.get("birth", {}), "birth")
    resolution = resolve_mode_a_input(birth_payload)
    if not resolution.ok or resolution.input is None:
        details = resolution.to_dict()
        raise DistributionError(
            resolution.error_code or "birth_input_unresolved",
            "birth input is not precise enough for a full natal build",
            details,
        )

    raw_location = payload.get("resolved_location")
    location: Optional[ResolvedBirthPlace] = None
    provider = None
    if raw_location is not None:
        location = resolved_location_from_payload(raw_location)
    else:
        provider = _network_provider(payload)
        if provider is None:
            raise DistributionError(
                "location_resolution_required",
                "build_natal requires a pre-resolved location or explicitly enabled network resolution",
                {"required_fields": list(_REQUIRED_LOCATION_FIELDS)},
            )

    try:
        if location is not None:
            project = build_project_natal(
                resolution.input,
                resolved_location=location,
            )
            serialized_location = location.to_dict()
        else:
            project = build_project_natal(resolution.input, provider)
            serialized_location = {
                "canonical_name": project.birth.get("resolved_place_label"),
                "timezone": project.birth.get("timezone"),
                "provider_name": project.time_basis.get("location_provider"),
                "provider_version": project.time_basis.get("location_provider_version"),
            }
        normalized = build_normalized_natal(project=project)
    except (NatalFoundationError, BirthFoundationError) as exc:
        raise _foundation_error(exc) from exc

    return {
        "input_resolution": resolution.to_dict(),
        "resolved_location": serialized_location,
        "project_natal": project.to_dict(),
        "normalized_natal": normalized.to_dict(),
    }


def _source_from_payload(value: object, field: str) -> NatalSource:
    raw = _require_mapping(value, field)
    required = (
        "source_type",
        "source_name",
        "source_version",
        "rule_profile",
        "rule_version",
        "maturity",
        "validation_status",
    )
    missing = [name for name in required if raw.get(name) in (None, "")]
    if missing:
        raise DistributionError(
            "invalid_natal_source",
            "%s is missing source metadata" % field,
            {"field": field, "missing_fields": missing},
        )
    try:
        return NatalSource(**{name: str(raw[name]) for name in required})
    except NatalFoundationError as exc:
        raise _foundation_error(exc) from exc


def project_natal_from_payload(value: object) -> ProjectNatalView:
    raw = _require_mapping(value, "project_natal")
    for field in ("birth", "time_basis", "bazi", "ziwei", "source"):
        if field not in raw:
            raise DistributionError(
                "invalid_project_natal",
                "project_natal is missing required data",
                {"missing_fields": [field]},
            )
    try:
        return ProjectNatalView(
            birth=_require_mapping(raw["birth"], "project_natal.birth"),
            time_basis=_require_mapping(raw["time_basis"], "project_natal.time_basis"),
            bazi=_require_mapping(raw["bazi"], "project_natal.bazi"),
            ziwei=_require_mapping(raw["ziwei"], "project_natal.ziwei"),
            source=_source_from_payload(raw["source"], "project_natal.source"),
        )
    except NatalFoundationError as exc:
        raise _foundation_error(exc) from exc


def reconcile_natal(payload: Mapping[str, object]) -> dict:
    payload = _require_mapping(payload, "payload")
    project = project_natal_from_payload(payload.get("project_natal"))
    external_source = _source_from_payload(payload.get("external_source"), "external_source")
    external_chart = _require_mapping(payload.get("external_chart"), "external_chart")
    try:
        external = import_external_natal(external_chart, external_source)
        normalized = build_normalized_natal(project=project, external=external)
    except NatalFoundationError as exc:
        raise _foundation_error(exc) from exc
    return {
        "normalized_natal": normalized.to_dict(),
    }
