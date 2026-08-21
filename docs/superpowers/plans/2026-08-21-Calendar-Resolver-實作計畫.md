# Calendar Resolver Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立 system-neutral 的 Calendar Resolver v1，將結構化 civil datetime + IANA timezone 正規化為可追溯、可驗證的 `CalendarContext`，並以 Ziwei adapter 對接既有流月／流日／流時 core，同時機械化 `Precision must be earned by input` 與 Gate 0→4 驗證流程。

**Architecture:** 上游先用 pure precision policy 判斷輸入是否足以支撐目標 capability；只有需要完整 civil datetime 的路徑才進 Resolver。Resolver 內部分離 models、pinned timezone normalization、lunar provider、validation 與 orchestration；命理日界完全留在 Resolver 外，第一版只新增 Ziwei adapter，不 refactor Bazi。

**Tech Stack:** Python 3.9+、標準函式庫 `unittest` / `dataclasses` / `datetime` / `zoneinfo` / `importlib.metadata` / `importlib.resources`，runtime dependency 固定 `lunar-python==1.4.8`、`tzdata==2026.3`。

**Spec:** `docs/superpowers/specs/2026-08-21-Calendar-Resolver-設計.md`

## Global Constraints

- `Precision must be earned by input`：輸入精度不足時只能追問、保留候選或降級，不得補假日期／假時間。
- Calendar Resolver 不解析自然語言；輸入從 structured local civil datetime 開始。
- `civil_datetime` 第一版不得含 embedded UTC offset。
- timezone 只接受 IANA identifier，不接受 `CST`、`EST`、`GMT+8`、`+08:00` 等模糊／固定 offset 表示。
- runtime lunar provider 固定 `lunar-python==1.4.8`，qualification source revision 固定 `000c8a3d74eed098d6256a28fdd51b869324c559`。
- timezone data 固定 `tzdata==2026.3`、IANA tzdb `2026c`，qualification source revision 固定 `a44279419071b7aa41ebe7eca301ebb2e759571a`。
- Gregorian→Lunar HKO exhaustive validated range 固定 `1901-01-01`～`2100-12-31`。
- `2057-09-28`～`2057-10-27` 固定為 `boundary_conflict`。
- `2089-09-04`、`2097-08-07` 固定為 `boundary_caution`。
- `out_of_validated_range` 與 provider error 必須分開。
- Resolver civil date 只在 local `00:00` 換日；`23:00–00:59` 的 hour branch 為子。
- `metaphysics_day_boundary_applied` 第一版固定 `false`。
- 不把八字 `23:00 early-Zi` policy 套到紫微或 Resolver。
- 第一版只正式接 Ziwei；不 refactor Bazi、不做 Qimen、不做紫微四化／流曜／細飛。
- 每個 task 都要先看到 failing test，再做最小實作，再跑測試 PASS，再 commit。
- Gate 0→4 必須依序 PASS；前一 gate FAIL 時停止，不得先做下一 gate。
- 最後必須跑完整 repo test suite；不得以修改既有 expected value 的方式掩蓋 regression。
- 不使用真實命主私人資料作 repo 測試。

---

## File / Responsibility Map

```text
requirements.txt
    唯一 runtime dependency manifest；精確 pin lunar-python / tzdata。

engine/calendar/__init__.py
    Calendar subsystem 公開 export；不承擔邏輯。

engine/calendar/precision.py
    Gate 0 pure policy：required precision、available precision、是否唯一定位。

engine/calendar/models.py
    CalendarInput、NormalizedTime、LunarDate、provider provenance、validation、policies、CalendarContext、public error/result contract。

engine/calendar/timezone.py
    pinned tzdata loading、IANA validation、local→UTC、DST nonexistent/ambiguous、utc_offset_hint、hour branch。

engine/calendar/lunar.py
    LunarCalendarProvider protocol、lunar-python 1.4.8 implementation、HKO validation status/boundary metadata。

engine/calendar/resolver.py
    orchestration；組合 timezone + lunar + validation，產出 CalendarResolution。

engine/ziwei/calendar_adapter.py
    只把成功 CalendarContext 轉交既有 month/day/hour core；不修改 lunar date、不套命理日界。

tests/test_calendar_precision.py
    Gate 0。

tests/test_calendar_models.py
    Gate 1 contract model、閏月正規化、error / validation serialization。

tests/test_calendar_timezone.py
    Gate 1 + Gate 2 timezone / DST / historical regression。

tests/test_calendar_lunar.py
    Gate 3 provider / validated range / boundary regression。

tests/test_calendar_resolver.py
    Resolver orchestration、public success/error shape、23:xx / 00:00 boundary。

tests/test_ziwei_calendar_adapter.py
    Gate 4 integration。

tests/test_calendar_package_exports.py
    subsystem public exports。
```

---

### Task 0: 建立執行隔離與 baseline 證據

**Files:**
- No code changes.

**Interfaces:**
- Consumes: approved design branch `design/calendar-resolver`。
- Produces: clean implementation worktree、baseline test count、可追溯起點。

- [ ] **Step 1: 使用 worktree skill 建立隔離環境**

執行工作前必須先 invoke `superpowers:using-git-worktrees`，從：

```text
design/calendar-resolver
```

建立 implementation branch：

```text
feature/calendar-resolver-v1
```

不得直接在 `main` 或 design branch 上寫 implementation code。

- [ ] **Step 2: 確認工作樹乾淨且起點正確**

Run:

```bash
git status --short
git log -1 --oneline
```

Expected:

```text
git status --short
→ no output
```

最新 commit 必須包含本 implementation plan commit，且 branch ancestry 來自 `design/calendar-resolver`。

- [ ] **Step 3: 跑完整 baseline test suite**

Run:

```bash
python -m unittest discover -v
```

Expected: 現有 suite 全部 PASS。依 Calendar Resolver 設計前狀態應為 50 tests；若實際 count 已因同步變更不同，但不是全部 PASS，停止執行並先找 root cause。

- [ ] **Step 4: 記錄 baseline**

在執行紀錄保留：

```text
command
actual test count
failures
errors
exit status
```

此 Task 無 commit；baseline PASS 後才進 Task 1。

---

### Task 1: Gate 0｜機械化 Input Resolution / Precision policy

