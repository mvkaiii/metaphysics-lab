"""Neutral deterministic Bazi structural relation truth.

This module contains no historical-event data, ranking semantics, domains, or
forecast wording.  It is shared structural infrastructure for prospective and
historical consumers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional, Tuple

from engine.calendar.sexagenary import GAN, ZHI, is_valid_sexagenary_pair


_COMPONENTS = ("year", "month", "day", "hour")
_ALLOWED_SCOPES = ("decadal", "yearly", "monthly", "daily", "hourly")


def _pairs(values):
    return frozenset(frozenset(pair) for pair in values)


def _sets(values):
    return frozenset(frozenset(items) for items in values)


CLASH_PAIRS = _pairs((
    ("子", "午"), ("丑", "未"), ("寅", "申"),
    ("卯", "酉"), ("辰", "戌"), ("巳", "亥"),
))

COMBINATION_PAIRS = _pairs((
    ("子", "丑"), ("寅", "亥"), ("卯", "戌"),
    ("辰", "酉"), ("巳", "申"), ("午", "未"),
))

THREE_HARMONY_SETS = _sets((
    ("申", "子", "辰"), ("亥", "卯", "未"),
    ("寅", "午", "戌"), ("巳", "酉", "丑"),
))

THREE_MEETING_SETS = _sets((
    ("亥", "子", "丑"), ("寅", "卯", "辰"),
    ("巳", "午", "未"), ("申", "酉", "戌"),
))

FULL_PUNISHMENT_SETS = _sets((
    ("寅", "巳", "申"),
    ("丑", "戌", "未"),
))
PAIR_PUNISHMENTS = _pairs((("子", "卯"),))
SELF_PUNISHMENTS = frozenset(("辰", "午", "酉", "亥"))

HARM_PAIRS = _pairs((
    ("子", "未"), ("丑", "午"), ("寅", "巳"),
    ("卯", "辰"), ("申", "亥"), ("酉", "戌"),
))

BREAK_PAIRS = _pairs((
    ("子", "酉"), ("丑", "辰"), ("寅", "亥"),
    ("卯", "午"), ("巳", "申"), ("未", "戌"),
))

STEM_COMBINATION_PAIRS = _pairs((
    ("甲", "己"), ("乙", "庚"), ("丙", "辛"),
    ("丁", "壬"), ("戊", "癸"),
))


@dataclass(frozen=True)
class StructuralRelation:
    tier: int
    relation_family: str
    target_layer: str
    target_component: str
    participants: Tuple[str, ...]

    def __post_init__(self) -> None:
        if self.tier not in (1, 2, 3):
            raise ValueError("tier must be 1, 2, or 3")
        for field_name in ("relation_family", "target_layer", "target_component"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError("%s must be a non-empty string" % field_name)
        participants = tuple(sorted(str(item) for item in self.participants))
        if not participants or any(not item for item in participants):
            raise ValueError("participants must contain non-empty values")
        object.__setattr__(self, "participants", participants)


def _pair(left: str, right: str) -> frozenset[str]:
    return frozenset((left, right))


def _validate_pillar(value: object, field: str) -> str:
    if not isinstance(value, str) or len(value) != 2:
        raise ValueError("%s must be a two-character pillar" % field)
    stem, branch = value[0], value[1]
    if stem not in GAN or branch not in ZHI or not is_valid_sexagenary_pair(stem, branch):
        raise ValueError("%s must be a valid sexagenary pillar" % field)
    return value


def _relation(
    tier: int,
    family: str,
    target_layer: str,
    target_component: str,
    participants,
) -> StructuralRelation:
    return StructuralRelation(
        tier=tier,
        relation_family=family,
        target_layer=target_layer,
        target_component=target_component,
        participants=tuple(participants),
    )


def _full_patterns(flow_branch: str, existing: set[str], patterns, family: str):
    result = []
    for pattern in patterns:
        if flow_branch not in pattern or pattern <= existing:
            continue
        if pattern - {flow_branch} <= existing:
            result.append(
                _relation(1, family, "pattern", "-".join(sorted(pattern)), tuple(pattern))
            )
    return result


def _partial_patterns(flow_branch: str, existing: set[str], patterns, family: str, completed):
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
                _relation(2, family, "pattern", "-".join(sorted(pattern)), tuple(pattern))
            )
    return result


def _punishment_pair(flow_branch: str, target_branch: str) -> bool:
    if flow_branch == target_branch and flow_branch in SELF_PUNISHMENTS:
        return True
    pair = _pair(flow_branch, target_branch)
    if pair in PAIR_PUNISHMENTS:
        return True
    return any(pair <= pattern for pattern in FULL_PUNISHMENT_SETS)


def detect_structural_relations(
    *,
    scope: str,
    target_pillar: str,
    natal_pillars: Mapping[str, str],
    decadal_pillar: Optional[str],
    decadal_boundary: bool = False,
) -> Tuple[StructuralRelation, ...]:
    """Return canonical structural relations for one target Bazi pillar.

    The result is intentionally interpretation-free.  ``decadal_boundary`` and
    ``sui_yun_bing_lin`` are yearly-only concepts; finer scopes cannot inherit
    them merely because they occur inside the same year.
    """

    if scope not in _ALLOWED_SCOPES:
        raise ValueError("unsupported structural relation scope: %s" % scope)
    target = _validate_pillar(target_pillar, "target_pillar")
    if not isinstance(natal_pillars, Mapping) or set(natal_pillars) != set(_COMPONENTS):
        raise ValueError("natal_pillars must contain exactly year/month/day/hour")
    natal = {
        component: _validate_pillar(natal_pillars[component], "natal_pillars.%s" % component)
        for component in _COMPONENTS
    }
    decadal = None if decadal_pillar is None else _validate_pillar(decadal_pillar, "decadal_pillar")
    if not isinstance(decadal_boundary, bool):
        raise ValueError("decadal_boundary must be bool")

    flow_stem, flow_branch = target[0], target[1]
    dec_stem = None if decadal is None else decadal[0]
    dec_branch = None if decadal is None else decadal[1]

    existing_branches = {pillar[1] for pillar in natal.values()}
    if dec_branch is not None and scope != "decadal":
        existing_branches.add(dec_branch)

    rows = []
    suppressed_branch = set()
    suppressed_stem = set()

    if scope == "yearly" and decadal_boundary:
        rows.append(_relation(1, "decadal_boundary", "cycle", "decadal", (target,)))

    if scope == "yearly" and decadal is not None and target == decadal:
        rows.append(_relation(1, "sui_yun_bing_lin", "decadal", "pillar", (target, decadal)))
        suppressed_branch.add(("decadal", "pillar"))
        suppressed_stem.add(("decadal", "pillar"))

    for component, pillar in natal.items():
        if target == pillar:
            rows.append(_relation(1, "natal_pillar_repeat", "natal", component, (target, pillar)))
            suppressed_branch.add(("natal", component))
            suppressed_stem.add(("natal", component))

    targets = [("natal", component, pillar) for component, pillar in natal.items()]
    if decadal is not None and scope != "decadal":
        targets.append(("decadal", "pillar", decadal))

    for layer, component, pillar in targets:
        target_branch = pillar[1]
        if _pair(flow_branch, target_branch) in CLASH_PAIRS:
            rows.append(_relation(
                1,
                "branch_clash_natal" if layer == "natal" else "branch_clash_decadal",
                layer,
                component,
                (flow_branch, target_branch),
            ))

    full_harmony = _full_patterns(
        flow_branch, existing_branches, THREE_HARMONY_SETS, "completes_three_harmony"
    )
    full_meeting = _full_patterns(
        flow_branch, existing_branches, THREE_MEETING_SETS, "completes_three_meeting"
    )
    full_punishment = _full_patterns(
        flow_branch, existing_branches, FULL_PUNISHMENT_SETS, "completes_three_punishment"
    )
    rows.extend(full_harmony)
    rows.extend(full_meeting)
    rows.extend(full_punishment)
    rows.extend(_partial_patterns(
        flow_branch, existing_branches, THREE_HARMONY_SETS, "partial_three_harmony", full_harmony
    ))
    rows.extend(_partial_patterns(
        flow_branch, existing_branches, THREE_MEETING_SETS, "partial_three_meeting", full_meeting
    ))

    completed_punishment_sets = {frozenset(item.participants) for item in full_punishment}
    for layer, component, pillar in targets:
        target_stem, target_branch = pillar[0], pillar[1]
        branch_pair = _pair(flow_branch, target_branch)
        if branch_pair in COMBINATION_PAIRS:
            rows.append(_relation(2, "branch_six_harmony", layer, component, (flow_branch, target_branch)))
        if _punishment_pair(flow_branch, target_branch):
            relevant_full = any(
                flow_branch in pattern and target_branch in pattern and pattern in completed_punishment_sets
                for pattern in FULL_PUNISHMENT_SETS
            )
            if not relevant_full:
                rows.append(_relation(
                    2, "branch_punishment_support", layer, component, (flow_branch, target_branch)
                ))
        if flow_branch == target_branch and (layer, component) not in suppressed_branch:
            rows.append(_relation(2, "branch_repeat", layer, component, (flow_branch, target_branch)))
        if _pair(flow_stem, target_stem) in STEM_COMBINATION_PAIRS:
            rows.append(_relation(2, "stem_combination", layer, component, (flow_stem, target_stem)))
        if branch_pair in HARM_PAIRS:
            rows.append(_relation(3, "branch_harm", layer, component, (flow_branch, target_branch)))
        if branch_pair in BREAK_PAIRS:
            rows.append(_relation(3, "branch_break", layer, component, (flow_branch, target_branch)))
        if flow_stem == target_stem and (layer, component) not in suppressed_stem:
            rows.append(_relation(3, "stem_repeat", layer, component, (flow_stem, target_stem)))

    unique = {}
    for row in rows:
        key = (
            row.tier,
            row.relation_family,
            row.target_layer,
            row.target_component,
            row.participants,
        )
        unique[key] = row
    return tuple(sorted(
        unique.values(),
        key=lambda item: (
            item.tier,
            item.relation_family,
            item.target_layer,
            item.target_component,
            item.participants,
        ),
    ))
