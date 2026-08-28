"""Deterministic Ziwei cold-start structural interpretation for Phase 3.5."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Tuple

from .errors import DistributionError
from .evidence_models import EvidenceFeature
from .structural_policy import (
    FLOWING_STAR_CATEGORY_FAMILY,
    MAPPING_PROFILE,
    SCOPE_ORDER,
    TRANSFORMATION_FAMILY,
    ZIWEI_PALACE_MAPPING,
    ZIWEI_STRUCTURAL_PROFILE,
    role_for_scope,
)

_ALLOWED_TOP_LEVEL = frozenset((
    "bazi",
    "calendar_context_summary",
    "ziwei",
    "provenance",
    "confidence_constraints",
))
_FORBIDDEN_KEYS = frozenset(("historical_records", "actual_event", "known_event_years"))
_QUALIFICATION_ORDER = {
    "qualified": 0,
    "needs_verification": 1,
    "unqualified": 2,
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
        _raise("unsupported Ziwei structural target scope", {"target_scope": target_scope})
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


def _source_qualification(value: object) -> str:
    if value == "validated":
        return "qualified"
    if value == "boundary_caution":
        return "needs_verification"
    return "unqualified"


def _combine_qualification(left: str, right: str) -> str:
    return left if _QUALIFICATION_ORDER[left] >= _QUALIFICATION_ORDER[right] else right


def _layer_validation(layer: Mapping[str, Any], flowing: Mapping[str, Any]) -> str:
    source = flowing.get("source")
    if isinstance(source, Mapping) and source.get("validation_status") is not None:
        return _source_qualification(source.get("validation_status"))
    return _source_qualification(flowing.get("validation"))


def _placement_index(scope: str, flowing: Mapping[str, Any]) -> dict:
    placements = flowing.get("placements")
    if not isinstance(placements, (list, tuple)):
        _raise("Ziwei flowing-star placements must be a sequence", {"scope": scope})
    result = {}
    for index, raw in enumerate(placements):
        row = _mapping(raw, "ziwei.%s.flowing_star_layer.placements[%d]" % (scope, index))
        key = (row.get("base_star"), row.get("target_branch"), row.get("scope"))
        if any(not isinstance(item, str) or not item for item in key):
            _raise("Ziwei flowing-star placement identity is incomplete", {"scope": scope, "index": index})
        if key[2] != scope:
            _raise("Ziwei flowing-star placement scope conflicts with its envelope", {"scope": scope, "index": index})
        category = row.get("category")
        if not isinstance(category, str) or category not in FLOWING_STAR_CATEGORY_FAMILY:
            _raise("unsupported Ziwei flowing-star category", {"scope": scope, "category": category})
        prior = result.get(key)
        canonical = dict(row)
        if prior is not None and prior != canonical:
            _raise("conflicting duplicate Ziwei flowing-star placement", {"scope": scope, "key": list(key)})
        result[key] = canonical
    return result


def _domain_for_palace(palace: object, *, scope: str, source: str) -> Mapping[str, Any]:
    if not isinstance(palace, str) or palace not in ZIWEI_PALACE_MAPPING:
        _raise(
            "Ziwei structural signal has no supported palace ownership",
            {"scope": scope, "source": source, "palace": palace},
        )
    return ZIWEI_PALACE_MAPPING[palace]


def _bucket(buckets: dict, scope: str, reference: str, domain: str, maturity: str):
    key = (scope, reference, domain)
    item = buckets.get(key)
    if item is None:
        item = {
            "event_families": set(),
            "flowing_categories": set(),
            "flowing_signals": [],
            "transformation_signals": [],
            "geometric_relations": set(),
            "qualification_status": "qualified",
            "maturity": maturity,
        }
        buckets[key] = item
    elif item["maturity"] != maturity:
        _raise(
            "Ziwei structural aggregate has conflicting maturity",
            {"scope": scope, "reference": reference, "domain": domain},
        )
    return item


def _strength(bucket: Mapping[str, Any]) -> str:
    has_flowing = bool(bucket["flowing_categories"])
    has_transformation = bool(bucket["transformation_signals"])
    if has_flowing and has_transformation:
        return "strong"
    if has_transformation or len(bucket["flowing_categories"]) >= 2:
        return "moderate"
    if len(bucket["flowing_categories"]) == 1:
        return "weak"
    return "unspecified"


def interpret_ziwei_structural_features(
    forecast_context: Mapping[str, Any],
    target_scope: str,
    source_context_digest: str,
) -> Tuple[EvidenceFeature, ...]:
    """Translate deterministic Ziwei dynamic facts into canonical evidence."""

    context = _mapping(forecast_context, "forecast_context")
    unknown = sorted(set(context) - _ALLOWED_TOP_LEVEL)
    if unknown:
        _raise("forecast context contains unsupported top-level fields", {"unknown_fields": unknown})
    _reject_forbidden_keys(context)
    digest = _validate_digest(source_context_digest)
    requested_scopes = _requested_scopes(context, target_scope)
    ziwei = _mapping(context.get("ziwei"), "ziwei")

    buckets = {}
    for scope in SCOPE_ORDER:
        if scope not in requested_scopes:
            continue
        layer = _mapping(ziwei.get(scope), "ziwei.%s" % scope)
        reference = layer.get("reference")
        if not isinstance(reference, str) or not reference:
            _raise("Ziwei scope reference must be non-empty", {"scope": scope})
        maturity = layer.get("maturity")
        if maturity not in ("stable", "experimental"):
            _raise("unsupported Ziwei structural maturity", {"scope": scope, "maturity": maturity})
        flowing = _mapping(layer.get("flowing_star_layer"), "ziwei.%s.flowing_star_layer" % scope)
        placement_index = _placement_index(scope, flowing)
        qualification = _layer_validation(layer, flowing)
        records = layer.get("materialized_flowing_stars")
        if not isinstance(records, (list, tuple)):
            _raise("Ziwei scope must contain materialized flowing stars", {"scope": scope})

        for index, raw_record in enumerate(records):
            record = _mapping(raw_record, "ziwei.%s.materialized_flowing_stars[%d]" % (scope, index))
            record_scope = record.get("scope")
            if record_scope != scope:
                _raise("Ziwei materialized flowing-star scope conflicts with envelope", {"scope": scope, "index": index})
            base_star = record.get("base_star")
            target_branch = record.get("target_branch")
            key = (base_star, target_branch, scope)
            placement = placement_index.get(key)
            if placement is None:
                _raise(
                    "Ziwei materialized flowing star has no deterministic placement join",
                    {"scope": scope, "index": index, "key": list(key)},
                )
            category = placement["category"]
            family = FLOWING_STAR_CATEGORY_FAMILY[category]
            palace = record.get("scope_palace") or record.get("natal_palace")
            mapped = _domain_for_palace(palace, scope=scope, source="flowing_star")
            source_reference = record.get("source_reference", reference)
            if not isinstance(source_reference, str) or not source_reference:
                _raise("Ziwei flowing-star source reference must be non-empty", {"scope": scope, "index": index})
            domain = str(mapped["primary_domain"])
            bucket = _bucket(buckets, scope, source_reference, domain, maturity)
            bucket["event_families"].update(mapped["event_family_support"])
            bucket["event_families"].add(family)
            bucket["flowing_categories"].add(category)
            bucket["flowing_signals"].append({
                "base_star": base_star,
                "category": category,
                "semantic_family": family,
                "target_branch": target_branch,
                "palace": palace,
                "display_name": record.get("display_name"),
            })
            bucket["qualification_status"] = _combine_qualification(
                bucket["qualification_status"], qualification
            )

        transformation = layer.get("transformation_layer")
        if transformation is not None:
            transformation_layer = _mapping(
                transformation,
                "ziwei.%s.transformation_layer" % scope,
            )
            transformation_qualification = _source_qualification(
                transformation_layer.get("validation", "validated")
            )
            edges = transformation_layer.get("flying_edges")
            if not isinstance(edges, (list, tuple)):
                _raise("Ziwei transformation flying_edges must be a sequence", {"scope": scope})
            for index, raw_edge in enumerate(edges):
                edge = _mapping(
                    raw_edge,
                    "ziwei.%s.transformation_layer.flying_edges[%d]" % (scope, index),
                )
                transformation_type = edge.get("transformation_type")
                if not isinstance(transformation_type, str) or transformation_type not in TRANSFORMATION_FAMILY:
                    _raise(
                        "unsupported Ziwei transformation type",
                        {"scope": scope, "transformation_type": transformation_type},
                    )
                palace = edge.get("target_palace")
                mapped = _domain_for_palace(palace, scope=scope, source="transformation")
                domain = str(mapped["primary_domain"])
                bucket = _bucket(buckets, scope, reference, domain, maturity)
                family = TRANSFORMATION_FAMILY[transformation_type]
                bucket["event_families"].update(mapped["event_family_support"])
                bucket["event_families"].add(family)
                geometric_relation = edge.get("geometric_relation")
                if geometric_relation is not None:
                    if not isinstance(geometric_relation, str) or not geometric_relation:
                        _raise("Ziwei geometric relation must be non-empty text", {"scope": scope, "index": index})
                    bucket["geometric_relations"].add(geometric_relation)
                bucket["transformation_signals"].append({
                    "edge_id": edge.get("edge_id"),
                    "transformation_type": transformation_type,
                    "semantic_family": family,
                    "star": edge.get("star"),
                    "target_palace": palace,
                    "geometric_relation": geometric_relation,
                })
                bucket["qualification_status"] = _combine_qualification(
                    bucket["qualification_status"], transformation_qualification
                )

    features = []
    for (scope, reference, domain), bucket in buckets.items():
        flowing_payloads = tuple(sorted(
            bucket["flowing_signals"],
            key=lambda row: (
                str(row.get("base_star")),
                str(row.get("target_branch")),
                str(row.get("category")),
                str(row.get("palace")),
            ),
        ))
        transformation_payloads = tuple(sorted(
            bucket["transformation_signals"],
            key=lambda row: (
                str(row.get("edge_id")),
                str(row.get("transformation_type")),
                str(row.get("star")),
                str(row.get("target_palace")),
            ),
        ))
        geometric_relations = tuple(sorted(bucket["geometric_relations"]))
        event_families = tuple(sorted(bucket["event_families"]))
        dependency_family = "ziwei.structural:%s:%s:%s" % (scope, reference, domain)
        identity = {
            "structural_profile": ZIWEI_STRUCTURAL_PROFILE,
            "semantic_profile": MAPPING_PROFILE,
            "scope": scope,
            "reference": reference,
            "primary_domain": domain,
            "dependency_family": dependency_family,
            "flowing_signals": flowing_payloads,
            "transformation_signals": transformation_payloads,
        }
        feature_id = "ziwei:%s:%s" % (scope, _canonical_digest(identity)[:24])
        try:
            role = role_for_scope(scope, target_scope)
        except ValueError as exc:
            raise DistributionError(
                "structural_interpretation_blocked",
                "invalid deterministic Ziwei scope relationship",
                {"scope": scope, "target_scope": target_scope, "error": str(exc)},
            ) from exc
        features.append(EvidenceFeature(
            feature_id=feature_id,
            system="ziwei",
            scope=scope,
            reference_window={"scope": scope, "reference": reference},
            primary_domain=domain,
            event_family_support=event_families,
            strength_class=_strength(bucket),
            maturity=bucket["maturity"],
            qualification_status=bucket["qualification_status"],
            source_family="ziwei.structural_interpretation",
            dependency_family=dependency_family,
            role=role,
            provenance={
                "structural_profile": ZIWEI_STRUCTURAL_PROFILE,
                "semantic_profile": MAPPING_PROFILE,
                "flowing_signals": flowing_payloads,
                "transformation_signals": transformation_payloads,
                "geometric_relations": geometric_relations,
                "aggregation_basis": "one_feature_per_scope_reference_domain",
                "source_context_digest": digest,
            },
        ))

    return tuple(sorted(
        features,
        key=lambda item: (
            SCOPE_ORDER.index(item.scope),
            str(item.reference_window.get("reference")),
            item.primary_domain,
            item.dependency_family,
            item.feature_id,
        ),
    ))
