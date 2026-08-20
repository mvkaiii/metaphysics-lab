# Ziwei Flow-Day Capability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 PR #1 模組化架構之上，完成可重現、可測試、可外部校驗的紫微流日定位能力，並以 `implemented / experimental / on_demand` 納入 capability registry。

**Architecture:** 流日沿用既有斗君流月定位，先取得流月命宮，再依「流月所在宮起初一、順行十二宮、一日一宮」推進。能力狀態集中於 `engine/ziwei/capabilities.py`；`day.py` 只負責流日定位與結構化輸出。流日第一版不加入流日四化、流曜、流時或 Cross-System Validation。

**Tech Stack:** Python 3.9+、標準函式庫 `unittest`；不新增第三方執行期相依套件。

**Spec:** `docs/設計/Metaphysics-Lab-v1.2-架構設計.md`

## Global Constraints

- 資料分類固定標示為 `Project 推導盤面`，不得冒充 Astralium 或其他第三方直接輸出。
- 紫微流月既有斗君、農曆初一換月、閏月前後半規則不得改變。
- 流日第一版只能在固定算法、自動測試、人工案例與至少兩個可信外部來源交叉一致後標 `experimental`。
- `on_demand` 代表可執行但不預設每次執行。
- Experimental 可以參與分析，但必須降權，不能單獨支撐高度確信。
- 本 PR 不實作流時、細部四化、流曜、細層飛化或 Cross-System Validation。
- 真實命主私人資料不得寫入共用 repo。

---

## File Map

- Create: `engine/ziwei/capabilities.py` — capability 狀態與查詢介面。
- Create: `engine/ziwei/day.py` — 紫微流日定位算法與 CLI。
- Modify: `engine/ziwei/common.py` — 提供通用十二宮重排 helper，避免 month/day 重複。
- Modify: `engine/ziwei/month.py` — 改用 common helper，輸出行為保持一致；features 改以 capability 語意補充，不把 on-demand 誤寫成不存在。
- Create: `tests/test_project_ziwei_day.py` — 流日算法、邊界、結構化輸出測試。
- Create: `tests/test_ziwei_capabilities.py` — capability 狀態與 routing 測試。
- Create: `core/紫微流日推導規則.md` — 固定公式、閏月處理、來源與限制。
- Modify: `README.md`、`CHANGELOG.md` — 公開能力與成熟度說明。

---

### Task 1: Capability Registry

**Files:**
- Create: `engine/ziwei/capabilities.py`
- Test: `tests/test_ziwei_capabilities.py`

**Interfaces:**
- Produces: `get_capability(capability_id: str) -> dict`, `can_execute(capability_id: str) -> bool`, `should_run_by_default(capability_id: str) -> bool`.
- Capability IDs: `ziwei.flow_month_palaces`, `ziwei.flow_day_palaces`, `ziwei.flow_hour_palaces`, `ziwei.transformations`, `ziwei.flowing_stars`, `ziwei.flying`.

- [ ] **Step 1: Write failing registry tests**

```python
import unittest
from engine.ziwei.capabilities import get_capability, can_execute, should_run_by_default


class ZiweiCapabilitiesTests(unittest.TestCase):
    def test_flow_month_is_stable_default(self):
        cap = get_capability("ziwei.flow_month_palaces")
        self.assertEqual(cap["implementation"], "implemented")
        self.assertEqual(cap["maturity"], "stable")
        self.assertEqual(cap["routing"], "default")
        self.assertTrue(can_execute(cap["id"]))
        self.assertTrue(should_run_by_default(cap["id"]))

    def test_flow_day_is_experimental_on_demand(self):
        cap = get_capability("ziwei.flow_day_palaces")
        self.assertEqual(cap["implementation"], "implemented")
        self.assertEqual(cap["maturity"], "experimental")
        self.assertEqual(cap["routing"], "on_demand")
        self.assertTrue(can_execute(cap["id"]))
        self.assertFalse(should_run_by_default(cap["id"]))

    def test_planned_capability_cannot_execute(self):
        self.assertFalse(can_execute("ziwei.flow_hour_palaces"))

    def test_unknown_capability_is_rejected(self):
        with self.assertRaises(KeyError):
            get_capability("ziwei.unknown")
```

