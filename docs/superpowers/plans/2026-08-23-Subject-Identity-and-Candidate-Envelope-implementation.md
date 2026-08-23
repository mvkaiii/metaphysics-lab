# Subject Identity + Candidate Envelope Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add multi-subject identity/registry support with subject-aware Case filenames, and allow partial natal Case creation when birth time is unknown or bounded without inventing time precision.

**Architecture:** Keep machine identity (`subject_id`) separate from human display metadata. Add a Project-level subject registry and make Case filenames derive from `filename_label + subject_short_id + canonical slot`. Add a candidate-envelope engine that enumerates all material minute states in the supplied uncertainty interval, builds Project natal candidates with existing deterministic builders, groups equivalent outputs, and classifies fields into invariant vs candidate-dependent values. Partial Base Case 00–04 is rendered from the envelope; unique-time-only workflows remain blocked.

**Tech Stack:** Python 3.9, existing `engine.birth`, `engine.natal`, `engine.distribution`, `unittest`, deterministic AI distribution builder.

**Spec:** `docs/superpowers/specs/2026-08-23-Subject-Identity-Registry-and-Unknown-Birth-Time-Candidate-Envelope-設計.md`

## Global Constraints

- Canonical filename format: `<filename_label>_<SUBJECT_SHORT_ID>_<slot>_<canonical_title>.md`.
- `subject_id` is opaque, runtime-generated, non-PII, and immutable after persistence.
- Default short id is 6 uppercase hex chars; collisions extend 8, 10, 12... until registry-unique.
- `subject_display_name` may change without changing `subject_id`.
- Unknown/bounded birth time must never be replaced by a default or midpoint.
- Candidate generation requires resolved location/timezone provenance; missing basis fails closed.
- Candidate envelope is experimental/on-demand and does not verify a birth time.
- Legacy Case Schema 1.0 nine-file packs remain readable.
- Case Schema / Project Contract remain 1.1 because this branch has not released 1.1 yet.
- Python 3.9 compatibility is mandatory.
- Full repository regression and deterministic distribution build must pass before merge.

---

### Task 0: Finish Historical Supplemental Integrity Guard

**Files:**
- Modify: `engine/distribution/calibration.py`
- Test: `tests/test_distribution_historical_integrity.py`

**Interfaces:**
- Consumes: selector `ranked_periods`, canonical Top4+Bottom1, supplemental blind points.
- Produces: `lock_historical_calibration()` rejection for supplemental points outside remaining ranked years, duplicate canonical years, or duplicate supplemental years.

- [ ] **Step 1: Run the existing RED integrity tests**

Run:
```bash
python -m unittest tests.test_distribution_historical_integrity -v
```
Expected: exactly the three supplemental integrity tests fail.

- [ ] **Step 2: Implement minimal supplemental validation before normalization**

Add logic equivalent to:
```python
canonical_years = set(expected_order)
ranked_years = set(ranked_map)
seen_supplemental = set()
for raw in supplemental:
    year = raw.get("reference_year")
    if year not in ranked_years:
        raise DistributionError("supplemental_outside_selector_window", ...)
    if year in canonical_years:
        raise DistributionError("supplemental_duplicates_canonical", ...)
    if year in seen_supplemental:
        raise DistributionError("duplicate_supplemental_point", ...)
    seen_supplemental.add(year)
```

- [ ] **Step 3: Re-run focused integrity tests**

Expected: PASS.

---

### Task 1: Subject Identity + Registry Runtime

**Files:**
- Create: `engine/distribution/subjects.py`
- Modify: `engine/distribution/constants.py`
- Modify: `engine/distribution/runtime.py`
- Test: `tests/test_distribution_subject_registry.py`

**Interfaces:**
- Produces:
  - `create_subject_identity(payload) -> dict`
  - `validate_subject_registry(payload) -> dict`
  - `rename_subject(payload) -> dict`
  - helpers `normalize_filename_label()`, `subject_short_id()`.

- [ ] **Step 1: Write RED tests** covering non-PII random id shape, same-name coexistence, deterministic label normalization, 6→8 digit short-id collision extension, registry validation, and rename preserving `subject_id`.

- [ ] **Step 2: Run RED tests**

Run:
```bash
python -m unittest tests.test_distribution_subject_registry -v
```
Expected: fail because subject actions do not exist.

