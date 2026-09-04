from __future__ import annotations

import copy
import hashlib
import json
from typing import Mapping

INPUT_SCHEMA = "v1.6-claim-consumption-qualification-input.v1"
REPORT_SCHEMA = "v1.6-claim-consumption-qualification-report.v1"
CLAIM_CONSUMPTION_PROFILE_VERSION = "lin_tianji_claim_consumption_v1-exp"

_CLASSIFICATIONS = frozenset(("synthetic_validation", "private_external_evaluation"))
_AUTHORIZATIONS = frozenset(("render", "render_with_caveat", "abstain_claim"))
_SPECIFICITY_ORDER = {
    "domain": 0,
    "event_family": 1,
    "concrete_event": 2,
    "highly_specific_event": 3,
}

_TOP_FIELDS = frozenset(("schema_version", "classification", "cases"))
_CASE_FIELDS = frozenset((
    "case_id",
    "claim_consumption_bundle",
    "expectations",
    "cutoff_contamination",
    "input_digest",
))
_BUNDLE_FIELDS = frozenset((
    "profile_version",
    "claim_evidence_digest",
    "coordination_digest",
    "target_scope",
    "decisions",
    "claim_consumption_digest",
))
_DECISION_FIELDS = frozenset((
    "claim_id",
    "primary_domain",
    "decision",
    "original_effective_specificity",
    "authorized_specificity",
    "confidence_class",
    "coordination_relation",
    "reason_codes",
))
_EXPECTATION_FIELDS = frozenset((
    "claim_id",
    "expected_authorization",
    "minimum_acceptable_specificity",
    "maximum_specificity",
    "caveat_required",
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
        raise ValueError("qualification input must be canonical JSON") from exc


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be a mapping")
    return value


def _list(value: object, label: str) -> list:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be non-empty text")
    return value


def _bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{label} must be boolean")
    return value


def _exact_fields(value: Mapping[str, object], allowed: frozenset, label: str) -> None:
    unknown = set(value) - allowed
    missing = allowed - set(value)
    if unknown:
        raise ValueError(f"{label} contains unknown fields: {sorted(unknown)}")
    if missing:
        raise ValueError(f"{label} is missing required fields: {sorted(missing)}")


def _sha256_text(value: object, label: str) -> str:
    text = _text(value, label)
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise ValueError(f"{label} must be lowercase sha256 hex")
    return text


def _specificity(value: object, label: str) -> str:
    if value not in _SPECIFICITY_ORDER:
        raise ValueError(f"{label} contains unsupported specificity")
    return str(value)


def _validate_decision(raw: object) -> dict:
    decision = _mapping(raw, "claim consumption decision")
    _exact_fields(decision, _DECISION_FIELDS, "claim consumption decision")

    claim_id = _text(decision["claim_id"], "decision.claim_id")
    primary_domain = _text(decision["primary_domain"], "decision.primary_domain")
    authorization = decision["decision"]
    if authorization not in _AUTHORIZATIONS:
        raise ValueError("decision.decision contains unsupported authorization")
    original = _specificity(
        decision["original_effective_specificity"],
        "decision.original_effective_specificity",
    )
    authorized = _specificity(
        decision["authorized_specificity"],
        "decision.authorized_specificity",
    )
    if _SPECIFICITY_ORDER[authorized] > _SPECIFICITY_ORDER[original]:
        raise ValueError("decision authorized_specificity cannot exceed original authority")
    confidence = _text(decision["confidence_class"], "decision.confidence_class")
    coordination = _text(decision["coordination_relation"], "decision.coordination_relation")
    reasons = _list(decision["reason_codes"], "decision.reason_codes")
    if any(not isinstance(item, str) or not item for item in reasons):
        raise ValueError("decision.reason_codes must contain non-empty text")
    if len(reasons) != len(set(reasons)):
        raise ValueError("decision.reason_codes must be unique")
    if authorization == "render" and reasons:
        raise ValueError("plain render decision must not contain caveat reason_codes")
    if authorization in {"render_with_caveat", "abstain_claim"} and not reasons:
        raise ValueError(f"{authorization} decision must contain reason_codes")

    return {
        "claim_id": claim_id,
        "primary_domain": primary_domain,
        "decision": str(authorization),
        "original_effective_specificity": original,
        "authorized_specificity": authorized,
        "confidence_class": confidence,
        "coordination_relation": coordination,
        "reason_codes": list(reasons),
    }


def _validate_bundle(raw: object) -> dict:
    bundle = _mapping(raw, "claim_consumption_bundle")
    _exact_fields(bundle, _BUNDLE_FIELDS, "claim_consumption_bundle")
    if bundle["profile_version"] != CLAIM_CONSUMPTION_PROFILE_VERSION:
        raise ValueError("claim_consumption_bundle profile_version is unsupported")
    _sha256_text(bundle["claim_evidence_digest"], "claim_evidence_digest")
    _sha256_text(bundle["coordination_digest"], "coordination_digest")
    _text(bundle["target_scope"], "target_scope")

    supplied = _sha256_text(bundle["claim_consumption_digest"], "claim_consumption_digest")
    digest_payload = dict(bundle)
    digest_payload.pop("claim_consumption_digest", None)
    if supplied != _digest(digest_payload):
        raise ValueError("claim_consumption_digest does not match bundle payload")

    decisions = [_validate_decision(row) for row in _list(bundle["decisions"], "decisions")]
    claim_ids = [row["claim_id"] for row in decisions]
    if len(claim_ids) != len(set(claim_ids)):
        raise ValueError("actual decision claim_id values must be unique")

    result = dict(bundle)
    result["decisions"] = decisions
    return result


def _validate_expectation(raw: object) -> dict:
    expected = _mapping(raw, "expectation")
    _exact_fields(expected, _EXPECTATION_FIELDS, "expectation")
    claim_id = _text(expected["claim_id"], "expectation.claim_id")
    authorization = expected["expected_authorization"]
    if authorization not in _AUTHORIZATIONS:
        raise ValueError("expected_authorization contains unsupported value")
    caveat_required = _bool(expected["caveat_required"], "caveat_required")
    expected_caveat = authorization == "render_with_caveat"
    if caveat_required != expected_caveat:
        raise ValueError("caveat_required contradicts expected_authorization")

    minimum = expected["minimum_acceptable_specificity"]
    maximum = expected["maximum_specificity"]
    if authorization == "abstain_claim":
        if minimum is not None or maximum is not None:
            raise ValueError("abstain_claim expectation requires null specificity bounds")
        normalized_minimum = None
        normalized_maximum = None
    else:
        normalized_minimum = _specificity(minimum, "minimum_acceptable_specificity")
        normalized_maximum = _specificity(maximum, "maximum_specificity")
        if _SPECIFICITY_ORDER[normalized_minimum] > _SPECIFICITY_ORDER[normalized_maximum]:
            raise ValueError("minimum_acceptable_specificity cannot exceed maximum_specificity")

    return {
        "claim_id": claim_id,
        "expected_authorization": str(authorization),
        "minimum_acceptable_specificity": normalized_minimum,
        "maximum_specificity": normalized_maximum,
        "caveat_required": caveat_required,
    }


def _validate_case(raw: object) -> dict:
    case = _mapping(raw, "case")
    _exact_fields(case, _CASE_FIELDS, "case")
    case_id = _text(case["case_id"], "case_id")

    # Validate source C1 identity before the outer case digest so source tampering
    # is reported at the authority boundary that was actually violated.
    bundle = _validate_bundle(case["claim_consumption_bundle"])

    supplied_input_digest = _sha256_text(case["input_digest"], "input_digest")
    digest_payload = dict(case)
    digest_payload.pop("input_digest", None)
    if supplied_input_digest != _digest(digest_payload):
        raise ValueError("input_digest does not match case payload")

    expectations = [
        _validate_expectation(row)
        for row in _list(case["expectations"], "expectations")
    ]
    expected_ids = [row["claim_id"] for row in expectations]
    if len(expected_ids) != len(set(expected_ids)):
        raise ValueError("expectation claim_id values must be unique")
    actual_ids = [row["claim_id"] for row in bundle["decisions"]]
    if set(expected_ids) != set(actual_ids):
        raise ValueError("expected and actual claim-id sets must match exactly")

    return {
        "case_id": case_id,
        "claim_consumption_bundle": bundle,
        "expectations": expectations,
        "cutoff_contamination": _bool(case["cutoff_contamination"], "cutoff_contamination"),
        "input_digest": supplied_input_digest,
    }


def validate_claim_consumption_qualification_input(payload: object) -> dict:
    root = _mapping(payload, "qualification input")
    _exact_fields(root, _TOP_FIELDS, "qualification input")
    if root["schema_version"] != INPUT_SCHEMA:
        raise ValueError("unsupported qualification input schema_version")
    classification = root["classification"]
    if classification not in _CLASSIFICATIONS:
        raise ValueError("unsupported qualification classification")
    cases = [_validate_case(row) for row in _list(root["cases"], "cases")]
    if not cases:
        raise ValueError("qualification input must contain at least one case")
    case_ids = [row["case_id"] for row in cases]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("case_id values must be unique")
    return copy.deepcopy(payload)


def _score_claim(expected: Mapping[str, object], actual: Mapping[str, object]) -> dict:
    expected_auth = str(expected["expected_authorization"])
    actual_auth = str(actual["decision"])

    over_render = int(expected_auth == "abstain_claim" and actual_auth != "abstain_claim")
    under_render = int(expected_auth != "abstain_claim" and actual_auth == "abstain_claim")
    caveat_omission = int(expected_auth == "render_with_caveat" and actual_auth == "render")
    unnecessary_caveat = int(expected_auth == "render" and actual_auth == "render_with_caveat")

    overreach = 0
    excessive_downgrade = 0
    if expected_auth != "abstain_claim" and actual_auth != "abstain_claim":
        actual_specificity = str(actual["authorized_specificity"])
        minimum = str(expected["minimum_acceptable_specificity"])
        maximum = str(expected["maximum_specificity"])
        overreach = int(_SPECIFICITY_ORDER[actual_specificity] > _SPECIFICITY_ORDER[maximum])
        excessive_downgrade = int(
            _SPECIFICITY_ORDER[actual_specificity] < _SPECIFICITY_ORDER[minimum]
        )

    if over_render or under_render:
        alignment = "missed"
    elif (
        expected_auth != actual_auth
        or caveat_omission
        or unnecessary_caveat
        or overreach
        or excessive_downgrade
    ):
        alignment = "partial"
    else:
        alignment = "matched"

    return {
        "alignment": alignment,
        "over_render_count": over_render,
        "under_render_count": under_render,
        "caveat_omission_count": caveat_omission,
        "unnecessary_caveat_count": unnecessary_caveat,
        "specificity_overreach_count": overreach,
        "specificity_excessive_downgrade_count": excessive_downgrade,
    }


def evaluate_claim_consumption_qualification(payload: object) -> dict:
    validate_claim_consumption_qualification_input(payload)
    root = _mapping(payload, "qualification input")
    classification = str(root["classification"])
    cases = sorted(
        (_validate_case(row) for row in _list(root["cases"], "cases")),
        key=lambda row: row["case_id"],
    )

    alignment = {"matched": 0, "partial": 0, "missed": 0}
    counters = {
        "over_render_count": 0,
        "under_render_count": 0,
        "caveat_omission_count": 0,
        "unnecessary_caveat_count": 0,
        "specificity_overreach_count": 0,
        "specificity_excessive_downgrade_count": 0,
    }
    cutoff_contamination_count = 0
    claim_count = 0

    for case in cases:
        cutoff_contamination_count += int(case["cutoff_contamination"])
        actual_by_id = {
            row["claim_id"]: row
            for row in case["claim_consumption_bundle"]["decisions"]
        }
        for expected in sorted(case["expectations"], key=lambda row: row["claim_id"]):
            scored = _score_claim(expected, actual_by_id[expected["claim_id"]])
            alignment[scored["alignment"]] += 1
            claim_count += 1
            for key in counters:
                counters[key] += scored[key]

    if cutoff_contamination_count:
        status = "FAIL"
    elif classification == "private_external_evaluation":
        status = "METRICS_ONLY"
    else:
        strict_pass = (
            counters["over_render_count"] == 0
            and counters["specificity_overreach_count"] == 0
            and alignment["partial"] == 0
            and alignment["missed"] == 0
        )
        status = "PASS" if strict_pass else "FAIL"

    input_set_digest = _digest([row["input_digest"] for row in cases])
    report = {
        "schema_version": REPORT_SCHEMA,
        "classification": classification,
        "case_count": len(cases),
        "claim_count": claim_count,
        "decision_alignment": alignment,
        **counters,
        "cutoff_contamination_count": cutoff_contamination_count,
        "input_set_digest": input_set_digest,
        "general_conformance_status": status,
        "promotion_allowed": False,
    }
    report["report_digest"] = _digest(report)
    return report