**Files:**
- Create: `engine/calendar/__init__.py`
- Create: `engine/calendar/precision.py`
- Create: `tests/test_calendar_precision.py`

**Interfaces:**
- Consumes: 上游已判斷出的 `required_precision`、`available_precision` 與 `is_unique`；不解析自然語言。
- Produces:
  - `TimePrecision.YEAR | MONTH | DAY | HOUR`
  - `PrecisionAssessment`
  - `assess_precision(required, available, *, is_unique=True) -> PrecisionAssessment`

- [ ] **Step 1: 先寫 Gate 0 failing tests**

建立 `tests/test_calendar_precision.py`：

```python
import unittest

from engine.calendar.precision import TimePrecision, assess_precision


class CalendarPrecisionTests(unittest.TestCase):
    def test_year_question_does_not_require_fake_datetime(self):
        result = assess_precision(TimePrecision.YEAR, TimePrecision.YEAR)
        self.assertTrue(result.can_execute)
        self.assertEqual(result.allowed_actions, ())

    def test_month_input_cannot_route_to_day_capability(self):
        result = assess_precision(TimePrecision.DAY, TimePrecision.MONTH)
        self.assertFalse(result.can_execute)
        self.assertEqual(result.reason, "insufficient_precision")
        self.assertEqual(result.allowed_actions, ("ask", "keep_candidates", "downgrade"))

    def test_non_unique_hour_input_cannot_execute(self):
        result = assess_precision(TimePrecision.HOUR, TimePrecision.HOUR, is_unique=False)
        self.assertFalse(result.can_execute)
        self.assertEqual(result.reason, "ambiguous_input")

    def test_exact_day_can_route_to_day_capability(self):
        result = assess_precision(TimePrecision.DAY, TimePrecision.DAY, is_unique=True)
        self.assertTrue(result.can_execute)

    def test_finer_input_can_satisfy_coarser_capability(self):
        result = assess_precision(TimePrecision.MONTH, TimePrecision.DAY)
        self.assertTrue(result.can_execute)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 跑測試確認先紅**

Run:

```bash
python -m unittest tests.test_calendar_precision -v
```

Expected: FAIL because `engine.calendar.precision` 尚不存在。

- [ ] **Step 3: 寫最小 precision policy**

`engine/calendar/precision.py`：

```python
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class TimePrecision(IntEnum):
    YEAR = 1
    MONTH = 2
    DAY = 3
    HOUR = 4


@dataclass(frozen=True)
class PrecisionAssessment:
    required: TimePrecision
    available: TimePrecision
    is_unique: bool
    can_execute: bool
    reason: str | None
    allowed_actions: tuple[str, ...]


def assess_precision(
    required: TimePrecision,
    available: TimePrecision,
    *,
    is_unique: bool = True,
) -> PrecisionAssessment:
    if available < required:
        return PrecisionAssessment(
            required=required,
            available=available,
            is_unique=is_unique,
            can_execute=False,
            reason="insufficient_precision",
            allowed_actions=("ask", "keep_candidates", "downgrade"),
        )
    if not is_unique:
        return PrecisionAssessment(
            required=required,
            available=available,
            is_unique=False,
            can_execute=False,
            reason="ambiguous_input",
            allowed_actions=("ask", "keep_candidates", "downgrade"),
        )
    return PrecisionAssessment(
        required=required,
        available=available,
        is_unique=True,
        can_execute=True,
        reason=None,
        allowed_actions=(),
    )
```

`engine/calendar/__init__.py` 暫時只 export：

```python
from .precision import PrecisionAssessment, TimePrecision, assess_precision

__all__ = ["PrecisionAssessment", "TimePrecision", "assess_precision"]
```

- [ ] **Step 4: Gate 0 驗證**

Run:

```bash
python -m unittest tests.test_calendar_precision -v
```

Expected: all tests PASS。

- [ ] **Step 5: Commit Gate 0**

```bash
git add engine/calendar/__init__.py engine/calendar/precision.py tests/test_calendar_precision.py
git commit -m "feat: add calendar precision gate"
```

Gate 0 PASS 後才進 Task 2。

---

### Task 2: Gate 1 基礎｜固定 dependency manifest 與 CalendarContext contract models

**Files:**
- Create: `requirements.txt`
- Create: `engine/calendar/models.py`
- Create: `tests/test_calendar_models.py`
- Modify: `engine/calendar/__init__.py`

**Interfaces:**
- Consumes: spec 的 CalendarContext / validation / error contract。
- Produces:
  - `CalendarInput`
  - `NormalizedTime`
  - `LunarDate`
  - `LunarProviderMetadata`
  - `TimezoneProviderMetadata`
  - `ValidationCheck`
  - `ValidationMetadata`
  - `CalendarPolicies`
  - `CalendarContext`
  - `ResolverError`
  - `CalendarResolution`
  - `combine_validation_status(...)`

- [ ] **Step 1: 建立唯一 dependency manifest**

`requirements.txt` 內容固定：

```text
lunar-python==1.4.8
tzdata==2026.3
```

Run:

```bash
python -m pip install -r requirements.txt
python -c "from importlib.metadata import version; import tzdata; print(version('lunar_python'), version('tzdata'), tzdata.IANA_VERSION)"
```

Expected:

```text
1.4.8 2026.3 2026c
```

若不是 exact versions，停止，不得進下一步。

- [ ] **Step 2: 先寫 models failing tests**

`tests/test_calendar_models.py` 至少包含：

```python
import unittest
from datetime import date, datetime, timezone

from engine.calendar.models import (
    CalendarContext,
    CalendarInput,
    CalendarPolicies,
    CalendarResolution,
    LunarDate,
    LunarProviderMetadata,
    NormalizedTime,
    ResolverError,
    TimezoneProviderMetadata,
    ValidationCheck,
    ValidationMetadata,
    combine_validation_status,
)


class CalendarModelTests(unittest.TestCase):
    def test_provider_negative_month_is_normalized(self):
        lunar = LunarDate.from_provider_values(2025, -6, 1)
        self.assertEqual(lunar.month, 6)
        self.assertTrue(lunar.is_leap_month)

    def test_validation_precedence(self):
        self.assertEqual(
            combine_validation_status("validated", "boundary_caution"),
            "boundary_caution",
        )
        self.assertEqual(
            combine_validation_status("out_of_validated_range", "boundary_conflict"),
            "boundary_conflict",
        )

    def test_error_result_serializes_public_contract(self):
        result = CalendarResolution.failure(
            ResolverError("invalid_datetime", "bad input", {"value": "x"})
        )
        self.assertEqual(
            result.to_dict(),
            {
                "ok": False,
                "error": {
                    "code": "invalid_datetime",
                    "message": "bad input",
                    "details": {"value": "x"},
                },
            },
        )
