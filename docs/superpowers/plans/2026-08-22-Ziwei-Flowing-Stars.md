# Ziwei Flowing Stars v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 實作 `ziwei.flowing_stars`：對已解析的大限／流年／流月／流日／流時干支來源，產生 deterministic、可版本化、可qualification 的動態流曜地支位置，並以獨立 layer 與既有四化／飛化安全 join。

**Architecture:** 採 Pure Placement Core + Scope Source Adapters + Independent `FlowingStarLayer`。月／日／時直接重用 Phase 2B `ResolvedCycleStem`；大限直接重用 Phase 2C0 `ZiweiDecadalPeriod.stem_branch`；流年使用 Calendar-neutral lunar-year sexagenary helper。Pure core 只處理 scope + stem + branch，不查日期、不重算時間、不修改 Stable Phase 2A `CycleTransformationLayer`。

**Tech Stack:** Python 3.9-compatible syntax、`unittest`、existing `engine/calendar/sexagenary.py`、`engine/ziwei/models.py`、Phase 2B fine-cycle resolver、Phase 2C0 natal models、pinned `SylarLong/iztro` v2.6.0 revision `814b77e6371e1050cac31bbf674db3c3138fcfde` 僅作 qualification oracle。

**Spec:** `docs/superpowers/specs/2026-08-22-Ziwei-Flowing-Stars-設計.md`

## Global Constraints

- Execution branch must start from the approved `design/ziwei-flowing-stars` head; do not implement directly on `main` or on the design branch.
- `ziwei.flowing_stars` final state is `implemented / experimental / on_demand / 1.0-exp`; never promote to Stable in this plan.
- Project profile ID is `ziwei-flowing-stars-common-v1`; iztro is qualification target only, not Project source classification.
- Canonical location is Earthly Branch (`target_branch`), never a palace name.
- Supported scopes are exactly `decadal`, `yearly`, `monthly`, `daily`, `hourly`.
- Core stars are exactly `天魁 天鉞 文昌 文曲 祿存 擎羊 陀羅 天馬 紅鸞 天喜`; `yearly` additionally includes `年解`.
- Non-yearly output count is exactly 10; yearly output count is exactly 11.
- Do not add 歲前十二神、將前十二神、博士十二神、長生十二神、小限流曜、大量雜曜、流曜亮度、吉凶 scoring or AI interpretation.
- Do not modify Stable `engine/ziwei/transformations.py`, `engine/ziwei/flying.py`, or `CycleTransformationLayer` semantics unless a RED test proves a design defect and the design is explicitly reopened.
- Monthly/daily/hourly adapters must reuse Phase 2B `ResolvedCycleStem` without recalculating stem/branch or boundary policy.
- Decadal adapter must reuse `ZiweiDecadalPeriod.stem_branch`; do not recompute decadal stems from birth data.
- Yearly adapter uses lunar-year stem + branch; do not reuse Bazi Li-Chun year policy.
- Formal `FlowingStarSource` accepts only valid 60-sexagenary stem/branch pairs; pure formula qualification may exercise all 10×12 stem/branch combinations.
- `boundary_conflict` and `out_of_validated_range` fail closed; `boundary_caution` may build a layer but must preserve caution metadata.
- Runtime Python must not import Node/npm, shell out to iztro, or call external services.
- Python production syntax must compile on Python 3.9. Do not use PEP 604 `X | None` or builtin generic annotations requiring 3.10+.
- Private Astralium flowing-star qualification starts `PENDING`; do not reuse Natal private PASS as flowing-star evidence.
- `VERSION.md`, Git tag, and GitHub Release remain unchanged during Unreleased Phase 2C.
- Temporary validation workflows/branches/PRs are validation-only and MUST NEVER MERGE.
- Every task follows RED → inspect expected failure → minimal GREEN → focused regression → commit.

---

## File Map

### Production files to create

- `engine/ziwei/flowing_star_models.py` — immutable profile/source/placement/layer/view support models and invariant validation.
- `engine/ziwei/flowing_star_sources.py` — decadal/yearly/monthly/daily/hourly source adapters only.
- `engine/ziwei/flowing_stars.py` — pure placement formulas, deterministic catalog ordering, layer builder.
- `engine/ziwei/flowing_star_view.py` — branch→palace materialization and transformation-layer join view.

### Production files to modify

- `engine/calendar/sexagenary.py` — add neutral `lunar_year_branch()` and valid-sexagenary-pair helper.
- `engine/ziwei/errors.py` — add `ZiweiFlowingStarError` with existing `{code, details}` contract.
- `engine/ziwei/capabilities.py` — final capability state and conditional dependency metadata.
- `engine/ziwei/__init__.py` — public exports after core is stable.

### Test / qualification files

- `tests/test_ziwei_phase2c_rule_source.py`
- `tests/test_ziwei_flowing_star_models.py`
- `tests/test_calendar_sexagenary_phase2c.py`
- `tests/test_ziwei_flowing_star_sources.py`
- `tests/test_ziwei_flowing_stars.py`
- `tests/test_ziwei_flowing_star_view.py`
- `tests/test_ziwei_phase2c_capabilities.py`
- `tests/test_ziwei_phase2c_qualification.py`
- `qualification/ziwei/phase2c/public-iztro-flowing-star-vectors.json`
- `qualification/ziwei/phase2c/private-astralium-summary.json`
- `qualification/ziwei/phase2c/phase2c-summary.json`
- `tools/check_phase2c_rule_source.py`
- `tools/qualify_ziwei_phase2c.py`

### Documentation to modify after product/qualification GREEN

