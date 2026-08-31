"""Deterministic offline interpretation bake-off for v1.6 research."""
from __future__ import annotations

from datetime import datetime
from typing import Mapping

from .errors import DistributionError

BAKEOFF_SCHEMA_VERSION = "v1.6-interpretation-bakeoff.v1"
BAKEOFF_REPORT_SCHEMA_VERSION = "v1.6-interpretation-bakeoff-report.v1"
VARIANT_IDS = ("V0", "V1", "V2", "V3", "V4")
SPECIFICITY_ORDER = ("domain", "event_family", "concrete_event")
ABSTENTION_LABELS = (
    "abstain_domain",
    "abstain_event_family",
    "abstain_timing",
    "abstain_concrete_event",
)
FORBIDDEN_PRIVATE_FIELDS = frozenset(("actual_event", "birth_date", "subject_name"))

_TOP_LEVEL_FIELDS = frozenset(("schema_version", "classification", "cases"))
_CASE_FIELDS = frozenset((
    "case_id", "target_scope", "knowledge_cutoff_at", "allowed_evidence_ids",
    "specificity_ceiling", "ground_truth", "variants",
))
_GROUND_TRUTH_FIELDS = frozenset(("primary_domains", "event_families", "actual_at"))
_VARIANT_FIELDS = frozenset(("variant_id", "claims", "personalization_records"))
_CLAIM_FIELDS = frozenset((
    "claim_id", "primary_domain", "event_family", "forecast_start", "forecast_end",
    "specificity", "evidence_ids", "abstentions",
))
_PERSONALIZATION_FIELDS = frozenset((
    "record_id", "knowledge_available_at", "domain", "event_family", "evaluation",
))
_PERSONALIZATION_EVALUATIONS = ("matched", "partial", "missed")


def _raise(message: str, details=None) -> None:
    raise DistributionError("invalid_v16_bakeoff", message, details)


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        _raise(f"{field} must be a mapping")
    return value


def _exact_fields(value: Mapping[str, object], allowed: frozenset[str], field: str) -> None:
    unknown = sorted(set(value) - allowed)
    missing = sorted(allowed - set(value))
    if unknown:
        _raise(f"{field} has unknown fields: {', '.join(unknown)}")
    if missing:
        _raise(f"{field} is missing fields: {', '.join(missing)}")


