"""Metaphysics Lab 紫微時間模組共用基礎。"""
from __future__ import annotations

ZHI = tuple("子丑寅卯辰巳午未申酉戌亥")
PALACE_NAMES = (
    "命宮", "兄弟宮", "夫妻宮", "子女宮", "財帛宮", "疾厄宮",
    "遷移宮", "交友宮", "官祿宮", "田宅宮", "福德宮", "父母宮",
)


def validate_month(month: int) -> None:
    if not 1 <= month <= 12:
        raise ValueError("農曆月必須介於 1 到 12")


def validate_day(day: int) -> None:
    if not 1 <= day <= 30:
        raise ValueError("農曆日必須介於 1 到 30")


def validate_branch(branch: str) -> None:
    if branch not in ZHI:
        raise ValueError("地支必須為：" + "、".join(ZHI))


def validate_palace(palace: str) -> None:
    if palace not in PALACE_NAMES:
        raise ValueError("宮位必須為：" + "、".join(PALACE_NAMES))


def palaces_from_ming_branch(ming_branch: str) -> dict[str, str]:
    """以指定命宮地支重排十二宮。"""
    validate_branch(ming_branch)
    ming_idx = ZHI.index(ming_branch)
    return {
        palace: ZHI[(ming_idx - offset) % 12]
        for offset, palace in enumerate(PALACE_NAMES)
    }
