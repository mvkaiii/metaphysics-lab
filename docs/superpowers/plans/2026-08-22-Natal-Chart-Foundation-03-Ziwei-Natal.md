# Natal Chart Foundation 03 — Ziwei Natal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 從 Workstream 01 的 birth/calendar/time views 建立 Ziwei Project 原生盤面：命身宮、十二宮宮干、五行局、核心星曜與亮度、命主身主、生年四化、本命48飛化與大限，並對 pinned iztro / private Astralium evidence 做 qualification。

**Architecture:** 新增 versioned Ziwei natal profile與純 Python deterministic rule tables。Natal Builder只負責本命骨架、安星、宮干與大限；生年四化與飛化重用既有 Phase 2A stable Transformation/Flying Core。Public iztro `814b77e6371e1050cac31bbf674db3c3138fcfde` 作 development/qualification oracle，不進 runtime。

**Tech Stack:** Python 3.9-compatible syntax、existing `engine/ziwei/common.py` / `basis.py` / `transformations.py` / `flying.py` / `composition.py`、pinned iztro 2.6.0 revision for qualification only、Workstream 01 true-solar profile。

**Spec:** `docs/superpowers/specs/2026-08-22-Natal-Chart-Foundation-設計.md`

## Global Constraints

- Ziwei effective time使用 Workstream 01 versioned true-solar view；不得修改 Calendar Resolver。
- v1 profile初始 `implemented / experimental / on_demand / 1.0-exp`。
- 不宣稱此 profile 為唯一紫微流派。
- Star catalog 至少包含十四主星 + `左輔 右弼 文昌 文曲` + 主要輔煞 `天魁 天鉞 祿存 擎羊 陀羅 火星 鈴星 天馬`。
- Transformation-required stars 必須全部唯一定位；缺一顆即 fail closed 四化／飛化。
- Brightness由versioned table提供，不由LLM猜。
- Natal Builder不複製四化表；直接重用 `metaphysics-lab-common-v1` Transformation Core。
- `ziwei.flowing_stars` 保持 planned/non-executable。

---

### Task 1: Define Ziwei natal profile, models, and capability state

**Files:**
- Create: `engine/ziwei/natal_models.py`
- Create: `engine/ziwei/natal_profiles.py`
- Modify: `engine/ziwei/capabilities.py`
- Create: `tests/test_ziwei_natal_models.py`
- Create: `tests/test_ziwei_natal_capabilities.py`

**Interfaces:**
- Produces `ZiweiNatalProfile(profile_id='ziwei-natal-true-solar-common-v1', rule_version='1.0-exp', time_basis='true_solar', star_catalog='ziwei-core-stars-v1', brightness_profile='ziwei-brightness-common-v1', decadal_profile='ziwei-decadal-common-v1')`
- Produces `ZiweiPalaceRecord(name, branch, heavenly_stem, stem_branch)`
- Produces `ZiweiStarRecord(star, palace, branch, category, brightness, catalog_profile)`
- Produces `ZiweiDecadalPeriod(index, age_start, age_end, palace, stem_branch, direction)`
- Produces `ZiweiNatalChart(...)`
- Adds `ziwei.natal_chart = implemented / experimental / on_demand / 1.0-exp`

- [ ] **Step 1: Write capability guard tests**

```python
def test_ziwei_natal_starts_experimental_without_promoting_phase2c():
    cap = get_capability('ziwei.natal_chart')
    assert (cap['implementation'], cap['maturity'], cap['routing'], cap['rule_version']) == (
        'implemented', 'experimental', 'on_demand', '1.0-exp'
    )
    assert get_capability('ziwei.flowing_stars')['implementation'] == 'planned'
```

- [ ] **Step 2: Write model validation tests**

Require exactly 12 unique canonical palace names and reject duplicate star identity inside a single natal chart.

- [ ] **Step 3: Run and verify failure**

```bash
python -m unittest tests.test_ziwei_natal_models tests.test_ziwei_natal_capabilities -v
```

- [ ] **Step 4: Implement frozen models/profile**

Use `PALACE_NAMES` and `ZHI` from `engine.ziwei.common`; do not create duplicate canonical sequences.

- [ ] **Step 5: Run focused tests**

```bash
python -m unittest tests.test_ziwei_natal_models tests.test_ziwei_natal_capabilities -v
```

