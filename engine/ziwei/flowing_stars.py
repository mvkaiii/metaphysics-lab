from __future__ import annotations

from typing import Dict, Tuple

from engine.calendar.sexagenary import GAN, ZHI

from .errors import ZiweiFlowingStarError
from .flowing_star_models import (
    FlowingStarLayer,
    FlowingStarPlacement,
    FlowingStarProfile,
    FlowingStarSource,
    SUPPORTED_FLOWING_STAR_SCOPES,
)
from .models import LayerIdentity, LayerProvenance
from .natal_stars import place_kui_yue, place_lucun_yang_tuo, place_tianma


FLOWING_STAR_PROFILE_ID = "ziwei-flowing-stars-common-v1"
FLOWING_STAR_RULE_VERSION = "1.0-exp"
FLOWING_STAR_QUALIFICATION_TARGET = "iztro-2.6.0-814b77e6"

FLOWING_STAR_CATALOG = (
    "天魁",
    "天鉞",
    "文昌",
    "文曲",
    "祿存",
    "擎羊",
    "陀羅",
    "天馬",
    "紅鸞",
    "天喜",
)

_STAR_CATEGORIES = {
    "天魁": "soft",
    "天鉞": "soft",
    "文昌": "soft",
    "文曲": "soft",
    "祿存": "lucun",
    "擎羊": "tough",
    "陀羅": "tough",
    "天馬": "tianma",
    "紅鸞": "flower",
    "天喜": "flower",
    "年解": "helper",
}

_CHANG_QU_BY_STEM = {
    "甲": ("巳", "酉"),
    "乙": ("午", "申"),
    "丙": ("申", "午"),
    "丁": ("酉", "巳"),
    "戊": ("申", "午"),
    "己": ("酉", "巳"),
    "庚": ("亥", "卯"),
    "辛": ("子", "寅"),
    "壬": ("寅", "子"),
    "癸": ("卯", "亥"),
}

_LUAN_XI_BY_BRANCH = {
    "子": ("卯", "酉"),
    "丑": ("寅", "申"),
    "寅": ("丑", "未"),
    "卯": ("子", "午"),
    "辰": ("亥", "巳"),
    "巳": ("戌", "辰"),
    "午": ("酉", "卯"),
    "未": ("申", "寅"),
    "申": ("未", "丑"),
    "酉": ("午", "子"),
    "戌": ("巳", "亥"),
    "亥": ("辰", "戌"),
}

_NIANJIE_BY_BRANCH = {
    "子": "戌",
    "丑": "酉",
    "寅": "申",
    "卯": "未",
    "辰": "午",
    "巳": "巳",
    "午": "辰",
    "未": "卯",
    "申": "寅",
    "酉": "丑",
    "戌": "子",
    "亥": "亥",
}


def _raise(code, message, details=None):
    raise ZiweiFlowingStarError(code, message, details)


def _validate_stem(stem: str) -> None:
    if stem not in GAN:
        _raise("invalid_flowing_star_stem", "invalid flowing-star heavenly stem", {"stem": stem})


def _validate_branch(branch: str) -> None:
    if branch not in ZHI:
        _raise("invalid_flowing_star_branch", "invalid flowing-star earthly branch", {"branch": branch})


def _validate_scope(scope: str) -> None:
    if scope not in SUPPORTED_FLOWING_STAR_SCOPES:
        _raise("unsupported_flowing_star_scope", "unsupported flowing-star scope", {"scope": scope})


def _provenance(profile_id: str) -> LayerProvenance:
    return LayerProvenance(
        "project_derived",
        "Metaphysics Lab",
        None,
        profile_id,
        FLOWING_STAR_RULE_VERSION,
        "engine.ziwei.flowing_stars",
    )


def get_flowing_star_profile() -> FlowingStarProfile:
    return FlowingStarProfile(
        FLOWING_STAR_PROFILE_ID,
        FLOWING_STAR_RULE_VERSION,
        "earthly_branch",
        FLOWING_STAR_QUALIFICATION_TARGET,
    )


def place_chang_qu_by_stem(stem: str) -> Dict[str, str]:
    _validate_stem(stem)
    chang, qu = _CHANG_QU_BY_STEM[stem]
    return {"文昌": chang, "文曲": qu}


def place_luan_xi(branch: str) -> Dict[str, str]:
    _validate_branch(branch)
    luan, xi = _LUAN_XI_BY_BRANCH[branch]
    return {"紅鸞": luan, "天喜": xi}


def place_nianjie(branch: str) -> Dict[str, str]:
    _validate_branch(branch)
    return {"年解": _NIANJIE_BY_BRANCH[branch]}


def place_flowing_stars_for_pair(
    scope: str,
    stem: str,
    branch: str,
    profile_id: str = FLOWING_STAR_PROFILE_ID,
) -> Tuple[FlowingStarPlacement, ...]:
    _validate_scope(scope)
    _validate_stem(stem)
    _validate_branch(branch)
    if profile_id != FLOWING_STAR_PROFILE_ID:
        _raise(
            "invalid_flowing_star_layer",
            "unsupported flowing-star profile",
            {"profile_id": profile_id},
        )

    by_star = {}
    for family in (
        place_kui_yue(stem),
        place_chang_qu_by_stem(stem),
        place_lucun_yang_tuo(stem),
        place_tianma(branch),
        place_luan_xi(branch),
    ):
        for star, target in family.items():
            if star in by_star:
                _raise("duplicate_flowing_star_identity", "duplicate flowing-star placement", {"star": star})
            by_star[star] = target

    order = FLOWING_STAR_CATALOG + (("年解",) if scope == "yearly" else ())
    if scope == "yearly":
        by_star.update(place_nianjie(branch))

    provenance = _provenance(profile_id)
    return tuple(
        FlowingStarPlacement(
            base_star=star,
            category=_STAR_CATEGORIES[star],
            scope=scope,
            target_branch=by_star[star],
            sequence=index + 1,
            provenance=provenance,
        )
        for index, star in enumerate(order)
    )


def build_flowing_star_layer(
    source: FlowingStarSource,
    profile_id: str = FLOWING_STAR_PROFILE_ID,
) -> FlowingStarLayer:
    if not isinstance(source, FlowingStarSource):
        _raise("missing_cycle_stem_source", "flowing-star layer requires FlowingStarSource")
    if profile_id != FLOWING_STAR_PROFILE_ID:
        _raise(
            "invalid_flowing_star_layer",
            "unsupported flowing-star profile",
            {"profile_id": profile_id},
        )

    placements = place_flowing_stars_for_pair(
        source.scope,
        source.heavenly_stem,
        source.earthly_branch,
        profile_id,
    )
    identity = LayerIdentity(
        source.chart_identity.chart_id,
        source.scope,
        source.reference,
        profile_id,
    )
    return FlowingStarLayer(
        identity=identity,
        source=source,
        placements=placements,
        profile_id=profile_id,
        rule_version=FLOWING_STAR_RULE_VERSION,
        classification="Project 推導盤面",
        maturity="experimental",
        validation=source.validation_status,
        provenance=_provenance(profile_id),
    )
