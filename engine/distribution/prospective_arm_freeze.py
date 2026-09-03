"""Outcome-blind paired Legacy/Candidate arm freeze for prospective research.

This module is orchestration and sealing only. It does not modify frozen EFA,
C1/C2, HCC/HOC, Legacy Adapter, ranking, mapping, scoring, or oracle semantics.
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import datetime
from zoneinfo import ZoneInfo

from .claim_authority_manifest import validate_claim_authority_manifest
from .claim_consumption_contract import build_claim_consumption_bundle
from .claim_evidence import build_claim_evidence_packets
from .coordination_policy_v2 import build_coordination_bundle
from .errors import DistributionError
from .event_family_attribution import build_event_family_attribution_bundle
from .event_family_legacy_adapter import build_event_family_legacy_adapter_bundle
from .hierarchical_claim_authority import build_hierarchical_claim_authority_bundle
from .hybrid_claim_composer import build_hybrid_claim_composer_bundle
from .hybrid_output_contract import build_hybrid_output_contract
from .interpretation_contract import build_interpretation_contract
from .interpretation_contract_v2 import build_interpretation_contract_v2
from .prospective_claim_universe import (
    validate_downstream_arm_universe,
    validate_s1_case_claims_against_efa,
)
from .prospective_window_scope import resolve_prospective_window_scope


PROSPECTIVE_ARM_FREEZE_SCHEMA = "v1.6-prospective-arm-freeze.v1"
PROSPECTIVE_ARM_FREEZE_PROFILE = "lin_tianji_prospective_arm_freeze_v1"

_INPUT_FIELDS = frozenset((
    "opaque_case_id",
    "sealed_at",
    "scope_policy",
    "claim_authority_manifest",
    "forecast_context_digest",
    "base_ranking",
    "structural_interpretation",
    "anchor",
    "locked_claim_ids",
    "s1_provenance",
))
_S1_FIELDS = frozenset((
    "composite_claim_authority_digest",
    "claim_universe_digest",
    "sampling_frame_digest",
    "sampling_receipt_digest",
))
_FORBIDDEN_KEYS = frozenset((
    "outcome",
    "oracle",
    "historical_records",
    "verified_events",
    "legacy_score",
    "candidate_score",
    "q1_result",
    "t1_result",
    "scoring",
    "adjudication",
))


def _raise(message: str, details=None) -> None:
    raise DistributionError(
        "invalid_prospective_arm_freeze",
        message,
        {} if details is None else dict(details),
    )


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        _raise("%s must be a mapping" % field, {"field": field})
    return value


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _raise("%s must be non-empty text" % field, {"field": field})
    return value.strip()


def _sha256(value: object, field: str) -> str:
    text = _text(value, field)
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        _raise("%s must be lowercase SHA-256 hex" % field, {"field": field})
    return text


def _canonical_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        _raise("arm-freeze payload must contain canonical JSON values")
        raise AssertionError("unreachable") from exc


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _exact_fields(value: Mapping[str, object], allowed: frozenset, field: str) -> None:
    missing = sorted(allowed - set(value))
    unknown = sorted(set(value) - allowed)
    if missing or unknown:
        _raise(
            "%s fields do not match the fixed contract" % field,
            {"field": field, "missing_fields": missing, "unknown_fields": unknown},
        )


def _scan_forbidden_keys(value: object, path: str = "payload") -> None:
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            key = str(raw_key)
            if key.lower() in _FORBIDDEN_KEYS:
                _raise(
                    "outcome/oracle/scoring material is forbidden during arm freeze",
                    {"field": "%s.%s" % (path, key)},
                )
            _scan_forbidden_keys(child, "%s.%s" % (path, key))
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _scan_forbidden_keys(child, "%s[%d]" % (path, index))


def _aware_iso_in_zone(value: object, field: str, timezone_name: str) -> datetime:
    text = _text(value, field)
    try:
        zone = ZoneInfo(timezone_name)
    except Exception as exc:
        _raise("scope timezone must be a valid IANA timezone", {"field": "scope_policy.timezone"})
        raise AssertionError("unreachable") from exc
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        _raise("%s must be an ISO-8601 datetime" % field, {"field": field})
        raise AssertionError("unreachable") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        _raise("%s must include an explicit UTC offset" % field, {"field": field})

    localized = parsed.astimezone(zone)
    if (
        localized.replace(tzinfo=None) != parsed.replace(tzinfo=None)
        or localized.utcoffset() != parsed.utcoffset()
    ):
        _raise(
            "%s offset does not match the frozen prospective timezone" % field,
            {"field": field, "timezone": timezone_name},
        )
    return localized


def _validated_pre_outcome_binding(
    *,
    sealed_at: object,
    scope_policy: Mapping[str, object],
    anchor: object,
) -> dict:
    """Fail closed before any forecast/interpretation builder can observe the input."""

    source = _mapping(anchor, "anchor")
    timezone_name = _text(scope_policy.get("timezone"), "scope_policy.timezone")
    query_timezone = _text(source.get("query_timezone"), "anchor.query_timezone")
    if query_timezone != timezone_name:
        _raise(
            "anchor query_timezone must exactly match frozen scope timezone",
            {"field": "anchor.query_timezone"},
        )

    expected_start = _text(scope_policy.get("window_start"), "scope_policy.window_start")
    expected_end = _text(scope_policy.get("window_end"), "scope_policy.window_end")
    anchor_start = _text(
        source.get("prospective_window_start"),
        "anchor.prospective_window_start",
    )
    anchor_end = _text(
        source.get("prospective_window_end"),
        "anchor.prospective_window_end",
    )
    if anchor_start != expected_start:
        _raise(
            "anchor prospective_window_start must exactly match frozen scope policy",
            {"field": "anchor.prospective_window_start"},
        )
    if anchor_end != expected_end:
        _raise(
            "anchor prospective_window_end must exactly match frozen scope policy",
            {"field": "anchor.prospective_window_end"},
        )

    seal = _aware_iso_in_zone(sealed_at, "sealed_at", timezone_name)
    outcome_start = _aware_iso_in_zone(expected_start, "scope_policy.window_start", timezone_name)
    if seal >= outcome_start:
        _raise(
            "sealed_at must be strictly earlier than the prospective outcome window",
            {"field": "sealed_at"},
        )

    query_anchor = _aware_iso_in_zone(
        source.get("query_anchor_at"),
        "anchor.query_anchor_at",
        timezone_name,
    )
    knowledge_cutoff = _aware_iso_in_zone(
        source.get("knowledge_cutoff_at"),
        "anchor.knowledge_cutoff_at",
        timezone_name,
    )
    if query_anchor > seal:
        _raise(
            "anchor.query_anchor_at must not extend past sealed_at",
            {"field": "anchor.query_anchor_at"},
        )
    if knowledge_cutoff > seal:
        _raise(
            "anchor.knowledge_cutoff_at must not extend past sealed_at",
            {"field": "anchor.knowledge_cutoff_at"},
        )

    return {
        "sealed_at": seal.isoformat(),
        "query_anchor_at": query_anchor.isoformat(),
        "knowledge_cutoff_at": knowledge_cutoff.isoformat(),
        "query_timezone": query_timezone,
        "prospective_window_start": expected_start,
        "prospective_window_end": expected_end,
    }


def _validated_scope_policy(value: object) -> dict:
    supplied = _mapping(value, "scope_policy")
    expected = resolve_prospective_window_scope(
        {
            "window_start": supplied.get("window_start"),
            "window_end": supplied.get("window_end"),
            "timezone": supplied.get("timezone"),
        }
    )
    if dict(supplied) != expected:
        _raise("scope_policy does not match canonical prospective-window resolver output")
    if expected["claim_target_scope"] != "yearly":
        _raise("arm freeze requires yearly claim authority")
    if expected["timing_scopes"] != ["monthly"]:
        _raise("arm freeze requires the frozen monthly timing scope")
    if expected["child_opening_scope"] != "yearly":
        _raise("arm freeze requires yearly child-opening authority")
    return expected


def _validated_s1_provenance(value: object) -> dict:
    source = _mapping(value, "s1_provenance")
    _exact_fields(source, _S1_FIELDS, "s1_provenance")
    return {
        field: _sha256(source.get(field), "s1_provenance.%s" % field)
        for field in sorted(_S1_FIELDS)
    }


def _validated_locked_ids(value: object) -> list[str]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        _raise("locked_claim_ids must be a non-empty sequence")
    ids = [_text(item, "locked_claim_ids") for item in value]
    if not ids:
        _raise("locked_claim_ids must not be empty")
    if len(ids) != len(set(ids)):
        _raise("locked_claim_ids must be unique")
    return ids


def _build_candidate_chain(
    *,
    base_ranking: Mapping[str, object],
    structural_interpretation: Mapping[str, object],
    anchor: Mapping[str, object],
) -> tuple[dict, dict, dict]:
    """Rebuild the frozen Candidate chain without changing any child semantics."""

    v1 = build_interpretation_contract(base_ranking, anchor)
    claim_bundle = build_claim_evidence_packets(
        base_ranking=base_ranking,
        structural_interpretation=structural_interpretation,
        domain_interpretation=v1["domain_interpretation"],
    )
    phase3_caps = {
        str(row["primary_domain"]): str(row["allowed_specificity"])
        for row in base_ranking.get("domains", [])
        if isinstance(row, Mapping)
    }
    coordination_bundle = build_coordination_bundle(
        claim_evidence_packets=claim_bundle["packets"],
        target_scope=str(base_ranking["target_scope"]),
        source_ranking_digest=str(base_ranking["ranking_digest"]),
        source_interpretation_digest=str(structural_interpretation["interpretation_digest"]),
        phase3_specificity_by_domain=phase3_caps,
    )
    c1_bundle = build_claim_consumption_bundle(
        claim_evidence_bundle=claim_bundle,
        coordination_bundle=coordination_bundle,
    )
    efa_bundle = build_event_family_attribution_bundle(
        base_ranking=base_ranking,
        structural_interpretation=structural_interpretation,
    )
    c2_bundle = build_hierarchical_claim_authority_bundle(
        claim_consumption_bundle=c1_bundle,
        event_family_attribution_bundle=efa_bundle,
        claim_evidence_bundle=claim_bundle,
    )
    hcc_bundle = build_hybrid_claim_composer_bundle(
        hierarchical_authority_bundle=c2_bundle,
        event_family_attribution_bundle=efa_bundle,
        interpretation_contract=v1,
        claim_evidence_bundle=claim_bundle,
    )
    hoc_bundle = build_hybrid_output_contract(
        hybrid_claim_composer_bundle=hcc_bundle,
    )
    provenance = {
        "claim_evidence_digest": claim_bundle["claim_evidence_digest"],
        "coordination_digest": coordination_bundle["coordination_digest"],
        "claim_consumption_digest": c1_bundle["claim_consumption_digest"],
        "event_family_attribution_digest": efa_bundle["event_family_attribution_digest"],
        "hierarchical_claim_authority_digest": c2_bundle["hierarchical_claim_authority_digest"],
        "hybrid_claim_composer_digest": hcc_bundle["hybrid_claim_composer_digest"],
        "hybrid_output_contract_digest": hoc_bundle["hybrid_output_contract_digest"],
    }
    return efa_bundle, hoc_bundle, provenance


def _assert_wrapper_matches_candidate(v2: Mapping[str, object], provenance: Mapping[str, object]) -> None:
    for field, expected in provenance.items():
        if v2.get(field) != expected:
            _raise(
                "Interpretation v2 wrapper digest diverges from rebuilt frozen Candidate chain",
                {"field": field},
            )


def build_prospective_arm_freeze(payload: Mapping[str, object]) -> dict:
    """Build and seal paired outcome-blind Legacy and Candidate outputs.

    The caller supplies a previously frozen S1 universe and the already-selected
    yearly structural/ranking source. Both arms are then derived from exactly
    that source and validated against the same locked child IDs.
    """

    source = _mapping(payload, "prospective arm-freeze input")
    _scan_forbidden_keys(source)
    _exact_fields(source, _INPUT_FIELDS, "prospective arm-freeze input")

    case_id = _text(source.get("opaque_case_id"), "opaque_case_id")
    scope_policy = _validated_scope_policy(source.get("scope_policy"))
    anchor = _mapping(source.get("anchor"), "anchor")
    pre_outcome_binding = _validated_pre_outcome_binding(
        sealed_at=source.get("sealed_at"),
        scope_policy=scope_policy,
        anchor=anchor,
    )
    sealed_at = pre_outcome_binding["sealed_at"]

    authority = validate_claim_authority_manifest(
        _mapping(source.get("claim_authority_manifest"), "claim_authority_manifest")
    )
    if authority["scope_policy"]["policy_digest"] != scope_policy["policy_digest"]:
        _raise("claim-authority manifest does not bind the supplied scope policy")
    if authority["resolved_target_scope"] != scope_policy["claim_target_scope"]:
        _raise("claim-authority manifest target scope does not match scope policy")

    forecast_context_digest = _sha256(
        source.get("forecast_context_digest"),
        "forecast_context_digest",
    )
    ranking = _mapping(source.get("base_ranking"), "base_ranking")
    interpretation = _mapping(
        source.get("structural_interpretation"),
        "structural_interpretation",
    )

    if ranking.get("target_scope") != scope_policy["claim_target_scope"]:
        _raise("base_ranking target_scope does not match frozen scope policy")
    if interpretation.get("target_scope") != scope_policy["claim_target_scope"]:
        _raise("structural_interpretation target_scope does not match frozen scope policy")
    structural_source_digest = _sha256(
        interpretation.get("source_context_digest"),
        "structural_interpretation.source_context_digest",
    )
    if structural_source_digest != forecast_context_digest:
        _raise("structural interpretation must derive from the supplied forecast context")

    ranking_digest = _sha256(ranking.get("ranking_digest"), "base_ranking.ranking_digest")
    interpretation_digest = _sha256(
        interpretation.get("interpretation_digest"),
        "structural_interpretation.interpretation_digest",
    )
    locked_ids = _validated_locked_ids(source.get("locked_claim_ids"))
    s1_provenance = _validated_s1_provenance(source.get("s1_provenance"))

    v2 = build_interpretation_contract_v2(
        ranking,
        anchor,
        structural_interpretation=interpretation,
    )
    legacy_bundle = build_event_family_legacy_adapter_bundle(
        interpretation_contract_v2=v2,
    )
    efa_bundle, hoc_bundle, candidate_provenance = _build_candidate_chain(
        base_ranking=ranking,
        structural_interpretation=interpretation,
        anchor=anchor,
    )
    _assert_wrapper_matches_candidate(v2, candidate_provenance)

    s1_validation = validate_s1_case_claims_against_efa(
        locked_claim_ids=locked_ids,
        efa_bundle=efa_bundle,
    )
    legacy_validation = validate_downstream_arm_universe(
        locked_claim_ids=locked_ids,
        arm_type="legacy",
        arm_bundle=legacy_bundle,
    )
    candidate_validation = validate_downstream_arm_universe(
        locked_claim_ids=locked_ids,
        arm_type="candidate_hoc",
        arm_bundle=hoc_bundle,
    )

    body = {
        "schema_version": PROSPECTIVE_ARM_FREEZE_SCHEMA,
        "profile_version": PROSPECTIVE_ARM_FREEZE_PROFILE,
        "opaque_case_id": case_id,
        "sealed_at": sealed_at,
        "pre_outcome_binding": pre_outcome_binding,
        "status": "WAITING_FOR_OUTCOME",
        "outcome_blind": True,
        "oracle_status": "NOT_CREATED",
        "scoring_status": "NOT_PERFORMED",
        "retuning_status": "PROHIBITED",
        "promotion_allowed": False,
        "target_scope": scope_policy["claim_target_scope"],
        "timing_scopes": copy.deepcopy(scope_policy["timing_scopes"]),
        "scope_policy_digest": scope_policy["policy_digest"],
        "claim_authority_profile": authority["claim_authority_profile"],
        "claim_authority_digest": authority["claim_authority_digest"],
        "source_forecast_context_digest": forecast_context_digest,
        "source_ranking_digest": ranking_digest,
        "source_structural_interpretation_digest": interpretation_digest,
        "structural_interpretation_source_context_digest": structural_source_digest,
        "source_interpretation_contract_v2_digest": _sha256(
            v2.get("interpretation_contract_digest"),
            "interpretation_contract_digest",
        ),
        "s1_provenance": s1_provenance,
        "s1_universe_validation": s1_validation,
        "legacy_provenance": {
            "source_interpretation_contract_v2_digest": v2["interpretation_contract_digest"],
            "legacy_adapter_digest": legacy_bundle["legacy_adapter_digest"],
        },
        "candidate_provenance": candidate_provenance,
        "legacy_arm": copy.deepcopy(legacy_bundle),
        "candidate_arm": copy.deepcopy(hoc_bundle),
        "legacy_universe_validation": legacy_validation,
        "candidate_universe_validation": candidate_validation,
    }
    return {**body, "arm_freeze_digest": _digest(body)}
