# Ziwei Flowing Stars v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 實作 `ziwei.flowing_stars`：對已解析的大限／流年／流月／流日／流時干支來源，產生 deterministic、可版本化、可qualification 的動態流曜地支位置，並以獨立 layer 與既有四化／飛化安全 join。

**Architecture:** 採 Pure Placement Core + Scope Source Adapters + Independent `FlowingStarLayer`。月／日／時直接重用 Phase 2B `ResolvedCycleStem`；大限直接重用 Phase 2C0 `ZiweiDecadalPeriod.stem_branch`；流年使用 Calendar-neutral lunar-year sexagenary helper。Pure core 不查日期、不重算時間、不修改 Stable Phase 2A `CycleTransformationLayer`。

**Tech Stack:** Python 3.9-compatible syntax、`unittest`、existing `engine/calendar/sexagenary.py`、`engine/ziwei/models.py`、Phase 2B fine-cycle resolver、Phase 2C0 natal models、pinned `SylarLong/iztro` v2.6.0 revision `814b77e6371e1050cac31bbf674db3c3138fcfde` 僅作 qualification oracle。

**Spec:** `docs/superpowers/specs/2026-08-22-Ziwei-Flowing-Stars-設計.md`

## Global Constraints

- Execution begins from the approved `design/ziwei-flowing-stars` head in an isolated worktree/feature branch created with the `using-git-worktrees` workflow; never implement directly on `main` or design.
- Final capability state: `implemented / experimental / on_demand / 1.0-exp`; never promote to Stable in this plan.
- Profile ID: `ziwei-flowing-stars-common-v1`; Project source classification remains Metaphysics Lab / `Project 推導盤面`.
- Canonical location is Earthly Branch only.
- Supported scopes are exactly `decadal`, `yearly`, `monthly`, `daily`, `hourly`.
- Core identities are exactly `天魁 天鉞 文昌 文曲 祿存 擎羊 陀羅 天馬 紅鸞 天喜`; yearly adds only `年解`.
- Non-yearly count = 10; yearly count = 11.
- Do not add 歲前十二神、將前十二神、博士十二神、長生十二神、小限流曜、大量雜曜、流曜亮度、scoring or AI interpretation.
- Do not change Stable `engine/ziwei/transformations.py`, `engine/ziwei/flying.py`, or `CycleTransformationLayer` semantics.
- Monthly/daily/hourly adapters reuse Phase 2B `ResolvedCycleStem` exactly; no re-resolution of month/day/hour stem or boundary policy.
- Decadal adapter reuses `ZiweiDecadalPeriod.stem_branch`; no recalculation from birth data.
- Yearly adapter uses lunar-year stem/branch; do not reuse Bazi Li-Chun year policy.
- Formal `FlowingStarSource` accepts only valid 60-sexagenary pairs. Pure formula qualification separately exercises all 10×12 stem/branch pairs.
- `boundary_conflict` and `out_of_validated_range` fail closed; `boundary_caution` propagates.
- Runtime Python never imports Node/npm, shells out to iztro, or calls an external service.
- Production code must compile on Python 3.9; do not use PEP 604 `X | None` syntax.
- Astralium flowing-star private qualification starts `PENDING`; do not reuse Phase 2C0 Natal private PASS.
- `VERSION.md`, Git tag, and GitHub Release stay unchanged during Unreleased Phase 2C.
- Temporary validation workflows/PRs MUST NEVER MERGE.
- Every implementation task follows RED → inspect expected failure → minimal GREEN → focused regression → commit.

---

## File Map

