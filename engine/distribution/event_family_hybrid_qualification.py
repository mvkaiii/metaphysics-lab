from __future__ import annotations

import copy
import hashlib
import json
from typing import Mapping

INPUT_SCHEMA = "v1.6-event-family-hybrid-qualification-input.v1"
REPORT_SCHEMA = "v1.6-event-family-hybrid-qualification-report.v1"

EFA_PROFILE_VERSION = "lin_tianji_event_family_attribution_v1-exp"
C2_PROFILE_VERSION = "lin_tianji_hierarchical_claim_authority_v1-exp"
HCC_PROFILE_VERSION = "lin_tianji_hybrid_claim_composer_v1-exp"
HOC_PROFILE_VERSION = "lin_tianji_hybrid_output_contract_v1-exp"

NEGATIVE_COUNTER_FIELDS = (
    "supported_child_miss_count",
    "unsupported_child_open_count",
    "role_scope_attribution_error_count",
    "provenance_loss_count",
    "over_render_count",
    "under_render_count",
    "specificity_overreach_count",
    "specificity_excessive_downgrade_count",
    "caveat_omission_count",
    "unnecessary_caveat_count",
    "false_convergence_count",
    "missed_convergence_count",
    "parallel_group_error_count",
    "divergence_erasure_count",
    "false_divergence_count",
    "false_absence_penalty_count",
    "visibility_loss_count",
    "unauthorized_render_unit_count",
    "audit_leak_count",
    "manifest_specificity_overreach_count",
    "required_caveat_manifest_omission_count",
    "unsupported_causality_authority_count",
    "identity_mismatch_count",
    "source_digest_failure_count",
    "determinism_failure_count",
    "cutoff_contamination_count",
)

_CLASSIFICATIONS = frozenset(("synthetic_validation", "private_external_evaluation"))
_AUTHORIZATIONS = frozenset(("render", "render_with_caveat", "abstain_child"))
_RELATIONS = frozenset((
    "direct_convergence",
    "single_system_qualified",
    "layered_complement",
    "divergence",
    "no_direct_target_support",
))
_VISIBILITIES = frozenset(("primary", "secondary", "audit_only"))
_SPECIFICITY_ORDER = {"domain": 0, "event_family": 1, "concrete_event": 2}

