# Ziwei Fine Cycle Stem Resolver v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立紫微流月／流日／流時天干 resolver，將合法解析出的細運干支接入既有 Transformation/Flying/Composition Core，並以公開 qualification 與 fail-closed gate 驗證後，第一版以 `experimental / on_demand` 啟用。

**Architecture:** `CalendarContext` 保持 neutral civil/calendar fact source；`engine/calendar/sexagenary.py` 提供不含命理日界的純六十甲子數學；`engine/ziwei/fine_cycle_stems.py` 套用 `ziwei-fine-cycle-lunar-late-zi-v1` profile 解析 monthly/daily/hourly stems；`engine/ziwei/fine_cycle.py` 只負責把 `ResolvedCycleStem` 接到既有 `get_transformation_set()`、`fly_transformations()`、`build_cycle_layer()`。Composition 正式增加 `monthly / daily / hourly` scopes，但保留 Phase 2A duplicate/conflict/chart-isolation invariants。

**Tech Stack:** Python 3.9+ compatible syntax、標準函式庫 `datetime` / `dataclasses` / `unittest` / `unittest.mock`、既有 `engine.calendar`、`engine.ziwei`；公開 qualification 解析 pinned GitHub source text，不增加 Node/npm runtime dependency。

**Spec:** `docs/superpowers/specs/2026-08-21-Ziwei-Fine-Cycle-Stem-Resolver-設計.md`

## Global Constraints

- Base baseline：Metaphysics Lab v1.2.0 release commit `e6ac041a16117402207e086b875904b41b674e59`。
- Implementation 必須從核准後的 `design/ziwei-fine-cycle-stem-resolver` exact head 建立 `feature/ziwei-fine-cycle-stem-resolver-v1`；不得直接改 `main`。
- 執行前使用 isolated worktree／等價隔離 branch；不得在已污染 working tree 上開始。
- Calendar Resolver 只提供 neutral civil/calendar facts；不得修改成紫微專用 resolver。
- Fine-cycle resolver 正式 orchestration 唯一 civil/calendar entry point 是 `CalendarContext`。
- Fine-cycle resolver 不 import `engine.bazi.calendar`；可以複用相同數學，但不得繼承 Bazi month/day-boundary policy。
- Production runtime 不 import Node/npm、不呼叫 iztro/lunar-lite、不連外。
- 第一版 profile 固定 `profile_id = ziwei-fine-cycle-lunar-late-zi-v1`、`rule_version = 1.0-exp`。
- 月份 basis 固定農曆月；閏月初一至十五歸原月、十六日起進下一 effective month。
- `late_zi_forward-v1`：00:00–22:59 使用 civil date；23:00–23:59 day stem 使用 civil date + 1 day。
- late-Zi 不提前切換 monthly stem；月界與 day-stem boundary 必須分離。
- Hour stem 必須以 effective Ziwei day stem 起五鼠遁。
- `metaphysics_day_boundary_applied = true` 必須 fail closed，error code `calendar_boundary_already_applied`。
- Calendar `boundary_conflict` 必須 fail closed；`boundary_caution` / `out_of_validated_range` 可輸出但 validation/provenance 不得被洗成 fully validated。
- 新增 `ZiweiFineCycleError`，不得改寫、重新命名或破壞既有 `ZiweiPhase2AError` contract。
- Fine-cycle stems / transformations / flying 第一版一律 `implemented / experimental / on_demand / 1.0-exp`。
- `ziwei.flowing_stars` 仍維持 planned；Phase 2C 才處理流曜。
- 不新增吉凶 scoring、resonance、final state、自動強弱排序或 AI interpretation。
- 不自動遍歷全年每日每時。
- Astralium fine-cycle private qualification 第一版固定 `pending`；不得反推 expected values 冒充 PASS。
- 每個 Task 必須走 RED → 確認 RED 原因 → minimal GREEN → targeted regression → commit；任何 Gate FAIL 立即停止，不把 failure 帶到下一 Task。
- 每個 promotion/merge 前必須跑 exact-head verification；feature→design 與 design→main 都需要使用者分別明確核准，不得自動 merge。

---

## File Map

### 新增

- `engine/calendar/sexagenary.py`：純 Gregorian/JDN/sexagenary helper，不套 Ziwei/Bazi boundary policy。
- `engine/ziwei/fine_cycle_stems.py`：Ziwei profile、CalendarContext validation、monthly/daily/hourly `ResolvedCycleStem` resolver。
- `engine/ziwei/fine_cycle.py`：resolved stem → existing Transformation/Flying/Composition thin orchestration。
- `tests/test_rule_source_reconciliation.py`：core 規則來源與 runtime capability 狀態一致性 gate。
- `tests/test_calendar_sexagenary.py`：純六十甲子 helper invariants。
- `tests/ziwei_phase2b_fixtures.py`：可重用 CalendarContext / Phase 2A chart fixture builders。
- `tests/test_ziwei_fine_cycle_stems.py`：profile、month/day/hour resolver、boundary/error tests。
- `tests/test_ziwei_fine_cycle_integration.py`：Transformation/Flying/Composition integration。
- `tests/test_ziwei_phase2b_capabilities.py`：capability lifecycle。
- `tests/test_ziwei_phase2b_qualification.py`：public/private qualification artifact contract。
- `tools/qualify_ziwei_phase2b_public.py`：解析 pinned lunar-lite / iztro source text 並產生 public evidence JSON。
- `qualification/ziwei/phase2b/public-lunar-lite-1d104fff.json`：公開 GanZhi qualification aggregate evidence。
- `qualification/ziwei/phase2b/public-iztro-814b77e6.json`：公開 fine-cycle stem→mutagen integration evidence。
- `qualification/ziwei/phase2b/private-astralium-summary.json`：只保存 pending aggregate，不含 raw chart。

### 修改

- `core/命理分析作業規範.md`
- `core/命理推導計算規則.md`
- `core/核心提示詞.md`
- `core/紫微流月推導規則.md`
- `core/紫微流日推導規則.md`
- `core/紫微流時推導規則.md`
- `engine/ziwei/errors.py`
- `engine/ziwei/models.py`
- `engine/ziwei/capabilities.py`
- `engine/ziwei/composition.py`
- `README.md`
- `CHANGELOG.md`
- `docs/架構說明.md`
- `docs/快速開始.md`
- `docs/安裝到ChatGPT-Project.md`
- `docs/更新與版本同步.md`

### 預設不修改

- `engine/bazi/*`
- `engine/ziwei/month.py`
- `engine/ziwei/day.py`
- `engine/ziwei/hour.py`
- `engine/ziwei/transformation_profiles.py`
- `engine/ziwei/transformations.py`
- `engine/ziwei/flying.py`

若 implementation 發現必須修改上述檔案，立即停止該 Task、記錄理由並做 scope review；不得順手修改。

---

### Task 0: Reconcile Formal Rule Sources Before Fine-Cycle Code

**Files:**
- Create: `tests/test_rule_source_reconciliation.py`
- Modify: six `core/*.md` rule files listed in File Map

**Interfaces:**
- Consumes: current `engine/ziwei/capabilities.py` states and Calendar Resolver v1 already in `main`.
- Produces: rule-source baseline that describes existing runtime facts consistently; Phase 2B fine-cycle transformation/flying remains planned at this Task.

- [ ] **Step 1: Write the RED rule-source test**

```python
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "core/命理分析作業規範.md",
    "core/命理推導計算規則.md",
    "core/核心提示詞.md",
    "core/紫微流月推導規則.md",
    "core/紫微流日推導規則.md",
    "core/紫微流時推導規則.md",
)


class RuleSourceReconciliationTests(unittest.TestCase):
    def _combined(self):
        return "\n".join((ROOT / path).read_text(encoding="utf-8") for path in FILES)

    def test_existing_runtime_capabilities_are_documented_as_existing(self):
        combined = self._combined()
        self.assertIn("Calendar Resolver v1", combined)
        self.assertIn("紫微流月定位", combined)
        self.assertIn("紫微流日定位", combined)
        self.assertIn("紫微流時定位", combined)
        self.assertIn("Ziwei Transformation Core", combined)
        self.assertIn("Ziwei Flying Core", combined)

    def test_stale_missing_runtime_statements_are_removed(self):
        combined = self._combined()
        for forbidden in (
            "Calendar / Input Resolver\n",
            "Calendar Resolver、timezone、國曆轉農曆與 23:00 日界 policy 尚未實作",
            "Project 紫微流月定位層",
            "Project 紫微流日定位層",
            "Project 紫微流時定位層",
        ):
            self.assertNotIn(forbidden, combined)

    def test_phase2b_fine_cycle_is_not_prematurely_promoted(self):
        text = (ROOT / "core/命理推導計算規則.md").read_text(encoding="utf-8")
        self.assertIn("流月／流日／流時細部四化", text)
        self.assertIn("planned", text.lower())


if __name__ == "__main__":
    unittest.main()
```