- `命理推導計算規則.md`
- `core/核心提示詞.md`
- `docs/架構說明.md`
- `README.md`
- `CHANGELOG.md`
- `docs/更新與版本同步.md` only if capability-state sync assertions require it.

---

### Task 0: Rule / Capability Reconciliation Gate

**Files:**
- Create: `tools/check_phase2c_rule_source.py`
- Create: `tests/test_ziwei_phase2c_rule_source.py`

**Interfaces:**
- Produces `check_phase2c_rule_source() -> dict`.
- Returned dict keys: `status`, `checks`, `main_baseline`, `release_identity`.
- `status` is `PASS` only when existing Phase 2A/2B/2C0 states and v1.2.0 release identity match the approved spec.
- This task does **not** change `ziwei.flowing_stars` from planned.

- [ ] **Step 1: Write the failing test for the missing rule-source checker**

```python
import unittest

from tools.check_phase2c_rule_source import check_phase2c_rule_source


class Phase2CRuleSourceTests(unittest.TestCase):
    def test_phase2c_prerequisites_match_approved_baseline(self):
        report = check_phase2c_rule_source()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["release_identity"], "v1.2.0")
        self.assertEqual(report["checks"]["ziwei.transformations"], "implemented/stable/on_demand")
        self.assertEqual(report["checks"]["ziwei.flying"], "implemented/stable/on_demand")
        self.assertEqual(report["checks"]["ziwei.flow_month_stem"], "implemented/experimental/on_demand")
        self.assertEqual(report["checks"]["ziwei.flow_day_stem"], "implemented/experimental/on_demand")
        self.assertEqual(report["checks"]["ziwei.flow_hour_stem"], "implemented/experimental/on_demand")
        self.assertEqual(report["checks"]["ziwei.natal_chart"], "implemented/experimental/on_demand")
        self.assertEqual(report["checks"]["ziwei.flowing_stars"], "planned/none/on_demand")
```

- [ ] **Step 2: Run RED and inspect the failure**

Run:

```bash
python -m unittest tests.test_ziwei_phase2c_rule_source -v
```

Expected: import failure because `tools.check_phase2c_rule_source` does not exist. Any failure in existing capability values is a real Gate failure; stop before Task 1.

- [ ] **Step 3: Implement the checker without mutating product state**

```python
from pathlib import Path

from engine.ziwei.capabilities import get_capability

_REQUIRED = (
    "ziwei.transformations",
    "ziwei.flying",
    "ziwei.flow_month_stem",
    "ziwei.flow_day_stem",
    "ziwei.flow_hour_stem",
    "ziwei.natal_chart",
    "ziwei.flowing_stars",
)


def _state(capability_id):
    cap = get_capability(capability_id)
    maturity = "none" if cap["maturity"] is None else cap["maturity"]
    return "%s/%s/%s" % (cap["implementation"], maturity, cap["routing"])


def check_phase2c_rule_source():
    version_text = Path("VERSION.md").read_text(encoding="utf-8")
    checks = {capability_id: _state(capability_id) for capability_id in _REQUIRED}
    expected = {
        "ziwei.transformations": "implemented/stable/on_demand",
        "ziwei.flying": "implemented/stable/on_demand",
        "ziwei.flow_month_stem": "implemented/experimental/on_demand",
        "ziwei.flow_day_stem": "implemented/experimental/on_demand",
        "ziwei.flow_hour_stem": "implemented/experimental/on_demand",
        "ziwei.natal_chart": "implemented/experimental/on_demand",
        "ziwei.flowing_stars": "planned/none/on_demand",
    }
    passed = checks == expected and "v1.2.0" in version_text
    return {
        "status": "PASS" if passed else "FAIL",
        "checks": checks,
        "main_baseline": "bb08ded1d8ed9b026bcd3d8719f00515da6054c3-or-legal-successor",
        "release_identity": "v1.2.0" if "v1.2.0" in version_text else "UNKNOWN",
    }
```

- [ ] **Step 4: Run GREEN and existing capability regression**

```bash
python -m unittest tests.test_ziwei_phase2c_rule_source tests.test_ziwei_capabilities tests.test_ziwei_natal_capabilities -v
```

Expected: PASS and emit/record `PHASE2C_RULE_SOURCE_RECONCILIATION_PASS` in the later validation workflow.

- [ ] **Step 5: Commit**

```bash
git add tools/check_phase2c_rule_source.py tests/test_ziwei_phase2c_rule_source.py
git commit -m "test: lock Phase 2C rule source gate"
```

---

### Task 1: Define Flowing-Star Error, Profile, Source, Placement, and Layer Models

**Files:**
- Modify: `engine/ziwei/errors.py`
- Create: `engine/ziwei/flowing_star_models.py`
- Create: `tests/test_ziwei_flowing_star_models.py`

**Interfaces:**
- Produces `ZiweiFlowingStarError(code, message, details=None)` with `.code` and `.details`.
- Produces frozen `FlowingStarProfile(profile_id, rule_version, canonical_location, qualification_target)`.
- Produces frozen `FlowingStarSource(chart_identity, scope, reference, heavenly_stem, earthly_branch, source_profile, rule_version, validation_status, provenance)`.
- Produces frozen `FlowingStarPlacement(base_star, category, scope, target_branch, sequence, provenance)`.
- Produces frozen `FlowingStarLayer(identity, source, placements, profile_id, rule_version, classification, maturity, validation, provenance)`.
- Produces frozen `ScopePalaceMapping(chart_id, scope, reference, palaces)` for optional materialization.
- Produces frozen `FlowingStarMaterializedRecord(base_star, display_name, target_branch, natal_palace, scope_palace, scope, source_reference)`.
- Produces frozen `ZiweiDynamicCycleView(transformation_layer, flowing_star_layer, materialized_records)`.

