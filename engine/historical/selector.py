from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from typing import Mapping, Sequence
from zoneinfo import ZoneInfo

from engine.bazi.calendar import flow_year_pillar, solar_term_time
from engine.bazi.structural_relations import detect_structural_relations

from .models import ActivationEvidence, ActivationRankVector

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
