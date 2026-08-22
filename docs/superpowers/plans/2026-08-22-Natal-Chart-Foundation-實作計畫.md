# Natal Chart Foundation v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立 Phase 2C0，讓使用者只提供性別、陽曆出生年月日、出生時間與出生地，即可建立可追溯的 Bazi / Ziwei Project 原生盤面；同時保留 Astralium 等外部盤面作欄位級校驗，最後輸出 canonical Markdown data pack。

**Architecture:** 將大規格拆成四個獨立 workstream：Birth/Location/Time Foundation → Bazi Natal → Ziwei Natal → Reconciliation/Exporter/Qualification。Calendar Resolver 維持 neutral；真太陽時與命理 school policy 留在 birth/natal adapter；Ziwei Transformation/Flying 重用 Phase 2A stable core；Phase 2C flowing stars 維持 planned。

**Tech Stack:** Python 3.9-compatible syntax、`lunar-python==1.4.8`、`tzdata==2026.3`、`geopy==2.5.0`、`timezonefinder==8.2.0`、stdlib `zoneinfo` / `dataclasses` / `unittest`；public Ziwei qualification 繼續使用 pinned iztro `814b77e6371e1050cac31bbf674db3c3138fcfde`，不作 runtime dependency。

**Spec:** `docs/superpowers/specs/2026-08-22-Natal-Chart-Foundation-設計.md`

## Global Constraints

- Base 必須是 `main` commit `dcb70947f53451c0a4760dc6231f95b901ef495e` 加上已批准的 design branch 文件；implementation 不直接寫 `main`。
- `reported_civil_time` 永遠保留，不得被真太陽時覆寫。
- Calendar Resolver 不做真太陽時、不猜地點、不套 Bazi/Ziwei 日界。
- 輸入不足或不唯一只能 `ask` / `keep_candidates` / `downgrade`；不得補假日期、假時間、假 timezone。
- Location Resolver 解析結果必須保存 coordinates、IANA timezone、provider/provenance；底層 chart engine 不接受未解析地名。
- Ziwei v1 true-solar target 固定為「經度校正 + equation of time」，第一版 Experimental；不得宣稱為唯一紫微標準。
- Bazi default 先採 normalized civil time + 23:00 day boundary，true-solar 僅作 candidate qualification；material difference 才形成 conflict。
- Project Natal Engine 第一版 `implemented / experimental / on_demand`；未達 qualification gate 不升 stable/default。
- Astralium raw/private chart 不進共用 repo；只保存 aggregate summary、case id、digest、版本與 pass/fail counts。
- Canonical Markdown 只能由 validated structured model deterministic export，不讓 LLM 重算盤面事實。
- `ziwei.flowing_stars` 必須維持 `planned`；Phase 2C0 不得偷做 moving stars。
- 每個 task 先寫 failing test，再最小實作，再跑 focused + regression tests，再 commit。
- 每個 workstream 完成後做 reviewer gate；任何 gate FAIL 停止後續 workstream。

---

## Workstream Decomposition

本 spec 涵蓋四個可獨立拒絕／接受的 subsystem，因此不使用單一巨型 execution plan。正式執行順序如下：

1. `docs/superpowers/plans/2026-08-22-Natal-Chart-Foundation-01-Birth-Location-Time.md`
   - Birth structured input contract
   - Precision / candidate handling
   - LocationProvider + default geocoder adapter
   - coordinates → IANA timezone
   - true-solar time views
   - Calendar validation propagation

2. `docs/superpowers/plans/2026-08-22-Natal-Chart-Foundation-02-Bazi-Natal.md`
   - Bazi natal models/profile
   - four pillars / day master / hidden stems / ten gods / elemental facts
   - Bazi civil-vs-true-solar comparison
   - Da Yun direction / start / sequence
   - Bazi qualification

3. `docs/superpowers/plans/2026-08-22-Natal-Chart-Foundation-03-Ziwei-Natal.md`
   - Ziwei natal models/profile
   - palace skeleton / palace stems / five-element bureau
   - 14 major stars + transformation-required stars + selected auxiliary/malefic catalog
   - brightness profile
   - life/body master + decadal cycles
   - Phase 2A Transformation/Flying integration
   - public/private qualification summaries

4. `docs/superpowers/plans/2026-08-22-Natal-Chart-Foundation-04-Reconciliation-Export-Qualification.md`
   - External / Project / Resolved views
   - field-level MATCH / EQUIVALENT / CONFLICT / NOT_COMPARABLE
   - INFO / CAUTION / BLOCKING
   - Experimental authority rule
   - canonical Markdown exporter
   - end-to-end workflow / capability registry / docs / privacy / full regression

---

## Execution Branching and Gates

### Gate 0 — exact design baseline

- [ ] Confirm `design/natal-chart-foundation` contains the approved spec and plan documents only relative to `main` before implementation begins.
- [ ] Record exact design HEAD SHA.
- [ ] Create `feature/natal-chart-foundation-v1` from that exact SHA.
- [ ] Never implement directly on `design/natal-chart-foundation`.

Expected check:

```bash
git diff --name-only dcb70947f53451c0a4760dc6231f95b901ef495e..design/natal-chart-foundation
```

Expected before feature implementation: only approved `docs/superpowers/specs/...Natal-Chart-Foundation...` and `docs/superpowers/plans/...Natal-Chart-Foundation...` files.

### Gate 1 — Workstream 01 accepted

Required focused suites:

```bash
python -m unittest \
  tests.test_birth_models \
  tests.test_birth_input_resolution \
  tests.test_birth_location \
  tests.test_birth_time_views \
  tests.test_birth_calendar_integration -v
```

Plus existing Calendar suite:

```bash
python -m unittest discover -s tests -p 'test_calendar*.py' -v
```