- [ ] **Step 6: Commit**

```bash
git add engine/ziwei/natal_models.py engine/ziwei/natal_profiles.py engine/ziwei/capabilities.py tests/test_ziwei_natal_models.py tests/test_ziwei_natal_capabilities.py
git commit -m "feat: define Ziwei natal schema"
```

---

### Task 2: Implement Ziwei effective-time adapter and lunar birth basis

**Files:**
- Create: `engine/ziwei/natal_time.py`
- Create: `tests/test_ziwei_natal_time.py`

**Interfaces:**
- Consumes `CalendarContext`, `BirthTimeViews`, `ZiweiNatalProfile`
- Produces `ZiweiBirthBasis(reported_datetime, normalized_datetime, true_solar_datetime, effective_datetime, effective_hour_branch, lunar_year, lunar_month, lunar_day, is_leap_month, validation, provenance)`
- Produces `build_ziwei_birth_basis(calendar, time_views, profile) -> ZiweiBirthBasis`

- [ ] **Step 1: Write Taipei true-solar preservation test**

For 1984-03-13 19:20 Taipei, assert reported civil remains 19:20, true-solar view is separately stored, and effective branch is derived from true-solar view.

- [ ] **Step 2: Write cross-boundary test**

Create a synthetic true-solar view crossing an hour branch and assert `ziwei_time_profile_conflict` metadata is material; do not overwrite reported time.

- [ ] **Step 3: Write calendar validation tests**

`boundary_conflict` → fail closed. `out_of_validated_range` → explicit unqualified candidate only.

- [ ] **Step 4: Implement adapter**

When true-solar correction changes civil date, resolve the effective Gregorian/lunar date through Calendar Resolver using the corrected local datetime and the same IANA timezone. Do not manually add/subtract lunar dates.

- [ ] **Step 5: Run tests**

```bash
python -m unittest tests.test_ziwei_natal_time tests.test_birth_time_views -v
```

- [ ] **Step 6: Commit**

```bash
git add engine/ziwei/natal_time.py tests/test_ziwei_natal_time.py
git commit -m "feat: add Ziwei natal time basis"
```

---

### Task 3: Implement Ming/Body palace, twelve-palace skeleton, palace stems, and five-element bureau

**Files:**
- Create: `engine/ziwei/natal_palaces.py`
- Create: `tests/test_ziwei_natal_palaces.py`
- Create: `qualification/ziwei/natal/public-iztro-palace-vectors.json`

**Interfaces:**
- Produces `resolve_ming_body_branches(lunar_month: int, hour_branch: str) -> tuple[str, str]`
- Reuses `palaces_from_ming_branch(ming_branch)`
- Produces `resolve_palace_stems(birth_year_stem: str, ming_branch: str) -> tuple[ZiweiPalaceRecord, ...]`
- Produces `resolve_five_element_bureau(ming_palace_stem: str, ming_palace_branch: str) -> str`

- [ ] **Step 1: Freeze public oracle vectors from pinned iztro revision**

Generate a committed public fixture covering all 12 lunar months × all 12 hour branches for Ming/Body branch outputs, using only synthetic/public data. Store pinned revision and digest in fixture metadata.

- [ ] **Step 2: Write vector tests before implementation**

```python
for case in fixture['cases']:
    assert resolve_ming_body_branches(case['lunar_month'], case['hour_branch']) == (
        case['ming_branch'], case['body_branch']
    )
```

- [ ] **Step 3: Implement Ming/Body algorithm as index math**

Use `ZHI` and an explicit 寅-base month index. Do not call Node/iztro at runtime. Keep the exact index formula in `natal_palaces.py` with comment referencing the pinned qualification revision.

- [ ] **Step 4: Freeze and implement palace-stem table/profile**

Generate public vectors for all 10 birth-year stems. Implement palace stems using a fixed Five-Tigers style table/profile extracted and reviewed from the pinned public source; store the resulting canonical mapping in Python constants, not dynamic JS calls.

- [ ] **Step 5: Freeze and implement five-element bureau table**

Test every legal Ming palace stem-branch combination that appears in public vectors. Bureau values allowed: `水二局`, `木三局`, `金四局`, `土五局`, `火六局`.

- [ ] **Step 6: Run focused tests**

```bash
python -m unittest tests.test_ziwei_natal_palaces -v
```

- [ ] **Step 7: Commit**

