# Natal Chart Foundation 04 — Reconciliation, Export & Qualification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 將 Project-native Bazi/Ziwei natal charts 與 Astralium/其他外部盤面收斂到同一 Normalized Natal Model，執行欄位級 reconciliation/authority resolution，輸出 deterministic canonical Markdown，並完成 Phase 2C0 全域 qualification、docs、privacy 與 regression gate。

**Architecture:** 新增 `engine/natal/` 作 cross-system aggregation/export 層；external import 只接收已由上游解析出的 structured external records，不在 deterministic engine 內 OCR/LLM 解析 PDF；reconciliation 保留 External / Project / Resolved 三個 view；Markdown exporter 只序列化 structured facts，不做命理解讀。

**Tech Stack:** Python 3.9-compatible syntax、stdlib dataclasses/enum/json/hashlib/pathlib、existing Bazi/Ziwei models and Phase 2A/2B core、unittest。

**Spec:** `docs/superpowers/specs/2026-08-22-Natal-Chart-Foundation-設計.md`

## Global Constraints

- External raw data與Project raw result永遠各自保留；Resolved View只做選擇，不覆寫來源。
- Reconciliation status固定：`MATCH`, `EQUIVALENT`, `CONFLICT`, `NOT_COMPARABLE`。
- Severity固定：`INFO`, `CAUTION`, `BLOCKING`。
- Project Natal Experimental期間，Astralium若存在且BLOCKING conflict，resolved欄位預設選external；Project結果仍保留。
- Stable後也不得吞掉BLOCKING conflict。
- Canonical exporter不能重算命盤、不能加入身強弱/格局/人生結論等AI推論。
- 共用repo禁止私人raw chart、完整地址與完整出生資料fixture。

---

### Task 1: Define Normalized Natal Model and source-aware field values

**Files:**
- Create: `engine/natal/__init__.py`
- Create: `engine/natal/models.py`
- Create: `engine/natal/errors.py`
- Create: `tests/test_natal_models.py`

**Interfaces:**
- Produces `NatalSource(source_type, source_name, source_version, rule_profile, rule_version, maturity, validation_status)`
- Produces generic `SourcedValue[T](value, source, notes=())`
- Produces `ExternalNatalView(birth, bazi, ziwei, source)`
- Produces `ProjectNatalView(birth, time_basis, bazi, ziwei, source)`
- Produces `ResolvedField(path, status, severity, selected_source, selected_value, external_value, project_value, reason)`
- Produces `ResolvedNatalView(fields: tuple[ResolvedField, ...])`
- Produces `NormalizedNatalChart(identity, external, project, resolved, validation, provenance)`

- [ ] **Step 1: Write immutable model and serialization tests**

```python
def test_normalized_model_keeps_external_and_project_values_separate():
    external = SourcedValue('巳', external_source)
    project = SourcedValue('午', project_source)
    field = ResolvedField('ziwei.ming_palace', 'CONFLICT', 'BLOCKING', 'external', '巳', external, project, 'project_engine_experimental')
    assert field.external_value.value == '巳'
    assert field.project_value.value == '午'
```

- [ ] **Step 2: Run and verify failure**

```bash
python -m unittest tests.test_natal_models -v
```

- [ ] **Step 3: Implement frozen generic/source models**

`to_dict()` must preserve both raw source values and resolved selection. Reject `selected_source` values outside `external`, `project`, `none`.

- [ ] **Step 4: Run tests and commit**

```bash
python -m unittest tests.test_natal_models -v
git add engine/natal tests/test_natal_models.py
git commit -m "feat: define normalized natal model"
```

---

### Task 2: Implement structured external-chart import contract

**Files:**
- Create: `engine/natal/external.py`
- Create: `tests/test_natal_external_import.py`

**Interfaces:**
- Produces `import_external_natal(payload: Mapping[str, object], source: NatalSource) -> ExternalNatalView`
- Accepts only normalized structured payload. PDF/MD extraction remains upstream ChatGPT/tool responsibility.

- [ ] **Step 1: Write Astralium-shaped structured import test**

Use a synthetic fixture with fields:

```text
birth.reported_datetime
birth.place_label
bazi.pillars (optional)
ziwei.ming_palace
ziwei.body_palace
ziwei.five_element_bureau
ziwei.palaces
ziwei.stars
ziwei.birth_transformations
ziwei.decadal_cycles
```

Assert source name/version/classification remain attached.

- [ ] **Step 2: Write partial external chart test**

An external payload may omit Bazi or some Ziwei fields; import succeeds with missing fields absent, enabling `NOT_COMPARABLE` later. It must not synthesize missing stars/palaces.

- [ ] **Step 3: Write invalid-schema tests**

Duplicate palace names, duplicate unique star identities, malformed four pillars, unknown source classification → `invalid_natal_schema`.

- [ ] **Step 4: Implement parser as schema validation only**

Do not parse Markdown strings or PDFs here. Require upper layer to provide normalized mapping.

- [ ] **Step 5: Run tests and commit**

```bash
python -m unittest tests.test_natal_external_import -v
git add engine/natal/external.py tests/test_natal_external_import.py
git commit -m "feat: import structured external natal charts"
```

---

### Task 3: Implement field-level reconciliation statuses and severity rules

**Files:**
- Create: `engine/birth/reconciliation.py`
- Create: `engine/natal/reconciliation.py`
- Create: `tests/test_natal_reconciliation.py`

**Interfaces:**
- Produces enums `ReconciliationStatus`, `ConflictSeverity`
- Produces `compare_scalar(path, external, project, *, equivalent=None) -> ResolvedField`
- Produces `reconcile_natal(external: ExternalNatalView | None, project: ProjectNatalView | None, *, project_maturity: str) -> ResolvedNatalView`

- [ ] **Step 1: Write canonical status tests**

```text
same value → MATCH
19:20 vs 19:16, same target hour branch → EQUIVALENT/INFO
external absent or project absent → NOT_COMPARABLE
巳 vs 午 Ming palace → CONFLICT/BLOCKING
brightness profile difference → CONFLICT/CAUTION
```

- [ ] **Step 2: Write BLOCKING field path matrix**

At minimum mark these paths BLOCKING:

```text
bazi.pillars.year/month/day/hour
birth.effective_hour_branch
ziwei.ming_palace
ziwei.body_palace
ziwei.five_element_bureau
ziwei.major_stars.*.palace
ziwei.transformation_required_stars.*.palace
ziwei.birth_transformations.*
bazi.decadal_direction
ziwei.decadal_cycles.*.palace
```

- [ ] **Step 3: Implement comparison primitives**

For unordered record collections use stable identity keys (`palace name`, `star name`, `transformation type`) before comparing; never compare raw list order as meaning.

- [ ] **Step 4: Implement material-equivalence callback for time views**

A time value can be `EQUIVALENT` only when the target component remains identical (same effective branch and same dependent chart field). Numeric-minute difference alone is not automatically conflict.

- [ ] **Step 5: Run tests and commit**

```bash
python -m unittest tests.test_natal_reconciliation -v
git add engine/birth/reconciliation.py engine/natal/reconciliation.py tests/test_natal_reconciliation.py
git commit -m "feat: reconcile natal chart fields"
```

---

### Task 4: Implement Experimental/Stable authority rules without overwriting raw views

**Files:**
- Modify: `engine/natal/reconciliation.py`
- Modify: `tests/test_natal_reconciliation.py`

**Interfaces:**
- Produces `select_resolved_source(status, severity, external, project, project_maturity) -> tuple[str, object, str]`

- [ ] **Step 1: Write Experimental authority tests**

```text
Project only → select project
Astralium + MATCH → resolved value identical; reason matched
Astralium + BLOCKING conflict + Project experimental → select external
Astralium + CAUTION conflict + Project experimental → keep comparison result; selection policy field-specific, default external when same field exists
```

- [ ] **Step 2: Write Stable authority tests**

Project Stable + external MATCH → Project may be default. Project Stable + BLOCKING conflict → keep conflict and choose Project only if explicit stable policy says default; reason must remain `blocking_conflict_requires_diagnosis`, never `match`.

- [ ] **Step 3: Implement selection as pure function**

Never mutate `ExternalNatalView` or `ProjectNatalView`. `ResolvedField` must carry both source values after selection.

