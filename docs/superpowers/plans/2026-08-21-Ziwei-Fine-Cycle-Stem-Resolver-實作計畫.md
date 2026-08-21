# Ziwei Fine Cycle Stem Resolver v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立紫微流月／流日／流時天干 resolver，將合法解析出的細運干支接入既有 Transformation/Flying/Composition Core，並以公開 qualification 與 fail-closed gate 驗證後，第一版以 `experimental / on_demand` 啟用。

**Architecture:** `CalendarContext` 保持 neutral civil/calendar fact source；`engine/calendar/sexagenary.py` 提供不含命理日界的純六十甲子數學；`engine/ziwei/fine_cycle_stems.py` 套用 `ziwei-fine-cycle-lunar-late-zi-v1` profile 解析 monthly/daily/hourly stems；`engine/ziwei/fine_cycle.py` 只負責把 `ResolvedCycleStem` 接到既有 `get_transformation_set()`、`fly_transformations()`、`build_cycle_layer()`。Composition 正式增加 `monthly / daily / hourly` scopes，但保留 Phase 2A duplicate/conflict/chart-isolation invariants。

**Tech Stack:** Python 3.9+ compatible syntax、標準函式庫 `datetime` / `dataclasses` / `unittest`、既有 `engine.calendar`、`engine.ziwei`；公開 qualification 解析 pinned GitHub source text，不增加 Node/npm runtime dependency。

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

- `core/命理分析作業規範.md`：先做 v1.2 runtime state reconciliation；Phase 2B promotion 後再加入 fine-cycle stem/flying 正式邊界。
- `core/命理推導計算規則.md`：移除 Calendar Resolver 未實作與舊 capability 敘述；完成後加入 Phase 2B profile。
- `core/核心提示詞.md`：同步 Calendar Resolver / fine-cycle capability boundary。
- `core/紫微流月推導規則.md`：同步流時現況與 fine-cycle transformation/flying 狀態。
- `core/紫微流日推導規則.md`：同步流時／Calendar Resolver 現況，完成後引用 Phase 2B day-stem profile。
- `core/紫微流時推導規則.md`：移除 Calendar Resolver 未實作舊敘述，完成後加入 hour stem / late-Zi policy。
- `engine/ziwei/errors.py`：新增 `ZiweiFineCycleError`，保留既有 class 不動。
- `engine/ziwei/models.py`：新增 immutable `FineCycleStemProfile` / `ResolvedCycleStem`。
- `engine/ziwei/capabilities.py`：新增 stem capability，promotion transformation/flying fine-cycle IDs。
- `engine/ziwei/composition.py`：擴充 fine-cycle scopes 與 availability；保留 duplicate/conflict protections。
- `README.md`、`CHANGELOG.md`、`docs/架構說明.md`、`docs/快速開始.md`、`docs/安裝到ChatGPT-Project.md`、`docs/更新與版本同步.md`：只在 Phase 2B exact-head gates 全綠後同步 implemented/experimental/on_demand 狀態；不在前面 Task 預先宣稱完成。

### 預設不修改

- `engine/bazi/*`
- `engine/ziwei/month.py`
- `engine/ziwei/day.py`
- `engine/ziwei/hour.py`
- `engine/ziwei/transformation_profiles.py`
- `engine/ziwei/transformations.py`
- `engine/ziwei/flying.py`

若實作中發現必須修改上述檔案，先停止並做 scope review；不得順手修改。

---

### Task 0: Reconcile Formal Rule Sources Before Fine-Cycle Code

**Files:**
- Create: `tests/test_rule_source_reconciliation.py`
- Modify: `core/命理分析作業規範.md`
- Modify: `core/命理推導計算規則.md`
- Modify: `core/核心提示詞.md`
- Modify: `core/紫微流月推導規則.md`
- Modify: `core/紫微流日推導規則.md`
- Modify: `core/紫微流時推導規則.md`

**Interfaces:**
- Consumes: current runtime states from `engine/ziwei/capabilities.py` and Calendar Resolver v1 already in `main`.
- Produces: rule-source baseline where existing features are described consistently; no Phase 2B capability is promoted yet.

- [ ] **Step 1: Write the RED rule-source test**

Create `tests/test_rule_source_reconciliation.py` with explicit current-state assertions:

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
    def test_current_runtime_capabilities_are_not_documented_as_missing(self):
        combined = "\n".join((ROOT / p).read_text(encoding="utf-8") for p in FILES)
        self.assertNotIn("Calendar / Input Resolver\n", combined)
        self.assertNotIn("Calendar Resolver\n- Cross-System Validation", combined)
        self.assertNotIn("Project 紫微流月定位層", combined)
        self.assertNotIn("Project Bazi Calendar Engine", combined)
        self.assertIn("Calendar Resolver v1", combined)
        self.assertIn("Ziwei Transformation Core", combined)
        self.assertIn("Ziwei Flying Core", combined)

    def test_fine_cycle_transformations_are_not_prematurely_marked_implemented(self):
        text = (ROOT / "core/命理推導計算規則.md").read_text(encoding="utf-8")
        self.assertIn("流月／流日／流時細部四化", text)
        self.assertIn("planned", text.lower())


if __name__ == "__main__":
    unittest.main()
