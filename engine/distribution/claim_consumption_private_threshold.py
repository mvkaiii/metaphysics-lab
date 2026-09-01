from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone
from typing import Mapping

POLICY_SCHEMA = "v1.6-claim-consumption-private-release-policy.v1"
SAMPLING_SCHEMA = "v1.6-claim-consumption-sampling-eligibility-receipt.v1"
IDENTITY_SCHEMA = "v1.6-claim-consumption-private-evaluation-identity-receipt.v1"
ORACLE_RECEIPT_SCHEMA = "v1.6-claim-consumption-oracle-seal-receipt.v1"
ORACLE_SEAL_SCHEMA = "v1.6-claim-consumption-oracle-seal.v1"
Q1_REPORT_SCHEMA = "v1.6-claim-consumption-qualification-report.v1"
REPORT_SCHEMA = "v1.6-claim-consumption-private-release-gate-report.v1"
POLICY_PROFILE = "lin_tianji_claim_consumption_private_strict_zero_v1"

_POLICY_FIELDS = frozenset((
    "schema_version",
    "policy_profile",
    "policy_frozen_at",
    "thresholds",
    "policy_digest",
    "promotion_allowed",
))
_THRESHOLD_FIELDS = frozenset((
    "cutoff_contamination_count",
    "over_render_count",
    "under_render_count",
    "caveat_omission_count",
    "unnecessary_caveat_count",
    "specificity_overreach_count",
    "specificity_excessive_downgrade_count",
    "partial_alignment_count",
    "missed_alignment_count",
))
_SAMPLING_FIELDS = frozenset((
    "schema_version",
    "sampling_profile",
    "status",
    "case_count",
    "claim_count",
    "sampling_protocol_digest",
    "sealed_at",
    "receipt_digest",
    "promotion_allowed",
))
_IDENTITY_FIELDS = frozenset((
    "schema_version",
    "candidate_sha",
    "oracle_seal_digest",
    "qualification_input_set_digest",
    "case_count",
    "claim_count",
    "bound_at",
    "receipt_digest",
    "promotion_allowed",
))
_ORACLE_RECEIPT_FIELDS = frozenset((
    "schema_version",
    "status",
    "oracle_profile",
    "case_count",
    "claim_count",
    "rubric_digest",
    "case_set_digest",
    "oracle_expectation_digest",
    "cutoff_contamination_count",
    "sealed_at",
    "seal_digest",
    "promotion_allowed",
))
_Q1_REPORT_FIELDS = frozenset((
    "schema_version",
    "classification",
    "case_count",
    "claim_count",
    "decision_alignment",
    "over_render_count",
    "under_render_count",
    "caveat_omission_count",
    "unnecessary_caveat_count",
    "specificity_overreach_count",
    "specificity_excessive_downgrade_count",
    "cutoff_contamination_count",
    "input_set_digest",
    "general_conformance_status",
    "promotion_allowed",
    "report_digest",
))
_ALIGNMENT_FIELDS = frozenset(("matched", "partial", "missed"))
_REPORT_FIELDS = frozenset((
    "schema_version",
    "policy_profile",
    "policy_digest",
    "sampling_profile",
    "sampling_receipt_digest",
    "evaluation_identity_receipt_digest",
    "candidate_sha",
    "oracle_seal_digest",
    "qualification_input_set_digest",
    "q1_report_digest",
    "case_count",
    "claim_count",
    "eligibility_status",
    "private_gate_status",
    "strict_zero_metrics",
    "promotion_allowed",
    "report_digest",
))


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
        raise ValueError("private threshold input must be canonical JSON") from exc


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be a mapping")
    return value


def _exact_fields(value: Mapping[str, object], allowed: frozenset, label: str) -> None:
    unknown = set(value) - allowed
    missing = allowed - set(value)
    if unknown:
        raise ValueError(f"{label} contains unknown fields: {sorted(unknown)}")
    if missing:
        raise ValueError(f"{label} is missing required fields: {sorted(missing)}")


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be non-empty text")
    return value


def _false(value: object, label: str) -> bool:
    if value is not False:
        raise ValueError(f"{label} must be false")
    return False


def _nonnegative_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    return value


def _positive_int(value: object, label: str) -> int:
    result = _nonnegative_int(value, label)
    if result < 1:
        raise ValueError(f"{label} must be at least 1")
    return result


def _sha256_text(value: object, label: str) -> str:
    text = _text(value, label)
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise ValueError(f"{label} must be lowercase sha256 hex")
    return text