```

再加入一個成功 `CalendarContext` serialization 測試，固定確認：

```text
schema_version = 1.0
resolver_version = 1.0.0
providers.lunar_calendar.name = lunar-python
providers.lunar_calendar.version = 1.4.8
providers.timezone_database.package_version = 2026.3
providers.timezone_database.tzdb_version = 2026c
policies.metaphysics_day_boundary_applied = false
```

- [ ] **Step 3: 跑 models 測試確認先紅**

```bash
python -m unittest tests.test_calendar_models -v
```

Expected: FAIL because `engine.calendar.models` 尚不存在。

- [ ] **Step 4: 實作固定 contract models**

`models.py` 必須使用 frozen dataclass，並固定：

```python
VALIDATION_PRECEDENCE = {
    "validated": 0,
    "out_of_validated_range": 1,
    "boundary_caution": 2,
    "boundary_conflict": 3,
}


def combine_validation_status(*statuses: str) -> str:
    return max(statuses, key=VALIDATION_PRECEDENCE.__getitem__)
```

`LunarDate`：

```python
@dataclass(frozen=True)
class LunarDate:
    year: int
    month: int
    day: int
    is_leap_month: bool

    @classmethod
    def from_provider_values(cls, year: int, month: int, day: int) -> "LunarDate":
        return cls(
            year=year,
            month=abs(month),
            day=day,
            is_leap_month=month < 0,
        )
```

Provider metadata 值固定：

```text
LunarProviderMetadata:
name = lunar-python
version = 1.4.8
source_revision = 000c8a3d74eed098d6256a28fdd51b869324c559

TimezoneProviderMetadata:
name = tzdata
package_version = 2026.3
tzdb_version = 2026c
source_revision = a44279419071b7aa41ebe7eca301ebb2e759571a
```

`NormalizedTime` 內部用 typed values：

```python
@dataclass(frozen=True)
class NormalizedTime:
    local_datetime: datetime
    utc_datetime: datetime
    utc_offset: str
    gregorian_date: date
    timezone: str
    hour_branch: str
```

`CalendarResolution.to_dict()` 成功時必須輸出：

```text
{"ok": true, ...CalendarContext fields...}
```

失敗時只能輸出：

```text
{"ok": false, "error": {code, message, details}}
```

不得在失敗物件中同時混入半成品 CalendarContext。

- [ ] **Step 5: 跑 models tests**

```bash
python -m unittest tests.test_calendar_models -v
```

Expected: PASS。

- [ ] **Step 6: 更新 package exports 並重跑 Gate 0 + models**

`engine/calendar/__init__.py` export precision public API 與上述 models；不要在此 import `lunar_python` 或載入 timezone database。

Run:

```bash
python -m unittest tests.test_calendar_precision tests.test_calendar_models -v
```

Expected: PASS。

- [ ] **Step 7: Commit dependency + models**

```bash
git add requirements.txt engine/calendar/models.py engine/calendar/__init__.py tests/test_calendar_models.py
git commit -m "feat: define calendar resolver contracts"
```

---

### Task 3: Gate 1｜實作 pinned timezone normalization、hour branch 與 basic errors

**Files:**
- Create: `engine/calendar/timezone.py`
- Create: `tests/test_calendar_timezone.py`

**Interfaces:**
- Consumes: `CalendarInput` / `NormalizedTime` / `ResolverError` models。
- Produces:
  - `parse_civil(value: str) -> datetime`
  - `parse_offset_hint(value: str) -> timedelta`
  - `offset_text(value: timedelta) -> str`
  - `hour_branch(hour: int) -> str`
  - `PinnedTzdataProvider`
  - `normalize_local_time(civil_datetime: str, timezone_name: str, utc_offset_hint: str | None = None) -> NormalizedTime`
  - `CalendarResolverException`

- [ ] **Step 1: 先寫 Gate 1 basic timezone tests**

`tests/test_calendar_timezone.py` 第一批測試：

```python
import unittest

from engine.calendar.timezone import (
    CalendarResolverException,
    normalize_local_time,
)


class CalendarTimezoneBasicTests(unittest.TestCase):
    def test_taipei_ordinary_normalization(self):
        result = normalize_local_time("2026-09-18T14:00:00", "Asia/Taipei")
        self.assertEqual(result.utc_offset, "+08:00")
        self.assertEqual(result.utc_datetime.isoformat(), "2026-09-18T06:00:00+00:00")
        self.assertEqual(result.gregorian_date.isoformat(), "2026-09-18")
        self.assertEqual(result.hour_branch, "未")

    def test_embedded_offset_is_rejected(self):
        with self.assertRaises(CalendarResolverException) as ctx:
            normalize_local_time("2026-09-18T14:00:00+08:00", "Asia/Taipei")
        self.assertEqual(ctx.exception.error.code, "invalid_datetime")

    def test_invalid_iana_timezone_is_rejected(self):
        with self.assertRaises(CalendarResolverException) as ctx:
            normalize_local_time("2026-09-18T14:00:00", "Mars/Olympus")
        self.assertEqual(ctx.exception.error.code, "invalid_timezone")

    def test_hour_branch_and_civil_midnight_are_independent(self):
        cases = (
            ("2026-09-18T22:59:00", "2026-09-18", "亥"),
            ("2026-09-18T23:00:00", "2026-09-18", "子"),
            ("2026-09-18T23:59:00", "2026-09-18", "子"),
            ("2026-09-19T00:00:00", "2026-09-19", "子"),
            ("2026-09-19T00:59:00", "2026-09-19", "子"),
            ("2026-09-19T01:00:00", "2026-09-19", "丑"),
        )
        for value, expected_date, expected_branch in cases:
            result = normalize_local_time(value, "Asia/Taipei")
            self.assertEqual(result.gregorian_date.isoformat(), expected_date)
            self.assertEqual(result.hour_branch, expected_branch)