Note: `Project Bazi Calendar Engine` may remain inside historical engine metadata if it is the literal legacy engine name; the capability/user-facing label must be `八字時間推導`. Do not fail a historical metadata string solely because it contains `Project`.

- [ ] **Step 2: Run RED and verify failure reason**

```bash
python -m unittest tests.test_rule_source_reconciliation -v
```

Expected: assertion failure caused by stale core wording. Syntax/import failure is not an acceptable RED.

- [ ] **Step 3: Reconcile only existing runtime facts**

All six core documents must converge on this state:

```text
Calendar Resolver v1 = implemented neutral infrastructure
紫微流月定位 = implemented / stable / default
紫微流日定位 = implemented / experimental / on_demand
紫微流時定位 = implemented / experimental / on_demand
Ziwei Transformation Core = implemented / stable / on_demand
Ziwei Flying Core = implemented / stable / on_demand
流月／流日／流時四化 = planned / on_demand
流月／流日／流時飛化 = planned / on_demand
流曜 = planned / on_demand
```

`Project 推導盤面` remains a data-classification term, not a capability prefix.

- [ ] **Step 4: Run GREEN and full baseline regression**

```bash
python -m unittest tests.test_rule_source_reconciliation -v
python -m unittest discover -v
```

Expected: PASS and full count >= 132.

- [ ] **Step 5: Commit only after the gate passes**

```text
RULE_SOURCE_RECONCILIATION_PASS
```

```bash
git add core tests/test_rule_source_reconciliation.py
git commit -m "docs: reconcile Ziwei runtime rule sources"
```

---

### Task 1: Extract Neutral Sexagenary Math from Policy

**Files:**
- Create: `engine/calendar/sexagenary.py`
- Create: `tests/test_calendar_sexagenary.py`

**Interfaces:**

```python
gregorian_jdn(value: date) -> int
sexagenary_day(value: date) -> tuple[str, str]
lunar_year_stem(lunar_year: int) -> str
five_tiger_month(year_stem: str, effective_month_ordinal: int) -> tuple[str, str]
five_mouse_hour(day_stem: str, hour_branch: str) -> tuple[str, str]
```

No function in this module accepts `CalendarContext` or applies a 23:00 policy.

- [ ] **Step 1: Write RED tests**

```python
import unittest
from datetime import date

from engine.calendar.sexagenary import (
    five_mouse_hour,
    five_tiger_month,
    lunar_year_stem,
    sexagenary_day,
)


class CalendarSexagenaryTests(unittest.TestCase):
    def test_known_public_days(self):
        self.assertEqual(sexagenary_day(date(2023, 3, 9)), ("丙", "寅"))
        self.assertEqual(sexagenary_day(date(2023, 4, 8)), ("丙", "申"))
        self.assertEqual(sexagenary_day(date(1987, 12, 6)), ("己", "丑"))
        self.assertEqual(sexagenary_day(date(1987, 12, 7)), ("庚", "寅"))

    def test_lunar_year_stem_cycle(self):
        self.assertEqual(lunar_year_stem(2023), "癸")
        self.assertEqual(lunar_year_stem(2083), "癸")

    def test_five_tiger_vectors(self):
        self.assertEqual(five_tiger_month("癸", 1), ("甲", "寅"))
        self.assertEqual(five_tiger_month("癸", 6), ("己", "未"))
        self.assertEqual(five_tiger_month("癸", 13), ("丙", "寅"))

    def test_five_mouse_vectors(self):
        self.assertEqual(five_mouse_hour("己", "丑"), ("乙", "丑"))
        self.assertEqual(five_mouse_hour("己", "亥"), ("乙", "亥"))
        self.assertEqual(five_mouse_hour("庚", "子"), ("丙", "子"))

    def test_invalid_inputs_fail_closed(self):
        with self.assertRaises(ValueError):
            five_tiger_month("X", 1)
        with self.assertRaises(ValueError):
            five_tiger_month("甲", 0)
        with self.assertRaises(ValueError):
            five_tiger_month("甲", 14)
        with self.assertRaises(ValueError):
            five_mouse_hour("X", "子")
        with self.assertRaises(ValueError):
            five_mouse_hour("甲", "X")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Verify RED**

```bash
python -m unittest tests.test_calendar_sexagenary -v
```

Expected: `ModuleNotFoundError: engine.calendar.sexagenary`.

- [ ] **Step 3: Implement the neutral helper**

```python
from __future__ import annotations

from datetime import date

GAN = tuple("甲乙丙丁戊己庚辛壬癸")
ZHI = tuple("子丑寅卯辰巳午未申酉戌亥")
MONTH_ZHI = tuple("寅卯辰巳午未申酉戌亥子丑")
FIRST_MONTH_STEM = {
    "甲": "丙", "己": "丙", "乙": "戊", "庚": "戊", "丙": "庚",
    "辛": "庚", "丁": "壬", "壬": "壬", "戊": "甲", "癸": "甲",
}
FIRST_HOUR_STEM = {
    "甲": "甲", "己": "甲", "乙": "丙", "庚": "丙", "丙": "戊",
    "辛": "戊", "丁": "庚", "壬": "庚", "戊": "壬", "癸": "壬",
}


def gregorian_jdn(value: date) -> int:
    year, month, day = value.year, value.month, value.day
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    return day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045


def sexagenary_day(value: date) -> tuple[str, str]:
    offset = gregorian_jdn(value) - 11
    return GAN[offset % 10], ZHI[offset % 12]


def lunar_year_stem(lunar_year: int) -> str:
    if not isinstance(lunar_year, int):
        raise ValueError("lunar_year must be int")
    return GAN[(lunar_year - 4) % 10]


def five_tiger_month(year_stem: str, effective_month_ordinal: int) -> tuple[str, str]:
    if year_stem not in FIRST_MONTH_STEM:
        raise ValueError("invalid heavenly stem")
    if not 1 <= effective_month_ordinal <= 13:
        raise ValueError("effective_month_ordinal must be 1..13")
    offset = effective_month_ordinal - 1
    start = GAN.index(FIRST_MONTH_STEM[year_stem])
    return GAN[(start + offset) % 10], MONTH_ZHI[offset % 12]


def five_mouse_hour(day_stem: str, hour_branch: str) -> tuple[str, str]:
    if day_stem not in FIRST_HOUR_STEM:
        raise ValueError("invalid heavenly stem")
    if hour_branch not in ZHI:
        raise ValueError("invalid earthly branch")
    branch_index = ZHI.index(hour_branch)
    start = GAN.index(FIRST_HOUR_STEM[day_stem])
    return GAN[(start + branch_index) % 10], hour_branch
```

- [ ] **Step 4: Run GREEN + Bazi regression**

```bash
python -m unittest tests.test_calendar_sexagenary -v
python -m unittest tests.test_project_bazi_calendar -v
```

Expected: both PASS; no Bazi production file changed.

- [ ] **Step 5: Commit**

```bash
git add engine/calendar/sexagenary.py tests/test_calendar_sexagenary.py
git commit -m "feat: add neutral sexagenary calendar helpers"
```

---

### Task 2: Add Fine-Cycle Error Contract, Models, and Test Fixture

**Files:**
- Modify: `engine/ziwei/errors.py`
- Modify: `engine/ziwei/models.py`
- Create: `tests/ziwei_phase2b_fixtures.py`
- Create: `tests/test_ziwei_fine_cycle_stems.py`

**Interfaces:**

```python
ZiweiFineCycleError(code: str, message: str, details: Mapping | None = None)
FineCycleStemProfile
ResolvedCycleStem
calendar_context(...) -> CalendarContext
```

- [ ] **Step 1: Write RED model/error tests**

```python
import unittest
from dataclasses import FrozenInstanceError
from datetime import date

from engine.ziwei.errors import ZiweiFineCycleError, ZiweiPhase2AError
from engine.ziwei.models import LayerProvenance, ResolvedCycleStem


