#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MingStack 紫微流月定位引擎 v1.0.0。

範圍只包含：
- 流年斗君
- 流月命宮
- 流月十二宮重排
- 一般農曆月邊界
- 閏月拆半規則

不包含：
- 紫微流日
- 紫微流時
- 流月四化
- 流月流曜
- 國曆轉農曆

所有輸出均屬 MingStack 的 Project 推導盤面，不是 Astralium 或其他第三方
排盤系統的直接輸出。
"""

from __future__ import annotations

import argparse
import json

ENGINE_NAME = "MingStack 紫微流月定位引擎"
ENGINE_VERSION = "1.0.0"
RULE_NAME = "斗君流月"

ZHI = tuple("子丑寅卯辰巳午未申酉戌亥")
PALACE_NAMES = (
    "命宮",
    "兄弟宮",
    "夫妻宮",
    "子女宮",
    "財帛宮",
    "疾厄宮",
    "遷移宮",
    "交友宮",
    "官祿宮",
    "田宅宮",
    "福德宮",
    "父母宮",
)

MONTH_BOUNDARY = "農曆初一；閏月採初一至十五歸原月、十六起歸下一月"
BOUNDARY_NOTE = (
    "紫微流月採農曆月，八字流月採節氣月；兩者在同一國曆日期可能落在不同月份，"
    "這是 MingStack 的設計差異，不是 bug。閏月另依本引擎固定的拆半規則處理。"
)


def _validate_month(month: int) -> None:
    if not 1 <= month <= 12:
        raise ValueError("農曆月必須介於 1 到 12")


def _validate_day(day: int) -> None:
    if not 1 <= day <= 30:
        raise ValueError("農曆日必須介於 1 到 30")


def _validate_branch(branch: str) -> None:
    if branch not in ZHI:
        raise ValueError("地支必須為：" + "、".join(ZHI))


def effective_lunar_month(lunar_month: int, lunar_day: int, is_leap_month: bool) -> int:
    """依 MingStack v1 邊界規則取得流月定位所使用的有效月份。"""
    _validate_month(lunar_month)
    _validate_day(lunar_day)
    if not is_leap_month:
        return lunar_month
    if lunar_day <= 15:
        return lunar_month
    return 1 if lunar_month == 12 else lunar_month + 1


def annual_doujun_branch(
    birth_lunar_month: int,
    birth_hour_branch: str,
    flow_year_branch: str,
) -> str:
    """依斗君法計算目標流年的正月流月命宮地支。"""
    _validate_month(birth_lunar_month)
    _validate_branch(birth_hour_branch)
    _validate_branch(flow_year_branch)

    year_idx = ZHI.index(flow_year_branch)
    birth_hour_idx = ZHI.index(birth_hour_branch)

    # 以流年地支所在宮起正月，逆數到出生月，再由該宮起子時順數到出生時辰。
    doujun_idx = (year_idx - (birth_lunar_month - 1) + birth_hour_idx) % 12
    return ZHI[doujun_idx]


def flow_month_ming_branch(
    birth_lunar_month: int,
    birth_hour_branch: str,
    flow_year_branch: str,
    lunar_month: int,
    lunar_day: int,
    is_leap_month: bool,
) -> str:
    """計算指定農曆月份的流月命宮地支。"""
    doujun = annual_doujun_branch(
        birth_lunar_month=birth_lunar_month,
        birth_hour_branch=birth_hour_branch,
        flow_year_branch=flow_year_branch,
    )
    effective_month = effective_lunar_month(lunar_month, lunar_day, is_leap_month)
    ming_idx = (ZHI.index(doujun) + (effective_month - 1)) % 12
    return ZHI[ming_idx]


def flow_month_palaces(ming_branch: str) -> dict[str, str]:
    """由流月命宮地支重排紫微十二宮。"""
    _validate_branch(ming_branch)
    ming_idx = ZHI.index(ming_branch)
    return {
        palace: ZHI[(ming_idx - offset) % 12]
        for offset, palace in enumerate(PALACE_NAMES)
    }


def project_derived_ziwei_month(
    birth_lunar_month: int,
    birth_hour_branch: str,
    flow_year_branch: str,
    lunar_month: int,
    lunar_day: int,
    is_leap_month: bool,
) -> dict:
    """產生可記錄到問事流程的 Project 紫微流月結果。"""
    doujun = annual_doujun_branch(
        birth_lunar_month=birth_lunar_month,
        birth_hour_branch=birth_hour_branch,
        flow_year_branch=flow_year_branch,
    )
    effective_month = effective_lunar_month(lunar_month, lunar_day, is_leap_month)
    ming_branch = flow_month_ming_branch(
        birth_lunar_month=birth_lunar_month,
        birth_hour_branch=birth_hour_branch,
        flow_year_branch=flow_year_branch,
        lunar_month=lunar_month,
        lunar_day=lunar_day,
        is_leap_month=is_leap_month,
    )
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "classification": "Project 推導盤面",
        "scope": "紫微流月",
        "rule": RULE_NAME,
        "month_boundary": MONTH_BOUNDARY,
        "boundary_note": BOUNDARY_NOTE,
        "inputs": {
            "birth_lunar_month": birth_lunar_month,
            "birth_hour_branch": birth_hour_branch,
            "flow_year_branch": flow_year_branch,
            "lunar_month": lunar_month,
            "lunar_day": lunar_day,
            "is_leap_month": is_leap_month,
        },
        "annual_doujun_branch": doujun,
        "effective_lunar_month": effective_month,
        "flow_month_ming_branch": ming_branch,
        "flow_month_palaces": flow_month_palaces(ming_branch),
        "features": {
            "flow_month_enabled": True,
            "flow_day_enabled": False,
            "flow_hour_enabled": False,
            "monthly_four_transformations_enabled": False,
            "monthly_flowing_stars_enabled": False,
        },
        "source_note": "此結果為 MingStack 依固定斗君算法推導，不是 Astralium 原始資料直接輸出。",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=f"{ENGINE_NAME} v{ENGINE_VERSION}")
    parser.add_argument("--birth-lunar-month", type=int, required=True, help="出生農曆月 1-12")
    parser.add_argument("--birth-hour-branch", required=True, help="出生時辰地支，例如 戌")
    parser.add_argument("--flow-year-branch", required=True, help="目標流年地支，例如 酉")
    parser.add_argument("--lunar-month", type=int, required=True, help="目標農曆月 1-12")
    parser.add_argument("--lunar-day", type=int, required=True, help="目標農曆日 1-30")
    parser.add_argument("--leap", action="store_true", help="目標月份是否為閏月")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    result = project_derived_ziwei_month(
        birth_lunar_month=args.birth_lunar_month,
        birth_hour_branch=args.birth_hour_branch,
        flow_year_branch=args.flow_year_branch,
        lunar_month=args.lunar_month,
        lunar_day=args.lunar_day,
        is_leap_month=args.leap,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))


if __name__ == "__main__":
    main()
