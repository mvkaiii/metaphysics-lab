#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MingStack - Project Bazi Calendar Engine v1.0.0

自包含的八字時間推導參考實作。

範圍：
- 以立春作為流年切換
- 以十二節作為流月切換並套用五虎遁
- 以 Julian Day Number 對應流日
- 23:00 換日
- 以五鼠遁推導流時
- 天干十神映射

重要：
- 本程式輸出屬於 Project 推導盤面，不是 Astralium 輸出。
- 節氣時間使用簡化太陽視黃經近似公式，適合一般流月判定；若目標時間距離節氣交界 15 分鐘內，應再用權威星曆覆核。
- 不需要第三方 Python 套件。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import argparse
import json
import math
from zoneinfo import ZoneInfo

ENGINE_NAME = "Project Bazi Calendar Engine"
ENGINE_VERSION = "1.0.0"
REFERENCE_ENGINE = "6tail/lunar-python v1.4.8 (commit 000c8a3)"
DAY_ROLLOVER = "23:00"
SOLAR_TERM_BOUNDARY_CAUTION_MINUTES = 15

GAN = tuple("甲乙丙丁戊己庚辛壬癸")
ZHI = tuple("子丑寅卯辰巳午未申酉戌亥")

JIE = (
    ("小寒", 285.0, 1, 5),
    ("立春", 315.0, 2, 4),
    ("驚蟄", 345.0, 3, 5),
    ("清明", 15.0, 4, 5),
    ("立夏", 45.0, 5, 5),
    ("芒種", 75.0, 6, 6),
    ("小暑", 105.0, 7, 7),
    ("立秋", 135.0, 8, 7),
    ("白露", 165.0, 9, 7),
    ("寒露", 195.0, 10, 8),
    ("立冬", 225.0, 11, 7),
    ("大雪", 255.0, 12, 7),
)
JIE_MAP = {name: (lon, month, day) for name, lon, month, day in JIE}

STEM_INFO = {
    "甲": ("木", True), "乙": ("木", False),
    "丙": ("火", True), "丁": ("火", False),
    "戊": ("土", True), "己": ("土", False),
    "庚": ("金", True), "辛": ("金", False),
    "壬": ("水", True), "癸": ("水", False),
}
GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


class BaziCalendarError(ValueError):
    pass


def _require_aware(dt: datetime) -> None:
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise BaziCalendarError("datetime 必須包含時區資訊，例如 ZoneInfo('Asia/Taipei')")


def _gregorian_jdn(year: int, month: int, day: int) -> int:
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    return day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045


def _jd_from_datetime(dt: datetime) -> float:
    _require_aware(dt)
    u = dt.astimezone(timezone.utc)
    y, m = u.year, u.month
    d = u.day + (u.hour + (u.minute + (u.second + u.microsecond / 1e6) / 60.0) / 60.0) / 24.0
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    return (
        math.floor(365.25 * (y + 4716))
        + math.floor(30.6001 * (m + 1))
        + d + b - 1524.5
    )


def _datetime_from_jd(jd: float) -> datetime:
    z = int(jd + 0.5)
    f = jd + 0.5 - z
    if z < 2299161:
        a = z
    else:
        alpha = int((z - 1867216.25) / 36524.25)
        a = z + 1 + alpha - alpha // 4
    b = a + 1524
    c = int((b - 122.1) / 365.25)
    d = int(365.25 * c)
    e = int((b - d) / 30.6001)
    day_float = b - d - int(30.6001 * e) + f
    month = e - 1 if e < 14 else e - 13
    year = c - 4716 if month > 2 else c - 4715
    day = int(day_float)
    seconds = round((day_float - day) * 86400)
    base = datetime(year, month, day, tzinfo=timezone.utc)
    return base + timedelta(seconds=seconds)