class FineCycleModelTests(unittest.TestCase):
    def test_phase2a_error_contract_remains(self):
        error = ZiweiPhase2AError("x", "message", {"a": 1})
        self.assertEqual(error.code, "x")
        self.assertEqual(error.details, {"a": 1})

    def test_fine_cycle_error_contract(self):
        error = ZiweiFineCycleError("invalid_fine_cycle_scope", "message", {"scope": "weekly"})
        self.assertEqual(error.code, "invalid_fine_cycle_scope")
        self.assertEqual(error.details, {"scope": "weekly"})

    def test_resolved_cycle_stem_is_frozen(self):
        provenance = LayerProvenance("project_derived", "Metaphysics Lab", None, "p", "1", "test")
        item = ResolvedCycleStem(
            "daily", "ziwei-day:2026-08-22@late_zi_forward-v1", "甲", "子",
            "ziwei-fine-cycle-lunar-late-zi-v1", "1.0-exp",
            date(2026, 8, 21), date(2026, 8, 22), None, "validated", provenance,
        )
        with self.assertRaises(FrozenInstanceError):
            item.heavenly_stem = "乙"
```

- [ ] **Step 2: Verify RED**

```bash
python -m unittest tests.test_ziwei_fine_cycle_stems.FineCycleModelTests -v
```

Expected: new imports are missing.

- [ ] **Step 3: Add error and dataclasses**

Append without altering `ZiweiPhase2AError`:

```python
class ZiweiFineCycleError(ValueError):
    def __init__(self, code, message, details=None):
        self.code = code
        self.details = dict(details or {})
        super().__init__(message)
```

Add to `models.py`:

```python
from datetime import date

@dataclass(frozen=True)
class FineCycleStemProfile:
    profile_id: str
    rule_version: str
    month_basis: str
    leap_month_policy: str
    lunar_year_basis: str
    ziwei_day_boundary: str
    hour_stem_basis: str

@dataclass(frozen=True)
class ResolvedCycleStem:
    scope: str
    reference: str
    heavenly_stem: str
    earthly_branch: str
    profile_id: str
    rule_version: str
    civil_date: date
    effective_date: date
    hour_branch: Optional[str]
    calendar_validation_status: str
    provenance: LayerProvenance
```

- [ ] **Step 4: Create exact CalendarContext fixture builder**

`tests/ziwei_phase2b_fixtures.py`:

```python
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from engine.calendar.models import (
    CalendarContext, CalendarInput, CalendarPolicies, LunarDate,
    LunarProviderMetadata, NormalizedTime, ProviderBundle,
    TimezoneProviderMetadata, ValidationCheck, ValidationMetadata,
)
from tests.ziwei_phase2a_fixtures import CHART, PROVENANCE, SYNTHETIC_STAR_RECORDS


def calendar_context(
    gregorian_date=date(2023, 7, 30),
    local_hour=1,
    local_minute=30,
    hour_branch="丑",
    lunar_year=2023,
    lunar_month=6,
    lunar_day=13,
    is_leap_month=False,
    calendar_status="validated",
    metaphysics_day_boundary_applied=False,
):
    zone = ZoneInfo("Asia/Taipei")
    local = datetime(
        gregorian_date.year, gregorian_date.month, gregorian_date.day,
        local_hour, local_minute, tzinfo=zone,
    )
    utc = local.astimezone(timezone.utc)
    offset = local.strftime("%z")
    offset = offset[:3] + ":" + offset[3:]
    return CalendarContext(
        "1.0",
        "1.0.0",
        CalendarInput(local.strftime("%Y-%m-%d %H:%M"), "Asia/Taipei"),
        NormalizedTime(local, utc, offset, gregorian_date, "Asia/Taipei", hour_branch),
        LunarDate(lunar_year, lunar_month, lunar_day, is_leap_month),
        ProviderBundle(
            LunarProviderMetadata("lunar-python", "1.4.8", "000c8a3"),
            TimezoneProviderMetadata("zoneinfo", "stdlib", "2026.3", "system"),
        ),
        ValidationMetadata(
            ValidationCheck(calendar_status, "calendar-test-v1"),
            ValidationCheck("validated", "timezone-test-v1"),
            calendar_status,
            "1900-2100",
            "test-boundary" if calendar_status == "boundary_conflict" else None,
            (),
        ),
        CalendarPolicies(
            "IANA timezone", "civil_midnight", "two_hour_branch",
            metaphysics_day_boundary_applied,
        ),
    )
```

- [ ] **Step 5: Run GREEN**

```bash
python -m unittest tests.test_ziwei_fine_cycle_stems.FineCycleModelTests -v
python -m unittest tests.test_ziwei_phase2a_models -v
```

Only after PASS emit `FINE_CYCLE_MODEL_INVARIANTS_PASS`.

- [ ] **Step 6: Commit**

```bash
git add engine/ziwei/errors.py engine/ziwei/models.py tests/ziwei_phase2b_fixtures.py tests/test_ziwei_fine_cycle_stems.py
git commit -m "feat: add Ziwei fine-cycle models and error contract"
```

---

### Task 3: Implement Fine-Cycle Profile and Monthly Stem Resolver

**Files:**
- Create: `engine/ziwei/fine_cycle_stems.py`
- Modify: `tests/test_ziwei_fine_cycle_stems.py`

**Interfaces:**

```python
FINE_CYCLE_PROFILE_ID = "ziwei-fine-cycle-lunar-late-zi-v1"
FINE_CYCLE_RULE_VERSION = "1.0-exp"
DAY_BOUNDARY_PROFILE = "late_zi_forward-v1"
get_fine_cycle_profile(profile_id=FINE_CYCLE_PROFILE_ID) -> FineCycleStemProfile
resolve_month_stem(context, profile_id=FINE_CYCLE_PROFILE_ID) -> ResolvedCycleStem
```

- [ ] **Step 1: Write RED monthly tests**

```python
from engine.ziwei.errors import ZiweiFineCycleError
from engine.ziwei.fine_cycle_stems import get_fine_cycle_profile, resolve_month_stem
from tests.ziwei_phase2b_fixtures import calendar_context


class FineCycleMonthTests(unittest.TestCase):
    def test_profile_is_explicit(self):
        profile = get_fine_cycle_profile()
        self.assertEqual(profile.profile_id, "ziwei-fine-cycle-lunar-late-zi-v1")
        self.assertEqual(profile.rule_version, "1.0-exp")
        self.assertEqual(profile.ziwei_day_boundary, "late_zi_forward-v1")

    def test_unknown_profile_has_no_fallback(self):
        with self.assertRaises(ZiweiFineCycleError) as cm:
            get_fine_cycle_profile("unknown")
        self.assertEqual(cm.exception.code, "invalid_fine_cycle_profile")

    def test_public_lunar_sixth_month_vector(self):
        result = resolve_month_stem(calendar_context(lunar_year=2023, lunar_month=6, lunar_day=13))
        self.assertEqual((result.heavenly_stem, result.earthly_branch), ("己", "未"))
        self.assertEqual(result.reference, "lunar:2023-06")

    def test_leap_day_15_and_16_split(self):
        before = resolve_month_stem(calendar_context(
            lunar_year=2023, lunar_month=2, lunar_day=15, is_leap_month=True,
        ))
        after = resolve_month_stem(calendar_context(
            lunar_year=2023, lunar_month=2, lunar_day=16, is_leap_month=True,
        ))
        self.assertEqual(before.reference, "lunar:2023-L02-A")
        self.assertEqual(after.reference, "lunar:2023-L02-B")
        self.assertEqual((before.heavenly_stem, before.earthly_branch), ("乙", "卯"))
        self.assertEqual((after.heavenly_stem, after.earthly_branch), ("丙", "辰"))

    def test_synthetic_leap_twelfth_second_half_uses_ordinal_13(self):
        result = resolve_month_stem(calendar_context(
            lunar_year=2023, lunar_month=12, lunar_day=16, is_leap_month=True,
        ))
        self.assertEqual(result.reference, "lunar:2023-L12-B")
        self.assertEqual((result.heavenly_stem, result.earthly_branch), ("丙", "寅"))

    def test_23xx_does_not_advance_month_stem(self):
        result = resolve_month_stem(calendar_context(
            local_hour=23, lunar_year=2023, lunar_month=6, lunar_day=30,
        ))
        self.assertEqual((result.heavenly_stem, result.earthly_branch), ("己", "未"))
```

- [ ] **Step 2: Verify RED**

```bash
python -m unittest tests.test_ziwei_fine_cycle_stems.FineCycleMonthTests -v
```

Expected: `engine.ziwei.fine_cycle_stems` is missing.

- [ ] **Step 3: Implement profile/context guard/month resolver**

```python
from __future__ import annotations

from datetime import timedelta

from engine.calendar.models import CalendarContext
from engine.calendar.sexagenary import five_mouse_hour, five_tiger_month, lunar_year_stem, sexagenary_day
from .errors import ZiweiFineCycleError
from .models import FineCycleStemProfile, LayerProvenance, ResolvedCycleStem