def _reject_private_keys(value: object, path: str = "payload") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in FORBIDDEN_PRIVATE_FIELDS:
                _raise(f"forbidden private-looking field at {path}.{key}")
            _reject_private_keys(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_private_keys(item, f"{path}[{index}]")


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        _raise(f"{field} must be non-empty text")
    return value


def _texts(value: object, field: str, *, allow_empty: bool = True) -> list[str]:
    if not isinstance(value, list):
        _raise(f"{field} must be a list")
    rows = []
    for item in value:
        rows.append(_text(item, field))
    if not allow_empty and not rows:
        _raise(f"{field} must not be empty")
    if len(rows) != len(set(rows)):
        _raise(f"{field} entries must be unique")
    return rows


def _aware_datetime(value: object, field: str) -> str:
    text = _text(value, field)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        _raise(f"{field} must be ISO datetime")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        _raise(f"{field} must be offset-aware")
    return text


def _specificity(value: object, field: str) -> str:
    text = _text(value, field)
    if text not in SPECIFICITY_ORDER:
        _raise(f"{field} has unsupported specificity: {text}")
    return text


def _normalize_claim(raw: object, field: str) -> dict:
    value = _mapping(raw, field)
    _exact_fields(value, _CLAIM_FIELDS, field)
    event_family = value["event_family"]
    if event_family is not None:
        event_family = _text(event_family, f"{field}.event_family")
    abstentions = _texts(value["abstentions"], f"{field}.abstentions")
    invalid_abstentions = sorted(set(abstentions) - set(ABSTENTION_LABELS))
    if invalid_abstentions:
        _raise(f"{field}.abstentions contains unsupported labels: {', '.join(invalid_abstentions)}")
    start = _aware_datetime(value["forecast_start"], f"{field}.forecast_start")
    end = _aware_datetime(value["forecast_end"], f"{field}.forecast_end")
    if datetime.fromisoformat(start) > datetime.fromisoformat(end):
        _raise(f"{field} forecast_start must not be after forecast_end")
    return {
        "claim_id": _text(value["claim_id"], f"{field}.claim_id"),
        "primary_domain": _text(value["primary_domain"], f"{field}.primary_domain"),
        "event_family": event_family,
        "forecast_start": start,
        "forecast_end": end,
        "specificity": _specificity(value["specificity"], f"{field}.specificity"),
        "evidence_ids": _texts(value["evidence_ids"], f"{field}.evidence_ids"),
        "abstentions": abstentions,
    }


def validate_v4_cutoff(records, knowledge_cutoff_at: str) -> tuple[dict, ...]:
    cutoff_text = _aware_datetime(knowledge_cutoff_at, "knowledge_cutoff_at")
    cutoff = datetime.fromisoformat(cutoff_text)
    if not isinstance(records, (list, tuple)):
        _raise("V4 personalization records must be a sequence")
    normalized = []
    contaminated = []
    for index, raw in enumerate(records):
        field = f"personalization_records[{index}]"
        value = _mapping(raw, field)
        _exact_fields(value, _PERSONALIZATION_FIELDS, field)
        available_text = _aware_datetime(value["knowledge_available_at"], f"{field}.knowledge_available_at")
        available = datetime.fromisoformat(available_text)
        event_family = value["event_family"]
        if event_family is not None:
            event_family = _text(event_family, f"{field}.event_family")
        evaluation = _text(value["evaluation"], f"{field}.evaluation")
        if evaluation not in _PERSONALIZATION_EVALUATIONS:
            _raise(f"{field}.evaluation is unsupported: {evaluation}")
        record = {
            "record_id": _text(value["record_id"], f"{field}.record_id"),
            "knowledge_available_at": available_text,
            "domain": _text(value["domain"], f"{field}.domain"),
            "event_family": event_family,
            "evaluation": evaluation,
        }
        normalized.append(record)
        if available > cutoff:
            contaminated.append(record)
    record_ids = [row["record_id"] for row in normalized]
    if len(record_ids) != len(set(record_ids)):
        _raise("V4 personalization record_id values must be unique")
    if contaminated:
        raise DistributionError(
            "bakeoff_cutoff_contamination",
            "V4 personalization record is after per-target cutoff",
            {
                "record_ids": [row["record_id"] for row in contaminated],
                "knowledge_available_at": [row["knowledge_available_at"] for row in contaminated],
                "knowledge_cutoff_at": cutoff_text,
            },
        )
    return tuple(normalized)


def _normalize_variant(raw: object, field: str) -> dict:
    value = _mapping(raw, field)
    _exact_fields(value, _VARIANT_FIELDS, field)
    variant_id = _text(value["variant_id"], f"{field}.variant_id")
    if variant_id not in VARIANT_IDS:
        _raise(f"{field}.variant_id is unsupported: {variant_id}")
    claims = value["claims"]
    if not isinstance(claims, list) or not claims:
        _raise(f"{field}.claims must be a non-empty list")
    personalization = value["personalization_records"]
    if not isinstance(personalization, list):
        _raise(f"{field}.personalization_records must be a list")
    return {
        "variant_id": variant_id,
        "claims": [_normalize_claim(item, f"{field}.claims[{index}]") for index, item in enumerate(claims)],
        "personalization_records": [dict(_mapping(item, f"{field}.personalization_records")) for item in personalization],
    }


def _normalize_case(raw: object, field: str) -> dict:
    value = _mapping(raw, field)
    _exact_fields(value, _CASE_FIELDS, field)
    ground = _mapping(value["ground_truth"], f"{field}.ground_truth")
    _exact_fields(ground, _GROUND_TRUTH_FIELDS, f"{field}.ground_truth")
    variants = value["variants"]
    if not isinstance(variants, list):
        _raise(f"{field}.variants must be a list")
    normalized_variants = [_normalize_variant(item, f"{field}.variants[{index}]") for index, item in enumerate(variants)]
    variant_ids = [item["variant_id"] for item in normalized_variants]
    if variant_ids != list(VARIANT_IDS):
        _raise(f"{field}.variants must contain V0..V4 exactly once in order")
    cutoff = _aware_datetime(value["knowledge_cutoff_at"], f"{field}.knowledge_cutoff_at")
    for variant in normalized_variants:
        records = variant["personalization_records"]
        if variant["variant_id"] != "V4" and records:
            _raise(f"{variant['variant_id']} personalization_records must be empty")
        if variant["variant_id"] == "V4":
            variant["personalization_records"] = list(validate_v4_cutoff(records, cutoff))
    return {
        "case_id": _text(value["case_id"], f"{field}.case_id"),
        "target_scope": _text(value["target_scope"], f"{field}.target_scope"),
        "knowledge_cutoff_at": cutoff,
        "allowed_evidence_ids": _texts(value["allowed_evidence_ids"], f"{field}.allowed_evidence_ids"),
        "specificity_ceiling": _specificity(value["specificity_ceiling"], f"{field}.specificity_ceiling"),
        "ground_truth": {
            "primary_domains": _texts(ground["primary_domains"], f"{field}.ground_truth.primary_domains", allow_empty=False),
            "event_families": _texts(ground["event_families"], f"{field}.ground_truth.event_families"),
            "actual_at": _aware_datetime(ground["actual_at"], f"{field}.ground_truth.actual_at"),
        },
        "variants": normalized_variants,
    }


def validate_bakeoff_fixture(payload: Mapping[str, object]) -> dict:
    raw = _mapping(payload, "payload")
    _reject_private_keys(raw)
    _exact_fields(raw, _TOP_LEVEL_FIELDS, "payload")
    if raw["schema_version"] != BAKEOFF_SCHEMA_VERSION:
        _raise("unsupported bakeoff schema_version")
    if raw["classification"] != "synthetic_test_case":
        _raise("public v1.6 bakeoff fixture must be classified synthetic_test_case")
    cases = raw["cases"]
    if not isinstance(cases, list) or len(cases) < 5:
        _raise("bakeoff fixture must contain at least five cases")
    normalized_cases = [_normalize_case(case, f"cases[{index}]") for index, case in enumerate(cases)]
    case_ids = [case["case_id"] for case in normalized_cases]
    if len(case_ids) != len(set(case_ids)):
        _raise("case_id values must be unique")
    claim_ids = []
    for case in normalized_cases:
        for variant in case["variants"]:
            claim_ids.extend(claim["claim_id"] for claim in variant["claims"])
    if len(claim_ids) != len(set(claim_ids)):
        _raise("claim_id values must be unique across fixture")
    return {
        "schema_version": BAKEOFF_SCHEMA_VERSION,
        "classification": "synthetic_test_case",
        "cases": normalized_cases,
    }


def _count(keys: tuple[str, ...]) -> dict:
    return {key: 0 for key in keys}


def _abstention_quality(claim: Mapping[str, object], ceiling: str) -> list[str]:
    results = []
    has_timing_evidence = any(str(item).upper().startswith("E-TIME-") for item in claim["evidence_ids"])
    for label in claim["abstentions"]:
        appropriate = (
            (label == "abstain_event_family" and ceiling == "domain")
            or (label == "abstain_concrete_event" and ceiling != "concrete_event")
            or (label == "abstain_timing" and not has_timing_evidence)
        )
        results.append("appropriate" if appropriate else "over_abstained")
    return results


def evaluate_bakeoff(payload: Mapping[str, object]) -> dict:
    fixture = validate_bakeoff_fixture(payload)
    variants = {}
    for variant_id in VARIANT_IDS:
        alignment = {
            "domain_match": _count(("matched", "missed")),
            "event_family_match": _count(("matched", "missed", "unscorable")),
            "timing_match": _count(("matched", "missed", "unscorable")),
            "specificity_appropriateness": _count(("pass", "fail")),
        }
        honesty = {
            "false_positive_count": 0,
            "unsupported_inference_count": 0,
            "method_leakage_count": 0,
            "abstention_quality": _count(("appropriate", "over_abstained")),
            "cutoff_contamination_count": 0,
        }
        traceability = _count(("traceable", "not_traceable"))
        for case in fixture["cases"]:
            truth = case["ground_truth"]
            allowed = set(case["allowed_evidence_ids"])
            ceiling = case["specificity_ceiling"]
            variant = next(item for item in case["variants"] if item["variant_id"] == variant_id)
            for claim in variant["claims"]:
                abstentions = set(claim["abstentions"])
                domain_active = "abstain_domain" not in abstentions
                family_active = claim["event_family"] is not None and "abstain_event_family" not in abstentions
                timing_active = "abstain_timing" not in abstentions

                domain_status = "matched" if claim["primary_domain"] in truth["primary_domains"] else "missed"
                alignment["domain_match"][domain_status] += 1

                if not family_active:
                    family_status = "unscorable"
                else:
                    family_status = "matched" if claim["event_family"] in truth["event_families"] else "missed"
                alignment["event_family_match"][family_status] += 1

                if not timing_active:
                    timing_status = "unscorable"
                else:
                    actual = datetime.fromisoformat(truth["actual_at"])
                    start = datetime.fromisoformat(claim["forecast_start"])
                    end = datetime.fromisoformat(claim["forecast_end"])
                    timing_status = "matched" if start <= actual <= end else "missed"
                alignment["timing_match"][timing_status] += 1

                specificity_ok = SPECIFICITY_ORDER.index(claim["specificity"]) <= SPECIFICITY_ORDER.index(ceiling)
                alignment["specificity_appropriateness"]["pass" if specificity_ok else "fail"] += 1

                domain_false = domain_active and claim["primary_domain"] not in truth["primary_domains"]
                family_false = family_active and claim["event_family"] not in truth["event_families"]
                if domain_false or family_false:
                    honesty["false_positive_count"] += 1

                unsupported = [item for item in claim["evidence_ids"] if item not in allowed]
                if unsupported:
                    honesty["unsupported_inference_count"] += 1
                if (not specificity_ok) or unsupported:
                    honesty["method_leakage_count"] += 1

                for quality in _abstention_quality(claim, ceiling):
                    honesty["abstention_quality"][quality] += 1

                if claim["abstentions"]:
                    traceability["traceable"] += 1
                elif claim["evidence_ids"] and not unsupported:
                    traceability["traceable"] += 1
                else:
                    traceability["not_traceable"] += 1

        variants[variant_id] = {
            "structural_outcome_alignment": alignment,
            "honesty_safety": honesty,
            "explanation_ux": {
                "reasoning_traceability": traceability,
                "readability": "externally_adjudicated",
                "actionability": "externally_adjudicated",
            },
        }
    return {
        "schema_version": BAKEOFF_REPORT_SCHEMA_VERSION,
        "classification": "synthetic_validation",
        "case_count": len(fixture["cases"]),
        "variant_ids": list(VARIANT_IDS),
        "variants": variants,
        "cutoff_contamination_count": 0,
        "release_eligible": True,
    }
