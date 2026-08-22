# AI Distribution Pack v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 將目前 Metaphysics Lab 模組化工程發布成適合 ChatGPT／Claude Project、手機優先、AI-first 的可攜式使用包：對外只有單一 `metaphysics_lab.py` runtime、固定 AI contract Markdown 與個別私人 Case Markdown；正常演算法升級只需替換 Python。

**Architecture:** Canonical truth 仍留在既有 `engine/**`、`core/**`、`templates/**`。新增 `engine/distribution/**` 作高階 action / schema / export adapter；新增 deterministic build tool，將 Metaphysics Lab 自有 Python modules 與必要 templates 嵌入單一 `.py` artifact。固定 Project Contract 不保存快速變動的 capability matrix；runtime 以現有 capability registries 自述目前能力。AI host 可執行 Python 時直接呼叫；不能執行時使用相同 action contract 的本機 CLI fallback。

**Tech Stack:** Python 3.9-compatible syntax、stdlib `argparse/json/ast/importlib/base64/zlib/tempfile/pathlib/hashlib`、existing `engine/birth` / `engine/calendar` / `engine/bazi` / `engine/ziwei` / `engine/natal`、`unittest`、GitHub Actions temporary validation workflow。第三方 runtime dependencies 保持既有 pinned `lunar-python==1.4.8`、`tzdata==2026.3`、`geopy==2.5.0`、`timezonefinder==8.2.0`；本階段不 vendor 未審查第三方 code。

**Spec:** `docs/superpowers/specs/2026-08-22-AI-Distribution-Pack-設計.md`

## Global Constraints

- Execution begins from approved `design/ai-distribution-pack` exact head in a new `feature/ai-distribution-pack-v1` branch; never implement directly on `main` or design.
- Existing Metaphysics algorithms stay canonical in modular `engine/**`; generated `metaphysics_lab.py` never becomes a second hand-maintained engine.
- Project Contract v1 = `1.0`; Runtime API schema v1 = `1.0`; Case schema v1 = `1.0`; distribution runtime implementation version starts `1.0-exp` and does not alter formal `VERSION.md` release identity.
- `PROJECT_INSTRUCTIONS.md` and `METAPHYSICS_CORE.md` contain long-lived AI governance/workflow only. Do not embed current Phase labels, capability state tables, qualification counts, oracle revisions, current star catalogs, or current rule profiles.
- Runtime capability truth is derived from the existing canonical registries: `engine/birth/capabilities.py`, `engine/bazi/capabilities.py`, `engine/natal/capabilities.py`, `engine/ziwei/capabilities.py`. Do not maintain a second capability table by hand.
- Full natal / forecast / cross-system analysis recommends High reasoning; Medium is minimum recommended; exact model names are deploy-time README guidance only.
- Python performs deterministic validation/calculation/serialization only; never perform free-form metaphysical interpretation or decision advice inside Python.
- AI-first is the primary UX. Local CLI is an equal-contract fallback, not a separate algorithm path.
- A host that cannot execute Python must fail closed; no response may claim a calculation was run without execution evidence.
- The single-file artifact bundles only Metaphysics Lab-owned source/templates. Third-party dependencies remain external unless a later license/size/portability gate explicitly approves vendoring.
- `runtime_info` must work without importing heavy calculation/location modules and must report dependency availability machine-readably.
- Network geocoding is optional. `build_natal` must support pre-resolved latitude / longitude / IANA timezone with provenance so an AI host can avoid Nominatim.
- Private Case data is never committed to the shared repo. Tests use public/synthetic fixtures only.
- Main user flow never requires ZIP extraction. GitHub Release assets are individually downloadable.
- Case permanent changes produce a replacement `.md` file; the AI must identify which old Project file to replace. ZIP remains backup-only.
- Existing Experimental capabilities remain Experimental; no Stable promotion, Astralium qualification completion, tag, GitHub Release, or `VERSION.md` bump occurs in this plan.
- Every code task follows RED → inspect expected failure → minimal GREEN → focused regression → commit. Final acceptance runs full repository regression and Python 3.9 compile checks.