def _sun_apparent_longitude(jd: float) -> float:
    t = (jd - 2451545.0) / 36525.0
    mean_long = (280.46646 + t * (36000.76983 + t * 0.0003032)) % 360.0
    mean_anom = 357.52911 + t * (35999.05029 - 0.0001537 * t)
    mr = math.radians(mean_anom)
    center = (
        math.sin(mr) * (1.914602 - t * (0.004817 + 0.000014 * t))
        + math.sin(2 * mr) * (0.019993 - 0.000101 * t)
        + math.sin(3 * mr) * 0.000289
    )
    true_long = (mean_long + center) % 360.0
    omega = 125.04 - 1934.136 * t
    return (true_long - 0.00569 - 0.00478 * math.sin(math.radians(omega))) % 360.0


def _angle_diff(angle: float, target: float) -> float:
    return ((angle - target + 180.0) % 360.0) - 180.0


def solar_term_time(year: int, term: str, tz: str | ZoneInfo = "Asia/Taipei") -> datetime:
    if term not in JIE_MAP:
        raise BaziCalendarError(f"不支援的節：{term}；可用：{', '.join(JIE_MAP)}")
    zone = ZoneInfo(tz) if isinstance(tz, str) else tz
    target, month, day_guess = JIE_MAP[term]
    center_local = datetime(year, month, day_guess, 12, 0, tzinfo=zone)
    lo = _jd_from_datetime(center_local - timedelta(days=3))
    hi = _jd_from_datetime(center_local + timedelta(days=3))

    step = 1.0 / 24.0
    x0 = lo
    f0 = _angle_diff(_sun_apparent_longitude(x0), target)
    bracket = None
    x = lo + step
    while x <= hi + 1e-12:
        f = _angle_diff(_sun_apparent_longitude(x), target)
        if f0 <= 0.0 <= f and abs(f - f0) < 5.0:
            bracket = (x0, x)
            break
        x0, f0 = x, f
        x += step
    if bracket is None:
        raise BaziCalendarError(f"找不到 {year} {term} 的太陽黃經交點")

    a, b = bracket
    for _ in range(60):
        mid = (a + b) / 2.0
        fm = _angle_diff(_sun_apparent_longitude(mid), target)
        if fm >= 0:
            b = mid
        else:
            a = mid
    return _datetime_from_jd((a + b) / 2.0).astimezone(zone)


def _lichun(dt: datetime) -> datetime:
    _require_aware(dt)
    return solar_term_time(dt.year, "立春", dt.tzinfo)  # type: ignore[arg-type]


def flow_year_pillar(dt: datetime) -> str:
    _require_aware(dt)
    pillar_year = dt.year if dt >= _lichun(dt) else dt.year - 1
    return GAN[(pillar_year - 4) % 10] + ZHI[(pillar_year - 4) % 12]


def _month_index(dt: datetime) -> int:
    _require_aware(dt)
    zone = dt.tzinfo
    boundaries = [(name, solar_term_time(dt.year, name, zone)) for name, *_ in JIE]  # type: ignore[arg-type]

    latest_pos = None
    for pos, (_, boundary) in enumerate(boundaries):
        if dt >= boundary:
            latest_pos = pos
        else:
            break

    if latest_pos is None:
        return 10
    if latest_pos == 0:
        return 11
    return latest_pos - 1


def flow_month_pillar(dt: datetime) -> str:
    _require_aware(dt)
    year_pillar = flow_year_pillar(dt)
    year_gan_idx = GAN.index(year_pillar[0])
    month_idx = _month_index(dt)
    start_gan_idx = ((year_gan_idx % 5) * 2 + 2) % 10
    gan_idx = (start_gan_idx + month_idx) % 10
    zhi_idx = (2 + month_idx) % 12
    return GAN[gan_idx] + ZHI[zhi_idx]


def day_pillar(dt: datetime) -> str:
    _require_aware(dt)
    effective = dt + timedelta(days=1) if dt.hour >= 23 else dt
    jdn = _gregorian_jdn(effective.year, effective.month, effective.day)
    offset = jdn - 11
    return GAN[offset % 10] + ZHI[offset % 12]


