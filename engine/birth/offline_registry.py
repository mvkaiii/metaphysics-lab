"""Deterministic offline birth-place registry for portable natal builds."""
from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence

from .errors import BirthFoundationError
from .models import ResolvedBirthPlace


REGISTRY_PROVIDER_NAME = "metaphysics_lab_offline_registry"
DEFAULT_REGISTRY_RELATIVE_PATH = "data/birth_places/registry.v1.json"
_SEPARATOR_PATTERN = re.compile(r"[\s\-‐‑‒–—―_/\\,，、.。:：;；]+", re.UNICODE)
_REQUIRED_RECORD_FIELDS = (
    "record_id",
    "canonical_name",
    "country_code",
    "admin_area",
    "latitude",
    "longitude",
    "timezone",
    "aliases",
    "source",
    "source_version",
    "source_reference",
)


def normalize_birth_place_alias(value: str) -> str:
    """Apply only the Project-approved conservative alias normalization."""
    if not isinstance(value, str):
        raise TypeError("birth-place alias must be text")
    normalized = unicodedata.normalize("NFKC", value).strip().casefold()
    normalized = _SEPARATOR_PATTERN.sub(" ", normalized)
    return " ".join(normalized.split())


def _require_text(record: Mapping[str, object], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError("offline birth-place record %s must be non-empty text" % field)
    return value.strip()


def _require_coordinate(record: Mapping[str, object], field: str, minimum: float, maximum: float) -> float:
    value = record.get(field)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("offline birth-place record %s must be numeric" % field)
    number = float(value)
    if not minimum <= number <= maximum:
        raise ValueError("offline birth-place record %s out of range" % field)
    return number


def _validated_record(record: Mapping[str, object]) -> Dict[str, object]:
    if not isinstance(record, Mapping):
        raise ValueError("offline birth-place record must be an object")
    missing = [field for field in _REQUIRED_RECORD_FIELDS if field not in record]
    if missing:
        raise ValueError("offline birth-place record missing fields: %s" % ", ".join(missing))
    record_id = _require_text(record, "record_id")
    canonical_name = _require_text(record, "canonical_name")
    country_code = _require_text(record, "country_code")
    if len(country_code) != 2 or country_code.upper() != country_code or not country_code.isalpha():
        raise ValueError("offline birth-place country_code must be ISO-like uppercase alpha-2")
    admin_area = record.get("admin_area")
    if admin_area is not None and not isinstance(admin_area, str):
        raise ValueError("offline birth-place admin_area must be text or null")
    latitude = _require_coordinate(record, "latitude", -90.0, 90.0)
    longitude = _require_coordinate(record, "longitude", -180.0, 180.0)
    timezone = _require_text(record, "timezone")
    aliases_raw = record.get("aliases")
    if not isinstance(aliases_raw, list) or not aliases_raw:
        raise ValueError("offline birth-place aliases must be a non-empty list")
    aliases: List[str] = []
    normalized_seen = set()
    for alias in aliases_raw:
        if not isinstance(alias, str) or not alias.strip():
            raise ValueError("offline birth-place aliases must contain non-empty text")
        clean = alias.strip()
        key = normalize_birth_place_alias(clean)
        if not key:
            raise ValueError("offline birth-place alias normalizes to empty text")
        if key in normalized_seen:
            raise ValueError("duplicate normalized alias within record %s: %s" % (record_id, clean))
        normalized_seen.add(key)
        aliases.append(clean)
    canonical_key = normalize_birth_place_alias(canonical_name)
    if canonical_key not in normalized_seen:
        aliases.append(canonical_name)
        normalized_seen.add(canonical_key)
    return {
        "record_id": record_id,
        "canonical_name": canonical_name,
        "country_code": country_code,
        "admin_area": admin_area.strip() if isinstance(admin_area, str) else None,
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone,
        "aliases": aliases,
        "source": _require_text(record, "source"),
        "source_version": _require_text(record, "source_version"),
        "source_reference": _require_text(record, "source_reference"),
    }


class OfflineBirthPlaceRegistry:
    def __init__(self, *, version: str, coverage_profile: str, records: Sequence[Mapping[str, object]]) -> None:
        if not isinstance(version, str) or not version.strip():
            raise ValueError("offline registry version must be non-empty text")
        if not isinstance(coverage_profile, str) or not coverage_profile.strip():
            raise ValueError("offline registry coverage_profile must be non-empty text")
        if not isinstance(records, Sequence) or isinstance(records, (str, bytes)):
            raise ValueError("offline registry records must be a sequence")
        self.version = version.strip()
        self.coverage_profile = coverage_profile.strip()
        validated = [_validated_record(record) for record in records]
        record_ids = [str(record["record_id"]) for record in validated]
        if len(record_ids) != len(set(record_ids)):
            raise ValueError("offline registry record_id values must be unique")
        self.records = tuple(validated)
        index: Dict[str, List[Dict[str, object]]] = {}
        for record in validated:
            for alias in record["aliases"]:
                key = normalize_birth_place_alias(str(alias))
                index.setdefault(key, []).append(record)
        self._alias_index = {key: tuple(value) for key, value in index.items()}

    def resolve(self, label: str) -> Optional[ResolvedBirthPlace]:
        key = normalize_birth_place_alias(label)
        if not key:
            return None
        matches = self._alias_index.get(key, ())
        if not matches:
            return None
        if len(matches) > 1:
            raise BirthFoundationError(
                "ambiguous_birth_place",
                "offline birth-place alias matches multiple registry records",
                {
                    "query": label,
                    "normalized_query": key,
                    "candidate_count": len(matches),
                    "candidates": [
                        {
                            "record_id": row["record_id"],
                            "canonical_name": row["canonical_name"],
                            "country_code": row["country_code"],
                            "admin_area": row["admin_area"],
                        }
                        for row in matches
                    ],
                },
            )
        record = matches[0]
        return ResolvedBirthPlace(
            canonical_name=str(record["canonical_name"]),
            latitude=float(record["latitude"]),
            longitude=float(record["longitude"]),
            timezone=str(record["timezone"]),
            provider_name=REGISTRY_PROVIDER_NAME,
            provider_version=self.version,
            resolution_status="resolved_offline_registry",
            provider_reference=(
                "registry:%s:%s:source=%s"
                % (self.version, record["record_id"], record["source_reference"])
            ),
        )

    def metadata(self) -> dict:
        source_profiles = sorted(
            set("%s:%s" % (row["source"], row["source_version"]) for row in self.records)
        )
        return {
            "version": self.version,
            "coverage_profile": self.coverage_profile,
            "record_count": len(self.records),
            "source_profiles": source_profiles,
        }


def load_offline_birth_place_registry(path: Optional[Path] = None) -> OfflineBirthPlaceRegistry:
    target = Path(path) if path is not None else Path(__file__).resolve().parents[2] / DEFAULT_REGISTRY_RELATIVE_PATH
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BirthFoundationError(
            "offline_registry_unavailable",
            "offline birth-place registry could not be loaded",
            {"path": str(target), "reason": str(exc)},
        ) from exc
    if not isinstance(raw, Mapping):
        raise BirthFoundationError("offline_registry_invalid", "offline birth-place registry root must be an object")
    try:
        version = raw["version"]
        coverage_profile = raw["coverage_profile"]
        records = raw["records"]
        if not isinstance(records, list):
            raise ValueError("records must be a list")
        return OfflineBirthPlaceRegistry(
            version=str(version),
            coverage_profile=str(coverage_profile),
            records=records,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise BirthFoundationError(
            "offline_registry_invalid",
            "offline birth-place registry failed validation",
            {"reason": str(exc)},
        ) from exc


@lru_cache(maxsize=1)
def _default_registry() -> OfflineBirthPlaceRegistry:
    return load_offline_birth_place_registry()


def resolve_offline_birth_place(label: str) -> Optional[ResolvedBirthPlace]:
    return _default_registry().resolve(label)


def offline_birth_place_registry_metadata() -> dict:
    return _default_registry().metadata()
