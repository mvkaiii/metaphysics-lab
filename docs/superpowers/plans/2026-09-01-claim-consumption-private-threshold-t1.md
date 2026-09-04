# Claim Consumption Private Threshold Governance T1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立 general-only、deterministic、aggregate-only 的 T1 private release gate，使用事前 freeze 的 strict-zero policy 對 eligible Q1 private aggregate report 輸出 `PASS / FAIL / INELIGIBLE`，且不修改 Q1/O1/C1 semantics。

**Architecture:** 新增獨立 `claim_consumption_private_threshold.py`，只接受五份 aggregate artifacts：frozen policy、sampling eligibility receipt、O1 public seal receipt、evaluation identity receipt、Q1 private aggregate report。module 先 strict validate/digest-check，再做 sequencing/identity eligibility，最後才比較 strict-zero metrics；thin CLI 只讀這五份 JSON 並輸出 canonical report。正式 policy artifact 為 public general governance artifact，可進 git；所有 tests 僅用 synthetic fixtures。

**Tech Stack:** Python 3.9、stdlib (`json`, `hashlib`, `datetime`, `argparse`, `pathlib`)、`unittest`、既有 `tools/build_ai_distribution.py`。

**Spec:** `docs/superpowers/specs/2026-09-01-claim-consumption-private-threshold-t1-design.zh-TW.md`

## Global Constraints

- Upstream O1 frozen candidate：GitHub `c810136936c4804560218c2cb03e86734afda37f`，tree `74f044bf7ad7616dba4cc2280021d6334ada1f6f`。
- Q1 scoring semantics、O1 seal/join semantics、C1 production policy、Coordination、Phase 3、Interpretation ranking、Hybrid render authority全部 read-only。
- T1 tests/source 不得讀、import 或引用任何 private adjudication workspace、raw private artifact、prior private aggregate metrics、case ids、claim ids 或 current exposed pair candidate behavior。
- T1 v1 policy profile 固定為 `lin_tianji_claim_consumption_private_strict_zero_v1`；所有九個 thresholds 必須是 `0`。
- `promotion_allowed=false` 必須存在於 policy、sampling receipt、evaluation identity receipt 與 final report。
- Invalid/tampered schema 或 digest 必須 raise `ValueError` / CLI non-zero；合法但 sequencing/sampling/identity 不合格才輸出 `INELIGIBLE`。
- T1 cycle 不執行任何 private Q1 evaluator；current exposed pair 永久不得用 T1 retrospective scoring。

---

## File Structure

- Create `engine/distribution/claim_consumption_private_threshold.py`：T1 schemas、validators、canonical digests、eligibility checks、strict-zero gate、report digest。
- Create `qualification/claim_consumption/v1.6/private-release-policy.strict-zero.v1.json`：事前 freeze、general-only strict-zero policy artifact。
- Create `tools/evaluate_v16_claim_consumption_private_threshold.py`：thin CLI，只讀五份 aggregate JSON。
- Create `tests/fixtures/v1.6-claim-consumption-private-threshold.synthetic.v1.json`：純 synthetic 五 artifact baseline。
- Create `tests/test_v16_claim_consumption_private_threshold.py`：T1-G1…G21 synthetic conformance、CLI parity、private contamination guard。
- Create `docs/research/2026-09-01-v1.6-claim-consumption-private-threshold-t1.md`：general governance method、prospective-only 限制與 hard gates。
- Modify only generated `dist/ai/metaphysics_lab.py` through formal builder if the new engine module is included by distribution rules.

---

### Task 1: Documents-only plan checkpoint

**Files:**
- Create: `docs/superpowers/plans/2026-09-01-claim-consumption-private-threshold-t1.md`

**Interfaces:**
- Consumes: approved T1 design spec.
- Produces: executable task sequence only; no production semantics.

- [ ] **Step 1: Verify workspace and approved spec**

```bash
git status --short
git branch --show-current
git rev-parse HEAD
sha256sum docs/superpowers/specs/2026-09-01-claim-consumption-private-threshold-t1-design.zh-TW.md
```

Expected: clean workspace before this plan file, branch `research/v1.6-claim-consumption-private-threshold-t1`, approved spec SHA256 `5b4ca87207c4d39bb63d4af45335c53c32a72e9f4b34ab48638845e90757b45b`.

- [ ] **Step 2: Plan self-review**