```

The exact forbidden strings may be adjusted only to match the stale wording present on the feature base; the semantic assertions above must remain: existing Calendar/Phase2A capabilities cannot be described as missing, while Phase2B fine-cycle transformations still cannot be described as implemented.

- [ ] **Step 2: Run RED and confirm it fails for stale docs, not test syntax**

Run:

```bash
python -m unittest tests.test_rule_source_reconciliation -v
```

Expected: at least one assertion fails because current `core/` docs still contain stale Calendar/Phase2A wording. Any import/syntax error is an invalid RED and must be fixed before continuing.

- [ ] **Step 3: Reconcile only existing runtime facts**

Apply these exact semantic updates across the six core docs:

```text
Calendar Resolver v1 = implemented neutral infrastructure
紫微流月定位 = implemented / stable / default
紫微流日定位 = implemented / experimental / on_demand
紫微流時定位 = implemented / experimental / on_demand
Ziwei Transformation Core = implemented / stable / on_demand
Ziwei Flying Core = implemented / stable / on_demand
流月／流日／流時四化 = planned / on_demand   # still Phase 2B pending at Task 0
流月／流日／流時飛化 = planned / on_demand   # still Phase 2B pending at Task 0
流曜 = planned / on_demand
```

Use capability names such as `紫微流月定位` and `八字時間推導`; reserve `Project 推導盤面` only for data classification.

- [ ] **Step 4: Run GREEN gate**

```bash
python -m unittest tests.test_rule_source_reconciliation -v
python -m unittest discover -v
```

Expected: reconciliation test PASS and full repository still PASS at the current baseline count or higher.

- [ ] **Step 5: Record marker and commit**

Only after the assertions pass:

```text
RULE_SOURCE_RECONCILIATION_PASS
```

Commit:

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
- Consumes: Python `datetime.date`; raw valid heavenly stem / earthly branch strings.
- Produces:
  - `gregorian_jdn(value: date) -> int`
  - `sexagenary_day(value: date) -> tuple[str, str]`
  - `lunar_year_stem(lunar_year: int) -> str`
  - `five_tiger_month(year_stem: str, effective_month_ordinal: int) -> tuple[str, str]`
  - `five_mouse_hour(day_stem: str, hour_branch: str) -> tuple[str, str]`
- These functions do not know `CalendarContext`, Bazi, Ziwei profile, 23:00, leap-month split, or chart identity.

- [ ] **Step 1: Write RED tests for known public vectors and invariants**

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

    def test_lunar_year_stem_cycles(self):
        self.assertEqual(lunar_year_stem(2023), "癸")
        self.assertEqual(lunar_year_stem(2083), "癸")

    def test_five_tiger_month_vectors(self):
        self.assertEqual(five_tiger_month("癸", 1), ("甲", "寅"))
        self.assertEqual(five_tiger_month("癸", 6), ("己", "未"))
        self.assertEqual(five_tiger_month("癸", 13), ("丙", "寅"))

    def test_five_mouse_vectors(self):
        self.assertEqual(five_mouse_hour("己", "丑"), ("乙", "丑"))
        self.assertEqual(five_mouse_hour("庚", "子"), ("丙", "子"))
```

Also add invalid-stem/branch/month tests that expect `ValueError`, not silent modulo fallback.

- [ ] **Step 2: Verify RED**

```bash
python -m unittest tests.test_calendar_sexagenary -v
```

Expected: import failure because `engine.calendar.sexagenary` does not exist. This is the intended RED.

- [ ] **Step 3: Implement the minimal neutral helper**

Create `engine/calendar/sexagenary.py`:

```python
from __future__ import annotations

from datetime import date

GAN = tuple("甲乙丙丁戊己庚辛壬癸")
ZHI = tuple("子丑寅卯辰巳午未申酉戌亥")
MONTH_ZHI = tuple("寅卯辰巳午未申酉戌亥子丑")
FIRST_MONTH_STEM = {
    "甲": "丙", "己": "丙",
    "乙": "戊", "庚": "戊",
    "丙": "庚", "辛": "庚",
    "丁": "壬", "壬": "壬",
    "戊": "甲", "癸": "甲",
}
FIRST_HOUR_STEM = {
    "甲": "甲", "己": "甲",
    "乙": "丙", "庚": "丙",
    "丙": "戊", "辛": "戊",
    "丁": "庚", "壬": "庚",
    "戊": "壬", "癸": "壬",
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
    start = GAN.index(FIRST_MONTH_STEM[year_stem])
    offset = effective_month_ordinal - 1
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

Do not import Bazi code.

- [ ] **Step 4: Run targeted and Bazi regression**

```bash
python -m unittest tests.test_calendar_sexagenary -v
python -m unittest tests.test_project_bazi_calendar -v
```

Expected: both PASS; Phase 2B helper must not alter Bazi output.

- [ ] **Step 5: Commit**

```bash
git add engine/calendar/sexagenary.py tests/test_calendar_sexagenary.py
git commit -m "feat: add neutral sexagenary calendar helpers"
```

---

### Task 2: Add Fine-Cycle Error Contract, Immutable Models, and Profile

**Files:**
- Modify: `engine/ziwei/errors.py`
- Modify: `engine/ziwei/models.py`
- Create: `tests/ziwei_phase2b_fixtures.py`
- Create: `tests/test_ziwei_fine_cycle_stems.py`

**Interfaces:**
- Produces `ZiweiFineCycleError(code, message, details=None)` without changing `ZiweiPhase2AError`.
- Produces immutable `FineCycleStemProfile` and `ResolvedCycleStem`.
- Produces `DEFAULT_FINE_CYCLE_PROFILE` and `get_fine_cycle_profile(profile_id)` in Task 3's module; Task 2 locks model shape first.

- [ ] **Step 1: Write RED model/error tests**

Add to `tests/test_ziwei_fine_cycle_stems.py`:

```python
import unittest
from dataclasses import FrozenInstanceError
from datetime import date

from engine.ziwei.errors import ZiweiFineCycleError, ZiweiPhase2AError
from engine.ziwei.models import FineCycleStemProfile, LayerProvenance, ResolvedCycleStem


class FineCycleModelTests(unittest.TestCase):
    def test_phase2a_error_contract_still_exists(self):
        err = ZiweiPhase2AError("x", "message", {"a": 1})
        self.assertEqual(err.code, "x")
        self.assertEqual(err.details, {"a": 1})

    def test_fine_cycle_error_contract(self):
        err = ZiweiFineCycleError("invalid_fine_cycle_scope", "message", {"scope": "weekly"})
        self.assertEqual(err.code, "invalid_fine_cycle_scope")
        self.assertEqual(err.details, {"scope": "weekly"})

    def test_resolved_cycle_stem_is_immutable(self):
        provenance = LayerProvenance("project_derived", "Metaphysics Lab", None, "p", "1", "test")
        item = ResolvedCycleStem(
            "daily", "ziwei-day:2026-08-22@late_zi_forward-v1", "甲", "子",
            "ziwei-fine-cycle-lunar-late-zi-v1", "1.0-exp",
            date(2026, 8, 21), date(2026, 8, 22), None, "validated", provenance,
        )
        with self.assertRaises(FrozenInstanceError):
            item.heavenly_stem = "乙"
```

Model signatures to lock:

```python
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

- [ ] **Step 2: Verify RED**

```bash
python -m unittest tests.test_ziwei_fine_cycle_stems.FineCycleModelTests -v
```

Expected: import failures for the new class/model names.

- [ ] **Step 3: Add error/model definitions**

Append a new class to `engine/ziwei/errors.py` without touching `ZiweiPhase2AError`:

```python
class ZiweiFineCycleError(ValueError):
    def __init__(self, code, message, details=None):
        self.code = code
        self.details = dict(details or {})
        super().__init__(message)
```

Add the two frozen dataclasses above to `engine/ziwei/models.py`; import `date` from `datetime`.

- [ ] **Step 4: Add Phase 2B fixture builders**

Create `tests/ziwei_phase2b_fixtures.py` with a `calendar_context(...)` helper that constructs the existing immutable `CalendarContext` using real `CalendarInput`, `NormalizedTime`, `LunarDate`, `ProviderBundle`, `ValidationMetadata`, and `CalendarPolicies`. Default fixture:

