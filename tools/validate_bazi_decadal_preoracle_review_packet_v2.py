"""Validate the Bazi decadal Task 3 v2 pre-oracle review packet.

This validator is intentionally non-sealing.  It checks that the v2 proposal
is self-contained enough for human/domain review and that the case census does
not leak direction/year-polarity answers.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
import math
import re

_OPAQUE_ID = re.compile(r"^bdv2-\d{3}$")
_FORBIDDEN_TAG_FRAGMENTS = (
    "forward",
    "reverse",
    "yin_year",
    "yang_year",
    "expected",
    "pillar",
)
_ALLOWED_TAGS = {
    "common_year",
    "leap_year",
    "leap_day",
    "before_published_jie_minute",
    "after_published_jie_minute",
    "cross_gregorian_year_lookup",
    "paired_sex_input",
}
_REQUIRED_BLOCKERS = {
    "DOMAIN_REVIEW_OF_V2_WRITTEN_PROFILE",
    "DOMAIN_REVIEW_OF_ORACLE_SOURCE_AND_TOLERANCES",
    "DOMAIN_REVIEW_OF_EQUALITY_COVERAGE_GAP",
    "PRODUCTION_CANDIDATE_FREEZE_PENDING",
    "SPECIFICATION_SHA256_NOT_FROZEN",
    "V2_CASE_BUNDLE_NOT_SEALED",
}
_REQUIRED_DECISIONS = {
    "V2-D1_ACCEPT_HKO_2015_2016_AS_ORACLE_ASTRONOMICAL_SOURCE_WITH_60_SECOND_PUBLISHED_PRECISION",
    "V2-D2_ACCEPT_SELF_CONTAINED_YEAR_AND_MONTH_PILLAR_RULES",
    "V2-D3_ACCEPT_SAME_12_PRE_RESULT_INPUTS_WITH_OPAQUE_IDS_AND_NEUTRAL_METADATA",
    "V2-D4_ACCEPT_EXISTING_COMPARISON_PATHS_AND_FROZEN_TOLERANCES",
    "V2-D5_ACCEPT_EXACT_EQUALITY_AS_WRITTEN_RULE_WITH_DISCLOSED_INDEPENDENT_COVERAGE_GAP",
}


def _aware(value):
    if not isinstance(value, str):
        return False
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return False
    return dt.tzinfo is not None and dt.utcoffset() is not None


def validate_review_packet_v2(payload):
    errors = []
    if not isinstance(payload, Mapping):
        return ["review_packet_v2: expected object"]
    if payload.get("schema_version") != "2.0":
        errors.append("review_packet_v2.schema_version")
    if payload.get("packet_type") != "bazi_decadal_preoracle_review_packet":
        errors.append("review_packet_v2.packet_type")
    if payload.get("status") != "DRAFT_PENDING_DOMAIN_REVIEW":
        errors.append("review_packet_v2.status")
    if payload.get("task3_status") != "NEEDS_EVIDENCE":
        errors.append("review_packet_v2.task3_status")
    if payload.get("seal_allowed") is not False:
        errors.append("review_packet_v2.seal_allowed")

    profile = payload.get("profile_candidate")
    if not isinstance(profile, Mapping):
        errors.append("review_packet_v2.profile_candidate")
        profile = {}
    expected_profile = {
        "profile_id": "bazi-natal-project-v1",
        "rule_version": "1.0-exp",
        "decadal_rule": "three-days-one-year-v1",
        "age_basis": "continuous_years_from_jie_interval",
        "review_candidate_path": "docs/research/bazi-decadal-independent-profile-spec.v2.candidate.md",
        "domain_review_status": "PENDING",
        "specification_sha256": None,
    }
    for key, expected in expected_profile.items():
        if profile.get(key) != expected:
            errors.append(f"review_packet_v2.profile_candidate.{key}")

    production = payload.get("production_timing_evidence")
    if not isinstance(production, Mapping):
        errors.append("review_packet_v2.production_timing_evidence")
        production = {}
    if production.get("provider") != "bundled lunar-python==1.4.8":
        errors.append("review_packet_v2.production_timing_evidence.provider")
    if production.get("runtime_authority") != "bundled":
        errors.append("review_packet_v2.production_timing_evidence.runtime_authority")
    if production.get("benchmark_result") != "PASS":
        errors.append("review_packet_v2.production_timing_evidence.benchmark_result")
    if production.get("hko_points") != 48 or production.get("within_60_seconds") != 48:
        errors.append("review_packet_v2.production_timing_evidence.coverage")
    if production.get("max_abs_seconds") != 30:
        errors.append("review_packet_v2.production_timing_evidence.max_abs_seconds")

    source = payload.get("independent_oracle_source_plan")
    if not isinstance(source, Mapping):
        errors.append("review_packet_v2.independent_oracle_source_plan")
        source = {}
    if source.get("provider") != "Hong Kong Observatory":
        errors.append("review_packet_v2.independent_oracle_source_plan.provider")
    if source.get("provider_role") != "independent_astronomical_input_only":
        errors.append("review_packet_v2.independent_oracle_source_plan.provider_role")
    if source.get("published_precision_seconds") != 60:
        errors.append("review_packet_v2.independent_oracle_source_plan.published_precision_seconds")
    sources = source.get("sources")
    expected_shas = {
        2015: "60a45ab889ef436936571a04a49387c6f9ce8d43243fb21c64e3fcb0331c8320",
        2016: "84beb01553646b807a7c15d6efebdd7550af1ac6d7f06e07bfdd124dab9e443b",
    }
    if not isinstance(sources, list) or len(sources) != 2:
        errors.append("review_packet_v2.independent_oracle_source_plan.sources")
    else:
        for row in sources:
            year = row.get("year") if isinstance(row, Mapping) else None
            if year not in expected_shas:
                errors.append("review_packet_v2.independent_oracle_source_plan.sources.year")
                continue
            if row.get("source_bytes_sha256") != expected_shas[year]:
                errors.append(f"review_packet_v2.independent_oracle_source_plan.sources[{year}].sha256")
            if row.get("source_bytes_status") != "CAPTURED_AND_VERIFIED":
                errors.append(f"review_packet_v2.independent_oracle_source_plan.sources[{year}].status")

    selection = payload.get("case_selection")
    if not isinstance(selection, Mapping):
        errors.append("review_packet_v2.case_selection")
        selection = {}
    if selection.get("selection_provenance") != "same_12_birth_and_sex_inputs_as_v1_pre_result_census_no_additions_removals_or_replacements":
        errors.append("review_packet_v2.case_selection.selection_provenance")
    for key in ("post_result_case_additions","post_result_case_removals","post_result_case_replacements"):
        if selection.get(key) != 0:
            errors.append(f"review_packet_v2.case_selection.{key}")
    if selection.get("original_selection_production_results_consulted") is not False:
        errors.append("review_packet_v2.case_selection.original_selection_production_results_consulted")
    cases = selection.get("cases")
    if not isinstance(cases, list) or len(cases) != 12:
        errors.append("review_packet_v2.case_selection.cases")
        cases = []
    seen = set()
    for index, case in enumerate(cases):
        if not isinstance(case, Mapping):
            errors.append(f"review_packet_v2.case_selection.cases[{index}]")
            continue
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not _OPAQUE_ID.fullmatch(case_id) or case_id in seen:
            errors.append(f"review_packet_v2.case_selection.cases[{index}].case_id")
        seen.add(case_id)
        if not _aware(case.get("birth_datetime")):
            errors.append(f"review_packet_v2.case_selection.cases[{index}].birth_datetime")
        if case.get("sex") not in {"male", "female"}:
            errors.append(f"review_packet_v2.case_selection.cases[{index}].sex")
        tags = case.get("coverage_tags")
        if not isinstance(tags, list) or not tags or len(tags) != len(set(tags)):
            errors.append(f"review_packet_v2.case_selection.cases[{index}].coverage_tags")
            continue
        if any(tag not in _ALLOWED_TAGS for tag in tags):
            errors.append(f"review_packet_v2.case_selection.cases[{index}].coverage_tags.allowed")
        lowered = " ".join(tags).lower()
        if any(fragment in lowered for fragment in _FORBIDDEN_TAG_FRAGMENTS):
            errors.append(f"review_packet_v2.case_selection.cases[{index}].coverage_tags.answer_leakage")

    comparison = payload.get("comparison_plan")
    paths = comparison.get("paths") if isinstance(comparison, Mapping) else None
    if not isinstance(paths, list):
        errors.append("review_packet_v2.comparison_plan.paths")
        paths = []
    by_path = {row.get("path"): row for row in paths if isinstance(row, Mapping)}
    expected = {
        "/decadal_direction": ("exact", None),
        "/periods/0/pillar": ("exact", None),
        "/periods/0/start_age_years": ("number_abs", 0.0002314814814814815),
        "/periods/0/start_datetime": ("datetime_abs_seconds", 7304.85),
        "/periods/1/end_datetime": ("datetime_abs_seconds", 7304.85),
    }
    if set(by_path) != set(expected):
        errors.append("review_packet_v2.comparison_plan.paths.census")
    for path, (kind, tolerance) in expected.items():
        row = by_path.get(path, {})
        if row.get("kind") != kind:
            errors.append(f"review_packet_v2.comparison_plan{path}.kind")
        if tolerance is not None:
            value = row.get("proposed_tolerance")
            if not isinstance(value, (int,float)) or isinstance(value,bool) or not math.isfinite(value) or value != tolerance:
                errors.append(f"review_packet_v2.comparison_plan{path}.tolerance")

    equality = payload.get("equality_coverage")
    if not isinstance(equality, Mapping):
        errors.append("review_packet_v2.equality_coverage")
    else:
        if equality.get("exact_subminute_hko_equality_case_present") is not False:
            errors.append("review_packet_v2.equality_coverage.exact_subminute_hko_equality_case_present")
        if equality.get("project_unit_test_present") is not True:
            errors.append("review_packet_v2.equality_coverage.project_unit_test_present")
        if equality.get("domain_acceptance_required") is not True:
            errors.append("review_packet_v2.equality_coverage.domain_acceptance_required")

    decisions = payload.get("review_decisions_required")
    if not isinstance(decisions, list) or set(decisions) != _REQUIRED_DECISIONS:
        errors.append("review_packet_v2.review_decisions_required")
    blockers = payload.get("blocking_items")
    if not isinstance(blockers, list) or set(blockers) != _REQUIRED_BLOCKERS:
        errors.append("review_packet_v2.blocking_items")

    boundary = payload.get("independence_boundary")
    if not isinstance(boundary, Mapping):
        errors.append("review_packet_v2.independence_boundary")
        boundary = {}
    for key in (
        "oracle_expected_values_present",
        "oracle_execution_started",
        "oracle_may_receive_production_code",
        "oracle_may_receive_production_output",
        "oracle_may_receive_comparison_results_before_seal",
    ):
        if boundary.get(key) is not False:
            errors.append(f"review_packet_v2.independence_boundary.{key}")

    return sorted(set(errors))


def ready_for_preoracle_seal_v2(payload):
    return False
