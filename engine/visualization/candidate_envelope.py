"""Pure Candidate Envelope v2 projection into a presentation-only summary."""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from typing import Any, Mapping


PROFILE_ID = "candidate-envelope-summary-v1"
RULE_VERSION = "1.0-exp"
_CANDIDATE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_TIME = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError("%s must be an object" % field)
    return value


def _integer(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("%s must be a non-negative integer" % field)
    return value


def _text_list(value: object, field: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ValueError("%s must be a list of non-empty strings" % field)
    return list(value)


def _leaf_count(value: object) -> int:
    if isinstance(value, Mapping):
        return sum(_leaf_count(child) for child in value.values())
    if isinstance(value, list):
        return sum(_leaf_count(child) for child in value)
    return 1


def _fact_counts(envelope: Mapping[str, object]) -> dict:
    result = {}
    for classification, prefix in (
        ("invariant", "invariant"),
        ("variant", "variant"),
        ("undetermined", "undetermined"),
        ("unavailable", "unavailable"),
    ):
        result[classification] = {
            "bazi": _leaf_count(_mapping(envelope.get("%s_bazi_facts" % prefix, {}), "%s_bazi_facts" % prefix)),
            "ziwei": _leaf_count(_mapping(envelope.get("%s_ziwei_facts" % prefix, {}), "%s_ziwei_facts" % prefix)),
        }
    return result


def project_candidate_envelope_summary(envelope: Mapping[str, object]) -> dict:
    if not isinstance(envelope, Mapping):
        raise ValueError("candidate_envelope must be an object")
    if envelope.get("profile_id") != "natal-candidate-envelope-v2" or envelope.get("rule_version") != "2.0-exp":
        raise ValueError("candidate envelope visualization requires natal-candidate-envelope-v2 / 2.0-exp")

    precision = envelope.get("natal_precision_state")
    if precision not in ("exact", "bounded", "unknown_time"):
        raise ValueError("natal_precision_state is invalid")
    local_resolution = envelope.get("local_time_resolution")
    if local_resolution not in ("unique", "ambiguous_fold", "nonexistent", "range", "unknown"):
        raise ValueError("local_time_resolution is invalid")

    candidates = envelope.get("candidates")
    if not isinstance(candidates, list):
        raise ValueError("candidates must be a list")
    candidate_count = _integer(envelope.get("candidate_count"), "candidate_count")
    if candidate_count != len(candidates):
        raise ValueError("candidate_count does not match candidates")

    domain = _mapping(envelope.get("candidate_domain"), "candidate_domain")
    coverage = _mapping(envelope.get("candidate_coverage"), "candidate_coverage")
    coverage_status = coverage.get("status")
    if coverage_status not in ("complete", "partial", "unsupported"):
        raise ValueError("candidate_coverage.status is invalid")

    legal = _integer(coverage.get("legal_occurrence_count"), "candidate_coverage.legal_occurrence_count")
    materialized = _integer(
        coverage.get("materialized_occurrence_count"),
        "candidate_coverage.materialized_occurrence_count",
    )
    unresolved = _integer(
        coverage.get("unresolved_occurrence_count"),
        "candidate_coverage.unresolved_occurrence_count",
    )
    material_states = _integer(
        coverage.get("material_state_count"),
        "candidate_coverage.material_state_count",
    )
    domain_legal = _integer(domain.get("legal_occurrence_count"), "candidate_domain.legal_occurrence_count")
    excluded = _integer(domain.get("excluded_label_count"), "candidate_domain.excluded_label_count")
    if legal != domain_legal:
        raise ValueError("candidate domain and coverage legal-occurrence counts disagree")
    if materialized + unresolved != legal:
        raise ValueError("candidate coverage occurrence counts are inconsistent")
    if material_states != candidate_count:
        raise ValueError("candidate coverage material_state_count does not match candidate_count")

    spans = []
    seen = set()
    for index, raw in enumerate(candidates):
        candidate = _mapping(raw, "candidates[%d]" % index)
        candidate_id = candidate.get("candidate_id")
        if (
            not isinstance(candidate_id, str)
            or not _CANDIDATE_ID.fullmatch(candidate_id)
            or candidate_id in seen
        ):
            raise ValueError("candidate_id is invalid or duplicated")
        seen.add(candidate_id)
        start = candidate.get("reported_time_start")
        end = candidate.get("reported_time_end")
        if not isinstance(start, str) or not _TIME.fullmatch(start):
            raise ValueError("candidate reported_time_start must be canonical HH:MM")
        if not isinstance(end, str) or not _TIME.fullmatch(end):
            raise ValueError("candidate reported_time_end must be canonical HH:MM")
        occurrence_count = candidate.get("occurrence_count")
        if occurrence_count is None:
            occurrence_count = 1
        occurrence_count = _integer(occurrence_count, "candidate occurrence_count")
        if occurrence_count < 1:
            raise ValueError("candidate occurrence_count must be positive")
        spans.append(
            {
                "candidate_id": candidate_id,
                "reported_time_start": start,
                "reported_time_end": end,
                "occurrence_count": occurrence_count,
            }
        )

    allowed = _text_list(envelope.get("allowed_analysis", []), "allowed_analysis")
    blocked = _text_list(envelope.get("blocked_analysis", []), "blocked_analysis")
    boundary = envelope.get("boundary_ambiguities", [])
    if not isinstance(boundary, list):
        raise ValueError("boundary_ambiguities must be a list")

    reason_codes = []
    limitations = [
        {
            "code": "PRESENTATION_ONLY",
            "message": "Visualization summarizes Candidate Envelope authority without ranking or selecting candidates.",
            "scope": "chart",
        },
        {
            "code": "NO_CANDIDATE_PROBABILITY",
            "message": "Candidate spans are not probabilities and carry no preference order.",
            "scope": "candidate_spans",
        },
    ]
    if coverage_status == "partial":
        reason_codes.append("PARTIAL_CANDIDATE_COVERAGE")
        limitations.append(
            {
                "code": "PARTIAL_CANDIDATE_COVERAGE",
                "message": "Some legal local-time occurrences were not materialized; observed common facts remain undetermined unless coverage is complete.",
                "scope": "coverage",
            }
        )
    elif coverage_status == "unsupported":
        reason_codes.append("CANDIDATE_COVERAGE_UNSUPPORTED")
        limitations.append(
            {
                "code": "CANDIDATE_COVERAGE_UNSUPPORTED",
                "message": "Candidate coverage is unavailable for this source.",
                "scope": "coverage",
            }
        )
    if boundary:
        reason_codes.append("BOUNDARY_AMBIGUITIES_PRESENT")

    source_digest = _digest(envelope)
    chart = {
        "chart_type": "candidate_envelope_summary",
        "schema_version": "1.0",
        "status": "ready" if candidate_count and coverage_status != "unsupported" else "unsupported",
        "reason_codes": reason_codes,
        "source_profile_id": "natal-candidate-envelope-v2",
        "source_rule_version": "2.0-exp",
        "natal_precision_state": precision,
        "local_time_resolution": local_resolution,
        "coverage": {
            "status": coverage_status,
            "legal_occurrence_count": legal,
            "materialized_occurrence_count": materialized,
            "unresolved_occurrence_count": unresolved,
            "material_state_count": material_states,
            "excluded_label_count": excluded,
        },
        "candidate_spans": spans,
        "fact_counts": _fact_counts(envelope),
        "allowed_analysis": allowed,
        "blocked_analysis": blocked,
        "boundary_ambiguity_count": len(boundary),
        "provenance": {
            "projection_profile_id": PROFILE_ID,
            "projection_rule_version": RULE_VERSION,
            "source_envelope_sha256": source_digest,
        },
        "limitations": limitations,
    }
    return deepcopy(chart)