```bash
python - <<'PY'
from pathlib import Path
p = Path('docs/superpowers/plans/2026-09-01-claim-consumption-private-threshold-t1.md')
text = p.read_text()
for forbidden in ('T'+'BD', 'T'+'ODO', 'implement'+' later', 'fill in'+' details'):
    assert forbidden not in text
for required in (
    'validate_private_release_policy',
    'validate_sampling_eligibility_receipt',
    'validate_private_evaluation_identity_receipt',
    'validate_oracle_seal_receipt',
    'validate_q1_private_report',
    'evaluate_claim_consumption_private_threshold',
):
    assert required in text
print('plan self-review: PASS')
PY
```

Expected: `plan self-review: PASS`.

- [ ] **Step 3: Commit documents-only plan**

```bash
git add docs/superpowers/plans/2026-09-01-claim-consumption-private-threshold-t1.md
git commit -m 'docs: add T1 private threshold implementation plan'
```

Expected: one documents-only commit.

---

### Task 2: Synthetic RED for T1 authority

**Files:**
- Create: `tests/fixtures/v1.6-claim-consumption-private-threshold.synthetic.v1.json`
- Create: `tests/test_v16_claim_consumption_private_threshold.py`

**Interfaces:**
- Consumes: frozen Q1 report schema names and O1 public receipt fields from approved spec.
- Produces: RED contract for `engine.distribution.claim_consumption_private_threshold`.

- [ ] **Step 1: Create one valid synthetic baseline fixture**

Fixture top-level keys are exactly `policy`, `sampling_receipt`, `oracle_receipt`, `evaluation_identity_receipt`, `q1_report`. Use opaque synthetic digests and counts only; no private/case/claim identifiers. Timestamps must satisfy:

```text
policy.policy_frozen_at = 2026-09-01T14:30:00Z
sampling_receipt.sealed_at = 2026-09-01T14:31:00Z
oracle_receipt.sealed_at = 2026-09-01T14:32:00Z
evaluation_identity_receipt.bound_at = 2026-09-01T14:33:00Z
```

Baseline counts: `case_count=4`, `claim_count=12`; Q1 alignment `matched=12, partial=0, missed=0`; every strict-zero metric is 0. Generate each digest with canonical JSON rather than hard-coding inconsistent values.

- [ ] **Step 2: Write RED tests**

Create `unittest.TestCase` tests that import the six public T1 functions and cover valid PASS, each nonzero strict metric FAIL, sampling/sequencing INELIGIBLE, identity/count mismatch INELIGIBLE, tamper/unknown rejection, aggregate-only deterministic report.

- [ ] **Step 3: Verify RED**

```bash
python -m py_compile tests/test_v16_claim_consumption_private_threshold.py
python -m json.tool tests/fixtures/v1.6-claim-consumption-private-threshold.synthetic.v1.json >/dev/null
python -m unittest -v tests.test_v16_claim_consumption_private_threshold
```

Expected: fails only with `ModuleNotFoundError: engine.distribution.claim_consumption_private_threshold`.

- [ ] **Step 4: Commit RED-only evidence**

```bash
git add tests/fixtures/v1.6-claim-consumption-private-threshold.synthetic.v1.json tests/test_v16_claim_consumption_private_threshold.py
git commit -m 'test: add RED contract for T1 private threshold gate'
```

---

### Task 3: Minimal policy/receipt/report validators and strict-zero evaluator GREEN

**Files:**
- Create: `engine/distribution/claim_consumption_private_threshold.py`
- Test: `tests/test_v16_claim_consumption_private_threshold.py`

**Interfaces:**
- Produces `validate_private_release_policy(payload: object) -> dict`.
- Produces `validate_sampling_eligibility_receipt(payload: object) -> dict`.
- Produces `validate_private_evaluation_identity_receipt(payload: object) -> dict`.
- Produces `validate_oracle_seal_receipt(payload: object) -> dict`.
- Produces `validate_q1_private_report(payload: object) -> dict`.
- Produces `evaluate_claim_consumption_private_threshold(policy: object, sampling_receipt: object, oracle_receipt: object, evaluation_identity_receipt: object, q1_report: object) -> dict`.

- [ ] **Step 1: Implement canonical primitives and exact schema constants**