- [ ] **Step 3: Implement `subjects.py`**

Use `secrets.token_hex(6)` for new identity body; normalize labels without romanization; derive short id from the hex body and extend against registry entries. Registry payload remains JSON-safe and renders `命主索引.md` deterministically from persisted identity values; ID generation itself is intentionally non-deterministic only at creation time.

- [ ] **Step 4: Register actions**

Add:
```text
subject.create_identity
subject.registry_validate
subject.rename
```
to `SUPPORTED_ACTIONS` and dispatcher routing.

- [ ] **Step 5: Run subject tests**

Expected: PASS.

---

### Task 2: Subject-Aware Case Filename Contract

**Files:**
- Modify: `engine/distribution/case_pack.py`
- Modify: `tests/test_distribution_case_pack.py`
- Create: `tests/test_distribution_case_identity.py`

**Interfaces:**
- Consumes: `subject_id`, `subject_display_name`, `subject_short_id`, `filename_label`.
- Produces: filenames such as `Kai_7F3A2C_01_命盤核心摘要.md`; parser resolves canonical slot from the right side so labels may contain `_`.

- [ ] **Step 1: Convert Case tests to RED subject-prefixed filenames** and preserve a legacy-1.0 fixture path for bare `00_...` through `08_...`.

- [ ] **Step 2: Implement canonical slot metadata independent of full filename**

Replace dictionaries keyed only by whole filename with canonical slot/title definitions, and add helpers:
```python
canonical_case_filename(identity, slot) -> str
parse_case_filename(filename) -> ParsedCaseFilename
```
Parser validates suffix `_<SHORTID>_<NN>_<canonical_title>.md` from the right.

- [ ] **Step 3: Add new front-matter fields**

Require for new 1.1 Case files:
```yaml
subject_display_name
subject_short_id
filename_label
```
Legacy 1.0 path keeps old required metadata compatibility.

- [ ] **Step 4: Make manifest and progressive materialization subject-aware**

`00` references the actual subject-prefixed filenames. `update_case_record()` resolves the target by canonical slot/record type, not by hard-coded bare filename.

- [ ] **Step 5: Implement explicit legacy migration**

`migrate_case()` accepts `subject_display_name` for 1.0→1.1 migration, preserves existing lineage `subject_id`, creates normalized display metadata and returns renamed files. Missing display name fails closed.

- [ ] **Step 6: Test mismatch failures**

Cover filename label, short id, slot/title, subject mismatch, mixed-subject pack, and rename consistency.

---

### Task 3: Candidate Envelope Core

**Files:**
- Create: `engine/natal/candidates.py`
- Modify: `engine/natal/capabilities.py`
- Modify: `engine/natal/__init__.py`
- Test: `tests/test_natal_candidate_envelope.py`
- Test: `tests/test_natal_capabilities.py`

**Interfaces:**
- Produces: `build_candidate_envelope(...) -> dict` with `natal_precision_state`, material candidate groups, invariant/variant Bazi and Ziwei facts, boundary failures, allowed/blocked analysis.

- [ ] **Step 1: Write RED tests** for unknown time, bounded range, no midpoint/default, deterministic partition, invariant equality, variant mapping, and missing location basis.

- [ ] **Step 2: Implement uncertainty interval enumeration at one-minute civil precision**

For v1, correctness beats premature optimization. Enumerate each HH:MM in the supplied same-date interval (unknown = 00:00..23:59), build exact existing Project natal candidates using the same resolved location/profile, serialize only chart facts that can materially vary, and group contiguous minutes with identical canonical signatures. Never substitute a midpoint. If a candidate minute cannot qualify, retain a failure record rather than dropping it.

- [ ] **Step 3: Classify invariant vs variant facts**

Recursively compare JSON-safe Bazi and Ziwei fact trees across all qualified candidate groups. A path is invariant only when every qualified candidate has the same value. Otherwise retain per-candidate values; no majority rule.

- [ ] **Step 4: Add capability registry entry**

```python
"natal.candidate_envelope": {
    "implementation": "implemented",
    "maturity": "experimental",
    "routing": "on_demand",
    "rule_version": "1.0-exp",
    ...
}
```

- [ ] **Step 5: Run candidate tests**

Expected: PASS.

---

### Task 4: Distribution Candidate Envelope Action