**Create:**
- `engine/ziwei/flowing_star_models.py`
- `engine/ziwei/flowing_star_sources.py`
- `engine/ziwei/flowing_stars.py`
- `engine/ziwei/flowing_star_view.py`
- `tools/check_phase2c_rule_source.py`
- `tools/qualify_ziwei_phase2c.py`
- `qualification/ziwei/phase2c/generate_iztro_vectors.mjs` — qualification-only generator; not runtime.
- `qualification/ziwei/phase2c/public-iztro-flowing-star-vectors.json`
- `qualification/ziwei/phase2c/private-astralium-summary.json`
- `qualification/ziwei/phase2c/phase2c-summary.json`
- `tests/test_ziwei_phase2c_rule_source.py`
- `tests/test_calendar_sexagenary_phase2c.py`
- `tests/test_ziwei_flowing_star_models.py`
- `tests/test_ziwei_flowing_star_sources.py`
- `tests/test_ziwei_flowing_stars.py`
- `tests/test_ziwei_flowing_star_view.py`
- `tests/test_ziwei_phase2c_capabilities.py`
- `tests/test_ziwei_phase2c_qualification.py`
- `tests/test_ziwei_phase2c_docs.py`
- `tests/test_ziwei_phase2c_acceptance.py`

**Modify:**
- `engine/calendar/sexagenary.py`
- `engine/ziwei/errors.py`
- `engine/ziwei/capabilities.py`
- `engine/ziwei/__init__.py`
- `命理推導計算規則.md`
- `core/核心提示詞.md`
- `docs/架構說明.md`
- `README.md`
- `CHANGELOG.md`
- `docs/更新與版本同步.md` only if existing machine-readable docs contracts require synchronization.

---

### Task 0: Rule / Capability Reconciliation Gate

**Files:** Create `tools/check_phase2c_rule_source.py`, `tests/test_ziwei_phase2c_rule_source.py`.

**Produces:** `check_phase2c_rule_source() -> dict` containing `status`, `checks`, `release_identity`. This task does not mutate capability state.

- [ ] **Step 1: Verify branch ancestry before writing code**

Execution command:

```bash
git merge-base --is-ancestor bb08ded1d8ed9b026bcd3d8719f00515da6054c3 HEAD
```

Expected exit code 0. If not, stop and reconcile the base; do not encode a fake baseline string in Python.

- [ ] **Step 2: Write RED test for missing checker**

```python
import unittest
from tools.check_phase2c_rule_source import check_phase2c_rule_source

class Phase2CRuleSourceTests(unittest.TestCase):
    def test_prerequisites_match_approved_state(self):
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

- [ ] **Step 3: Run RED**

```bash
python -m unittest tests.test_ziwei_phase2c_rule_source -v
```

Expected only missing module/import. Any state mismatch is a real Gate failure.

- [ ] **Step 4: Implement checker**

Use `engine.ziwei.capabilities.get_capability()` and read `VERSION.md`; compare the exact states above. Return `PASS` only when all match and `v1.2.0` is present.

- [ ] **Step 5: Run GREEN and capability regression**

```bash
python -m unittest tests.test_ziwei_phase2c_rule_source -v
python -m unittest discover -s tests -p '*capabilit*.py'
```

- [ ] **Step 6: Commit**

```bash
git add tools/check_phase2c_rule_source.py tests/test_ziwei_phase2c_rule_source.py
git commit -m "test: lock Phase 2C rule source gate"
```

---

### Task 1: Add Neutral Lunar-Year and Legal-Sexagenary Helpers

**Files:** Modify `engine/calendar/sexagenary.py`; create `tests/test_calendar_sexagenary_phase2c.py`.

**Produces:** `lunar_year_branch(lunar_year: int) -> str`, `is_valid_sexagenary_pair(stem: str, branch: str) -> bool`.

- [ ] **Step 1: Write RED tests**

```python
from engine.calendar.sexagenary import GAN, ZHI, is_valid_sexagenary_pair, lunar_year_branch

class Phase2CSexagenaryTests(unittest.TestCase):
    def test_lunar_year_branch(self):
        self.assertEqual(lunar_year_branch(1984), "子")
        self.assertEqual(lunar_year_branch(1996), "子")
        self.assertEqual(lunar_year_branch(2026), "午")

    def test_exactly_sixty_pairs_are_legal(self):
        legal = [(g, z) for g in GAN for z in ZHI if is_valid_sexagenary_pair(g, z)]
        self.assertEqual(len(legal), 60)
        self.assertTrue(is_valid_sexagenary_pair("甲", "子"))
        self.assertFalse(is_valid_sexagenary_pair("甲", "丑"))
