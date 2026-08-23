from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from typing import Mapping, Sequence
from zoneinfo import ZoneInfo

from engine.bazi.calendar import flow_year_pillar, solar_term_time

from .models import ActivationEvidence, ActivationRankVector
from .relations import (
    BREAK_PAIRS,
    CLASH_PAIRS,
    COMBINATION_PAIRS,
    FULL_PUNISHMENT_SETS,
    HARM_PAIRS,
    PAIR_PUNISHMENTS,
    SELF_PUNISHMENTS,
    STEM_COMBINATION_PAIRS,
    THREE_HARMONY_SETS,
    THREE_MEETING_SETS,
)

PROFILE_ID = "historical-activation-bazi-v1"
RULE_VERSION = "1.0-exp"
_FORBIDDEN_HINTS = frozenset((
    "preferred_years", "known_event_years", "event_keywords", "manual_rank_override",
))
_COMPONENTS = ("year", "month", "day", "hour")


def _canonical_digest(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _aware_datetime(value: object, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("%s must be an ISO datetime" % field)
    parsed = datetime.fromisoformat(value.strip())
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("%s must include timezone offset" % field)
    return parsed


def completed_flow_year_periods(as_of_datetime: str, timezone: str, count: int = 10) -> tuple[dict, ...]:
    if not isinstance(count, int) or isinstance(count, bool) or count < 1:
        raise ValueError("count must be a positive integer")
    if not isinstance(timezone, str) or not timezone.strip():
        raise ValueError("timezone must be a non-empty IANA timezone")
    zone = ZoneInfo(timezone.strip())
    as_of = _aware_datetime(as_of_datetime, "as_of_datetime").astimezone(zone)
    this_lichun = solar_term_time(as_of.year, "立春", zone)
    current_label = as_of.year if as_of >= this_lichun else as_of.year - 1
    last_completed = current_label - 1
    labels = range(last_completed - count + 1, last_completed + 1)
    periods = []
    for label in labels:
        start = solar_term_time(label, "立春", zone)
        end = solar_term_time(label + 1, "立春", zone)
        if end > as_of:
            raise AssertionError("completed-flow-year window included an unfinished period")
        pillar = flow_year_pillar(start + timedelta(seconds=1))
        periods.append({
            "label_year": label,
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
            "flow_year_pillar": pillar,
        })
    return tuple(periods)


def _pair(left: str, right: str) -> frozenset[str]:
    return frozenset((left, right))


def _evidence(
    label_year: int,
    tier: int,
    family: str,
    target_layer: str,
    target_component: str,
    participants: Sequence[str],
    **metadata,
) -> ActivationEvidence:
    canonical_participants = tuple(sorted(str(item) for item in participants))
    eid = "%s:T%s:%s:%s:%s:%s" % (
        label_year,
        tier,
        family,
        target_layer,
        target_component,
        ",".join(canonical_participants),
    )
    return ActivationEvidence(
        evidence_id=eid,
        tier=tier,
        relation_family=family,
        target_layer=target_layer,
        target_component=target_component,
        participants=canonical_participants,
        metadata=metadata,
    )


def _full_patterns(flow_branch: str, existing: set[str], patterns, family: str, label_year: int):
    result = []
    for pattern in patterns:
        if flow_branch not in pattern or pattern <= existing:
            continue
        if pattern - {flow_branch} <= existing:
            result.append(
                _evidence(label_year, 1, family, "pattern", "-".join(sorted(pattern)), tuple(pattern))
            )
    return result


def _partial_patterns(flow_branch: str, existing: set[str], patterns, family: str, label_year: int, completed):
    completed_sets = {frozenset(item.participants) for item in completed}
    result = []
    for pattern in patterns:
        if flow_branch not in pattern or pattern in completed_sets:
            continue
        if pattern <= existing:
            continue
        members = (pattern & existing) | {flow_branch}
        if len(members) >= 2:
            result.append(
                _evidence(label_year, 2, family, "pattern", "-".join(sorted(pattern)), tuple(pattern))
            )
    return result


def _punishment_pair(flow_branch: str, target_branch: str) -> bool:
    if flow_branch == target_branch and flow_branch in SELF_PUNISHMENTS:
        return True
    pair = _pair(flow_branch, target_branch)
    if pair in PAIR_PUNISHMENTS:
        return True
    return any(pair <= pattern for pattern in FULL_PUNISHMENT_SETS)


def build_year_evidence(
    *,
    label_year: int,
    flow_year_pillar: str,
    natal_pillars: Mapping[str, str],
    decadal_pillar: str,
    decadal_boundary: bool,
) -> tuple[ActivationEvidence, ...]:
    if not isinstance(flow_year_pillar, str) or len(flow_year_pillar) != 2:
        raise ValueError("flow_year_pillar must be a two-character pillar")
    if not isinstance(decadal_pillar, str) or len(decadal_pillar) != 2:
        raise ValueError("decadal_pillar must be a two-character pillar")
    if any(component not in natal_pillars for component in _COMPONENTS):
        raise ValueError("natal_pillars must contain year/month/day/hour")
    flow_stem, flow_branch = flow_year_pillar[0], flow_year_pillar[1]
    dec_stem, dec_branch = decadal_pillar[0], decadal_pillar[1]
    natal = {component: str(natal_pillars[component]) for component in _COMPONENTS}
    existing_branches = {pillar[1] for pillar in natal.values()} | {dec_branch}

    evidence = []
    suppressed_branch = set()
    suppressed_stem = set()

    if decadal_boundary:
        evidence.append(_evidence(label_year, 1, "decadal_boundary", "cycle", "decadal", (flow_year_pillar,)))

    if flow_year_pillar == decadal_pillar:
        evidence.append(_evidence(
            label_year, 1, "sui_yun_bing_lin", "decadal", "pillar", (flow_year_pillar, decadal_pillar)
        ))
        suppressed_branch.add(("decadal", "pillar"))
        suppressed_stem.add(("decadal", "pillar"))

    for component, pillar in natal.items():
        if len(pillar) != 2:
            raise ValueError("natal pillar must contain stem+branch")
        if flow_year_pillar == pillar:
            evidence.append(_evidence(
                label_year, 1, "natal_pillar_repeat", "natal", component, (flow_year_pillar, pillar)
            ))
            suppressed_branch.add(("natal", component))
            suppressed_stem.add(("natal", component))

    targets = [("natal", component, pillar) for component, pillar in natal.items()]
    targets.append(("decadal", "pillar", decadal_pillar))

    for layer, component, pillar in targets:
        target_stem, target_branch = pillar[0], pillar[1]
        branch_pair = _pair(flow_branch, target_branch)
        if branch_pair in CLASH_PAIRS:
            evidence.append(_evidence(
                label_year, 1,
                "branch_clash_natal" if layer == "natal" else "branch_clash_decadal",
                layer, component, (flow_branch, target_branch),
            ))

    full_harmony = _full_patterns(
        flow_branch, existing_branches, THREE_HARMONY_SETS, "completes_three_harmony", label_year
    )
    full_meeting = _full_patterns(
        flow_branch, existing_branches, THREE_MEETING_SETS, "completes_three_meeting", label_year
    )
    full_punishment = _full_patterns(
        flow_branch, existing_branches, FULL_PUNISHMENT_SETS, "completes_three_punishment", label_year
    )
    evidence.extend(full_harmony)
    evidence.extend(full_meeting)
    evidence.extend(full_punishment)

    evidence.extend(_partial_patterns(
        flow_branch, existing_branches, THREE_HARMONY_SETS, "partial_three_harmony", label_year, full_harmony
    ))
    evidence.extend(_partial_patterns(
        flow_branch, existing_branches, THREE_MEETING_SETS, "partial_three_meeting", label_year, full_meeting
    ))

    completed_punishment_sets = {frozenset(item.participants) for item in full_punishment}
    for layer, component, pillar in targets:
        target_stem, target_branch = pillar[0], pillar[1]
        branch_pair = _pair(flow_branch, target_branch)
        if branch_pair in COMBINATION_PAIRS:
            evidence.append(_evidence(
                label_year, 2, "branch_six_harmony", layer, component, (flow_branch, target_branch)
            ))
        if _punishment_pair(flow_branch, target_branch):
            relevant_full = any(
                flow_branch in pattern and target_branch in pattern and pattern in completed_punishment_sets
                for pattern in FULL_PUNISHMENT_SETS
            )
            if not relevant_full:
                evidence.append(_evidence(
                    label_year, 2, "branch_punishment_support", layer, component, (flow_branch, target_branch)
                ))
        if flow_branch == target_branch and (layer, component) not in suppressed_branch:
            evidence.append(_evidence(
                label_year, 2, "branch_repeat", layer, component, (flow_branch, target_branch)
            ))
        if _pair(flow_stem, target_stem) in STEM_COMBINATION_PAIRS:
            evidence.append(_evidence(
                label_year, 2, "stem_combination", layer, component, (flow_stem, target_stem)
            ))
        if branch_pair in HARM_PAIRS:
            evidence.append(_evidence(
                label_year, 3, "branch_harm", layer, component, (flow_branch, target_branch)
            ))
        if branch_pair in BREAK_PAIRS:
            evidence.append(_evidence(
                label_year, 3, "branch_break", layer, component, (flow_branch, target_branch)
            ))
        if flow_stem == target_stem and (layer, component) not in suppressed_stem:
            evidence.append(_evidence(
                label_year, 3, "stem_repeat", layer, component, (flow_stem, target_stem)
            ))

    unique = {}
    for item in evidence:
        key = (
            item.tier, item.relation_family, item.target_layer,
            item.target_component, tuple(item.participants),
        )
        unique[key] = item
    return tuple(sorted(unique.values(), key=lambda item: item.evidence_id))


def rank_evidence(evidence: Sequence[ActivationEvidence]) -> ActivationRankVector:
    tier_family = {}
    tier_count = {}
    for tier in (1, 2, 3):
        selected = [item for item in evidence if item.tier == tier]
        tier_family[tier] = len({item.relation_family for item in selected})
        tier_count[tier] = len(selected)
    natal_t1 = any(item.tier == 1 and item.target_layer == "natal" for item in evidence)
    decadal_t1 = any(item.tier == 1 and item.target_layer == "decadal" for item in evidence)
    return ActivationRankVector(
        tier1_family_count=tier_family[1],
        tier1_evidence_count=tier_count[1],
        cross_layer_tier1=bool(natal_t1 and decadal_t1),
        tier2_family_count=tier_family[2],
        tier2_evidence_count=tier_count[2],
        tier3_family_count=tier_family[3],
        tier3_evidence_count=tier_count[3],
    )


def _project_bazi(normalized: Mapping[str, object]) -> Mapping[str, object]:
    validation = normalized.get("validation", {})
    if isinstance(validation, Mapping) and int(validation.get("blocking_conflict_count", 0) or 0) > 0:
        raise ValueError("historical selector is blocked by natal conflict")
    project = normalized.get("project")
    if not isinstance(project, Mapping):
        raise ValueError("historical selector requires Project natal facts")
    bazi = project.get("bazi")
    if not isinstance(bazi, Mapping):
        raise ValueError("historical selector requires Project Bazi facts")
    return bazi


def _decadal_context(bazi: Mapping[str, object], period: Mapping[str, object]) -> dict:
    rows = bazi.get("decadal_periods")
    if not isinstance(rows, (list, tuple)) or not rows:
        raise ValueError("Project Bazi decadal periods are missing")
    start = _aware_datetime(period["period_start"], "period_start")
    end = _aware_datetime(period["period_end"], "period_end")
    midpoint = start + (end - start) / 2
    parsed = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        row_start = _aware_datetime(row.get("start_datetime"), "decadal.start_datetime")
        row_end = _aware_datetime(row.get("end_datetime"), "decadal.end_datetime")
        parsed.append((row, row_start, row_end))
    active = next((row for row, row_start, row_end in parsed if row_start <= midpoint < row_end), None)
    if active is None:
        raise ValueError("no Bazi decadal period covers flow-year midpoint")
    boundaries = sorted({
        boundary.isoformat()
        for _row, row_start, row_end in parsed
        for boundary in (row_start, row_end)
        if start <= boundary < end
    })
    return {
        "index": int(active["index"]),
        "pillar": str(active["pillar"]),
        "boundary_in_period": bool(boundaries),
        "boundary_datetimes": boundaries,
    }


def _control_quality(rank: ActivationRankVector) -> str:
    if rank.tier1_family_count > 0:
        return "relative_low"
    if rank.tier2_family_count > 0:
        return "acceptable_control"
    return "strong_control"


def select_historical_activation(payload: Mapping[str, object]) -> dict:
    if not isinstance(payload, Mapping):
        raise ValueError("selector payload must be a mapping")
    forbidden = sorted(_FORBIDDEN_HINTS & set(payload))
    if forbidden:
        raise ValueError("history-based ranking hints are forbidden: %s" % ", ".join(forbidden))
    normalized = payload.get("normalized_natal")
    if not isinstance(normalized, Mapping):
        raise ValueError("normalized_natal must be a mapping")
    timezone = payload.get("timezone")
    as_of = payload.get("as_of_datetime")
    if not isinstance(timezone, str) or not isinstance(as_of, str):
        raise ValueError("as_of_datetime and timezone are required")
    bazi = _project_bazi(normalized)
    natal_pillars = bazi.get("pillars")
    if not isinstance(natal_pillars, Mapping):
        raise ValueError("Project Bazi pillars are missing")

    periods = completed_flow_year_periods(as_of, timezone, 10)
    rows = []
    decadal_indices = set()
    boundary_in_window = False
    for period in periods:
        context = _decadal_context(bazi, period)
        decadal_indices.add(context["index"])
        boundary_in_window = boundary_in_window or context["boundary_in_period"]
        evidence = build_year_evidence(
            label_year=period["label_year"],
            flow_year_pillar=period["flow_year_pillar"],
            natal_pillars=natal_pillars,
            decadal_pillar=context["pillar"],
            decadal_boundary=context["boundary_in_period"],
        )
        rank = rank_evidence(evidence)
        rows.append({
            **dict(period),
            "decadal_index": context["index"],
            "decadal_pillar": context["pillar"],
            "decadal_boundary_in_period": context["boundary_in_period"],
            "decadal_boundary_datetimes": context["boundary_datetimes"],
            "rank_vector": rank.to_dict(),
            "evidence": [item.to_dict() for item in evidence],
            "_sort_key": rank.as_sort_key(period["label_year"]),
        })
    ranked = sorted(rows, key=lambda row: row["_sort_key"], reverse=True)
    for row in ranked:
        row.pop("_sort_key", None)
    high = ranked[:4]
    control = ranked[-1]
    if boundary_in_window:
        coverage = "boundary_in_window"
    elif len(decadal_indices) > 1:
        coverage = "cross_cycle"
    else:
        coverage = "single_cycle"

    canonical = {
        "profile_id": PROFILE_ID,
        "rule_version": RULE_VERSION,
        "as_of_datetime": as_of,
        "timezone": timezone,
        "ranked_periods": ranked,
        "high_year_labels": [item["label_year"] for item in high],
        "control_year_label": control["label_year"],
        "control_quality": _control_quality(ActivationRankVector(**control["rank_vector"])),
        "major_cycle_coverage": coverage,
    }
    digest = _canonical_digest(canonical)
    return {
        "classification": "Project 推導盤面",
        "capability_id": "historical.activation_selector",
        "profile_id": PROFILE_ID,
        "rule_version": RULE_VERSION,
        "maturity": "experimental",
        "ranking_basis": "bazi_only",
        "as_of_datetime": as_of,
        "timezone": timezone,
        "ranked_periods": ranked,
        "high_years": high,
        "control_year": control,
        "control_quality": canonical["control_quality"],
        "major_cycle_coverage": coverage,
        "selection_digest": digest,
        "provenance": {
            "derived_by": "engine.historical.selector",
            "annual_boundary": "li_chun",
            "selection_policy": "lexicographic_top4_bottom1_no_override",
            "ziwei_ranking_authority": False,
        },
    }
