# Claim Consumption Qualification Q1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an independent deterministic qualification authority for Claim Consumption C1 decisions without changing C1 policy or reusing prior private Interpretation labels.

**Architecture:** A new pure Python evaluator validates a strict structured oracle plus frozen C1 public bundles, scores authorization/caveat/specificity alignment, and emits aggregate-only deterministic reports. A thin CLI exposes the evaluator; synthetic fixtures prove behavior. Production C1 remains read-only.

**Tech Stack:** Python 3.9, stdlib `json`/`hashlib`/`argparse`, unittest/pytest discovery, existing deterministic AI distribution builder.

**Spec:** `docs/superpowers/specs/2026-09-01-claim-consumption-qualification-q1-design.md`

## Global Constraints

- Authoritative upstream frozen GitHub SHA: `39a084b9e7e5d56f0d6ac0970ed5683258a4d402`.
- Branch: `research/v1.6-claim-consumption-qualification-q1`.
- `engine/distribution/claim_consumption_contract.py` is frozen/read-only.
- `engine/distribution/coordination_policy_v2.py` is frozen/read-only.
- Phase 3 ranking and Claim Evidence candidate sets are frozen/read-only.
- Do not derive Q1 policy, labels, or thresholds from prior private aggregate outcomes.
- No raw subject/event text in Q1 inputs or reports.
- Unknown fields fail closed.
- `promotion_allowed` is always `false` in Q1.
- No private Q1 evaluation until an independently adjudicated Q1 oracle and any non-zero private thresholds are sealed before evaluation.
- TDD mandatory: evaluator production code is written only after observed synthetic RED.
- Development/debugging happens in the online workspace first; GitHub is final Hosted exact-SHA confirmation only.

---

### Task 1: Freeze Q1 design and plan

**Files:**
- Create: `docs/superpowers/specs/2026-09-01-claim-consumption-qualification-q1-design.md`
- Create: `docs/superpowers/plans/2026-09-01-claim-consumption-qualification-q1.md`

**Produces:** a frozen schema, scoring matrix, aggregate-report contract, and governance boundary before evaluator code.

- [ ] Verify the spec contains no placeholder markers, no private-case labels, and no release thresholds derived from prior private outcomes.
- [ ] Verify the plan maps every spec requirement to Tasks 2-6.
- [ ] Commit documents only:

```bash
git add docs/superpowers/specs/2026-09-01-claim-consumption-qualification-q1-design.md \
        docs/superpowers/plans/2026-09-01-claim-consumption-qualification-q1.md
git commit -m "docs: design claim consumption qualification q1"
```

---

### Task 2: Synthetic RED contract

**Files:**
- Create: `tests/fixtures/v1.6-claim-consumption-qualification.synthetic.v1.json`
- Create: `tests/test_v16_claim_consumption_qualification.py`

**Interfaces:**
- Consumes: existing C1 public decision field names from `claim_consumption_contract.py`.
- Produces desired evaluator API:

```python
from engine.distribution.claim_consumption_qualification import (
    INPUT_SCHEMA,
    REPORT_SCHEMA,
    evaluate_claim_consumption_qualification,
    validate_claim_consumption_qualification_input,
)
```

- [ ] Create a synthetic fixture with `classification="synthetic_validation"`, at least three cases, and exact-match examples for `render`, `render_with_caveat`, and `abstain_claim`. Every case has a valid canonical `input_digest`; every embedded C1 bundle has a valid `claim_consumption_digest`.
- [ ] Add `unittest.TestCase` tests that assert the baseline report has:

```python
assert report["general_conformance_status"] == "PASS"
assert report["decision_alignment"] == {"matched": report["claim_count"], "partial": 0, "missed": 0}
assert report["promotion_allowed"] is False
```

- [ ] Add mutation tests for over-render, under-render, caveat omission, unnecessary caveat, specificity overreach, specificity excessive downgrade, cutoff contamination, malformed C1 digest, malformed case input digest, duplicate/missing/extra claim IDs, and private/unknown fields.
- [ ] Add order-permutation test requiring byte-identical aggregate report after case-order permutation.
- [ ] Run:

```bash
python -m unittest -v tests.test_v16_claim_consumption_qualification
```

Expected RED: import failure for `engine.distribution.claim_consumption_qualification`. Fixture syntax/digest construction errors do not count as valid RED.

- [ ] Commit RED only:

```bash
git add tests/fixtures/v1.6-claim-consumption-qualification.synthetic.v1.json \
        tests/test_v16_claim_consumption_qualification.py
git commit -m "test: define claim consumption qualification q1 red gate"
```

---

### Task 3: Minimal deterministic evaluator

**Files:**
- Create: `engine/distribution/claim_consumption_qualification.py`
- Test: `tests/test_v16_claim_consumption_qualification.py`

**Public interface:**

```python
INPUT_SCHEMA = "v1.6-claim-consumption-qualification-input.v1"
REPORT_SCHEMA = "v1.6-claim-consumption-qualification-report.v1"

def validate_claim_consumption_qualification_input(payload: object) -> dict:
    ...

def evaluate_claim_consumption_qualification(payload: object) -> dict:
    ...
```