---

## File Map

**Create:**
- `core/AI工作流程.md`
- `engine/distribution/__init__.py`
- `engine/distribution/constants.py`
- `engine/distribution/errors.py`
- `engine/distribution/manifest.py`
- `engine/distribution/dependencies.py`
- `engine/distribution/natal.py`
- `engine/distribution/forecast.py`
- `engine/distribution/case_pack.py`
- `engine/distribution/runtime.py`
- `templates/case/00_case_index.md.tmpl`
- `templates/case/01_core_summary.md.tmpl`
- `templates/case/02_calibration.md.tmpl`
- `templates/case/03_bazi.md.tmpl`
- `templates/case/04_ziwei.md.tmpl`
- `templates/case/05_verified_events.md.tmpl`
- `templates/case/06_year_tracking.md.tmpl`
- `templates/case/07_question_tracking.md.tmpl`
- `templates/case/08_decisions.md.tmpl`
- `tools/build_ai_distribution.py`
- `dist/ai/metaphysics_lab.py` — generated artifact
- `dist/ai/METAPHYSICS_CORE.md` — generated artifact
- `dist/ai/PROJECT_INSTRUCTIONS.md` — generated artifact
- `tests/test_ai_contract_docs.py`
- `tests/test_distribution_runtime_info.py`
- `tests/test_distribution_natal.py`
- `tests/test_distribution_forecast.py`
- `tests/test_distribution_case_pack.py`
- `tests/test_ai_distribution_build.py`
- `tests/test_ai_distribution_bundle.py`
- `tests/test_ai_distribution_docs.py`
- `tests/test_ai_distribution_acceptance.py`

**Modify:**
- `core/核心提示詞.md`
- `core/命理分析作業規範.md`
- `engine/natal/orchestration.py`
- `README.md`
- `docs/快速開始.md`
- `docs/安裝到ChatGPT-Project.md`
- `docs/更新與版本同步.md`
- `CHANGELOG.md`

**Do not modify for runtime feature semantics:**
- `engine/bazi/calendar.py`
- `engine/ziwei/transformations.py`
- `engine/ziwei/flying.py`
- `engine/ziwei/fine_cycle_stems.py`
- `engine/ziwei/flowing_stars.py`
- `VERSION.md`

---

### Task 0: Project Contract Stability Gate

**Files:** Create `core/AI工作流程.md`, `tests/test_ai_contract_docs.py`; modify `core/核心提示詞.md`, `core/命理分析作業規範.md`.

**Purpose:** Remove fast-changing runtime facts from fixed AI contract while preserving the actual analysis governance.

- [ ] Write RED tests asserting both fixed contract sources preserve: eight evidence classes, `Precision must be earned by input`, External / Project / Resolved, blind forecast then event calibration, Experimental evidence downgrade, multi-person isolation, high-risk limits, and the requirement to query runtime capability state.
- [ ] Add RED tests forbidding fixed contract strings that encode current dynamic state, including current Phase labels, `ziwei.flowing_stars = planned`, `ziwei.flowing_stars = implemented`, qualification case counts, pinned oracle revisions, and statements that a specific capability is permanently Stable/Experimental.
- [ ] Run: `python -m unittest tests.test_ai_contract_docs -v` and confirm expected RED because current files hard-code Phase/capability state.
- [ ] Create `core/AI工作流程.md` with stable workflows: first run, build/validate natal, future forecast two-stage isolation, permanent record update, runtime unavailable fallback, capability routing from `runtime_info`, file replacement UX.
- [ ] Refactor `core/核心提示詞.md` to become Project Contract source. Replace hard-coded current capability details with rules: query current runtime manifest; never run unimplemented capability; downgrade Experimental; preserve provenance.
- [ ] Refactor `core/命理分析作業規範.md` similarly. Keep domain boundaries and evidence rules; remove current Phase/capability table and false/stale `flowing_stars planned` statements.
- [ ] GREEN: `python -m unittest tests.test_ai_contract_docs -v`.
- [ ] Focused regression: `python -m unittest tests.test_ziwei_phase2c_docs tests.test_natal_export -v` if those modules exist; otherwise run all existing docs/natal export tests discovered by unittest.
- [ ] Commit: `docs: stabilize AI project contract`.

