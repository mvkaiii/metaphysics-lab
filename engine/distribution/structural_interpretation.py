"""Canonical Phase 3.5 cold-start structural interpretation authority."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from .bazi_structural_interpretation import interpret_bazi_structural_features
from .errors import DistributionError
from .structural_policy import MAPPING_PROFILE, SCOPE_ORDER, STRUCTURAL_PROFILE_VERSION
from .ziwei_structural_interpretation import interpret_ziwei_structural_features

_ALLOWED_CONTEXT_FIELDS = frozenset({
    "bazi",
    "calendar_context_summary",
    "ziwei",
    "provenance",
    "confidence_constraints",
})
_SYSTEM_ORDER = ("bazi", "ziwei")


def _raise(code: str, message: str, details=None) -> None:
    raise DistributionError(code, message, {} if details is None else dict(details))


def _mapping(value: object, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        _raise(
            "invalid_structural_interpretation_context",
            "%s must be a structured mapping" % field,
            {"field": field},
        )
    return value


def _canonical_json(value: object) -> bytes:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        _raise(
            "invalid_structural_interpretation_context",
            "structural interpretation input must be canonical JSON",
            {"error": str(exc)},
        )
    return encoded.encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _validate_context(value: object) -> Mapping[str, Any]:
    context = _mapping(value, "forecast_context")
    unknown = sorted(set(context) - _ALLOWED_CONTEXT_FIELDS)
    if unknown:
        _raise(
            "invalid_structural_interpretation_context",
            "forecast context contains unsupported top-level fields",
            {"unknown_fields": unknown},
        )
    return context


def _validate_mapping_profile(value: object) -> str:
    if value != MAPPING_PROFILE:
        _raise(
            "unsupported_structural_mapping_profile",
            "unsupported structural interpretation mapping profile",
            {"mapping_profile": value, "supported": MAPPING_PROFILE},
        )
    return MAPPING_PROFILE


def _feature_sort_key(feature) -> tuple:
    try:
        scope_index = SCOPE_ORDER.index(feature.scope)
        system_index = _SYSTEM_ORDER.index(feature.system)
    except ValueError as exc:
        _raise(
            "invalid_structural_interpretation_feature",
            "structural interpreter returned an unsupported scope or system",
            {"scope": feature.scope, "system": feature.system},
        )
        raise AssertionError("unreachable") from exc
    return (
        scope_index,
        system_index,
        feature.primary_domain,
        feature.dependency_family,
        feature.feature_id,
    )


def interpret_structural_evidence(
    forecast_context: Mapping[str, object],
    target_scope: str,
    mapping_profile: str = MAPPING_PROFILE,
) -> dict:
    """Return deterministic, history-free structural evidence for Phase 3 ranking."""

    context = _validate_context(forecast_context)
    profile = _validate_mapping_profile(mapping_profile)
    source_context_digest = _digest(context)

    features = list(
        interpret_bazi_structural_features(
            context,
            target_scope,
            source_context_digest,
        )
    )
    features.extend(
        interpret_ziwei_structural_features(
            context,
            target_scope,
            source_context_digest,
        )
    )
    ordered = tuple(sorted(features, key=_feature_sort_key))

    payload = {
        "structural_profile_version": STRUCTURAL_PROFILE_VERSION,
        "mapping_profile_version": profile,
        "target_scope": target_scope,
        "source_context_digest": source_context_digest,
        "features": [feature.to_dict() for feature in ordered],
    }
    payload["interpretation_digest"] = _digest(payload)
    return payload