- [ ] **Step 1: Write RED model/error tests**

```python
import unittest
from dataclasses import FrozenInstanceError

from engine.ziwei.errors import ZiweiFlowingStarError
from engine.ziwei.flowing_star_models import FlowingStarProfile


class FlowingStarModelTests(unittest.TestCase):
    def test_error_contract_matches_existing_ziwei_errors(self):
        err = ZiweiFlowingStarError("cycle_scope_mismatch", "x", {"scope": "daily"})
        self.assertEqual(err.code, "cycle_scope_mismatch")
        self.assertEqual(err.details, {"scope": "daily"})

    def test_profile_is_frozen_and_versioned(self):
        profile = FlowingStarProfile(
            "ziwei-flowing-stars-common-v1",
            "1.0-exp",
            "earthly_branch",
            "iztro-2.6.0-814b77e6",
        )
        with self.assertRaises(FrozenInstanceError):
            profile.rule_version = "2"
```

Also add tests that reject unsupported scope, empty reference, unknown category, invalid branch, duplicate star identity, wrong star count, wrong `LayerIdentity` chart/scope/reference/profile, and non-`experimental` maturity.

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_ziwei_flowing_star_models -v
```

Expected: missing module/error class only.

- [ ] **Step 3: Add `ZiweiFlowingStarError`**

```python
class ZiweiFlowingStarError(ValueError):
    def __init__(self, code, message, details=None):
        self.code = code
        self.details = dict(details or {})
        super().__init__(message)
```

- [ ] **Step 4: Implement frozen models with explicit invariants**

Use `typing.Optional`, `typing.Mapping`, `typing.Tuple`; do not use `X | None` or `list[str]` in production annotations. Import existing `ChartIdentity`, `LayerIdentity`, `LayerProvenance`, `CycleTransformationLayer` from `engine.ziwei.models`. `FlowingStarLayer.__post_init__` must enforce 10/11 count, unique `base_star`, valid `target_branch`, and exact identity/source/profile consistency.

- [ ] **Step 5: Run GREEN and model regressions**

```bash
python -m unittest tests.test_ziwei_flowing_star_models tests.test_ziwei_fine_cycle_stems tests.test_ziwei_models -v
```

If `tests.test_ziwei_models` does not exist on the execution head, run the existing Phase 2A model suite found by `python -m unittest discover -s tests -p 'test_ziwei*.py'` instead; do not create a fake module to satisfy the command.

- [ ] **Step 6: Commit**

```bash
git add engine/ziwei/errors.py engine/ziwei/flowing_star_models.py tests/test_ziwei_flowing_star_models.py
git commit -m "feat: define Ziwei flowing-star models"
```

---

### Task 2: Add Neutral Lunar-Year Branch and Sexagenary-Pair Helpers

**Files:**
- Modify: `engine/calendar/sexagenary.py`
- Create: `tests/test_calendar_sexagenary_phase2c.py`

**Interfaces:**
- Produces `lunar_year_branch(lunar_year: int) -> str`.
- Produces `is_valid_sexagenary_pair(stem: str, branch: str) -> bool`.
- Existing `lunar_year_stem()` semantics remain unchanged.

- [ ] **Step 1: Write RED tests for complete year cycle and legal-pair parity**

```python
import unittest

from engine.calendar.sexagenary import GAN, ZHI, is_valid_sexagenary_pair, lunar_year_branch


class Phase2CSexagenaryTests(unittest.TestCase):
    def test_lunar_year_branch_repeats_every_twelve_years(self):
        self.assertEqual(lunar_year_branch(1984), "子")
        self.assertEqual(lunar_year_branch(1996), "子")
        self.assertEqual(lunar_year_branch(2026), "午")

    def test_exactly_sixty_of_120_stem_branch_pairs_are_legal(self):
        legal = [(g, z) for g in GAN for z in ZHI if is_valid_sexagenary_pair(g, z)]
        self.assertEqual(len(legal), 60)
        self.assertTrue(is_valid_sexagenary_pair("甲", "子"))
        self.assertFalse(is_valid_sexagenary_pair("甲", "丑"))
```

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_calendar_sexagenary_phase2c -v
```

- [ ] **Step 3: Implement neutral helpers**

```python
def lunar_year_branch(lunar_year: int) -> str:
    if not isinstance(lunar_year, int) or isinstance(lunar_year, bool):
        raise ValueError("lunar_year must be int")
    return ZHI[(lunar_year - 4) % 12]


def is_valid_sexagenary_pair(stem: str, branch: str) -> bool:
    if stem not in GAN or branch not in ZHI:
        return False
    return GAN.index(stem) % 2 == ZHI.index(branch) % 2
```

- [ ] **Step 4: Run GREEN plus full Calendar tests**

```bash
python -m unittest tests.test_calendar_sexagenary_phase2c -v
python -m unittest discover -s tests -p 'test_calendar*.py'
```

- [ ] **Step 5: Commit**

```bash
git add engine/calendar/sexagenary.py tests/test_calendar_sexagenary_phase2c.py
git commit -m "feat: add neutral lunar-year sexagenary helpers"
```

---

### Task 3: Implement Five Scope Source Adapters

**Files:**
- Create: `engine/ziwei/flowing_star_sources.py`
- Create: `tests/test_ziwei_flowing_star_sources.py`

**Interfaces:**
- `source_from_decadal(period: ZiweiDecadalPeriod, chart_identity: ChartIdentity) -> FlowingStarSource`
- `source_from_yearly(context: CalendarContext, chart_identity: ChartIdentity) -> FlowingStarSource`
- `source_from_resolved_cycle(resolution: ResolvedCycleStem, chart_identity: ChartIdentity, expected_scope: str) -> FlowingStarSource`
- Convenience wrappers: `source_from_monthly(...)`, `source_from_daily(...)`, `source_from_hourly(...)`.