```text
civil datetime = 2023-07-30 01:30 Asia/Taipei
lunar date = 2023-06-13 non-leap
hour branch = 丑
calendar validation = validated
metaphysics_day_boundary_applied = false
```

Also re-export/import `CHART`, `PROVENANCE`, `SYNTHETIC_STAR_RECORDS` from `tests.ziwei_phase2a_fixtures` for later integration tests instead of copying the chart fixture.

- [ ] **Step 5: Run GREEN**

```bash
python -m unittest tests.test_ziwei_fine_cycle_stems.FineCycleModelTests -v
python -m unittest tests.test_ziwei_phase2a_models -v
```

Expected: PASS; Phase 2A models remain unchanged.

- [ ] **Step 6: Marker and commit**

```text
FINE_CYCLE_MODEL_INVARIANTS_PASS
```

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
- `get_fine_cycle_profile(profile_id: str = FINE_CYCLE_PROFILE_ID) -> FineCycleStemProfile`
- `resolve_month_stem(context: CalendarContext, profile_id: str = FINE_CYCLE_PROFILE_ID) -> ResolvedCycleStem`
- Internal `_ensure_usable_context(context)` shared by day/hour tasks later.

- [ ] **Step 1: Write RED profile + monthly tests**

```python
from engine.ziwei.errors import ZiweiFineCycleError
from engine.ziwei.fine_cycle_stems import (
    FINE_CYCLE_PROFILE_ID,
    get_fine_cycle_profile,
    resolve_month_stem,
)
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

    def test_public_2023_lunar_sixth_month_vector(self):
        result = resolve_month_stem(calendar_context(lunar_year=2023, lunar_month=6, lunar_day=13))
        self.assertEqual((result.heavenly_stem, result.earthly_branch), ("己", "未"))
        self.assertEqual(result.reference, "lunar:2023-06")

    def test_leap_month_day_15_and_16_split(self):
        before = resolve_month_stem(calendar_context(lunar_year=2023, lunar_month=2, lunar_day=15, is_leap_month=True))
        after = resolve_month_stem(calendar_context(lunar_year=2023, lunar_month=2, lunar_day=16, is_leap_month=True))
        self.assertEqual(before.reference, "lunar:2023-L02-A")
        self.assertEqual(after.reference, "lunar:2023-L02-B")
        self.assertEqual((before.heavenly_stem, before.earthly_branch), ("乙", "卯"))
        self.assertEqual((after.heavenly_stem, after.earthly_branch), ("丙", "辰"))

    def test_23xx_does_not_advance_month_stem(self):
        context = calendar_context(
            local_hour=23,
            lunar_year=2023,
            lunar_month=6,
            lunar_day=30,
        )
        result = resolve_month_stem(context)
        self.assertEqual((result.heavenly_stem, result.earthly_branch), ("己", "未"))
```

Add a synthetic leap-twelfth day-16 test asserting ordinal 13 behavior continues the stem sequence and returns 寅 branch; label it synthetic in the test name.

- [ ] **Step 2: Verify RED**

```bash
python -m unittest tests.test_ziwei_fine_cycle_stems.FineCycleMonthTests -v
```

Expected: import failure because `fine_cycle_stems.py` does not exist.

- [ ] **Step 3: Implement profile, context guard, reference builder, month resolver**

Core constants:

```python
FINE_CYCLE_PROFILE_ID = "ziwei-fine-cycle-lunar-late-zi-v1"
FINE_CYCLE_RULE_VERSION = "1.0-exp"
DAY_BOUNDARY_PROFILE = "late_zi_forward-v1"
DEFAULT_FINE_CYCLE_PROFILE = FineCycleStemProfile(
    FINE_CYCLE_PROFILE_ID,
    FINE_CYCLE_RULE_VERSION,
    "lunar_month",
    "split_after_day_15",
    "lunar_year",
    DAY_BOUNDARY_PROFILE,
    "effective_ziwei_day_stem",
)
```

Required guard behavior:

```python
def _ensure_usable_context(context):
    if context.validation.calendar_conversion.status == "boundary_conflict":
        raise ZiweiFineCycleError(
            "calendar_context_unusable",
            "calendar conversion is in boundary conflict",
            {"boundary_id": context.validation.boundary_id},
        )
    if context.policies.metaphysics_day_boundary_applied:
        raise ZiweiFineCycleError(
            "calendar_boundary_already_applied",
            "metaphysics day boundary must be applied by the Ziwei profile exactly once",
        )
```

Monthly reference rules:

```python
if not context.lunar.is_leap_month:
    reference = f"lunar:{year:04d}-{month:02d}"
elif day <= 15:
    reference = f"lunar:{year:04d}-L{month:02d}-A"
else:
    reference = f"lunar:{year:04d}-L{month:02d}-B"
```

Use `lunar_year_stem()` and `five_tiger_month()` from `engine.calendar.sexagenary`; do not duplicate the tables.

- [ ] **Step 4: Run GREEN + existing month regression**

```bash
python -m unittest tests.test_ziwei_fine_cycle_stems.FineCycleMonthTests -v
python -m unittest tests.test_project_ziwei_month tests.test_ziwei_calendar_adapter -v
```

Expected: PASS; existing palace month positioning is unchanged.

- [ ] **Step 5: Markers and commit**

```text
MONTH_STEM_INVARIANTS_PASS
LEAP_MONTH_BOUNDARY_PASS
```

```bash
git add engine/ziwei/fine_cycle_stems.py tests/test_ziwei_fine_cycle_stems.py
git commit -m "feat: resolve Ziwei fine-cycle monthly stems"
```

---

### Task 4: Implement Daily Stem Resolver and Late-Zi Boundary

**Files:**
- Modify: `engine/ziwei/fine_cycle_stems.py`
- Modify: `tests/test_ziwei_fine_cycle_stems.py`

**Interfaces:**
- `resolve_day_stem(context: CalendarContext, profile_id: str = FINE_CYCLE_PROFILE_ID) -> ResolvedCycleStem`
- Internal `_effective_ziwei_date(context, profile) -> date`.

- [ ] **Step 1: Write RED day-boundary tests**

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

    def test_2300_advances_effective_date(self):
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

    def test_preapplied_metaphysics_boundary_is_rejected(self):
        with self.assertRaises(ZiweiFineCycleError) as cm:
            resolve_day_stem(calendar_context(metaphysics_day_boundary_applied=True))
        self.assertEqual(cm.exception.code, "calendar_boundary_already_applied")

    def test_calendar_boundary_conflict_is_rejected(self):
        with self.assertRaises(ZiweiFineCycleError) as cm:
            resolve_day_stem(calendar_context(calendar_status="boundary_conflict"))
        self.assertEqual(cm.exception.code, "calendar_context_unusable")
