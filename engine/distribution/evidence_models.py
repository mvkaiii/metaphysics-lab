"""Immutable evidence feature contract for 林氏天機 v1.5 Phase 2."""

from __future__ import annotations

from dataclasses import dataclass
import math
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .errors import DistributionError

SYSTEMS = ("bazi", "ziwei", "qimen", "historical", "reality")
SCOPES = ("natal", "major_cycle", "decadal", "yearly", "monthly", "daily", "hourly")
ROLES = ("target_evidence", "modifier", "timing_trigger", "personalization", "reality_constraint")
MATURITY_STATES = ("stable", "experimental")
QUALIFICATION_STATES = ("qualified", "needs_verification", "unqualified")
STRENGTH_CLASSES = ("unspecified", "weak", "moderate", "strong")

_FIELDS = (
    "feature_id",
    "system",
    "scope",
    "reference_window",
    "primary_domain",
    "event_family_support",
    "strength_class",
    "maturity",
    "qualification_status",
    "source_family",
    "dependency_family",
    "role",
    "provenance",
)


def _raise(field: str, message: str, **details: Any) -> None:
    payload = {"field": field}
    payload.update(details)
    raise DistributionError("invalid_evidence_feature", message, payload)


def _require_text(field: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        _raise(field, f"{field} must be a non-empty string")
    return value.strip()


def _freeze_json(field: str, value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            _raise(field, f"{field} must contain finite JSON numbers")
        return value
    if isinstance(value, Mapping):
        frozen = {}
        for key, item in value.items():
            if not isinstance(key, str):
                _raise(field, f"{field} mapping keys must be strings")
            frozen[key] = _freeze_json(field, item)
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(field, item) for item in value)
    _raise(field, f"{field} must be JSON-serializable")
    raise AssertionError("unreachable")


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


def _require_enum(field: str, value: Any, allowed: Tuple[str, ...]) -> str:
    normalized = _require_text(field, value)
    if normalized not in allowed:
        _raise(field, f"unsupported {field}", value=normalized, allowed=allowed)
    return normalized


@dataclass(frozen=True)
class EvidenceFeature:
    feature_id: str
    system: str
    scope: str
    reference_window: Mapping[str, Any]
    primary_domain: str
    event_family_support: Tuple[str, ...]
    strength_class: str
    maturity: str
    qualification_status: str
    source_family: str
    dependency_family: str
    role: str
    provenance: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "feature_id", _require_text("feature_id", self.feature_id))
        object.__setattr__(self, "system", _require_enum("system", self.system, SYSTEMS))
        object.__setattr__(self, "scope", _require_enum("scope", self.scope, SCOPES))
        if not isinstance(self.reference_window, Mapping):
            _raise("reference_window", "reference_window must be a mapping")
        object.__setattr__(self, "reference_window", _freeze_json("reference_window", self.reference_window))
        object.__setattr__(self, "primary_domain", _require_text("primary_domain", self.primary_domain))

        if not isinstance(self.event_family_support, (list, tuple)):
            _raise("event_family_support", "event_family_support must be a sequence of strings")
        families = tuple(_require_text("event_family_support", item) for item in self.event_family_support)
        if len(set(families)) != len(families):
            _raise("event_family_support", "event_family_support must not contain duplicates")
        object.__setattr__(self, "event_family_support", families)

        object.__setattr__(
            self,
            "strength_class",
            _require_enum("strength_class", self.strength_class, STRENGTH_CLASSES),
        )
        object.__setattr__(self, "maturity", _require_enum("maturity", self.maturity, MATURITY_STATES))
        object.__setattr__(
            self,
            "qualification_status",
            _require_enum("qualification_status", self.qualification_status, QUALIFICATION_STATES),
        )
        object.__setattr__(self, "source_family", _require_text("source_family", self.source_family))
        object.__setattr__(self, "dependency_family", _require_text("dependency_family", self.dependency_family))
        object.__setattr__(self, "role", _require_enum("role", self.role, ROLES))
        if not isinstance(self.provenance, Mapping):
            _raise("provenance", "provenance must be a mapping")
        object.__setattr__(self, "provenance", _freeze_json("provenance", self.provenance))

    def to_dict(self) -> dict:
        return {
            "feature_id": self.feature_id,
            "system": self.system,
            "scope": self.scope,
            "reference_window": _thaw_json(self.reference_window),
            "primary_domain": self.primary_domain,
            "event_family_support": list(self.event_family_support),
            "strength_class": self.strength_class,
            "maturity": self.maturity,
            "qualification_status": self.qualification_status,
            "source_family": self.source_family,
            "dependency_family": self.dependency_family,
            "role": self.role,
            "provenance": _thaw_json(self.provenance),
        }


def evidence_feature_from_dict(payload: Mapping[str, Any]) -> EvidenceFeature:
    if not isinstance(payload, Mapping):
        _raise("payload", "evidence feature payload must be a mapping")

    keys = set(payload)
    required = set(_FIELDS)
    missing = sorted(required - keys)
    unknown = sorted(keys - required)
    if missing or unknown:
        details = {}
        if missing:
            details["missing_fields"] = missing
        if unknown:
            details["unknown_fields"] = unknown
        _raise("payload", "evidence feature fields do not match the contract", **details)

    return EvidenceFeature(
        feature_id=payload["feature_id"],
        system=payload["system"],
        scope=payload["scope"],
        reference_window=payload["reference_window"],
        primary_domain=payload["primary_domain"],
        event_family_support=payload["event_family_support"],
        strength_class=payload["strength_class"],
        maturity=payload["maturity"],
        qualification_status=payload["qualification_status"],
        source_family=payload["source_family"],
        dependency_family=payload["dependency_family"],
        role=payload["role"],
        provenance=payload["provenance"],
    )