- [ ] **Step 1: Write RED tests for decadal/yearly/monthly/daily/hourly adapters**

Use real existing model constructors. Key assertions:

```python
source = source_from_resolved_cycle(resolution, chart_identity, "daily")
self.assertEqual(source.scope, "daily")
self.assertEqual(source.reference, resolution.reference)
self.assertEqual(source.heavenly_stem, resolution.heavenly_stem)
self.assertEqual(source.earthly_branch, resolution.earthly_branch)
```

Add explicit negative tests for:

- `ResolvedCycleStem.scope="daily"` requested as monthly → `cycle_scope_mismatch`.
- invalid 60-cycle pair → `invalid_sexagenary_pair`.
- `boundary_conflict` → `calendar_boundary_conflict`.
- `out_of_validated_range` → `calendar_out_of_validated_range`.
- blank/malformed decadal `stem_branch` → `decadal_source_not_resolved`.

- [ ] **Step 2: Write yearly basis tests**

Construct Calendar contexts around lunar-year change. Assert adapter uses `context.lunar.year` through `lunar_year_stem()` + `lunar_year_branch()` and reference exactly `lunar-year:YYYY`. Do not derive from Gregorian year or Bazi year pillar.

- [ ] **Step 3: Run RED**

```bash
python -m unittest tests.test_ziwei_flowing_star_sources -v
```

- [ ] **Step 4: Implement shared source validator**

```python
def _build_source(chart_identity, scope, reference, stem, branch, source_profile, rule_version, validation_status, provenance):
    if scope not in FLOWING_STAR_SCOPES:
        raise ZiweiFlowingStarError("unsupported_flowing_star_scope", "unsupported flowing-star scope", {"scope": scope})
    if not is_valid_sexagenary_pair(stem, branch):
        raise ZiweiFlowingStarError("invalid_sexagenary_pair", "flowing-star source must be a valid sexagenary pair", {"stem": stem, "branch": branch})
    if validation_status == "boundary_conflict":
        raise ZiweiFlowingStarError("calendar_boundary_conflict", "calendar source is in boundary conflict")
    if validation_status == "out_of_validated_range":
        raise ZiweiFlowingStarError("calendar_out_of_validated_range", "calendar source is outside validated range")
    return FlowingStarSource(...)
```

Use exact source profile IDs from upstream models (`ZiweiDecadalPeriod` provenance when available; Phase 2B profile/rule version for resolved cycles; lunar-year basis profile for yearly).

- [ ] **Step 5: Run GREEN plus Phase 2B/2C0 source regressions**

```bash
python -m unittest tests.test_ziwei_flowing_star_sources tests.test_ziwei_fine_cycle_stems tests.test_ziwei_natal_decadal -v
```

If the exact Natal decadal test module name differs, resolve the existing filename before execution and run the real module; do not skip decadal regression.

- [ ] **Step 6: Commit**

```bash
git add engine/ziwei/flowing_star_sources.py tests/test_ziwei_flowing_star_sources.py
git commit -m "feat: add flowing-star source adapters"
```

---

### Task 4: Implement Pure Flowing-Star Placement Core

**Files:**
- Create: `engine/ziwei/flowing_stars.py`
- Create: `tests/test_ziwei_flowing_stars.py`

**Interfaces:**
- Constants: `FLOWING_STAR_PROFILE_ID = "ziwei-flowing-stars-common-v1"`, `FLOWING_STAR_RULE_VERSION = "1.0-exp"`.
- `get_flowing_star_profile(profile_id=FLOWING_STAR_PROFILE_ID) -> FlowingStarProfile`.
- `place_chang_qu_by_stem(heavenly_stem: str) -> dict`.
- `place_luan_xi(earthly_branch: str) -> dict`.
- `place_nianjie(earthly_branch: str) -> dict`.
- `place_flowing_stars_for_pair(scope: str, heavenly_stem: str, earthly_branch: str, profile_id=...) -> Tuple[FlowingStarPlacement, ...]` — pure formula API used by exhaustive oracle; validates each stem/branch independently but does not require the pair to be one of the 60 cycles.
- `build_flowing_star_layer(source: FlowingStarSource, profile_id=...) -> FlowingStarLayer` — formal runtime API; source already enforces valid 60-cycle pair.

- [ ] **Step 1: Write RED tests for fixed catalog/order**

```python
expected = (
    "天魁", "天鉞", "文昌", "文曲", "祿存",
    "擎羊", "陀羅", "天馬", "紅鸞", "天喜",
)
rows = place_flowing_stars_for_pair("monthly", "甲", "子")
self.assertEqual(tuple(row.base_star for row in rows), expected)
self.assertEqual(tuple(row.sequence for row in rows), tuple(range(1, 11)))
```

For yearly, assert `年解` is sequence 11 and no other scope includes it.

- [ ] **Step 2: Write exact 昌曲 / 鸞喜 / 年解 table tests**

Hard-code the approved spec tables in test fixtures, not implementation constants imported back into tests. Cover all 10 stems for Chang/Qu and all 12 branches for Luan/Xi and Nianjie.

- [ ] **Step 3: Write reuse tests for existing 2C0 helpers**

Patch/spy or direct equality-test that flowing-star outputs for `天魁/天鉞`, `祿存/擎羊/陀羅`, and `天馬` match `place_kui_yue()`, `place_lucun_yang_tuo()`, and `place_tianma()` from `engine.ziwei.natal_stars`; do not copy those tables into production `flowing_stars.py`.