```

Also assert `boundary_caution` is preserved as `calendar_validation_status == "boundary_caution"` rather than rejected.

- [ ] **Step 2: Verify RED**

```bash
python -m unittest tests.test_ziwei_fine_cycle_stems.FineCycleDayTests -v
```

Expected: missing function or failed assertions.

- [ ] **Step 3: Implement minimal daily resolver**

```python
def _effective_ziwei_date(context, profile):
    civil = context.normalized_time.gregorian_date
    local = context.normalized_time.local_datetime
    if profile.ziwei_day_boundary != DAY_BOUNDARY_PROFILE:
        raise ZiweiFineCycleError("invalid_fine_cycle_profile", "unsupported day boundary profile")
    return civil + timedelta(days=1) if local.hour >= 23 else civil


def resolve_day_stem(context, profile_id=FINE_CYCLE_PROFILE_ID):
    _ensure_usable_context(context)
    profile = get_fine_cycle_profile(profile_id)
    effective = _effective_ziwei_date(context, profile)
    stem, branch = sexagenary_day(effective)
    reference = "ziwei-day:%s@%s" % (effective.isoformat(), profile.ziwei_day_boundary)
    return ResolvedCycleStem(...)
```

`civil_date` is the CalendarContext civil Gregorian date; `effective_date` is the profile-adjusted date. Do not mutate CalendarContext.

- [ ] **Step 4: Run GREEN + Calendar/Bazi boundary regression**

```bash
python -m unittest tests.test_ziwei_fine_cycle_stems.FineCycleDayTests -v
python -m unittest tests.test_calendar_resolver tests.test_calendar_timezone tests.test_project_bazi_calendar -v
```

Expected: PASS. Calendar remains midnight-based; Bazi retains its own existing output.

- [ ] **Step 5: Markers and commit**

```text
DAY_STEM_BOUNDARY_PASS
CALENDAR_BOUNDARY_DOUBLE_APPLY_REJECTED
```

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
- `resolve_hour_stem(context: CalendarContext, profile_id: str = FINE_CYCLE_PROFILE_ID) -> ResolvedCycleStem`
- Must call/derive from the exact same effective day calculation as `resolve_day_stem()`.

- [ ] **Step 1: Write RED hour tests**

```python
from engine.ziwei.fine_cycle_stems import resolve_hour_stem


class FineCycleHourTests(unittest.TestCase):
    def test_public_regular_hour_vector(self):
        result = resolve_hour_stem(calendar_context(
            gregorian_date=date(1987, 12, 6), local_hour=21, local_minute=30, hour_branch="亥",
        ))
        self.assertEqual((result.heavenly_stem, result.earthly_branch), ("乙", "亥"))

    def test_late_zi_uses_next_day_stem_for_hour(self):
        day = resolve_day_stem(calendar_context(
            gregorian_date=date(1987, 12, 6), local_hour=23, local_minute=30, hour_branch="子",
        ))
        hour = resolve_hour_stem(calendar_context(
            gregorian_date=date(1987, 12, 6), local_hour=23, local_minute=30, hour_branch="子",
        ))
        self.assertEqual(day.heavenly_stem, "庚")
        self.assertEqual((hour.heavenly_stem, hour.earthly_branch), ("丙", "子"))
        self.assertEqual(hour.effective_date, day.effective_date)
        self.assertEqual(hour.reference, "ziwei-hour:1987-12-07:子@late_zi_forward-v1")
```

Add 10 day-stem × 12 hour-branch invariant loop against `five_mouse_hour()` to cover all groups.

- [ ] **Step 2: Verify RED**

```bash
python -m unittest tests.test_ziwei_fine_cycle_stems.FineCycleHourTests -v
```

Expected: missing function or coherence assertion failure.

- [ ] **Step 3: Implement hourly resolver**

Implementation requirement:

```python
def resolve_hour_stem(context, profile_id=FINE_CYCLE_PROFILE_ID):
    _ensure_usable_context(context)
    profile = get_fine_cycle_profile(profile_id)
    effective = _effective_ziwei_date(context, profile)
    day_stem, _ = sexagenary_day(effective)
    stem, branch = five_mouse_hour(day_stem, context.normalized_time.hour_branch)
    reference = "ziwei-hour:%s:%s@%s" % (
        effective.isoformat(), branch, profile.ziwei_day_boundary
    )
    return ResolvedCycleStem(...)
```

Do not call Bazi `time_pillar()` and do not recompute hour branch from civil hour.

- [ ] **Step 4: Run GREEN and existing flow-hour regression**

```bash
python -m unittest tests.test_ziwei_fine_cycle_stems.FineCycleHourTests -v
python -m unittest tests.test_project_ziwei_hour tests.test_ziwei_calendar_adapter -v
```

Expected: PASS.

- [ ] **Step 5: Markers and commit**

```text
HOUR_STEM_INVARIANTS_PASS
LATE_ZI_COHERENCE_PASS
```

```bash
git add engine/ziwei/fine_cycle_stems.py tests/test_ziwei_fine_cycle_stems.py
git commit -m "feat: resolve Ziwei hourly stems coherently"
```

---

### Task 6: Integrate Resolved Stems with Transformation and Flying Core

**Files:**
- Create: `engine/ziwei/fine_cycle.py`
- Create: `tests/test_ziwei_fine_cycle_integration.py`

**Interfaces:**
- Consumes `ResolvedCycleStem`, `ChartIdentity`, `StarLocationIndex`.
- Produces `build_fine_cycle_layer(resolution, chart_identity, star_locations, transformation_profile_id=PROFILE_ID) -> CycleTransformationLayer`.
- Reuses existing `get_transformation_set()`, `fly_transformations()`, `build_cycle_layer()`; no new four-transformation table.

- [ ] **Step 1: Write RED integration tests**

```python
import unittest

from engine.ziwei.basis import build_star_location_index
from engine.ziwei.errors import ZiweiFineCycleError
from engine.ziwei.fine_cycle import build_fine_cycle_layer
from engine.ziwei.fine_cycle_stems import resolve_month_stem
from tests.ziwei_phase2b_fixtures import CHART, PROVENANCE, SYNTHETIC_STAR_RECORDS, calendar_context


class FineCycleTransformationIntegrationTests(unittest.TestCase):
    def test_month_resolution_builds_four_transformations_and_edges(self):
        stars = build_star_location_index(SYNTHETIC_STAR_RECORDS, CHART, PROVENANCE)
        resolution = resolve_month_stem(calendar_context(lunar_year=2023, lunar_month=6, lunar_day=13))
        layer = build_fine_cycle_layer(resolution, CHART, stars)
        self.assertEqual(layer.identity.scope, "monthly")
        self.assertEqual(layer.identity.reference, resolution.reference)
        self.assertEqual(layer.heavenly_stem, resolution.heavenly_stem)
        self.assertEqual(len(layer.transformations.transformations), 4)
        self.assertEqual(len(layer.flying_edges), 4)

    def test_chart_mismatch_is_rejected(self):
        # Build star index for a different ChartIdentity and assert fail closed.
        with self.assertRaises(Exception):
            ...
