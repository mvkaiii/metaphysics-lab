# Calendar Resolver Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立 system-neutral 的 Calendar Resolver v1，將結構化 civil datetime + IANA timezone 正規化為可追溯、可驗證的 `CalendarContext`，並以 Ziwei adapter 對接既有流月／流日／流時 core，同時機械化 `Precision must be earned by input` 與 Gate 0→4。

**Architecture:** 上游先用 pure precision policy 判斷輸入是否足以支撐目標 capability；只有需要完整 civil datetime 的路徑才進 Resolver。Resolver 內部分離 models、pinned timezone normalization、lunar provider、validation 與 orchestration；命理日界完全留在 Resolver 外，第一版只新增 Ziwei adapter，不 refactor Bazi。

**Tech Stack:** Python 3.9+、標準函式庫 `unittest` / `dataclasses` / `datetime` / `zoneinfo` / `importlib.metadata` / `importlib.resources`，runtime dependency 固定 `lunar-python==1.4.8`、`tzdata==2026.3`。

**Spec:** `docs/superpowers/specs/2026-08-21-Calendar-Resolver-設計.md`

## Global Constraints

- `Precision must be earned by input`：輸入精度不足時只能追問、保留候選或降級，不得補假日期／假時間。
- Calendar Resolver 不解析自然語言；輸入從 structured local civil datetime 開始。
- `civil_datetime` 第一版不得含 embedded UTC offset。
- timezone 只接受 IANA identifier，不接受 `CST`、`EST`、`GMT+8`、`+08:00` 等模糊／固定 offset 表示。
- runtime lunar provider 固定 `lunar-python==1.4.8`；qualification source revision 固定 `000c8a3d74eed098d6256a28fdd51b869324c559`。
- timezone data 固定 `tzdata==2026.3`、IANA tzdb `2026c`；qualification source revision 固定 `a44279419071b7aa41ebe7eca301ebb2e759571a`。
- Gregorian→Lunar HKO exhaustive validated range 固定 `1901-01-01`～`2100-12-31`。
- `2057-09-28`～`2057-10-27` 固定為 `boundary_conflict`。
- `2089-09-04`、`2097-08-07` 固定為 `boundary_caution`。
- `out_of_validated_range` 與 provider error 必須分開。
- Resolver civil date 只在 local `00:00` 換日；`23:00–00:59` 的 hour branch 為子。
- `metaphysics_day_boundary_applied` 第一版固定 `false`。
- 不把八字 `23:00 early-Zi` policy 套到紫微或 Resolver。
- 第一版只正式接 Ziwei；不 refactor Bazi、不做 Qimen、不做紫微四化／流曜／細飛。
- 每個 implementation task 都要先看到 failing test，再做最小實作，再跑測試 PASS，再 commit。
- Gate 0→4 必須依序 PASS；前一 gate FAIL 時停止，不得先做下一 gate。
- 最後必須跑完整 repo test suite；不得以修改既有 expected value 的方式掩蓋 regression。
- 不使用真實命主私人資料作 repo 測試。

---

## Locked Public Interfaces

後續 Task 必須使用以下名稱，不得自行改名。

```python
# engine/calendar/precision.py
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
) -> PrecisionAssessment: ...
```

```python
# engine/calendar/models.py
@dataclass(frozen=True)
class CalendarInput:
    civil_datetime: str
    timezone: str
    utc_offset_hint: str | None = None

@dataclass(frozen=True)
class NormalizedTime:
    local_datetime: datetime
    utc_datetime: datetime
    utc_offset: str
    gregorian_date: date
    timezone: str
    hour_branch: str

@dataclass(frozen=True)
class LunarDate:
    year: int
    month: int
    day: int
    is_leap_month: bool

    @classmethod
    def from_provider_values(cls, year: int, month: int, day: int) -> "LunarDate": ...

@dataclass(frozen=True)
class LunarProviderMetadata:
    name: str
    version: str
    source_revision: str

@dataclass(frozen=True)
class TimezoneProviderMetadata:
    name: str
    package_version: str
    tzdb_version: str
    source_revision: str

@dataclass(frozen=True)
class ProviderBundle:
    lunar_calendar: LunarProviderMetadata
    timezone_database: TimezoneProviderMetadata

@dataclass(frozen=True)
class ValidationCheck:
    status: str
    profile: str

@dataclass(frozen=True)
class CalendarValidationDecision:
    check: ValidationCheck
    validated_range: str
    boundary_id: str | None
    notes: tuple[str, ...]

@dataclass(frozen=True)
class ValidationMetadata:
    calendar_conversion: ValidationCheck
    timezone_normalization: ValidationCheck
    overall_status: str
    validated_range: str
    boundary_id: str | None
    notes: tuple[str, ...]

@dataclass(frozen=True)
class CalendarPolicies:
    timezone_basis: str
    lunar_date_boundary: str
    hour_branch_basis: str
    metaphysics_day_boundary_applied: bool

@dataclass(frozen=True)
class CalendarContext:
    schema_version: str
    resolver_version: str
    input: CalendarInput
    normalized_time: NormalizedTime
    lunar: LunarDate
    providers: ProviderBundle
    validation: ValidationMetadata
    policies: CalendarPolicies

@dataclass(frozen=True)
class ResolverError:
    code: str
    message: str
    details: dict

@dataclass(frozen=True)
class CalendarResolution:
    ok: bool
    context: CalendarContext | None
    error: ResolverError | None

    @classmethod
    def success(cls, context: CalendarContext) -> "CalendarResolution": ...

    @classmethod
    def failure(cls, error: ResolverError) -> "CalendarResolution": ...

    def to_dict(self) -> dict: ...

class CalendarResolverException(ValueError):
    def __init__(self, code: str, message: str, details: dict | None = None): ...

def combine_validation_status(*statuses: str) -> str: ...
```

