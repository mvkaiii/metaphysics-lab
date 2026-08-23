# Progressive Case + Historical Blind Calibration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 將 v1.3.0 固定 9-file Case 改為 00～04 Base Case + 05～08 progressive materialization，並加入第一次未來問事的 Stage 1 lock、Historical Blind Calibration lock/finalize 與 05 ledger。

**Architecture:** `engine/distribution/case_pack.py` 保持 Case Markdown 唯一寫入責任；新增 `engine/distribution/calibration.py` 管理 canonical digest、blind lock、verification normalization 與 timing evaluation。`engine/distribution/runtime.py` 只做 action routing。Case schema 升為 1.1；新版接受 1.1 progressive Case，也向後讀取 legacy 1.0 完整 9-file Case。Historical selector selection 由另一份 plan 實作，本 plan 只消費 selector structured output，不自行選年。

**Tech Stack:** Python stdlib、existing distribution runtime、`unittest`、existing AI distribution builder。

**Spec:** `docs/superpowers/specs/2026-08-23-Progressive-Case-Historical-Blind-Calibration-設計.md` + `docs/superpowers/specs/2026-08-23-Progressive-Case-Historical-Blind-Calibration-修訂.md`

## Global Constraints

- Production implementation must occur on a feature branch based on the approved design head, never directly on `main`.
- New Case schema = `1.1`; Project Contract must be bumped because workflow semantics change. Legacy Case schema `1.0` remains readable.
- New Case export contains exactly 00～04; 05～08 do not exist until first real record.
- `00_專案索引.md` is the materialization manifest and owns `historical_calibration_status`.
- First future question may lock Stage 1 before historical calibration, but Stage 2 must not run until calibration is finalized or explicitly degraded as unavailable.
- Locked forecast and locked historical blind payloads are immutable by digest.
- `05` stores three clearly separated classifications: blind prediction = 命理推論; user-confirmed actual = 已驗證事件; evaluation = 已校驗資料.
- `cannot_recall` never becomes a miss and never fabricates an actual event.
- Timing evaluation uses Bazi flow-year intervals when actual date/month precision supports it; Gregorian year-only answers near Li-Chun may remain ambiguous.
- Canonical selection is supplied by `historical.activation_selector`; calibration code must not select, replace, or reorder canonical years.
- No capability maturity promotion beyond what the approved specs define.
- Every behavior change follows RED → expected failure → minimal GREEN → focused regression.

---

## File Map

**Create:**
- `engine/distribution/calibration.py` — lock/finalize/timing evaluation helpers.
- `tests/test_distribution_historical_calibration.py` — lock/finalize/immutability/timing tests.

**Modify:**
- `engine/distribution/constants.py` — contract/schema versions and new actions.
- `engine/distribution/case_pack.py` — Base/Progressive Case model, materialization, legacy validation.
- `engine/distribution/runtime.py` — new calibration actions and tracking materialization routes.
- `tests/test_distribution_case_pack.py` — replace fixed-nine expectations with progressive lifecycle expectations.
- `tests/test_distribution_runtime_info.py` — assert new contract/schema/actions.
- `core/AI工作流程.md`, `core/核心提示詞.md`, `core/命理分析作業規範.md` — workflow contract.
- `README.md`, `docs/快速開始.md`, `docs/安裝到ChatGPT-Project.md`, `docs/更新與版本同步.md` — user lifecycle docs.
- `dist/ai/*` — regenerated artifacts only through `tools/build_ai_distribution.py`.

---

### Task 1: Case 1.1 Progressive Export and Validation

**Files:** modify `engine/distribution/constants.py`, `engine/distribution/case_pack.py`, `tests/test_distribution_case_pack.py`, `tests/test_distribution_runtime_info.py`.

**Interfaces:**
- `BASE_CASE_FILES: tuple[str, ...] = CASE_FILES[:5]`
- `PROGRESSIVE_CASE_FILES: tuple[str, ...] = CASE_FILES[5:]`
- `validate_case({"case_files": mapping}) -> {status, subject_id, validated_files, case_schema_version}`

- [ ] **Step 1: Write RED tests** replacing the first export test with:

```python
def test_new_case_exports_only_base_files(self):
    result = self.export()
    self.assertTrue(result["ok"], result)
    self.assertEqual(list(result["data"]["files"]), EXPECTED_BASE_FILES)
    self.assertIn("Historical Calibration: uncalibrated", result["data"]["files"]["00_專案索引.md"])
```

Add tests that a 1.1 five-file Case validates, arbitrary optional 05～08 subsets validate only when `00` manifest agrees, and a legacy 1.0 nine-file Case remains readable.

- [ ] **Step 2: Run RED**: `python -m unittest tests.test_distribution_case_pack tests.test_distribution_runtime_info -v`; expected failures: exporter still returns nine files and schema/contract are 1.0.
- [ ] **Step 3: Minimal GREEN**: set `CASE_SCHEMA_VERSION = "1.1"`, `PROJECT_CONTRACT_VERSION = "1.1"`; make export render only `BASE_CASE_FILES`; render `00` with materialized/pending manifest and calibration state; change `_case_files`/`validate_case` to accept Base + optional progressive files and legacy 1.0 nine-file packs.
- [ ] **Step 4: GREEN regression**: rerun the two focused modules.
- [ ] **Step 5: Commit** `feat: add progressive case schema 1.1`.

### Task 2: First Materialization of 05–08

**Files:** modify `engine/distribution/case_pack.py`, `tests/test_distribution_case_pack.py`.

**Interfaces:**
- `materialize_case_record(payload) -> {subject_id, changed_files}`
- Required payload fields: `case_files`, `filename`, `entry`, `updated_at`, `last_modified_by`.