def _git_sha(value: object, label: str) -> str:
    text = _text(value, label)
    if len(text) != 40 or any(ch not in "0123456789abcdef" for ch in text):
        raise ValueError(f"{label} must be 40-character lowercase git sha")
    return text


def _timestamp(value: object, label: str) -> str:
    text = _text(value, label)
    if not text.endswith("Z"):
        raise ValueError(f"{label} must be UTC RFC3339 Z timestamp")
    try:
        parsed = datetime.fromisoformat(text[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError(f"{label} must be UTC RFC3339 Z timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError(f"{label} must be UTC RFC3339 Z timestamp")
    return text


def _timestamp_value(value: str) -> datetime:
    return datetime.fromisoformat(value[:-1] + "+00:00")


def validate_private_release_policy(payload: object) -> dict:
    policy = _mapping(payload, "private release policy")
    _exact_fields(policy, _POLICY_FIELDS, "private release policy")
    if policy["schema_version"] != POLICY_SCHEMA:
        raise ValueError("unsupported private release policy schema_version")
    if policy["policy_profile"] != POLICY_PROFILE:
        raise ValueError("unsupported private release policy_profile")
    thresholds = _mapping(policy["thresholds"], "thresholds")
    _exact_fields(thresholds, _THRESHOLD_FIELDS, "thresholds")
    normalized_thresholds = {}
    for key in sorted(_THRESHOLD_FIELDS):
        value = _nonnegative_int(thresholds[key], f"thresholds.{key}")
        if value != 0:
            raise ValueError("strict-zero policy thresholds must all equal 0")
        normalized_thresholds[key] = value
    normalized = {
        "schema_version": POLICY_SCHEMA,
        "policy_profile": POLICY_PROFILE,
        "policy_frozen_at": _timestamp(policy["policy_frozen_at"], "policy_frozen_at"),
        "thresholds": normalized_thresholds,
        "policy_digest": _sha256_text(policy["policy_digest"], "policy_digest"),
        "promotion_allowed": _false(policy["promotion_allowed"], "promotion_allowed"),
    }
    supplied = normalized["policy_digest"]
    digest_payload = dict(normalized)
    digest_payload.pop("policy_digest")
    if supplied != _digest(digest_payload):
        raise ValueError("policy_digest does not match policy payload")
    return copy.deepcopy(dict(policy))


def validate_sampling_eligibility_receipt(payload: object) -> dict:
    receipt = _mapping(payload, "sampling eligibility receipt")
    _exact_fields(receipt, _SAMPLING_FIELDS, "sampling eligibility receipt")
    if receipt["schema_version"] != SAMPLING_SCHEMA:
        raise ValueError("unsupported sampling eligibility schema_version")
    status = receipt["status"]
    if status not in {"ELIGIBLE", "INELIGIBLE"}:
        raise ValueError("sampling status must be ELIGIBLE or INELIGIBLE")
    case_count = _nonnegative_int(receipt["case_count"], "case_count")
    claim_count = _nonnegative_int(receipt["claim_count"], "claim_count")
    if status == "ELIGIBLE" and (case_count < 1 or claim_count < 1):
        raise ValueError("ELIGIBLE sampling receipt requires positive case/claim counts")
    normalized = {
        "schema_version": SAMPLING_SCHEMA,
        "sampling_profile": _text(receipt["sampling_profile"], "sampling_profile"),
        "status": str(status),
        "case_count": case_count,
        "claim_count": claim_count,
        "sampling_protocol_digest": _sha256_text(receipt["sampling_protocol_digest"], "sampling_protocol_digest"),
        "sealed_at": _timestamp(receipt["sealed_at"], "sampling sealed_at"),
        "receipt_digest": _sha256_text(receipt["receipt_digest"], "sampling receipt_digest"),
        "promotion_allowed": _false(receipt["promotion_allowed"], "promotion_allowed"),
    }
    supplied = normalized["receipt_digest"]
    digest_payload = dict(normalized)
    digest_payload.pop("receipt_digest")
    if supplied != _digest(digest_payload):
        raise ValueError("sampling receipt_digest does not match receipt payload")
    return copy.deepcopy(dict(receipt))


def validate_private_evaluation_identity_receipt(payload: object) -> dict:
    receipt = _mapping(payload, "private evaluation identity receipt")
    _exact_fields(receipt, _IDENTITY_FIELDS, "private evaluation identity receipt")
    if receipt["schema_version"] != IDENTITY_SCHEMA:
        raise ValueError("unsupported evaluation identity schema_version")
    normalized = {
        "schema_version": IDENTITY_SCHEMA,
        "candidate_sha": _git_sha(receipt["candidate_sha"], "candidate_sha"),
        "oracle_seal_digest": _sha256_text(receipt["oracle_seal_digest"], "oracle_seal_digest"),
        "qualification_input_set_digest": _sha256_text(receipt["qualification_input_set_digest"], "qualification_input_set_digest"),
        "case_count": _positive_int(receipt["case_count"], "case_count"),
        "claim_count": _positive_int(receipt["claim_count"], "claim_count"),
        "bound_at": _timestamp(receipt["bound_at"], "bound_at"),
        "receipt_digest": _sha256_text(receipt["receipt_digest"], "evaluation identity receipt_digest"),
        "promotion_allowed": _false(receipt["promotion_allowed"], "promotion_allowed"),
    }
    supplied = normalized["receipt_digest"]
    digest_payload = dict(normalized)
    digest_payload.pop("receipt_digest")
    if supplied != _digest(digest_payload):
        raise ValueError("evaluation identity receipt_digest does not match receipt payload")
    return copy.deepcopy(dict(receipt))


def validate_oracle_seal_receipt(payload: object) -> dict:
    receipt = _mapping(payload, "oracle seal receipt")
    _exact_fields(receipt, _ORACLE_RECEIPT_FIELDS, "oracle seal receipt")
    if receipt["schema_version"] != ORACLE_RECEIPT_SCHEMA:
        raise ValueError("unsupported oracle seal receipt schema_version")
    if receipt["status"] != "SEALED":
        raise ValueError("oracle seal receipt status must be SEALED")
    normalized = {
        "schema_version": ORACLE_RECEIPT_SCHEMA,
        "status": "SEALED",
        "oracle_profile": _text(receipt["oracle_profile"], "oracle_profile"),
        "case_count": _nonnegative_int(receipt["case_count"], "case_count"),
        "claim_count": _nonnegative_int(receipt["claim_count"], "claim_count"),
        "rubric_digest": _sha256_text(receipt["rubric_digest"], "rubric_digest"),
        "case_set_digest": _sha256_text(receipt["case_set_digest"], "case_set_digest"),
        "oracle_expectation_digest": _sha256_text(receipt["oracle_expectation_digest"], "oracle_expectation_digest"),
        "cutoff_contamination_count": _nonnegative_int(receipt["cutoff_contamination_count"], "cutoff_contamination_count"),
        "sealed_at": _timestamp(receipt["sealed_at"], "oracle sealed_at"),
        "seal_digest": _sha256_text(receipt["seal_digest"], "seal_digest"),
        "promotion_allowed": _false(receipt["promotion_allowed"], "promotion_allowed"),
    }
    seal_payload = {
        "schema_version": ORACLE_SEAL_SCHEMA,
        "oracle_profile": normalized["oracle_profile"],
        "case_count": normalized["case_count"],
        "claim_count": normalized["claim_count"],
        "rubric_digest": normalized["rubric_digest"],
        "oracle_expectation_digest": normalized["oracle_expectation_digest"],
        "case_set_digest": normalized["case_set_digest"],
        "cutoff_contamination_count": normalized["cutoff_contamination_count"],
        "sealed_at": normalized["sealed_at"],
    }
    if normalized["seal_digest"] != _digest(seal_payload):
        raise ValueError("seal_digest does not match oracle seal payload")
    return copy.deepcopy(dict(receipt))


def validate_q1_private_report(payload: object) -> dict:
    report = _mapping(payload, "Q1 private report")
    _exact_fields(report, _Q1_REPORT_FIELDS, "Q1 private report")
    if report["schema_version"] != Q1_REPORT_SCHEMA:
        raise ValueError("unsupported Q1 report schema_version")
    if report["classification"] != "private_external_evaluation":
        raise ValueError("Q1 classification must be private_external_evaluation")
    if report["general_conformance_status"] != "METRICS_ONLY":
        raise ValueError("Q1 private report must be METRICS_ONLY")
    _false(report["promotion_allowed"], "promotion_allowed")
    case_count = _positive_int(report["case_count"], "case_count")
    claim_count = _nonnegative_int(report["claim_count"], "claim_count")
    alignment = _mapping(report["decision_alignment"], "decision_alignment")
    _exact_fields(alignment, _ALIGNMENT_FIELDS, "decision_alignment")
    matched = _nonnegative_int(alignment["matched"], "decision_alignment.matched")
    partial = _nonnegative_int(alignment["partial"], "decision_alignment.partial")
    missed = _nonnegative_int(alignment["missed"], "decision_alignment.missed")
    if matched + partial + missed != claim_count:
        raise ValueError("decision_alignment totals must equal claim_count")
    for key in (
        "over_render_count",
        "under_render_count",
        "caveat_omission_count",
        "unnecessary_caveat_count",
        "specificity_overreach_count",
        "specificity_excessive_downgrade_count",
        "cutoff_contamination_count",
    ):
        _nonnegative_int(report[key], key)
    _sha256_text(report["input_set_digest"], "input_set_digest")
    supplied = _sha256_text(report["report_digest"], "report_digest")
    digest_payload = dict(report)
    digest_payload.pop("report_digest")
    if supplied != _digest(digest_payload):
        raise ValueError("report_digest does not match Q1 report payload")
    return copy.deepcopy(dict(report))


def evaluate_claim_consumption_private_threshold(
    policy: object,
    sampling_receipt: object,
    oracle_receipt: object,
    evaluation_identity_receipt: object,
    q1_report: object,
) -> dict:
    validated_policy = validate_private_release_policy(policy)
    validated_sampling = validate_sampling_eligibility_receipt(sampling_receipt)
    validated_oracle = validate_oracle_seal_receipt(oracle_receipt)
    validated_identity = validate_private_evaluation_identity_receipt(evaluation_identity_receipt)
    validated_q1 = validate_q1_private_report(q1_report)

    policy_time = _timestamp_value(str(validated_policy["policy_frozen_at"]))
    sampling_time = _timestamp_value(str(validated_sampling["sealed_at"]))
    oracle_time = _timestamp_value(str(validated_oracle["sealed_at"]))
    identity_time = _timestamp_value(str(validated_identity["bound_at"]))

    counts_equal = (
        validated_sampling["case_count"]
        == validated_identity["case_count"]
        == validated_oracle["case_count"]
        == validated_q1["case_count"]
        and validated_sampling["claim_count"]
        == validated_identity["claim_count"]
        == validated_oracle["claim_count"]
        == validated_q1["claim_count"]
    )
    bindings_equal = (
        validated_identity["oracle_seal_digest"] == validated_oracle["seal_digest"]
        and validated_identity["qualification_input_set_digest"] == validated_q1["input_set_digest"]
    )
    prospective = (
        policy_time < oracle_time
        and sampling_time <= oracle_time
        and oracle_time <= identity_time
    )
    eligible = (
        validated_sampling["status"] == "ELIGIBLE"
        and counts_equal
        and bindings_equal
        and prospective
        and validated_oracle["cutoff_contamination_count"] == 0
    )

    strict_zero_metrics = {
        "cutoff_contamination_count": validated_q1["cutoff_contamination_count"],
        "over_render_count": validated_q1["over_render_count"],
        "under_render_count": validated_q1["under_render_count"],
        "caveat_omission_count": validated_q1["caveat_omission_count"],
        "unnecessary_caveat_count": validated_q1["unnecessary_caveat_count"],
        "specificity_overreach_count": validated_q1["specificity_overreach_count"],
        "specificity_excessive_downgrade_count": validated_q1["specificity_excessive_downgrade_count"],
        "partial_alignment_count": validated_q1["decision_alignment"]["partial"],
        "missed_alignment_count": validated_q1["decision_alignment"]["missed"],
    }

    if not eligible:
        eligibility_status = "INELIGIBLE"
        private_gate_status = "INELIGIBLE"
    else:
        eligibility_status = "ELIGIBLE"
        private_gate_status = "PASS" if all(value == 0 for value in strict_zero_metrics.values()) else "FAIL"

    report = {
        "schema_version": REPORT_SCHEMA,
        "policy_profile": validated_policy["policy_profile"],
        "policy_digest": validated_policy["policy_digest"],
        "sampling_profile": validated_sampling["sampling_profile"],
        "sampling_receipt_digest": validated_sampling["receipt_digest"],
        "evaluation_identity_receipt_digest": validated_identity["receipt_digest"],
        "candidate_sha": validated_identity["candidate_sha"],
        "oracle_seal_digest": validated_oracle["seal_digest"],
        "qualification_input_set_digest": validated_q1["input_set_digest"],
        "q1_report_digest": validated_q1["report_digest"],
        "case_count": validated_q1["case_count"],
        "claim_count": validated_q1["claim_count"],
        "eligibility_status": eligibility_status,
        "private_gate_status": private_gate_status,
        "strict_zero_metrics": strict_zero_metrics,
        "promotion_allowed": False,
    }
    _exact_fields(report, _REPORT_FIELDS - {"report_digest"}, "private gate report")
    report["report_digest"] = _digest(report)
    _exact_fields(report, _REPORT_FIELDS, "private gate report")
    return report
