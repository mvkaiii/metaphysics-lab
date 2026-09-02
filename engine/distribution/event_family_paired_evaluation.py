"""Aggregate-only paired Legacy vs Hybrid event-family evaluation for v1.6 research.

The evaluator consumes a sealed structured child-outcome oracle, a deterministic
Legacy Adapter bundle, and a frozen Hybrid Output Contract bundle.  It never
parses renderer prose, never changes either arm, and never authorizes release.
"""

from __future__ import annotations

import hashlib
import json
from typing import Mapping

from .event_family_legacy_adapter import EVENT_FAMILY_LEGACY_ADAPTER_PROFILE_VERSION
from .event_family_paired_oracle import verify_event_family_paired_oracle
from .hybrid_output_contract import HYBRID_OUTPUT_CONTRACT_PROFILE_VERSION


PAIRED_INPUT_SCHEMA = "v1.6-event-family-paired-evaluation-input.v1"
PAIRED_REPORT_SCHEMA = "v1.6-event-family-paired-evaluation-report.v1"

_ROOT_FIELDS = frozenset((
    "schema_version",
    "classification",
    "oracle",
    "oracle_seal_receipt",
    "cases",
))
_CASE_FIELDS = frozenset((
    "case_id",
    "legacy_adapter_bundle",
    "candidate_hoc_bundle",
    "input_digest",
))

_SPECIFICITY_ORDER = {
    "event_family": 0,
    "concrete_event": 1,
    "highly_specific_event": 2,
}
_RENDERABLE = frozenset(("render", "render_with_caveat"))

_METRIC_FIELDS = (
    "supported_child_hit_count",
    "supported_child_miss_count",
    "unsupported_child_render_count",
    "specificity_overreach_count",
    "caveat_error_count",
    "false_convergence_count",
)


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
        raise ValueError("paired evaluation input must be canonical JSON") from exc


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


def _sha256(value: object, label: str) -> str:
    text = _text(value, label)
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise ValueError(f"{label} must be lowercase sha256 hex")
    return text


def _exact_fields(value: Mapping[str, object], allowed: frozenset, label: str) -> None:
    unknown = set(value) - allowed
    missing = allowed - set(value)
    if unknown:
        raise ValueError(f"{label} contains unknown fields: {sorted(unknown)}")
    if missing:
        raise ValueError(f"{label} is missing required fields: {sorted(missing)}")


def _validated_bundle_digest(bundle: Mapping[str, object], field: str, label: str) -> str:
    supplied = _sha256(bundle.get(field), field)
    body = dict(bundle)
    body.pop(field, None)
    actual = _digest(body)
    if actual != supplied:
        raise ValueError(f"{label} digest does not match payload")
    return supplied


def _child_identity(raw: Mapping[str, object], label: str) -> dict:
    return {
        "child_claim_id": _text(raw.get("child_claim_id"), f"{label}.child_claim_id"),
        "primary_domain": _text(raw.get("primary_domain"), f"{label}.primary_domain"),
        "event_family": _text(raw.get("event_family"), f"{label}.event_family"),
    }


def _validated_legacy(bundle: object) -> dict:
    source = _mapping(bundle, "legacy_adapter_bundle")
    if source.get("profile_version") != EVENT_FAMILY_LEGACY_ADAPTER_PROFILE_VERSION:
        raise ValueError("unsupported Legacy Adapter profile")
    target_scope = _text(source.get("target_scope"), "legacy target_scope")
    _validated_bundle_digest(source, "legacy_adapter_digest", "Legacy Adapter")
    raw_children = _list(source.get("children"), "Legacy Adapter children")
    children = {}
    for raw in raw_children:
        row = _mapping(raw, "Legacy Adapter child")
        identity = _child_identity(row, "Legacy Adapter child")
        child_id = identity["child_claim_id"]
        if child_id in children:
            raise ValueError("Legacy Adapter child IDs must be unique")
        decision = row.get("decision")
        if decision not in _RENDERABLE and decision != "abstain_child":
            raise ValueError("Legacy Adapter child decision is unsupported")
        specificity = row.get("authorized_specificity")
        if decision in _RENDERABLE:
            if specificity not in _SPECIFICITY_ORDER:
                raise ValueError("renderable Legacy child specificity is unsupported")
        elif specificity is not None:
            raise ValueError("abstained Legacy child specificity must be null")
        caveat = row.get("caveat_required")
        if not isinstance(caveat, bool):
            raise ValueError("Legacy child caveat_required must be boolean")
        relation = row.get("projected_cross_system_relation")
        if not isinstance(relation, str) or not relation:
            raise ValueError("Legacy child projected relation must be non-empty text")
        children[child_id] = {
            **identity,
            "rendered": decision in _RENDERABLE,
            "specificity": specificity,
            "caveated": caveat,
            "relation": relation,
        }
    if not children:
        raise ValueError("Legacy Adapter must contain at least one child")
    return {
        "target_scope": target_scope,
        "children": children,
        "universe": sorted(
            [
                {
                    "child_claim_id": row["child_claim_id"],
                    "primary_domain": row["primary_domain"],
                    "event_family": row["event_family"],
                }
                for row in children.values()
            ],
            key=lambda row: row["child_claim_id"],
        ),
    }


