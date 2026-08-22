from __future__ import annotations

from typing import Tuple

from engine.calendar.sexagenary import FIRST_MONTH_STEM, GAN

from .common import PALACE_NAMES, ZHI, palaces_from_ming_branch, validate_branch, validate_month
from .natal_models import ZiweiPalaceRecord
from .transformation_profiles import LEGAL_STEMS


_BUREAU_BY_INDEX = ("木三局", "金四局", "水二局", "火六局", "土五局")


def resolve_ming_body_branches(lunar_month: int, hour_branch: str) -> Tuple[str, str]:
    """Resolve Ming/Body branches using the pinned common Ziwei profile.

    This mirrors the pinned iztro contract: 寅 is palace index 0, the effective
    lunar month is counted forward, and the birth hour branch is counted
    backward for Ming / forward for Body.
    """
    validate_month(lunar_month)
    validate_branch(hour_branch)

    month_index = lunar_month - 1
    hour_index = ZHI.index(hour_branch)
    ming_palace_index = (month_index - hour_index) % 12
    body_palace_index = (month_index + hour_index) % 12
    yin_branch_index = ZHI.index("寅")
    return (
        ZHI[(ming_palace_index + yin_branch_index) % 12],
        ZHI[(body_palace_index + yin_branch_index) % 12],
    )


def _palace_stem_for_branch(birth_year_stem: str, branch: str) -> str:
    if birth_year_stem not in FIRST_MONTH_STEM or birth_year_stem not in LEGAL_STEMS:
        raise ValueError("invalid birth-year heavenly stem")
    validate_branch(branch)
    start_index = GAN.index(FIRST_MONTH_STEM[birth_year_stem])
    palace_offset = (ZHI.index(branch) - ZHI.index("寅")) % 12
    return GAN[(start_index + palace_offset) % 10]


def resolve_palace_stems(birth_year_stem: str, ming_branch: str) -> Tuple[ZiweiPalaceRecord, ...]:
    if birth_year_stem not in LEGAL_STEMS:
        raise ValueError("invalid birth-year heavenly stem")
    validate_branch(ming_branch)

    branches_by_palace = palaces_from_ming_branch(ming_branch)
    records = []
    for palace in PALACE_NAMES:
        branch = branches_by_palace[palace]
        stem = _palace_stem_for_branch(birth_year_stem, branch)
        records.append(
            ZiweiPalaceRecord(
                name=palace,
                branch=branch,
                heavenly_stem=stem,
                stem_branch=stem + branch,
            )
        )
    return tuple(records)


def resolve_five_element_bureau(ming_stem: str, ming_branch: str) -> str:
    """Resolve the five-element bureau from Ming palace stem/branch.

    Number mapping follows the pinned iztro profile:
    stem pairs -> 1..5; branch pairs within a six-branch cycle -> 1..3;
    sum is reduced modulo five and mapped to 木三/金四/水二/火六/土五.
    """
    if ming_stem not in LEGAL_STEMS:
        raise ValueError("invalid Ming palace heavenly stem")
    validate_branch(ming_branch)

    heavenly_stem_number = LEGAL_STEMS.index(ming_stem) // 2 + 1
    earthly_branch_number = (ZHI.index(ming_branch) % 6) // 2 + 1
    index = heavenly_stem_number + earthly_branch_number
    while index > 5:
        index -= 5
    return _BUREAU_BY_INDEX[index - 1]