- [ ] **Step 4: Write invariant/property tests across the 600 formula combinations**

```python
for scope in ("decadal", "yearly", "monthly", "daily", "hourly"):
    for stem in GAN:
        for branch in ZHI:
            rows = place_flowing_stars_for_pair(scope, stem, branch)
            self.assertEqual(len(rows), 11 if scope == "yearly" else 10)
            self.assertEqual(len({row.base_star for row in rows}), len(rows))
```

Also assert: Tianxi is six branches opposite Hongluan, Yang/Tuo are adjacent to Lucun, Tianma is always one of `寅申巳亥`, and repeated calls produce equal tuples.

- [ ] **Step 5: Run RED**

```bash
python -m unittest tests.test_ziwei_flowing_stars -v
```

- [ ] **Step 6: Implement the pure core**

Use existing helpers:

```python
from .natal_stars import place_kui_yue, place_lucun_yang_tuo, place_tianma
```

Implement Chang/Qu exactly from the approved table:

```python
_CHANG_QU_BY_STEM = {
    "甲": ("巳", "酉"), "乙": ("午", "申"),
    "丙": ("申", "午"), "丁": ("酉", "巳"),
    "戊": ("申", "午"), "己": ("酉", "巳"),
    "庚": ("亥", "卯"), "辛": ("子", "寅"),
    "壬": ("寅", "子"), "癸": ("卯", "亥"),
}
```

Implement Hongluan as reverse count from 卯 by canonical year-branch index and Tianxi as +6; implement Nianjie exact approved 12-branch mapping. Build placements in one fixed `_FLOWING_STAR_ORDER` tuple, never by arbitrary dict iteration.

- [ ] **Step 7: Run GREEN and Natal helper regression**

```bash
python -m unittest tests.test_ziwei_flowing_stars tests.test_ziwei_natal_stars -v
```

- [ ] **Step 8: Commit**

```bash
git add engine/ziwei/flowing_stars.py tests/test_ziwei_flowing_stars.py
git commit -m "feat: implement Ziwei flowing-star core"
```

---

### Task 5: Build Independent Flowing-Star Layer and Validate 60 Legal Sources

**Files:**
- Modify: `engine/ziwei/flowing_stars.py`
- Modify: `tests/test_ziwei_flowing_stars.py`

**Interfaces:**
- `build_flowing_star_layer(source, profile_id=FLOWING_STAR_PROFILE_ID) -> FlowingStarLayer`.
- Layer identity uses existing `LayerIdentity(source.chart_identity.chart_id, source.scope, source.reference, profile.profile_id)`.
- Layer classification is exactly `Project 推導盤面`, maturity exactly `experimental`.

- [ ] **Step 1: Write RED formal-source tests for 300 legal sources**

Generate 60 legal pairs using `is_valid_sexagenary_pair`, then for each of five scopes construct a `FlowingStarSource` and build a layer. Assert 300/300 succeed.

- [ ] **Step 2: Write RED invalid-source tests for the other 300 pairs**

Attempting to construct/adapt any parity-invalid stem/branch pair must fail before `build_flowing_star_layer()` with `invalid_sexagenary_pair`. Do not weaken `FlowingStarSource` just to reuse the 600 formula matrix.

- [ ] **Step 3: Add identity/profile/validation fail-closed tests**

Assert layer creation rejects source/layer mismatch and unknown profile. `boundary_caution` remains visible in `layer.validation`; blocking statuses never reach available layer construction.

- [ ] **Step 4: Implement minimal layer builder**

```python
def build_flowing_star_layer(source, profile_id=FLOWING_STAR_PROFILE_ID):
    profile = get_flowing_star_profile(profile_id)
    placements = place_flowing_stars_for_pair(
        source.scope,
        source.heavenly_stem,
        source.earthly_branch,
        profile.profile_id,
    )
    identity = LayerIdentity(
        source.chart_identity.chart_id,
        source.scope,
        source.reference,
        profile.profile_id,
    )
    return FlowingStarLayer(
        identity,
        source,
        placements,
        profile.profile_id,
        profile.rule_version,
        "Project 推導盤面",
        "experimental",
        source.validation_status,
        _project_provenance(profile),
    )
```

- [ ] **Step 5: Run focused and all Ziwei tests**

```bash
python -m unittest tests.test_ziwei_flowing_stars tests.test_ziwei_flowing_star_sources -v
python -m unittest discover -s tests -p 'test_ziwei*.py'
```

- [ ] **Step 6: Commit**

```bash
git add engine/ziwei/flowing_stars.py tests/test_ziwei_flowing_stars.py
git commit -m "feat: build Ziwei flowing-star layers"
```

---

### Task 6: Implement Materialized Palace View and Dynamic Cycle Join

**Files:**
- Create: `engine/ziwei/flowing_star_view.py`
- Create: `tests/test_ziwei_flowing_star_view.py`

**Interfaces:**
- `materialize_flowing_star_layer(layer: FlowingStarLayer, natal_palaces, scope_mapping: Optional[ScopePalaceMapping] = None) -> Tuple[FlowingStarMaterializedRecord, ...]`.
- `join_dynamic_cycle(transformation_layer: CycleTransformationLayer, flowing_star_layer: FlowingStarLayer, materialized_records=()) -> ZiweiDynamicCycleView`.
- Join key is exactly `(chart_id, scope, reference)`; `rule_profile` equality is **not** required.

- [ ] **Step 1: Write RED natal-palace materialization test**

Use a complete 12-record `ZiweiPalaceRecord` set. For every placement, assert `target_branch` is unchanged and `natal_palace` equals the palace whose `branch` matches.

