#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Metaphysics Lab 紫微流時定位模組 v1.0.0-exp。"""
from __future__ import annotations

import argparse
import json

from .capabilities import get_capability
from .common import ZHI, palaces_from_ming_branch, validate_branch
from .day import flow_day_ming_branch
from .month import effective_lunar_month, flow_month_ming_branch

ENGINE_NAME = "Metaphysics Lab 紫微流時定位引擎"
ENGINE_VERSION = "1.0.0-exp"
RULE_NAME = "流日命宮起子時順行一時辰一宮"
CAPABILITY_ID = "ziwei.flow_hour_palaces"
SOURCE_NOTE = (
    "流時定位採『流日命宮起子時，之後每時辰順行一宮』；"
    "已與 iztro 固定程式版本及獨立公開文字排法資料交叉比對。"
)


def flow_hour_ming_branch(
    birth_lunar_month: int,
    birth_hour_branch: str,
    flow_year_branch: str,
    lunar_month: int,
    lunar_day: int,
    is_leap_month: bool,
    hour_branch: str,
) -> str:
    """Resolve the flow-hour Life Palace branch for a trusted lunar date/hour branch."""
    validate_branch(hour_branch)
    day_branch = flow_day_ming_branch(
        birth_lunar_month,
        birth_hour_branch,
        flow_year_branch,
        lunar_month,
        lunar_day,
        is_leap_month,
    )
    return ZHI[(ZHI.index(day_branch) + ZHI.index(hour_branch)) % 12]


def flow_hour_palaces(ming_branch: str) -> dict[str, str]:
    """Return the twelve flow-hour palaces anchored at the hour Life Palace."""
    return palaces_from_ming_branch(ming_branch)


def project_derived_ziwei_hour(
    birth_lunar_month: int,
    birth_hour_branch: str,
    flow_year_branch: str,
    lunar_month: int,
    lunar_day: int,
    is_leap_month: bool,
    hour_branch: str,
) -> dict:
    """Return structured Project-derived Ziwei flow-hour placement."""
    validate_branch(hour_branch)
    capability = get_capability(CAPABILITY_ID)
    effective_month = effective_lunar_month(lunar_month, lunar_day, is_leap_month)
    month_branch = flow_month_ming_branch(
        birth_lunar_month,
        birth_hour_branch,
        flow_year_branch,
        lunar_month,
        lunar_day,
        is_leap_month,
    )
    day_branch = flow_day_ming_branch(
        birth_lunar_month,
        birth_hour_branch,
        flow_year_branch,
        lunar_month,
        lunar_day,
        is_leap_month,
    )
    hour_ming_branch = flow_hour_ming_branch(
        birth_lunar_month,
        birth_hour_branch,
        flow_year_branch,
        lunar_month,
        lunar_day,
        is_leap_month,
        hour_branch,
    )
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "classification": "Project 推導盤面",
        "scope": "紫微流時",
        "rule": RULE_NAME,
        "capability": capability,
        "inputs": {
            "birth_lunar_month": birth_lunar_month,
            "birth_hour_branch": birth_hour_branch,
            "flow_year_branch": flow_year_branch,
            "lunar_month": lunar_month,
            "lunar_day": lunar_day,
            "is_leap_month": is_leap_month,
            "hour_branch": hour_branch,
        },
        "effective_lunar_month": effective_month,
        "flow_month_ming_branch": month_branch,
        "flow_day_ming_branch": day_branch,
        "flow_hour_ming_branch": hour_ming_branch,
        "flow_hour_palaces": flow_hour_palaces(hour_ming_branch),
        "features": {
            "flow_hour_implemented": True,
            "flow_hour_default_routing": False,
            "hourly_four_transformations_implemented": False,
            "hourly_flowing_stars_implemented": False,
            "fine_flying_implemented": False,
            "calendar_resolver_implemented": True,
        },
        "source_note": SOURCE_NOTE,
        "confidence_note": (
            "此 capability 第一版為 Experimental / On-demand；可執行並累積驗證，"
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
    parser.add_argument("--hour-branch", required=True, help="已解析的目標時辰地支，例如 丑")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    result = project_derived_ziwei_hour(
        birth_lunar_month=args.birth_lunar_month,
        birth_hour_branch=args.birth_hour_branch,
        flow_year_branch=args.flow_year_branch,
        lunar_month=args.lunar_month,
        lunar_day=args.lunar_day,
        is_leap_month=args.leap,
        hour_branch=args.hour_branch,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))


if __name__ == "__main__":
    main()