def _validated_candidate(bundle: object) -> dict:
    source = _mapping(bundle, "candidate_hoc_bundle")
    if source.get("profile_version") != HYBRID_OUTPUT_CONTRACT_PROFILE_VERSION:
        raise ValueError("unsupported Hybrid Output Contract profile")
    target_scope = _text(source.get("target_scope"), "candidate target_scope")
    _validated_bundle_digest(source, "hybrid_output_contract_digest", "Hybrid Output Contract")

    ordinary = _list(source.get("children"), "HOC children")
    audit = _list(source.get("audit_only_children"), "HOC audit_only_children")
    children = {}
    ordinary_ids = set()
    audit_ids = set()
    for raw, collection in ((row, "ordinary") for row in ordinary):
        row = _mapping(raw, "HOC ordinary child")
        identity = _child_identity(row, "HOC ordinary child")
        child_id = identity["child_claim_id"]
        if child_id in children:
            raise ValueError("HOC child IDs must be unique across ordinary/audit collections")
        decision = row.get("authority_decision")
        if decision not in _RENDERABLE:
            raise ValueError("HOC ordinary child must carry render authority")
        specificity = row.get("authorized_specificity")
        if specificity not in _SPECIFICITY_ORDER:
            raise ValueError("HOC ordinary child specificity is unsupported")
        caveats = row.get("required_caveats")
        if not isinstance(caveats, list) or any(not isinstance(item, str) or not item for item in caveats):
            raise ValueError("HOC required_caveats must be a text list")
        relation = row.get("cross_system_relation")
        if not isinstance(relation, str) or not relation:
            raise ValueError("HOC ordinary child cross_system_relation must be non-empty text")
        children[child_id] = {
            **identity,
            "rendered": True,
            "specificity": specificity,
            "caveated": bool(caveats),
            "relation": relation,
        }
        ordinary_ids.add(child_id)

    for raw in audit:
        row = _mapping(raw, "HOC audit child")
        identity = _child_identity(row, "HOC audit child")
        child_id = identity["child_claim_id"]
        if child_id in children:
            raise ValueError("HOC child IDs must be unique across ordinary/audit collections")
        if row.get("authority_decision") != "abstain_child":
            raise ValueError("HOC audit child must be abstain_child")
        if row.get("authorized_specificity") is not None:
            raise ValueError("HOC audit child specificity must be null")
        caveats = row.get("required_caveats")
        if not isinstance(caveats, list) or any(not isinstance(item, str) or not item for item in caveats):
            raise ValueError("HOC audit required_caveats must be a text list")
        children[child_id] = {
            **identity,
            "rendered": False,
            "specificity": None,
            "caveated": False,
            "relation": row.get("cross_system_relation"),
        }
        audit_ids.add(child_id)

    if not children:
        raise ValueError("HOC must contain at least one child")

    rendered_ids = []
    for raw in _list(source.get("render_units"), "HOC render_units"):
        unit = _mapping(raw, "HOC render unit")
        members = _list(unit.get("member_child_claim_ids"), "render unit member_child_claim_ids")
        if not members:
            raise ValueError("HOC render unit must contain at least one child")
        for child_id in members:
            child_id = _text(child_id, "render unit child id")
            if child_id in rendered_ids:
                raise ValueError("HOC renderable child cannot be consumed twice")
            rendered_ids.append(child_id)
    rendered_set = set(rendered_ids)
    if rendered_set != ordinary_ids:
        raise ValueError("HOC render-unit membership must exactly equal ordinary child set")
    if rendered_set & audit_ids:
        raise ValueError("HOC audit child cannot appear in render units")

    return {
        "target_scope": target_scope,
        "children": children,
        "universe": sorted(
            [
                {
                    "child_claim_id": row["child_claim_id"],
                    "primary_domain": row["primary_domain"],
                    "event_family": row["event_family"],
                }
                for row in children.values()
            ],
            key=lambda row: row["child_claim_id"],
        ),
    }