```python
POLICY_SCHEMA = 'v1.6-claim-consumption-private-release-policy.v1'
SAMPLING_SCHEMA = 'v1.6-claim-consumption-sampling-eligibility-receipt.v1'
IDENTITY_SCHEMA = 'v1.6-claim-consumption-private-evaluation-identity-receipt.v1'
ORACLE_RECEIPT_SCHEMA = 'v1.6-claim-consumption-oracle-seal-receipt.v1'
Q1_REPORT_SCHEMA = 'v1.6-claim-consumption-qualification-report.v1'
REPORT_SCHEMA = 'v1.6-claim-consumption-private-release-gate-report.v1'
POLICY_PROFILE = 'lin_tianji_claim_consumption_private_strict_zero_v1'
```

Canonical JSON: `ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False`; reject bool where non-negative integer is required.

- [ ] **Step 2: Implement policy validator**

Exact policy fields: `schema_version`, `policy_profile`, `policy_frozen_at`, `thresholds`, `policy_digest`, `promotion_allowed`. Exact threshold fields are the nine spec metrics; every value must equal integer `0`; `promotion_allowed=False`; validate canonical digest excluding `policy_digest`.

- [ ] **Step 3: Implement sampling and evaluation identity validators**

Sampling exact fields and rules follow the spec. Identity exact fields and rules follow the spec. Validate each receipt digest excluding `receipt_digest`.

- [ ] **Step 4: Implement O1 public receipt validator**

Reconstruct the O1 private seal digest payload from receipt aggregate fields using schema `v1.6-claim-consumption-oracle-seal.v1`; require `status='SEALED'`, `promotion_allowed=False` and exact `seal_digest`.

- [ ] **Step 5: Implement Q1 private aggregate report validator**

Require exact frozen Q1 report fields, `classification='private_external_evaluation'`, `general_conformance_status='METRICS_ONLY'`, `promotion_allowed=False`; validate report digest excluding `report_digest`; require all counters non-negative and `matched + partial + missed == claim_count`.

- [ ] **Step 6: Implement eligibility then threshold evaluation**

Only after all artifacts validate, output `INELIGIBLE` if sampling status is not ELIGIBLE, sequencing fails, case/claim counts mismatch, identity digests mismatch, identity bound_at is before oracle seal, or oracle receipt contamination is nonzero. Eligible evidence gets `FAIL` if any strict-zero metric is >0, else `PASS`.

- [ ] **Step 7: Build deterministic aggregate-only report**

Use exact report fields from spec. `candidate_sha` only comes from identity receipt. `promotion_allowed=False`. Never include case/claim ids, domain, prose, expected/actual decisions or private data.

- [ ] **Step 8: Run GREEN and frozen regressions**

```bash
python -m unittest -v \
  tests.test_v16_claim_consumption_private_threshold \
  tests.test_v16_claim_consumption_qualification \
  tests.test_v16_claim_consumption_oracle_seal \
  tests.test_v16_claim_consumption_contract
```

Expected: all PASS.

- [ ] **Step 9: Commit evaluator GREEN**

```bash
git add engine/distribution/claim_consumption_private_threshold.py tests/test_v16_claim_consumption_private_threshold.py tests/fixtures/v1.6-claim-consumption-private-threshold.synthetic.v1.json
git commit -m 'research: add strict-zero T1 private threshold authority'
```

---

### Task 4: Frozen general policy artifact + CLI + governance doc RED→GREEN

**Files:**
- Create: `qualification/claim_consumption/v1.6/private-release-policy.strict-zero.v1.json`
- Create: `tools/evaluate_v16_claim_consumption_private_threshold.py`
- Create: `docs/research/2026-09-01-v1.6-claim-consumption-private-threshold-t1.md`
- Modify: `tests/test_v16_claim_consumption_private_threshold.py`

**Interfaces:** CLI args are `--policy`, `--sampling-receipt`, `--oracle-receipt`, `--evaluation-identity-receipt`, `--q1-report`, optional `--output`.

- [ ] **Step 1: Add RED tests for policy artifact, CLI parity and governance markers**

Assert the frozen public policy validates byte-for-byte, CLI output matches direct API, output-file parity works, method doc includes `promotion_allowed=false`, `current exposed pair`, prospective sequence and prohibition wording, and source/tests/docs do not reference private workspace/metrics/digests.

- [ ] **Step 2: Verify RED**

```bash
python -m unittest -v tests.test_v16_claim_consumption_private_threshold
```

