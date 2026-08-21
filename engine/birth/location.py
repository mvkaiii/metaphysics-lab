from __future__ import annotations

from typing import Optional, Protocol, Tuple

import geopy
from geopy.exc import GeopyError
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

from .errors import BirthFoundationError
from .models import BirthPlaceInput, GeocodeCandidate, ResolvedBirthPlace


class LocationProvider(Protocol):
    name: str
    version: str

    def geocode(self, query: str) -> Tuple[GeocodeCandidate, ...]:
        ...


_TIMEZONE_FINDER: Optional[TimezoneFinder] = None


def _get_timezone_finder() -> TimezoneFinder:
    global _TIMEZONE_FINDER
    if _TIMEZONE_FINDER is None:
        _TIMEZONE_FINDER = TimezoneFinder(in_memory=True)
    return _TIMEZONE_FINDER


def _provider_name(provider: LocationProvider) -> str:
    return str(getattr(provider, "name", provider.__class__.__name__))


def _provider_version(provider: LocationProvider) -> str:
    return str(getattr(provider, "version", "unknown"))


def resolve_birth_place(
    place: BirthPlaceInput,
    provider: LocationProvider,
) -> ResolvedBirthPlace:
    try:
        candidates = tuple(provider.geocode(place.label))
    except GeopyError as exc:
        raise BirthFoundationError(
            "location_provider_unavailable",
            "birth place provider is unavailable",
            {"provider": _provider_name(provider)},
        ) from exc
    except OSError as exc:
        raise BirthFoundationError(
            "location_provider_unavailable",
            "birth place provider is unavailable",
            {"provider": _provider_name(provider)},
        ) from exc

    if not candidates:
        raise BirthFoundationError(
            "location_not_resolved",
            "birth place could not be resolved",
            {"query": place.label, "provider": _provider_name(provider)},
        )
    if len(candidates) != 1:
        raise BirthFoundationError(
            "ambiguous_birth_place",
            "birth place resolved to multiple material candidates",
            {
                "query": place.label,
                "provider": _provider_name(provider),
                "candidate_count": len(candidates),
            },
        )

    candidate = candidates[0]
    if not (-90.0 <= candidate.latitude <= 90.0) or not (-180.0 <= candidate.longitude <= 180.0):
        raise BirthFoundationError(
            "location_not_resolved",
            "birth place provider returned invalid coordinates",
            {"provider": _provider_name(provider)},
        )

    timezone_name = _get_timezone_finder().timezone_at(
        lng=candidate.longitude,
        lat=candidate.latitude,
    )
    if not timezone_name:
        raise BirthFoundationError(
            "timezone_not_resolved",
            "IANA timezone could not be resolved from birth coordinates",
            {
                "latitude": candidate.latitude,
                "longitude": candidate.longitude,
            },
        )

    return ResolvedBirthPlace(
        canonical_name=candidate.name,
        latitude=candidate.latitude,
        longitude=candidate.longitude,
        timezone=timezone_name,
        provider_name=_provider_name(provider),
        provider_version=_provider_version(provider),
        resolution_status="resolved",
        provider_reference=candidate.raw_id,
    )


class NominatimLocationProvider:
    name = "nominatim"
    version = geopy.__version__

    def __init__(self, user_agent: str, timeout_seconds: float = 10.0) -> None:
        if not user_agent.strip():
            raise ValueError("Nominatim user_agent is required")
        self._geocoder = Nominatim(
            user_agent=user_agent,
            timeout=timeout_seconds,
        )

    @staticmethod
    def _minimal_name(raw: dict, fallback: str) -> str:
        address = raw.get("address") or {}
        locality = (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("municipality")
            or address.get("county")
            or address.get("state")
        )
        country = address.get("country")
        if locality and country:
            return "%s, %s" % (locality, country)
        if locality:
            return str(locality)
        if country:
            return str(country)
        return fallback

    def geocode(self, query: str) -> Tuple[GeocodeCandidate, ...]:
        locations = self._geocoder.geocode(
            query,
            exactly_one=False,
            limit=5,
            addressdetails=True,
            featuretype="city",
        )
        if not locations:
            return ()
        candidates = []
        for location in locations:
            raw = dict(location.raw or {})
            raw_id = raw.get("place_id") or raw.get("osm_id") or "unknown"
            address = raw.get("address") or {}
            candidates.append(
                GeocodeCandidate(
                    name=self._minimal_name(raw, query),
                    latitude=float(location.latitude),
                    longitude=float(location.longitude),
                    country_code=str(address.get("country_code", "")),
                    raw_id="nominatim:%s" % raw_id,
                )
            )
        return tuple(candidates)