```

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_calendar_sexagenary_phase2c -v
```

- [ ] **Step 3: Implement helpers**

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

- [ ] **Step 4: Run GREEN plus Calendar regression**

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

### Task 2: Define Error, Profile, Source, Placement, Layer, and View Models

**Files:** Modify `engine/ziwei/errors.py`; create `engine/ziwei/flowing_star_models.py`, `tests/test_ziwei_flowing_star_models.py`.

**Produces:**
- `ZiweiFlowingStarError(code, message, details=None)`.
- frozen `FlowingStarProfile(profile_id, rule_version, canonical_location, qualification_target)`.
- frozen `FlowingStarSource(chart_identity, scope, reference, heavenly_stem, earthly_branch, source_profile, rule_version, validation_status, provenance)`.
- frozen `FlowingStarPlacement(base_star, category, scope, target_branch, sequence, provenance)`.
- frozen `FlowingStarLayer(identity, source, placements, profile_id, rule_version, classification, maturity, validation, provenance)`.
- frozen `ScopePalaceMapping(chart_id, scope, reference, palaces)`.
- frozen `FlowingStarMaterializedRecord(...)` and `ZiweiDynamicCycleView(...)`.

- [ ] **Step 1: Write RED immutability/error/model tests**

```python
err = ZiweiFlowingStarError("cycle_scope_mismatch", "x", {"scope": "daily"})
self.assertEqual(err.code, "cycle_scope_mismatch")
self.assertEqual(err.details, {"scope": "daily"})
```

Create a `FlowingStarSource` with `甲子` and assert it is frozen; constructing `甲丑` must raise `ZiweiFlowingStarError` code `invalid_sexagenary_pair`. Also reject unsupported scope, blank reference, invalid branch, unknown category, duplicate star identity, wrong 10/11 count, identity/source mismatch, and non-`experimental` layer maturity.

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_ziwei_flowing_star_models -v
```

- [ ] **Step 3: Add error class**

```python
class ZiweiFlowingStarError(ValueError):
    def __init__(self, code, message, details=None):
        self.code = code
        self.details = dict(details or {})
        super().__init__(message)