FINE_CYCLE_PROFILE_ID = "ziwei-fine-cycle-lunar-late-zi-v1"
FINE_CYCLE_RULE_VERSION = "1.0-exp"
DAY_BOUNDARY_PROFILE = "late_zi_forward-v1"
DEFAULT_FINE_CYCLE_PROFILE = FineCycleStemProfile(
    FINE_CYCLE_PROFILE_ID, FINE_CYCLE_RULE_VERSION, "lunar_month",
    "split_after_day_15", "lunar_year", DAY_BOUNDARY_PROFILE,
    "effective_ziwei_day_stem",
)


def get_fine_cycle_profile(profile_id=FINE_CYCLE_PROFILE_ID):
    if profile_id != FINE_CYCLE_PROFILE_ID:
        raise ZiweiFineCycleError(
            "invalid_fine_cycle_profile", "unknown Ziwei fine-cycle profile",
            {"profile_id": profile_id},
        )
    return DEFAULT_FINE_CYCLE_PROFILE


def _ensure_usable_context(context: CalendarContext) -> None:
    if context.validation.calendar_conversion.status == "boundary_conflict":
        raise ZiweiFineCycleError(
            "calendar_context_unusable", "calendar conversion is in boundary conflict",
            {"boundary_id": context.validation.boundary_id},
        )
    if context.policies.metaphysics_day_boundary_applied:
        raise ZiweiFineCycleError(
            "calendar_boundary_already_applied",
            "Ziwei day boundary must be applied exactly once by the fine-cycle profile",
        )


def _provenance(profile):
    return LayerProvenance(
        "project_derived", "Metaphysics Lab", None,
        profile.profile_id, profile.rule_version,
        "engine.ziwei.fine_cycle_stems",
    )


def resolve_month_stem(context, profile_id=FINE_CYCLE_PROFILE_ID):
    _ensure_usable_context(context)
    profile = get_fine_cycle_profile(profile_id)
    year, month, day = context.lunar.year, context.lunar.month, context.lunar.day
    leap = context.lunar.is_leap_month
    ordinal = month + (1 if leap and day >= 16 else 0)
    stem, branch = five_tiger_month(lunar_year_stem(year), ordinal)
    if not leap:
        reference = f"lunar:{year:04d}-{month:02d}"
    elif day <= 15:
        reference = f"lunar:{year:04d}-L{month:02d}-A"
    else:
        reference = f"lunar:{year:04d}-L{month:02d}-B"
    civil = context.normalized_time.gregorian_date
    return ResolvedCycleStem(
        "monthly", reference, stem, branch,
        profile.profile_id, profile.rule_version,
        civil, civil, None,
        context.validation.overall_status,
        _provenance(profile),
    )
```

- [ ] **Step 4: Run GREEN + existing month/calendar adapter regression**

```bash
python -m unittest tests.test_ziwei_fine_cycle_stems.FineCycleMonthTests -v
python -m unittest tests.test_project_ziwei_month tests.test_ziwei_calendar_adapter -v
```

After PASS emit:

```text
MONTH_STEM_INVARIANTS_PASS
LEAP_MONTH_BOUNDARY_PASS
```

- [ ] **Step 5: Commit**

```bash
git add engine/ziwei/fine_cycle_stems.py tests/test_ziwei_fine_cycle_stems.py
git commit -m "feat: resolve Ziwei monthly stems"
```

---

### Task 4: Implement Daily Stem Resolver and Late-Zi Boundary

**Files:**
- Modify: `engine/ziwei/fine_cycle_stems.py`
- Modify: `tests/test_ziwei_fine_cycle_stems.py`

**Interfaces:**

```python
resolve_day_stem(context, profile_id=FINE_CYCLE_PROFILE_ID) -> ResolvedCycleStem
```

- [ ] **Step 1: Write RED boundary tests**

```python
from datetime import date
from engine.ziwei.fine_cycle_stems import resolve_day_stem


class FineCycleDayTests(unittest.TestCase):
    def test_2259_uses_civil_date(self):
        result = resolve_day_stem(calendar_context(
            gregorian_date=date(1987, 12, 6), local_hour=22, local_minute=59,
        ))
        self.assertEqual(result.effective_date, date(1987, 12, 6))
        self.assertEqual((result.heavenly_stem, result.earthly_branch), ("己", "丑"))

    def test_2300_advances_one_day(self):
        result = resolve_day_stem(calendar_context(
            gregorian_date=date(1987, 12, 6), local_hour=23, local_minute=0,
        ))
        self.assertEqual(result.effective_date, date(1987, 12, 7))
        self.assertEqual((result.heavenly_stem, result.earthly_branch), ("庚", "寅"))
        self.assertEqual(result.reference, "ziwei-day:1987-12-07@late_zi_forward-v1")

    def test_0000_does_not_double_advance(self):
        result = resolve_day_stem(calendar_context(
            gregorian_date=date(1987, 12, 7), local_hour=0, local_minute=0,
        ))
        self.assertEqual(result.effective_date, date(1987, 12, 7))

    def test_preapplied_boundary_is_rejected(self):
        with self.assertRaises(ZiweiFineCycleError) as cm:
            resolve_day_stem(calendar_context(metaphysics_day_boundary_applied=True))
        self.assertEqual(cm.exception.code, "calendar_boundary_already_applied")

    def test_calendar_boundary_conflict_is_rejected(self):
        with self.assertRaises(ZiweiFineCycleError) as cm:
            resolve_day_stem(calendar_context(calendar_status="boundary_conflict"))
        self.assertEqual(cm.exception.code, "calendar_context_unusable")

    def test_boundary_caution_is_preserved(self):
        result = resolve_day_stem(calendar_context(calendar_status="boundary_caution"))
        self.assertEqual(result.calendar_validation_status, "boundary_caution")
```

- [ ] **Step 2: Verify RED**

```bash
python -m unittest tests.test_ziwei_fine_cycle_stems.FineCycleDayTests -v
```

Expected: `resolve_day_stem` missing.

- [ ] **Step 3: Implement effective-date helper and daily resolver**

```python
def _effective_ziwei_date(context, profile):
    if profile.ziwei_day_boundary != DAY_BOUNDARY_PROFILE:
        raise ZiweiFineCycleError(
            "invalid_fine_cycle_profile", "unsupported Ziwei day boundary profile",
            {"boundary": profile.ziwei_day_boundary},
        )
    civil = context.normalized_time.gregorian_date
    local = context.normalized_time.local_datetime
    return civil + timedelta(days=1) if local.hour >= 23 else civil


def resolve_day_stem(context, profile_id=FINE_CYCLE_PROFILE_ID):
    _ensure_usable_context(context)
    profile = get_fine_cycle_profile(profile_id)
    civil = context.normalized_time.gregorian_date
    effective = _effective_ziwei_date(context, profile)
    stem, branch = sexagenary_day(effective)
    reference = "ziwei-day:%s@%s" % (
        effective.isoformat(), profile.ziwei_day_boundary,
    )
    return ResolvedCycleStem(
        "daily", reference, stem, branch,
        profile.profile_id, profile.rule_version,
        civil, effective, None,
        context.validation.overall_status,
        _provenance(profile),
    )
```

- [ ] **Step 4: Run GREEN + Calendar/Bazi boundary regression**

```bash
python -m unittest tests.test_ziwei_fine_cycle_stems.FineCycleDayTests -v
python -m unittest tests.test_calendar_resolver tests.test_calendar_timezone tests.test_project_bazi_calendar -v
```

After PASS emit:

```text
DAY_STEM_BOUNDARY_PASS
CALENDAR_BOUNDARY_DOUBLE_APPLY_REJECTED
```

- [ ] **Step 5: Commit**

```bash
git add engine/ziwei/fine_cycle_stems.py tests/test_ziwei_fine_cycle_stems.py
git commit -m "feat: resolve Ziwei daily stems with late-Zi boundary"
```

---

### Task 5: Implement Hourly Stem Resolver and Late-Zi Coherence

**Files:**
- Modify: `engine/ziwei/fine_cycle_stems.py`
- Modify: `tests/test_ziwei_fine_cycle_stems.py`

**Interfaces:**

```python
resolve_hour_stem(context, profile_id=FINE_CYCLE_PROFILE_ID) -> ResolvedCycleStem
```

- [ ] **Step 1: Write RED hour/coherence tests**

```python
from engine.calendar.sexagenary import GAN, ZHI, five_mouse_hour
from engine.ziwei.fine_cycle_stems import resolve_hour_stem