Blocking failures: ambiguity silently resolved, false timezone, lost `reported_civil_time`, true-solar applied inside Calendar Resolver, Python 3.9 incompatibility.

### Gate 2 — Workstream 02 accepted

Required focused suites:

```bash
python -m unittest \
  tests.test_bazi_natal_models \
  tests.test_bazi_natal \
  tests.test_bazi_decadal_luck \
  tests.test_bazi_natal_qualification -v
```

Plus current Bazi regression:

```bash
python -m unittest tests.test_project_bazi_calendar -v
```

Blocking failures: four-pillar mismatch on locked baseline vectors, hidden-stem/ten-god mismatch, silently replacing civil profile with true-solar result, inconsistent Da Yun direction/start contract.

### Gate 3 — Workstream 03 accepted

Required focused suites:

```bash
python -m unittest \
  tests.test_ziwei_natal_models \
  tests.test_ziwei_natal_palaces \
  tests.test_ziwei_natal_stars \
  tests.test_ziwei_natal_brightness \
  tests.test_ziwei_natal_decadal \
  tests.test_ziwei_natal_integration \
  tests.test_ziwei_natal_qualification -v
```

Plus all existing Ziwei regression tests:

```bash
python -m unittest discover -s tests -p 'test_ziwei*.py' -v
```

Blocking failures: incomplete transformation-required star catalog, non-48 natal flying graph, Phase 2A/2B maturity regression, `ziwei.flowing_stars` becoming executable, private raw chart committed.

### Gate 4 — Workstream 04 accepted

Required focused suites:

```bash
python -m unittest \
  tests.test_natal_external_import \
  tests.test_natal_reconciliation \
  tests.test_natal_export \
  tests.test_natal_end_to_end \
  tests.test_natal_capabilities \
  tests.test_natal_privacy -v
```

Full repository:

```bash
python -m unittest discover -s tests -v
```

Additional source checks:

```bash
python -m compileall -q engine tests tools
python - <<'PY'
import ast
from pathlib import Path
for root in ('engine', 'tests', 'tools'):
    for path in Path(root).rglob('*.py'):
        ast.parse(path.read_text(encoding='utf-8'), feature_version=(3, 9))
print('PYTHON39_SYNTAX_PASS')
PY
```

### Gate 5 — feature exact-head acceptance

- [ ] Run live/default LocationProvider qualification separately from deterministic unit tests; a network/provider outage is infrastructure FAIL, not chart-algorithm FAIL.
- [ ] Run Bazi public/reference qualification and save aggregate summary.
- [ ] Run Ziwei pinned iztro public qualification and Astralium private aggregate qualification.
- [ ] Assert private raw payload is absent from git diff.
- [ ] Assert `ziwei.flowing_stars` remains planned/non-executable.
- [ ] Assert no Qimen scope changes.
- [ ] Assert VERSION is not promoted merely because implementation exists.
- [ ] Record exact feature HEAD and validation evidence.

### Gate 6 — feature → design

Only after explicit user approval of feature integration:

- [ ] Create formal PR `feature/natal-chart-foundation-v1` → `design/natal-chart-foundation`.
- [ ] Merge with expected head SHA lock.
- [ ] Re-run exact design-merge-SHA post-merge validation.
- [ ] Close validation-only PRs unmerged.

### Gate 7 — design → main

Requires a second, separate explicit user approval:

- [ ] Freshly verify `main` and `design` exact SHAs and divergence.
- [ ] Create formal design → main PR.
- [ ] Validate formal diff scope.
- [ ] Merge only after explicit design → main approval.
- [ ] Re-run exact main merge SHA post-merge validation.
- [ ] Close validation-only branches/PRs unmerged.

---

## Promotion Rule

Phase 2C0 feature completion and capability promotion are separate decisions.

Initial runtime state:

```text
birth.input_resolution    implemented / experimental-or-stable-by-tests / on_demand
birth.location_resolution implemented / experimental / on_demand
birth.true_solar_time     implemented / experimental / on_demand
bazi.natal_chart          implemented / experimental / on_demand
ziwei.natal_chart         implemented / experimental / on_demand
natal.reconciliation      implemented / stable-if-contract-tests-pass / on_demand
natal.markdown_export     implemented / stable-if-schema-tests-pass / on_demand
```

`bazi.natal_chart` and `ziwei.natal_chart` may become `stable / default` only in a later explicit promotion change after qualification evidence covers the required boundary matrix. A successful Phase 2C0 implementation PR alone must not silently promote them.

---

## Final Acceptance Markers

The final validation workflow should emit these machine-searchable markers only after all corresponding assertions pass:

```text
BIRTH_INPUT_PRECISION_PASS
LOCATION_RESOLUTION_PASS
TRUE_SOLAR_TIME_PROFILE_PASS
CALENDAR_VALIDATION_PROPAGATION_PASS
BAZI_NATAL_CORE_PASS
BAZI_TIME_PROFILE_COMPARISON_PASS
BAZI_DECadal_LUCK_PASS
ZIWEI_NATAL_PALACE_PASS
ZIWEI_NATAL_STAR_CATALOG_PASS
ZIWEI_NATAL_BRIGHTNESS_PASS
ZIWEI_NATAL_DECadal_PASS
ZIWEI_PHASE2A_REUSE_PASS
NATAL_RECONCILIATION_PASS
NATAL_MARKDOWN_EXPORT_PASS
PRIVATE_NATAL_PRIVACY_PASS
PHASE2C_FLOWING_STARS_STILL_PLANNED_PASS
PYTHON39_SYNTAX_PASS
FULL_REGRESSION_PASS
PHASE2C0_ACCEPTANCE_PASS
```

Do not emit an acceptance marker early or from a skipped test path.