- [ ] **Step 4: Run tests and commit**

```bash
python -m unittest tests.test_natal_reconciliation -v
git add engine/natal/reconciliation.py tests/test_natal_reconciliation.py
git commit -m "feat: add natal authority resolution"
```

---

### Task 5: Build deterministic canonical Markdown exporter

**Files:**
- Create: `engine/natal/export.py`
- Create: `templates/natal/bazi_data_pack.md.tmpl`
- Create: `templates/natal/ziwei_data_pack.md.tmpl`
- Create: `templates/natal/calibration_record.md.tmpl`
- Create: `tests/test_natal_export.py`

**Interfaces:**
- Produces `export_bazi_markdown(chart: NormalizedNatalChart, generated_date: date) -> str`
- Produces `export_ziwei_markdown(chart: NormalizedNatalChart, generated_date: date) -> str`
- Produces `export_calibration_markdown(chart: NormalizedNatalChart, generated_date: date) -> str`

- [ ] **Step 1: Write snapshot-style structural tests**

Require headings:

```text
資料來源
資料分類
Engine / Profile / Rule Version
出生資料
時間校正摘要
Validation / Reconciliation
正式盤面欄位
Provenance 摘要
```

Assert no headings named `AI判斷`, `身強弱`, `喜用神`, `人生結論` are emitted by canonical exporter.

- [ ] **Step 2: Write deterministic-output test**

Same structured input + same `generated_date` must produce byte-identical Markdown. Record ordering must be canonical: Bazi year/month/day/hour; Ziwei `PALACE_NAMES`; stars sorted by catalog sequence; transformations 祿權科忌.

- [ ] **Step 3: Implement minimal template renderer without new template dependency**

Use stdlib string assembly or `str.format` with committed `.tmpl` files. Do not add Jinja dependency for this exporter.

- [ ] **Step 4: Implement UX-level time summary**

If correction does not change chart:

```text
已完成出生地時間校正，未造成時辰／核心盤面變更。
```

If BLOCKING time conflict:

```text
出生時間校正跨越命理邊界；請查看「排盤差異」區塊。
```

Technical minute/profile details remain in provenance section.

- [ ] **Step 5: Run tests and commit**

```bash
python -m unittest tests.test_natal_export -v
git add engine/natal/export.py templates/natal tests/test_natal_export.py
git commit -m "feat: export canonical natal markdown"
```

---

### Task 6: Add end-to-end Mode A / B / C orchestration

**Files:**
- Create: `engine/natal/orchestration.py`
- Create: `tests/test_natal_end_to_end.py`

**Interfaces:**
- Produces `build_project_natal(birth_input, location_provider) -> ProjectNatalView`
- Produces `build_bazi_imported_view(four_pillars_payload, source) -> ExternalNatalView`
- Produces `build_normalized_natal(*, project=None, external=None) -> NormalizedNatalChart`

- [ ] **Step 1: Write Mode A end-to-end test**

Use fake location provider and full structured birth input. Assert Project view contains Bazi + Ziwei charts and source classification `Project 原生盤面`.

- [ ] **Step 2: Write Mode B four-pillars-only test**

Assert Bazi external/imported view succeeds; Ziwei project build is not attempted; status explains missing civil identity rather than guessing a date.

- [ ] **Step 3: Write Mode C external + Project cross-check test**

Provide synthetic Astralium structured external view plus same birth data; assert both views are retained and resolved field statuses are populated.

- [ ] **Step 4: Write missing-field prompt contract data test**

Orchestration returns machine-readable `missing_fields` / `allowed_actions`; it does not emit a natural-language prompt itself. ChatGPT/UI layer can render that data.

- [ ] **Step 5: Implement orchestration with dependency injection**

`build_project_natal` receives `LocationProvider`; unit tests never hit live network. It calls Workstream 01 → Bazi → Ziwei in order and stops on blocking errors.

- [ ] **Step 6: Run tests and commit**

```bash
python -m unittest tests.test_natal_end_to_end -v
git add engine/natal/orchestration.py tests/test_natal_end_to_end.py
git commit -m "feat: orchestrate natal chart workflows"
```

---

### Task 7: Add cross-cutting capability registry checks and preserve Phase 2C boundary