**Required behavior snippet:**

```text
涉及目前 capability implementation / maturity / routing / rule_version / qualification 時：
1. 先讀當前 metaphysics_lab.py runtime_info。
2. 以 runtime manifest 為目前執行真相。
3. 固定核心規範只決定如何使用該狀態，不自行保存狀態快照。
```

---

### Task 1: Runtime Manifest and Dependency Doctor

**Files:** Create `engine/distribution/{__init__,constants,errors,manifest,dependencies,runtime}.py`, `tests/test_distribution_runtime_info.py`.

**Public constants:**

```python
PROJECT_CONTRACT_VERSION = "1.0"
RUNTIME_SCHEMA_VERSION = "1.0"
CASE_SCHEMA_VERSION = "1.0"
DISTRIBUTION_RUNTIME_VERSION = "1.0-exp"
```

**Public dispatcher contract:**

```python
def dispatch(action: str, payload: Mapping[str, object] | None = None) -> dict:
    ...
```

Implementation must use Python 3.9-compatible `Optional[...]`, not PEP 604 in production source.

**Envelope:**

```json
{"ok": true, "action": "runtime_info", "runtime_version": "1.0-exp", "data": {...}}
```

or

```json
{"ok": false, "action": "...", "runtime_version": "1.0-exp", "error": {"code": "...", "message": "...", "details": {...}}}
```

- [ ] Write RED tests for `runtime_info`: version fields, supported actions, aggregated capabilities, `ziwei.flowing_stars` matching canonical registry, and dependency status for all four pinned external packages.
- [ ] Add a RED test monkeypatching dependency detection to missing `geopy`/`timezonefinder`; `runtime_info` must still return `ok=True` and mark those dependencies unavailable.
- [ ] Implement `manifest.py` without importing `engine.ziwei` package. Read canonical capability registry source files and parse `_CAPABILITIES` using `ast.parse` + `ast.literal_eval`; reject non-literal/duplicate capability IDs.
- [ ] Implement `dependencies.py` using `importlib.util.find_spec` and `importlib.metadata.version` without importing packages. Report `installed`, `version`, `expected_version`, `matches_pin`, `role`, `required_for`.
- [ ] Implement `runtime.py` dispatcher with only `runtime_info` active initially; unknown actions return structured `unsupported_action`.
- [ ] Ensure `runtime_info` does not import `engine.calendar`, `engine.birth.location`, or `engine.ziwei` package initializers.
- [ ] GREEN: `python -m unittest tests.test_distribution_runtime_info -v`.
- [ ] Focused regression: capability registry tests for birth/bazi/natal/ziwei.
- [ ] Commit: `feat: add self-describing distribution runtime`.

---

### Task 2: High-Level Natal Actions and Pre-resolved Location

**Files:** Create `engine/distribution/natal.py`, `tests/test_distribution_natal.py`; modify `engine/natal/orchestration.py`, `engine/distribution/runtime.py`.

**Purpose:** `build_natal` must work with either current network location provider path or a supplied resolved location, so AI hosts are not forced to have geocoding dependencies/network.

**Input example:**

```json
{
  "birth": {
    "sex": "male",
    "birth_date": "1984-03-13",
    "birth_time": "19:20",
    "birth_place": "台北市"
  },
  "resolved_location": {
    "canonical_name": "Taipei City, Taiwan",
    "latitude": 25.033,
    "longitude": 121.5654,
    "timezone": "Asia/Taipei",
    "provider_name": "ai_host",
    "provider_version": "user-confirmed",
    "provider_reference": null
  }
}
```

