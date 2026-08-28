"""Deterministic Phase 4 historical-personalization boundary.

Phase 4 consumes an immutable Phase 3 ranking snapshot plus finalized,
machine-readable Historical Calibration records. It never rewrites the base
ranking and never interprets free-text event descriptions.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from typing import Mapping, Sequence

from .errors import DistributionError
from .evidence_policy import SPECIFICITY_LEVELS
from .historical_personalization_policy import (
    BASE_RANKING_POLICY_VERSION,
    MIN_ELIGIBLE_SAMPLES,
    PERSONALIZATION_PROFILE_VERSION,
    bounded_modifier,
    evidence_unit,
    normalize_domain_id,
    normalize_event_family_id,
    support_class,
)


_TARGET_SCOPES = frozenset(("decadal", "yearly", "monthly", "daily", "hourly"))
_CALIBRATION_STATUSES = frozenset(("uncalibrated", "basic", "calibrated"))
_VERIFICATION_STATES = frozenset(("matched", "partial", "not_matched", "cannot_recall"))
_DIMENSION_STATUSES = frozenset(("matched", "partial", "missed", "unscorable"))
_TIMING_STATUSES = frozenset(
    ("exact_flow_year", "shifted", "missed", "unscorable", "unscorable_or_ambiguous")
)
_BLINDNESS_STATES = frozenset(("blind", "contaminated"))
_ROLES = frozenset(("high_activation", "control"))


def _raise(message: str, details=None) -> None:
    raise DistributionError("invalid_historical_personalization", message, details)


def _canonical_digest(value: object) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        _raise("%s must be a mapping" % label, {"type": type(value).__name__})
    return value


def _ordered_texts(value: object, label: str) -> list:
    if not isinstance(value, (list, tuple)):
        _raise("%s must be an ordered sequence" % label)
    result = []
    for item in value:
        if not isinstance(item, str) or not item:
            _raise("%s entries must be non-empty text" % label)
        result.append(item)
    return result


def _validate_base_ranking(base_ranking: object) -> dict:
    base = _mapping(base_ranking, "base_ranking")
    if base.get("policy_version") != BASE_RANKING_POLICY_VERSION:
        _raise(
            "unsupported base ranking policy",
            {"policy_version": base.get("policy_version")},
        )
    target_scope = base.get("target_scope")
    if target_scope not in _TARGET_SCOPES:
        _raise("unsupported base ranking target_scope", {"target_scope": target_scope})

    digest = base.get("ranking_digest")
    if not isinstance(digest, str) or not digest:
        _raise("base ranking must include ranking_digest")
    digest_payload = dict(base)
    digest_payload.pop("ranking_digest", None)
    actual_digest = _canonical_digest(digest_payload)
    if actual_digest != digest:
        _raise(
            "base ranking digest does not match payload",
            {"expected_digest": digest, "actual_digest": actual_digest},
        )

    domains = base.get("domains")
    if not isinstance(domains, list):
        _raise("base ranking domains must be a list")
    seen_domains = set()
    validated_domains = []
    for row in domains:
        item = _mapping(row, "base ranking domain")
        domain = item.get("primary_domain")
        if not isinstance(domain, str) or not domain:
            _raise("base ranking domain must have primary_domain")
        if domain in seen_domains:
            _raise("base ranking domains must be unique", {"primary_domain": domain})
        seen_domains.add(domain)
        rank = item.get("rank")
        score = item.get("ordinal_score_scaled")
        if isinstance(rank, bool) or not isinstance(rank, int) or rank < 1:
            _raise("base ranking domain rank must be a positive integer", {"primary_domain": domain})
        if isinstance(score, bool) or not isinstance(score, int):
            _raise("base ranking ordinal_score_scaled must be an integer", {"primary_domain": domain})
        specificity = item.get("allowed_specificity")
        if specificity not in SPECIFICITY_LEVELS:
            _raise("base ranking contains invalid specificity", {"primary_domain": domain})
        event_families = _ordered_texts(item.get("event_families"), "base event_families")
        validated_domains.append(
            {
                "primary_domain": domain,
                "rank": rank,
                "ordinal_score_scaled": score,
                "allowed_specificity": specificity,
                "event_families": event_families,
            }
        )

    expected_ranks = list(range(1, len(validated_domains) + 1))
    if [row["rank"] for row in validated_domains] != expected_ranks:
        _raise("base ranking domain ranks must be contiguous and in rank order")

    return {
        "policy_version": BASE_RANKING_POLICY_VERSION,
        "target_scope": target_scope,
        "ranking_digest": digest,
        "domains": validated_domains,
    }


def _normalize_historical_records(records: object, base_domain_map: Mapping[str, object]):
    if not isinstance(records, (list, tuple)):
        _raise("historical_records must be an ordered sequence")

    normalized = []
    excluded = Counter()
    seen_record_ids = set()
    authoritative_years = set()
    eligible_count = 0
    control_count = 0
    timing_counts = Counter()

    for source_order, raw in enumerate(records, start=1):
        record = _mapping(raw, "historical record")
        record_id = record.get("record_id")
        if not isinstance(record_id, str) or not record_id:
            _raise("historical record must have a non-empty record_id")
        if record_id in seen_record_ids:
            _raise("duplicate historical record_id", {"record_id": record_id})
        seen_record_ids.add(record_id)

        record_type = record.get("record_type")
        if record_type != "historical_calibration":
            excluded["unsupported_record_type"] += 1
            normalized.append(
                {
                    "record_id": record_id,
                    "record_type": record_type,
                    "source_order": source_order,
                    "eligibility": {
                        "general_score_eligible": False,
                        "score_authority": False,
                        "domain_score_eligible": False,
                        "event_family_score_eligible": False,
                        "reasons": ["unsupported_record_type"],
                    },
                }
            )
            continue

        calibration_id = record.get("calibration_id")
        if not isinstance(calibration_id, str) or not calibration_id:
            _raise("historical calibration record must have calibration_id", {"record_id": record_id})
        origin = record.get("origin")
        if origin not in ("canonical", "supplemental"):
            _raise("historical calibration origin is invalid", {"record_id": record_id})

        blind = _mapping(record.get("blind_prediction"), "blind_prediction")
        evaluation = _mapping(record.get("evaluation"), "evaluation")
        role = blind.get("role")
        if role not in _ROLES:
            _raise("historical calibration role is invalid", {"record_id": record_id, "role": role})
        predicted_flow_year = blind.get("predicted_flow_year")
        if isinstance(predicted_flow_year, bool) or not isinstance(predicted_flow_year, int):
            _raise("predicted_flow_year must be an integer", {"record_id": record_id})
        blindness_status = blind.get("blindness_status")
        if blindness_status not in _BLINDNESS_STATES:
            _raise("blindness_status is invalid", {"record_id": record_id})

        raw_domains = _ordered_texts(blind.get("primary_domains"), "primary_domains")
        raw_families = _ordered_texts(blind.get("event_family"), "event_family")
        canonical_domains = [normalize_domain_id(value) for value in raw_domains]
        canonical_domains = [value for value in canonical_domains if value is not None]
        canonical_families = [normalize_event_family_id(value) for value in raw_families]
        canonical_families = [value for value in canonical_families if value is not None]
        if len(canonical_domains) != len(raw_domains):
            excluded["unmapped_domain"] += 1
        if len(canonical_families) != len(raw_families):
            excluded["unmapped_event_family"] += 1

        verification_state = evaluation.get("verification_state")
        domain_status = evaluation.get("domain_status")
        event_form_status = evaluation.get("event_form_status")
        timing_status = evaluation.get("timing_status")
        if verification_state not in _VERIFICATION_STATES:
            _raise("verification_state is invalid", {"record_id": record_id})
        if domain_status not in _DIMENSION_STATUSES:
            _raise("domain_status is invalid", {"record_id": record_id})
        if event_form_status not in _DIMENSION_STATUSES:
            _raise("event_form_status is invalid", {"record_id": record_id})
        if timing_status not in _TIMING_STATUSES:
            _raise("timing_status is invalid", {"record_id": record_id})
        offset = evaluation.get("offset_flow_years")
        if offset is not None and (isinstance(offset, bool) or not isinstance(offset, int)):
            _raise("offset_flow_years must be an integer or null", {"record_id": record_id})
        boundary_ambiguity = evaluation.get("boundary_ambiguity")
        if not isinstance(boundary_ambiguity, bool):
            _raise("boundary_ambiguity must be boolean", {"record_id": record_id})

        reasons = []
        if blindness_status != "blind":
            reasons.append("contaminated")
            excluded["contaminated"] += 1
        if verification_state == "cannot_recall":
            reasons.append("cannot_recall")
            excluded["cannot_recall"] += 1
        if role == "control":
            reasons.append("control_audit_only")
            excluded["control_audit_only"] += 1
            control_count += 1

        general_score_eligible = not reasons
        score_authority = False
        if general_score_eligible:
            if predicted_flow_year in authoritative_years:
                reasons.append("duplicate_reference_year")
                excluded["duplicate_reference_year"] += 1
            else:
                authoritative_years.add(predicted_flow_year)
                score_authority = True
                eligible_count += 1

        single_base_domain = (
            score_authority
            and len(canonical_domains) == 1
            and canonical_domains[0] in base_domain_map
        )

        domain_score_eligible = score_authority
        if domain_score_eligible:
            if len(canonical_domains) == 0:
                domain_score_eligible = False
                if "unmapped_domain" not in reasons:
                    reasons.append("unmapped_domain")
            elif len(canonical_domains) != 1:
                domain_score_eligible = False
                reasons.append("ambiguous_multi_domain")
                excluded["ambiguous_multi_domain"] += 1
            elif canonical_domains[0] not in base_domain_map:
                domain_score_eligible = False
                reasons.append("domain_not_in_base")
                excluded["domain_not_in_base"] += 1
            elif domain_status == "unscorable":
                domain_score_eligible = False
                reasons.append("unscorable_domain")
                excluded["unscorable_domain"] += 1

        event_family_score_eligible = single_base_domain
        if event_family_score_eligible:
            if len(canonical_families) == 0:
                event_family_score_eligible = False
                if "unmapped_event_family" not in reasons:
                    reasons.append("unmapped_event_family")
            elif len(canonical_families) != 1:
                event_family_score_eligible = False
                reasons.append("ambiguous_multi_family")
                excluded["ambiguous_multi_family"] += 1
            else:
                domain_id = canonical_domains[0]
                base_families = base_domain_map[domain_id]["event_families"]
                if canonical_families[0] not in base_families:
                    event_family_score_eligible = False
                    reasons.append("event_family_not_in_base")
                    excluded["event_family_not_in_base"] += 1
                elif event_form_status == "unscorable":
                    event_family_score_eligible = False
                    reasons.append("unscorable_event_family")
                    excluded["unscorable_event_family"] += 1

        timing_counts[timing_status] += 1

        normalized.append(
            {
                "record_id": record_id,
                "record_type": "historical_calibration",
                "calibration_id": calibration_id,
                "source_order": source_order,
                "origin": origin,
                "role": role,
                "predicted_flow_year": predicted_flow_year,
                "blindness_status": blindness_status,
                "raw_domains": raw_domains,
                "raw_event_families": raw_families,
                "canonical_domains": canonical_domains,
                "canonical_event_families": canonical_families,
                "verification_state": verification_state,
                "domain_status": domain_status,
                "event_form_status": event_form_status,
                "timing_status": timing_status,
                "offset_flow_years": offset,
                "boundary_ambiguity": boundary_ambiguity,
                "eligibility": {
                    "general_score_eligible": general_score_eligible,
                    "score_authority": score_authority,
                    "domain_score_eligible": domain_score_eligible,
                    "event_family_score_eligible": event_family_score_eligible,
                    "reasons": reasons,
                    "mapped_to_current_base_domain": any(
                        domain in base_domain_map for domain in canonical_domains
                    ),
                },
            }
        )

    return normalized, {
        "eligible_record_count": eligible_count,
        "excluded_record_counts": dict(sorted(excluded.items())),
        "control_audit": {"record_count": control_count},
        "timing_audit": {"status_counts": dict(sorted(timing_counts.items()))},
    }


def _aggregate_domain_support(normalized_records):
    aggregate = defaultdict(lambda: {"support_units": 0, "record_ids": []})
    for record in normalized_records:
        eligibility = record.get("eligibility", {})
        if not eligibility.get("domain_score_eligible"):
            continue
        domain = record["canonical_domains"][0]
        unit = evidence_unit(record["domain_status"])
        if unit is None:
            continue
        aggregate[domain]["support_units"] += unit
        aggregate[domain]["record_ids"].append(record["record_id"])
    return aggregate


def _aggregate_event_family_support(normalized_records):
    aggregate = defaultdict(lambda: {"support_units": 0, "record_ids": []})
    for record in normalized_records:
        eligibility = record.get("eligibility", {})
        if not eligibility.get("event_family_score_eligible"):
            continue
        domain = record["canonical_domains"][0]
        family = record["canonical_event_families"][0]
        unit = evidence_unit(record["event_form_status"])
        if unit is None:
            continue
        aggregate[(domain, family)]["support_units"] += unit
        aggregate[(domain, family)]["record_ids"].append(record["record_id"])
    return aggregate


def _personalize_event_families(domain_id, base_families, family_support, enabled):
    if not enabled:
        return list(base_families), [], [], False

    family_rows = []
    any_qualified = False
    for base_index, family in enumerate(base_families):
        support = family_support.get((domain_id, family), {"support_units": 0, "record_ids": []})
        eligible_count = len(support["record_ids"])
        modifier = bounded_modifier(support["support_units"], eligible_count)
        if eligible_count >= MIN_ELIGIBLE_SAMPLES:
            any_qualified = True
        family_rows.append((family, modifier, base_index))

    family_rows.sort(key=lambda item: (-item[1], item[2], item[0]))
    order = [item[0] for item in family_rows]
    preferred = [item[0] for item in family_rows if item[1] > 0]
    deprioritized = [item[0] for item in family_rows if item[1] < 0]
    return order, preferred, deprioritized, any_qualified


def personalize_ranking(
    base_ranking: Mapping[str, object],
    historical_calibration_status: str,
    historical_records: Sequence[object],
) -> dict:
    """Apply bounded historical personalization after immutable Phase 3 ranking."""

    base = _validate_base_ranking(base_ranking)
    if historical_calibration_status not in _CALIBRATION_STATUSES:
        _raise(
            "historical_calibration_status is invalid",
            {"historical_calibration_status": historical_calibration_status},
        )
    base_domain_map = {row["primary_domain"]: row for row in base["domains"]}
    normalized, audit = _normalize_historical_records(historical_records, base_domain_map)

    source_identity = {
        "historical_calibration_status": historical_calibration_status,
        "records": normalized,
    }
    historical_source_digest = _canonical_digest(source_identity)

    domain_support = _aggregate_domain_support(normalized)
    family_support = _aggregate_event_family_support(normalized)
    personalization_enabled = historical_calibration_status != "uncalibrated"
    any_qualified_domain = False
    any_qualified_family = False
    domains = []
    for row in base["domains"]:
        domain_id = row["primary_domain"]
        support = domain_support.get(domain_id, {"support_units": 0, "record_ids": []})
        record_ids = list(support["record_ids"])
        eligible_count = len(record_ids)
        if personalization_enabled:
            modifier = bounded_modifier(support["support_units"], eligible_count)
            domain_class = support_class(modifier, eligible_count)
            supporting_record_ids = record_ids
            if eligible_count >= MIN_ELIGIBLE_SAMPLES:
                any_qualified_domain = True
        else:
            modifier = 0
            domain_class = "insufficient"
            supporting_record_ids = []

        base_families = list(row["event_families"])
        (
            personalized_family_order,
            preferred_families,
            deprioritized_families,
            qualified_family,
        ) = _personalize_event_families(
            domain_id,
            base_families,
            family_support,
            personalization_enabled,
        )
        if qualified_family:
            any_qualified_family = True

        domains.append(
            {
                "primary_domain": domain_id,
                "base_rank": row["rank"],
                "base_ordinal_score_scaled": row["ordinal_score_scaled"],
                "historical_modifier_scaled": modifier,
                "personalized_ordering_score_scaled": row["ordinal_score_scaled"] + modifier,
                "personalized_rank": row["rank"],
                "historical_support_class": domain_class,
                "supporting_record_ids": supporting_record_ids,
                "base_event_families": base_families,
                "personalized_event_family_order": personalized_family_order,
                "preferred_event_families": preferred_families,
                "deprioritized_event_families": deprioritized_families,
                "allowed_specificity": row["allowed_specificity"],
            }
        )

    personalization_applied = personalization_enabled and (
        any_qualified_domain or any_qualified_family
    )
    if personalization_applied:
        domains.sort(
            key=lambda item: (
                -item["personalized_ordering_score_scaled"],
                item["base_rank"],
                item["primary_domain"],
            )
        )
        for personalized_rank, row in enumerate(domains, start=1):
            row["personalized_rank"] = personalized_rank
        personalization_status = "applied"
        no_op_reasons = []
    else:
        domains.sort(key=lambda item: item["base_rank"])
        for row in domains:
            row["personalized_rank"] = row["base_rank"]
        personalization_status = "no_op"
        no_op_reasons = []
        if not historical_records:
            no_op_reasons.append("no_history")
        if historical_calibration_status == "uncalibrated":
            no_op_reasons.append("uncalibrated")
        if historical_records and audit["eligible_record_count"] == 0:
            no_op_reasons.append("no_eligible_history")
        if (
            historical_calibration_status != "uncalibrated"
            and audit["eligible_record_count"] > 0
            and not any_qualified_domain
            and not any_qualified_family
        ):
            no_op_reasons.append("insufficient_history")

    result = {
        "profile_version": PERSONALIZATION_PROFILE_VERSION,
        "base_policy_version": base["policy_version"],
        "target_scope": base["target_scope"],
        "base_ranking_digest": base["ranking_digest"],
        "historical_source_digest": historical_source_digest,
        "historical_calibration_status": historical_calibration_status,
        "personalization_status": personalization_status,
        "no_op_reasons": no_op_reasons,
        "eligible_record_count": audit["eligible_record_count"],
        "excluded_record_counts": audit["excluded_record_counts"],
        "control_audit": audit["control_audit"],
        "timing_audit": audit["timing_audit"],
        "domains": domains,
    }
    result["personalization_digest"] = _canonical_digest(result)
    return result