**Files:**
- Create: `engine/natal/capabilities.py`
- Create: `tests/test_natal_capabilities.py`
- Modify: `engine/birth/capabilities.py`
- Modify: `engine/bazi/capabilities.py`
- Modify: `engine/ziwei/capabilities.py`

**Interfaces:**
- Adds `natal.reconciliation`, `natal.markdown_export`
- Registry tests aggregate all Phase 2C0 capability states without duplicating implementation code.

- [ ] **Step 1: Write state matrix test**

Expected initial states:

```text
birth.input_resolution       implemented experimental on_demand 1.0-exp
birth.location_resolution    implemented experimental on_demand 1.0-exp
birth.true_solar_time        implemented experimental on_demand 1.0-exp
bazi.natal_chart             implemented experimental on_demand 1.0-exp
ziwei.natal_chart            implemented experimental on_demand 1.0-exp
natal.reconciliation         implemented stable       on_demand 1.0
natal.markdown_export        implemented stable       on_demand 1.0
ziwei.flowing_stars          planned     None         on_demand None
```

- [ ] **Step 2: Add dependency graph assertions**

`ziwei.natal_chart` depends on `birth.true_solar_time`, `ziwei.transformations`, `ziwei.flying`; `bazi.natal_chart` depends on birth/calendar foundation; `natal.markdown_export` depends on reconciliation.

- [ ] **Step 3: Run capability regression**

```bash
python -m unittest tests.test_natal_capabilities tests.test_ziwei_phase2a_capabilities tests.test_ziwei_phase2b_capabilities -v
```

- [ ] **Step 4: Commit**

```bash
git add engine/natal/capabilities.py engine/birth/capabilities.py engine/bazi/capabilities.py engine/ziwei/capabilities.py tests/test_natal_capabilities.py
git commit -m "feat: register natal foundation capabilities"
```

---

### Task 8: Add privacy, qualification-summary, and exact-scope tests

**Files:**
- Create: `tests/test_natal_privacy.py`
- Create: `tests/test_natal_qualification_summary.py`
- Create: `qualification/natal/phase2c0-summary.json`
- Create: `tools/qualify_natal_phase2c0.py`

**Interfaces:**
- Aggregates Workstream 01/02/03 qualification summaries.
- Final summary contains no raw private chart fields.

- [ ] **Step 1: Write forbidden-key recursive scanner**

Fail on keys:

```text
name
full_name
full_address
hospital
birth_datetime
raw_birth_input
raw_chart
raw_payload
external_raw
```

Allow opaque `case_id`, digest, counts, versions, aggregate field statuses.

- [ ] **Step 2: Write phase-summary schema test**

Required sections:

```text
birth_location_time
bazi_natal
ziwei_natal
reconciliation
markdown_export
regression
privacy
phase2c_boundary
```

- [ ] **Step 3: Implement aggregation tool**

It reads committed/public aggregate summaries plus a local optional private-summary path supplied at runtime. It must write only aggregate counts/digests; private input path/content is never copied.

- [ ] **Step 4: Run tests and commit**

```bash
python -m unittest tests.test_natal_privacy tests.test_natal_qualification_summary -v
git add tests/test_natal_privacy.py tests/test_natal_qualification_summary.py qualification/natal/phase2c0-summary.json tools/qualify_natal_phase2c0.py
git commit -m "test: aggregate Phase 2C0 qualification"
```

---

### Task 9: Reconcile docs, prompts, data classification, and user guidance

**Files:**
- Modify: `core/命理分析作業規範.md`
- Modify: `core/命理推導計算規則.md`
- Modify: `core/核心提示詞.md`
- Modify: `docs/架構說明.md`
- Modify: `docs/快速開始.md`
- Modify: `docs/安裝到ChatGPT-Project.md`
- Modify: `docs/更新與版本同步.md`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Create: `tests/test_phase2c0_docs.py`

**Interfaces:**
- Documents 8 data classes including `Project 原生盤面`.
- User input guidance: sex + Gregorian date + birth time + birth place; only ask missing fields.
- Documents true-solar default qualification target for Ziwei and independent Bazi profile.

- [ ] **Step 1: Write docs assertions before editing docs**