- [ ] Write RED tests that incomplete birth payload returns the existing machine-readable `missing_fields` / `allowed_actions` rather than an exception.
- [ ] Write RED test for `build_natal` with pre-resolved location and no geopy/timezonefinder usage; assert Project Bazi/Ziwei facts, source classification, time basis, runtime version, and no free-form interpretation.
- [ ] Write RED test for `reconcile_natal` with synthetic external structured chart, asserting External / Project / Resolved preservation and conflict status.
- [ ] Modify `build_project_natal` compatibly to accept either existing `location_provider` or keyword `resolved_location: ResolvedBirthPlace`; exactly one path is used. Existing positional callers must remain valid.
- [ ] Add strict constructor/validator in distribution natal adapter for pre-resolved location: coordinates in range, non-empty canonical name/timezone/provider, timezone validated by Calendar Resolver when calculation runs.
- [ ] Implement `build_natal` action. If neither pre-resolved location nor an explicitly enabled network provider is available, return `location_resolution_required` with required fields; do not guess.
- [ ] Implement `reconcile_natal` action using existing `import_external_natal` and `build_normalized_natal`; source metadata is supplied explicitly in payload.
- [ ] Add dispatcher routes.
- [ ] GREEN: `python -m unittest tests.test_distribution_natal -v`.
- [ ] Regression: existing birth/location/calendar/natal/orchestration/export/reconciliation tests.
- [ ] Commit: `feat: add portable natal runtime actions`.

---

### Task 3: Forecast Context Action

**Files:** Create `engine/distribution/forecast.py`, `tests/test_distribution_forecast.py`; modify `engine/distribution/runtime.py`.

**Purpose:** Give AI one deterministic action that materializes only the time layers requested for a forecast, while leaving interpretation to AI.

**Input contract:**

```json
{
  "normalized_natal": {...},
  "target": {"civil_datetime": "2026-09-15T14:30:00", "timezone": "Asia/Taipei"},
  "requested_scopes": ["yearly", "monthly"],
  "ziwei_decadal_index": 5
}
```

**Output sections:**

```text
bazi
calendar_context_summary
ziwei.yearly
ziwei.monthly
ziwei.daily        only when requested
ziwei.hourly       only when requested
ziwei.decadal      only when requested and index supplied
provenance
confidence_constraints
```

- [ ] Write RED tests for a synthetic normalized natal fixture: yearly+monthly request must not compute daily/hourly; each included layer carries scope/reference/classification/maturity.
- [ ] RED test daily/hourly at 23:xx to prove fine-cycle resolver keeps its own `late_zi_forward-v1` boundary and Calendar Resolver stays neutral.
- [ ] RED test flowing stars materialize from the same resolved source as fine-cycle transformation/flying for monthly/daily/hourly; no second stem resolver.
- [ ] RED test decadal request reconstructs selected `ZiweiDecadalPeriod` from stored deterministic natal data and uses its `stem_branch`.
- [ ] RED test BLOCKING natal conflict or missing Project Ziwei facts returns structured `forecast_basis_blocked`, not partial invented output.
- [ ] Implement helper to reconstruct a deterministic `ChartIdentity`, natal palace records and `StarLocationIndex` from stored Project natal facts. The identity must be stable for identical stored facts and must not claim to be the original in-memory Phase 2C0 chart object.
- [ ] Use existing `engine.bazi.calendar.project_derived` for Bazi target context.
- [ ] Use `resolve_calendar` once per target; then reuse that `CalendarContext` for Ziwei monthly/daily/hourly stem resolution.
- [ ] For monthly/daily/hourly, call existing `resolve_*_stem` → `build_fine_cycle_layer` → matching `source_from_*` → `build_flowing_star_layer` → `materialize_flowing_star_layer`.
- [ ] For yearly, use `source_from_yearly`; use canonical transformation profile if a yearly transformation layer is requested by current runtime capabilities; do not borrow Bazi Li-Chun year.
- [ ] For decadal, use stored decadal `stem_branch`; never recalculate from birth input.
- [ ] Serialize dataclasses/enums/mappings to stable JSON-safe structures; output no interpretation.
- [ ] GREEN: `python -m unittest tests.test_distribution_forecast -v`.
- [ ] Regression: existing fine-cycle, flowing-star, transformation/flying tests.
- [ ] Commit: `feat: add deterministic forecast context action`.