class FineCycleHourTests(unittest.TestCase):
    def test_public_regular_hour_vector(self):
        result = resolve_hour_stem(calendar_context(
            gregorian_date=date(1987, 12, 6), local_hour=21, local_minute=30, hour_branch="亥",
        ))
        self.assertEqual((result.heavenly_stem, result.earthly_branch), ("乙", "亥"))

    def test_late_zi_uses_next_day_stem_for_hour(self):
        context = calendar_context(
            gregorian_date=date(1987, 12, 6), local_hour=23, local_minute=30, hour_branch="子",
        )
        day = resolve_day_stem(context)
        hour = resolve_hour_stem(context)
        self.assertEqual(day.heavenly_stem, "庚")
        self.assertEqual((hour.heavenly_stem, hour.earthly_branch), ("丙", "子"))
        self.assertEqual(hour.effective_date, day.effective_date)
        self.assertEqual(hour.reference, "ziwei-hour:1987-12-07:子@late_zi_forward-v1")

    def test_all_day_stem_hour_branch_pairs_are_defined(self):
        for day_stem in GAN:
            for branch in ZHI:
                hour_stem, returned_branch = five_mouse_hour(day_stem, branch)
                self.assertIn(hour_stem, GAN)
                self.assertEqual(returned_branch, branch)
```

- [ ] **Step 2: Verify RED**

```bash
python -m unittest tests.test_ziwei_fine_cycle_stems.FineCycleHourTests -v
```

Expected: `resolve_hour_stem` missing.

- [ ] **Step 3: Implement hourly resolver using the same effective date**

```python
def resolve_hour_stem(context, profile_id=FINE_CYCLE_PROFILE_ID):
    _ensure_usable_context(context)
    profile = get_fine_cycle_profile(profile_id)
    civil = context.normalized_time.gregorian_date
    effective = _effective_ziwei_date(context, profile)
    day_stem, _ = sexagenary_day(effective)
    stem, branch = five_mouse_hour(day_stem, context.normalized_time.hour_branch)
    reference = "ziwei-hour:%s:%s@%s" % (
        effective.isoformat(), branch, profile.ziwei_day_boundary,
    )
    return ResolvedCycleStem(
        "hourly", reference, stem, branch,
        profile.profile_id, profile.rule_version,
        civil, effective, branch,
        context.validation.overall_status,
        _provenance(profile),
    )
```

Do not call `engine.bazi.calendar.time_pillar()` and do not derive branch from `local_datetime.hour`.

- [ ] **Step 4: Run GREEN + existing flow-hour regression**

```bash
python -m unittest tests.test_ziwei_fine_cycle_stems.FineCycleHourTests -v
python -m unittest tests.test_project_ziwei_hour tests.test_ziwei_calendar_adapter -v
```

After PASS emit:

```text
HOUR_STEM_INVARIANTS_PASS
LATE_ZI_COHERENCE_PASS
```

- [ ] **Step 5: Commit**

```bash
git add engine/ziwei/fine_cycle_stems.py tests/test_ziwei_fine_cycle_stems.py
git commit -m "feat: resolve Ziwei hourly stems coherently"
```

---

### Task 6: Integrate Fine-Cycle Resolutions into Transformation/Flying/Composition

**Files:**
- Create: `engine/ziwei/fine_cycle.py`
- Create: `tests/test_ziwei_fine_cycle_integration.py`
- Modify: `engine/ziwei/composition.py`
- Modify: `tests/test_ziwei_composition.py`

**Interfaces:**

```python
build_fine_cycle_layer(
    resolution: ResolvedCycleStem,
    chart_identity: ChartIdentity,
    star_locations: StarLocationIndex,
    transformation_profile_id: str = PROFILE_ID,
) -> CycleTransformationLayer
```

The implementation must use existing `get_transformation_set`, `fly_transformations`, and `build_cycle_layer`.

- [ ] **Step 1: Write RED integration/composition tests**

`tests/test_ziwei_fine_cycle_integration.py`:

```python
import unittest
from unittest.mock import patch

from engine.ziwei.basis import build_star_location_index
from engine.ziwei.errors import ZiweiFineCycleError, ZiweiPhase2AError
from engine.ziwei.fine_cycle import build_fine_cycle_layer
from engine.ziwei.fine_cycle_stems import resolve_day_stem, resolve_hour_stem, resolve_month_stem
from engine.ziwei.models import ChartIdentity
from engine.ziwei.transformations import get_transformation_set
from tests.ziwei_phase2b_fixtures import CHART, PROVENANCE, SYNTHETIC_STAR_RECORDS, calendar_context


class FineCycleIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.stars = build_star_location_index(SYNTHETIC_STAR_RECORDS, CHART, PROVENANCE)

    def test_each_scope_builds_four_transformations_and_four_edges(self):
        resolutions = (
            resolve_month_stem(calendar_context()),
            resolve_day_stem(calendar_context()),
            resolve_hour_stem(calendar_context()),
        )
        for resolution in resolutions:
            layer = build_fine_cycle_layer(resolution, CHART, self.stars)
            self.assertEqual(layer.identity.scope, resolution.scope)
            self.assertEqual(layer.identity.reference, resolution.reference)
            self.assertEqual(layer.heavenly_stem, resolution.heavenly_stem)
            self.assertEqual(len(layer.transformations.transformations), 4)
            self.assertEqual(len(layer.flying_edges), 4)

    def test_chart_mismatch_fails_closed(self):
        other = ChartIdentity("other", "natal", "synthetic-v1")
        resolution = resolve_month_stem(calendar_context())
        with self.assertRaises(ZiweiPhase2AError) as cm:
            build_fine_cycle_layer(resolution, other, self.stars)
        self.assertEqual(cm.exception.code, "chart_basis_mismatch")

    def test_internal_transformation_stem_mismatch_fails_closed(self):
        resolution = resolve_month_stem(calendar_context())
        wrong = get_transformation_set("丁" if resolution.heavenly_stem != "丁" else "丙")
        with patch("engine.ziwei.fine_cycle.get_transformation_set", return_value=wrong):
            with self.assertRaises(ZiweiFineCycleError) as cm:
                build_fine_cycle_layer(resolution, CHART, self.stars)
        self.assertEqual(cm.exception.code, "fine_cycle_stem_mismatch")
```

Update `tests/test_ziwei_composition.py`:

```python
def test_fine_cycle_scopes_are_supported(self):
    natal = _base_natal()
    for scope, reference in (
        ("monthly", "lunar:2026-07"),
        ("daily", "ziwei-day:2026-08-21@late_zi_forward-v1"),
        ("hourly", "ziwei-hour:2026-08-21:申@late_zi_forward-v1"),
    ):
        source, trans, edges, identity = _components(scope, reference, "丙", natal)
        layer = build_cycle_layer(identity, source, trans, edges, PROVENANCE)
        self.assertEqual(layer.identity.scope, scope)


def test_unknown_cycle_scope_is_still_rejected(self):
    natal = _base_natal()
    source, trans, edges, identity = _components("weekly", "week:1", "丙", natal)
    with self.assertRaises(ZiweiPhase2AError) as cm:
        build_cycle_layer(identity, source, trans, edges, PROVENANCE)
    self.assertEqual(cm.exception.code, "unsupported_scope")
```

Add a coexistence test that creates one yearly, one monthly, one daily and one hourly layer, calls `build_layer_stack`, and asserts the four identities remain distinct. Add duplicate fine-cycle identity tests by reusing the same built monthly layer twice and expecting `duplicate_layer_identity`; create a second monthly layer with same `LayerIdentity` but altered `earthly_branch` using `dataclasses.replace()` and expect `layer_conflict`.

- [ ] **Step 2: Verify RED**

```bash
python -m unittest tests.test_ziwei_fine_cycle_integration tests.test_ziwei_composition -v
```

Expected: fine scope rejected by current `SUPPORTED_SCOPES` and/or missing `fine_cycle.py`.

- [ ] **Step 3: Expand Composition without weakening Phase 2A invariants**

```python
SUPPORTED_SCOPES = {
    "birth_year", "decadal", "yearly", "monthly", "daily", "hourly",
}
```

Keep all current identity/source/profile/stem/edge coherence checks. Replace hard fine-cycle unavailability with:

```python
"monthly_transformations": AvailabilityRecord("conditional", "matching_resolved_stem_required"),
"daily_transformations": AvailabilityRecord("conditional", "matching_resolved_stem_required"),
"hourly_transformations": AvailabilityRecord("conditional", "matching_resolved_stem_required"),
```

- [ ] **Step 4: Implement thin fine-cycle orchestration**

```python
from .composition import build_cycle_layer
from .errors import ZiweiFineCycleError, ZiweiPhase2AError
from .flying import fly_transformations
from .models import CycleStemSource, LayerIdentity
from .transformation_profiles import PROFILE_ID
from .transformations import get_transformation_set

FINE_SCOPES = {"monthly", "daily", "hourly"}


