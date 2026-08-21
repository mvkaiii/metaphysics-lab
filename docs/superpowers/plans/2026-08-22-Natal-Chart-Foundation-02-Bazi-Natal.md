# Natal Chart Foundation 02 — Bazi Natal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 從 Workstream 01 的結構化 birth/calendar/time views 建立 Bazi Project 原生盤面：四柱、日主、藏干、十神、五行基本資料與大運核心資訊，並能偵測 civil-default 與 true-solar candidate 是否造成 material conflict。

**Architecture:** 新增 `engine/bazi/natal_models.py` 與 `engine/bazi/natal.py`；四柱計算重用現有 `engine/bazi/calendar.py` 的固定干支與 23:00 baseline，不把流運輸出分類冒充本命；藏干／十神／大運使用 versioned natal profile。True-solar candidate 只比較，不自動覆蓋 default。

**Tech Stack:** Python 3.9-compatible syntax、existing `engine/bazi/calendar.py`、stdlib dataclasses/enum/datetime；`lunar-python==1.4.8` 只作 secondary qualification oracle，不成為本 workstream 新增的 Bazi runtime decision source。

**Spec:** `docs/superpowers/specs/2026-08-22-Natal-Chart-Foundation-設計.md`

## Global Constraints

- Bazi default effective time = normalized civil time；23:00 day boundary沿用現有 Bazi baseline。
- True-solar view是 qualification candidate；只有 material pillar difference 才產生 `TIME_PROFILE_CONFLICT`。
- Builder 不自動宣稱身強弱、格局、喜用神、忌神或吉凶分數。
- 所有 deterministic facts 標 `Project 原生盤面`，不是 `Project 推導盤面`。
- Calendar `boundary_conflict` 對受影響欄位 fail closed；`out_of_validated_range` 只能產 unqualified candidate。

---

### Task 1: Define Bazi natal profile and immutable models

**Files:**
- Create: `engine/bazi/natal_models.py`
- Create: `tests/test_bazi_natal_models.py`
- Create: `engine/bazi/capabilities.py`
- Create: `tests/test_bazi_natal_capabilities.py`

**Interfaces:**
- Produces `BaziNatalProfile(profile_id='bazi-natal-project-v1', rule_version='1.0-exp', effective_time_basis='normalized_civil', day_boundary='23:00', decadal_rule='three-days-one-year-v1')`
- Produces `Pillar(stem, branch)` with `.text`
- Produces `HiddenStem(stem, weight_rank)`
- Produces `PillarDetail(pillar, hidden_stems, stem_ten_god, hidden_ten_gods)`
- Produces `BaziDecadalPeriod(index, pillar, start_age_years, end_age_years, start_datetime, end_datetime)`
- Produces `BaziNatalChart(profile, effective_datetime, pillars, day_master, pillar_details, element_counts, decadal_direction, decadal_start, decadal_periods, validation, provenance)`
- Capability `bazi.natal_chart = implemented / experimental / on_demand / 1.0-exp`

- [ ] **Step 1: Write failing model/capability tests**

```python
def test_bazi_natal_profile_is_not_stable_by_default():
    cap = get_capability('bazi.natal_chart')
    assert (cap['implementation'], cap['maturity'], cap['routing']) == ('implemented', 'experimental', 'on_demand')


def test_pillar_text_is_deterministic():
    assert Pillar('甲', '子').text == '甲子'
```

- [ ] **Step 2: Run and verify failure**

```bash
python -m unittest tests.test_bazi_natal_models tests.test_bazi_natal_capabilities -v
```

- [ ] **Step 3: Implement frozen dataclasses and validation**

Ten stems/branches must be validated against the same canonical sequences used by `engine/bazi/calendar.py`. `element_counts` is a mapping of `木火土金水` to non-negative integers and is explicitly labeled raw/basic counts, not strength scoring.

- [ ] **Step 4: Run focused tests**

```bash
python -m unittest tests.test_bazi_natal_models tests.test_bazi_natal_capabilities -v
```

- [ ] **Step 5: Commit**

```bash
git add engine/bazi/natal_models.py engine/bazi/capabilities.py tests/test_bazi_natal_models.py tests/test_bazi_natal_capabilities.py
git commit -m "feat: define Bazi natal schema"
```

---

### Task 2: Build four pillars from the Bazi effective-time profile

**Files:**
- Create: `engine/bazi/natal.py`
- Create: `tests/test_bazi_natal.py`

**Interfaces:**
- Consumes `CalendarContext`, `BirthTimeViews`, `BaziNatalProfile`
- Produces `build_bazi_natal(calendar: CalendarContext, time_views: BirthTimeViews, sex: Sex, profile=BaziNatalProfile(...)) -> BaziNatalChart`
- Internal `select_bazi_effective_datetime(time_views, profile) -> datetime`

- [ ] **Step 1: Write locked four-pillar regression tests**

Use at least:

```text
1984-03-13 19:20 Asia/Taipei
2026-08-20 17:12 Asia/Taipei
2026-08-20 23:30 Asia/Taipei
```

For each, compare `build_bazi_natal(...).pillars` against existing `engine.bazi.calendar.bazi_pillars()` on the same normalized civil datetime.

- [ ] **Step 2: Run and verify failure**

```bash
python -m unittest tests.test_bazi_natal -v
```

- [ ] **Step 3: Implement profile-based effective time selection**

For v1 default:

```python
if profile.effective_time_basis != 'normalized_civil':
    raise BaziNatalError('unsupported_bazi_time_profile', ...)
effective = time_views.normalized_civil.local_datetime
```

Call existing `bazi_pillars(effective)` and split each two-character value into `Pillar`.

- [ ] **Step 4: Preserve Calendar validation**

If `calendar.validation.overall_status == 'boundary_conflict'`, raise `calendar_boundary_conflict`. If `out_of_validated_range`, chart may be materialized only with validation `unqualified_candidate`; do not mark `validated`.

- [ ] **Step 5: Run focused + existing Bazi regression**

```bash
python -m unittest tests.test_bazi_natal tests.test_project_bazi_calendar -v
```

- [ ] **Step 6: Commit**

```bash
git add engine/bazi/natal.py tests/test_bazi_natal.py
git commit -m "feat: build Bazi natal pillars"
```

---

### Task 3: Add hidden stems, ten gods, and element facts

**Files:**
- Modify: `engine/bazi/natal.py`
- Modify: `engine/bazi/natal_models.py`
- Modify: `tests/test_bazi_natal.py`

**Interfaces:**
- Produces `hidden_stems(branch: str) -> tuple[str, ...]`
- Reuses `engine.bazi.calendar.ten_god(day_master, target_stem)`
- Produces `basic_element_counts(pillars, hidden_stems_by_pillar) -> Mapping[str, int]`

- [ ] **Step 1: Write exact hidden-stem table tests**

The v1 table is fixed:

```text
子 癸
丑 己癸辛
寅 甲丙戊
卯 乙
辰 戊乙癸
巳 丙戊庚
午 丁己
未 己丁乙
申 庚壬戊
酉 辛
戌 戊辛丁
亥 壬甲
```

Test all 12 branches, not samples only.

- [ ] **Step 2: Write ten-god integrity test**

For every pillar stem and every hidden stem, assert stored ten-god equals `ten_god(chart.day_master, stem)`.

- [ ] **Step 3: Run and verify failure**

```bash
python -m unittest tests.test_bazi_natal -v
```

- [ ] **Step 4: Implement table-driven facts**

Keep hidden stems as ordered tuples; do not invent percentage weights in v1. `weight_rank` is 1..N by table order only.

`basic_element_counts` counts the eight visible stem/branch primary elements plus hidden stems in a separately named structure if needed; do not collapse this into strength judgement. If both visible and hidden totals are exported, name them `visible_counts` and `hidden_stem_counts`.

- [ ] **Step 5: Run tests**

```bash
python -m unittest tests.test_bazi_natal tests.test_project_bazi_calendar -v
```

- [ ] **Step 6: Commit**

```bash
git add engine/bazi/natal.py engine/bazi/natal_models.py tests/test_bazi_natal.py
git commit -m "feat: add Bazi natal hidden stems and ten gods"
```

---

### Task 4: Implement civil-vs-true-solar Bazi comparison

**Files:**
- Modify: `engine/bazi/natal.py`
- Create: `tests/test_bazi_time_profile_comparison.py`

**Interfaces:**
- Produces `BaziTimeComparison(status, default_pillars, true_solar_pillars, affected_components, severity)`
- Produces `compare_bazi_time_views(time_views: BirthTimeViews) -> BaziTimeComparison`

- [ ] **Step 1: Write EQUIVALENT test**

Taipei 1984-03-13 19:20: if both civil and true-solar candidate produce the same four pillars, assert:

```text
status = EQUIVALENT
affected_components = ()
severity = INFO
```

- [ ] **Step 2: Write material conflict synthetic test**

Construct a `BirthTimeViews` where normalized civil is `19:02` and true-solar candidate `18:56` on a fixed date. Assert only the hour pillar differs and result is:

```text
status = CONFLICT
error_code = bazi_time_profile_conflict
severity = BLOCKING
```

If a synthetic vector crosses 23:00/date boundary and changes day/hour pillars, assert both components are listed.

- [ ] **Step 3: Implement comparison without changing default chart**

Compute pillars independently for `normalized_civil` and `true_solar`; compare `(year, month, day, hour)` tuples. Never mutate the default `BaziNatalChart`.

- [ ] **Step 4: Run tests**

```bash
python -m unittest tests.test_bazi_time_profile_comparison tests.test_bazi_natal -v
```

- [ ] **Step 5: Commit**

```bash
git add engine/bazi/natal.py tests/test_bazi_time_profile_comparison.py
git commit -m "feat: compare Bazi natal time profiles"
```