def _empty_metrics() -> dict:
    return {field: 0 for field in _METRIC_FIELDS}


def _score_arm(*, arm: Mapping[str, object], outcomes: list[Mapping[str, object]]) -> dict:
    metrics = _empty_metrics()
    children = arm["children"]
    for outcome in outcomes:
        status = outcome["outcome_status"]
        if status == "indeterminate":
            continue
        child = children[outcome["child_claim_id"]]
        rendered = bool(child["rendered"])
        if status == "supported":
            if rendered:
                metrics["supported_child_hit_count"] += 1
            else:
                metrics["supported_child_miss_count"] += 1
        elif status == "unsupported":
            if rendered:
                metrics["unsupported_child_render_count"] += 1
        else:
            raise ValueError("oracle outcome_status is unsupported")

        if not rendered:
            continue

        maximum = outcome["maximum_supported_specificity"]
        if status == "supported":
            if maximum not in _SPECIFICITY_ORDER:
                raise ValueError("supported oracle child has unsupported maximum specificity")
            actual = child["specificity"]
            if actual not in _SPECIFICITY_ORDER:
                raise ValueError("rendered child has unsupported specificity")
            if _SPECIFICITY_ORDER[actual] > _SPECIFICITY_ORDER[maximum]:
                metrics["specificity_overreach_count"] += 1

        if bool(child["caveated"]) != bool(outcome["caveat_required"]):
            metrics["caveat_error_count"] += 1

        relation = child["relation"]
        if (
            relation in {"direct_convergence", "direct_convergence_projection"}
            and outcome["expected_cross_system_relation"] != "direct_convergence"
        ):
            metrics["false_convergence_count"] += 1
    return metrics


def _research_label(legacy: Mapping[str, int], candidate: Mapping[str, int]) -> str:
    comparisons = [
        candidate["supported_child_hit_count"] >= legacy["supported_child_hit_count"],
        candidate["unsupported_child_render_count"] <= legacy["unsupported_child_render_count"],
        candidate["specificity_overreach_count"] <= legacy["specificity_overreach_count"],
        candidate["caveat_error_count"] <= legacy["caveat_error_count"],
        candidate["false_convergence_count"] <= legacy["false_convergence_count"],
    ]
    strict_better = [
        candidate["supported_child_hit_count"] > legacy["supported_child_hit_count"],
        candidate["unsupported_child_render_count"] < legacy["unsupported_child_render_count"],
        candidate["specificity_overreach_count"] < legacy["specificity_overreach_count"],
        candidate["caveat_error_count"] < legacy["caveat_error_count"],
        candidate["false_convergence_count"] < legacy["false_convergence_count"],
    ]
    worse = [
        candidate["supported_child_hit_count"] < legacy["supported_child_hit_count"],
        candidate["unsupported_child_render_count"] > legacy["unsupported_child_render_count"],
        candidate["specificity_overreach_count"] > legacy["specificity_overreach_count"],
        candidate["caveat_error_count"] > legacy["caveat_error_count"],
        candidate["false_convergence_count"] > legacy["false_convergence_count"],
    ]
    if all(comparisons) and any(strict_better):
        return "PARETO_IMPROVEMENT_EVIDENCE"
    if all(comparisons):
        return "NON_INFERIOR_NO_STRICT_GAIN"
    if any(strict_better) and any(worse):
        return "TRADEOFF"
    return "REGRESSION"