Tests must require these phrases/semantic markers in authoritative docs:

```text
Project 原生盤面
Precision must be earned by input
reported_civil_time
Calendar Resolver 不負責真太陽時
真太陽時＝經度校正＋均時差
Astralium 為可選 external qualification source
External / Project / Resolved
MATCH / EQUIVALENT / CONFLICT / NOT_COMPARABLE
```

And require `紫微流曜` / `ziwei.flowing_stars` remain planned.

- [ ] **Step 2: Run docs tests and verify failure**

```bash
python -m unittest tests.test_phase2c0_docs -v
```

- [ ] **Step 3: Update authoritative docs**

Do not write Project true-solar output as Astralium output. Document Experimental maturity clearly.

- [ ] **Step 4: Add user-facing examples**

Example complete input:

```text
男，1984年3月13日19:20，台北市出生
```

Example missing fields: only ask for missing sex/time. Example ambiguous time: preserve candidate range and explain possible multiple charts.

- [ ] **Step 5: Run docs tests and commit**

```bash
python -m unittest tests.test_phase2c0_docs -v
git add core docs README.md CHANGELOG.md tests/test_phase2c0_docs.py
git commit -m "docs: document Natal Chart Foundation"
```

---

### Task 10: Full acceptance, regression, and evidence markers

**Files:**
- Modify/Create validation workflow only on temporary validation branch during Gate execution; do not merge validation-only workflow if it is not part of normal repo CI.
- No production file changes unless a real defect is found and fixed through its own test cycle.

**Interfaces:**
- Emits markers from master implementation plan only after successful assertions.

- [ ] **Step 1: Run all focused Phase 2C0 suites**

```bash
python -m unittest \
  tests.test_birth_models \
  tests.test_birth_input_resolution \
  tests.test_birth_location \
  tests.test_birth_calendar_integration \
  tests.test_birth_time_views \
  tests.test_bazi_natal_models \
  tests.test_bazi_natal \
  tests.test_bazi_time_profile_comparison \
  tests.test_bazi_decadal_luck \
  tests.test_ziwei_natal_models \
  tests.test_ziwei_natal_time \
  tests.test_ziwei_natal_palaces \
  tests.test_ziwei_natal_stars \
  tests.test_ziwei_natal_brightness \
  tests.test_ziwei_natal_decadal \
  tests.test_ziwei_natal_integration \
  tests.test_natal_models \
  tests.test_natal_external_import \
  tests.test_natal_reconciliation \
  tests.test_natal_export \
  tests.test_natal_end_to_end \
  tests.test_natal_capabilities \
  tests.test_natal_privacy \
  tests.test_phase2c0_docs -v
```

- [ ] **Step 2: Run Calendar/Bazi/Ziwei regressions and full repository**

```bash
python -m unittest discover -s tests -p 'test_calendar*.py' -v
python -m unittest tests.test_project_bazi_calendar -v
python -m unittest discover -s tests -p 'test_ziwei*.py' -v
python -m unittest discover -s tests -v
```

- [ ] **Step 3: Run syntax and compile gates**

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

- [ ] **Step 4: Run live/external qualification separately**

Run location-provider live qualification, Bazi reference qualification, pinned iztro Ziwei qualification, and local private Astralium aggregate qualification. Infrastructure outage must be reported distinctly and blocks formal acceptance until rerun succeeds; it must not be relabeled as algorithm FAIL/PASS.

- [ ] **Step 5: Verify scope and privacy**

```bash
git diff --name-only <feature-base-sha>..HEAD
```

Assert no Qimen implementation, no `ziwei.flowing_stars` implementation, no private raw chart, no validation-only workflow intended to remain temporary.

- [ ] **Step 6: Produce phase summary and final markers**

Only after all gates pass, emit `PHASE2C0_ACCEPTANCE_PASS`; preserve Bazi/Ziwei natal maturity as Experimental unless a separate promotion decision is explicitly approved.

- [ ] **Step 7: Commit any normal qualification summaries**

```bash
git add qualification/natal qualification/bazi/natal qualification/ziwei/natal
git commit -m "test: record Phase 2C0 acceptance evidence"
```

If no tracked evidence changed, do not create an empty commit.