```python
# engine/calendar/timezone.py
class PinnedTzdataProvider:
    metadata: TimezoneProviderMetadata
    def zone(self, timezone_name: str) -> ZoneInfo: ...

def normalize_local_time(
    civil_datetime: str,
    timezone_name: str,
    utc_offset_hint: str | None = None,
    *,
    provider: PinnedTzdataProvider | None = None,
) -> NormalizedTime: ...
```

```python
# engine/calendar/lunar.py
class LunarCalendarProvider(Protocol):
    metadata: LunarProviderMetadata
    def convert(self, civil_date: date) -> LunarDate: ...

class LunarPythonProvider:
    metadata: LunarProviderMetadata
    def convert(self, civil_date: date) -> LunarDate: ...

def calendar_validation_for(civil_date: date) -> CalendarValidationDecision: ...
```

```python
# engine/calendar/resolver.py
def resolve_calendar(
    civil_datetime: str,
    timezone_name: str,
    utc_offset_hint: str | None = None,
    *,
    lunar_provider: LunarCalendarProvider | None = None,
    timezone_provider: PinnedTzdataProvider | None = None,
) -> CalendarResolution: ...
```

```python
# engine/ziwei/calendar_adapter.py
class ZiweiCalendarAdapterError(ValueError):
    code: str

def ziwei_month_from_calendar(
    context: CalendarContext,
    birth_lunar_month: int,
    birth_hour_branch: str,
    flow_year_branch: str,
) -> dict: ...

def ziwei_day_from_calendar(
    context: CalendarContext,
    birth_lunar_month: int,
    birth_hour_branch: str,
    flow_year_branch: str,
) -> dict: ...

def ziwei_hour_from_calendar(
    context: CalendarContext,
    birth_lunar_month: int,
    birth_hour_branch: str,
    flow_year_branch: str,
) -> dict: ...
```

---

## File / Responsibility Map

```text
requirements.txt                         exact runtime pins only
engine/calendar/__init__.py             Calendar subsystem exports only
engine/calendar/precision.py            Gate 0 pure precision policy
engine/calendar/models.py               data / error / serialization contract
engine/calendar/timezone.py             pinned tzdata + DST + hour branch
engine/calendar/lunar.py                lunar-python provider + HKO validation profile
engine/calendar/resolver.py             orchestration only
engine/ziwei/calendar_adapter.py        CalendarContext → existing Ziwei core

tests/test_calendar_precision.py        Gate 0
tests/test_calendar_models.py           Gate 1 contract
tests/test_calendar_timezone.py         Gate 1 + Gate 2
tests/test_calendar_lunar.py            Gate 3
tests/test_calendar_resolver.py         resolver orchestration
tests/test_ziwei_calendar_adapter.py     Gate 4
tests/test_calendar_package_exports.py  public exports
```

---

### Task 0: 執行隔離與 baseline 證據

**Files:** No code changes.

**Interfaces:**
- Consumes: approved `design/calendar-resolver`。
- Produces: clean implementation worktree、baseline suite evidence。

- [ ] **Step 1: 建立隔離 worktree**

執行前 invoke `superpowers:using-git-worktrees`，從 `design/calendar-resolver` 建立：

```text
feature/calendar-resolver-v1
```

- [ ] **Step 2: 確認起點**

```bash
git status --short
git log -1 --oneline
```

Expected: `git status --short` 無輸出；最新 commit 包含本 implementation plan。

- [ ] **Step 3: 跑 baseline**

```bash
python -m unittest discover -v
```

Expected: 現有 suite 全部 PASS。設計核准時基準為 50 tests；若 count 不同但全部 PASS，可記錄實際 count 後繼續；只要有 failure/error 就停止。

- [ ] **Step 4: 記錄證據**

記錄 exact command、actual test count、failures、errors、exit status。Task 0 無 commit。

---

### Task 1: Gate 0｜Precision policy

**Files:**
- Create: `engine/calendar/__init__.py`
- Create: `engine/calendar/precision.py`
- Create: `tests/test_calendar_precision.py`

**Interfaces:** 使用 Locked Public Interfaces 的 `TimePrecision` / `PrecisionAssessment` / `assess_precision()`。

- [ ] **Step 1: 寫 failing tests**

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
        self.assertTrue(
            assess_precision(TimePrecision.DAY, TimePrecision.DAY, is_unique=True).can_execute
        )

    def test_finer_input_satisfies_coarser_capability(self):
        self.assertTrue(
            assess_precision(TimePrecision.MONTH, TimePrecision.DAY).can_execute
        )
```

- [ ] **Step 2: 驗證先紅**

```bash
python -m unittest tests.test_calendar_precision -v
```

Expected: FAIL because module 尚不存在。

- [ ] **Step 3: 最小實作**

```python
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

