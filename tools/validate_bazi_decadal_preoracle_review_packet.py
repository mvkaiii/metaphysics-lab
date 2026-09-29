"""Validate the Bazi decadal pre-oracle human/domain review packet.

This validator intentionally keeps the packet non-sealable while any declared
review or source-binding blocker remains. It does not calculate Bazi values.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
import math


_REQUIRED_BLOCKERS = {
    "DOMAIN_REVIEW_OF_WRITTEN_PROFILE",
    "EQUALITY_AT_JIE_RULE_UNRESOLVED",
    "ENDPOINT_GENERATION_RULE_UNRESOLVED",
    "SOURCE_PRECISION_SEMANTICS_UNRESOLVED",
    "EXACT_SOURCE_BYTES_SHA256_MISSING",
    "SPECIFICATION_SHA256_MISSING",
}


def _aware(value):
    if not isinstance(value, str):
        return False
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return False
    return dt.tzinfo is not None and dt.utcoffset() is not None


def validate_review_packet(payload):
    errors = []
    if not isinstance(payload, Mapping):
        return ["review_packet: expected object"]
    if payload.get("schema_version") != "1.0":
        errors.append("review_packet.schema_version")
    if payload.get("packet_type") != "bazi_decadal_preoracle_review_packet":
        errors.append("review_packet.packet_type")
    if payload.get("status") != "DRAFT_PENDING_DOMAIN_REVIEW":
        errors.append("review_packet.status")
    if payload.get("task3_status") != "NEEDS_EVIDENCE":
        errors.append("review_packet.task3_status")
    if payload.get("seal_allowed") is not False:
        errors.append("review_packet.seal_allowed")

    profile = payload.get("profile_candidate")
    if not isinstance(profile, Mapping):
        errors.append("review_packet.profile_candidate")
        profile = {}
    expected_profile = {
        "profile_id": "bazi-natal-project-v1",
        "rule_version": "1.0-exp",
        "decadal_rule": "three-days-one-year-v1",
        "age_basis": "continuous_years_from_jie_interval",
        "domain_review_status": "PENDING",
    }
    for key, expected in expected_profile.items():
        if profile.get(key) != expected:
            errors.append(f"review_packet.profile_candidate.{key}")
    if profile.get("specification_sha256") is not None:
        errors.append("review_packet.profile_candidate.specification_sha256: must remain null before review")

    source_plan = payload.get("external_source_plan")
    if not isinstance(source_plan, Mapping):
        errors.append("review_packet.external_source_plan")
        source_plan = {}
    if source_plan.get("provider") != "Hong Kong Observatory":
        errors.append("review_packet.external_source_plan.provider")
    if source_plan.get("provider_role") != "astronomical_input_only":
        errors.append("review_packet.external_source_plan.provider_role")
    sources = source_plan.get("sources")
    if not isinstance(sources, list) or [row.get("year") for row in sources if isinstance(row, Mapping)] != [2015, 2016]:
        errors.append("review_packet.external_source_plan.sources")
    else:
        for index, row in enumerate(sources):
            if row.get("source_bytes_sha256") is not None:
                errors.append(f"review_packet.external_source_plan.sources[{index}].source_bytes_sha256: must be null before capture")
            if row.get("source_bytes_status") != "NOT_YET_CAPTURED":
                errors.append(f"review_packet.external_source_plan.sources[{index}].source_bytes_status")

    selection = payload.get("case_selection")
    if not isinstance(selection, Mapping):
        errors.append("review_packet.case_selection")
        selection = {}
    if selection.get("production_results_consulted_for_selection") is not False:
        errors.append("review_packet.case_selection.production_results_consulted_for_selection")
    cases = selection.get("cases")
    if not isinstance(cases, list) or len(cases) != 12:
        errors.append("review_packet.case_selection.cases")
        cases = []
    ids = set()
    for index, case in enumerate(cases):
        if not isinstance(case, Mapping):
            errors.append(f"review_packet.case_selection.cases[{index}]")
            continue
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not case_id or case_id in ids:
            errors.append(f"review_packet.case_selection.cases[{index}].case_id")
        ids.add(case_id)
        if not _aware(case.get("birth_datetime")):
            errors.append(f"review_packet.case_selection.cases[{index}].birth_datetime")
        if case.get("sex") not in {"male", "female"}:
            errors.append(f"review_packet.case_selection.cases[{index}].sex")
        tags = case.get("coverage_tags")
        if not isinstance(tags, list) or not tags or len(tags) != len(set(tags)):
            errors.append(f"review_packet.case_selection.cases[{index}].coverage_tags")

    comparison = payload.get("comparison_plan")
    paths = comparison.get("paths") if isinstance(comparison, Mapping) else None
    if not isinstance(paths, list):
        errors.append("review_packet.comparison_plan.paths")
        paths = []
    by_path = {row.get("path"): row for row in paths if isinstance(row, Mapping)}
    expected_paths = {
        "/decadal_direction",
        "/periods/0/pillar",
        "/periods/0/start_age_years",
        "/periods/0/start_datetime",
        "/periods/1/end_datetime",
    }
    if set(by_path) != expected_paths:
        errors.append("review_packet.comparison_plan.paths.census")
    age = by_path.get("/periods/0/start_age_years", {})
    dt = by_path.get("/periods/0/start_datetime", {})
    if age.get("tolerance_status") != "PROPOSED_PENDING_DOMAIN_REVIEW":
        errors.append("review_packet.comparison_plan.start_age_years.status")
    if dt.get("tolerance_status") != "PROPOSED_PENDING_DOMAIN_REVIEW":
        errors.append("review_packet.comparison_plan.start_datetime.status")
    if not isinstance(age.get("proposed_tolerance"), (int, float)) or isinstance(age.get("proposed_tolerance"), bool) or not math.isfinite(age["proposed_tolerance"]):
        errors.append("review_packet.comparison_plan.start_age_years.tolerance")
    if not isinstance(dt.get("proposed_tolerance"), (int, float)) or isinstance(dt.get("proposed_tolerance"), bool) or not math.isfinite(dt["proposed_tolerance"]):
        errors.append("review_packet.comparison_plan.start_datetime.tolerance")

    blockers = payload.get("blocking_items")
    if not isinstance(blockers, list) or set(blockers) != _REQUIRED_BLOCKERS:
        errors.append("review_packet.blocking_items")

    boundary = payload.get("independence_boundary")
    if not isinstance(boundary, Mapping):
        errors.append("review_packet.independence_boundary")
        boundary = {}
    required_false = (
        "oracle_expected_values_present",
        "oracle_execution_started",
        "oracle_may_receive_production_code",
        "oracle_may_receive_production_output",
        "oracle_may_receive_comparison_results_before_seal",
    )
    for key in required_false:
        if boundary.get(key) is not False:
            errors.append(f"review_packet.independence_boundary.{key}")

    return sorted(set(errors))


def ready_for_preoracle_seal(payload):
    return False if validate_review_packet(payload) else (
        payload.get("seal_allowed") is True and not payload.get("blocking_items")
    )