```

- [ ] **Step 4: Implement frozen models**

`FlowingStarSource.__post_init__` must call Task 1 `is_valid_sexagenary_pair()`. `FlowingStarLayer.__post_init__` must enforce: `identity.chart_id == source.chart_identity.chart_id`, same scope/reference, `identity.rule_profile == profile_id`, unique star identities, exact count, valid branches, `classification == "Project 推導盤面"`, `maturity == "experimental"`.

Use `typing.Optional`, `Mapping`, `Tuple`; no PEP 604 syntax.

- [ ] **Step 5: Run GREEN and Ziwei model regression**

```bash
python -m unittest tests.test_ziwei_flowing_star_models tests.test_ziwei_fine_cycle_stems -v
```

- [ ] **Step 6: Commit**

```bash
git add engine/ziwei/errors.py engine/ziwei/flowing_star_models.py tests/test_ziwei_flowing_star_models.py
git commit -m "feat: define Ziwei flowing-star models"
```

---

### Task 3: Implement Five Scope Source Adapters

**Files:** Create `engine/ziwei/flowing_star_sources.py`, `tests/test_ziwei_flowing_star_sources.py`.

**Produces:**
- `source_from_decadal(period, chart_identity) -> FlowingStarSource`
- `source_from_yearly(context, chart_identity) -> FlowingStarSource`
- `source_from_resolved_cycle(resolution, chart_identity, expected_scope) -> FlowingStarSource`
- wrappers `source_from_monthly`, `source_from_daily`, `source_from_hourly`.

- [ ] **Step 1: Write RED tests for all five adapters**

For month/day/hour, assert source scope/reference/stem/branch exactly equal the supplied Phase 2B `ResolvedCycleStem`; no recalculation is allowed. Daily resolution passed as monthly must raise `cycle_scope_mismatch`.

- [ ] **Step 2: Write yearly basis RED tests**

Around a lunar-new-year boundary, assert source uses `context.lunar.year`, `lunar_year_stem()`, and `lunar_year_branch()` with reference `lunar-year:YYYY`; Gregorian year and Bazi year pillar are not inputs.

- [ ] **Step 3: Write decadal RED tests**

`ZiweiDecadalPeriod.stem_branch="庚辰"` must yield `庚/辰`. Blank, malformed, or invalid-pair stem_branch must raise `decadal_source_not_resolved`.

- [ ] **Step 4: Write validation propagation tests**

`boundary_caution` survives in source; `boundary_conflict` raises `calendar_boundary_conflict`; `out_of_validated_range` raises `calendar_out_of_validated_range`.

- [ ] **Step 5: Run RED**

```bash
python -m unittest tests.test_ziwei_flowing_star_sources -v
```

- [ ] **Step 6: Implement adapters as thin translation only**

The shared constructor validates scope/reference and delegates legal-pair enforcement to `FlowingStarSource`. Monthly/daily/hourly preserve Phase 2B `profile_id`, `rule_version`, `reference`, `calendar_validation_status`, and provenance. Decadal never reads birth year/sex. Yearly uses neutral lunar-year helpers.

- [ ] **Step 7: Run GREEN plus Phase 2B/2C0 regressions**

```bash
python -m unittest tests.test_ziwei_flowing_star_sources tests.test_ziwei_fine_cycle_stems tests.test_ziwei_natal_decadal -v
```

If the actual decadal test filename differs, resolve and run the existing decadal suite; do not skip it.

- [ ] **Step 8: Commit**

```bash
git add engine/ziwei/flowing_star_sources.py tests/test_ziwei_flowing_star_sources.py
git commit -m "feat: add flowing-star source adapters"
```

---

### Task 4: Implement Pure Flowing-Star Placement Core and Formal Layer Builder

**Files:** Create `engine/ziwei/flowing_stars.py`, `tests/test_ziwei_flowing_stars.py`.

**Produces:**
- `FLOWING_STAR_PROFILE_ID = "ziwei-flowing-stars-common-v1"`
- `FLOWING_STAR_RULE_VERSION = "1.0-exp"`
- `get_flowing_star_profile()`
- `place_chang_qu_by_stem(stem)`
- `place_luan_xi(branch)`
- `place_nianjie(branch)`
- `place_flowing_stars_for_pair(scope, stem, branch, profile_id=...) -> Tuple[FlowingStarPlacement, ...]`
- `build_flowing_star_layer(source, profile_id=...) -> FlowingStarLayer`

- [ ] **Step 1: Write fixed catalog/order RED tests**

Expected order:

```python
("天魁", "天鉞", "文昌", "文曲", "祿存", "擎羊", "陀羅", "天馬", "紅鸞", "天喜")
```

Yearly appends only `年解` as sequence 11.

- [ ] **Step 2: Write exact approved table tests**

Chang/Qu: `甲巳酉, 乙午申, 丙申午, 丁酉巳, 戊申午, 己酉巳, 庚亥卯, 辛子寅, 壬寅子, 癸卯亥`.

Hongluan/Tianxi by branch: `子卯酉, 丑寅申, 寅丑未, 卯子午, 辰亥巳, 巳戌辰, 午酉卯, 未申寅, 申未丑, 酉午子, 戌巳亥, 亥辰戌`.

Nianjie: `子戌, 丑酉, 寅申, 卯未, 辰午, 巳巳, 午辰, 未卯, 申寅, 酉丑, 戌子, 亥亥`.

- [ ] **Step 3: Write reuse RED tests**

Flowing outputs for 魁鉞、祿羊陀、天馬 must equal existing `place_kui_yue`, `place_lucun_yang_tuo`, `place_tianma` results. Production code must import/reuse those helpers, not copy their tables.

- [ ] **Step 4: Write 600 pure-formula invariant tests**

For 5 scopes × 10 stems × 12 branches, assert exact 10/11 count, unique canonical identities, valid branches, deterministic sequence. Also assert Tianxi opposite Hongluan, Yang/Tuo adjacent Lucun, Tianma only in `寅申巳亥`.

- [ ] **Step 5: Run RED**

```bash
python -m unittest tests.test_ziwei_flowing_stars -v
```

- [ ] **Step 6: Implement pure core**

Use one fixed order tuple. `place_flowing_stars_for_pair()` validates stem and branch individually but intentionally does not require a legal 60-cycle pair because it is the formula/oracle API. `build_flowing_star_layer()` accepts only `FlowingStarSource`, which already enforces the 60-cycle constraint.

- [ ] **Step 7: Validate 300 formal sources**

Generate the 60 legal pairs via `is_valid_sexagenary_pair`; across five scopes build 300 formal layers, all must pass. Invalid pairs must fail at source construction and never reach the layer builder.

- [ ] **Step 8: Run GREEN and Natal helper regression**

```bash
python -m unittest tests.test_ziwei_flowing_stars tests.test_ziwei_natal_stars -v
```

- [ ] **Step 9: Commit**

```bash
git add engine/ziwei/flowing_stars.py tests/test_ziwei_flowing_stars.py
git commit -m "feat: implement Ziwei flowing-star core"
```

---

### Task 5: Implement Materialized Palace View and Dynamic Join

**Files:** Create `engine/ziwei/flowing_star_view.py`, `tests/test_ziwei_flowing_star_view.py`.

**Produces:**
- `materialize_flowing_star_layer(layer, natal_palaces, scope_mapping=None)`
- `join_dynamic_cycle(transformation_layer, flowing_star_layer, materialized_records=())`

**Join key:** exactly `(chart_id, scope, reference)`; `rule_profile` equality is not required.

- [ ] **Step 1: Write natal materialization RED tests**

Complete 12-palace input maps each `target_branch` to `natal_palace`; `target_branch` remains unchanged. Missing/duplicate branch map fails closed.

- [ ] **Step 2: Write optional scope-map RED tests**

No mapping → `scope_palace is None`. Matching 12-branch `ScopePalaceMapping` populates it. Wrong chart/scope/reference raises `flowing_star_materialization_mismatch`.

- [ ] **Step 3: Lock exact display-name mapping in tests**

Suffix mapping:

```python
{
    "天魁": "魁", "天鉞": "鉞", "文昌": "昌", "文曲": "曲",
    "祿存": "祿", "擎羊": "羊", "陀羅": "陀", "天馬": "馬",
    "紅鸞": "鸞", "天喜": "喜", "年解": "年解",
}
```

Prefix mapping:

```python
{"decadal": "運", "yearly": "流", "monthly": "月", "daily": "日", "hourly": "時"}
```

Thus examples are `運魁`, `流祿`, `月鸞`, `日馬`, `時喜`; `年解` remains `年解`.

- [ ] **Step 4: Write join RED tests using a real CycleTransformationLayer**

Same chart/scope/reference but different rule profiles must join successfully. Wrong chart, scope, or reference fails with machine-readable mismatch details.

- [ ] **Step 5: Implement view helpers only**

Do not modify `engine/ziwei/composition.py` or `ZiweiLayerStack.cycles` semantics.

- [ ] **Step 6: Run GREEN plus Stable composition/fine-cycle regression**

```bash
python -m unittest tests.test_ziwei_flowing_star_view -v
python -m unittest discover -s tests -p 'test_ziwei*.py'
```

- [ ] **Step 7: Commit**

```bash
git add engine/ziwei/flowing_star_view.py tests/test_ziwei_flowing_star_view.py
git commit -m "feat: add flowing-star dynamic view"
```

---

### Task 6: Update Capability Registry and Public Exports

**Files:** Modify `engine/ziwei/capabilities.py`, `engine/ziwei/__init__.py`; create `tests/test_ziwei_phase2c_capabilities.py`.

- [ ] **Step 1: Write RED capability test**

Expected:

```text
ziwei.flowing_stars = implemented / experimental / on_demand / 1.0-exp
module = engine.ziwei.flowing_stars
can_execute = True
should_run_by_default = False
```

- [ ] **Step 2: Lock no maturity cascade**

Transformations/flying remain stable; flow month/day/hour stems and natal_chart remain experimental.

- [ ] **Step 3: Lock conditional dependency metadata**

```python
{
    "decadal": ("ziwei.natal_chart",),
    "yearly": (),
    "monthly": ("ziwei.flow_month_stem",),
    "daily": ("ziwei.flow_day_stem",),
    "hourly": ("ziwei.flow_hour_stem",),
}
```

Plain `dependencies` must not imply all three fine-cycle stems are required for every scope.

- [ ] **Step 4: Run RED**

```bash
python -m unittest tests.test_ziwei_phase2c_capabilities -v
```

- [ ] **Step 5: Update registry and minimal public exports**

Export layer builder, source adapters, and view helper; do not export private lookup tables.

- [ ] **Step 6: Run GREEN and capability suite**

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

### Task 7: Pinned iztro 600-Case Public Qualification

**Files:** Create `qualification/ziwei/phase2c/generate_iztro_vectors.mjs`, `public-iztro-flowing-star-vectors.json`, `private-astralium-summary.json`, `tools/qualify_ziwei_phase2c.py`, `tests/test_ziwei_phase2c_qualification.py`.

**Public expected totals:** 600 source combinations, 6120 placements, 0 unexpected mismatch.

- [ ] **Step 1: Write qualification-only Node generator**

The script receives a local built checkout path to pinned iztro, imports its public `star.getHoroscopeStar`, loops:

```javascript
for (const scope of ['decadal', 'yearly', 'monthly', 'daily', 'hourly'])
  for (const stem of stems)
    for (const branch of branches)
      collect(scope, stem, branch, star.getHoroscopeStar(stem, branch, scope));
