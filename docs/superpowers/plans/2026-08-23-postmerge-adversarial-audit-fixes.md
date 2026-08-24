# Post-Merge Adversarial Audit Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remediate confirmed adversarial-audit defects #161–#165 without changing release identity or promoting Experimental capabilities.

**Architecture:** Keep fixes at existing trust boundaries: bind blind inputs to one subject, validate Candidate Envelope semantics against candidates, replace caller-reconstructable lock authority with persisted Case authority, make tracking append idempotent, and enforce display-name/filename-label identity consistency. Each defect is handled test-first and independently verifiable.

**Tech Stack:** Python 3.9+, unittest, GitHub Actions, deterministic AI distribution builder.

**Spec:** GitHub Issues #161, #162, #163, #164, #165 and existing Project Contract / Case Schema 1.1 documentation.

## Global Constraints

- Base commit: `f716cdfc7d793991a5c79eba86ee266a5a538b60`.
- Work only on `fix/postmerge-audit-161-165`; never commit directly to `main`.
- Preserve formal release identity `v1.3.0`.
- Preserve `natal.candidate_envelope` maturity as `implemented / experimental / on_demand / 1.0-exp`.
- Keep Legacy Case 1.0 readable and non-destructive.
- No midpoint/default-time birth-time fallback.
- TDD for every behavior change: failing regression test first, verify RED, minimal fix, verify GREEN.
- Rebuild and verify generated distribution after runtime-source changes.

---

### Task 0: Make CI validate the actual branch/PR SHA

**Files:**
- Modify: `.github/workflows/feature-historical-calibration-validation.yml`

**Interfaces:**
- Consumes: GitHub `push`, `pull_request`, `workflow_dispatch` contexts.
- Produces: validation job that checks out the SHA that triggered the run rather than the obsolete historical feature branch.

- [ ] Replace the hard-coded checkout ref with event SHA semantics.
- [ ] Allow pushes from `fix/postmerge-audit-161-165` to trigger validation while retaining the historical feature trigger.
- [ ] Preserve existing generated-distribution persistence behavior only for the old historical feature branch.
- [ ] Open a draft PR and confirm job logs show the stabilization branch exact HEAD.

### Task 1: #162 bind Historical Stage 1 sources to one subject

**Files:**
- Modify: `tests/test_distribution_historical_calibration.py`
- Modify: `engine/distribution/calibration.py`

**Interfaces:**
- Consumes: `source_files_used`, `subject_id`, parsed subject-aware Case filenames.
- Produces: `blind_source_violation` when subject-aware Base5 files mix short IDs or conflict with the requested subject identity.

- [ ] Add a failing test using 00–04 filenames split across two `subject_short_id` values.
- [ ] Run focused historical-calibration tests and verify the new test fails for acceptance, not syntax/setup.
- [ ] Make source canonicalization retain parsed subject identity and require one short ID for subject-aware Base5.
- [ ] Bind subject-aware source identity to the requested subject where sufficient identity data exists; preserve explicit legacy bare-filename compatibility.
- [ ] Re-run focused tests and verify GREEN.

### Task 2: #161 validate Candidate Envelope semantic classification

**Files:**
- Modify: `tests/test_distribution_partial_case.py`
- Modify: `engine/distribution/partial_case.py`
- Reuse: `engine/natal/candidates.py`

**Interfaces:**
- Consumes: Candidate Envelope candidates and caller-provided invariant/variant Bazi/Ziwei facts.
- Produces: `invalid_candidate_envelope` unless caller classification equals deterministic candidate-derived classification.

- [ ] Add a failing test with two different hour pillars but a forged invariant hour pillar.
- [ ] Add missing-path / no-majority coverage where needed to lock semantic comparison behavior.
- [ ] Verify RED.
- [ ] Recompute canonical invariant/variant classification from candidate facts with the existing trusted classifier and compare canonical structures.
- [ ] Verify focused partial-Case and candidate-classification tests GREEN.

### Task 3: #163 make Historical lock authority non-reconstructable by finalize caller

**Files:**
- Modify: `tests/test_distribution_historical_calibration.py`
- Modify: `engine/distribution/calibration.py`
- Modify: `engine/distribution/case_pack.py` only if persisted lock-record lookup/validation requires a Case ledger helper.

**Interfaces:**
- Consumes: a persisted authoritative lock record and calibration responses.
- Produces: finalize output only when the supplied lock matches the authoritative persisted record; a caller cannot alter semantic lock fields and simply recompute SHA-256.

- [ ] Add a failing regression test that tampers interpretation/selection/source identity, recomputes `canonical_digest`, and proves current finalize accepts it.
- [ ] Verify RED.
- [ ] Implement portable/local authority using immutable persisted Case lock record or equivalent caller-independent authority already available in the runtime; do **not** rely on a bundled HMAC secret.
- [ ] Keep SHA-256 only as deterministic content identifier/checksum, not as sole immutability authority.
- [ ] Verify both legacy tamper test and recomputed-digest attack test GREEN.

### Task 4: #164 make progressive append idempotent by record_id

**Files:**
- Modify: `tests/test_distribution_case_pack.py`
- Modify: `engine/distribution/case_pack.py`

**Interfaces:**
- Consumes: tracking file body and `entry.record_id`.
- Produces: identical retry as deterministic no-op; same ID with different payload fails closed; different IDs append normally.

- [ ] Add failing tests for identical same-ID retry and same-ID/different-payload collision.
- [ ] Verify RED.
- [ ] Parse existing records between record markers and enforce record ID uniqueness.
- [ ] Return no content duplication for byte-equivalent retry; reject conflicting reuse.
- [ ] Verify focused Case Pack tests GREEN.

### Task 5: #165 bind filename_label to normalized display name

**Files:**
- Modify: `tests/test_distribution_subjects.py` and/or existing Subject Registry test module.
- Modify: `tests/test_distribution_case_pack.py` where Case identity validation is covered.
- Modify: `engine/distribution/subjects.py`
- Modify: `engine/distribution/case_pack.py`

**Interfaces:**
- Consumes: `subject_display_name`, `filename_label`.
- Produces: identity only when `filename_label == normalize_filename_label(subject_display_name)`.

- [ ] Add failing registry and Case-payload mismatch tests.
- [ ] Verify RED.
- [ ] Enforce the display-derived normalized label in both identity validators.
- [ ] Verify Unicode/whitespace/punctuation normalization and rename tests stay GREEN.

### Task 6: Full verification and review handoff

**Files:**
- Regenerate: `dist/ai/*` when source changes require it.
- Update docs only if runtime contract wording must change for #163 authority semantics.

- [ ] Run `python tools/build_ai_distribution.py`.
- [ ] Run `python tools/build_ai_distribution.py --check`.
- [ ] Ensure committed distribution is byte-identical to deterministic rebuild.
- [ ] Run focused #161–#165 regression suites.
- [ ] Run `python -m unittest discover -s tests -p 'test_*.py' -v`.
- [ ] Run `python -m compileall engine tests tools`.
- [ ] Confirm bundle/modular parity, documentation contracts, release identity, and capability maturity tests execute and pass.
- [ ] Open/refresh one draft PR to `main` with `Fixes #161` through `Fixes #165`, but do not merge.
- [ ] Record exact final HEAD and CI evidence for independent Codex adversarial review.
