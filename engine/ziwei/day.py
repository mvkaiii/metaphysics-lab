#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Metaphysics Lab 紫微流日定位模組 v1.0.0-exp。"""
from __future__ import annotations

import argparse
import json

from .capabilities import get_capability
from .common import ZHI, palaces_from_ming_branch, validate_day
from .month import effective_lunar_month, flow_month_ming_branch

ENGINE_NAME = "Metaphysics Lab 紫微流日定位引擎"
ENGINE_VERSION = "1.0.0-exp"
RULE_NAME = "流月命宮起初一順行一日一宮"
CAPABILITY_ID = "ziwei.flow_day_palaces"
DAY_BOUNDARY = "以可信農曆來源提供的目標農曆日為準；本模組不負責國曆轉農曆"
LEAP_MONTH_NOTE = (
    "閏月先依 Project 流月規則切分：初一至十五歸原月、十六起歸下一有效月；"
    "再以實際農曆日數 lunar_day-1 推流日，不在十六日重置為第一日。"
)
SOURCE_NOTE = (
    "流日定位採『流月所在宮起初一，順行十二宮，一日一宮』；"
    "已與 iztro 公開安星訣/實作及獨立公開排法資料交叉比對。"
)


def flow_day_ming_branch(
    birth_lunar_month: int,
    birth_hour_branch: str,
    flow_year_branch: str,
    lunar_month: int,
    lunar_day: int,
    is_leap_month: bool,
) -> str:
    """Resolve the flow-day Life Palace branch for a trusted lunar date."""
    validate_day(lunar_day)
    month_branch = flow_month_ming_branch(
        birth_lunar_month=birth_lunar_month,
        birth_hour_branch=birth_hour_branch,
        flow_year_branch=flow_year_branch,
        lunar_month=lunar_month,
        lunar_day=lunar_day,
        is_leap_month=is_leap_month,
    )
    return ZHI[(ZHI.index(month_branch) + lunar_day - 1) % 12]


def flow_day_palaces(ming_branch: str) -> dict[str, str]:
    """Return the twelve flow-day palaces anchored at the day Life Palace."""
    return palaces_from_ming_branch(ming_branch)


def project_derived_ziwei_day(
    birth_lunar_month: int,
    birth_hour_branch: str,
    flow_year_branch: str,
    lunar_month: int,
    lunar_day: int,
    is_leap_month: bool,
) -> dict:
    """Return structured Project-derived Ziwei flow-day placement."""
    capability = get_capability(CAPABILITY_ID)
    effective_month = effective_lunar_month(lunar_month, lunar_day, is_leap_month)
    month_branch = flow_month_ming_branch(
        birth_lunar_month=birth_lunar_month,
        birth_hour_branch=birth_hour_branch,
        flow_year_branch=flow_year_branch,
        lunar_month=lunar_month,
        lunar_day=lunar_day,
        is_leap_month=is_leap_month,
    )
    day_branch = flow_day_ming_branch(
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
        "scope": "紫微流日",
        "rule": RULE_NAME,
        "capability": capability,
        "day_boundary": DAY_BOUNDARY,
        "leap_month_note": LEAP_MONTH_NOTE,
        "inputs": {
            "birth_lunar_month": birth_lunar_month,
            "birth_hour_branch": birth_hour_branch,
            "flow_year_branch": flow_year_branch,
            "lunar_month": lunar_month,
            "lunar_day": lunar_day,
            "is_leap_month": is_leap_month,
        },
        "effective_lunar_month": effective_month,
        "flow_month_ming_branch": month_branch,
        "flow_day_ming_branch": day_branch,
        "flow_day_palaces": flow_day_palaces(day_branch),
        "features": {
            "flow_day_implemented": True,
            "flow_day_default_routing": False,
            "flow_hour_implemented": True,
            "flow_hour_default_routing": False,
            "daily_four_transformations_implemented": False,
            "daily_flowing_stars_implemented": False,
            "fine_flying_implemented": False,
        },
        "source_note": SOURCE_NOTE,
        "confidence_note": (
            "此 capability 目前為 Experimental / On-demand；可執行與驗證，"
            "但分析時需降權，不能單獨支撐高度確信結論。"
        ),
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
    result = project_derived_ziwei_day(
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