```

Convert iztro palace-array index (寅起) to canonical Project branch before serializing. Store package version, revision, source file names, and deterministic case ordering. This generator is qualification tooling only and is never imported by Python runtime.

- [ ] **Step 2: Generate fixture from exact pinned revision**

Validation setup:

```bash
git clone https://github.com/SylarLong/iztro.git /tmp/iztro-phase2c
git -C /tmp/iztro-phase2c checkout 814b77e6371e1050cac31bbf674db3c3138fcfde
cd /tmp/iztro-phase2c && npm ci && npm run build
cd "$PROJECT_ROOT"
node qualification/ziwei/phase2c/generate_iztro_vectors.mjs /tmp/iztro-phase2c > qualification/ziwei/phase2c/public-iztro-flowing-star-vectors.json
```

If upstream build command differs at the pinned revision, inspect its package scripts and use the pinned repository's actual build command; do not switch revision or package version to make the build easier.

- [ ] **Step 3: Preserve independent golden anchors**

Fixture/tests must include pinned upstream examples for `getHoroscopeStar("庚", "辰", "decadal")` and `getHoroscopeStar("癸", "卯", "yearly")` independently of the exhaustive loop.

- [ ] **Step 4: Write RED Python qualification tests**

```python
report = run_public_qualification()
self.assertEqual(report["status"], "PASS")
self.assertEqual(report["source_case_count"], 600)
self.assertEqual(report["placement_check_count"], 6120)
self.assertEqual(report["unexpected_mismatch_count"], 0)
```

Also assert fixture contains no private birth data and no excluded star groups.

- [ ] **Step 5: Implement Python qualifier**

Compare Project `place_flowing_stars_for_pair()` exactly on `(scope, base_star, category, target_branch)`. A mismatch is unexpected unless the approved spec explicitly names a profile difference; Phase 2C v1 currently names none.

- [ ] **Step 6: Create private summary as explicit PENDING**

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

- [ ] **Step 7: Run GREEN**

```bash
python tools/qualify_ziwei_phase2c.py --public
python -m unittest tests.test_ziwei_phase2c_qualification tests.test_ziwei_flowing_stars -v
```

Required markers: `IZTRO_FLOWING_STARS_600_600_PASS`, `IZTRO_FLOWING_STARS_0_UNEXPECTED_MISMATCH`.

- [ ] **Step 8: Commit**

```bash
git add qualification/ziwei/phase2c tools/qualify_ziwei_phase2c.py tests/test_ziwei_phase2c_qualification.py
git commit -m "test: qualify Ziwei flowing stars against pinned iztro"
```

---

### Task 8: Documentation, Privacy Summary, and Scope Lock

**Files:** Modify authoritative docs listed in File Map; create `tests/test_ziwei_phase2c_docs.py`.

- [ ] **Step 1: Write docs RED assertions before editing docs**

Require authoritative docs to state: `Phase 2C Ziwei Flowing Stars`, profile `ziwei-flowing-stars-common-v1`, `implemented / experimental / on_demand`, `Project 推導盤面`, Astralium flowing-stars `PENDING`, excluded 歲前／將前十二神, and unchanged v1.2.0 release identity.

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_ziwei_phase2c_docs -v
```