**Files:**
- Modify: `engine/distribution/natal.py`
- Modify: `engine/distribution/constants.py`
- Modify: `engine/distribution/runtime.py`
- Test: `tests/test_distribution_candidate_envelope.py`

**Interfaces:**
- Produces runtime action `natal.candidate_envelope`.
- Input supports exact existing birth fields plus either `birth_time_range` or missing `birth_time`, with required resolved location.

- [ ] **Step 1: Write RED distribution tests** for unknown and bounded payloads, structured missing-location error, and modular result shape.

- [ ] **Step 2: Implement payload parsing** without calling the full-natal precision gate first. Validate birth date/place/sex and resolved location, pass uncertainty to candidate core.

- [ ] **Step 3: Register dispatcher action and runtime capability exposure**.

- [ ] **Step 4: Run focused tests**.

---

### Task 5: Partial Base Case 00–04

**Files:**
- Modify: `engine/distribution/case_pack.py`
- Test: `tests/test_distribution_partial_case.py`

**Interfaces:**
- `export_case_markdown` accepts exactly one of `normalized_natal` or `candidate_envelope`.
- Partial output uses the same subject-aware filename contract.

- [ ] **Step 1: Write RED tests** that unknown-time envelope exports and validates Base Case 00–04.

- [ ] **Step 2: Add partial renderers**

00 includes natal status, birth-time status, candidate count, allowed/blocked analysis. 01 renders fixed sections `【已確定盤面】`, `【候選依賴盤面】`, `【目前不可唯一判定】`. 02 records precision/source/candidate metadata. 03 renders Bazi invariants/variants/candidate set/blocked conclusions. 04 renders Ziwei invariants/candidate summaries/blocked conclusions.

- [ ] **Step 3: Ensure unique-time-only actions fail closed** when given partial envelope rather than normalized full natal.

- [ ] **Step 4: Run partial Case tests**.

---

### Task 6: AI Workflow + Documentation Contract

**Files:**
- Modify: `core/AI工作流程.md`
- Modify: `core/命理分析作業規範.md`
- Modify: `core/PROJECT_INSTRUCTIONS.md`
- Modify: `docs/命盤資料準備指南.md`
- Modify: `docs/安裝到ChatGPT-Project.md`
- Modify: `docs/快速開始.md`
- Modify: `docs/資料治理.md`
- Modify: `CHANGELOG.md`
- Modify: `tests/test_document_contract_consistency.py`

**Interfaces:**
- New workflow reads/creates `命主索引.md`, resolves subject before Case reads, and never assumes every question is about the Project owner.

- [ ] **Step 1: Add RED documentation tests** for subject registry, single-underscore filename examples, unknown-time partial Case wording, and no obsolete bare 1.1 filename examples in current user docs.

- [ ] **Step 2: Update canonical instructions and user docs** while preserving v1.3.0 release snapshot wording in `VERSION.md`.

- [ ] **Step 3: Run documentation tests**.

---

### Task 7: Distribution Parity and Full Verification

**Files:**
- Modify: `tests/test_ai_distribution_bundle.py`
- Modify: focused CI workflow if required
- Generated: `dist/ai/metaphysics_lab.py`, `dist/ai/METAPHYSICS_CORE.md`, `dist/ai/PROJECT_INSTRUCTIONS.md`

**Interfaces:**
- Bundle must expose subject identity/registry, candidate envelope, and subject-aware Case actions identically to modular runtime.

- [ ] **Step 1: Add bundle parity tests** for `subject.create_identity` shape without asserting random value equality, deterministic registry validation, candidate envelope, and partial Case export.

- [ ] **Step 2: Rebuild distribution**

Run:
```bash
python tools/build_ai_distribution.py
python tools/build_ai_distribution.py --check
```
Expected: deterministic build check PASS.

- [ ] **Step 3: Run focused suites**

Run all subject/candidate/case/historical/documentation tests.

- [ ] **Step 4: Run full repository regression**

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```
Expected: 0 failures.

- [ ] **Step 5: Python 3.9 compile check**

```bash
python -m compileall engine dist/ai/metaphysics_lab.py
```
Expected: PASS.

- [ ] **Step 6: Final diff review**

Confirm no capability maturity promotions, no `main` merge, no v1.3.0 tag/release mutation, no PII in committed fixtures, and no conflicting filename conventions.