---

### Task 5: Implement Da Yun direction and start-time profile

**Files:**
- Modify: `engine/bazi/natal.py`
- Modify: `engine/bazi/natal_models.py`
- Create: `tests/test_bazi_decadal_luck.py`

**Interfaces:**
- Produces `decadal_direction(year_stem: str, sex: Sex) -> str` returning `forward` or `reverse`
- Produces `decadal_start_delta(birth_dt: datetime, direction: str) -> timedelta`
- Produces `build_decadal_periods(month_pillar: Pillar, birth_dt: datetime, direction: str, count: int = 10) -> tuple[BaziDecadalPeriod, ...]`

- [ ] **Step 1: Write yin/yang direction matrix test**

Rule profile `three-days-one-year-v1`:

```text
陽年男、陰年女 → forward
陰年男、陽年女 → reverse
```

Yang stems: `甲丙戊庚壬`; Yin stems: `乙丁己辛癸`.

Test all 10 stems × both sexes.

- [ ] **Step 2: Write solar-term interval tests**

Reuse `engine.bazi.calendar.solar_term_time()` and the existing 12 `JIE` boundaries. For forward, measure birth instant → next Jie; for reverse, previous Jie → birth instant.

Fixed conversion:

```text
3 civil days of interval = 1 tropical year of luck age
1 interval day = 4 luck months
2 interval hours = 10 luck days
```

Implement mathematically as:

```python
start_age_years = interval.total_seconds() / (3 * 86400)
start_datetime = birth_dt + timedelta(days=start_age_years * 365.2425)
```

Store raw interval seconds and derived decimal start age in provenance so later profile revisions remain auditable.

- [ ] **Step 3: Write month-pillar sequence test**

The first Da Yun pillar is one sexagenary step after natal month pillar for forward, one step before for reverse. Each next period advances the same direction. Generate exactly 10 periods for v1.

- [ ] **Step 4: Implement direction/start/sequence**

Do not round the start instant to whole years. Presentation rounding belongs in exporter/UI.

- [ ] **Step 5: Run focused tests**

```bash
python -m unittest tests.test_bazi_decadal_luck -v
```

- [ ] **Step 6: Commit**

```bash
git add engine/bazi/natal.py engine/bazi/natal_models.py tests/test_bazi_decadal_luck.py
git commit -m "feat: add Bazi decadal luck core"
```

---

### Task 6: Add Bazi reference qualification and aggregate evidence

**Files:**
- Create: `tools/qualify_bazi_natal.py`
- Create: `qualification/bazi/natal/public-lunar-python-1.4.8.json`
- Create: `qualification/bazi/natal/private-summary.json`
- Create: `tests/test_bazi_natal_qualification.py`

**Interfaces:**
- Public tool compares Project output with pinned `lunar-python==1.4.8` for public synthetic vectors.
- Private summary schema contains only `case_id`, source digest, engine/profile versions, counts, field statuses; no raw birth datetime/name/address.

- [ ] **Step 1: Create public vector matrix**

At minimum cover:

```text
normal daytime
22:59 / 23:00 / 23:59 / 00:00
before/after 立春
before/after one additional Jie boundary
male/female direction
civil-vs-true-solar same pillars
civil-vs-true-solar changed hour pillar
```

- [ ] **Step 2: Compare exact fields**

Required fields:

```text
four pillars
day master
hidden stems
ten gods
decadal direction
decadal start age
decadal pillar sequence
```

If `lunar-python` uses a different Da Yun start convention, record that field as `CONFLICT/profile_difference`; do not change Project algorithm merely to force a match.

- [ ] **Step 3: Write privacy tests**

Reject qualification JSON containing keys `name`, `full_address`, `birth_datetime`, `raw_chart`, `raw_payload`.

- [ ] **Step 4: Run focused + Bazi regression**

```bash
python -m unittest \
  tests.test_bazi_natal_models \
  tests.test_bazi_natal_capabilities \
  tests.test_bazi_natal \
  tests.test_bazi_time_profile_comparison \
  tests.test_bazi_decadal_luck \
  tests.test_bazi_natal_qualification \
  tests.test_project_bazi_calendar -v
```

- [ ] **Step 5: Python 3.9 syntax gate**

```bash
python - <<'PY'
import ast
from pathlib import Path
for path in list(Path('engine/bazi').rglob('*.py')) + list(Path('tests').glob('test_bazi*.py')):
    ast.parse(path.read_text(encoding='utf-8'), feature_version=(3, 9))
print('PYTHON39_BAZI_NATAL_PASS')
PY
```

- [ ] **Step 6: Commit evidence scaffolding**

```bash
git add tools/qualify_bazi_natal.py qualification/bazi/natal tests/test_bazi_natal_qualification.py
git commit -m "test: qualify Bazi natal engine"
```

Workstream 02 acceptance requires Project four-pillar core to match locked internal baseline and all profile differences to remain explicit rather than silently reconciled.