Expected: failures only because policy artifact/CLI/method doc are absent.

- [ ] **Step 3: Create deterministic policy artifact**

Capture the actual current UTC RFC3339 `Z` timestamp at policy-artifact creation as `policy_frozen_at`, then freeze it permanently; all nine thresholds are `0`. The timestamp is governance metadata and must not be backdated or derived from private outcomes.

- [ ] **Step 4: Implement thin CLI**

CLI loads only five aggregate JSON files, calls evaluator once, emits canonical JSON plus newline or byte-identical output file. No raw oracle, joined private input, candidate case output, Git, network or private directory access.

- [ ] **Step 5: Write governance method doc**

Document exact sequence: `T1 policy freeze -> sampling receipt freeze -> new oracle seal -> candidate freeze -> candidate output -> O1 join -> evaluation identity freeze -> Q1 exactly once -> T1 gate`. State current exposed pair is permanently prospective-ineligible and this T1 cycle runs no private evaluator.

- [ ] **Step 6: Run GREEN**

```bash
python -m unittest -v tests.test_v16_claim_consumption_private_threshold
```

- [ ] **Step 7: Commit CLI/policy/docs**

```bash
git add qualification/claim_consumption/v1.6/private-release-policy.strict-zero.v1.json tools/evaluate_v16_claim_consumption_private_threshold.py docs/research/2026-09-01-v1.6-claim-consumption-private-threshold-t1.md tests/test_v16_claim_consumption_private_threshold.py
git commit -m 'research: freeze strict-zero T1 private release policy'
```

---

### Task 5: Formal builder and focused regression

**Files:**
- Modify only if generated: `dist/ai/metaphysics_lab.py`

- [ ] **Step 1: Run formal builder and inspect scope**

```bash
python tools/build_ai_distribution.py
python tools/build_ai_distribution.py --check
git diff --check
git status --short
```

- [ ] **Step 2: Run T1 + frozen focused regression**

```bash
python -m unittest -v \
  tests.test_v16_claim_consumption_private_threshold \
  tests.test_v16_claim_consumption_qualification \
  tests.test_v16_claim_consumption_oracle_seal \
  tests.test_v16_claim_consumption_contract \
  tests.test_v16_coordination_wrapper_integration \
  tests.test_v16_coordination_policy_v2
```

- [ ] **Step 3: Commit deterministic generated artifact**

```bash
git add dist/ai/metaphysics_lab.py
git commit -m 'build: refresh AI runtime for T1 private threshold authority'
```

Only commit if builder changed the file.

---

### Task 6: Full local hard gates

- [ ] **Step 1: Run qualification/release/package gates** using current `.github/workflows/validation.yml` commands verbatim.
- [ ] **Step 2: Run official focused regression command** from the same workflow verbatim.
- [ ] **Step 3: Run `python -m unittest discover -v` once to completion; require zero failures/errors.**
- [ ] **Step 4: Run `python -m compileall -q engine tools tests` under Python 3.9.x; require exit 0.**
- [ ] **Step 5: Fresh builder parity and clean tree:**

```bash
python tools/build_ai_distribution.py --check
git diff --check
git diff --exit-code
test -z "$(git status --porcelain)"
```

---

### Task 7: GitHub transport, Hosted same-SHA confirmation and freeze

- [ ] **Step 1:** Byte-transport exact local tree onto branch `research/v1.6-claim-consumption-private-threshold-t1` forked from frozen O1 SHA `c810136936c4804560218c2cb03e86734afda37f`; verify every candidate file SHA256 and generated runtime SHA.
- [ ] **Step 2:** Compare GitHub branch against frozen O1; allow only T1 module/tests/fixture/policy/CLI/docs/plan/spec and canonical generated runtime; forbid private artifacts.
- [ ] **Step 3:** Create Draft research PR base `research/v1.6-claim-consumption-oracle-seal-o1` and Draft main CI carrier; never merge carrier.
- [ ] **Step 4:** Require Hosted same-SHA PASS for validation SHA, qualifications, builder, focused regression, prediction, release surface, deterministic package, full regression, Python 3.9 compile and clean tree.
- [ ] **Step 5:** Freeze candidate; authoritative PR status `GENERAL_HOSTED_QUALIFIED / PRIVATE_NOT_AUTHORIZED`; close carrier; record no private Q1 evaluator ran and current exposed pair remains permanently prospective-ineligible.