- [ ] **Step 2: Run test and confirm RED**

Run: `python -m unittest -v tests/test_ziwei_capabilities.py`
Expected: import error because `engine.ziwei.capabilities` does not yet exist.

- [ ] **Step 3: Implement minimal registry**

Use immutable-at-module-load dictionaries containing `id`, `implementation`, `maturity`, `routing`, `rule_version`, `module`, and `dependencies`. Planned capabilities use `maturity: None`; `can_execute` returns true only for `implementation == "implemented"`.

- [ ] **Step 4: Run registry tests**

Run: `python -m unittest -v tests/test_ziwei_capabilities.py`
Expected: PASS.

- [ ] **Step 5: Commit**

Commit message: `feat: add ziwei capability registry`

---

### Task 2: Common Palace Mapping Helper

**Files:**
- Modify: `engine/ziwei/common.py`
- Modify: `engine/ziwei/month.py`
- Test: `tests/test_project_ziwei_month.py`
- Test: `tests/test_engine_module_layout.py`

**Interfaces:**
- Produces: `palaces_from_ming_branch(ming_branch: str) -> dict[str, str]`.
- `flow_month_palaces()` remains public and returns the same mapping as before.

- [ ] **Step 1: Add a failing helper test**

Add a test asserting `palaces_from_ming_branch("卯")` maps `命宮→卯`, `兄弟宮→寅`, `夫妻宮→丑`, `父母宮→辰`.

- [ ] **Step 2: Run targeted tests and confirm RED**

Run: `python -m unittest -v tests/test_engine_module_layout.py tests/test_project_ziwei_month.py`
Expected: only the new helper import/test fails.

- [ ] **Step 3: Implement helper and delegate month mapping to it**

Formula:

```python
ming_idx = ZHI.index(ming_branch)
return {palace: ZHI[(ming_idx - offset) % 12] for offset, palace in enumerate(PALACE_NAMES)}
```

`flow_month_palaces()` calls this helper instead of duplicating the formula.

- [ ] **Step 4: Run month + layout regression tests**

Run: `python -m unittest -v tests/test_project_ziwei_month.py tests/test_engine_module_layout.py`
Expected: all existing results unchanged.

- [ ] **Step 5: Commit**

Commit message: `refactor: share ziwei palace mapping helper`

---

### Task 3: Ziwei Flow-Day Engine

**Files:**
- Create: `engine/ziwei/day.py`
- Create: `tests/test_project_ziwei_day.py`

**Interfaces:**
- Consumes: `flow_month_ming_branch(...)`, `palaces_from_ming_branch(...)`, validators from `common.py`, registry metadata.
- Produces: `flow_day_ming_branch(...) -> str`, `flow_day_palaces(ming_branch: str) -> dict[str, str]`, `project_derived_ziwei_day(...) -> dict`.

- [ ] **Step 1: Write failing flow-day tests**

Test cases:

```python
# 公開斗君例：1993 農曆五月戌時，2017 酉年，正月流月命宮=卯。
# 初一=卯、初二=辰、十二=寅、十三回卯。
self.assertEqual(flow_day_ming_branch(5, "戌", "酉", 1, 1, False), "卯")
self.assertEqual(flow_day_ming_branch(5, "戌", "酉", 1, 2, False), "辰")
self.assertEqual(flow_day_ming_branch(5, "戌", "酉", 1, 13, False), "卯")

# 閏月沿用 Project 現有拆半規則，並跟 iztro 現行 dailyIndex 實作一致：
# day16 先把流月切到下一有效月，再以實際 lunar_day-1 推流日，不重置日數。
```

Also test day 0/31 rejection, invalid branch rejection, palace remap, and output metadata.

- [ ] **Step 2: Run test and confirm RED**

Run: `python -m unittest -v tests/test_project_ziwei_day.py`
Expected: import error because `engine.ziwei.day` does not exist.

- [ ] **Step 3: Implement flow-day formula**

Core formula:

```python
month_branch = flow_month_ming_branch(...)
day_idx = (ZHI.index(month_branch) + lunar_day - 1) % 12
return ZHI[day_idx]
```

Structured output includes:

```text
classification = Project 推導盤面
scope = 紫微流日
rule = 流月命宮起初一順行一日一宮
implementation = implemented
maturity = experimental
routing = on_demand
```