- [ ] **Step 2: Write optional scope-palace tests**

No scope mapping → `scope_palace is None`. Complete matching `ScopePalaceMapping` → scope palace populated. Mapping with fewer than 12 unique branches or mismatched chart/scope/reference → `flowing_star_materialization_mismatch`.

- [ ] **Step 3: Write RED join tests**

Create a real `CycleTransformationLayer` from existing Phase 2A/2B helpers and a flowing-star layer with the same chart/scope/reference but a different `rule_profile`; join must succeed. Mismatched chart, scope, or reference must fail with details naming the mismatched field.

- [ ] **Step 4: Implement display names only in view layer**

Prefix map:

```python
_PREFIX = {
    "decadal": "運",
    "yearly": "流",
    "monthly": "月",
    "daily": "日",
    "hourly": "時",
}
```

Display identity for `年解` remains `年解`. For other base stars, strip leading `天` only where the approved presentation naming expects `魁/鉞/昌/曲/馬/喜`; do not alter canonical `base_star` in the layer. Lock exact names in tests before implementation.

- [ ] **Step 5: Run GREEN plus Stable composition regression**

```bash
python -m unittest tests.test_ziwei_flowing_star_view -v
python -m unittest tests.test_ziwei_phase2a_composition tests.test_ziwei_fine_cycle -v
```

Resolve actual existing module filenames on the execution head if they differ; the intent is mandatory regression of `composition.py` and `fine_cycle.py`, not optional skipping.

- [ ] **Step 6: Commit**

```bash
git add engine/ziwei/flowing_star_view.py tests/test_ziwei_flowing_star_view.py
git commit -m "feat: add flowing-star materialized view"
```

---

### Task 7: Update Capability Registry and Public Exports

**Files:**
- Modify: `engine/ziwei/capabilities.py`
- Modify: `engine/ziwei/__init__.py`
- Create: `tests/test_ziwei_phase2c_capabilities.py`

**Interfaces:**
- `ziwei.flowing_stars = implemented / experimental / on_demand / 1.0-exp`.
- `module = engine.ziwei.flowing_stars`.
- Existing plain `dependencies` remains empty or contains only unconditional shared prerequisites; scope-specific prerequisites are stored as `conditional_dependencies`.

- [ ] **Step 1: Write RED capability state test**

```python
cap = get_capability("ziwei.flowing_stars")
self.assertEqual(
    (cap["implementation"], cap["maturity"], cap["routing"], cap["rule_version"]),
    ("implemented", "experimental", "on_demand", "1.0-exp"),
)
self.assertEqual(cap["module"], "engine.ziwei.flowing_stars")
self.assertTrue(can_execute("ziwei.flowing_stars"))
self.assertFalse(should_run_by_default("ziwei.flowing_stars"))
```

- [ ] **Step 2: Lock non-promotion states**

Assert transformations/flying remain stable and monthly/daily/hourly stem + natal_chart remain experimental. This test must fail if Phase 2C causes maturity cascade.

- [ ] **Step 3: Lock conditional dependency metadata**

Expected metadata:

```python
{
    "decadal": ("ziwei.natal_chart",),
    "yearly": (),
    "monthly": ("ziwei.flow_month_stem",),
    "daily": ("ziwei.flow_day_stem",),
    "hourly": ("ziwei.flow_hour_stem",),
}
```

Do not interpret this as a runtime AND across all scopes.

- [ ] **Step 4: Run RED**

```bash
python -m unittest tests.test_ziwei_phase2c_capabilities -v
```

- [ ] **Step 5: Update registry and exports**

Export only stable public entry points needed by callers, such as `build_flowing_star_layer`, source adapters, and materialization helper. Do not export private table constants.

- [ ] **Step 6: Run GREEN and all capability tests**

```bash
python -m unittest tests.test_ziwei_phase2c_capabilities -v
python -m unittest discover -s tests -p '*capabilit*.py'
```

- [ ] **Step 7: Commit**

```bash
git add engine/ziwei/capabilities.py engine/ziwei/__init__.py tests/test_ziwei_phase2c_capabilities.py
git commit -m "feat: enable Ziwei flowing-stars capability"
```

---

### Task 8: Build Pinned iztro Public Qualification and Privacy-Safe Summary

**Files:**
- Create: `qualification/ziwei/phase2c/public-iztro-flowing-star-vectors.json`
- Create: `qualification/ziwei/phase2c/private-astralium-summary.json`
- Create: `tools/qualify_ziwei_phase2c.py`
- Create: `tests/test_ziwei_phase2c_qualification.py`

**Interfaces:**
- Public fixture metadata includes exact oracle `package_version=2.6.0`, `revision=814b77e6371e1050cac31bbf674db3c3138fcfde`, source files, case count, and SHA-256 of canonical fixture payload.
- `run_public_qualification() -> dict` returns aggregate counts and mismatches.
- `build_phase2c_summary(public_report, private_summary) -> dict` emits only aggregate/status/digest/version fields.

- [ ] **Step 1: Create oracle fixture generation procedure outside runtime path**

During implementation/validation, check out pinned iztro revision and invoke its `star.getHoroscopeStar(stem, branch, scope)` for all 600 `(scope, stem, branch)` combinations. Convert iztro palace indexes to canonical Earthly Branches before writing the fixture. The committed JSON must not contain private birth data.

Expected aggregate:

```text
source combinations = 600
placements = 6120
  decadal  = 1200
  yearly   = 1320
  monthly  = 1200
  daily    = 1200
  hourly   = 1200
```

- [ ] **Step 2: Include pinned upstream golden anchors**