def build_fine_cycle_layer(
    resolution,
    chart_identity,
    star_locations,
    transformation_profile_id=PROFILE_ID,
):
    if resolution.scope not in FINE_SCOPES:
        raise ZiweiFineCycleError(
            "invalid_fine_cycle_scope", "unsupported fine-cycle scope",
            {"scope": resolution.scope},
        )
    if star_locations.chart_identity != chart_identity:
        raise ZiweiPhase2AError(
            "chart_basis_mismatch", "fine-cycle chart and star index mismatch",
        )
    source = CycleStemSource(
        "cycle_stem", chart_identity, resolution.scope,
        resolution.reference, resolution.heavenly_stem,
    )
    transformations = get_transformation_set(
        resolution.heavenly_stem, transformation_profile_id,
    )
    if transformations.heavenly_stem != resolution.heavenly_stem:
        raise ZiweiFineCycleError(
            "fine_cycle_stem_mismatch",
            "resolved stem and transformation stem differ",
            {
                "resolved_stem": resolution.heavenly_stem,
                "transformation_stem": transformations.heavenly_stem,
            },
        )
    edges = fly_transformations(transformations, star_locations, source)
    identity = LayerIdentity(
        chart_identity.chart_id, resolution.scope,
        resolution.reference, transformations.profile_id,
    )
    layer = build_cycle_layer(
        identity, source, transformations, edges,
        resolution.provenance, earthly_branch=resolution.earthly_branch,
    )
    if (
        layer.identity.scope != resolution.scope
        or layer.identity.reference != resolution.reference
        or layer.heavenly_stem != resolution.heavenly_stem
    ):
        raise ZiweiFineCycleError(
            "fine_cycle_reference_conflict",
            "built layer does not preserve resolved fine-cycle identity",
        )
    return layer
```

- [ ] **Step 5: Run GREEN + Phase2A flying/composition regression**

```bash
python -m unittest tests.test_ziwei_fine_cycle_integration tests.test_ziwei_composition tests.test_ziwei_flying -v
```

After PASS emit:

```text
FINE_CYCLE_TRANSFORMATIONS_PASS
FINE_CYCLE_FLYING_PASS
FINE_CYCLE_COMPOSITION_PASS
FINE_CYCLE_NEGATIVE_CASES_PASS
```

- [ ] **Step 6: Commit**

```bash
git add engine/ziwei/fine_cycle.py engine/ziwei/composition.py tests/test_ziwei_fine_cycle_integration.py tests/test_ziwei_composition.py
git commit -m "feat: integrate Ziwei fine-cycle transformation layers"
```

---

### Task 7: Promote Capability Lifecycle to Implemented / Experimental / On-Demand

**Files:**
- Modify: `engine/ziwei/capabilities.py`
- Create: `tests/test_ziwei_phase2b_capabilities.py`
- Modify: `tests/test_ziwei_phase2a_capabilities.py`

**Interfaces:**

New IDs:

```text
ziwei.flow_month_stem
ziwei.flow_day_stem
ziwei.flow_hour_stem
```

Existing fine-cycle transformation/flying IDs move from planned to implemented/experimental/on_demand. `ziwei.flowing_stars` stays planned.

- [ ] **Step 1: Write RED capability tests**

```python
import unittest
from engine.ziwei.capabilities import can_execute, get_capability, should_run_by_default


class ZiweiPhase2BCapabilityTests(unittest.TestCase):
    def test_stem_capabilities_are_experimental_on_demand(self):
        for capability_id in (
            "ziwei.flow_month_stem", "ziwei.flow_day_stem", "ziwei.flow_hour_stem",
        ):
            cap = get_capability(capability_id)
            self.assertEqual(cap["implementation"], "implemented")
            self.assertEqual(cap["maturity"], "experimental")
            self.assertEqual(cap["routing"], "on_demand")
            self.assertEqual(cap["rule_version"], "1.0-exp")
            self.assertTrue(can_execute(capability_id))
            self.assertFalse(should_run_by_default(capability_id))

    def test_fine_cycle_transformations_and_flying_are_experimental_on_demand(self):
        ids = (
            "ziwei.flow_month_transformations", "ziwei.flow_day_transformations", "ziwei.flow_hour_transformations",
            "ziwei.flow_month_flying", "ziwei.flow_day_flying", "ziwei.flow_hour_flying",
        )
        for capability_id in ids:
            cap = get_capability(capability_id)
            self.assertEqual(
                (cap["implementation"], cap["maturity"], cap["routing"], cap["rule_version"]),
                ("implemented", "experimental", "on_demand", "1.0-exp"),
            )
            self.assertTrue(can_execute(capability_id))
            self.assertFalse(should_run_by_default(capability_id))

    def test_flowing_stars_remain_planned(self):
        self.assertEqual(get_capability("ziwei.flowing_stars")["implementation"], "planned")
        self.assertFalse(can_execute("ziwei.flowing_stars"))
```

Replace the stale Phase2A test that requires all fine-cycle IDs to be planned; keep Phase2A assertions that `ziwei.transformations` and `ziwei.flying` remain stable/on_demand.

- [ ] **Step 2: Verify RED**

```bash
python -m unittest tests.test_ziwei_phase2b_capabilities -v
```

Expected: new IDs missing and existing fine-cycle IDs still planned.

- [ ] **Step 3: Update registry with exact dependency graph**

```text
ziwei.flow_month_stem -> engine.ziwei.fine_cycle_stems -> ()
ziwei.flow_day_stem   -> engine.ziwei.fine_cycle_stems -> ()
ziwei.flow_hour_stem  -> engine.ziwei.fine_cycle_stems -> ()

ziwei.flow_month_transformations -> flow_month_stem + ziwei.transformations
ziwei.flow_day_transformations   -> flow_day_stem + ziwei.transformations
ziwei.flow_hour_transformations  -> flow_hour_stem + ziwei.transformations

ziwei.flow_month_flying -> flow_month_transformations + ziwei.flying
ziwei.flow_day_flying   -> flow_day_transformations + ziwei.flying
ziwei.flow_hour_flying  -> flow_hour_transformations + ziwei.flying
```

All nine Phase2B IDs use:

```text
implementation = implemented
maturity = experimental
routing = on_demand
rule_version = 1.0-exp
```

- [ ] **Step 4: Run GREEN**

```bash
python -m unittest tests.test_ziwei_phase2b_capabilities tests.test_ziwei_phase2a_capabilities tests.test_ziwei_capabilities -v
```

After PASS emit `CAPABILITY_EXPERIMENTAL_ON_DEMAND_PASS`.

- [ ] **Step 5: Commit**

```bash
git add engine/ziwei/capabilities.py tests/test_ziwei_phase2b_capabilities.py tests/test_ziwei_phase2a_capabilities.py
git commit -m "feat: enable experimental Ziwei fine-cycle capabilities"
```

---

### Task 8: Build Reproducible Public Qualification for lunar-lite and iztro

**Files:**
- Create: `tools/qualify_ziwei_phase2b_public.py`
- Create: `tests/test_ziwei_phase2b_qualification.py`
- Create: `qualification/ziwei/phase2b/public-lunar-lite-1d104fff.json`
- Create: `qualification/ziwei/phase2b/public-iztro-814b77e6.json`

**Interfaces:**

```python
normalize_ts(source_text: str) -> str
qualify_lunar_lite_source(ganzhi_source: str, tests_source: str, source_revision: str, run_timestamp: str) -> dict
qualify_iztro_source(functional_source: str, source_revision: str, run_timestamp: str) -> dict
```

Production runtime never imports this tool.

- [ ] **Step 1: Write RED qualification contract tests**

```python
import unittest
from tools.qualify_ziwei_phase2b_public import qualify_iztro_source, qualify_lunar_lite_source


class Phase2BPublicQualificationTests(unittest.TestCase):
    def test_lunar_lite_requires_pinned_public_vectors(self):
        with self.assertRaises(Exception):
            qualify_lunar_lite_source("", "", "1d104fff", "2026-08-21T00:00:00Z")

    def test_iztro_requires_each_fine_scope_mutagen_link(self):
        bad = "monthly: { mutagen: getMutagensByHeavenlyStem(monthly[0]) }"
        with self.assertRaises(Exception):
            qualify_iztro_source(bad, "814b77e6", "2026-08-21T00:00:00Z")
```

In the committed test, assert `ZiweiFineCycleError.code == "qualification_mismatch"` for both cases, not a generic exception.

- [ ] **Step 2: Verify RED**

```bash
python -m unittest tests.test_ziwei_phase2b_qualification -v
```

Expected: tool module missing.

- [ ] **Step 3: Implement deterministic source normalization and lunar-lite evidence**

Use whitespace-normalized source rather than a fragile TypeScript AST dependency:

```python
import re

