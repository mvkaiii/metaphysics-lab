from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from typing import Mapping, Sequence
from zoneinfo import ZoneInfo

from engine.bazi.calendar import flow_month_pillar, flow_year_pillar, solar_term_time
from engine.bazi.structural_relations import detect_structural_relations

from .control_eligibility import historical_strength_class
from .models import ActivationEvidence, ActivationRankVector

FLOW_MONTH_START_TERMS = (
    "立春", "驚蟄", "清明", "立夏", "芒種", "小暑",
    "立秋", "白露", "寒露", "立冬", "大雪", "小寒",
)

PROFILE_ID = "historical-activation-bazi-v1"
RULE_VERSION = "1.0-exp"
_FORBIDDEN_HINTS = frozenset((
    "preferred_years", "known_event_years", "event_keywords", "manual_rank_override",
))


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
    """Return calibration periods for the previous Gregorian label years.

    The public name is retained for compatibility. Calibration labels exclude
    the current Gregorian year even before LiChun; each label still uses its
    LiChun-to-next-LiChun technical flow-year period for deterministic evidence.
    """
    if not isinstance(count, int) or isinstance(count, bool) or count < 1:
        raise ValueError("count must be a positive integer")
    if not isinstance(timezone, str) or not timezone.strip():
        raise ValueError("timezone must be a non-empty IANA timezone")
    zone = ZoneInfo(timezone.strip())
    as_of = _aware_datetime(as_of_datetime, "as_of_datetime").astimezone(zone)
    labels = range(as_of.year - count, as_of.year)
    periods = []
    for label in labels:
        start = solar_term_time(label, "立春", zone)
        end = solar_term_time(label + 1, "立春", zone)
        pillar = flow_year_pillar(start + timedelta(seconds=1))
        periods.append({
            "label_year": label,
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
            "flow_year_pillar": pillar,
        })
    return tuple(periods)


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


def build_year_evidence(
    *,
    label_year: int,
    flow_year_pillar: str,
    natal_pillars: Mapping[str, str],
    decadal_pillar: str,
    decadal_boundary: bool,
) -> tuple[ActivationEvidence, ...]:
    """Translate neutral Bazi structural truth into the legacy activation contract."""
    relations = detect_structural_relations(
        scope="yearly",
        target_pillar=flow_year_pillar,
        natal_pillars=natal_pillars,
        decadal_pillar=decadal_pillar,
        decadal_boundary=decadal_boundary,
    )
    evidence = tuple(
        _evidence(
            label_year,
            row.tier,
            row.relation_family,
            row.target_layer,
            row.target_component,
            row.participants,
        )
        for row in relations
    )
    return tuple(sorted(evidence, key=lambda item: item.evidence_id))


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


def flow_month_periods_for_year(annual_period: Mapping[str, object], timezone: str) -> tuple[dict, ...]:
    if not isinstance(annual_period, Mapping):
        raise ValueError("annual_period must be a mapping")
    if not isinstance(timezone, str) or not timezone.strip():
        raise ValueError("timezone must be a non-empty IANA timezone")
    label_year = annual_period.get("label_year")
    if not isinstance(label_year, int) or isinstance(label_year, bool):
        raise ValueError("annual_period.label_year must be an integer")
    start = _aware_datetime(annual_period.get("period_start"), "period_start")
    end = _aware_datetime(annual_period.get("period_end"), "period_end")
    boundaries = [start]
    for term in FLOW_MONTH_START_TERMS[1:]:
        boundary_year = label_year + 1 if term == "小寒" else label_year
        boundaries.append(solar_term_time(boundary_year, term, timezone))
    boundaries.append(end)
    if len(boundaries) != 13 or any(left >= right for left, right in zip(boundaries, boundaries[1:])):
        raise ValueError("flow-month boundaries are incomplete or non-monotonic")
    rows = []
    for month_start, month_end in zip(boundaries, boundaries[1:]):
        rows.append({
            "period_start": month_start.isoformat(),
            "period_end": month_end.isoformat(),
            "flow_month_pillar": flow_month_pillar(month_start + timedelta(seconds=1)),
        })
    return tuple(rows)


def build_month_activation_diagnostics(
    *,
    annual_row: Mapping[str, object],
    natal_pillars: Mapping[str, str],
    bazi: Mapping[str, object],
    timezone: str,
) -> dict:
    if not isinstance(annual_row, Mapping):
        raise ValueError("annual_row must be a mapping")
    if not isinstance(natal_pillars, Mapping):
        raise ValueError("natal_pillars must be a mapping")
    if not isinstance(bazi, Mapping):
        raise ValueError("bazi must be a mapping")
    raw_parent_rank = annual_row.get("rank_vector")
    if not isinstance(raw_parent_rank, Mapping):
        raise ValueError("annual_row.rank_vector must be a mapping")
    parent_rank = ActivationRankVector(**dict(raw_parent_rank))
    parent_strength = historical_strength_class(parent_rank)
    try:
        periods = flow_month_periods_for_year(annual_row, timezone)
    except ValueError:
        return {
            "coverage_complete": False,
            "coverage_count": 0,
            "local_windows": [],
            "months": [],
        }

    months = []
    local_windows = []
    try:
        for period in periods:
            context = _decadal_context(bazi, period)
            relations = detect_structural_relations(
                scope="monthly",
                target_pillar=period["flow_month_pillar"],
                natal_pillars=natal_pillars,
                decadal_pillar=context["pillar"],
                decadal_boundary=False,
            )
            evidence = tuple(
                _evidence(
                    int(annual_row["label_year"]),
                    relation.tier,
                    relation.relation_family,
                    relation.target_layer,
                    relation.target_component,
                    relation.participants,
                )
                for relation in relations
            )
            rank = rank_evidence(evidence)
            child_strength = historical_strength_class(rank)
            if child_strength == "strong" and parent_strength in {"weak", "unspecified"}:
                window_type = "local_spike"
            elif child_strength == "strong":
                window_type = "active_window"
            else:
                window_type = None
            row = {
                "period_start": period["period_start"],
                "period_end": period["period_end"],
                "flow_month_pillar": period["flow_month_pillar"],
                "decadal_pillar": context["pillar"],
                "rank_vector": rank.to_dict(),
                "strength_class": child_strength,
                "window_type": window_type,
            }
            months.append(row)
            if window_type is not None:
                local_windows.append(dict(row))
    except (KeyError, TypeError, ValueError):
        return {
            "coverage_complete": False,
            "coverage_count": len(months),
            "local_windows": local_windows,
            "months": months,
        }

    return {
        "coverage_complete": len(months) == 12,
        "coverage_count": len(months),
        "local_windows": local_windows,
        "months": months,
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