def evaluate_event_family_paired_comparison(payload: object) -> dict:
    """Evaluate both frozen arms against one sealed structured oracle."""

    root = _mapping(payload, "paired evaluation input")
    _exact_fields(root, _ROOT_FIELDS, "paired evaluation input")
    if root["schema_version"] != PAIRED_INPUT_SCHEMA:
        raise ValueError("unsupported paired evaluation input schema")
    classification = _text(root["classification"], "classification")
    cases = _list(root["cases"], "paired evaluation cases")
    if not cases:
        raise ValueError("paired evaluation must contain at least one case")

    normalized_cases = []
    case_ids = set()
    shared_universe = None
    for raw in cases:
        case = _mapping(raw, "paired evaluation case")
        _exact_fields(case, _CASE_FIELDS, "paired evaluation case")
        case_id = _text(case["case_id"], "case_id")
        if case_id in case_ids:
            raise ValueError("paired evaluation case_id values must be unique")
        case_ids.add(case_id)
        supplied_input_digest = _sha256(case["input_digest"], "input_digest")
        body = {
            "case_id": case_id,
            "legacy_adapter_bundle": case["legacy_adapter_bundle"],
            "candidate_hoc_bundle": case["candidate_hoc_bundle"],
        }
        if _digest(body) != supplied_input_digest:
            raise ValueError("input_digest does not match paired case payload")

        legacy = _validated_legacy(case["legacy_adapter_bundle"])
        candidate = _validated_candidate(case["candidate_hoc_bundle"])
        if legacy["target_scope"] != candidate["target_scope"]:
            raise ValueError("Legacy and Candidate target_scope must match")
        if legacy["universe"] != candidate["universe"]:
            raise ValueError("Legacy and Candidate child universes must exactly match")
        if shared_universe is None:
            shared_universe = legacy["universe"]
        elif legacy["universe"] != shared_universe:
            raise ValueError("all paired cases must use the same frozen child universe")
        normalized_cases.append(
            {
                "case_id": case_id,
                "input_digest": supplied_input_digest,
                "target_scope": legacy["target_scope"],
                "legacy": legacy,
                "candidate": candidate,
            }
        )

    assert shared_universe is not None
    verified_receipt = verify_event_family_paired_oracle(
        oracle=root["oracle"],
        seal_receipt=root["oracle_seal_receipt"],
        shared_child_universe=shared_universe,
    )
    if verified_receipt["classification"] != classification:
        raise ValueError("paired evaluation classification must match sealed oracle")

    oracle = _mapping(root["oracle"], "oracle")
    oracle_cases = _list(oracle.get("cases"), "oracle cases")
    oracle_index = {}
    for raw in oracle_cases:
        oracle_case = _mapping(raw, "oracle case")
        oracle_case_id = _text(oracle_case.get("case_id"), "oracle case_id")
        if oracle_case_id in oracle_index:
            raise ValueError("oracle case_id values must be unique")
        oracle_index[oracle_case_id] = oracle_case
    if set(oracle_index) != case_ids:
        raise ValueError("paired and oracle case_id sets must exactly match")

    legacy_total = _empty_metrics()
    candidate_total = _empty_metrics()
    scored_child_count = 0
    indeterminate_child_count = 0

    for case in sorted(normalized_cases, key=lambda row: row["case_id"]):
        oracle_case = oracle_index[case["case_id"]]
        if oracle_case.get("target_scope") != case["target_scope"]:
            raise ValueError("paired case target_scope must match oracle")
        outcomes = _list(oracle_case.get("child_outcomes"), "oracle child_outcomes")
        outcome_identity = sorted(
            [
                {
                    "child_claim_id": _text(row.get("child_claim_id"), "oracle child_claim_id"),
                    "primary_domain": _text(row.get("primary_domain"), "oracle primary_domain"),
                    "event_family": _text(row.get("event_family"), "oracle event_family"),
                }
                for row in outcomes
            ],
            key=lambda row: row["child_claim_id"],
        )
        if outcome_identity != shared_universe:
            raise ValueError("oracle child universe must exactly match paired arms")
        scored_child_count += sum(1 for row in outcomes if row.get("outcome_status") != "indeterminate")
        indeterminate_child_count += sum(1 for row in outcomes if row.get("outcome_status") == "indeterminate")

        legacy_metrics = _score_arm(arm=case["legacy"], outcomes=outcomes)
        candidate_metrics = _score_arm(arm=case["candidate"], outcomes=outcomes)
        for field in _METRIC_FIELDS:
            legacy_total[field] += legacy_metrics[field]
            candidate_total[field] += candidate_metrics[field]

    report = {
        "schema_version": PAIRED_REPORT_SCHEMA,
        "classification": classification,
        "case_count": len(normalized_cases),
        "scored_child_count": scored_child_count,
        "indeterminate_child_count": indeterminate_child_count,
        "legacy_metrics": legacy_total,
        "candidate_metrics": candidate_total,
        "research_label": _research_label(legacy_total, candidate_total),
        "input_set_digest": _digest(
            sorted(case["input_digest"] for case in normalized_cases)
        ),
        "oracle_digest": verified_receipt["oracle_digest"],
        "promotion_allowed": False,
    }
    report["report_digest"] = _digest(report)
    return report