```

Do not leave the ellipsis in the committed test. Materialize `ChartIdentity("other", "natal", "synthetic-v1")`, build its star index, pass it with the original chart identity, and assert the existing `ZiweiPhase2AError.code == "chart_basis_mismatch"`.

Add a test constructing a tampered `ResolvedCycleStem` whose scope/reference/stem is inconsistent with the requested source and assert `ZiweiFineCycleError.code == "fine_cycle_stem_mismatch"` before lower-level flying executes.

- [ ] **Step 2: Verify RED**

```bash
python -m unittest tests.test_ziwei_fine_cycle_integration.FineCycleTransformationIntegrationTests -v
```

Expected: import failure because `fine_cycle.py` does not exist.

- [ ] **Step 3: Implement thin orchestration**

Core shape:

```python
from .composition import build_cycle_layer
from .errors import ZiweiFineCycleError
from .flying import fly_transformations
from .models import CycleStemSource, LayerIdentity
from .transformation_profiles import PROFILE_ID
from .transformations import get_transformation_set

FINE_SCOPES = {"monthly", "daily", "hourly"}


def build_fine_cycle_layer(resolution, chart_identity, star_locations, transformation_profile_id=PROFILE_ID):
    if resolution.scope not in FINE_SCOPES:
        raise ZiweiFineCycleError(
            "invalid_fine_cycle_scope", "unsupported fine-cycle scope", {"scope": resolution.scope}
        )
    if star_locations.chart_identity != chart_identity:
        from .errors import ZiweiPhase2AError
        raise ZiweiPhase2AError("chart_basis_mismatch", "fine-cycle chart and star index mismatch")
    source = CycleStemSource(
        "cycle_stem", chart_identity, resolution.scope, resolution.reference, resolution.heavenly_stem
    )
    transformations = get_transformation_set(resolution.heavenly_stem, transformation_profile_id)
    if transformations.heavenly_stem != resolution.heavenly_stem:
        raise ZiweiFineCycleError("fine_cycle_stem_mismatch", "resolved and transformation stems differ")
    edges = fly_transformations(transformations, star_locations, source)
    identity = LayerIdentity(
        chart_identity.chart_id, resolution.scope, resolution.reference, transformations.profile_id
    )
    return build_cycle_layer(
        identity, source, transformations, edges, resolution.provenance,
        earthly_branch=resolution.earthly_branch,
    )
```

Do not calculate month/day/hour stem inside this module.

- [ ] **Step 4: Run targeted tests**

At this point the existing Composition scope guard is expected to reject monthly/daily/hourly. That is acceptable only if the RED proves the remaining failure is exactly `unsupported_scope` from Composition. Record that as the dependency for Task 7; do not weaken the test to accept failure.

```bash
python -m unittest tests.test_ziwei_fine_cycle_integration.FineCycleTransformationIntegrationTests -v
```

Expected before Task 7: the orchestration reaches `build_cycle_layer()` and fails specifically because Composition does not yet accept the fine scope. This is a staged RED, not a Task 6 GREEN.

- [ ] **Step 5: Commit orchestration only after confirming the staged RED reason**

Commit the module and test as an intentionally staged dependency commit only if repository workflow allows RED commits on feature branches; otherwise fold Task 6 and Task 7 into one local RED→GREEN cycle and make the commit after Task 7. Preferred repository behavior here is **no persistent RED commit**, so do not push a failing feature head.

---

### Task 7: Expand Composition to Monthly / Daily / Hourly Scopes

**Files:**
- Modify: `engine/ziwei/composition.py`
- Modify: `tests/test_ziwei_composition.py`
- Modify: `tests/test_ziwei_fine_cycle_integration.py`

**Interfaces:**
- `SUPPORTED_SCOPES = {"birth_year", "decadal", "yearly", "monthly", "daily", "hourly"}`.
- Existing `build_cycle_layer()` now accepts fine scopes under the same component-coherence invariants.
- `_availability()` reports fine-cycle transformations as conditional/available-by-resolution rather than hard unavailable.

- [ ] **Step 1: Replace old RED test that expects fine-cycle rejection**

In `tests/test_ziwei_composition.py`, replace `test_fine_cycle_scope_is_rejected` with explicit accepted-scope tests:

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
```

Add tests proving:

- same fine-cycle identity duplicated → `duplicate_layer_identity`;
- same identity different layer → `layer_conflict`;
- monthly/daily/hourly can coexist with yearly in one stack;
- fine-cycle chart mismatch still → `chart_basis_mismatch`;
- arbitrary scope `weekly` still → `unsupported_scope`.

- [ ] **Step 2: Verify RED**

```bash
python -m unittest tests.test_ziwei_composition -v
python -m unittest tests.test_ziwei_fine_cycle_integration -v
```

Expected: fine scopes fail because current `SUPPORTED_SCOPES` is Phase2A-only.

- [ ] **Step 3: Expand Composition minimally**

Change:

```python
SUPPORTED_SCOPES = {"birth_year", "decadal", "yearly", "monthly", "daily", "hourly"}
```

Update the unsupported-scope message to no longer say "Phase 2A does not execute fine-cycle transformations". Keep all identity/source/profile/stem/edge coherence checks unchanged.

Update availability from hard `unavailable / fine_cycle_stem_resolver_not_enabled` to:

```python
"monthly_transformations": AvailabilityRecord("conditional", "matching_resolved_stem_required")
"daily_transformations": AvailabilityRecord("conditional", "matching_resolved_stem_required")
"hourly_transformations": AvailabilityRecord("conditional", "matching_resolved_stem_required")
```

Do not mark a layer available unless an actual `CycleTransformationLayer` has been built.

- [ ] **Step 4: Run GREEN**

```bash
python -m unittest tests.test_ziwei_composition -v
python -m unittest tests.test_ziwei_fine_cycle_integration -v
python -m unittest tests.test_ziwei_flying -v
```

Expected: PASS.

- [ ] **Step 5: Markers and commit Task 6 + Task 7 together if needed**

```text
FINE_CYCLE_TRANSFORMATIONS_PASS
FINE_CYCLE_FLYING_PASS
FINE_CYCLE_COMPOSITION_PASS
FINE_CYCLE_NEGATIVE_CASES_PASS
```