---

### Task 4: Case Schema and Nine-file Markdown Export

**Files:** Create `engine/distribution/case_pack.py`, nine `templates/case/*.tmpl`, `tests/test_distribution_case_pack.py`; modify `engine/distribution/runtime.py`.

**Canonical filenames:**

```text
00_專案索引.md
01_命盤核心摘要.md
02_命盤資料校驗紀錄.md
03_八字結構化資料包.md
04_紫微基礎資料包.md
05_驗證事件紀錄.md
06_流年追蹤紀錄.md
07_問事追蹤紀錄.md
08_重大決策紀錄.md
```

**Front matter minimum:**

```text
case_schema_version
project_contract_version
record_type
subject_id
created_at
last_updated_at
last_modified_by
runtime_version_if_applicable
source_classification
mutation_policy
```

- [ ] Write RED golden test: fixed normalized natal + fixed timestamp + fixed subject id produces exactly nine names and byte-identical Markdown on repeated export.
- [ ] RED test every document has all required front-matter fields and `subject_id` is opaque/stable; no real-name requirement.
- [ ] RED test `03`/`04` contain deterministic facts/provenance but not free-form fortune interpretation; reuse existing natal export functions where possible instead of duplicating their ordering logic.
- [ ] RED test initial `05`-`08` tracking files are valid empty records and do not fabricate events/forecasts/decisions.
- [ ] RED incremental mutation test: appending one verified event returns only `05_驗證事件紀錄.md`; `01`-`04` byte content is untouched.
- [ ] RED immutable-history test: attempting to replace an existing `blind_forecast` body in `06`/`07` is rejected with `immutable_blind_forecast`.
- [ ] Implement a small front-matter parser/renderer with stdlib only; do not add PyYAML.
- [ ] Implement `export_case_markdown` action taking deterministic normalized natal plus optional AI-supplied labeled analysis sections. AI text is stored only under an explicit `命理推論` section and never reclassified as fact.
- [ ] Implement `validate_case` for filename set, schema compatibility, required metadata, duplicate subject mismatch, and record-type/filename matching.
- [ ] Implement `migrate_case`: v1 same-schema returns `compatible/no_change`; future migration dispatch shape exists, but no invented migration path.
- [ ] Implement `update_case_record` internal/action helper for append-first `05`-`08`, returning `{changed_files: {filename: text}}` only.
- [ ] GREEN: `python -m unittest tests.test_distribution_case_pack -v`.
- [ ] Regression: `tests.test_natal_export` and current template tests.
- [ ] Commit: `feat: add portable case markdown pack`.

---

### Task 5: Deterministic AI Distribution Build

**Files:** Create `tools/build_ai_distribution.py`, `tests/test_ai_distribution_build.py`, generated `dist/ai/*`.

**Build products:**

```text
dist/ai/metaphysics_lab.py
dist/ai/METAPHYSICS_CORE.md
dist/ai/PROJECT_INSTRUCTIONS.md
```

**Source rules:**
- `PROJECT_INSTRUCTIONS.md` = exact normalized build from `core/核心提示詞.md`.
- `METAPHYSICS_CORE.md` = stable sections from `core/AI工作流程.md` + `core/命理分析作業規範.md`, with source markers. It must not include `命理推導計算規則.md` or dynamic capability snapshots.
- `metaphysics_lab.py` = generated bundle containing all Metaphysics Lab-owned runtime Python sources required by `engine/distribution` and necessary templates/resources; no third-party package source.