- [ ] Implement canonical JSON and SHA-256 helpers with sorted keys, compact separators, UTF-8, `ensure_ascii=False`, `allow_nan=False`.
- [ ] Reject unknown fields at every schema level.
- [ ] Validate `classification` is `synthetic_validation` or `private_external_evaluation`.
- [ ] Validate case IDs and claim IDs are non-empty and unique.
- [ ] Validate embedded C1 bundle `profile_version == "lin_tianji_claim_consumption_v1-exp"` and recompute `claim_consumption_digest`.
- [ ] Require exact equality of expected and actual claim-id sets.
- [ ] Validate authorization values and caveat-required redundancy.
- [ ] Validate specificity bounds and require `null/null` for expected abstention.
- [ ] Recompute and validate every `input_digest`.
- [ ] Score exact authorization, caveat, specificity band, and these six counters exactly:

```text
over_render_count
under_render_count
caveat_omission_count
unnecessary_caveat_count
specificity_overreach_count
specificity_excessive_downgrade_count
```
- [ ] Sort cases by `case_id` and claims by `claim_id` before aggregation.
- [ ] Emit only aggregate fields from the spec; do not emit case IDs, claim IDs, domains, or reason codes.
- [ ] `general_conformance_status` is `PASS` only for synthetic inputs with zero contamination/over-render/overreach/partial/missed; for private inputs use `METRICS_ONLY` unless contamination makes it `FAIL`.
- [ ] Keep `promotion_allowed=False` unconditionally.
- [ ] Compute deterministic `input_set_digest` and `report_digest`.
- [ ] Run Q1 tests GREEN:

```bash
python -m unittest -v tests.test_v16_claim_consumption_qualification
```

- [ ] Run frozen C1 regressions unchanged:

```bash
python -m unittest -v tests.test_v16_claim_consumption_contract
python -m pytest tests/test_v16_coordination_wrapper_integration.py tests/test_v16_coordination_policy_v2.py -q
```

- [ ] Commit:

```bash
git add engine/distribution/claim_consumption_qualification.py \
        tests/test_v16_claim_consumption_qualification.py
git commit -m "feat: add deterministic claim consumption qualification q1"
```

---

### Task 4: Deterministic CLI and method documentation

**Files:**
- Create: `tools/evaluate_v16_claim_consumption_qualification.py`
- Create: `docs/research/2026-09-01-v1.6-claim-consumption-qualification-q1.md`
- Modify: `tests/test_v16_claim_consumption_qualification.py`

**CLI:**

```bash
python tools/evaluate_v16_claim_consumption_qualification.py --input PATH [--output PATH]
```

- [ ] Add RED tests requiring two stdout runs over the synthetic fixture to be byte-identical and equal to the direct evaluator report.
- [ ] Add method-doc assertions requiring explicit statements that Q1 does not tune C1, does not reuse prior private labels, emits aggregate-only private reports, and cannot promote a release by itself.
- [ ] Run tests and observe RED for missing CLI/doc.
- [ ] Implement a thin CLI: load UTF-8 JSON, call evaluator, canonical pretty JSON with sorted keys + trailing newline; optional output writes the same bytes and stdout remains empty when `--output` is supplied.
- [ ] Write the method doc with schema, metrics, synthetic gate, private-sealing prerequisites, and `promotion_allowed=false` boundary.
- [ ] Re-run GREEN.
- [ ] Commit CLI/docs/tests.

---

### Task 5: Local full hard gates and deterministic distribution

**Files:**
- Generated only via builder: `dist/ai/metaphysics_lab.py` if the new engine module is included by source discovery.

- [ ] Run focused Q1 + frozen upstream suites.
- [ ] Run existing AI contract doc tests unchanged.
- [ ] Run:

```bash
python tools/build_ai_distribution.py
python tools/build_ai_distribution.py --check
```

- [ ] Inspect `git diff --name-only` and `git diff --stat`; do not hand-edit generated outputs.
- [ ] Run Validation-equivalent qualification/focused/prediction/release/package commands from `.github/workflows/lin-tianji-v1.5-validation.yml`.
- [ ] Run full repository regression under the ready Python 3.9 runtime.
- [ ] Run:

```bash
python -m compileall -q engine tools tests
```

- [ ] Commit builder outputs only after source/tests/docs are already GREEN.
- [ ] Require after commit:

```bash
python tools/build_ai_distribution.py --check
git diff --exit-code
git status --porcelain
```

Expected: builder check PASS, no diff, clean status.

---

### Task 6: GitHub transport + Hosted exact-SHA confirmation

- [ ] Move only locally verified source/test/doc content to `research/v1.6-claim-consumption-qualification-q1` based on the frozen C1 candidate.
- [ ] Rebuild generated outputs using the official builder and require byte hashes to equal the locally approved generated outputs before committing them.
- [ ] Create a same-tree empty Hosted-trigger commit if required by GitHub workflow-trigger behavior.
- [ ] Require one exact SHA to pass:

```text
Bazi qualification
Ziwei qualification
AI distribution rebuild/upload
focused regression
prediction validation
release surface
deterministic package
full repository regression
Python 3.9 compile
clean tree
```

- [ ] Freeze the Q1 candidate SHA only after all Hosted steps PASS.
- [ ] Do not execute a Q1 private evaluation in this cycle unless an independently prepared Q1 claim-level oracle and any non-zero private thresholds were sealed before evaluation. The old v1.6 Interpretation private aggregate is not such an oracle.