Store at least the exact upstream cases for `getHoroscopeStar("庚", "辰", "decadal")` and `getHoroscopeStar("癸", "卯", "yearly")`. Tests must compare these known cases independently of the 600-case loop so a converter bug cannot self-validate.

- [ ] **Step 3: Write RED qualification tests**

```python
report = run_public_qualification()
self.assertEqual(report["status"], "PASS")
self.assertEqual(report["source_case_count"], 600)
self.assertEqual(report["placement_check_count"], 6120)
self.assertEqual(report["unexpected_mismatch_count"], 0)
```

Also assert fixture has no forbidden private keys and no extra star identities such as 歲建/將星/博士/長生.

- [ ] **Step 4: Implement Python qualifier against committed fixture**

For each case call `place_flowing_stars_for_pair(scope, stem, branch)` and compare canonical `(base_star, category, target_branch, scope)` exactly. Do not normalize an actual mismatch into a profile difference unless the approved spec explicitly defines it.

- [ ] **Step 5: Create initial private summary as explicit PENDING**

```json
{
  "source": "Astralium flowing-stars",
  "status": "PENDING",
  "case_count": 0,
  "unexpected_mismatch_count": 0,
  "promotion_allowed": false,
  "raw_private_data_committed": false
}
```

Do not copy Phase 2C0 Natal private PASS into this file.

- [ ] **Step 6: Run public qualification and focused tests**

```bash
python tools/qualify_ziwei_phase2c.py --public
python -m unittest tests.test_ziwei_phase2c_qualification tests.test_ziwei_flowing_stars -v
```

Expected markers:

```text
IZTRO_FLOWING_STARS_600_600_PASS
IZTRO_FLOWING_STARS_0_UNEXPECTED_MISMATCH
```

- [ ] **Step 7: Commit**

```bash
git add qualification/ziwei/phase2c tools/qualify_ziwei_phase2c.py tests/test_ziwei_phase2c_qualification.py
git commit -m "test: qualify Ziwei flowing stars against pinned iztro"
```

---

### Task 9: Synchronize Rules, Prompt, Architecture, README, and Changelog

**Files:**
- Modify: `命理推導計算規則.md`
- Modify: `core/核心提示詞.md`
- Modify: `docs/架構說明.md`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Optionally Modify: `docs/更新與版本同步.md` only if existing machine-readable docs assertions require the new capability state.
- Create: `tests/test_ziwei_phase2c_docs.py`

**Interfaces:**
- Documentation states `ziwei.flowing_stars = implemented / experimental / on_demand / 1.0-exp` only after Tasks 1–8 are GREEN.
- Documentation keeps `VERSION.md` release identity at v1.2.0.
- Documentation explicitly distinguishes `Project 推導盤面` from third-party raw output.
- Documentation keeps Astralium flowing-stars qualification `PENDING` unless a separate private qualification is later run.

- [ ] **Step 1: Write docs RED assertions before editing docs**

Assertions must require all of these phrases/semantics in authoritative docs:

```text
Phase 2C Ziwei Flowing Stars
ziwei-flowing-stars-common-v1
implemented / experimental / on_demand
Project 推導盤面
Astralium flowing-stars = PENDING
歲前／將前十二神 not in Phase 2C v1
VERSION v1.2.0 unchanged
```

Also assert Phase 2B and Phase 2C0 docs are not rewritten to claim flowing stars were already included there.

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_ziwei_phase2c_docs -v
```

- [ ] **Step 3: Update authoritative docs minimally**

`命理推導計算規則.md` must define the five scope sources and explain that month/day/hour reuse Phase 2B, decadal reuses 2C0, yearly uses lunar-year helper. `core/核心提示詞.md` must allow Project-derived flowing-star layers only when the source precision exists. `docs/架構說明.md` must show the independent layer beside transformation/flying. `CHANGELOG.md` adds `Unreleased｜Phase 2C Ziwei Flowing Stars` above earlier Unreleased sections.

- [ ] **Step 4: Explicitly do not edit VERSION.md**

Use a test that reads `VERSION.md` and asserts `Metaphysics Lab Core：**v1.2.0**` remains present. If docs changes require a release bump, stop; that is outside this plan.

- [ ] **Step 5: Run GREEN plus existing docs regression**

```bash
python -m unittest tests.test_ziwei_phase2c_docs -v
python -m unittest discover -s tests -p '*docs*.py'
```

- [ ] **Step 6: Commit**

```bash
git add 命理推導計算規則.md core/核心提示詞.md docs/架構說明.md README.md CHANGELOG.md tests/test_ziwei_phase2c_docs.py
git commit -m "docs: document Phase 2C flowing stars"
```

If `docs/更新與版本同步.md` was required by failing existing assertions, include it in the same commit after preserving its old machine-readable section markers.

---

### Task 10: Phase 2C Acceptance Workflow, Aggregate Evidence, and Formal Feature Snapshot

**Files:**
- Create on **temporary validation branch only**: `.github/workflows/phase2c-tdd.yml`
- Create on **temporary validation branch only**: `.github/workflows/phase2c-acceptance.yml`
- Create: `qualification/ziwei/phase2c/phase2c-summary.json`
- Create: `tests/test_ziwei_phase2c_acceptance.py`

**Interfaces:**
- Final shared marker: `PHASE2C_ACCEPTANCE_PASS` only after every prior Gate passes.
- Formal feature tree excludes temporary workflow files.
- Capability remains Experimental and private qualification remains PENDING unless separately authorized and executed.

- [ ] **Step 1: Write acceptance test contract**

The test must verify:

```text
public qualification PASS
600 source cases
6120 placement checks
0 unexpected mismatch
private Astralium status PENDING or privacy-safe authorized aggregate PASS
promotion_allowed false
ziwei.flowing_stars implemented/experimental/on_demand/1.0-exp
transformations/flying stable unchanged
flow_month/day/hour stem experimental unchanged
natal_chart experimental unchanged
VERSION.md v1.2.0 unchanged
no private raw keys
no Qimen files changed
no yearlyDecStar/歲前/將前 catalog leakage
```

- [ ] **Step 2: Run focused Phase 2C suite locally/on feature validation branch**

```bash
python -m unittest \
  tests.test_ziwei_phase2c_rule_source \
  tests.test_ziwei_flowing_star_models \
  tests.test_calendar_sexagenary_phase2c \
  tests.test_ziwei_flowing_star_sources \
  tests.test_ziwei_flowing_stars \
  tests.test_ziwei_flowing_star_view \
  tests.test_ziwei_phase2c_capabilities \
  tests.test_ziwei_phase2c_qualification \
  tests.test_ziwei_phase2c_docs \
  tests.test_ziwei_phase2c_acceptance -v