def assess_precision(required, available, *, is_unique=True):
    if available < required:
        return PrecisionAssessment(
            required, available, is_unique, False,
            "insufficient_precision", ("ask", "keep_candidates", "downgrade")
        )
    if not is_unique:
        return PrecisionAssessment(
            required, available, False, False,
            "ambiguous_input", ("ask", "keep_candidates", "downgrade")
        )
    return PrecisionAssessment(required, available, True, True, None, ())
```

`engine/calendar/__init__.py` 此 Task 只 export precision API。

- [ ] **Step 4: Gate 0 PASS**

```bash
python -m unittest tests.test_calendar_precision -v
```

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add engine/calendar/__init__.py engine/calendar/precision.py tests/test_calendar_precision.py
git commit -m "feat: add calendar precision gate"
```

---

### Task 2: Gate 1 基礎｜Dependency pins + contract models

**Files:**
- Create: `requirements.txt`
- Create: `engine/calendar/models.py`
- Create: `tests/test_calendar_models.py`
- Modify: `engine/calendar/__init__.py`

**Interfaces:** 使用 Locked Public Interfaces 的所有 models。

- [ ] **Step 1: 建立唯一 dependency manifest**

```text
lunar-python==1.4.8
tzdata==2026.3
```

```bash
python -m pip install -r requirements.txt
python -c "from importlib.metadata import version; import tzdata; assert version('lunar_python') == '1.4.8'; assert version('tzdata') == '2026.3'; assert tzdata.IANA_VERSION == '2026c'; print('DEPENDENCY_PASS')"
```

Expected: `DEPENDENCY_PASS`。

- [ ] **Step 2: 寫 exact model tests**

```python
import unittest
from datetime import date, datetime, timezone
from engine.calendar.models import *

class CalendarModelTests(unittest.TestCase):
    def test_provider_negative_month_is_normalized(self):
        self.assertEqual(
            LunarDate.from_provider_values(2025, -6, 1),
            LunarDate(2025, 6, 1, True),
        )

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
            {"ok": False, "error": {
                "code": "invalid_datetime",
                "message": "bad input",
                "details": {"value": "x"},
            }},
        )

    def test_success_context_serializes_contract(self):
        context = CalendarContext(
            schema_version="1.0",
            resolver_version="1.0.0",
            input=CalendarInput("2026-09-18T14:00:00", "Asia/Taipei"),
            normalized_time=NormalizedTime(
                datetime(2026, 9, 18, 14, 0),
                datetime(2026, 9, 18, 6, 0, tzinfo=timezone.utc),
                "+08:00",
                date(2026, 9, 18),
                "Asia/Taipei",
                "未",
            ),
            lunar=LunarDate(2026, 8, 8, False),
            providers=ProviderBundle(
                LunarProviderMetadata(
                    "lunar-python", "1.4.8",
                    "000c8a3d74eed098d6256a28fdd51b869324c559",
                ),
                TimezoneProviderMetadata(
                    "tzdata", "2026.3", "2026c",
                    "a44279419071b7aa41ebe7eca301ebb2e759571a",
                ),
            ),
            validation=ValidationMetadata(
                ValidationCheck("validated", "hko-gregorian-lunar-1901-2100-v1"),
                ValidationCheck("validated", "tzdata-2026.3-iana-2026c-v1"),
                "validated",
                "1901-01-01/2100-12-31",
                None,
                (),
            ),
            policies=CalendarPolicies(
                "IANA legal local civil time",
                "local civil midnight (00:00)",
                "local civil clock; 子=23:00-00:59",
                False,
            ),
        )
        payload = CalendarResolution.success(context).to_dict()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["schema_version"], "1.0")
        self.assertEqual(payload["resolver_version"], "1.0.0")
        self.assertEqual(payload["providers"]["lunar_calendar"]["version"], "1.4.8")
        self.assertEqual(payload["providers"]["timezone_database"]["tzdb_version"], "2026c")
        self.assertFalse(payload["policies"]["metaphysics_day_boundary_applied"])
```

- [ ] **Step 3: 驗證先紅**

```bash
python -m unittest tests.test_calendar_models -v
```

Expected: FAIL because models 尚不存在。

- [ ] **Step 4: 實作 models**

所有 dataclass 欄位、名稱與型別必須完全依 Locked Public Interfaces。另固定：

```python
VALIDATION_PRECEDENCE = {
    "validated": 0,
    "out_of_validated_range": 1,
    "boundary_caution": 2,
    "boundary_conflict": 3,
}

def combine_validation_status(*statuses: str) -> str:
    return max(statuses, key=VALIDATION_PRECEDENCE.__getitem__)

class CalendarResolverException(ValueError):
    def __init__(self, code: str, message: str, details: dict | None = None):
        self.error = ResolverError(code, message, details or {})
        super().__init__(message)
```

`LunarDate.from_provider_values()` 必須使用 `abs(month)` 與 `month < 0`。所有 `to_dict()` 將 `datetime/date` 轉 ISO string、tuple notes 轉 list；`CalendarResolution.success(...).to_dict()` 回 `{"ok": True, **context.to_dict()}`，failure 只回 `ok=false + error`。

- [ ] **Step 5: PASS + export**

```bash
python -m unittest tests.test_calendar_precision tests.test_calendar_models -v
```

Expected: PASS。更新 `engine/calendar/__init__.py` export precision + models，但不要 import `lunar_python` 或建立 provider instance。

- [ ] **Step 6: Commit**

```bash
git add requirements.txt engine/calendar/models.py engine/calendar/__init__.py tests/test_calendar_models.py
git commit -m "feat: define calendar resolver contracts"
```