- [ ] **Step 1: RED tests** for first append to absent `05`, `06`, `07`, `08`. Assert first materialization returns `00 + target`; subsequent append returns target only; a major-decision record is not duplicated into 07 automatically.
- [ ] **Step 2: Verify RED** because current `update_case_record` requires all nine files.
- [ ] **Step 3: GREEN**: when target progressive file is absent, render its canonical tracking body, append the first entry, update `00` manifest, and return both changed files. When present, append only target. Preserve `05` verification validation and blind forecast immutability.
- [ ] **Step 4: GREEN regression**: `python -m unittest tests.test_distribution_case_pack -v`.
- [ ] **Step 5: Commit** `feat: materialize case records on demand`.

### Task 3: Blind Forecast Lock

**Files:** create `engine/distribution/calibration.py`, create/modify `tests/test_distribution_historical_calibration.py`, modify `engine/distribution/runtime.py`, `engine/distribution/constants.py`.

**Interfaces:**

```python
def lock_blind_forecast(payload: Mapping[str, object]) -> dict:
    # returns blind_forecast_id, locked_payload, payload_digest
```

Canonical digest must be SHA-256 over UTF-8 JSON with `sort_keys=True`, compact separators and no mutable timestamp added after hashing.

- [ ] **Step 1: RED**: test identical payloads yield identical digest; changed forecast text changes digest; source allowlist must be exactly Base files; payload declaring 05–08 as read is rejected.
- [ ] **Step 2: Verify RED** action unsupported.
- [ ] **Step 3: GREEN**: implement canonical JSON/digest and strict source guard; add `lock_blind_forecast` to runtime actions.
- [ ] **Step 4: GREEN regression** focused runtime + calibration tests.
- [ ] **Step 5: Commit** `feat: lock first-stage blind forecasts`.

### Task 4: Historical Blind Set Lock

**Files:** modify `engine/distribution/calibration.py`, `tests/test_distribution_historical_calibration.py`, `runtime.py`, `constants.py`.

**Interfaces:**

```python
def lock_historical_calibration(payload):
    # input includes selector_result.selection_digest and 5 canonical test points
```

- [ ] **Step 1: RED**: reject canonical test-point years/roles that differ from selector selection; allow `blindness_status = blind|contaminated`; allow optional supplemental points but assert they do not alter `canonical_selection_digest`.
- [ ] **Step 2: Verify RED**.
- [ ] **Step 3: GREEN**: validate selector digest binding, normalize blind interpretation payload, return immutable digest.
- [ ] **Step 4: GREEN regression**.
- [ ] **Step 5: Commit** `feat: lock historical blind calibration sets`.

### Task 5: Finalize Calibration and Materialize 05

**Files:** modify `calibration.py`, `case_pack.py`, `tests/test_distribution_historical_calibration.py`.

**Interfaces:**

```python
def finalize_historical_calibration(payload) -> dict:
    # verifies locked digest, evaluates user responses, returns ledger records + calibration status
```

- [ ] **Step 1: RED tests** for `matched`, `partial`, `not_matched`, `cannot_recall`; tampered locked payload rejected; `cannot_recall` creates no `actual_event`; 3 blind+scorable points produce `basic`; fewer than 3 remain `uncalibrated`; contaminated points do not count toward blind scorable threshold.
- [ ] **Step 2: RED timing tests**: predicted 2016 flow year + actual `2017-01-15` maps to `exact_flow_year`; actual after next Li-Chun becomes `shifted`; year-only answer that straddles Li-Chun produces ambiguity rather than a fabricated offset.
- [ ] **Step 3: Verify RED**.
- [ ] **Step 4: GREEN**: implement verification normalization, use selector period boundaries for timing, build `05` ledger entries with nested classification blocks, materialize 05 through Case writer and update 00 calibration status.
- [ ] **Step 5: GREEN regression** calibration + case-pack tests.
- [ ] **Step 6: Commit** `feat: finalize historical blind calibration`.

### Task 6: Contract and UX Documentation

**Files:** modify core/docs/README listed in File Map plus related doc tests.

- [ ] **Step 1: RED docs tests** asserting: first Case is 00～04; 05 starts only after verification; 06～08 are on-demand; first future question locks Stage 1 before history is revealed; canonical selector years are Python-owned; `relative_low` must not be called stable.
- [ ] **Step 2: Verify RED**.
- [ ] **Step 3: GREEN docs** update canonical source docs; remove fixed-nine wording.
- [ ] **Step 4: GREEN docs regression** existing `test_ai_contract_docs`, `test_ai_distribution_docs` plus new assertions.
- [ ] **Step 5: Commit** `docs: document progressive case calibration workflow`.

### Task 7: Distribution Rebuild and Acceptance

**Files:** regenerate `dist/ai/METAPHYSICS_CORE.md`, `PROJECT_INSTRUCTIONS.md`, `metaphysics_lab.py`; modify acceptance/build tests only if contract assertions need version 1.1.

- [ ] **Step 1: Run focused full distribution suite**: `python -m unittest tests.test_distribution_case_pack tests.test_distribution_historical_calibration tests.test_distribution_runtime_info tests.test_ai_contract_docs tests.test_ai_distribution_build tests.test_ai_distribution_bundle tests.test_ai_distribution_docs tests.test_ai_distribution_acceptance -v`.
- [ ] **Step 2: Build artifacts**: `python tools/build_ai_distribution.py --output-dir dist/ai`.
- [ ] **Step 3: Verify deterministic build**: `python tools/build_ai_distribution.py --output-dir dist/ai --check`.
- [ ] **Step 4: Run full repository regression**: `python -m unittest discover -s tests -v`.
- [ ] **Step 5: Compile**: `python -m compileall engine tools dist/ai/metaphysics_lab.py`.
- [ ] **Step 6: Commit** `build: refresh progressive case distribution`.