- [ ] **Step 3: Update docs only after product + public qualification GREEN**

`命理推導計算規則.md`: document five source adapters and no recalculation rule. `core/核心提示詞.md`: only invoke flow stars when input precision/source exists. `docs/架構說明.md`: show independent flowing-star layer beside transformation/flying. `CHANGELOG.md`: add `Unreleased｜Phase 2C Ziwei Flowing Stars` above older Unreleased sections. Preserve existing machine-readable headings in version-sync docs.

- [ ] **Step 4: Lock VERSION.md unchanged**

Test exact current release string `Metaphysics Lab Core：**v1.2.0**`; do not edit VERSION.md in this task.

- [ ] **Step 5: Run GREEN and existing docs regression**

```bash
python -m unittest tests.test_ziwei_phase2c_docs -v
python -m unittest discover -s tests -p '*docs*.py'
```

- [ ] **Step 6: Commit**

```bash
git add 命理推導計算規則.md core/核心提示詞.md docs/架構說明.md README.md CHANGELOG.md tests/test_ziwei_phase2c_docs.py
git commit -m "docs: document Phase 2C flowing stars"
```

Include `docs/更新與版本同步.md` only if required by an existing failing docs contract, while preserving old section markers.

---

### Task 9: Final Acceptance, Aggregate Evidence, and Formal Feature Snapshot