---

### Task 3: Gate 1｜Pinned timezone normalization + basic boundaries

**Files:**
- Create: `engine/calendar/timezone.py`
- Create: `tests/test_calendar_timezone.py`

**Interfaces:** `normalize_local_time(..., provider=None)` 必須與 Locked Public Interfaces 完全一致。

- [ ] **Step 1: 寫 basic failing tests**

```python
import unittest
from engine.calendar.models import CalendarResolverException
from engine.calendar.timezone import normalize_local_time

class CalendarTimezoneTests(unittest.TestCase):
    def test_taipei_ordinary_normalization(self):
        result = normalize_local_time("2026-09-18T14:00:00", "Asia/Taipei")
        self.assertEqual(result.utc_offset, "+08:00")
        self.assertEqual(result.utc_datetime.isoformat(), "2026-09-18T06:00:00+00:00")
        self.assertEqual(result.gregorian_date.isoformat(), "2026-09-18")
        self.assertEqual(result.hour_branch, "未")

    def test_embedded_offset_is_invalid_datetime(self):
        with self.assertRaises(CalendarResolverException) as ctx:
            normalize_local_time("2026-09-18T14:00:00+08:00", "Asia/Taipei")
        self.assertEqual(ctx.exception.error.code, "invalid_datetime")

    def test_invalid_iana_timezone(self):
        with self.assertRaises(CalendarResolverException) as ctx:
            normalize_local_time("2026-09-18T14:00:00", "Mars/Olympus")
        self.assertEqual(ctx.exception.error.code, "invalid_timezone")

    def test_hour_branch_does_not_change_civil_date_at_23(self):
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

- [ ] **Step 2: 驗證先紅**

```bash
python -m unittest tests.test_calendar_timezone -v
```

Expected: FAIL because timezone module 尚不存在。

- [ ] **Step 3: 實作 pinned provider 與 core helpers**

固定 provenance：

```python
EXPECTED_TZDATA_VERSION = "2026.3"
EXPECTED_IANA_VERSION = "2026c"
TIMEZONE_SOURCE_REVISION = "a44279419071b7aa41ebe7eca301ebb2e759571a"
TIMEZONE_PROFILE = "tzdata-2026.3-iana-2026c-v1"
ZHI = tuple("子丑寅卯辰巳午未申酉戌亥")
```

`PinnedTzdataProvider.__init__()` 必須 assert installed package / IANA versions；不符時 raise `CalendarResolverException("provider_failure", ...)`。

`zone()` 不使用 host OS `TZPATH`；使用：

```python
resource = files("tzdata.zoneinfo").joinpath(*timezone_name.split("/"))
with resource.open("rb") as handle:
    return ZoneInfo.from_file(handle, key=timezone_name)