```

- [ ] **Step 3: Run full regression**

```bash
python -m unittest discover -s tests -p 'test*.py'
```

Any failure stops acceptance. Do not claim a Phase 2C algorithm failure when the failing step is validation infrastructure; classify the failure before changing code.

- [ ] **Step 4: Run Python 3.9 syntax Gate**

```bash
python3.9 -m compileall -q engine tools tests
```

If CI provides only `python` at 3.9, assert `python --version` starts with `Python 3.9.` before compileall.

- [ ] **Step 5: Run qualification Gate**

```bash
python tools/qualify_ziwei_phase2c.py --public
```

Required output markers:

```text
IZTRO_FLOWING_STARS_600_600_PASS
IZTRO_FLOWING_STARS_0_UNEXPECTED_MISMATCH
PHASE2C_PRIVATE_FLOWING_STARS_PENDING_OK
```

If private qualification is later explicitly authorized, replace only the private marker with privacy-safe aggregate PASS; do not change public expectations or maturity.

- [ ] **Step 6: Build deterministic aggregate summary**

`phase2c-summary.json` must contain only version/profile/revision/status/count/digest/capability-state fields. Forbidden keys recursively include `full_name`, `full_address`, `hospital`, `birth_datetime`, `raw_birth_input`, `raw_chart`, `raw_payload`, `external_raw`, and private file paths.

- [ ] **Step 7: Create temporary validation workflows and a MUST NEVER MERGE PR**

The workflows run only on the temporary validation branch/PR. They must execute focused suite, full repo, Python 3.9, public qualification, privacy/scope checks, and emit `PHASE2C_ACCEPTANCE_PASS` only after all steps succeed.

- [ ] **Step 8: Verify exact-head acceptance**

Record exact feature/validation head SHA and workflow run IDs. Queued or in-progress is not success. All acceptance evidence used for merge review must belong to the same effective product tree.

- [ ] **Step 9: Create formal feature snapshot without temporary workflows**

Build/squash `feature/ziwei-flowing-stars-v1` so the formal tree contains product code, tests, docs, qualification fixtures/summaries, and this approved spec/plan, but no `.github/workflows/phase2c-*.yml` validation-only files.

- [ ] **Step 10: Fresh-validate the formal feature snapshot**

Create a new temporary validation branch from the formal feature snapshot, add the validation workflows only there, and rerun every Gate. Confirm diff against formal feature is exactly the temporary workflow files.

- [ ] **Step 11: Stop at feature→design approval Gate**

Do not merge automatically. Present exact feature SHA, fresh validation run IDs, public qualification counts/digest, private status, capability states, and diff scope. Require explicit user approval for `feature/ziwei-flowing-stars-v1 → design/ziwei-flowing-stars`.

---

## Execution Order and Stop Conditions

1. Task 0 must PASS before any production implementation.
2. Tasks 1–3 establish models and trusted sources; no placement code before source contracts are GREEN.
3. Tasks 4–5 establish pure formulas and formal layers.
4. Task 6 adds optional views without changing Stable Phase 2A composition semantics.
5. Task 7 flips capability to implemented only after executable core/source/view tests are GREEN.
6. Task 8 must reach `600/600` and `0 unexpected mismatch`; otherwise stop before docs/final acceptance.
7. Task 9 documents only capabilities actually proven by Tasks 1–8.
8. Task 10 is evidence/integration; it does not relax algorithm tests to get a green badge.
9. A failure in any Gate blocks downstream work until root cause is classified and fixed.
10. `feature → design` and `design → main` remain two separate explicit user approvals after implementation.

## Self-Review Checklist

- Spec coverage: pure core, 5 adapters, 10/11-star catalog, legal 60-cycle source constraint, independent layer, materialization, join semantics, qualification, privacy, docs, capability lifecycle, Python 3.9, branch governance are each mapped to a task.
- Placeholder scan: no `TBD`, `TODO`, “similar to previous task”, or unspecified error-handling step remains.
- Type consistency: `FlowingStarSource` uses existing `ChartIdentity`; `FlowingStarLayer` uses existing `LayerIdentity`; join compares `chart_id + scope + reference`, not full identity equality; month/day/hour adapters consume existing `ResolvedCycleStem`; decadal consumes `ZiweiDecadalPeriod`.
- Runtime boundary: iztro appears only in qualification generation/checking; production imports remain Python-only.
- Scope boundary: no `yearlyDecStar`, 歲前/將前十二神, brightness, small-limit, scoring, or interpretation task exists.
- Maturity boundary: only `ziwei.flowing_stars` changes state, and only to Experimental.