```

- [ ] **Step 2: 跑測試確認先紅**

```bash
python -m unittest tests.test_calendar_timezone.CalendarTimezoneBasicTests -v
```

Expected: FAIL because timezone module 尚不存在。

- [ ] **Step 3: 實作 pinned tzdata loader**

不要依賴 host OS `TZPATH`。使用 installed `tzdata` package resource：

```python
from importlib.metadata import version
from importlib.resources import files
from zoneinfo import ZoneInfo

import tzdata

EXPECTED_TZDATA_VERSION = "2026.3"
EXPECTED_IANA_VERSION = "2026c"


class PinnedTzdataProvider:
    def __init__(self) -> None:
        if version("tzdata") != EXPECTED_TZDATA_VERSION or tzdata.IANA_VERSION != EXPECTED_IANA_VERSION:
            raise CalendarResolverException.provider_failure(
                "pinned tzdata provenance mismatch"
            )

    def zone(self, timezone_name: str) -> ZoneInfo:
        parts = timezone_name.split("/")
        if not timezone_name or any(part in ("", ".", "..") for part in parts):
            raise CalendarResolverException.invalid_timezone(timezone_name)
        resource = files("tzdata.zoneinfo").joinpath(*parts)
        try:
            with resource.open("rb") as handle:
                return ZoneInfo.from_file(handle, key=timezone_name)
        except (FileNotFoundError, IsADirectoryError):
            raise CalendarResolverException.invalid_timezone(timezone_name)
```

`CalendarResolverException` 必須包住 `ResolverError`，factory 至少提供：

```text
invalid_datetime
invalid_timezone
nonexistent_local_time
ambiguous_local_time
invalid_utc_offset_hint
provider_failure
```

- [ ] **Step 4: 實作 civil parser / hour branch / candidate normalization**

核心規則沿 qualification probe：

```python
ZHI = tuple("子丑寅卯辰巳午未申酉戌亥")