```

空 segment、`.`、`..`、不存在檔案都轉 `invalid_timezone`。

`hour_branch(hour)` 固定：

```python
return ZHI[((hour + 1) // 2) % 12]
```

`parse_civil()` 用 `datetime.fromisoformat()`；解析失敗或已有 `tzinfo` 都轉 `invalid_datetime`。

`normalize_local_time()` 必須用傳入 `provider`；若為 `None` 才建立 `PinnedTzdataProvider()`。對 fold 0/1 各做 local→UTC→local round-trip，只有回到原 wall time且 offset 一致者才保留，最後依 `(utc, offset)` 去重。

- [ ] **Step 4: Gate 1 PASS**

```bash
python -m unittest tests.test_calendar_models tests.test_calendar_timezone -v
```

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add engine/calendar/timezone.py tests/test_calendar_timezone.py
git commit -m "feat: add pinned timezone normalization"
```

---

### Task 4: Gate 2｜DST ambiguity / nonexistent + historical timezone

**Files:**
- Modify: `tests/test_calendar_timezone.py`
- Modify: `engine/calendar/timezone.py` only if the new tests expose a defect.

**Interfaces:** 延續 Task 3，不新增 public API。

- [ ] **Step 1: 新增 exact DST tests**

```python
def test_new_york_spring_forward_gap_is_error(self):
    with self.assertRaises(CalendarResolverException) as ctx:
        normalize_local_time("2026-03-08T02:30:00", "America/New_York")
    self.assertEqual(ctx.exception.error.code, "nonexistent_local_time")


def test_new_york_fall_back_lists_two_candidates(self):
    with self.assertRaises(CalendarResolverException) as ctx:
        normalize_local_time("2026-11-01T01:30:00", "America/New_York")
    self.assertEqual(ctx.exception.error.code, "ambiguous_local_time")
    self.assertEqual(
        ctx.exception.error.details["candidates"],
        [
            {"utc_offset": "-04:00", "utc_datetime": "2026-11-01T05:30:00+00:00"},
            {"utc_offset": "-05:00", "utc_datetime": "2026-11-01T06:30:00+00:00"},
        ],
    )


def test_valid_offset_hints_choose_exact_candidate(self):
    first = normalize_local_time("2026-11-01T01:30:00", "America/New_York", "-04:00")
    second = normalize_local_time("2026-11-01T01:30:00", "America/New_York", "-05:00")
    self.assertEqual(first.utc_datetime.isoformat(), "2026-11-01T05:30:00+00:00")
    self.assertEqual(second.utc_datetime.isoformat(), "2026-11-01T06:30:00+00:00")


def test_invalid_offset_hint_is_rejected(self):
    with self.assertRaises(CalendarResolverException) as ctx:
        normalize_local_time("2026-11-01T01:30:00", "America/New_York", "-06:00")
    self.assertEqual(ctx.exception.error.code, "invalid_utc_offset_hint")


def test_unique_time_cannot_be_overridden_by_wrong_hint(self):
    with self.assertRaises(CalendarResolverException) as ctx:
        normalize_local_time("2026-07-15T12:00:00", "America/New_York", "-05:00")
    self.assertEqual(ctx.exception.error.code, "invalid_utc_offset_hint")
```

- [ ] **Step 2: 實作 ambiguity contract**

固定行為：0 candidates→`nonexistent_local_time`；2 candidates且無 hint→`ambiguous_local_time` + ordered candidate list；有 hint 時 parse `±HH:MM` 並且必須 exact-match one candidate，否則 `invalid_utc_offset_hint`。hint 不得覆寫 tzdb。

- [ ] **Step 3: 新增 exact round-trip / historical tests**

```python
def test_cross_zone_roundtrips(self):
    cases = (
        ("2026-01-15T12:00:00", "America/New_York", "-05:00"),
        ("2026-07-15T12:00:00", "America/New_York", "-04:00"),
        ("2026-01-15T12:00:00", "Europe/London", "+00:00"),
        ("2026-07-15T12:00:00", "Europe/London", "+01:00"),
        ("2026-07-15T12:00:00", "Asia/Tokyo", "+09:00"),
        ("2026-01-15T12:00:00", "Australia/Sydney", "+11:00"),
        ("2026-07-15T12:00:00", "Australia/Sydney", "+10:00"),
    )
    for value, zone, offset in cases:
        result = normalize_local_time(value, zone)
        self.assertEqual(result.utc_offset, offset)
        self.assertEqual(
            result.utc_datetime.astimezone(result.local_datetime.tzinfo).replace(tzinfo=None),
            result.local_datetime.replace(tzinfo=None),
        )


def test_historical_taipei_offsets(self):
    cases = (
        ("1937-09-30T12:00:00", "+08:00"),
        ("1937-10-01T12:00:00", "+09:00"),
        ("1945-09-20T12:00:00", "+09:00"),
        ("1945-09-21T12:00:00", "+08:00"),
        ("1946-06-01T12:00:00", "+09:00"),
        ("1946-11-01T12:00:00", "+08:00"),
        ("1979-08-01T12:00:00", "+09:00"),
        ("1979-11-01T12:00:00", "+08:00"),
    )
    for value, offset in cases:
        self.assertEqual(normalize_local_time(value, "Asia/Taipei").utc_offset, offset)
```

- [ ] **Step 4: Gate 2 PASS**

```bash
python -m unittest tests.test_calendar_timezone -v
```

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add engine/calendar/timezone.py tests/test_calendar_timezone.py
git commit -m "test: lock calendar DST and historical timezone behavior"
```

---

### Task 5: Gate 3｜lunar-python provider + HKO validation profile

**Files:**
- Create: `engine/calendar/lunar.py`
- Create: `tests/test_calendar_lunar.py`

**Interfaces:** 使用 Locked Public Interfaces 的 `LunarCalendarProvider`、`LunarPythonProvider`、`calendar_validation_for()`。

- [ ] **Step 1: 寫 failing tests**

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
    def test_known_lunar_new_year(self):
        self.assertEqual(
            LunarPythonProvider().convert(date(2025, 1, 29)),
            LunarDate(2025, 1, 1, False),
        )

    def test_known_2025_leap_sixth_month(self):
        self.assertEqual(
            LunarPythonProvider().convert(date(2025, 7, 25)),
            LunarDate(2025, 6, 1, True),
        )

    def test_validated_edges(self):
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

    def test_out_of_validated_range(self):
        self.assertEqual(
            calendar_validation_for(date(2150, 3, 1)).check.status,
            "out_of_validated_range",
        )

    @patch("engine.calendar.lunar.Solar.fromYmd", side_effect=IndexError("unsupported"))
    def test_provider_unsupported_date(self, _mock):
        with self.assertRaises(LunarProviderUnsupportedDate):
            LunarPythonProvider().convert(date(2150, 3, 1))

    @patch("engine.calendar.lunar.Solar.fromYmd", side_effect=RuntimeError("boom"))
    def test_provider_failure(self, _mock):
        with self.assertRaises(LunarProviderFailure):
            LunarPythonProvider().convert(date(2026, 8, 21))
```

- [ ] **Step 2: 驗證先紅**

```bash
python -m unittest tests.test_calendar_lunar -v
```

Expected: FAIL because lunar module 尚不存在。

- [ ] **Step 3: 實作 exact provider**

```python
EXPECTED_LUNAR_VERSION = "1.4.8"
LUNAR_SOURCE_REVISION = "000c8a3d74eed098d6256a28fdd51b869324c559"
CALENDAR_PROFILE = "hko-gregorian-lunar-1901-2100-v1"
VALIDATED_START = date(1901, 1, 1)
VALIDATED_END = date(2100, 12, 31)
CONFLICT_START = date(2057, 9, 28)
CONFLICT_END = date(2057, 10, 27)
```

`LunarPythonProvider.__init__()` 檢查 `version("lunar_python") == "1.4.8"`；不符 raise `LunarProviderFailure`。`convert()` 使用：

```python
lunar = Solar.fromYmd(civil_date.year, civil_date.month, civil_date.day).getLunar()
return LunarDate.from_provider_values(lunar.getYear(), lunar.getMonth(), lunar.getDay())
```

`ValueError` / `IndexError`→`LunarProviderUnsupportedDate`；其他 unexpected exception→`LunarProviderFailure`。

- [ ] **Step 4: 實作 exact validation decision**

判斷順序：2057 conflict window → 2089/2097 exact caution → outside validated range → validated。

Boundary IDs 固定：

```text
hko-new-moon-2057-09-28-conflict
hko-new-moon-2089-09-04-caution
hko-new-moon-2097-08-07-caution
```

`validated_range` 固定 `1901-01-01/2100-12-31`。

- [ ] **Step 5: Gate 3 PASS**

```bash
python -m unittest tests.test_calendar_lunar -v
```

Expected: PASS。

- [ ] **Step 6: Commit**

```bash
git add engine/calendar/lunar.py tests/test_calendar_lunar.py
git commit -m "feat: add lunar provider and validation profile"
```

---

### Task 6: Resolver orchestration

**Files:**
- Create: `engine/calendar/resolver.py`
- Create: `tests/test_calendar_resolver.py`
- Modify: `engine/calendar/__init__.py`

**Interfaces:** `resolve_calendar()` exact signature使用 Locked Public Interfaces；必須把 `timezone_provider` 傳給 `normalize_local_time(..., provider=timezone_provider)`，把 `lunar_provider` 用作 conversion provider。

- [ ] **Step 1: 寫 resolver failing tests**

```python
import unittest
from datetime import date
from engine.calendar.models import LunarDate, LunarProviderMetadata
from engine.calendar.resolver import resolve_calendar

class StubFutureProvider:
    metadata = LunarProviderMetadata("stub", "1", "test-only")
    def convert(self, civil_date: date) -> LunarDate:
        return LunarDate(2150, 1, 1, False)

class CalendarResolverTests(unittest.TestCase):
    def test_success_context(self):
        result = resolve_calendar("2026-09-18T14:00:00", "Asia/Taipei")
        self.assertTrue(result.ok)
        context = result.context
        assert context is not None
        self.assertEqual(context.schema_version, "1.0")
        self.assertEqual(context.resolver_version, "1.0.0")
        self.assertEqual(context.normalized_time.hour_branch, "未")
        self.assertFalse(context.policies.metaphysics_day_boundary_applied)
        self.assertEqual(context.providers.lunar_calendar.version, "1.4.8")
        self.assertEqual(context.providers.timezone_database.tzdb_version, "2026c")

    def test_23xx_keeps_same_civil_date(self):
        result = resolve_calendar("2026-09-18T23:30:00", "Asia/Taipei")
        context = result.context
        assert context is not None
        self.assertEqual(context.normalized_time.gregorian_date.isoformat(), "2026-09-18")
        self.assertEqual(context.normalized_time.hour_branch, "子")
        self.assertFalse(context.policies.metaphysics_day_boundary_applied)

    def test_boundary_conflict_remains_success_with_conflict_metadata(self):
        result = resolve_calendar("2057-09-28T12:00:00", "Asia/Taipei")
        self.assertTrue(result.ok)
        context = result.context
        assert context is not None
        self.assertEqual(context.validation.calendar_conversion.status, "boundary_conflict")
        self.assertEqual(context.validation.overall_status, "boundary_conflict")

    def test_out_of_range_provider_success_is_not_error(self):
        result = resolve_calendar(
            "2150-03-01T12:00:00",
            "Asia/Taipei",
            lunar_provider=StubFutureProvider(),
        )
        self.assertTrue(result.ok)
        context = result.context
        assert context is not None
        self.assertEqual(context.validation.calendar_conversion.status, "out_of_validated_range")

    def test_invalid_timezone_returns_public_error(self):
        result = resolve_calendar("2026-09-18T14:00:00", "Mars/Olympus")
        self.assertFalse(result.ok)
        assert result.error is not None
        self.assertEqual(result.error.code, "invalid_timezone")
```

- [ ] **Step 2: 驗證先紅**

```bash
python -m unittest tests.test_calendar_resolver -v
```

Expected: FAIL because resolver module 尚不存在。

- [ ] **Step 3: 實作 orchestration**

固定：

```text
schema_version = "1.0"
resolver_version = "1.0.0"
timezone profile = "tzdata-2026.3-iana-2026c-v1"
```

流程只能是：normalize local time → convert normalized Gregorian date → calendar validation → combine statuses → build context。成功 timezone validation status 固定 `validated`。

Policies 固定：

```text
IANA legal local civil time
local civil midnight (00:00)
local civil clock; 子=23:00-00:59
false
```

錯誤 mapping：`CalendarResolverException`→其 `ResolverError`；`LunarProviderUnsupportedDate`→`provider_unsupported_date`；`LunarProviderFailure`→`provider_failure`。`boundary_conflict` 仍 `ok=true`，不得改 lunar result。

- [ ] **Step 4: PASS + all Gate 0～3 regression**

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

- [ ] **Step 5: Export + Commit**

`engine/calendar/__init__.py` 公開 `TimePrecision`、`PrecisionAssessment`、`assess_precision`、`CalendarContext`、`CalendarResolution`、`resolve_calendar`；不得 import `engine.ziwei`。

```bash
git add engine/calendar/resolver.py engine/calendar/__init__.py tests/test_calendar_resolver.py
git commit -m "feat: add calendar resolver orchestration"
```

---

### Task 7: Gate 4｜Ziwei Calendar Adapter

**Files:**
- Create: `engine/ziwei/calendar_adapter.py`
- Create: `tests/test_ziwei_calendar_adapter.py`
- Modify: `engine/ziwei/hour.py`
- Modify: `tests/test_project_ziwei_hour.py`

**Interfaces:** 三個 adapter function exact signature使用 Locked Public Interfaces；既有 month/day/hour core signature不得改。

- [ ] **Step 1: 先讓既有 availability flag 測試變紅**

將 `tests/test_project_ziwei_hour.py` 中唯一這一項目標改成：

```python
self.assertTrue(result["features"]["calendar_resolver_implemented"])
```

```bash
python -m unittest tests.test_project_ziwei_hour -v
```

Expected: FAIL only on this availability flag；若其他 existing expected 失敗，停止並查 root cause。

- [ ] **Step 2: 最小更新 hour metadata**

只把 `engine/ziwei/hour.py` structured output 的：

```python
"calendar_resolver_implemented": True,
```

不得新增 Resolver import 或 civil datetime parameters。

```bash
python -m unittest tests.test_project_ziwei_hour -v
```

Expected: PASS。

- [ ] **Step 3: 寫 adapter failing tests**

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
    def test_month_adapter_passes_resolved_lunar_fields(self):
        context = resolve_calendar("2025-01-29T12:00:00", "Asia/Taipei").context
        assert context is not None
        adapted = ziwei_month_from_calendar(context, 5, "戌", "巳")
        expected = project_derived_ziwei_month(
            5, "戌", "巳",
            context.lunar.month, context.lunar.day, context.lunar.is_leap_month,
        )
        self.assertEqual(adapted["ziwei"], expected)

    def test_day_adapter_passes_resolved_lunar_fields(self):
        context = resolve_calendar("2025-01-29T12:00:00", "Asia/Taipei").context
        assert context is not None
        adapted = ziwei_day_from_calendar(context, 5, "戌", "巳")
        expected = project_derived_ziwei_day(
            5, "戌", "巳",
            context.lunar.month, context.lunar.day, context.lunar.is_leap_month,
        )
        self.assertEqual(adapted["ziwei"], expected)

    def test_hour_adapter_uses_resolver_hour_branch_without_day_rollover(self):
        context = resolve_calendar("2026-09-18T23:30:00", "Asia/Taipei").context
        assert context is not None
        adapted = ziwei_hour_from_calendar(context, 5, "戌", "午")
        expected = project_derived_ziwei_hour(
            5, "戌", "午",
            context.lunar.month, context.lunar.day, context.lunar.is_leap_month,
            "子",
        )
        self.assertEqual(adapted["ziwei"], expected)
        self.assertEqual(adapted["calendar"]["gregorian_date"], "2026-09-18")
        self.assertFalse(adapted["calendar"]["metaphysics_day_boundary_applied"])

    def test_boundary_conflict_is_rejected(self):
        context = resolve_calendar("2057-09-28T12:00:00", "Asia/Taipei").context
        assert context is not None
        with self.assertRaises(ZiweiCalendarAdapterError) as ctx:
            ziwei_day_from_calendar(context, 5, "戌", "巳")
        self.assertEqual(ctx.exception.code, "boundary_conflict")
```

- [ ] **Step 4: 驗證先紅**

```bash
python -m unittest tests.test_ziwei_calendar_adapter -v
```

Expected: FAIL because adapter module 尚不存在。

- [ ] **Step 5: 實作 adapter**

```python
class ZiweiCalendarAdapterError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)

def _ensure_usable_context(context: CalendarContext) -> None:
    if context.validation.calendar_conversion.status == "boundary_conflict":
        raise ZiweiCalendarAdapterError(
            "boundary_conflict",
            context.validation.boundary_id or "calendar boundary conflict",
        )
```

三個 adapter 都先 `_ensure_usable_context()`，再原樣傳 `context.lunar.month/day/is_leap_month`；hour 另傳 `context.normalized_time.hour_branch`。回傳固定：

```python
{
    "calendar": {
        "gregorian_date": context.normalized_time.gregorian_date.isoformat(),
        "lunar": {
            "year": context.lunar.year,
            "month": context.lunar.month,
            "day": context.lunar.day,
            "is_leap_month": context.lunar.is_leap_month,
        },
        "hour_branch": context.normalized_time.hour_branch,
        "calendar_validation_status": context.validation.calendar_conversion.status,
        "boundary_id": context.validation.boundary_id,
        "metaphysics_day_boundary_applied": context.policies.metaphysics_day_boundary_applied,
    },
    "ziwei": existing_core_output,
}
```

不得修改 lunar date、重新轉曆、重新解析 timezone、套 Bazi 23:00 policy、或替 conflict 偷選 oracle date。

- [ ] **Step 6: Gate 4 PASS**

```bash
python -m unittest \
  tests.test_ziwei_calendar_adapter \
  tests.test_project_ziwei_month \
  tests.test_project_ziwei_day \
  tests.test_project_ziwei_hour \
  -v
```

Expected: PASS。

- [ ] **Step 7: Commit**

```bash
git add engine/ziwei/calendar_adapter.py engine/ziwei/hour.py tests/test_ziwei_calendar_adapter.py tests/test_project_ziwei_hour.py
git commit -m "feat: connect calendar resolver to Ziwei"
```

---

### Task 8: Public exports、docs、version、full regression

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

**Interfaces:** 不新增 runtime API；只鎖定 exports、文件與發布狀態。

- [ ] **Step 1: 寫 export test**

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
```

```bash
python -m unittest tests.test_calendar_package_exports -v
```

若 FAIL，只補缺失 export。

- [ ] **Step 2: README / 架構說明改成 exact status**

必須寫入：

```text
Calendar Resolver v1 = implemented
Input Resolution / Precision Gate = upstream pure policy
natural-language parsing = outside Resolver
runtime lunar = lunar-python 1.4.8
HKO validated range = 1901-01-01..2100-12-31
2057-09-28..2057-10-27 = boundary_conflict
2089-09-04 / 2097-08-07 = boundary_caution
timezone = pinned tzdata 2026.3 / IANA 2026c
23:00 = 子時，但 civil date 只在 00:00 換日
metaphysics_day_boundary_applied = false
Ziwei = first adapter
Bazi refactor = not included
```

同時刪除「Calendar / Input Resolver 尚未實作」的舊描述；不得寫成 2100 以外已驗證、CWA exhaustive automation 已完成、或紫微 23:00 日界已決定。

- [ ] **Step 3: 安裝／更新文件列出 exact runtime set**

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

明寫需要 `pip install -r requirements.txt`；缺少 exact dependencies 時不得宣稱 Resolver 可執行。

- [ ] **Step 4: core 規範同步 Input Resolution Gate**

新增四條明文規則：

```text
先判斷 target capability 最低時間精度。
不足 → 追問 / 保留候選 / 降級。
不得為下游 API 補假日期／假時間。
Resolver neutral civil/calendar context 與 Bazi/Ziwei/Qimen day-boundary policy 分離。
```

不得修改「先盲判、再事件校準」流程。

- [ ] **Step 5: VERSION.md exact change**

保留：

```text
Metaphysics Lab Core：v1.1.0
```

不把 v1.2 開發線誤發布成正式版。於「v1.2 開發線狀態」新增／修改為：

```text
Metaphysics Lab Calendar Resolver：v1.0.0
Calendar / Input Resolver：implemented
Ziwei Calendar Adapter：implemented
```

「相容性」中的 Resolver 改成：

```text
Calendar / Input Resolver：v1.2 開發線已實作 v1.0.0；需要 lunar-python 1.4.8 與 tzdata 2026.3。
```

- [ ] **Step 6: CHANGELOG.md exact change**

在 `未發布｜v1.2 引擎重構與細時間 capability` 新增 `### Calendar Resolver v1`，列：precision gate、pinned providers、HKO range/boundaries、DST contract、Ziwei first adapter、Bazi unchanged。並從「後續尚未實作」移除 `Calendar / Input Resolver`；保留紫微 transformations / Cross-System Validation 尚未實作。

- [ ] **Step 7: Calendar subsystem regression**

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

- [ ] **Step 8: Full repo regression**

```bash
python -m unittest discover -v
```

Expected: 全部 PASS；既有 Bazi、Ziwei month/day/hour、capability registry、wrapper、CLI tests 全部維持 PASS。

- [ ] **Step 9: Provenance gate**

```bash
python -c "from importlib.metadata import version; import tzdata; assert version('lunar_python') == '1.4.8'; assert version('tzdata') == '2026.3'; assert tzdata.IANA_VERSION == '2026c'; print('PROVENANCE_PASS')"
```

Expected: `PROVENANCE_PASS`。

- [ ] **Step 10: Scope diff gate**

```bash
git diff --stat design/calendar-resolver...HEAD
git diff --name-only design/calendar-resolver...HEAD
```

確認沒有 Bazi refactor、Qimen implementation、紫微 transformations / 流曜 / 細飛、qualification probe workflow 回流、或真實命主私人資料。

- [ ] **Step 11: Commit**

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

- [ ] Baseline repo suite 在任何 implementation 前 PASS。
- [ ] Gate 0 precision policy PASS。
- [ ] Gate 1 model/basic timezone/error contract PASS。
- [ ] Gate 2 DST / historical timezone PASS。
- [ ] Gate 3 lunar provider / HKO validation contract PASS。
- [ ] Gate 4 Ziwei adapter integration PASS。
- [ ] `23:30` 仍是當日 civil date、hour branch=子、`metaphysics_day_boundary_applied=false`。
- [ ] `2057-09-28..2057-10-27` 不被靜默當 validated。
- [ ] `2089-09-04` / `2097-08-07` 保留 caution。
- [ ] 2100 以外不宣稱 validated。
- [ ] malformed / ambiguous timezone input 不被偷偷猜值。
- [ ] `lunar-python==1.4.8` / `tzdata==2026.3` / `IANA 2026c` provenance PASS。
- [ ] existing Ziwei month/day/hour behavior 維持 PASS。
- [ ] Bazi engine 沒有被 refactor。
- [ ] 完整 `python -m unittest discover -v` PASS。
- [ ] docs 與實際 API / validation status 一致。

只有全部 PASS 後，Calendar Resolver v1 才可進入 branch finishing / PR review；任何一項 FAIL 都停在當前 task 修正，不得把未驗證問題帶到下一步。
