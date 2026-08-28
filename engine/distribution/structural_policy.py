"""Closed semantic policy for Phase 3.5 structural interpretation."""

from __future__ import annotations

MAPPING_PROFILE = "lin_tianji_domain_v2-exp"
BAZI_STRUCTURAL_PROFILE = "lin_tianji_bazi_structural_v1-exp"
ZIWEI_STRUCTURAL_PROFILE = "lin_tianji_ziwei_structural_v1-exp"
STRUCTURAL_PROFILE_VERSION = "lin_tianji_structural_v1-exp"

SCOPE_ORDER = ("decadal", "yearly", "monthly", "daily", "hourly")

BAZI_TEN_GOD_MAPPING = {
    "比肩": {"primary_domain": "peers", "event_family_support": ("peer_alignment", "self_assertion")},
    "劫財": {"primary_domain": "peers", "event_family_support": ("resource_competition", "peer_exchange")},
    "食神": {"primary_domain": "expression", "event_family_support": ("creative_output", "sustained_delivery")},
    "傷官": {"primary_domain": "expression", "event_family_support": ("communication_visibility", "rule_friction")},
    "偏財": {"primary_domain": "finance", "event_family_support": ("variable_income", "commercial_opportunity")},
    "正財": {"primary_domain": "finance", "event_family_support": ("earned_income", "resource_management")},
    "七殺": {"primary_domain": "career", "event_family_support": ("authority_pressure", "role_change")},
    "正官": {"primary_domain": "career", "event_family_support": ("formal_role", "responsibility")},
    "偏印": {"primary_domain": "learning_support", "event_family_support": ("specialized_learning", "unconventional_support")},
    "正印": {"primary_domain": "learning_support", "event_family_support": ("formal_learning", "institutional_support")},
}

ZIWEI_PALACE_MAPPING = {
    "命宮": {"primary_domain": "self", "event_family_support": ("identity_direction",)},
    "兄弟宮": {"primary_domain": "peers", "event_family_support": ("peer_relations",)},
    "夫妻宮": {"primary_domain": "partnership", "event_family_support": ("close_partnership",)},
    "子女宮": {"primary_domain": "children_creation", "event_family_support": ("children_creation",)},
    "財帛宮": {"primary_domain": "finance", "event_family_support": ("income_assets",)},
    "疾厄宮": {"primary_domain": "health", "event_family_support": ("health_load",)},
    "遷移宮": {"primary_domain": "mobility_external", "event_family_support": ("movement_external",)},
    "交友宮": {"primary_domain": "social_network", "event_family_support": ("social_network",)},
    "官祿宮": {"primary_domain": "career", "event_family_support": ("career_role",)},
    "田宅宮": {"primary_domain": "home_property", "event_family_support": ("home_property",)},
    "福德宮": {"primary_domain": "wellbeing", "event_family_support": ("inner_wellbeing",)},
    "父母宮": {"primary_domain": "family_support", "event_family_support": ("family_support",)},
}

FLOWING_STAR_CATEGORY_FAMILY = {
    "soft": "support_or_coordination",
    "lucun": "resource_accumulation",
    "tough": "pressure_or_friction",
    "tianma": "movement_or_change",
    "flower": "relationship_visibility",
    "helper": "support_or_resolution",
}

TRANSFORMATION_FAMILY = {
    "祿": "resource_or_attraction",
    "權": "responsibility_or_control",
    "科": "recognition_or_mediation",
    "忌": "constraint_or_friction",
}

RELATION_STRENGTH = {
    "decadal_boundary": "strong",
    "sui_yun_bing_lin": "strong",
    "natal_pillar_repeat": "strong",
    "branch_clash_natal": "strong",
    "branch_clash_decadal": "strong",
    "completes_three_harmony": "strong",
    "completes_three_meeting": "strong",
    "completes_three_punishment": "strong",
    "branch_six_harmony": "moderate",
    "partial_three_harmony": "moderate",
    "partial_three_meeting": "moderate",
    "branch_punishment_support": "moderate",
    "branch_repeat": "moderate",
    "stem_combination": "moderate",
    "branch_harm": "weak",
    "branch_break": "weak",
    "stem_repeat": "weak",
}

RELATION_EVENT_FAMILY = {
    "natal_pillar_repeat": "recurrence_or_reactivation",
    "branch_repeat": "recurrence_or_reactivation",
    "stem_repeat": "recurrence_or_reactivation",
    "branch_clash_natal": "friction_or_change",
    "branch_clash_decadal": "friction_or_change",
    "branch_punishment_support": "friction_or_change",
    "completes_three_punishment": "friction_or_change",
    "branch_harm": "friction_or_change",
    "branch_break": "friction_or_change",
    "branch_six_harmony": "alignment_or_binding",
    "stem_combination": "alignment_or_binding",
    "partial_three_harmony": "alignment_or_binding",
    "partial_three_meeting": "alignment_or_binding",
    "completes_three_harmony": "structure_formation",
    "completes_three_meeting": "structure_formation",
    "sui_yun_bing_lin": "amplified_repetition",
    "decadal_boundary": "recurrence_or_reactivation",
}

_STRENGTH_ORDER = {
    "unspecified": 0,
    "weak": 1,
    "moderate": 2,
    "strong": 3,
}


def role_for_scope(scope: str, target_scope: str) -> str:
    """Return the Phase 3 role implied by structural time granularity."""

    if scope not in SCOPE_ORDER:
        raise ValueError("unsupported structural scope: %s" % scope)
    if target_scope not in SCOPE_ORDER:
        raise ValueError("unsupported structural target scope: %s" % target_scope)
    scope_index = SCOPE_ORDER.index(scope)
    target_index = SCOPE_ORDER.index(target_scope)
    if scope_index == target_index:
        return "target_evidence"
    if scope_index < target_index:
        return "modifier"
    return "timing_trigger"


def strongest_relation_class(relation_families) -> str:
    """Return the strongest closed activation class, or unspecified."""

    strongest = "unspecified"
    for family in relation_families:
        if family not in RELATION_STRENGTH:
            raise ValueError("unsupported structural relation family: %s" % family)
        candidate = RELATION_STRENGTH[family]
        if _STRENGTH_ORDER[candidate] > _STRENGTH_ORDER[strongest]:
            strongest = candidate
    return strongest