def hour_branch(hour: int) -> str:
    return ZHI[((hour + 1) // 2) % 12]
```

`parse_civil()` 必須用 `datetime.fromisoformat()`，且 `parsed.tzinfo is not None` 時回 `invalid_datetime`。

`local_candidates()` 必須對 `fold=0/1` 各做一次：

```text
local aware → UTC → same zone round-trip
```

只有 round-trip 回原始 wall time 且 offset 一致才是合法 candidate；candidate 依 UTC instant 去重。

`normalize_local_time()`：

```text
0 candidates → nonexistent_local_time
1 candidate  → success
2 candidates + no hint → ambiguous_local_time + all candidates in error.details
hint supplied → 必須 match exactly one candidate，否則 invalid_utc_offset_hint
```

合法 hint 在 unique time 可作一致性確認，但不得覆寫 tzdb；若 hint 與唯一合法 offset 不同，回 `invalid_utc_offset_hint`。

- [ ] **Step 5: Gate 1 basic test**

Run:

```bash
python -m unittest tests.test_calendar_models tests.test_calendar_timezone.CalendarTimezoneBasicTests -v
```

Expected: PASS。

此時 Gate 1 的 basic datetime、IANA、hour branch、error shape、provider metadata / leap normalization / validation precedence 均已有 deterministic tests。

- [ ] **Step 6: Commit timezone basic**

```bash
git add engine/calendar/timezone.py tests/test_calendar_timezone.py
git commit -m "feat: add pinned timezone normalization"
```

Gate 1 PASS 後才進 Task 4。

---

### Task 4: Gate 2｜鎖定 DST ambiguity / nonexistent 與 historical timezone regression

**Files:**
- Modify: `tests/test_calendar_timezone.py`
- Modify: `engine/calendar/timezone.py` only if new tests expose a real defect.

**Interfaces:**
- Consumes: Task 3 `normalize_local_time()` / pinned tzdata loader。
- Produces: qualification probe 中 2026 DST 與 historical Asia/Taipei 行為的產品 regression tests。

- [ ] **Step 1: 加入 nonexistent / ambiguous failing tests**

新增：

```python
def test_new_york_spring_forward_gap_is_error(self):
    with self.assertRaises(CalendarResolverException) as ctx:
        normalize_local_time("2026-03-08T02:30:00", "America/New_York")
    self.assertEqual(ctx.exception.error.code, "nonexistent_local_time")


def test_new_york_fall_back_overlap_lists_two_candidates(self):
    with self.assertRaises(CalendarResolverException) as ctx:
        normalize_local_time("2026-11-01T01:30:00", "America/New_York")
    self.assertEqual(ctx.exception.error.code, "ambiguous_local_time")
    candidates = ctx.exception.error.details["candidates"]
    self.assertEqual([c["utc_offset"] for c in candidates], ["-04:00", "-05:00"])
    self.assertEqual(
        [c["utc_datetime"] for c in candidates],
        ["2026-11-01T05:30:00+00:00", "2026-11-01T06:30:00+00:00"],
    )


def test_offset_hint_selects_exact_overlap_candidate(self):
    first = normalize_local_time(
        "2026-11-01T01:30:00", "America/New_York", "-04:00"
    )
    second = normalize_local_time(
        "2026-11-01T01:30:00", "America/New_York", "-05:00"
    )
    self.assertEqual(first.utc_datetime.isoformat(), "2026-11-01T05:30:00+00:00")
    self.assertEqual(second.utc_datetime.isoformat(), "2026-11-01T06:30:00+00:00")


def test_invalid_offset_hint_is_rejected(self):
    with self.assertRaises(CalendarResolverException) as ctx:
        normalize_local_time(
            "2026-11-01T01:30:00", "America/New_York", "-06:00"
        )
    self.assertEqual(ctx.exception.error.code, "invalid_utc_offset_hint")
```

- [ ] **Step 2: 跑 DST tests；若失敗只修當前 root cause**

```bash
python -m unittest tests.test_calendar_timezone -v
```

Expected: PASS after any required minimal fix。

- [ ] **Step 3: 加入 cross-zone round-trip 與 historical Taipei cases**

固定 cases：

```python
ROUNDTRIP_CASES = (
    ("2026-01-15T12:00:00", "America/New_York", "-05:00"),
    ("2026-07-15T12:00:00", "America/New_York", "-04:00"),
    ("2026-01-15T12:00:00", "Europe/London", "+00:00"),
    ("2026-07-15T12:00:00", "Europe/London", "+01:00"),
    ("2026-07-15T12:00:00", "Asia/Tokyo", "+09:00"),
    ("2026-01-15T12:00:00", "Australia/Sydney", "+11:00"),
    ("2026-07-15T12:00:00", "Australia/Sydney", "+10:00"),
)

HISTORICAL_TAIPEI = (
    ("1937-09-30T12:00:00", "+08:00"),
    ("1937-10-01T12:00:00", "+09:00"),
    ("1945-09-20T12:00:00", "+09:00"),
    ("1945-09-21T12:00:00", "+08:00"),
    ("1946-06-01T12:00:00", "+09:00"),
    ("1946-11-01T12:00:00", "+08:00"),
    ("1979-08-01T12:00:00", "+09:00"),
    ("1979-11-01T12:00:00", "+08:00"),
)
```

每個 case 都 assert exact offset；cross-zone cases 再 assert UTC→local round-trip 回原 wall time。

- [ ] **Step 4: Gate 2 驗證**

```bash
python -m unittest tests.test_calendar_timezone -v
```

Expected: all timezone tests PASS。

- [ ] **Step 5: Commit Gate 2**

```bash
git add engine/calendar/timezone.py tests/test_calendar_timezone.py
git commit -m "test: lock calendar DST and historical timezone behavior"
```

Gate 2 PASS 後才進 Task 5。

---

### Task 5: Gate 3｜實作 lunar-python provider 與 HKO validation contract

**Files:**
- Create: `engine/calendar/lunar.py`
- Create: `tests/test_calendar_lunar.py`

**Interfaces:**
- Consumes: `lunar-python==1.4.8`、`LunarDate`、validation models。
- Produces:
  - `LunarCalendarProvider` protocol
  - `LunarPythonProvider.convert(civil_date: date) -> LunarDate`
  - `calendar_validation_for(civil_date: date) -> CalendarValidationDecision`
  - `LunarProviderUnsupportedDate`
  - `LunarProviderFailure`

- [ ] **Step 1: 先寫 provider / validation failing tests**

`tests/test_calendar_lunar.py`：

```python
import unittest
from datetime import date
from unittest.mock import patch

from engine.calendar.lunar import (
    LunarProviderFailure,
    LunarProviderUnsupportedDate,
    LunarPythonProvider,
    calendar_validation_for,
)
from engine.calendar.models import LunarDate


class CalendarLunarTests(unittest.TestCase):
    def test_known_lunar_new_year_conversion(self):
        result = LunarPythonProvider().convert(date(2025, 1, 29))
        self.assertEqual(result, LunarDate(2025, 1, 1, False))

    def test_known_2025_leap_sixth_month_normalizes_negative_month(self):
        result = LunarPythonProvider().convert(date(2025, 7, 25))
        self.assertEqual(result, LunarDate(2025, 6, 1, True))

    def test_validated_range_edges(self):
        self.assertEqual(calendar_validation_for(date(1901, 1, 1)).check.status, "validated")
        self.assertEqual(calendar_validation_for(date(2100, 12, 31)).check.status, "validated")

    def test_2057_conflict_window(self):
        for value in (date(2057, 9, 28), date(2057, 10, 10), date(2057, 10, 27)):
            decision = calendar_validation_for(value)
            self.assertEqual(decision.check.status, "boundary_conflict")
            self.assertEqual(decision.boundary_id, "hko-new-moon-2057-09-28-conflict")
        self.assertEqual(calendar_validation_for(date(2057, 10, 28)).check.status, "validated")

    def test_caution_dates(self):
        self.assertEqual(calendar_validation_for(date(2089, 9, 4)).check.status, "boundary_caution")
        self.assertEqual(calendar_validation_for(date(2097, 8, 7)).check.status, "boundary_caution")

    def test_out_of_validated_range_is_not_provider_error(self):
        decision = calendar_validation_for(date(2150, 3, 1))
        self.assertEqual(decision.check.status, "out_of_validated_range")

    @patch("engine.calendar.lunar.Solar.fromYmd", side_effect=IndexError("unsupported"))
    def test_provider_unsupported_date_has_specific_exception(self, _mock):
        with self.assertRaises(LunarProviderUnsupportedDate):
            LunarPythonProvider().convert(date(2150, 3, 1))

    @patch("engine.calendar.lunar.Solar.fromYmd", side_effect=RuntimeError("boom"))
    def test_unexpected_provider_error_is_failure(self, _mock):
        with self.assertRaises(LunarProviderFailure):
            LunarPythonProvider().convert(date(2026, 8, 21))
```

- [ ] **Step 2: 跑 Gate 3 tests 確認先紅**

```bash
python -m unittest tests.test_calendar_lunar -v
```

Expected: FAIL because lunar module 尚不存在。

- [ ] **Step 3: 實作 provider provenance 與 conversion**

`engine/calendar/lunar.py` 必須固定：

```python
from lunar_python import Solar
from importlib.metadata import version

EXPECTED_LUNAR_VERSION = "1.4.8"
LUNAR_SOURCE_REVISION = "000c8a3d74eed098d6256a28fdd51b869324c559"
```

`LunarPythonProvider.__init__()` 若 `version("lunar_python") != "1.4.8"`，raise `LunarProviderFailure`。

`convert()` 核心：

```python
lunar = Solar.fromYmd(civil_date.year, civil_date.month, civil_date.day).getLunar()
return LunarDate.from_provider_values(
    lunar.getYear(),
    lunar.getMonth(),
    lunar.getDay(),
)
```

錯誤分類：

```text
ValueError / IndexError → LunarProviderUnsupportedDate
其他 unexpected Exception → LunarProviderFailure
```

不得直接把第三方 exception 當 public Resolver API。

- [ ] **Step 4: 實作 validation decision**

固定 constants：

```python
VALIDATED_START = date(1901, 1, 1)
VALIDATED_END = date(2100, 12, 31)
CONFLICT_START = date(2057, 9, 28)
CONFLICT_END = date(2057, 10, 27)
CAUTION_BOUNDARIES = {
    date(2089, 9, 4): "hko-new-moon-2089-09-04-caution",
    date(2097, 8, 7): "hko-new-moon-2097-08-07-caution",
}
CALENDAR_PROFILE = "hko-gregorian-lunar-1901-2100-v1"
```

判斷順序固定：

```text
2057 conflict window
→ 2089 / 2097 caution exact date
→ outside 1901-2100
→ validated
```

`validated_range` 字串固定：

```text
1901-01-01/2100-12-31
```

- [ ] **Step 5: Gate 3 驗證**

```bash
python -m unittest tests.test_calendar_lunar -v
```

Expected: PASS。

- [ ] **Step 6: Commit Gate 3**

```bash
git add engine/calendar/lunar.py tests/test_calendar_lunar.py
git commit -m "feat: add lunar provider and validation profile"
```

Gate 3 PASS 後才進 Task 6。

---

### Task 6: 組合 Calendar Resolver orchestration 與 public success/error contract

**Files:**
- Create: `engine/calendar/resolver.py`
- Create: `tests/test_calendar_resolver.py`
- Modify: `engine/calendar/__init__.py`

**Interfaces:**
- Consumes: `normalize_local_time()`、`LunarPythonProvider`、`calendar_validation_for()`、models。
- Produces:
  - `resolve_calendar(civil_datetime: str, timezone_name: str, utc_offset_hint: str | None = None, *, lunar_provider=None, timezone_provider=None) -> CalendarResolution`
  - successful `CalendarContext`

- [ ] **Step 1: 先寫 resolver failing tests**

`tests/test_calendar_resolver.py` 至少包含：

```python
import unittest
from datetime import date

from engine.calendar.resolver import resolve_calendar


class CalendarResolverTests(unittest.TestCase):
    def test_success_context_contains_provenance_and_policies(self):
        result = resolve_calendar("2026-09-18T14:00:00", "Asia/Taipei")
        self.assertTrue(result.ok)
        context = result.context
        self.assertIsNotNone(context)
        assert context is not None
        self.assertEqual(context.input.timezone, "Asia/Taipei")
        self.assertEqual(context.normalized_time.hour_branch, "未")
        self.assertFalse(context.policies.metaphysics_day_boundary_applied)
        self.assertEqual(context.providers.lunar_calendar.version, "1.4.8")
        self.assertEqual(context.providers.timezone_database.package_version, "2026.3")

    def test_23xx_does_not_apply_metaphysical_rollover(self):
        result = resolve_calendar("2026-09-18T23:30:00", "Asia/Taipei")
        self.assertTrue(result.ok)
        context = result.context
        assert context is not None
        self.assertEqual(context.normalized_time.gregorian_date.isoformat(), "2026-09-18")
        self.assertEqual(context.normalized_time.hour_branch, "子")
        self.assertFalse(context.policies.metaphysics_day_boundary_applied)

    def test_boundary_conflict_is_success_with_warning_metadata(self):
        result = resolve_calendar("2057-09-28T12:00:00", "Asia/Taipei")
        self.assertTrue(result.ok)
        context = result.context
        assert context is not None
        self.assertEqual(context.validation.calendar_conversion.status, "boundary_conflict")
        self.assertEqual(context.validation.overall_status, "boundary_conflict")

    def test_out_of_range_can_still_be_success_when_provider_calculates(self):
        result = resolve_calendar("2150-03-01T12:00:00", "Asia/Taipei")
        if result.ok:
            context = result.context
            assert context is not None
            self.assertEqual(
                context.validation.calendar_conversion.status,
                "out_of_validated_range",
            )
        else:
            self.assertEqual(result.error.code, "provider_unsupported_date")

    def test_invalid_timezone_returns_public_error_result(self):
        result = resolve_calendar("2026-09-18T14:00:00", "Mars/Olympus")
        self.assertFalse(result.ok)
        self.assertEqual(result.error.code, "invalid_timezone")
```

對 `out_of_range` 測試另外加入 deterministic stub provider，保證至少有一個「provider succeeds + out_of_validated_range」case，不依賴 lunar-python 未驗證的未來支援範圍。

- [ ] **Step 2: 跑 resolver tests 確認先紅**

```bash
python -m unittest tests.test_calendar_resolver -v
```

Expected: FAIL because resolver module 尚不存在。

- [ ] **Step 3: 實作 resolver orchestration**

固定版本：

```text
schema_version = 1.0
resolver_version = 1.0.0
```

流程必須是：

```text
1. normalize_local_time
2. Gregorian date = normalized local civil date
3. lunar provider convert(Gregorian date)
4. calendar_validation_for(Gregorian date)
5. timezone validation = validated / tzdata-2026.3-iana-2026c-v1
6. combine overall status
7. build CalendarContext
8. return CalendarResolution.success(context)
```

Policies 固定：

```text
timezone_basis = IANA legal local civil time
lunar_date_boundary = local civil midnight (00:00)
hour_branch_basis = local civil clock; 子=23:00-00:59
metaphysics_day_boundary_applied = false
```

錯誤 mapping：

```text
CalendarResolverException → 其內 ResolverError
LunarProviderUnsupportedDate → provider_unsupported_date
LunarProviderFailure → provider_failure
```

成功 `boundary_conflict` 仍 `ok=true`；Resolver 不偷偷改用 HKO oracle date。

- [ ] **Step 4: 跑 resolver tests**

```bash
python -m unittest tests.test_calendar_resolver -v
```

Expected: PASS。

- [ ] **Step 5: 重跑 Gate 0～3 全部產品測試**

```bash
python -m unittest \
  tests.test_calendar_precision \
  tests.test_calendar_models \
  tests.test_calendar_timezone \
  tests.test_calendar_lunar \
  tests.test_calendar_resolver \
  -v
```

Expected: PASS，failures=0，errors=0。

- [ ] **Step 6: 更新 package exports**

`engine/calendar/__init__.py` 公開：

```text
TimePrecision
PrecisionAssessment
assess_precision
CalendarContext
CalendarResolution
resolve_calendar
```

不要 eager-create provider instance，也不要 import `engine.ziwei`。

- [ ] **Step 7: Commit Resolver**

```bash
git add engine/calendar/resolver.py engine/calendar/__init__.py tests/test_calendar_resolver.py
git commit -m "feat: add calendar resolver orchestration"
```

---

### Task 7: Gate 4｜建立 Ziwei Calendar Adapter，不改既有 core

**Files:**
- Create: `engine/ziwei/calendar_adapter.py`
- Create: `tests/test_ziwei_calendar_adapter.py`
- Modify: `engine/ziwei/hour.py`

**Interfaces:**
- Consumes: successful `CalendarContext`、既有 `project_derived_ziwei_month/day/hour()`。
- Produces:
  - `ziwei_month_from_calendar(...) -> dict`
  - `ziwei_day_from_calendar(...) -> dict`
  - `ziwei_hour_from_calendar(...) -> dict`
  - `ZiweiCalendarAdapterError`

- [ ] **Step 1: 先更新既有 flow-hour feature test 的目標狀態**

目前 `tests/test_project_ziwei_hour.py` 仍 assert：

```text
calendar_resolver_implemented = false
```

Calendar Resolver 真正完成後，先把該 expected 改成：

```text
calendar_resolver_implemented = true
```

只允許改這個 capability availability flag；不得改既有流時公式 expected values。

Run:

```bash
python -m unittest tests.test_project_ziwei_hour -v
```

Expected: FAIL，因 `hour.py` 尚未更新 flag。

- [ ] **Step 2: 最小更新 `hour.py` availability metadata**

將 structured output：

```python
"calendar_resolver_implemented": True,
```

不得在 `hour.py` import Resolver，也不得把 civil datetime / timezone 參數塞進既有核心函式。

Run:

```bash
python -m unittest tests.test_project_ziwei_hour -v
```

Expected: PASS。

- [ ] **Step 3: 寫 adapter failing tests**

`tests/test_ziwei_calendar_adapter.py`：

```python
import unittest

from engine.calendar.resolver import resolve_calendar
from engine.ziwei.calendar_adapter import (
    ZiweiCalendarAdapterError,
    ziwei_day_from_calendar,
    ziwei_hour_from_calendar,
    ziwei_month_from_calendar,
)
from engine.ziwei.day import project_derived_ziwei_day
from engine.ziwei.hour import project_derived_ziwei_hour
from engine.ziwei.month import project_derived_ziwei_month


class ZiweiCalendarAdapterTests(unittest.TestCase):
    def test_month_adapter_passes_resolved_lunar_fields_to_existing_core(self):
        resolution = resolve_calendar("2025-01-29T12:00:00", "Asia/Taipei")
        context = resolution.context
        assert context is not None
        adapted = ziwei_month_from_calendar(context, 5, "戌", "巳")
        expected = project_derived_ziwei_month(
            5,
            "戌",
            "巳",
            context.lunar.month,
            context.lunar.day,
            context.lunar.is_leap_month,
        )
        self.assertEqual(adapted["ziwei"], expected)

    def test_hour_adapter_uses_resolver_hour_branch_without_day_rollover(self):
        resolution = resolve_calendar("2026-09-18T23:30:00", "Asia/Taipei")
        context = resolution.context
        assert context is not None
        adapted = ziwei_hour_from_calendar(context, 5, "戌", "午")
        expected = project_derived_ziwei_hour(
            5,
            "戌",
            "午",
            context.lunar.month,
            context.lunar.day,
            context.lunar.is_leap_month,
            "子",
        )
        self.assertEqual(adapted["ziwei"], expected)
        self.assertEqual(adapted["calendar"]["gregorian_date"], "2026-09-18")

    def test_boundary_conflict_is_rejected_by_adapter(self):
        resolution = resolve_calendar("2057-09-28T12:00:00", "Asia/Taipei")
        context = resolution.context
        assert context is not None
        with self.assertRaises(ZiweiCalendarAdapterError) as ctx:
            ziwei_day_from_calendar(context, 5, "戌", "巳")
        self.assertEqual(ctx.exception.code, "boundary_conflict")
```

- [ ] **Step 4: 跑 adapter tests 確認先紅**

```bash
python -m unittest tests.test_ziwei_calendar_adapter -v
```

Expected: FAIL because adapter module 尚不存在。

- [ ] **Step 5: 實作 adapter**

Adapter helper：

```python
def _ensure_usable_context(context: CalendarContext) -> None:
    if context.validation.calendar_conversion.status == "boundary_conflict":
        raise ZiweiCalendarAdapterError(
            "boundary_conflict",
            context.validation.boundary_id or "calendar boundary conflict",
        )
```

三個 public function 都：

```text
1. _ensure_usable_context(context)
2. 讀 context.lunar.month / day / is_leap_month
3. month/day 呼叫既有 core
4. hour 額外讀 context.normalized_time.hour_branch
5. 回 {"calendar": minimal provenance/validation metadata, "ziwei": existing_core_output}
```

`calendar` 區塊至少保留：

```text
gregorian_date
lunar
hour_branch
calendar_validation_status
boundary_id
metaphysics_day_boundary_applied
```

不得：

```text
修改 lunar date
重新轉 Gregorian→Lunar
重新解析 timezone
套用 Bazi 23:00 policy
替 boundary_conflict 偷選 HKO date
```

- [ ] **Step 6: Gate 4 integration tests**

```bash
python -m unittest \
  tests.test_ziwei_calendar_adapter \
  tests.test_project_ziwei_month \
  tests.test_project_ziwei_day \
  tests.test_project_ziwei_hour \
  -v
```

Expected: PASS。

- [ ] **Step 7: Commit Gate 4**

```bash
git add engine/ziwei/calendar_adapter.py engine/ziwei/hour.py tests/test_ziwei_calendar_adapter.py tests/test_project_ziwei_hour.py
git commit -m "feat: connect calendar resolver to Ziwei"
```

Gate 4 PASS 後才進 Task 8。

---

### Task 8: Public exports、文件同步與完整 regression gate

**Files:**
- Create: `tests/test_calendar_package_exports.py`
- Modify: `engine/calendar/__init__.py`
- Modify: `README.md`
- Modify: `docs/架構說明.md`
- Modify: `docs/安裝到ChatGPT-Project.md`
- Modify: `docs/更新與版本同步.md`
- Modify: `core/命理分析作業規範.md`
- Modify: `VERSION.md`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: Gate 0～4 全部通過的正式 API。
- Produces: 使用者／Agent 可安裝、可找到、文件與實作一致的 Calendar Resolver v1。

- [ ] **Step 1: 先寫 package export test**

`tests/test_calendar_package_exports.py`：

```python
import unittest

import engine.calendar as calendar


class CalendarPackageExportTests(unittest.TestCase):
    def test_public_exports_exist(self):
        for name in (
            "TimePrecision",
            "PrecisionAssessment",
            "assess_precision",
            "CalendarContext",
            "CalendarResolution",
            "resolve_calendar",
        ):
            self.assertTrue(hasattr(calendar, name), name)


if __name__ == "__main__":
    unittest.main()
```

Run:

```bash
python -m unittest tests.test_calendar_package_exports -v
```

若 FAIL，只補缺失 export，不做 unrelated refactor。

- [ ] **Step 2: 同步 README / 架構說明**

文件必須明寫：

```text
Calendar Resolver = implemented v1
Input Resolution / Precision Gate = upstream pure policy
Natural-language parsing = not Resolver responsibility
lunar runtime = lunar-python 1.4.8
validated range = 1901-01-01..2100-12-31
2057 conflict / 2089+2097 caution
pinned tzdata = 2026.3 / IANA 2026c
23:00 = 子時但 civil date 不換日
metaphysics_day_boundary_applied = false
Ziwei = first adapter
Bazi refactor = not included
```

不得寫成：

```text
Resolver 已處理八字 23:00 換日
紫微 23:00 換日已決定
2100 以後已驗證
CWA exhaustive automation 已完成
```

- [ ] **Step 3: 同步 ChatGPT Project 安裝／更新文件**

`docs/安裝到ChatGPT-Project.md` 與 `docs/更新與版本同步.md` 加入 Resolver 實際執行所需檔案：

```text
requirements.txt
engine/calendar/__init__.py
engine/calendar/precision.py
engine/calendar/models.py
engine/calendar/timezone.py
engine/calendar/lunar.py
engine/calendar/resolver.py
engine/ziwei/calendar_adapter.py
```

並明寫 runtime 環境需要安裝 exact dependencies；只複製 Python 檔但沒有 `lunar-python==1.4.8` / `tzdata==2026.3` 時不得宣稱可執行 Resolver。

- [ ] **Step 4: 同步 core 分析規範**

`core/命理分析作業規範.md` 加入：

```text
先判斷目標 capability 需要的最低時間精度。
不足 → 追問 / 保留候選 / 降級。
不得用假日期／假時間填滿 Resolver input。
Resolver 只處理 neutral civil/calendar context。
Bazi / Ziwei / Qimen day-boundary policy 各自處理。
```

既有「先盲判、再事件校準」規則不得被這次修改破壞。

- [ ] **Step 5: 更新 VERSION / CHANGELOG**

記錄至少：

```text
Calendar Resolver v1
Gate 0 precision policy
pinned lunar/tzdata providers
HKO validated range / boundary metadata
Ziwei first adapter
Bazi unchanged
```

版本號依 repo 現有 v1.2 開發線規則更新；不得宣稱紫微 transformations 已完成。

- [ ] **Step 6: 跑 Calendar subsystem 全測試**

```bash
python -m unittest \
  tests.test_calendar_precision \
  tests.test_calendar_models \
  tests.test_calendar_timezone \
  tests.test_calendar_lunar \
  tests.test_calendar_resolver \
  tests.test_calendar_package_exports \
  tests.test_ziwei_calendar_adapter \
  -v
```

Expected: PASS，failures=0，errors=0。

- [ ] **Step 7: 跑完整 repo regression**

```bash
python -m unittest discover -v
```

Expected: 全部 PASS。

特別確認：

```text
existing Bazi tests = PASS
existing Ziwei month tests = PASS
existing Ziwei day tests = PASS
existing Ziwei hour tests = PASS
capability registry tests = PASS
wrapper / CLI tests = PASS
```

- [ ] **Step 8: 驗證 dependency provenance**

```bash
python -c "from importlib.metadata import version; import tzdata; assert version('lunar_python') == '1.4.8'; assert version('tzdata') == '2026.3'; assert tzdata.IANA_VERSION == '2026c'; print('PROVENANCE_PASS')"
```

Expected:

```text
PROVENANCE_PASS
```

- [ ] **Step 9: 檢查 implementation diff scope**

```bash
git diff --stat design/calendar-resolver...HEAD
git diff --name-only design/calendar-resolver...HEAD
```

確認沒有：

```text
Bazi refactor
Qimen implementation
紫微 transformations / 流曜 / 細飛
qualification probe workflow 被搬回 main
真實命主私人資料
```

- [ ] **Step 10: Commit docs / exports / final regression state**

```bash
git add \
  engine/calendar/__init__.py \
  tests/test_calendar_package_exports.py \
  README.md \
  docs/架構說明.md \
  docs/安裝到ChatGPT-Project.md \
  docs/更新與版本同步.md \
  core/命理分析作業規範.md \
  VERSION.md \
  CHANGELOG.md
git commit -m "docs: integrate Calendar Resolver v1"
```

---

## Final Verification Checklist

執行完成前必須逐項有證據：

- [ ] Baseline repo suite 在任何 implementation 前 PASS。
- [ ] Gate 0 precision policy PASS。
- [ ] Gate 1 model/basic timezone/error contract PASS。
- [ ] Gate 2 DST / historical timezone PASS。
- [ ] Gate 3 lunar provider / HKO validation contract PASS。
- [ ] Gate 4 Ziwei adapter integration PASS。
- [ ] `23:30` 仍是當日 civil/lunar date，hour branch=子，`metaphysics_day_boundary_applied=false`。
- [ ] `2057-09-28..2057-10-27` 不被靜默當 validated。
- [ ] `2089-09-04` / `2097-08-07` 保留 caution。
- [ ] 2100 以外不宣稱 validated。
- [ ] malformed / ambiguous timezone input 不被偷偷猜值。
- [ ] `lunar-python==1.4.8` / `tzdata==2026.3` / `IANA 2026c` provenance PASS。
- [ ] existing Ziwei month/day/hour behavior 維持 PASS。
- [ ] Bazi engine 沒有被 refactor。
- [ ] 完整 `python -m unittest discover -v` PASS。
- [ ] docs 與實際 API / validation status 一致。

只有全部 PASS 後，Calendar Resolver v1 才可進入 branch finishing / PR review 流程；任何一項 FAIL 都停在當前 task 修正，不得把未驗證問題帶到下一步。