- [ ] RED test running builder twice yields byte-identical three artifacts for same source tree/build metadata.
- [ ] RED test fixed MD artifacts do not contain forbidden dynamic strings (`Phase 2C`, qualification counts, current oracle hash, current capability matrix snippets).
- [ ] RED test generated Python contains build/source digest metadata and no absolute local path.
- [ ] Implement source discovery rooted at repo: include `engine/**/*.py` and required `templates/**/*.tmpl`; exclude tests, qualification raw data, docs, private files, caches.
- [ ] Encode payload as deterministic sorted-path JSON → UTF-8 → zlib → base64. Record per-file SHA256 and aggregate source digest.
- [ ] Generated bootstrap exposes:

```python
def dispatch(action, payload=None): ...
```

and CLI:

```text
python metaphysics_lab.py runtime-info [--pretty]
python metaphysics_lab.py request --input request.json [--pretty]
python metaphysics_lab.py request --input - [--pretty]
```

- [ ] `runtime-info` path must not unpack/import full engine; bundle may embed a precomputed manifest and dependency doctor logic in bootstrap.
- [ ] Non-manifest actions unpack owned sources/resources into a temporary directory, prepend it to `sys.path`, lazily import `engine.distribution.runtime`, then call the same dispatcher.
- [ ] Build tool supports `--output-dir` and `--check`. `--check` exits nonzero if committed `dist/ai` differs from deterministic rebuild.
- [ ] Generate and commit `dist/ai/*` from the feature source.
- [ ] GREEN: `python -m unittest tests.test_ai_distribution_build -v` and `python tools/build_ai_distribution.py --check`.
- [ ] Commit: `build: generate mobile-first AI distribution assets`.

---

### Task 6: Bundled Runtime Parity and CLI Fallback

**Files:** Create `tests/test_ai_distribution_bundle.py`; modify build/bootstrap/runtime only as required by failures.

- [ ] RED parity test: modular `engine.distribution.runtime.dispatch("runtime_info", {})` equals generated single-file `runtime-info` normalized JSON except allowed build-artifact metadata fields.
- [ ] RED parity test for one deterministic natal request using pre-resolved location; modular result equals bundled result.
- [ ] RED parity test for one forecast context request (monthly + daily or equivalent public fixture); modular result equals bundled result.
- [ ] RED parity test for case export filenames/content at fixed timestamp.
- [ ] RED subprocess test `python dist/ai/metaphysics_lab.py request --input -` reads JSON stdin and returns one JSON object with exit code 0 on logical success.
- [ ] RED test unknown action returns structured error with non-crashing CLI behavior.
- [ ] RED dependency test invokes `runtime-info` in an environment where optional location deps are masked/unavailable; it must still succeed and report them unavailable.
- [ ] RED missing core dependency test must produce machine-readable dependency/action failure rather than traceback when an action requiring lunar/tz provider cannot execute.
- [ ] GREEN all bundle tests.
- [ ] Run `python -m compileall -q engine tools dist/ai/metaphysics_lab.py` under Python 3.9 in CI.
- [ ] Commit: `test: enforce modular and bundled runtime parity`.

---

### Task 7: Mobile-first Human Docs and Runtime-only Upgrade UX

**Files:** Create `tests/test_ai_distribution_docs.py`; modify `README.md`, `docs/快速開始.md`, `docs/安裝到ChatGPT-Project.md`, `docs/更新與版本同步.md`, `CHANGELOG.md`.