```bash
git add engine/ziwei/fine_cycle.py engine/ziwei/composition.py tests/test_ziwei_fine_cycle_integration.py tests/test_ziwei_composition.py
git commit -m "feat: integrate Ziwei fine-cycle transformation layers"
```

---

### Task 8: Promote Capability Lifecycle to Implemented / Experimental / On-Demand

**Files:**
- Modify: `engine/ziwei/capabilities.py`
- Create: `tests/test_ziwei_phase2b_capabilities.py`
- Modify: `tests/test_ziwei_phase2a_capabilities.py`

**Interfaces:**
- New IDs: `ziwei.flow_month_stem`, `ziwei.flow_day_stem`, `ziwei.flow_hour_stem`.
- Existing fine-cycle transformation/flying IDs move from planned to implemented experimental.
- `ziwei.flowing_stars` remains planned.

- [ ] **Step 1: Write RED lifecycle tests**

```python
import unittest

from engine.ziwei.capabilities import can_execute, get_capability, should_run_by_default


class ZiweiPhase2BCapabilityTests(unittest.TestCase):
    def test_fine_cycle_stems_are_experimental_on_demand(self):
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
        for capability_id in (
            "ziwei.flow_month_transformations", "ziwei.flow_day_transformations", "ziwei.flow_hour_transformations",
            "ziwei.flow_month_flying", "ziwei.flow_day_flying", "ziwei.flow_hour_flying",
        ):
            cap = get_capability(capability_id)
            self.assertEqual((cap["implementation"], cap["maturity"], cap["routing"]),
                             ("implemented", "experimental", "on_demand"))
            self.assertTrue(can_execute(capability_id))
            self.assertFalse(should_run_by_default(capability_id))

    def test_flowing_stars_remain_planned(self):
        self.assertEqual(get_capability("ziwei.flowing_stars")["implementation"], "planned")
```

Update Phase2A test `test_fine_cycle_capabilities_remain_planned` so it no longer asserts stale Phase2A state. Replace it with an invariant that Phase2A core remains stable/on-demand and flowing stars remain planned; Phase2B lifecycle belongs only in the new test file.

- [ ] **Step 2: Verify RED**

```bash
python -m unittest tests.test_ziwei_phase2b_capabilities -v
```

Expected: missing stem IDs / planned fine-cycle transformations.

- [ ] **Step 3: Update registry**

Stem modules:

```text
ziwei.flow_month_stem -> engine.ziwei.fine_cycle_stems
ziwei.flow_day_stem   -> engine.ziwei.fine_cycle_stems
ziwei.flow_hour_stem  -> engine.ziwei.fine_cycle_stems
```

Dependencies:

```text
flow_month_transformations -> flow_month_stem + ziwei.transformations
flow_day_transformations   -> flow_day_stem + ziwei.transformations
flow_hour_transformations  -> flow_hour_stem + ziwei.transformations
flow_*_flying              -> matching flow_*_transformations + ziwei.flying
```

All Phase2B promoted capabilities:

```text
implementation = implemented
maturity = experimental
routing = on_demand
rule_version = 1.0-exp
```

Do not modify `ziwei.flow_month_palaces` maturity/routing and do not promote existing flow day/hour palace positioning.

- [ ] **Step 4: Run GREEN**

```bash
python -m unittest tests.test_ziwei_phase2b_capabilities tests.test_ziwei_phase2a_capabilities tests.test_ziwei_capabilities -v
```

Expected: PASS.

- [ ] **Step 5: Marker and commit**

```text
CAPABILITY_EXPERIMENTAL_ON_DEMAND_PASS
```

```bash
git add engine/ziwei/capabilities.py tests/test_ziwei_phase2b_capabilities.py tests/test_ziwei_phase2a_capabilities.py
git commit -m "feat: enable experimental Ziwei fine-cycle capabilities"
```

---

### Task 9: Build Public lunar-lite Qualification

**Files:**
- Create: `tools/qualify_ziwei_phase2b_public.py`
- Create: `tests/test_ziwei_phase2b_qualification.py`
- Create after qualification run: `qualification/ziwei/phase2b/public-lunar-lite-1d104fff.json`

**Interfaces:**
- Tool consumes local copies of pinned upstream source files passed by path; it never fetches network at runtime.
- `parse_lunar_lite_vectors(source_text: str) -> tuple[dict, ...]`
- `qualify_lunar_lite(vectors, source_revision, run_timestamp) -> dict`

- [ ] **Step 1: Write RED parser and report-contract tests**

Test fixture source text should contain a minimal excerpt with the exact pinned public vectors, including:

```text
lunar 2023-6-13, timeIndex 1, non-leap -> 癸卯 己未 己丑 乙丑
lunar 2023-6-13, timeIndex 12, non-leap -> 癸卯 己未 庚寅 丙子
lunar 2023-2-11, timeIndex 1, leap -> 癸卯 乙卯 己丑 乙丑
solar 1987-12-6, timeIndex 11 -> 丁卯 辛亥 己丑 乙亥
solar 1987-12-6, timeIndex 12 -> 丁卯 辛亥 庚寅 丙子
```

Tests must verify:

- parser rejects missing/changed expected vectors with `ZiweiFineCycleError("qualification_mismatch", ...)`;
- report includes source name `SylarLong/lunar-lite`, revision `1d104fffa31609e9f112898cc57545827e8d57ae`, package `0.2.8`;
- externally covered cases are separated from synthetic-only edge cases;
- no Astralium fields appear.

- [ ] **Step 2: Verify RED**

```bash
python -m unittest tests.test_ziwei_phase2b_qualification -v
```

Expected: missing qualification tool import.

- [ ] **Step 3: Implement parser/evaluator**

Follow Phase2A tool style: parser only reads text supplied through CLI. It must compare Project outputs from `five_tiger_month`, `sexagenary_day`, `five_mouse_hour`, and fine-cycle resolver where enough CalendarContext data is constructible.

CLI:

```text
python tools/qualify_ziwei_phase2b_public.py \
  --lunar-lite-ganzhi-ts /tmp/lunar-lite-ganzhi.ts \
  --lunar-lite-tests-ts /tmp/lunar-lite-ganzhi.test.ts \
  --iztro-functional-ts /tmp/FunctionalAstrolabe.ts \
  --lunar-lite-revision 1d104fffa31609e9f112898cc57545827e8d57ae \
  --iztro-revision 814b77e6371e1050cac31bbf674db3c3138fcfde \
  --output-dir qualification/ziwei/phase2b \
  --run-timestamp 2026-08-21T00:00:00Z
```

The tool may produce both public JSON files in one run, but keep lunar-lite and iztro evidence separate.

- [ ] **Step 4: Run qualification against exact pinned sources**

Fetch source snapshots outside production runtime using the pinned revisions, save them to temporary validation paths, and run the CLI. Expected lunar-lite report:

```text
status = PASS
external_coverage > 0
mismatches = []
not_externally_covered includes leap-twelfth-half edge if no pinned vector exists
```

Only then print:

```text
PUBLIC_LUNAR_LITE_QUALIFICATION_PASS
```

- [ ] **Step 5: Run tests and commit evidence**

```bash
python -m unittest tests.test_ziwei_phase2b_qualification -v
```

Commit only source metadata, public expected vectors/comparison results, and evidence digests. Do not commit downloaded upstream source files.

```bash
git add tools/qualify_ziwei_phase2b_public.py tests/test_ziwei_phase2b_qualification.py qualification/ziwei/phase2b/public-lunar-lite-1d104fff.json
git commit -m "test: qualify Ziwei fine-cycle stems against lunar-lite"
```

---

### Task 10: Qualify iztro Fine-Cycle Stem→Mutagen Integration

**Files:**
- Modify: `tools/qualify_ziwei_phase2b_public.py`
- Modify: `tests/test_ziwei_phase2b_qualification.py`
- Create after qualification run: `qualification/ziwei/phase2b/public-iztro-814b77e6.json`

**Interfaces:**
- `parse_iztro_fine_cycle_integration(source_text: str) -> dict[str, bool]`.
- Must prove pinned iztro `monthly`, `daily`, `hourly` each feed their own stem into `getMutagensByHeavenlyStem(...)`.

- [ ] **Step 1: Write RED source-contract tests**

Tests must require these semantic patterns in pinned `FunctionalAstrolabe.ts`:

```text
monthly ... mutagen: getMutagensByHeavenlyStem(monthly[0])
daily   ... mutagen: getMutagensByHeavenlyStem(daily[0])
hourly  ... mutagen: getMutagensByHeavenlyStem(hourly[0])
```

The parser must fail if any one scope is absent or references a different stem source.

- [ ] **Step 2: Verify RED**

```bash
python -m unittest tests.test_ziwei_phase2b_qualification -v
```

Expected: iztro integration test fails until parser/evidence path is implemented.

- [ ] **Step 3: Implement and run pinned-source integration qualification**

The evidence JSON must contain:

```json
{
  "source_name": "SylarLong/iztro",
  "source_revision": "814b77e6371e1050cac31bbf674db3c3138fcfde",
  "package_version": "2.6.0",
  "monthly_mutagen_uses_monthly_stem": true,
  "daily_mutagen_uses_daily_stem": true,
  "hourly_mutagen_uses_hourly_stem": true,
  "status": "PASS"
}
```

Also run at least one Project resolution per scope through `get_transformation_set()` and assert exactly four transformations; this verifies our integration path, not iztro's star locations.

Only then print:

```text
PUBLIC_IZTRO_INTEGRATION_PASS
```

- [ ] **Step 4: Regression and commit**

```bash
python -m unittest tests.test_ziwei_phase2b_qualification tests.test_ziwei_transformations -v
```

```bash
git add tools/qualify_ziwei_phase2b_public.py tests/test_ziwei_phase2b_qualification.py qualification/ziwei/phase2b/public-iztro-814b77e6.json
git commit -m "test: qualify fine-cycle transformation integration against iztro"
```

---

### Task 11: Record Astralium Pending State and Enforce Privacy

**Files:**
- Create: `qualification/ziwei/phase2b/private-astralium-summary.json`
- Modify: `tests/test_ziwei_phase2b_qualification.py`

**Interfaces:**
- Repo stores only aggregate `PENDING`; no raw chart, birthday, name, star locations, palace stems, expected fine-cycle edges.

- [ ] **Step 1: Write RED privacy/pending tests**

```python
import json
from pathlib import Path


def test_private_summary_is_pending_without_raw_chart_payload(self):
    path = Path("qualification/ziwei/phase2b/private-astralium-summary.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    self.assertEqual(payload["status"], "PENDING")
    self.assertEqual(payload["reason_code"], "fine_cycle_source_not_available")
    raw = path.read_text(encoding="utf-8")
    for forbidden in (
        "star_locations", "palace_stems", "expected_edges", "birth_datetime", "出生年月", "姓名"
    ):
        self.assertNotIn(forbidden, raw)
```

Use `unittest.TestCase` syntax in the actual file.

- [ ] **Step 2: Verify RED**

```bash
python -m unittest tests.test_ziwei_phase2b_qualification -v
```

Expected: missing private summary file.

- [ ] **Step 3: Create aggregate pending summary**

Exact minimal payload:

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

- [ ] **Step 4: Run GREEN**

```bash
python -m unittest tests.test_ziwei_phase2b_qualification -v
```

Only then record:

```text
ASTRALIUM_FINE_CYCLE_PENDING
PRIVACY_PASS
```

- [ ] **Step 5: Commit**

```bash
git add qualification/ziwei/phase2b/private-astralium-summary.json tests/test_ziwei_phase2b_qualification.py
git commit -m "test: record pending Astralium fine-cycle qualification"
```

---

### Task 12: Promote Formal Rules and User-Facing Docs After Code Gates Are Green

**Files:**
- Modify: `core/命理分析作業規範.md`
- Modify: `core/命理推導計算規則.md`
- Modify: `core/核心提示詞.md`
- Modify: `core/紫微流月推導規則.md`
- Modify: `core/紫微流日推導規則.md`
- Modify: `core/紫微流時推導規則.md`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `docs/架構說明.md`
- Modify: `docs/快速開始.md`
- Modify: `docs/安裝到ChatGPT-Project.md`
- Modify: `docs/更新與版本同步.md`

**Interfaces:**
- Documents exact implemented state only after Tasks 1–11 are green.
- Formal Metaphysics Lab release version remains `v1.2.0` during feature/design integration; a later release-maintenance step decides whether to cut `v1.3.0`. Do not silently retag v1.2.0.

- [ ] **Step 1: Write/update documentation consistency test before changing docs**

Extend `tests/test_rule_source_reconciliation.py` so post-Phase2B docs must contain:

```text
ziwei-fine-cycle-lunar-late-zi-v1
late_zi_forward-v1
流月／流日／流時天干 = implemented / experimental / on_demand
流月／流日／流時四化 = implemented / experimental / on_demand
流月／流日／流時飛化 = implemented / experimental / on_demand
流曜 = planned / on_demand
Astralium fine-cycle qualification = pending
```

It must also reject statements that Calendar Resolver performs the Ziwei 23:00 rollover or that fine-cycle capabilities are default/stable.

- [ ] **Step 2: Verify RED**

```bash
python -m unittest tests.test_rule_source_reconciliation -v
```

Expected: fail because docs have not yet been promoted.

- [ ] **Step 3: Update formal rules and README/docs**

Required public wording:

```text
Ziwei Fine Cycle Stem Resolver v1
- implementation: implemented
- maturity: experimental
- routing: on_demand
- rule profile: ziwei-fine-cycle-lunar-late-zi-v1
- day boundary: late_zi_forward-v1
- public qualification: lunar-lite PASS; iztro integration PASS
- private Astralium fine-cycle qualification: pending
```

Clarify:

- `Project 推導盤面` remains the data classification.
- Calendar Resolver remains neutral and midnight-based.
- Monthly boundary remains lunar; 23:00 affects day/hour stem only.
- Fine-cycle four transformations/flying are now executable on demand.
- Flowing stars remain Phase 2C planned.
- Existing flow day/hour palace positioning maturity remains Experimental.

`CHANGELOG.md` should add an **Unreleased / Phase 2B** section rather than pretending a new formal release tag already exists. `VERSION.md` is intentionally not modified in this feature plan; formal version bump happens only after Phase 2B reaches `main` and a separate release decision is made.

- [ ] **Step 4: Run docs consistency + local link check**

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

Expected: PASS.

- [ ] **Step 5: Commit docs**

```bash
git add core README.md CHANGELOG.md docs tests/test_rule_source_reconciliation.py
git commit -m "docs: document experimental Ziwei fine-cycle capabilities"
```

---

### Task 13: Exact-Head Final Validation and Promotion Gate

**Files:**
- No production changes unless a validation failure reveals a real defect; any defect requires its own RED/GREEN fix before re-running this task.
- Temporary validation workflow must stay outside the formal feature diff and must never be merged.

**Interfaces:**
- Consumes exact feature head.
- Produces evidence that all acceptance markers correspond to actual assertions on the same SHA.

- [ ] **Step 1: Freeze exact feature SHA and formal diff scope**

Record:

```bash
FEATURE_SHA=$(git rev-parse HEAD)
echo "$FEATURE_SHA"
git -c core.quotePath=false diff --name-only design/ziwei-fine-cycle-stem-resolver...HEAD
```

Assert changed files are only those declared by this plan plus the plan/spec themselves; no Qimen, unrelated Bazi production code, private chart, or permanent `.github/` workflow.

- [ ] **Step 2: Python supported-version syntax gate**

At minimum parse all changed production Python files as Python 3.9 syntax:

```bash
python - <<'PY'
import ast, subprocess
files = subprocess.check_output(
    ['git', '-c', 'core.quotePath=false', 'diff', '--name-only', 'design/ziwei-fine-cycle-stem-resolver...HEAD'],
    text=True,
).splitlines()
for path in files:
    if path.endswith('.py') and (path.startswith('engine/') or path.startswith('tools/')):
        source = open(path, encoding='utf-8').read()
        ast.parse(source, filename=path, feature_version=(3, 9))
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

Expected: all PASS.

- [ ] **Step 4: Run Ziwei / Calendar / Bazi / full regressions**

```bash
python -m unittest discover -v -s tests -p 'test_ziwei*.py'
python -m unittest discover -v -s tests -p 'test_calendar*.py'
python -m unittest tests.test_project_bazi_calendar -v
python -m unittest discover -v
```

Record actual counts from output; do not hard-code expected new totals in advance. Existing v1.2.0 baseline lower bounds are:

```text
Ziwei >= 83
Calendar >= 35
Bazi >= 10
Full repo >= 132
```

All must be PASS and new counts must not drop below baseline.

- [ ] **Step 5: Re-run qualification and privacy/scope gates on the same SHA**

Using exact pinned public source snapshots, re-run `tools/qualify_ziwei_phase2b_public.py` and assert both committed public JSONs match the regenerated result except allowed run timestamp metadata. Re-run private-summary forbidden-key scan.

- [ ] **Step 6: Assert capability boundaries**

Programmatically verify on exact head:

```text
ziwei.flow_month_stem/day/hour_stem = implemented / experimental / on_demand / 1.0-exp
ziwei.flow_month/day/hour_transformations = implemented / experimental / on_demand / 1.0-exp
ziwei.flow_month/day/hour_flying = implemented / experimental / on_demand / 1.0-exp
ziwei.flowing_stars = planned / on_demand / not executable
ziwei.transformations/flying = still implemented / stable / on_demand / 1.0
flow_day_palaces / flow_hour_palaces remain experimental / on_demand
```

- [ ] **Step 7: Emit acceptance markers only after assertions pass**

Final evidence must contain all of:

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

- [ ] **Step 8: Request code review on exact feature head**

Review specifically for:

- hidden reuse of Bazi policy;
- month boundary/day boundary cross-contamination;
- 23:00 double rollover;
- resolved stem/source/identity mismatch;
- fine-cycle layer collision;
- accidental default/stable promotion;
- private Astralium leakage;
- synthetic test mislabeled as external qualification.

Important findings require independent RED→GREEN fixes and a full exact-head revalidation.

- [ ] **Step 9: Stop at feature→design approval gate**

When exact feature head is fully GREEN, open formal PR:

```text
feature/ziwei-fine-cycle-stem-resolver-v1
→ design/ziwei-fine-cycle-stem-resolver
```

Do **not** merge automatically. Report exact SHA, diff scope, test counts, qualification evidence, and ask for explicit user approval.

---

## Post-Feature Integration Procedure

After user explicitly approves feature→design:

1. Re-read PR state/head/base/mergeability and verify exact approved head SHA.
2. Squash merge feature→design.
3. Run design post-merge validation on the actual design merge commit with the same gates and actual test counts.
4. If any gate fails, stop; do not open design→main.
5. If GREEN, open formal design→main PR.
6. Stop and obtain a **second explicit user approval**.
7. After design→main merge, run post-main exact-head validation again.
8. Only after post-main is GREEN may Phase 2B be called closed.
9. Formal release version/tag is a separate release-maintenance decision; do not silently reuse or move `v1.2.0`.

---

## Plan Self-Review Checklist

Before execution, verify:

- [ ] Every spec requirement maps to Task 0–13.
- [ ] No `TBD`, `TODO`, "similar to Task N", or unspecified error handling remains.
- [ ] Function names are consistent across tasks: `sexagenary_day`, `five_tiger_month`, `five_mouse_hour`, `resolve_month_stem`, `resolve_day_stem`, `resolve_hour_stem`, `build_fine_cycle_layer`.
- [ ] Error classes remain separated: existing `ZiweiPhase2AError`; new `ZiweiFineCycleError`.
- [ ] Public profile IDs and rule versions exactly match the approved spec.
- [ ] Fine-cycle capabilities never become default or stable in v1.
- [ ] Flowing stars remain out of scope.
- [ ] No private Astralium raw payload enters the repository.
- [ ] No implementation begins until the user explicitly approves this plan.