**Files:** Create `qualification/ziwei/phase2c/phase2c-summary.json`, `tests/test_ziwei_phase2c_acceptance.py`. Temporary validation branch only: `.github/workflows/phase2c-tdd.yml`, `.github/workflows/phase2c-acceptance.yml`.

- [ ] **Step 1: Write acceptance contract**

Assert: 600 cases, 6120 checks, 0 mismatch, private PENDING (or separately authorized privacy-safe aggregate PASS), `promotion_allowed=false`, flowing_stars implemented/experimental/on_demand, transformations/flying stable unchanged, month/day/hour stems + natal experimental unchanged, VERSION v1.2.0 unchanged, no private raw keys, no Qimen changes, no excluded star leakage.

- [ ] **Step 2: Run focused suite**

```bash
python -m unittest \
  tests.test_ziwei_phase2c_rule_source \
  tests.test_calendar_sexagenary_phase2c \
  tests.test_ziwei_flowing_star_models \
  tests.test_ziwei_flowing_star_sources \
  tests.test_ziwei_flowing_stars \
  tests.test_ziwei_flowing_star_view \
  tests.test_ziwei_phase2c_capabilities \
  tests.test_ziwei_phase2c_qualification \
  tests.test_ziwei_phase2c_docs \
  tests.test_ziwei_phase2c_acceptance -v
```

