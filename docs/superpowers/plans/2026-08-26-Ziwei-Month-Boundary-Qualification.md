# Ziwei Month Boundary Qualification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the remaining Ziwei fine-cycle month-layer qualification gap, especially leap-twelfth-month second-half continuity, then lock the surrounding month/timezone/runtime boundaries with reproducible evidence and CI drift checks.

**Architecture:** Keep `engine.ziwei.month` and `engine.ziwei.fine_cycle_stems` as the production authorities. Add an independent qualification builder that consumes pinned public `lunar-python==1.4.8`, binds the existing pinned lunar-lite source contract, and checks Project month palace/stem behavior without changing formulas. Boundary tests exercise Calendar Resolver, downstream source reuse, and generated-runtime parity.

**Tech Stack:** Python 3.9, unittest, lunar-python==1.4.8, existing Metaphysics Lab runtime and GitHub Actions.

**Spec:** `core/命理推導計算規則.md` sections 3.1 and 4 plus the user-approved scope in this conversation.

## Global Constraints

- Do not change production metaphysics formulas unless a reproduced qualification mismatch requires a separately justified fix.
- Do not promote capability maturity.
- Preserve Calendar Resolver neutrality; Ziwei month-layer logic consumes resolved lunar fields and does not apply a 23:00 month rollover.
- Preserve the split rule: leap month day 1-15 uses the original month; day 16 onward uses the next effective month.
- Preserve source reuse: transformations, flying, and flowing-star layers must consume one resolved monthly source rather than recomputing month stems.
- Keep public qualification evidence privacy-safe and deterministic.
- Keep release/tag/version identity unchanged.

---

### Task 1: Establish a RED qualification gate

**Files:**
- Create: `tests/test_ziwei_month_boundary_qualification.py`

**Interfaces:**
- Consumes: repository paths only.
- Produces: a failing test that requires `tools/build_ziwei_month_boundary_qualification.py` and committed evidence under `qualification/ziwei/month_boundary/`.

- [ ] **Step 1: Write the failing test** requiring the reproducible builder and evidence file.
- [ ] **Step 2: Run full CI** and confirm exactly the new gate fails for missing deliverables, with pre-existing tests green.
- [ ] **Step 3: Record RED run/head evidence in the PR.**

### Task 2: Build public month-layer qualification evidence

**Files:**
- Create: `tools/build_ziwei_month_boundary_qualification.py`
- Create: `qualification/ziwei/month_boundary/public-lunar-python-1.4.8.json`
- Create: `qualification/ziwei/month_boundary/README.md`
- Modify: `tests/test_ziwei_month_boundary_qualification.py`

**Interfaces:**
- Consumes: `resolve_month_stem(context)`, `effective_lunar_month(...)`, pinned `lunar-python==1.4.8`, existing lunar-lite Phase 2B report/source contract.
- Produces: `build_report()`, `write_report()`, `check_report()` and deterministic JSON evidence.

- [ ] **Step 1: Add a fresh-oracle test** that fails until a builder can compare Project monthly behavior with pinned public lunar month continuity.
- [ ] **Step 2: Implement the minimal builder.** For ordinary months compare against public `LunarMonth` Ganzhi. For leap first half compare against the leap month's base month; for leap second half compare against `LunarMonth.next(1)`. Include the real historical leap-twelfth year 1574 and verify day 15/day 16 continuity into lunar 1575 month 1.
- [ ] **Step 3: Bind the existing lunar-lite source contract.** Record that its generic `fixLeap` formula is an external source anchor, while its 12-element branch table cannot directly runtime-cover leap-12 second-half; do not hide that limitation.
- [ ] **Step 4: Run qualification.** If any mismatch appears, stop and debug before changing production code. If zero mismatches, commit exact canonical JSON.
- [ ] **Step 5: Add `--check`** and verify the committed evidence is non-mutating and reproducible.

### Task 3: Complete month boundary coverage

**Files:**
- Modify: `tests/test_ziwei_month_boundary_qualification.py`

**Interfaces:**
- Consumes: Calendar Resolver and the existing monthly forecast path.
- Produces: explicit regression boundaries around the qualified month rule.

- [ ] **Step 1: Add leap-day 15/16 tests** for both palace effective month and fine-cycle month stem.
- [ ] **Step 2: Add ordinary month-end/new-month tests** proving month changes only when neutral lunar conversion changes, not at Ziwei 23:00 day rollover.
- [ ] **Step 3: Add lunar-year boundary tests** proving previous-year month 12 to next-year month 1 continuity.
- [ ] **Step 4: Add DST tests** proving nonexistent/ambiguous civil times are owned by Calendar Resolver and two legal fall-back instants for one local civil time do not fork the Ziwei month result.
- [ ] **Step 5: Add source-reuse tests** proving monthly transformations/flying/flowing stars use the exact same resolved monthly reference and stem.
- [ ] **Step 6: Add modular/generated parity** for normal month, leap split boundary, late-Zi, and lunar-year boundary targets where supported by the runtime validation range.

### Task 4: Make qualification a permanent drift gate

**Files:**
- Modify: `.github/workflows/feature-historical-calibration-validation.yml`

**Interfaces:**
- Consumes: committed month-boundary evidence.
- Produces: CI command `python tools/build_ziwei_month_boundary_qualification.py --check`.

- [ ] **Step 1: Add the CI check after existing Bazi/Ziwei flow-time gates.**
- [ ] **Step 2: Run full repository regression, compile, distribution rebuild/check, clean-tree, and artifact upload on the exact final HEAD.**

### Task 5: Reconcile the authoritative rule source after evidence is green

**Files:**
- Modify: `core/命理推導計算規則.md`

**Interfaces:**
- Consumes: exact qualification evidence from Tasks 2-4.
- Produces: documentation that distinguishes what is externally qualified, what remains a public-oracle limitation, and what remains experimental.

- [ ] **Step 1: Replace only the stale qualification-status sentence** for `leap_twelfth_month_second_half`; do not alter formulas or maturity.
- [ ] **Step 2: State the public-oracle limitation explicitly:** lunar-lite cannot directly index a thirteenth branch entry, so the closed Project case is qualified through historical leap-12 existence plus pinned lunar-python next-lunar-month continuity and Project property tests.
- [ ] **Step 3: Run documentation and full regression gates again.**

### Task 6: Final evidence and PR handoff

**Files:**
- Modify: PR body only.

- [ ] **Step 1: Record RED → GREEN evidence, exact final SHA, counts, artifact digest, and final changed-file boundary.**
- [ ] **Step 2: Verify no production `engine/*` algorithm, release/tag/version, or capability maturity change occurred unless a real mismatch forced a separately explained change.**
- [ ] **Step 3: Leave the PR open and unmerged until explicit merge authorization.**