```bash
git add engine/ziwei/natal_palaces.py tests/test_ziwei_natal_palaces.py qualification/ziwei/natal/public-iztro-palace-vectors.json
git commit -m "feat: add Ziwei natal palace skeleton"
```

---

### Task 4: Implement 14 major-star placement with explicit rule tables

**Files:**
- Create: `engine/ziwei/star_catalog.py`
- Create: `engine/ziwei/natal_stars.py`
- Create: `tests/test_ziwei_natal_stars.py`
- Create: `qualification/ziwei/natal/public-iztro-major-star-vectors.json`

**Interfaces:**
- Produces `MAJOR_STARS = ('紫微','天機','太陽','武曲','天同','廉貞','天府','太陰','貪狼','巨門','天相','天梁','七殺','破軍')`
- Produces `place_major_stars(lunar_day: int, bureau: str) -> tuple[tuple[str, str], ...]` where each tuple is `(star, branch)`
- Produces `materialize_star_records(placements, palaces, profile) -> tuple[ZiweiStarRecord, ...]`

- [ ] **Step 1: Generate public fixture from pinned iztro**

Cover lunar days 1..30 across all five bureau values. Fixture must contain only public synthetic inputs and 14-star branch outputs.

- [ ] **Step 2: Write completeness tests**

Every case must return exactly 14 unique stars, set-equal to `MAJOR_STARS`, and every branch must be one of `ZHI`.

- [ ] **Step 3: Implement Ziwei/Tianfu anchor placement and derived star sequences**

Encode the reviewed deterministic tables/index offsets from pinned public source in Python. Runtime function must depend only on `lunar_day` and `bureau`; it must not depend on Astralium or Node.

- [ ] **Step 4: Add invariant tests**

For every fixture case:

```text
14 unique stars
no missing branch
same input → same tuple order
no mutable global state
```

- [ ] **Step 5: Run tests**

```bash
python -m unittest tests.test_ziwei_natal_stars -v
```

- [ ] **Step 6: Commit**

```bash
git add engine/ziwei/star_catalog.py engine/ziwei/natal_stars.py tests/test_ziwei_natal_stars.py qualification/ziwei/natal/public-iztro-major-star-vectors.json
git commit -m "feat: place Ziwei major stars"
```

---

### Task 5: Add transformation-required stars and selected auxiliary/malefic catalog

**Files:**
- Modify: `engine/ziwei/star_catalog.py`
- Modify: `engine/ziwei/natal_stars.py`
- Modify: `tests/test_ziwei_natal_stars.py`
- Create: `qualification/ziwei/natal/public-iztro-aux-star-vectors.json`

**Interfaces:**
- Required transformation extras: `左輔`, `右弼`, `文昌`, `文曲`
- Selected v1 auxiliary/malefic: `天魁`, `天鉞`, `祿存`, `擎羊`, `陀羅`, `火星`, `鈴星`, `天馬`
- Produces `place_auxiliary_stars(birth_basis, birth_year_stem, profile) -> tuple[tuple[str, str], ...]`

- [ ] **Step 1: Add catalog contract test**

Compute union of all stars in `engine.ziwei.transformation_profiles.PROFILE` and assert it is a subset of the natal star catalog.

- [ ] **Step 2: Generate pinned public vectors**

Cover all 10 birth-year stems, all 12 birth hour branches, all 12 lunar months where the selected rules depend on those fields.

- [ ] **Step 3: Implement each selected star family as focused pure function**

Examples of required signatures:

```python
def place_left_right_assistants(lunar_month: int) -> dict[str, str]: ...
def place_chang_qu(hour_branch: str) -> dict[str, str]: ...
def place_kui_yue(year_stem: str) -> dict[str, str]: ...
def place_lucun_yang_tuo(year_stem: str) -> dict[str, str]: ...
def place_fire_bell(year_branch: str, hour_branch: str) -> dict[str, str]: ...
def place_tianma(year_branch: str) -> dict[str, str]: ...
```

Each function gets its own fixture cases; do not create one 500-line `place_everything()` function.

- [ ] **Step 4: Add fail-closed test for missing transformation star**

Remove one required star from a synthetic catalog and assert natal integration raises `missing_transformation_star_location` before calling Flying Core.

- [ ] **Step 5: Run tests**

```bash
python -m unittest tests.test_ziwei_natal_stars -v
```