LUNAR_LITE_REQUIRED_VECTORS = (
    ("lunar-2023-06-13-chou", 'date: "2023-6-13", timeIndex: 1, isLeap: false, result: "癸卯 己未 己丑 乙丑"),
    ("lunar-2023-06-13-late-zi", 'date: "2023-6-13", timeIndex: 12, isLeap: false, result: "癸卯 己未 庚寅 丙子"),
    ("lunar-2023-leap-02-11", 'date: "2023-2-11", timeIndex: 1, isLeap: true, result: "癸卯 乙卯 己丑 乙丑"),
    ("solar-1987-12-06-hai", 'date: "1987-12-6", timeIndex: 11, result: "丁卯 辛亥 己丑 乙亥"),
    ("solar-1987-12-06-late-zi", 'date: "1987-12-6", timeIndex: 12, result: "丁卯 辛亥 庚寅 丙子"),
)


def normalize_ts(source_text):
    return re.sub(r"\s+", " ", source_text).strip()


def _require_fragment(text, fragment, vector_id):
    if fragment not in text:
        raise ZiweiFineCycleError(
            "qualification_mismatch", "pinned upstream vector is missing or changed",
            {"vector_id": vector_id},
        )
```

`qualify_lunar_lite_source()` must first assert the pinned `ganzhi.ts` contains the five-tiger `FIVE_TIGER` usage, `getDayGanExact`, `getDayZhiExact`, `getTimeGan`, and `getTimeZhi`. It then requires all five normalized test-vector fragments above and compares Project math:

```text
2023 lunar month 6 -> 己未
2023 leap lunar month 2 day 11 -> 乙卯
1987-12-06 day -> 己丑
1987-12-07 day -> 庚寅
己 day / 亥 hour -> 乙亥
庚 day / 子 hour -> 丙子
```

Report fields:

```json
{
  "source_name": "SylarLong/lunar-lite",
  "source_revision": "1d104fffa31609e9f112898cc57545827e8d57ae",
  "package_version": "0.2.8",
  "cases_checked": 6,
  "cases_matched": 6,
  "not_externally_covered": ["leap_twelfth_second_half"],
  "mismatches": [],
  "status": "PASS"
}
```

- [ ] **Step 4: Implement iztro integration evidence**

Normalize `FunctionalAstrolabe.ts` and require all three fragments:

```python
IZTRO_REQUIRED = {
    "monthly": "mutagen: getMutagensByHeavenlyStem(monthly[0])",
    "daily": "mutagen: getMutagensByHeavenlyStem(daily[0])",
    "hourly": "mutagen: getMutagensByHeavenlyStem(hourly[0])",
}
```

`qualify_iztro_source()` returns:

```json
{
  "source_name": "SylarLong/iztro",
  "source_revision": "814b77e6371e1050cac31bbf674db3c3138fcfde",
  "package_version": "2.6.0",
  "monthly_mutagen_uses_monthly_stem": true,
  "daily_mutagen_uses_daily_stem": true,
  "hourly_mutagen_uses_hourly_stem": true,
  "project_sample_transformations_each": 4,
  "status": "PASS"
}
```

Project sample transformation count must be obtained by calling `get_transformation_set()` for one resolved stem from each scope, not hard-coded into the assertion path.

- [ ] **Step 5: Add CLI and run against exact pinned snapshots**

CLI arguments:

```text
--lunar-lite-ganzhi-ts
--lunar-lite-tests-ts
--iztro-functional-ts
--lunar-lite-revision
--iztro-revision
--output-dir
--run-timestamp
```

Validation command:

```bash
python tools/qualify_ziwei_phase2b_public.py \
  --lunar-lite-ganzhi-ts /tmp/lunar-lite-ganzhi.ts \
  --lunar-lite-tests-ts /tmp/lunar-lite-ganzhi.test.ts \
  --iztro-functional-ts /tmp/FunctionalAstrolabe.ts \
  --lunar-lite-revision 1d104fffa31609e9f112898cc57545827e8d57ae \
  --iztro-revision 814b77e6371e1050cac31bbf674db3c3138fcfde \
  --output-dir qualification/ziwei/phase2b \
  --run-timestamp 2026-08-21T00:00:00Z
```

Downloaded source snapshots remain temporary and are never committed.

- [ ] **Step 6: Run GREEN**

```bash
python -m unittest tests.test_ziwei_phase2b_qualification tests.test_ziwei_transformations -v
```

Only after both JSON reports are PASS emit:

```text
PUBLIC_LUNAR_LITE_QUALIFICATION_PASS
PUBLIC_IZTRO_INTEGRATION_PASS
```

- [ ] **Step 7: Commit tool/tests/public evidence**

```bash
git add tools/qualify_ziwei_phase2b_public.py tests/test_ziwei_phase2b_qualification.py qualification/ziwei/phase2b/public-*.json
git commit -m "test: qualify Ziwei fine-cycle public evidence"
```

---

### Task 9: Record Astralium Pending State and Enforce Privacy

**Files:**
- Create: `qualification/ziwei/phase2b/private-astralium-summary.json`
- Modify: `tests/test_ziwei_phase2b_qualification.py`

**Interfaces:** repo stores only aggregate pending evidence.

- [ ] **Step 1: Write RED privacy test**

```python
class Phase2BPrivateQualificationTests(unittest.TestCase):
    def test_private_summary_is_pending_without_raw_chart(self):
        path = Path("qualification/ziwei/phase2b/private-astralium-summary.json")
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "PENDING")
        self.assertEqual(payload["reason_code"], "fine_cycle_source_not_available")
        raw = path.read_text(encoding="utf-8")
        for forbidden in (
            "star_locations", "palace_stems", "expected_edges",
            "birth_datetime", "出生年月", "姓名",
        ):
            self.assertNotIn(forbidden, raw)
```

- [ ] **Step 2: Verify RED**

```bash
python -m unittest tests.test_ziwei_phase2b_qualification.Phase2BPrivateQualificationTests -v
```

Expected: file missing.

- [ ] **Step 3: Create exact aggregate summary**

```json
{
  "source_name": "Astralium",
  "phase": "2B",
  "scope": "fine_cycle_stems_transformations_flying",
  "status": "PENDING",
  "reason_code": "fine_cycle_source_not_available",
  "reason": "Current private Astralium source package does not provide a complete fine-cycle stem/transformation/flying payload for qualification.",
  "raw_private_payload_committed": false
}
```

- [ ] **Step 4: Run GREEN and commit**

```bash
python -m unittest tests.test_ziwei_phase2b_qualification -v
git add qualification/ziwei/phase2b/private-astralium-summary.json tests/test_ziwei_phase2b_qualification.py
git commit -m "test: record pending Astralium fine-cycle qualification"
```

Only after PASS emit:

```text
ASTRALIUM_FINE_CYCLE_PENDING
PRIVACY_PASS
```

---

### Task 10: Promote Formal Rules and User-Facing Docs After Code Gates Are Green

**Files:**
- Modify: six core rule docs
- Modify: `README.md`, `CHANGELOG.md`, `docs/架構說明.md`, `docs/快速開始.md`, `docs/安裝到ChatGPT-Project.md`, `docs/更新與版本同步.md`
- Modify: `tests/test_rule_source_reconciliation.py`

**Interfaces:** documents only capabilities that have passed Tasks 1–9.

- [ ] **Step 1: Convert reconciliation test to post-Phase2B RED**

Add exact positive strings:

```python
def test_phase2b_documented_state_matches_runtime(self):
    combined = self._combined() + "\n" + (ROOT / "README.md").read_text(encoding="utf-8")
    for required in (
        "ziwei-fine-cycle-lunar-late-zi-v1",
        "late_zi_forward-v1",
        "implemented / experimental / on_demand",
        "Astralium fine-cycle qualification = pending",
    ):
        self.assertIn(required, combined)
    self.assertIn("流曜", combined)
    self.assertIn("planned", combined.lower())
```

Add negative assertions that no doc says fine-cycle stem/transformation/flying is Stable or Default, and no doc says Calendar Resolver itself performs the Ziwei 23:00 rollover.

- [ ] **Step 2: Verify RED**

```bash
python -m unittest tests.test_rule_source_reconciliation -v
```

Expected: missing Phase2B promoted wording.

- [ ] **Step 3: Update formal docs with exact state**

Every capability table/section must converge on:

```text
Ziwei Fine Cycle Stem Resolver v1
profile = ziwei-fine-cycle-lunar-late-zi-v1
day boundary = late_zi_forward-v1
flow_month/day/hour_stem = implemented / experimental / on_demand / 1.0-exp
flow_month/day/hour_transformations = implemented / experimental / on_demand / 1.0-exp
flow_month/day/hour_flying = implemented / experimental / on_demand / 1.0-exp
flowing_stars = planned / on_demand
public qualification = lunar-lite PASS + iztro integration PASS
Astralium fine-cycle qualification = pending
```

Also state:

```text
Calendar Resolver = neutral civil/calendar infrastructure
23:00 policy = Ziwei fine-cycle profile responsibility
monthly stem boundary = lunar month; late-Zi does not pre-switch month
Project 推導盤面 = data classification, not capability prefix
```

`CHANGELOG.md` gets `## Unreleased｜Phase 2B` because no new formal release tag exists yet. Do not change or move `v1.2.0`; `VERSION.md` remains the current formal release record until a later release-maintenance decision.

- [ ] **Step 4: Run docs/local-links GREEN**

```bash
python -m unittest tests.test_rule_source_reconciliation -v
python - <<'PY'
import re
from pathlib import Path
for path in [Path('README.md'), *Path('docs').glob('*.md')]:
    text = path.read_text(encoding='utf-8')
    for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)', text):
        if target.startswith(('http://', 'https://', '#', 'mailto:')):
            continue
        target = target.split('#', 1)[0]
        if target:
            assert (path.parent / target).resolve().exists(), f'broken local link: {path} -> {target}'
print('LOCAL_LINKS_PASS')
PY
```

- [ ] **Step 5: Commit**

```bash
git add core README.md CHANGELOG.md docs tests/test_rule_source_reconciliation.py
git commit -m "docs: document experimental Ziwei fine-cycle capabilities"
```

---

### Task 11: Exact-Head Final Validation, Review, and Merge Gates

**Files:** no formal production changes unless a defect is found; any defect starts a new RED/GREEN loop before this Task restarts.

**Interfaces:** consumes exact feature head and produces reproducible acceptance evidence.

- [ ] **Step 1: Freeze exact feature SHA and formal diff**

```bash
FEATURE_SHA=$(git rev-parse HEAD)
echo "FEATURE_SHA=$FEATURE_SHA"
git -c core.quotePath=false diff --name-only design/ziwei-fine-cycle-stem-resolver...HEAD
```

Formal diff must be restricted to the files listed by this plan plus spec/plan. Reject Qimen changes, unrelated Bazi production changes, raw private data, or permanent validation workflow changes.

- [ ] **Step 2: Python 3.9 syntax gate**

```bash
python - <<'PY'
import ast, subprocess
files = subprocess.check_output(
    ['git', '-c', 'core.quotePath=false', 'diff', '--name-only',
     'design/ziwei-fine-cycle-stem-resolver...HEAD'], text=True,
).splitlines()
for path in files:
    if path.endswith('.py') and (path.startswith('engine/') or path.startswith('tools/')):
        ast.parse(open(path, encoding='utf-8').read(), filename=path, feature_version=(3, 9))
print('PYTHON39_SYNTAX_PASS')
PY
```

- [ ] **Step 3: Run Phase 2B targeted suite**

```bash
python -m unittest \
  tests.test_rule_source_reconciliation \
  tests.test_calendar_sexagenary \
  tests.test_ziwei_fine_cycle_stems \
  tests.test_ziwei_fine_cycle_integration \
  tests.test_ziwei_phase2b_capabilities \
  tests.test_ziwei_phase2b_qualification -v
```

- [ ] **Step 4: Run complete regressions and record actual counts**

```bash
python -m unittest discover -v -s tests -p 'test_ziwei*.py'
python -m unittest discover -v -s tests -p 'test_calendar*.py'
python -m unittest tests.test_project_bazi_calendar -v
python -m unittest discover -v
```

Counts are read from actual output, not predicted. Lower bounds from v1.2.0:

```text
Ziwei >= 83
Calendar >= 35
Bazi >= 10
Full repo >= 132
```

Any lower count or failure stops the gate.

- [ ] **Step 5: Re-run public qualification on exact pinned sources**

Regenerate both public JSONs using Task 8 CLI. Compare regenerated JSON to committed evidence after removing only `run_timestamp`. `status`, source revision, package version, expected vectors, coverage and mismatch lists must match exactly.

- [ ] **Step 6: Assert privacy and capability boundaries**

Programmatic assertions must verify:

```text
flow_month/day/hour_stem = implemented / experimental / on_demand / 1.0-exp
flow_month/day/hour_transformations = implemented / experimental / on_demand / 1.0-exp
flow_month/day/hour_flying = implemented / experimental / on_demand / 1.0-exp
ziwei.transformations / ziwei.flying = still stable / on_demand / 1.0
flow_day_palaces / flow_hour_palaces = still experimental / on_demand
ziwei.flowing_stars = planned and not executable
private Astralium summary = PENDING and contains no forbidden raw fields
```

- [ ] **Step 7: Emit markers only from passed assertions**

Final evidence must contain:

```text
RULE_SOURCE_RECONCILIATION_PASS
FINE_CYCLE_MODEL_INVARIANTS_PASS
MONTH_STEM_INVARIANTS_PASS
LEAP_MONTH_BOUNDARY_PASS
DAY_STEM_BOUNDARY_PASS
HOUR_STEM_INVARIANTS_PASS
LATE_ZI_COHERENCE_PASS
CALENDAR_BOUNDARY_DOUBLE_APPLY_REJECTED
FINE_CYCLE_TRANSFORMATIONS_PASS
FINE_CYCLE_FLYING_PASS
FINE_CYCLE_COMPOSITION_PASS
FINE_CYCLE_NEGATIVE_CASES_PASS
PUBLIC_LUNAR_LITE_QUALIFICATION_PASS
PUBLIC_IZTRO_INTEGRATION_PASS
ASTRALIUM_FINE_CYCLE_PENDING
CAPABILITY_EXPERIMENTAL_ON_DEMAND_PASS
ZIWEI_REGRESSION_PASS
CALENDAR_REGRESSION_PASS
BAZI_REGRESSION_PASS
FULL_REPO_PASS
SCOPE_PASS
PRIVACY_PASS
LOCAL_LINKS_PASS
PYTHON39_SYNTAX_PASS
```

- [ ] **Step 8: Review exact feature head**

Reviewer must explicitly inspect:

```text
no hidden import/reuse of Bazi policy
no month/day boundary cross-contamination
no 23:00 double rollover
ResolvedCycleStem/source/layer identity coherence
fine-cycle duplicate/conflict semantics
no accidental Stable/Default promotion
no private Astralium leakage
no synthetic case labeled external qualification
```

Each Important/Critical finding requires a new failing test, minimal fix, targeted GREEN, then a complete Task 11 rerun.

- [ ] **Step 9: Stop at feature→design approval gate**

Open formal PR:

```text
feature/ziwei-fine-cycle-stem-resolver-v1
→ design/ziwei-fine-cycle-stem-resolver
```

Report exact feature SHA, formal file list, actual test counts, public qualification results, private pending state, scope/privacy status. Do not merge until user explicitly approves that PR.

---

## Post-Feature Integration Procedure

After explicit feature→design approval:

1. Re-read PR state, base, head SHA and mergeability; reject head drift.
2. Squash merge feature→design.
3. Re-run all Task 11 gates against the actual design merge commit.
4. Any failure stops; do not create design→main PR.
5. If GREEN, create formal design→main PR.
6. Obtain a second explicit user merge approval.
7. Squash merge design→main only after approval.
8. Re-run Task 11 equivalent gates against the actual `main` merge commit.
9. Only post-main GREEN closes Phase 2B.
10. Formal release version/tag remains a separate release-maintenance decision; never move/reuse `v1.2.0`.

---

## Plan Self-Review Result

- Spec coverage: Tasks 0–11 cover rule-source reconciliation, neutral sexagenary math, models/errors, month/day/hour stems, late-Zi, Calendar protection, stable references, Transformation/Flying integration, Composition, capability lifecycle, public qualification, Astralium pending/privacy, docs, regression, review and merge gates.
- Placeholder scan: no `TBD`, `TODO`, ellipsis placeholder, generic "add tests" step, or unspecified error-handling step remains.
- Type consistency: plan uses only `sexagenary_day`, `lunar_year_stem`, `five_tiger_month`, `five_mouse_hour`, `resolve_month_stem`, `resolve_day_stem`, `resolve_hour_stem`, `build_fine_cycle_layer`, `ZiweiFineCycleError`, and the existing Phase 2A APIs with consistent signatures.
- Scope: flowing stars, Qimen, AI interpretation, scoring, Bazi policy changes and private Astralium reverse inference remain out of scope.
- Implementation gate: no production code may be written until the user explicitly approves this plan.