- [ ] **Step 3: Run full repo regression**

```bash
python -m unittest discover -s tests -p 'test*.py'
```

- [ ] **Step 4: Run Python 3.9 syntax Gate**

```bash
python3.9 -m compileall -q engine tools tests
```

If CI executable is `python`, first assert `python --version` is Python 3.9.x.

- [ ] **Step 5: Run qualification Gate**

```bash
python tools/qualify_ziwei_phase2c.py --public
```

Required markers: `IZTRO_FLOWING_STARS_600_600_PASS`, `IZTRO_FLOWING_STARS_0_UNEXPECTED_MISMATCH`, `PHASE2C_PRIVATE_FLOWING_STARS_PENDING_OK`.

- [ ] **Step 6: Build deterministic privacy-safe summary**

`phase2c-summary.json` may contain only profile/version/revision/status/count/digest/capability-state data. Recursively forbid `full_name`, `full_address`, `hospital`, `birth_datetime`, `raw_birth_input`, `raw_chart`, `raw_payload`, `external_raw`, and private file paths.

- [ ] **Step 7: Add temporary validation workflows on validation branch only**

They run focused suite, full repo, Python 3.9, public qualification, privacy/scope checks. Emit `PHASE2C_ACCEPTANCE_PASS` only after every Gate succeeds.

- [ ] **Step 8: Verify exact-head evidence**

Queued/in-progress is not success. Record exact validation SHA, run IDs, artifact digest, fixture digest, and capability state from the same effective product tree.

- [ ] **Step 9: Create formal `feature/ziwei-flowing-stars-v1` snapshot without temporary workflows**

Formal tree contains product code/tests/docs/spec/plan/qualification evidence, but no `.github/workflows/phase2c-*.yml`.

- [ ] **Step 10: Fresh-validate formal feature snapshot**

Create a temporary validation branch from formal feature, add only validation workflows, rerun all Gates, and prove diff vs feature is exactly those workflow files.

- [ ] **Step 11: Stop at explicit feature→design approval Gate**

Present exact feature SHA, fresh run IDs, 600/600 + 0 mismatch evidence, private status, capability states, and diff scope. Do not merge until the user explicitly approves `feature/ziwei-flowing-stars-v1 → design/ziwei-flowing-stars`.

---

## Stop Conditions

1. Task 0 must PASS before production implementation.
2. Task 1 helpers must exist before `FlowingStarSource` legal-pair validation.
3. Tasks 2–3 must GREEN before placement code.
4. Task 4 pure core + formal layer must GREEN before materialized views/capability flip.
5. Task 7 must reach 600/600 and 0 unexpected mismatch before docs/final acceptance.
6. Validation infrastructure failures and product algorithm failures must be classified separately.
7. `feature → design` and `design → main` require separate explicit approvals after implementation.

## Self-Review Result

- Spec coverage: all twenty spec sections map to Tasks 0–9.
- Dependency ordering fixed: neutral legal-pair helper precedes `FlowingStarSource` validation.
- Display names are fully enumerated; no presentation mapping is left implicit.
- Qualification generator has an exact repo path and pinned-revision execution contract.
- Type consistency: source uses existing `ChartIdentity`; layer uses existing `LayerIdentity`; join compares `chart_id + scope + reference`; month/day/hour consume `ResolvedCycleStem`; decadal consumes `ZiweiDecadalPeriod`.
- Runtime boundary: Node/iztro exists only in qualification tooling.
- Scope boundary: no excluded dynamic star groups, brightness, small-limit, scoring, or interpretation task is present.
- Maturity boundary: only `ziwei.flowing_stars` changes state, and only to Experimental.
- Placeholder scan: no `TBD`, `TODO`, “similar to Task N”, or unspecified implementation step remains.