def time_pillar(dt: datetime) -> str:
    _require_aware(dt)
    day = day_pillar(dt)
    day_gan_idx = GAN.index(day[0])
    zhi_idx = ((dt.hour + 1) // 2) % 12
    gan_idx = (day_gan_idx % 5 * 2 + zhi_idx) % 10
    return GAN[gan_idx] + ZHI[zhi_idx]


def bazi_pillars(dt: datetime) -> tuple[str, str, str, str]:
    return flow_year_pillar(dt), flow_month_pillar(dt), day_pillar(dt), time_pillar(dt)


def ten_god(day_master: str, target_stem: str) -> str:
    if day_master not in STEM_INFO or target_stem not in STEM_INFO:
        raise BaziCalendarError("十神計算僅接受十天干")
    dm_elem, dm_yang = STEM_INFO[day_master]
    tg_elem, tg_yang = STEM_INFO[target_stem]
    same_polarity = dm_yang == tg_yang

    if tg_elem == dm_elem:
        return "比肩" if same_polarity else "劫財"
    if GENERATES[dm_elem] == tg_elem:
        return "食神" if same_polarity else "傷官"
    if CONTROLS[dm_elem] == tg_elem:
        return "偏財" if same_polarity else "正財"
    if CONTROLS[tg_elem] == dm_elem:
        return "七殺" if same_polarity else "正官"
    if GENERATES[tg_elem] == dm_elem:
        return "偏印" if same_polarity else "正印"
    raise AssertionError("unreachable element relation")


def _boundary_warning(dt: datetime) -> dict | None:
    _require_aware(dt)
    candidates = []
    for year in (dt.year - 1, dt.year, dt.year + 1):
        for name, *_ in JIE:
            boundary = solar_term_time(year, name, dt.tzinfo)  # type: ignore[arg-type]
            delta_minutes = abs((dt - boundary).total_seconds()) / 60.0
            candidates.append((delta_minutes, name, boundary))
    delta_minutes, name, boundary = min(candidates, key=lambda x: x[0])
    if delta_minutes > SOLAR_TERM_BOUNDARY_CAUTION_MINUTES:
        return None
    return {
        "needs_external_verification": True,
        "term": name,
        "computed_boundary": boundary.isoformat(),
        "distance_minutes": round(delta_minutes, 3),
        "reason": (
            f"目標時間距 Project 計算的{name}交界少於 "
            f"{SOLAR_TERM_BOUNDARY_CAUTION_MINUTES} 分鐘；請用權威節氣資料交叉確認。"
        ),
    }


def project_derived(dt: datetime, day_master: str | None = None) -> dict:
    year, month, day, time = bazi_pillars(dt)
    result = {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "classification": "Project 推導盤面",
        "reference_engine": REFERENCE_ENGINE,
        "datetime": dt.isoformat(),
        "timezone": str(dt.tzinfo),
        "day_rollover": DAY_ROLLOVER,
        "year": year,
        "month": month,
        "day": day,
        "time": time,
        "solar_term_boundary_caution_minutes": SOLAR_TERM_BOUNDARY_CAUTION_MINUTES,
        "boundary_warning": _boundary_warning(dt),
    }
    if day_master:
        result["ten_gods"] = {
            "year": ten_god(day_master, year[0]),
            "month": ten_god(day_master, month[0]),
            "day": ten_god(day_master, day[0]),
            "time": ten_god(day_master, time[0]),
        }
    return result


def _parse_datetime(value: str, tz_name: str) -> datetime:
    zone = ZoneInfo(tz_name)
    naive = datetime.strptime(value, "%Y-%m-%d %H:%M")
    return naive.replace(tzinfo=zone)


def main() -> None:
    parser = argparse.ArgumentParser(description=f"{ENGINE_NAME} v{ENGINE_VERSION}")
    parser.add_argument("datetime", help='local datetime, e.g. "2026-08-20 17:12"')
    parser.add_argument("--tz", default="Asia/Taipei", help="IANA timezone")
    parser.add_argument("--day-master", help="natal day stem, e.g. 丙")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    dt = _parse_datetime(args.datetime, args.tz)
    print(json.dumps(project_derived(dt, args.day_master), ensure_ascii=False, indent=2 if args.pretty else None))


if __name__ == "__main__":
    main()