_TOP_FIELDS = frozenset(("schema_version", "classification", "cases"))
_CASE_FIELDS = frozenset((
    "case_id",
    "efa_bundle",
    "c2_bundle",
    "hcc_bundle",
    "hoc_bundle",
    "child_expectations",
    "composition_expectations",
    "absence_policy_cases",
    "determinism_receipt",
    "cutoff_contamination",
    "input_digest",
))
_EFA_FIELDS = frozenset((
    "profile_version", "target_scope", "base_ranking_digest",
    "structural_interpretation_digest", "children", "event_family_attribution_digest",
))
_EFA_CHILD_FIELDS = frozenset((
    "child_claim_id", "parent_claim_id", "primary_domain", "event_family", "target_scope",
    "candidate_source", "child_opened", "bazi_target_feature_ids", "ziwei_target_feature_ids",
    "modifier_feature_ids", "timing_trigger_feature_ids", "direct_target_dependency_families",
    "direct_target_systems", "maturity_summary", "qualification_summary",
    "required_verification_caveat", "family_specificity_ceiling", "source_ranking_digest",
    "source_structural_interpretation_digest",
))
_C2_FIELDS = frozenset((
    "profile_version", "target_scope", "claim_evidence_digest", "claim_consumption_digest",
    "event_family_attribution_digest", "decisions", "hierarchical_claim_authority_digest",
))
_C2_DECISION_FIELDS = frozenset((
    "child_claim_id", "parent_claim_id", "primary_domain", "event_family", "decision",
    "parent_decision", "parent_authorized_specificity", "family_specificity_ceiling",
    "authorized_specificity", "source_systems", "reason_codes",
))
_HCC_FIELDS = frozenset((
    "profile_version", "target_scope", "hierarchical_claim_authority_digest",
    "event_family_attribution_digest", "source_interpretation_contract_digest",
    "source_claim_evidence_digest", "children", "composition_groups",
    "hybrid_claim_composer_digest",
))
_HCC_CHILD_FIELDS = frozenset((
    "child_claim_id", "parent_claim_id", "primary_domain", "event_family",
    "authority_decision", "authorized_specificity", "source_systems",
    "cross_system_relation", "visibility", "required_caveats",
))
_HCC_GROUP_FIELDS = frozenset(("composition_type", "primary_domain", "member_child_claim_ids"))
_HOC_FIELDS = frozenset((
    "profile_version", "target_scope", "source_hybrid_claim_composer_digest",
    "render_units", "children", "audit_only_children", "hybrid_output_contract_digest",
))
_RENDER_UNIT_FIELDS = frozenset((
    "render_unit_id", "member_child_claim_ids", "primary_domain", "target_scope",
    "composition_type", "cross_system_relations", "visibility", "authorized_specificity",
    "required_caveats", "causality_allowed", "source_efa_digest", "source_c2_digest",
    "source_hcc_digest",
))
_EXPECTATION_FIELDS = frozenset((
    "child_claim_id", "expected_opened", "expected_direct_target_systems",
    "expected_direct_target_dependency_families", "expected_authorization",
    "minimum_acceptable_specificity", "maximum_specificity", "caveat_required",
    "expected_cross_system_relation", "expected_visibility", "expected_in_render_manifest",
))
_COMPOSITION_EXPECTATION_FIELDS = frozenset((
    "composition_type", "member_child_claim_ids", "expected_manifest_presence",
))
_ABSENCE_FIELDS = frozenset((
    "child_claim_id", "materialized_system", "missing_system", "expected_authorization",
    "expected_relation",
))
_RECEIPT_FIELDS = frozenset((
    "source_identity_digest",
    "first_efa_digest", "second_efa_digest",
    "first_c2_digest", "second_c2_digest",
    "first_hcc_digest", "second_hcc_digest",
    "first_hoc_digest", "second_hoc_digest",
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
        raise ValueError("Q2 input must be canonical JSON") from exc


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


def _sha256_text(value: object, label: str) -> str:
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


def _text_list(value: object, label: str) -> list:
    rows = _list(value, label)
    if any(not isinstance(item, str) or not item for item in rows):
        raise ValueError(f"{label} must contain non-empty text")
    if len(rows) != len(set(rows)):
        raise ValueError(f"{label} values must be unique")
    return rows


def _nullable_specificity(value: object, label: str):
    if value is None:
        return None
    if value not in _SPECIFICITY_ORDER:
        raise ValueError(f"{label} contains unsupported specificity")
    return str(value)


def _validate_efa_child(raw: object) -> None:
    row = _mapping(raw, "EFA child")
    _exact_fields(row, _EFA_CHILD_FIELDS, "EFA child")
    for field in ("child_claim_id", "parent_claim_id", "primary_domain", "event_family", "target_scope", "candidate_source"):
        _text(row[field], f"EFA child.{field}")
    _bool(row["child_opened"], "EFA child.child_opened")
    for field in (
        "bazi_target_feature_ids", "ziwei_target_feature_ids", "modifier_feature_ids",
        "timing_trigger_feature_ids", "direct_target_dependency_families", "direct_target_systems",
        "maturity_summary", "qualification_summary",
    ):
        _text_list(row[field], f"EFA child.{field}")
    _bool(row["required_verification_caveat"], "EFA child.required_verification_caveat")
    _nullable_specificity(row["family_specificity_ceiling"], "EFA child.family_specificity_ceiling")
    _sha256_text(row["source_ranking_digest"], "EFA child.source_ranking_digest")
    _sha256_text(row["source_structural_interpretation_digest"], "EFA child.source_structural_interpretation_digest")


def _validate_efa(raw: object) -> None:
    bundle = _mapping(raw, "efa_bundle")
    _exact_fields(bundle, _EFA_FIELDS, "efa_bundle")
    if bundle["profile_version"] != EFA_PROFILE_VERSION:
        raise ValueError("efa_bundle profile_version is unsupported")
    _text(bundle["target_scope"], "efa_bundle.target_scope")
    _sha256_text(bundle["base_ranking_digest"], "efa_bundle.base_ranking_digest")
    _sha256_text(bundle["structural_interpretation_digest"], "efa_bundle.structural_interpretation_digest")
    _sha256_text(bundle["event_family_attribution_digest"], "efa_bundle.event_family_attribution_digest")
    children = _list(bundle["children"], "efa_bundle.children")
    for row in children:
        _validate_efa_child(row)
    ids = [row["child_claim_id"] for row in children]
    if len(ids) != len(set(ids)):
        raise ValueError("efa_bundle child_claim_id values must be unique")


def _validate_c2_decision(raw: object) -> None:
    row = _mapping(raw, "C2 decision")
    _exact_fields(row, _C2_DECISION_FIELDS, "C2 decision")
    for field in ("child_claim_id", "parent_claim_id", "primary_domain", "event_family", "parent_decision"):
        _text(row[field], f"C2 decision.{field}")
    if row["decision"] not in _AUTHORIZATIONS:
        raise ValueError("C2 decision.decision contains unsupported authorization")
    _nullable_specificity(row["parent_authorized_specificity"], "C2 decision.parent_authorized_specificity")
    _nullable_specificity(row["family_specificity_ceiling"], "C2 decision.family_specificity_ceiling")
    _nullable_specificity(row["authorized_specificity"], "C2 decision.authorized_specificity")
    _text_list(row["source_systems"], "C2 decision.source_systems")
    _text_list(row["reason_codes"], "C2 decision.reason_codes")


def _validate_c2(raw: object) -> None:
    bundle = _mapping(raw, "c2_bundle")
    _exact_fields(bundle, _C2_FIELDS, "c2_bundle")
    if bundle["profile_version"] != C2_PROFILE_VERSION:
        raise ValueError("c2_bundle profile_version is unsupported")
    _text(bundle["target_scope"], "c2_bundle.target_scope")
    for field in ("claim_evidence_digest", "claim_consumption_digest", "event_family_attribution_digest", "hierarchical_claim_authority_digest"):
        _sha256_text(bundle[field], f"c2_bundle.{field}")
    decisions = _list(bundle["decisions"], "c2_bundle.decisions")
    for row in decisions:
        _validate_c2_decision(row)
    ids = [row["child_claim_id"] for row in decisions]
    if len(ids) != len(set(ids)):
        raise ValueError("c2_bundle child_claim_id values must be unique")


def _validate_hcc_child(raw: object) -> None:
    row = _mapping(raw, "HCC child")
    _exact_fields(row, _HCC_CHILD_FIELDS, "HCC child")
    for field in ("child_claim_id", "parent_claim_id", "primary_domain", "event_family"):
        _text(row[field], f"HCC child.{field}")
    if row["authority_decision"] not in _AUTHORIZATIONS:
        raise ValueError("HCC child authority_decision is unsupported")
    _nullable_specificity(row["authorized_specificity"], "HCC child.authorized_specificity")
    _text_list(row["source_systems"], "HCC child.source_systems")
    if row["cross_system_relation"] not in _RELATIONS:
        raise ValueError("HCC child cross_system_relation is unsupported")
    if row["visibility"] not in _VISIBILITIES:
        raise ValueError("HCC child visibility is unsupported")
    _text_list(row["required_caveats"], "HCC child.required_caveats")


def _validate_hcc(raw: object) -> None:
    bundle = _mapping(raw, "hcc_bundle")
    _exact_fields(bundle, _HCC_FIELDS, "hcc_bundle")
    if bundle["profile_version"] != HCC_PROFILE_VERSION:
        raise ValueError("hcc_bundle profile_version is unsupported")
    _text(bundle["target_scope"], "hcc_bundle.target_scope")
    for field in (
        "hierarchical_claim_authority_digest", "event_family_attribution_digest",
        "source_interpretation_contract_digest", "source_claim_evidence_digest",
        "hybrid_claim_composer_digest",
    ):
        _sha256_text(bundle[field], f"hcc_bundle.{field}")
    children = _list(bundle["children"], "hcc_bundle.children")
    for row in children:
        _validate_hcc_child(row)
    ids = [row["child_claim_id"] for row in children]
    if len(ids) != len(set(ids)):
        raise ValueError("hcc_bundle child_claim_id values must be unique")
    for raw_group in _list(bundle["composition_groups"], "hcc_bundle.composition_groups"):
        group = _mapping(raw_group, "HCC composition group")
        _exact_fields(group, _HCC_GROUP_FIELDS, "HCC composition group")
        _text(group["composition_type"], "HCC composition group.composition_type")
        _text(group["primary_domain"], "HCC composition group.primary_domain")
        _text_list(group["member_child_claim_ids"], "HCC composition group.member_child_claim_ids")


def _validate_render_unit(raw: object) -> None:
    row = _mapping(raw, "HOC render unit")
    _exact_fields(row, _RENDER_UNIT_FIELDS, "HOC render unit")
    for field in ("render_unit_id", "primary_domain", "target_scope", "composition_type"):
        _text(row[field], f"HOC render unit.{field}")
    _text_list(row["member_child_claim_ids"], "HOC render unit.member_child_claim_ids")
    _text_list(row["cross_system_relations"], "HOC render unit.cross_system_relations")
    if row["visibility"] not in _VISIBILITIES:
        raise ValueError("HOC render unit visibility is unsupported")
    _nullable_specificity(row["authorized_specificity"], "HOC render unit.authorized_specificity")
    _text_list(row["required_caveats"], "HOC render unit.required_caveats")
    _bool(row["causality_allowed"], "HOC render unit.causality_allowed")
    for field in ("source_efa_digest", "source_c2_digest", "source_hcc_digest"):
        _sha256_text(row[field], f"HOC render unit.{field}")


def _validate_hoc(raw: object) -> None:
    bundle = _mapping(raw, "hoc_bundle")
    _exact_fields(bundle, _HOC_FIELDS, "hoc_bundle")
    if bundle["profile_version"] != HOC_PROFILE_VERSION:
        raise ValueError("hoc_bundle profile_version is unsupported")
    _text(bundle["target_scope"], "hoc_bundle.target_scope")
    _sha256_text(bundle["source_hybrid_claim_composer_digest"], "hoc_bundle.source_hybrid_claim_composer_digest")
    _sha256_text(bundle["hybrid_output_contract_digest"], "hoc_bundle.hybrid_output_contract_digest")
    for row in _list(bundle["render_units"], "hoc_bundle.render_units"):
        _validate_render_unit(row)
    for field in ("children", "audit_only_children"):
        rows = _list(bundle[field], f"hoc_bundle.{field}")
        for row in rows:
            _validate_hcc_child(row)
        ids = [row["child_claim_id"] for row in rows]
        if len(ids) != len(set(ids)):
            raise ValueError(f"hoc_bundle.{field} child_claim_id values must be unique")


def _validate_expectation(raw: object) -> None:
    row = _mapping(raw, "child expectation")
    _exact_fields(row, _EXPECTATION_FIELDS, "child expectation")
    _text(row["child_claim_id"], "child expectation.child_claim_id")
    _bool(row["expected_opened"], "child expectation.expected_opened")
    _text_list(row["expected_direct_target_systems"], "child expectation.expected_direct_target_systems")
    _text_list(row["expected_direct_target_dependency_families"], "child expectation.expected_direct_target_dependency_families")
    if row["expected_authorization"] not in _AUTHORIZATIONS:
        raise ValueError("child expectation expected_authorization is unsupported")
    minimum = _nullable_specificity(row["minimum_acceptable_specificity"], "child expectation.minimum_acceptable_specificity")
    maximum = _nullable_specificity(row["maximum_specificity"], "child expectation.maximum_specificity")
    if minimum is not None and maximum is not None and _SPECIFICITY_ORDER[minimum] > _SPECIFICITY_ORDER[maximum]:
        raise ValueError("minimum_acceptable_specificity cannot exceed maximum_specificity")
    _bool(row["caveat_required"], "child expectation.caveat_required")
    relation = row["expected_cross_system_relation"]
    if relation is not None and relation not in _RELATIONS:
        raise ValueError("child expectation expected_cross_system_relation is unsupported")
    if row["expected_visibility"] not in _VISIBILITIES:
        raise ValueError("child expectation expected_visibility is unsupported")
    _bool(row["expected_in_render_manifest"], "child expectation.expected_in_render_manifest")


def _validate_case(raw: object) -> None:
    case = _mapping(raw, "Q2 case")
    _exact_fields(case, _CASE_FIELDS, "Q2 case")
    _text(case["case_id"], "Q2 case.case_id")
    _validate_efa(case["efa_bundle"])
    _validate_c2(case["c2_bundle"])
    _validate_hcc(case["hcc_bundle"])
    _validate_hoc(case["hoc_bundle"])
    expectations = _list(case["child_expectations"], "Q2 case.child_expectations")
    for row in expectations:
        _validate_expectation(row)
    expectation_ids = [row["child_claim_id"] for row in expectations]
    if len(expectation_ids) != len(set(expectation_ids)):
        raise ValueError("child expectation child_claim_id values must be unique")
    for raw_row in _list(case["composition_expectations"], "Q2 case.composition_expectations"):
        row = _mapping(raw_row, "composition expectation")
        _exact_fields(row, _COMPOSITION_EXPECTATION_FIELDS, "composition expectation")
        _text(row["composition_type"], "composition expectation.composition_type")
        _text_list(row["member_child_claim_ids"], "composition expectation.member_child_claim_ids")
        _bool(row["expected_manifest_presence"], "composition expectation.expected_manifest_presence")
    for raw_row in _list(case["absence_policy_cases"], "Q2 case.absence_policy_cases"):
        row = _mapping(raw_row, "absence policy case")
        _exact_fields(row, _ABSENCE_FIELDS, "absence policy case")
        _text(row["child_claim_id"], "absence policy case.child_claim_id")
        _text(row["materialized_system"], "absence policy case.materialized_system")
        _text(row["missing_system"], "absence policy case.missing_system")
        if row["expected_authorization"] not in _AUTHORIZATIONS:
            raise ValueError("absence policy expected_authorization is unsupported")
        if row["expected_relation"] not in _RELATIONS:
            raise ValueError("absence policy expected_relation is unsupported")
    receipt = _mapping(case["determinism_receipt"], "Q2 case.determinism_receipt")
    _exact_fields(receipt, _RECEIPT_FIELDS, "Q2 case.determinism_receipt")
    for field in _RECEIPT_FIELDS:
        _sha256_text(receipt[field], f"Q2 case.determinism_receipt.{field}")
    _bool(case["cutoff_contamination"], "Q2 case.cutoff_contamination")
    supplied = _sha256_text(case["input_digest"], "Q2 case.input_digest")
    body = copy.deepcopy(dict(case))
    body.pop("input_digest", None)
    if supplied != _digest(body):
        raise ValueError("input_digest does not match Q2 case payload")


def validate_event_family_hybrid_qualification_input(payload: object) -> dict:
    root = _mapping(payload, "Q2 qualification input")
    _exact_fields(root, _TOP_FIELDS, "Q2 qualification input")
    if root["schema_version"] != INPUT_SCHEMA:
        raise ValueError("unsupported Q2 qualification input schema_version")
    if root["classification"] not in _CLASSIFICATIONS:
        raise ValueError("unsupported Q2 qualification classification")
    cases = _list(root["cases"], "Q2 qualification input.cases")
    if not cases:
        raise ValueError("Q2 qualification input.cases must not be empty")
    for case in cases:
        _validate_case(case)
    case_ids = [case["case_id"] for case in cases]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("Q2 case_id values must be unique")
    return copy.deepcopy(dict(root))


def _self_digest_ok(bundle: Mapping[str, object], digest_field: str) -> bool:
    body = copy.deepcopy(dict(bundle))
    supplied = body.pop(digest_field, None)
    return isinstance(supplied, str) and supplied == _digest(body)


def _index(rows: list, label: str) -> dict:
    result = {}
    for row in rows:
        child_id = row["child_claim_id"]
        if child_id in result:
            raise ValueError(f"duplicate {label} child_claim_id")
        result[child_id] = row
    return result


def _render_membership(render_units: list) -> dict:
    membership = {}
    for unit in render_units:
        for child_id in unit["member_child_claim_ids"]:
            membership.setdefault(child_id, []).append(unit)
    return membership


def _specificity_compare(actual, bound) -> int:
    if actual is None or bound is None:
        return 0
    return _SPECIFICITY_ORDER[actual] - _SPECIFICITY_ORDER[bound]


def _all_zero(counters: Mapping[str, int]) -> bool:
    return all(counters[field] == 0 for field in NEGATIVE_COUNTER_FIELDS)


def evaluate_event_family_hybrid_qualification(payload: object) -> dict:
    validated = validate_event_family_hybrid_qualification_input(payload)
    counters = {field: 0 for field in NEGATIVE_COUNTER_FIELDS}
    alignment = {"matched": 0, "partial": 0, "missed": 0}
    child_count = 0

    for case in validated["cases"]:
        efa = case["efa_bundle"]
        c2 = case["c2_bundle"]
        hcc = case["hcc_bundle"]
        hoc = case["hoc_bundle"]

        source_failures = 0
        source_failures += int(not _self_digest_ok(efa, "event_family_attribution_digest"))
        source_failures += int(not _self_digest_ok(c2, "hierarchical_claim_authority_digest"))
        source_failures += int(not _self_digest_ok(hcc, "hybrid_claim_composer_digest"))
        source_failures += int(not _self_digest_ok(hoc, "hybrid_output_contract_digest"))
        counters["source_digest_failure_count"] += source_failures

        identity_failures = 0
        identity_failures += int(c2["event_family_attribution_digest"] != efa["event_family_attribution_digest"])
        identity_failures += int(hcc["event_family_attribution_digest"] != efa["event_family_attribution_digest"])
        identity_failures += int(hcc["hierarchical_claim_authority_digest"] != c2["hierarchical_claim_authority_digest"])
        identity_failures += int(hoc["source_hybrid_claim_composer_digest"] != hcc["hybrid_claim_composer_digest"])
        for unit in hoc["render_units"]:
            identity_failures += int(unit["source_efa_digest"] != efa["event_family_attribution_digest"])
            identity_failures += int(unit["source_c2_digest"] != c2["hierarchical_claim_authority_digest"])
            identity_failures += int(unit["source_hcc_digest"] != hcc["hybrid_claim_composer_digest"])
        counters["identity_mismatch_count"] += identity_failures

        receipt = case["determinism_receipt"]
        actual_pairs = (
            ("efa", efa["event_family_attribution_digest"]),
            ("c2", c2["hierarchical_claim_authority_digest"]),
            ("hcc", hcc["hybrid_claim_composer_digest"]),
            ("hoc", hoc["hybrid_output_contract_digest"]),
        )
        for prefix, actual_digest in actual_pairs:
            first = receipt[f"first_{prefix}_digest"]
            second = receipt[f"second_{prefix}_digest"]
            if first != second or first != actual_digest:
                counters["determinism_failure_count"] += 1

        if case["cutoff_contamination"]:
            counters["cutoff_contamination_count"] += 1

        efa_by_id = _index(efa["children"], "EFA")
        c2_by_id = _index(c2["decisions"], "C2")
        hcc_by_id = _index(hcc["children"], "HCC")
        ordinary_by_id = _index(hoc["children"], "HOC ordinary")
        audit_by_id = _index(hoc["audit_only_children"], "HOC audit")
        membership = _render_membership(hoc["render_units"])

        for audit_id in audit_by_id:
            if audit_id in membership:
                counters["audit_leak_count"] += 1

        for unit in hoc["render_units"]:
            if unit["causality_allowed"] is True:
                counters["unsupported_causality_authority_count"] += 1
            member_rows = [hcc_by_id.get(child_id) for child_id in unit["member_child_claim_ids"]]
            member_rows = [row for row in member_rows if row is not None]
            if member_rows:
                specificity_values = [row["authorized_specificity"] for row in member_rows if row["authorized_specificity"] is not None]
                if specificity_values:
                    conservative = min(specificity_values, key=lambda value: _SPECIFICITY_ORDER[value])
                    if _specificity_compare(unit["authorized_specificity"], conservative) > 0:
                        counters["manifest_specificity_overreach_count"] += 1
                required = []
                for row in member_rows:
                    for caveat in row["required_caveats"]:
                        if caveat not in required:
                            required.append(caveat)
                if any(caveat not in unit["required_caveats"] for caveat in required):
                    counters["required_caveat_manifest_omission_count"] += 1

        for expected in case["child_expectations"]:
            child_count += 1
            child_id = expected["child_claim_id"]
            efa_row = efa_by_id.get(child_id)
            c2_row = c2_by_id.get(child_id)
            hcc_row = hcc_by_id.get(child_id)
            hard_error = False
            partial_error = False

            actual_opened = bool(efa_row and efa_row["child_opened"])
            if expected["expected_opened"] and not actual_opened:
                counters["supported_child_miss_count"] += 1
                hard_error = True
            if not expected["expected_opened"] and actual_opened:
                counters["unsupported_child_open_count"] += 1
                hard_error = True

            if efa_row is None:
                counters["provenance_loss_count"] += 1
                hard_error = True
            else:
                if set(efa_row["direct_target_systems"]) != set(expected["expected_direct_target_systems"]):
                    counters["role_scope_attribution_error_count"] += 1
                    hard_error = True
                if set(efa_row["direct_target_dependency_families"]) != set(expected["expected_direct_target_dependency_families"]):
                    counters["provenance_loss_count"] += 1
                    hard_error = True

            actual_auth = c2_row["decision"] if c2_row else "abstain_child"
            expected_auth = expected["expected_authorization"]
            actual_renderable = actual_auth in {"render", "render_with_caveat"}
            expected_renderable = expected_auth in {"render", "render_with_caveat"}
            if expected_renderable and not actual_renderable:
                counters["under_render_count"] += 1
                hard_error = True
            if not expected_renderable and actual_renderable:
                counters["over_render_count"] += 1
                hard_error = True

            if expected_renderable and actual_renderable and c2_row is not None:
                actual_specificity = c2_row["authorized_specificity"]
                if _specificity_compare(actual_specificity, expected["maximum_specificity"]) > 0:
                    counters["specificity_overreach_count"] += 1
                    hard_error = True
                if _specificity_compare(actual_specificity, expected["minimum_acceptable_specificity"]) < 0:
                    counters["specificity_excessive_downgrade_count"] += 1
                    hard_error = True

                actual_caveat = actual_auth == "render_with_caveat"
                if expected["caveat_required"] and not actual_caveat:
                    counters["caveat_omission_count"] += 1
                    partial_error = True
                if not expected["caveat_required"] and expected_auth == "render" and actual_caveat:
                    counters["unnecessary_caveat_count"] += 1
                    partial_error = True

            expected_relation = expected["expected_cross_system_relation"]
            actual_relation = hcc_row["cross_system_relation"] if hcc_row else None
            if expected_relation is not None:
                if expected_relation == "direct_convergence" and actual_relation != "direct_convergence":
                    counters["missed_convergence_count"] += 1
                    partial_error = True
                elif expected_relation != "direct_convergence" and actual_relation == "direct_convergence":
                    counters["false_convergence_count"] += 1
                    partial_error = True
                if expected_relation == "divergence" and actual_relation != "divergence":
                    counters["divergence_erasure_count"] += 1
                    partial_error = True
                elif expected_relation != "divergence" and actual_relation == "divergence":
                    counters["false_divergence_count"] += 1
                    partial_error = True
                if expected_relation not in {"direct_convergence", "divergence"} and actual_relation not in {expected_relation, "direct_convergence", "divergence"}:
                    partial_error = True

            actual_visibility = hcc_row["visibility"] if hcc_row else None
            if actual_visibility != expected["expected_visibility"]:
                counters["visibility_loss_count"] += 1
                partial_error = True

            is_rendered = child_id in membership
            if expected["expected_in_render_manifest"] and not is_rendered:
                counters["under_render_count"] += 1
                hard_error = True
            if not expected["expected_in_render_manifest"] and is_rendered:
                counters["unauthorized_render_unit_count"] += 1
                hard_error = True

            if hard_error:
                alignment["missed"] += 1
            elif partial_error:
                alignment["partial"] += 1
            else:
                alignment["matched"] += 1

        actual_groups = hcc["composition_groups"]
        for expected_group in case["composition_expectations"]:
            expected_members = set(expected_group["member_child_claim_ids"])
            matched_group = any(
                group["composition_type"] == expected_group["composition_type"]
                and set(group["member_child_claim_ids"]) == expected_members
                for group in actual_groups
            )
            manifest_group = any(
                unit["composition_type"] == "parallel_sibling_group"
                and set(unit["member_child_claim_ids"]) == expected_members
                for unit in hoc["render_units"]
            )
            expected_manifest = expected_group["expected_manifest_presence"]
            if not matched_group or manifest_group != expected_manifest:
                counters["parallel_group_error_count"] += 1

        for absence in case["absence_policy_cases"]:
            child_id = absence["child_claim_id"]
            c2_row = c2_by_id.get(child_id)
            hcc_row = hcc_by_id.get(child_id)
            actual_auth = c2_row["decision"] if c2_row else "abstain_child"
            actual_relation = hcc_row["cross_system_relation"] if hcc_row else None
            if actual_auth != absence["expected_authorization"] or actual_relation != absence["expected_relation"]:
                counters["false_absence_penalty_count"] += 1

    input_identity = [
        {"case_id": case["case_id"], "input_digest": case["input_digest"]}
        for case in sorted(validated["cases"], key=lambda item: item["case_id"])
    ]
    status = "METRICS_ONLY"
    if validated["classification"] == "synthetic_validation":
        status = "PASS" if _all_zero(counters) and alignment["partial"] == 0 and alignment["missed"] == 0 else "FAIL"

    report = {
        "schema_version": REPORT_SCHEMA,
        "classification": validated["classification"],
        "case_count": len(validated["cases"]),
        "child_count": child_count,
        "decision_alignment": alignment,
        **counters,
        "input_set_digest": _digest(input_identity),
        "general_conformance_status": status,
        "promotion_allowed": False,
    }
    report["report_digest"] = _digest(report)
    return report
