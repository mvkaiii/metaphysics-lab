"""Deterministic Bazi cold-start structural interpretation for Phase 3.5."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Tuple

from engine.bazi.structural_relations import detect_structural_relations

from .errors import DistributionError
from .evidence_models import EvidenceFeature
from .structural_policy import (
    BAZI_STRUCTURAL_PROFILE,
    BAZI_TEN_GOD_MAPPING,
    MAPPING_PROFILE,
    RELATION_EVENT_FAMILY,
    SCOPE_ORDER,
    role_for_scope,
    strongest_relation_class,
)

_ALLOWED_TOP_LEVEL = frozenset((
    "bazi",
    "calendar_context_summary",
    "ziwei",
    "provenance",
    "confidence_constraints",
))
_FORBIDDEN_KEYS = frozenset(("historical_records", "actual_event", "known_event_years"))
_SCOPE_FIELDS = {
    "yearly": ("year", "year"),
    "monthly": ("month", "month"),
    "daily": ("day", "day"),
    "hourly": ("time", "time"),
}


def _raise(message: str, details=None) -> None:
    raise DistributionError(
        "structural_interpretation_blocked",
        message,
        {} if details is None else dict(details),
    )


def _mapping(value: object, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        _raise("%s must be a mapping" % field, {"field": field})
    return value


def _reject_forbidden_keys(value: object, path: str = "forecast_context") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in _FORBIDDEN_KEYS:
                _raise(
                    "historical or outcome fields are not accepted by structural interpretation",
                    {"field": str(key), "path": path},
                )
            _reject_forbidden_keys(item, "%s.%s" % (path, key))
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_forbidden_keys(item, "%s[%d]" % (path, index))


def _validate_digest(value: object) -> str:
    if not isinstance(value, str) or len(value) != 64:
        _raise("source_context_digest must be a sha256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise DistributionError(
            "structural_interpretation_blocked",
            "source_context_digest must be a sha256 hex digest",
        ) from exc
    return value.lower()


def _canonical_digest(value: object) -> str:
    try:
        payload = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise DistributionError(
            "structural_interpretation_blocked",
            "structural feature identity must be canonical JSON",
            {"error": str(exc)},
        ) from exc
    return hashlib.sha256(payload).hexdigest()


def _requested_scopes(context: Mapping[str, Any], target_scope: str) -> Tuple[str, ...]:
    if target_scope not in SCOPE_ORDER:
        _raise("unsupported Bazi structural target scope", {"target_scope": target_scope})
    constraints = _mapping(context.get("confidence_constraints"), "confidence_constraints")
    raw = constraints.get("ziwei_requested_scopes")
    if not isinstance(raw, (list, tuple)) or not raw:
        _raise("forecast context must carry requested scopes")
    scopes = []
    for scope in raw:
        if not isinstance(scope, str) or scope not in SCOPE_ORDER:
            _raise("forecast context contains unsupported requested scope", {"scope": scope})
        if scope in scopes:
            _raise("forecast context contains duplicate requested scope", {"scope": scope})
        scopes.append(scope)
    if target_scope not in scopes:
        _raise(
            "target scope is not materialized in forecast context",
            {"target_scope": target_scope, "requested_scopes": scopes},
        )
    return tuple(scopes)


def _relation_payloads(relations) -> Tuple[dict, ...]:
    payloads = []
    for relation in relations:
        family = relation.relation_family
        if family not in RELATION_EVENT_FAMILY:
            _raise("unsupported Bazi structural relation", {"relation_family": family})
        payloads.append({
            "tier": relation.tier,
            "relation_family": family,
            "target_layer": relation.target_layer,
            "target_component": relation.target_component,
            "participants": list(relation.participants),
        })
    return tuple(payloads)


def _scope_inputs(
    context: Mapping[str, Any],
    requested_scopes: Tuple[str, ...],
):
    bazi = _mapping(context.get("bazi"), "bazi")
    ten_gods = _mapping(bazi.get("ten_gods"), "bazi.ten_gods")
    structural = _mapping(bazi.get("structural_context"), "bazi.structural_context")
    current_decadal = structural.get("current_decadal")

    inputs = []
    if current_decadal is not None:
        decadal = _mapping(current_decadal, "bazi.structural_context.current_decadal")
        inputs.append(("decadal", decadal.get("pillar"), decadal.get("ten_god")))

    for scope in SCOPE_ORDER:
        if scope == "decadal" or scope not in requested_scopes:
            continue
        pillar_field, god_field = _SCOPE_FIELDS[scope]
        inputs.append((scope, bazi.get(pillar_field), ten_gods.get(god_field)))
    return bazi, structural, tuple(inputs)


def interpret_bazi_structural_features(
    forecast_context: Mapping[str, Any],
    target_scope: str,
    source_context_digest: str,
) -> Tuple[EvidenceFeature, ...]:
    """Translate deterministic Bazi facts into canonical Phase 3.5 evidence."""

    context = _mapping(forecast_context, "forecast_context")
    unknown = sorted(set(context) - _ALLOWED_TOP_LEVEL)
    if unknown:
        _raise("forecast context contains unsupported top-level fields", {"unknown_fields": unknown})
    _reject_forbidden_keys(context)
    digest = _validate_digest(source_context_digest)
    requested_scopes = _requested_scopes(context, target_scope)
    bazi, structural, inputs = _scope_inputs(context, requested_scopes)

    natal_pillars = _mapping(structural.get("natal_pillars"), "bazi.structural_context.natal_pillars")
    current_decadal = structural.get("current_decadal")
    decadal_pillar = None
    if current_decadal is not None:
        decadal_pillar = _mapping(
            current_decadal,
            "bazi.structural_context.current_decadal",
        ).get("pillar")
    boundaries = structural.get("decadal_boundaries_in_flow_year")
    if not isinstance(boundaries, (list, tuple)):
        _raise("bazi.structural_context.decadal_boundaries_in_flow_year must be a sequence")

    qualification_status = "needs_verification" if bazi.get("boundary_warning") else "qualified"
    features = []
    for scope, pillar, ten_god in inputs:
        if not isinstance(pillar, str) or not pillar:
            _raise("Bazi structural target pillar is missing", {"scope": scope})
        semantic = BAZI_TEN_GOD_MAPPING.get(ten_god)
        if semantic is None:
            _raise("unsupported materialized Bazi ten god", {"scope": scope, "ten_god": ten_god})

        try:
            relations = detect_structural_relations(
                scope=scope,
                target_pillar=pillar,
                natal_pillars=natal_pillars,
                decadal_pillar=decadal_pillar,
                decadal_boundary=scope == "yearly" and bool(boundaries),
            )
            strength_class = strongest_relation_class(
                relation.relation_family for relation in relations
            )
            role = role_for_scope(scope, target_scope)
        except ValueError as exc:
            raise DistributionError(
                "structural_interpretation_blocked",
                "invalid deterministic Bazi structural context",
                {"scope": scope, "error": str(exc)},
            ) from exc

        relation_payloads = _relation_payloads(relations)
        event_families = set(semantic["event_family_support"])
        event_families.update(
            RELATION_EVENT_FAMILY[relation.relation_family]
            for relation in relations
        )
        primary_domain = str(semantic["primary_domain"])
        dependency_family = "bazi.structural:%s:%s:%s" % (
            scope,
            pillar,
            primary_domain,
        )
        identity = {
            "structural_profile": BAZI_STRUCTURAL_PROFILE,
            "semantic_profile": MAPPING_PROFILE,
            "scope": scope,
            "pillar": pillar,
            "ten_god": ten_god,
            "primary_domain": primary_domain,
            "dependency_family": dependency_family,
            "canonical_relations": relation_payloads,
        }
        feature_id = "bazi:%s:%s" % (scope, _canonical_digest(identity)[:24])
        semantic_families = tuple(sorted(event_families))
        features.append(EvidenceFeature(
            feature_id=feature_id,
            system="bazi",
            scope=scope,
            reference_window={
                "scope": scope,
                "pillar": pillar,
                "target_datetime": bazi.get("datetime"),
            },
            primary_domain=primary_domain,
            event_family_support=semantic_families,
            strength_class=strength_class,
            maturity="experimental",
            qualification_status=qualification_status,
            source_family="bazi.structural_interpretation",
            dependency_family=dependency_family,
            role=role,
            provenance={
                "structural_profile": BAZI_STRUCTURAL_PROFILE,
                "semantic_profile": MAPPING_PROFILE,
                "canonical_relations": relation_payloads,
                "semantic_families": semantic_families,
                "aggregation_basis": "one_feature_per_scope_domain",
                "source_context_digest": digest,
            },
        ))

    return tuple(sorted(
        features,
        key=lambda item: (
            SCOPE_ORDER.index(item.scope),
            item.primary_domain,
            item.dependency_family,
            item.feature_id,
        ),
    ))
