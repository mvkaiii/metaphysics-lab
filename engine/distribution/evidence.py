"""Deterministic evidence normalization for 林氏天機 v1.5 Phase 2.

This module only converts already-materialized forecast context into traceable
EvidenceFeature records.  It intentionally contains no eligibility, weighting,
ranking, probability, or specificity policy; those belong to later phases.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from .errors import DistributionError
from .evidence_models import EvidenceFeature, SCOPES


MAPPING_PROFILE = "lin_tianji_domain_v1-exp"

BAZI_TEN_GOD_MAPPING = {
    "比肩": {
        "primary_domain": "peers",
        "event_family_support": ("peer_alignment", "self_assertion"),
    },
    "劫財": {
        "primary_domain": "peers",
        "event_family_support": ("resource_competition", "peer_exchange"),
    },
    "食神": {
        "primary_domain": "expression",
        "event_family_support": ("creative_output", "sustained_delivery"),
    },
    "傷官": {
        "primary_domain": "expression",
        "event_family_support": ("communication_visibility", "rule_friction"),
    },
    "偏財": {
        "primary_domain": "finance",
        "event_family_support": ("variable_income", "commercial_opportunity"),
    },
    "正財": {
        "primary_domain": "finance",
        "event_family_support": ("earned_income", "resource_management"),
    },
    "七殺": {
        "primary_domain": "career",
        "event_family_support": ("authority_pressure", "role_change"),
    },
    "正官": {
        "primary_domain": "career",
        "event_family_support": ("formal_role", "responsibility"),
    },
    "偏印": {
        "primary_domain": "learning_support",
        "event_family_support": ("specialized_learning", "unconventional_support"),
    },
    "正印": {
        "primary_domain": "learning_support",
        "event_family_support": ("formal_learning", "institutional_support"),
    },
}

ZIWEI_PALACE_MAPPING = {
    "命宮": {
        "primary_domain": "self",
        "event_family_support": ("identity_direction",),
    },
    "兄弟宮": {
        "primary_domain": "peers",
        "event_family_support": ("peer_relations",),
    },
    "夫妻宮": {
        "primary_domain": "partnership",
        "event_family_support": ("close_partnership",),
    },
    "子女宮": {
        "primary_domain": "children_creation",
        "event_family_support": ("children_creation",),
    },
    "財帛宮": {
        "primary_domain": "finance",
        "event_family_support": ("income_assets",),
    },
    "疾厄宮": {
        "primary_domain": "health",
        "event_family_support": ("health_load",),
    },
    "遷移宮": {
        "primary_domain": "mobility_external",
        "event_family_support": ("movement_external",),
    },
    "交友宮": {
        "primary_domain": "social_network",
        "event_family_support": ("social_network",),
    },
    "官祿宮": {
        "primary_domain": "career",
        "event_family_support": ("career_role",),
    },
    "田宅宮": {
        "primary_domain": "home_property",
        "event_family_support": ("home_property",),
    },
    "福德宮": {
        "primary_domain": "wellbeing",
        "event_family_support": ("inner_wellbeing",),
    },
    "父母宮": {
        "primary_domain": "family_support",
        "event_family_support": ("family_support",),
    },
}

_SCOPE_ORDER = ("decadal", "yearly", "monthly", "daily", "hourly")
_BAZI_SCOPE_FIELDS = {
    "yearly": ("year", "year"),
    "monthly": ("month", "month"),
    "daily": ("day", "day"),
    "hourly": ("time", "time"),
}


def _raise(code: str, message: str, details: Mapping[str, Any] | None = None) -> None:
    raise DistributionError(code, message, {} if details is None else dict(details))


def _mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        _raise(
            "invalid_evidence_context",
            "%s must be a structured mapping" % field_name,
            {"field": field_name},
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
            "invalid_evidence_context",
            "forecast context must be JSON-serializable",
            {"error": str(exc)},
        )
    return encoded.encode("utf-8")


def _canonical_digest(value: object) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _requested_scopes(context: Mapping[str, Any]) -> tuple[str, ...]:
    constraints = _mapping(context.get("confidence_constraints"), "confidence_constraints")
    raw = constraints.get("ziwei_requested_scopes")
    if not isinstance(raw, (list, tuple)) or not raw:
        _raise(
            "evidence_scope_blocked",
            "forecast context does not declare requested scopes",
            {"reason": "missing_requested_scopes"},
        )
    scopes = tuple(raw)
    if any(not isinstance(scope, str) or scope not in _SCOPE_ORDER for scope in scopes):
        _raise(
            "evidence_scope_blocked",
            "forecast context declares an unsupported requested scope",
            {"requested_scopes": list(scopes), "allowed_scopes": list(_SCOPE_ORDER)},
        )
    if len(scopes) != len(set(scopes)):
        _raise(
            "evidence_scope_blocked",
            "forecast context requested scopes must be unique",
            {"requested_scopes": list(scopes)},
        )
    return scopes


def _role_for_scope(scope: str, target_scope: str) -> str:
    if scope == target_scope:
        return "target_evidence"
    scope_index = _SCOPE_ORDER.index(scope)
    target_index = _SCOPE_ORDER.index(target_scope)
    if scope_index < target_index:
        return "modifier"
    return "timing_trigger"


def _validate_target_scope(target_scope: object, requested_scopes: tuple[str, ...]) -> str:
    if not isinstance(target_scope, str) or target_scope not in SCOPES or target_scope not in _SCOPE_ORDER:
        _raise(
            "evidence_scope_blocked",
            "target scope is unsupported for deterministic forecast evidence",
            {"target_scope": target_scope, "allowed_scopes": list(_SCOPE_ORDER)},
        )
    if target_scope not in requested_scopes:
        _raise(
            "evidence_scope_blocked",
            "target scope is not present in the forecast context",
            {"target_scope": target_scope, "requested_scopes": list(requested_scopes)},
        )
    return target_scope


def _validate_mapping_profile(mapping_profile: object) -> str:
    if mapping_profile != MAPPING_PROFILE:
        _raise(
            "unsupported_evidence_mapping_profile",
            "unsupported evidence mapping profile",
            {"mapping_profile": mapping_profile, "supported": MAPPING_PROFILE},
        )
    return MAPPING_PROFILE


def _source_qualification_status(validation_status: object) -> str:
    if validation_status == "validated":
        return "qualified"
    if validation_status == "boundary_caution":
        return "needs_verification"
    return "unqualified"


def _bazi_qualification_status(bazi: Mapping[str, Any]) -> str:
    return "needs_verification" if bazi.get("boundary_warning") else "qualified"


def _feature_id(system: str, scope: str, source_identity: object, discriminator: object) -> str:
    digest = _canonical_digest(
        {
            "system": system,
            "scope": scope,
            "source_identity": source_identity,
            "discriminator": discriminator,
            "mapping_profile": MAPPING_PROFILE,
        }
    )
    return "%s:%s:%s" % (system, scope, digest[:24])


def _bazi_features(
    context: Mapping[str, Any],
    requested_scopes: tuple[str, ...],
    target_scope: str,
) -> list[dict]:
    bazi = _mapping(context.get("bazi"), "bazi")
    ten_gods = _mapping(bazi.get("ten_gods"), "bazi.ten_gods")
    features = []

    for scope in requested_scopes:
        fields = _BAZI_SCOPE_FIELDS.get(scope)
        if fields is None:
            continue
        pillar_field, ten_god_field = fields
        pillar = bazi.get(pillar_field)
        ten_god = ten_gods.get(ten_god_field)
        if not isinstance(pillar, str) or not pillar.strip():
            _raise(
                "evidence_scope_blocked",
                "requested Bazi scope is missing a deterministic pillar",
                {"scope": scope, "field": pillar_field},
            )
        if not isinstance(ten_god, str) or ten_god not in BAZI_TEN_GOD_MAPPING:
            _raise(
                "evidence_scope_blocked",
                "requested Bazi scope is missing a supported Ten God label",
                {"scope": scope, "ten_god": ten_god},
            )

        mapped = BAZI_TEN_GOD_MAPPING[ten_god]
        dependency_family = "bazi.project_calendar:%s:%s" % (scope, pillar)
        provenance = {
            "adapter": "engine.distribution.evidence:bazi_ten_god",
            "mapping_profile": MAPPING_PROFILE,
            "source_record": dict(bazi),
            "engine": bazi.get("engine"),
            "version": bazi.get("version"),
            "classification": bazi.get("classification"),
            "reference_engine": bazi.get("reference_engine"),
            "datetime": bazi.get("datetime"),
            "timezone": bazi.get("timezone"),
            "pillar": pillar,
            "ten_god": ten_god,
            "boundary_warning": bazi.get("boundary_warning"),
        }
        feature = EvidenceFeature(
            feature_id=_feature_id("bazi", scope, dependency_family, ten_god),
            system="bazi",
            scope=scope,
            reference_window={
                "scope": scope,
                "pillar": pillar,
                "target_datetime": bazi.get("datetime"),
            },
            primary_domain=mapped["primary_domain"],
            event_family_support=mapped["event_family_support"],
            strength_class="unspecified",
            maturity="experimental",
            qualification_status=_bazi_qualification_status(bazi),
            source_family="bazi.project_calendar",
            dependency_family=dependency_family,
            role=_role_for_scope(scope, target_scope),
            provenance=provenance,
        )
        features.append(feature.to_dict())
    return features


def _ziwei_features(
    context: Mapping[str, Any],
    requested_scopes: tuple[str, ...],
    target_scope: str,
) -> list[dict]:
    ziwei = _mapping(context.get("ziwei"), "ziwei")
    features = []

    for scope in requested_scopes:
        raw_layer = ziwei.get(scope)
        if not isinstance(raw_layer, Mapping):
            _raise(
                "evidence_scope_blocked",
                "requested Ziwei scope is missing from forecast context",
                {"scope": scope},
            )
        layer = raw_layer
        reference = layer.get("reference")
        maturity = layer.get("maturity")
        flowing = _mapping(layer.get("flowing_star_layer"), "ziwei.%s.flowing_star_layer" % scope)
        source = _mapping(flowing.get("source"), "ziwei.%s.flowing_star_layer.source" % scope)
        source_reference = source.get("reference", reference)
        validation_status = source.get("validation_status")
        records = layer.get("materialized_flowing_stars")
        if not isinstance(records, (list, tuple)):
            _raise(
                "invalid_evidence_context",
                "Ziwei scope must contain materialized flowing stars",
                {"scope": scope},
            )
        if maturity not in ("stable", "experimental"):
            _raise(
                "invalid_evidence_context",
                "Ziwei layer maturity is unsupported",
                {"scope": scope, "maturity": maturity},
            )
        if not isinstance(source_reference, str) or not source_reference.strip():
            _raise(
                "invalid_evidence_context",
                "Ziwei layer source reference must be non-empty",
                {"scope": scope},
            )

        dependency_family = "ziwei.flowing_star:%s:%s" % (scope, source_reference)
        for index, raw_record in enumerate(records):
            record = _mapping(raw_record, "ziwei.%s.materialized_flowing_stars[%d]" % (scope, index))
            palace = record.get("scope_palace") or record.get("natal_palace")
            if not isinstance(palace, str) or palace not in ZIWEI_PALACE_MAPPING:
                _raise(
                    "evidence_scope_blocked",
                    "Ziwei materialized record has no supported structural palace label",
                    {"scope": scope, "index": index, "palace": palace},
                )
            mapped = ZIWEI_PALACE_MAPPING[palace]
            discriminator = {
                "base_star": record.get("base_star"),
                "target_branch": record.get("target_branch"),
                "palace": palace,
                "sequence": index,
            }
            feature = EvidenceFeature(
                feature_id=_feature_id("ziwei", scope, dependency_family, discriminator),
                system="ziwei",
                scope=scope,
                reference_window={"scope": scope, "reference": source_reference},
                primary_domain=mapped["primary_domain"],
                event_family_support=mapped["event_family_support"],
                strength_class="unspecified",
                maturity=maturity,
                qualification_status=_source_qualification_status(validation_status),
                source_family="ziwei.flowing_star",
                dependency_family=dependency_family,
                role=_role_for_scope(scope, target_scope),
                provenance={
                    "adapter": "engine.distribution.evidence:ziwei_flowing_star_palace",
                    "mapping_profile": MAPPING_PROFILE,
                    "structural_palace": palace,
                    "source_record": dict(record),
                    "source_layer": dict(flowing),
                    "layer_classification": layer.get("classification"),
                    "layer_maturity": maturity,
                },
            )
            features.append(feature.to_dict())
    return features


def build_evidence_features(
    forecast_context: Mapping[str, object],
    target_scope: str,
    mapping_profile: str = MAPPING_PROFILE,
) -> dict:
    """Normalize deterministic forecast context into traceable evidence features."""

    context = _mapping(forecast_context, "forecast_context")
    source_context_digest = _canonical_digest(context)
    profile = _validate_mapping_profile(mapping_profile)
    requested_scopes = _requested_scopes(context)
    target = _validate_target_scope(target_scope, requested_scopes)

    features = []
    features.extend(_bazi_features(context, requested_scopes, target))
    features.extend(_ziwei_features(context, requested_scopes, target))

    return {
        "features": features,
        "target_scope": target,
        "mapping_profile": profile,
        "source_context_digest": source_context_digest,
    }