It must also include the resolved flow-month branch, flow-day branch, 12-palace mapping, input echo, leap-month note, source/validation note, and an explicit statement that daily four transformations / stars / flow-hour are not part of this PR.

- [ ] **Step 4: Add CLI**

CLI arguments mirror `month.py`: birth lunar month, birth hour branch, flow-year branch, target lunar month/day, leap flag, pretty output.

- [ ] **Step 5: Run flow-day tests**

Run: `python -m unittest -v tests/test_project_ziwei_day.py tests/test_ziwei_capabilities.py`
Expected: PASS.

- [ ] **Step 6: Commit**

Commit message: `feat: add experimental on-demand ziwei flow-day engine`

---

### Task 4: Formal Rule + External Validation Record

**Files:**
- Create: `core/紫微流日推導規則.md`
- Test: manual source comparison record in the same document.

**Interfaces:**
- Documents the exact algorithm implemented by `engine/ziwei/day.py`.

- [ ] **Step 1: Record source A — iztro**

Document that iztro's published 安星訣 states: flow day starts from the flow-month palace on lunar day 1 and advances one palace per day; its current `FunctionalAstrolabe.ts` implements `dailyIndex = fixIndex(monthlyIndex + lunarDay - 1)`.

Reference URLs:
- `https://www.iztro.com/zh_TW/learn/setup`
- `https://github.com/SylarLong/iztro/blob/main/src/astro/FunctionalAstrolabe.ts`

- [ ] **Step 2: Record source B — published secondary references**

Use at least one independent source that states the same rule, for example:
- `https://destiny.to/ubbthreads/topic/102283` (discussion quoting 慧心齋主著作)
- `https://www.yixiangqiankun.com/zh-tw/26472.htm`

Do not claim these prove all schools agree; record them as corroborating this selected Project method.

- [ ] **Step 3: Document Project-specific leap convention**

State that the existing Project flow-month engine and iztro both split a leap month after day 15 for monthly placement. For flow day, Metaphysics Lab follows the same operational order as iztro: first resolve the effective monthly palace, then add the actual lunar day offset (`lunar_day - 1`); day 16 does not reset to day 1. This convention is versioned and remains Experimental until wider cross-checking.

- [ ] **Step 4: Document non-goals and boundary**

No Gregorian→lunar conversion, no Ziwei flow-day Four Transformations, no daily flowing stars, no flow-hour. Input lunar date must come from a trusted calendar source.

- [ ] **Step 5: Commit**

Commit message: `docs: define and validate ziwei flow-day rule`

---

### Task 5: Regression + Docs + Stacked PR

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Optional modify: `docs/設計/Metaphysics-Lab-v1.2-架構設計.md` only if status wording still says flow-day is planned.

**Interfaces:**
- User-facing state: `ziwei.flow_day_palaces = implemented / experimental / on_demand`.

- [ ] **Step 1: Run full Python tests**

Run: `python -m unittest discover -v`
Expected: 0 failures / 0 errors.

- [ ] **Step 2: Run CLI smoke tests**

Run both:

```bash
python -m engine.ziwei.day --birth-lunar-month 5 --birth-hour-branch 戌 --flow-year-branch 酉 --lunar-month 1 --lunar-day 2 --pretty
python engine/project_ziwei_month.py --birth-lunar-month 5 --birth-hour-branch 戌 --flow-year-branch 酉 --lunar-month 2 --lunar-day 1 --pretty
```

Expected: first returns flow-day `辰`; second remains backward compatible.

- [ ] **Step 3: Update README / CHANGELOG**

State clearly:
- Flow day is now executable.
- It is Experimental and On-demand.
- General month/year questions do not run it by default.
- Flow hour / transformations / flowing stars / flying remain planned in separate PRs.

- [ ] **Step 4: Re-run full tests after docs/status edits**

Run: `python -m unittest discover -v`
Expected: 0 failures / 0 errors.

- [ ] **Step 5: Open stacked PR**

Head: `feature/ziwei-flow-day-capability`
Base: `refactor/v1.2-engine-layout`
Title: `feat: 新增紫微流日 on-demand capability`

PR body must include algorithm, maturity/routing state, source validation, tests, leap-month convention, and explicit non-goals.