- [ ] RED docs tests requiring the first-use path to name exactly the two uploads plus one copied Project Instructions artifact; require startup phrase `開始建立我的命理專案。` and High reasoning recommendation.
- [ ] RED docs tests forbid main install instructions from telling users to upload `engine/`, `requirements.txt`, multiple Python modules, or unzip a package.
- [ ] RED docs tests require explicit fallback: if AI host cannot execute Python, use one local CLI request flow; never pretend execution.
- [ ] RED docs tests require normal upgrade wording: replace `metaphysics_lab.py`; fixed core MD and Case MD remain unless contract/schema migration is explicitly required.
- [ ] README first screen: short product description, GitHub Release asset list, ChatGPT/Claude generic setup, High reasoning, startup phrase. Keep developer/release history sections below and clearly label historical snapshots.
- [ ] Rewrite `docs/快速開始.md` around AI-first first-run and Case MD download/re-upload workflow.
- [ ] Rewrite `docs/安裝到ChatGPT-Project.md` to the distribution pack rather than repo-module upload. Include Claude Project as the same generic workflow where UI concepts overlap; do not invent unsupported automatic Python execution guarantees.
- [ ] Rewrite `docs/更新與版本同步.md`: Project Contract vs Runtime vs Case schema; normal runtime update = Python only; dynamic capability status comes from `runtime_info`; remove stale `flowing_stars planned` operational checks.
- [ ] Add CHANGELOG Unreleased entry for AI Distribution Pack without changing `VERSION.md`.
- [ ] GREEN docs tests.
- [ ] Commit: `docs: add mobile-first AI distribution workflow`.

---

### Task 8: Final Acceptance / No-release Gate

**Files:** Create `tests/test_ai_distribution_acceptance.py`; no production semantic change unless a gate finds a defect.

**Acceptance assertions:**

```text
Project Contract sources stable and runtime-driven
runtime_info self-describing
build_natal / reconcile_natal structured actions
resolve_forecast_context deterministic and scope-bounded
nine Case Markdown files + incremental replacement rules
single-file deterministic build
modular == bundle parity
mobile-first individual assets
no VERSION/tag/release/promotion changes
```

- [ ] Write acceptance test that checks artifact filenames, versions, contract digests, no current capability matrix in fixed MD, and `dist/ai/metaphysics_lab.py` generated marker/source digest.
- [ ] Run focused distribution suite:

```bash
python -m unittest \
  tests.test_ai_contract_docs \
  tests.test_distribution_runtime_info \
  tests.test_distribution_natal \
  tests.test_distribution_forecast \
  tests.test_distribution_case_pack \
  tests.test_ai_distribution_build \
  tests.test_ai_distribution_bundle \
  tests.test_ai_distribution_docs \
  tests.test_ai_distribution_acceptance -v
```

- [ ] Run deterministic build check:

```bash
python tools/build_ai_distribution.py --check
```

- [ ] Run full repository regression:

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

- [ ] Run Python 3.9 compileall:

```bash
python -m compileall -q engine tools dist/ai/metaphysics_lab.py
```

- [ ] Verify `VERSION.md` still declares formal v1.2.0 release identity and that no capability maturity has been promoted by this feature.
- [ ] Verify `dist/ai` contains no private Case data, no raw Astralium private payload, no PDF/image, no qualification private evidence.
- [ ] Commit: `test: complete AI distribution acceptance gate`.

---

## CI / Validation Strategy

The active repo has no permanent GitHub Actions workflow. During implementation, validation uses temporary branches/workflows that **MUST NEVER MERGE**, matching prior Phase 2C governance.

For each meaningful batch:

1. Create/update feature branch code/tests.
2. Create a temporary validation branch from the exact feature head.
3. Add one temporary workflow file under `.github/workflows/` that checks exact base/head locks, installs `requirements.txt`, runs targeted tests, full regression when appropriate, and Python 3.9 compileall.
4. Open a draft validation PR to a safe base only to trigger Actions.
5. Inspect logs/results.
6. Close validation PR with `merged=false`.
7. Never merge validation-only workflow commits into feature/design/main.

Final feature head must not contain temporary validation workflow files.

---

## Completion / Integration Boundary

Implementation completion means:

- all Task 0–8 gates pass on the feature branch,
- generated `dist/ai` is deterministic and parity-verified,
- docs support the mobile-first AI-first flow,
- private Case handling remains local to users,
- no formal release identity or Stable promotion happened.

After completion, use `superpowers:verification-before-completion`, then `superpowers:finishing-a-development-branch`. Feature → design and design → main remain separate explicit governance decisions; do not auto-merge either boundary without user approval.