- [ ] **Step 6: Commit**

```bash
git add engine/ziwei/star_catalog.py engine/ziwei/natal_stars.py tests/test_ziwei_natal_stars.py qualification/ziwei/natal/public-iztro-aux-star-vectors.json
git commit -m "feat: add Ziwei core auxiliary stars"
```

---

### Task 6: Add versioned star brightness profile

**Files:**
- Create: `engine/ziwei/brightness_profiles.py`
- Create: `tests/test_ziwei_natal_brightness.py`
- Create: `qualification/ziwei/natal/public-iztro-brightness-vectors.json`

**Interfaces:**
- Produces `BRIGHTNESS_PROFILE_ID = 'ziwei-brightness-common-v1'`
- Produces `brightness_for(star: str, branch: str, profile_id=...) -> str | None`
- Allowed labels: `廟`, `旺`, `得`, `利`, `平`, `不`, `陷`; `None` when the v1 profile intentionally does not define brightness for that selected star.

- [ ] **Step 1: Freeze public brightness vectors**

Extract brightness for all 14 major stars across 12 branches from pinned public source; include the four transformation extras only if the source defines them consistently.

- [ ] **Step 2: Write full table test**

Test every committed `(star, branch)` pair, not samples.

- [ ] **Step 3: Implement immutable mapping**

Unknown star/branch is validation error; a known star with intentionally undefined brightness returns `None` only if catalog metadata says `brightness_optional=True`.

- [ ] **Step 4: Run tests and commit**

```bash
python -m unittest tests.test_ziwei_natal_brightness -v
git add engine/ziwei/brightness_profiles.py tests/test_ziwei_natal_brightness.py qualification/ziwei/natal/public-iztro-brightness-vectors.json
git commit -m "feat: add Ziwei brightness profile"
```

---

### Task 7: Implement Life Master, Body Master, and decadal cycles

**Files:**
- Create: `engine/ziwei/natal_decadal.py`
- Create: `tests/test_ziwei_natal_decadal.py`
- Create: `qualification/ziwei/natal/public-iztro-decadal-vectors.json`

**Interfaces:**
- Produces `resolve_life_body_master(ming_branch: str, birth_year_branch: str) -> tuple[str, str]`
- Produces `resolve_decadal_direction(birth_year_stem: str, sex: Sex) -> str`
- Produces `build_ziwei_decadal_periods(palaces, bureau, direction, count=12) -> tuple[ZiweiDecadalPeriod, ...]`

- [ ] **Step 1: Freeze public master/decadal vectors**

Cover all 12 Ming branches and all 12 birth-year branches for masters; all 10 stems × both sexes for direction; all five bureau values for age-start basis.

- [ ] **Step 2: Write direction tests**

Use the exact reviewed pinned-public profile; encode yin/yang/sex direction rule as a table-driven function and freeze output for all 20 stem/sex combinations.

- [ ] **Step 3: Write decadal period shape tests**

Exactly 12 periods, non-overlapping age ranges, canonical palace names, and `stem_branch` matching the natal palace record.

- [ ] **Step 4: Implement masters/direction/periods from fixed tables**

Do not derive Da Xian from Bazi Da Yun functions; the two systems remain separate.

- [ ] **Step 5: Run tests and commit**

```bash
python -m unittest tests.test_ziwei_natal_decadal -v
git add engine/ziwei/natal_decadal.py tests/test_ziwei_natal_decadal.py qualification/ziwei/natal/public-iztro-decadal-vectors.json
git commit -m "feat: add Ziwei natal decadal cycles"
```

---

### Task 8: Assemble Ziwei Natal Builder and reuse Phase 2A Transformation/Flying Core

**Files:**
- Create: `engine/ziwei/natal.py`
- Modify: `engine/ziwei/__init__.py`
- Create: `tests/test_ziwei_natal_integration.py`

**Interfaces:**
- Produces `build_ziwei_natal(birth_basis, sex, profile=...) -> ZiweiNatalChart`
- Reuses `build_star_location_index()` and `build_palace_stem_index()` from `basis.py`
- Reuses existing Transformation/Flying/Composition APIs to produce birth-year transformations and a 48-edge `NatalFlyingGraph`

- [ ] **Step 1: Write end-to-end synthetic builder test**

Assert:

```text
12 palace records
all 14 major stars unique
all transformation-required stars present
birth transformations = 4
natal flying edges = 48
12 decadal periods
classification = Project 原生盤面
maturity = experimental
```

- [ ] **Step 2: Write chart-identity consistency test**

`StarLocationIndex`, `PalaceStemIndex`, `NatalFlyingGraph`, birth-year layer must all share one `ChartIdentity`; mismatch must fail closed.

- [ ] **Step 3: Implement assembly without copying Phase 2A rules**

Build star/palace indexes from Natal Builder records, then invoke existing core. No local 四化 table in `natal.py`.

- [ ] **Step 4: Run Phase 2A/2B compatibility suites**

```bash
python -m unittest \
  tests.test_ziwei_natal_integration \
  tests.test_ziwei_phase2a_capabilities \
  tests.test_ziwei_phase2b_capabilities \
  tests.test_ziwei_composition \
  tests.test_ziwei_fine_cycle_integration -v
```

- [ ] **Step 5: Commit**

```bash
git add engine/ziwei/natal.py engine/ziwei/__init__.py tests/test_ziwei_natal_integration.py
git commit -m "feat: assemble Ziwei natal chart"
```

---

### Task 9: Add public/private Ziwei natal qualification and privacy gates

**Files:**
- Create: `tools/qualify_ziwei_natal_public.py`
- Create: `qualification/ziwei/natal/public-iztro-814b77e6.json`
- Create: `qualification/ziwei/natal/private-astralium-summary.json`
- Create: `tests/test_ziwei_natal_qualification.py`
- Create: `tests/test_ziwei_natal_privacy.py`

**Interfaces:**
- Public qualification compares synthetic birth cases against pinned iztro revision.
- Private Astralium summary stores aggregate counts/digest only.

- [ ] **Step 1: Define required qualification fields**

```text
lunar birth
true-solar adjustment/result
hour branch
Ming palace
Body palace
five-element bureau
12 palace branches
12 palace stems
14 major stars
transformation-required stars
selected auxiliaries/malefics
brightness
Life Master / Body Master
birth transformations
48 natal flying edges
12 decadal periods
```

- [ ] **Step 2: Build boundary matrix**

At minimum public synthetic cases cover different longitude/timezones via Workstream 01 fixtures, true-solar crossing hour, leap lunar month, all five bureau, all ten birth-year stems, both sexes.

- [ ] **Step 3: Add private summary privacy assertions**

Reject keys `name`, `birth_datetime`, `full_address`, `raw_chart`, `raw_payload`, and any 12-palace raw private payload object. Allow `case_id`, digest, counts, versions, field-status totals.

- [ ] **Step 4: Run focused Ziwei suite**

```bash
python -m unittest \
  tests.test_ziwei_natal_models \
  tests.test_ziwei_natal_capabilities \
  tests.test_ziwei_natal_time \
  tests.test_ziwei_natal_palaces \
  tests.test_ziwei_natal_stars \
  tests.test_ziwei_natal_brightness \
  tests.test_ziwei_natal_decadal \
  tests.test_ziwei_natal_integration \
  tests.test_ziwei_natal_qualification \
  tests.test_ziwei_natal_privacy -v
```

- [ ] **Step 5: Run all existing Ziwei regressions**

```bash
python -m unittest discover -s tests -p 'test_ziwei*.py' -v
```

- [ ] **Step 6: Python 3.9 syntax + scope gate**

```bash
python - <<'PY'
import ast
from pathlib import Path
for path in list(Path('engine/ziwei').rglob('*.py')) + list(Path('tests').glob('test_ziwei*.py')):
    ast.parse(path.read_text(encoding='utf-8'), feature_version=(3, 9))
print('PYTHON39_ZIWEI_NATAL_PASS')
PY
```

Assert `get_capability('ziwei.flowing_stars')['implementation'] == 'planned'`.

- [ ] **Step 7: Commit qualification scaffolding**

```bash
git add tools/qualify_ziwei_natal_public.py qualification/ziwei/natal tests/test_ziwei_natal_qualification.py tests/test_ziwei_natal_privacy.py
git commit -m "test: qualify Ziwei natal engine"
```

Workstream 03 acceptance requires exact internal invariants and explicit external qualification status. If Astralium evidence is insufficient, keep `ziwei.natal_chart` Experimental; do not fabricate PASS or promote Stable.