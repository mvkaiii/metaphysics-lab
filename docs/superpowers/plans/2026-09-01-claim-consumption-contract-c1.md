# Claim Consumption Contract C1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic Python-owned claim-consumption authority between frozen Claim Evidence / Coordination output and Hybrid AI rendering, without changing upstream ranking, candidate, confidence, or Coordination semantics.

**Architecture:** Create one focused downstream module that validates the two immutable source bundles, joins packets to Coordination relations by `primary_domain`, computes a conservative authorized specificity, and emits `render`, `render_with_caveat`, or `abstain_claim`. Integrate the bundle into Interpretation v2, then update Hybrid AI fixed-contract docs so AI consumes Python decisions without recomputing them.

**Tech Stack:** Python 3.9, pytest/unittest, existing deterministic SHA-256 canonical JSON conventions, GitHub Actions validation, AI distribution builder.

**Spec:** `docs/research/2026-09-01-v1.6-claim-consumption-contract-c1-design.md`

## Global Constraints

- Base research SHA is `fff3eee3be8d5c7dca28a00df68228a48e261292`.
- Work only on `research/v1.6-claim-consumption-contract-c1`.
- `engine/distribution/coordination_policy_v2.py` semantics are frozen and MUST NOT change.
- Phase 3 is the only base ranking authority.
- Claim Evidence Packet candidate sets and legacy fields remain immutable.
- C1 may preserve or lower specificity only; never raise it.
- C1 never raises confidence.
- C1 never creates/reorders/removes domains or event-family candidates.
- No probability semantics.
- No private/Kai data may be read or used for policy selection before all general gates pass.
- No merge, default switch, tag, release, or private evaluation before Hosted hard gates pass on one candidate SHA.
- TDD is mandatory: no production code before an observed failing test.

---

## File map

- Create `engine/distribution/claim_consumption_contract.py`: deterministic validation, decision policy, canonical digest.
- Create `tests/test_v16_claim_consumption_contract.py`: synthetic/general-only C1 unit tests.
- Modify `engine/distribution/interpretation_contract_v2.py`: build and expose C1 bundle without mutating v1/Claim Evidence/Coordination.
- Modify `tests/test_v16_coordination_wrapper_integration.py`: wrapper integration and mutation guards.
- Modify `core/AI工作流程.md`: Hybrid consumes `claim_consumption_decisions` as Python authority.
- Modify `core/核心提示詞.md`: fixed Hybrid guardrails for C1.
- Modify `tests/test_ai_contract_docs.py`: RED/GREEN contract-doc assertions.
- Regenerate `dist/ai/metaphysics_core.md`, `dist/ai/metaphysics_lab.py`, `dist/ai/project_instructions.txt` only through `tools/build_ai_distribution.py` if the builder declares them generated outputs.

---

### Task 1: Freeze synthetic C1 RED tests

**Files:**
- Create: `tests/test_v16_claim_consumption_contract.py`

**Interfaces:**
- Consumes: frozen Claim Evidence and Coordination bundle shapes.
- Produces: desired public API `build_claim_consumption_bundle(*, claim_evidence_bundle, coordination_bundle) -> dict` and constant `CLAIM_CONSUMPTION_PROFILE_VERSION`.

- [ ] **Step 1: Write the failing import and synthetic fixtures**

Use real bundle builders where practical; do not import any private data. The test file begins with:

```python
import copy
import hashlib
import json

import pytest

from engine.distribution.claim_consumption_contract import (
    CLAIM_CONSUMPTION_PROFILE_VERSION,
    build_claim_consumption_bundle,
)
```

Provide a canonical digest helper and minimal synthetic claim/coordination bundle fixture that includes valid source digests, target scope, packet IDs, evidence, abstentions, confidence, and relations.

- [ ] **Step 2: Add G1/G2/G3/G4 behavior tests**

Required assertions:

```python
assert direct_decision["decision"] == "render"
assert layered_decision["decision"] == "render_with_caveat"
assert "layered_complement" in layered_decision["reason_codes"]
assert {d["decision"] for d in parallel_result["decisions"]} == {"render_with_caveat"}
assert {d["primary_domain"] for d in parallel_result["decisions"]} == {"career", "finance"}
assert single_decision["decision"] == "render_with_caveat"
assert single_decision["coordination_relation"] == "single_system_support"
```

The direct-convergence fixture must have no existing abstention and non-low confidence so `render` is reachable.

- [ ] **Step 3: Add G5/G6/G7 fail-closed and specificity tests**

Required assertions:

```python
with pytest.raises(ValueError):
    build_claim_consumption_bundle(
        claim_evidence_bundle=tampered_claim_bundle,
        coordination_bundle=coordination_bundle,
    )

assert downgraded["original_effective_specificity"] == "concrete_event"
assert downgraded["authorized_specificity"] == "event_family"
assert "specificity_downgraded" in downgraded["reason_codes"]
```

Also mutate a coordination cap upward beyond packet authority and assert fail-closed rather than upgrade.

- [ ] **Step 4: Add G8/G9/G10/G11 tests**

Required assertions:

```python
assert build_claim_consumption_bundle(...) == build_claim_consumption_bundle(...reversed_inputs...)
assert legacy_parallel_decision["coordination_relation"] == "parallel_signals"
assert legacy_parallel_decision["decision"] == "render_with_caveat"
assert original_claim_bundle == frozen_claim_bundle
assert original_coordination_bundle == frozen_coordination_bundle
assert zero_support["decision"] == "abstain_claim"
assert zero_support["reason_codes"] == ["no_same_scope_target_support"]
```

- [ ] **Step 5: Observe RED before production code**

Run in a Python 3.9-capable environment:

```bash
python -m pytest tests/test_v16_claim_consumption_contract.py -q
```

Expected RED: import failure for `engine.distribution.claim_consumption_contract` because the module does not exist yet. A syntax/fixture failure is not an acceptable RED; fix the test until the failure is specifically caused by the missing production module.

- [ ] **Step 6: Commit RED only**

```bash
git add tests/test_v16_claim_consumption_contract.py
git commit -m "test: define claim consumption contract c1 red gate"
```

Do not create production implementation in this commit.

---

### Task 2: Implement minimal deterministic C1 module

**Files:**
- Create: `engine/distribution/claim_consumption_contract.py`
- Test: `tests/test_v16_claim_consumption_contract.py`

**Interfaces:**
- Consumes: complete Claim Evidence bundle and frozen Coordination bundle.
- Produces: `CLAIM_CONSUMPTION_PROFILE_VERSION = "lin_tianji_claim_consumption_v1-exp"` and `build_claim_consumption_bundle(...)`.

- [ ] **Step 1: Add profile constants and canonical helpers**

```python
CLAIM_CONSUMPTION_PROFILE_VERSION = "lin_tianji_claim_consumption_v1-exp"
_ALLOWED_DECISIONS = {"render", "render_with_caveat", "abstain_claim"}
_ALLOWED_RELATIONS = {
    "direct_domain_convergence",
    "layered_complement",
    "parallel_signals",
    "parallel_context",
    "single_system_support",
}
_SPECIFICITY_ORDER = {
    "domain": 0,
    "event_family": 1,
    "concrete_event": 2,
    "highly_specific_event": 3,
}
```

Use the repository canonical JSON pattern: UTF-8, sorted keys, compact separators, `allow_nan=False`, SHA-256.

- [ ] **Step 2: Validate source bundle digests and provenance alignment**

Implement validation that recomputes and verifies `claim_evidence_digest` and `coordination_digest`, then requires:

```python
claim_bundle["target_scope"] == coordination_bundle["target_scope"]
claim_bundle["base_ranking_digest"] == coordination_bundle["source_ranking_digest"]
claim_bundle["structural_interpretation_digest"] == coordination_bundle["source_interpretation_digest"]
```

Require unique equal domain sets across packets and relations.

- [ ] **Step 3: Implement conservative decision function**

For each packet/relation pair:

```python
authorized = min(
    (packet["effective_specificity"], relation["coordination_specificity_cap"]),
    key=lambda value: _SPECIFICITY_ORDER[value],
)
```

Reject a coordination cap that is more permissive than packet effective specificity.

Decision precedence:

```text
if system_support_count == 0:
    abstain_claim
elif any caveat condition:
    render_with_caveat
else:
    render
```

Canonical caveat reasons in this order:

```python
_REASON_ORDER = (
    "single_system_support",
    "parallel_context",
    "parallel_signals",
    "layered_complement",
    "specificity_downgraded",
    "low_confidence",
    "existing_abstention",
)
```

Do not use legacy `cross_system_relation` to select the decision.

- [ ] **Step 4: Emit deterministic output without mutating inputs**

Output:

```python
{
    "profile_version": CLAIM_CONSUMPTION_PROFILE_VERSION,
    "claim_evidence_digest": claim_bundle["claim_evidence_digest"],
    "coordination_digest": coordination_bundle["coordination_digest"],
    "target_scope": claim_bundle["target_scope"],
    "decisions": decisions_sorted_by_primary_domain,
    "claim_consumption_digest": canonical_digest_of_previous_fields,
}
```

Each decision copies:

```text
claim_id
primary_domain
decision
original_effective_specificity
authorized_specificity
confidence_class
coordination_relation
reason_codes
```

- [ ] **Step 5: Run focused tests to GREEN**

```bash
python -m pytest tests/test_v16_claim_consumption_contract.py -q
```

Expected: PASS.

- [ ] **Step 6: Run frozen upstream regressions**

```bash
python -m pytest \
  tests/test_distribution_claim_evidence.py \
  tests/test_v16_coordination_policy_v2.py \
  -q
```

Expected: PASS with no changed upstream semantics.

- [ ] **Step 7: Commit minimal module**

```bash
git add engine/distribution/claim_consumption_contract.py tests/test_v16_claim_consumption_contract.py
git commit -m "feat: add deterministic claim consumption contract c1"
```

---

### Task 3: Integrate C1 into Interpretation v2 without changing v1

**Files:**
- Modify: `engine/distribution/interpretation_contract_v2.py`
- Modify: `tests/test_v16_coordination_wrapper_integration.py`

**Interfaces:**
- Consumes: `build_claim_consumption_bundle` from Task 2.
- Produces: v2 fields `claim_consumption_profile_version`, `claim_consumption_digest`, `claim_consumption_decisions`.

- [ ] **Step 1: Write wrapper RED tests first**

Add tests asserting:

```python
result["claim_consumption_profile_version"] == "lin_tianji_claim_consumption_v1-exp"
assert result["claim_consumption_digest"]
assert result["claim_consumption_decisions"]
```

For a disjoint-domain fixture:

```python
assert {row["coordination_relation"] for row in result["claim_consumption_decisions"]} == {"parallel_signals"}
assert {row["decision"] for row in result["claim_consumption_decisions"]} == {"render_with_caveat"}
```

Keep the existing v1 deterministic equality assertion unchanged.

- [ ] **Step 2: Run wrapper tests and observe RED**

```bash
python -m pytest tests/test_v16_coordination_wrapper_integration.py -q
```

Expected RED: missing C1 fields in v2 output.

- [ ] **Step 3: Add minimal integration**

Import `build_claim_consumption_bundle`, call it after Coordination is built, then deep-copy only its public metadata/decisions into v2 result before recomputing the v2 digest.

Do not modify `build_interpretation_contract`, Claim Evidence, or Coordination inputs.

- [ ] **Step 4: Verify focused GREEN**

```bash
python -m pytest \
  tests/test_v16_claim_consumption_contract.py \
  tests/test_v16_coordination_wrapper_integration.py \
  tests/test_v16_coordination_policy_v2.py \
  tests/test_distribution_claim_evidence.py \
  -q
```

Expected: PASS.

- [ ] **Step 5: Commit integration**

```bash
git add engine/distribution/interpretation_contract_v2.py tests/test_v16_coordination_wrapper_integration.py
git commit -m "feat: expose claim consumption authority in interpretation v2"
```

---

### Task 4: Add Hybrid AI consumer guardrails with TDD

**Files:**
- Modify: `tests/test_ai_contract_docs.py`
- Modify: `core/AI工作流程.md`
- Modify: `core/核心提示詞.md`

**Interfaces:**
- Consumes: v2 `claim_consumption_decisions` from Task 3.
- Produces: fixed Hybrid contract that renders only within Python-owned decision/specificity authority.

- [ ] **Step 1: Add doc-contract RED test**

Extend `tests/test_ai_contract_docs.py` to require all phrases:

```text
claim_consumption_decisions
claim_consumption_digest
render_with_caveat
abstain_claim
claim consumption Python authority
不得重新判定 claim consumption decision
不得把 abstain_claim 改成可呈現 claim
不得高於 authorized_specificity
不得因 claim consumption 提高 confidence
```

- [ ] **Step 2: Run doc test and observe RED**

```bash
python -m pytest tests/test_ai_contract_docs.py -q
```

Expected RED: new C1 phrases absent from fixed docs.

- [ ] **Step 3: Update fixed docs minimally**

Add a compact v2 C1 consumer section after current Coordination guardrails:

- Python `decision` is authoritative.
- `render`: AI may render only within existing claim fields and `authorized_specificity`.
- `render_with_caveat`: AI must preserve the supplied conservative reason; it may not erase or invert it.
- `abstain_claim`: AI must not render that claim as a prospective claim.
- AI must not recompute decisions from raw Bazi/Ziwei evidence.
- AI must not raise confidence or specificity.
- reality context may still affect strategy only under the existing reality-context policy; it does not reopen an abstained forecast claim.

Do not embed runtime snapshots or private-case examples.

- [ ] **Step 4: Verify doc GREEN**

```bash
python -m pytest tests/test_ai_contract_docs.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit Hybrid contract changes**

```bash
git add tests/test_ai_contract_docs.py core/AI工作流程.md core/核心提示詞.md
git commit -m "docs: bind hybrid rendering to claim consumption authority"
```

---

### Task 5: Rebuild deterministic AI distribution and run local hard gates

**Files:**
- Generated only through: `tools/build_ai_distribution.py`
- Expected generated candidates: `dist/ai/metaphysics_core.md`, `dist/ai/metaphysics_lab.py`, `dist/ai/project_instructions.txt`

**Interfaces:**
- Consumes: fixed docs and current runtime source.
- Produces: deterministic distribution synchronized to source.

- [ ] **Step 1: Rebuild through the formal builder**

```bash
python tools/build_ai_distribution.py
```

- [ ] **Step 2: Verify builder parity**

```bash
python tools/build_ai_distribution.py --check
```

Expected: PASS.

- [ ] **Step 3: Inspect generated diff before committing**

```bash
git status --porcelain
git diff --stat
git diff -- dist/ai/metaphysics_core.md dist/ai/metaphysics_lab.py dist/ai/project_instructions.txt
```

Only deterministic builder-authorized generated changes are allowed. No manually edited generated content.

- [ ] **Step 4: Run focused regressions**

```bash
python -m pytest \
  tests/test_v16_claim_consumption_contract.py \
  tests/test_v16_coordination_wrapper_integration.py \
  tests/test_v16_coordination_policy_v2.py \
  tests/test_distribution_claim_evidence.py \
  tests/test_ai_contract_docs.py \
  -q
```

Expected: PASS.

- [ ] **Step 5: Run full repository regression**

Use the repository's Hosted-equivalent Python test command. At minimum:

```bash
python -m unittest discover -s tests
```

and any pytest suites not included by unittest discovery according to the Validation workflow.

Expected: PASS.

- [ ] **Step 6: Compile on Python 3.9 semantics**

```bash
python -m compileall -q engine tools tests
```

Expected: PASS.

- [ ] **Step 7: Commit generated artifacts only after all local gates pass**

```bash
git add dist/ai/metaphysics_core.md dist/ai/metaphysics_lab.py dist/ai/project_instructions.txt
git commit -m "build: refresh ai distribution for claim consumption c1"
```

If only a subset is changed by the formal builder, stage only that subset.

- [ ] **Step 8: Re-run builder check and clean-tree gate after the commit**

```bash
python tools/build_ai_distribution.py --check
git diff --exit-code
git status --porcelain
```

Expected: builder check PASS, empty diff, empty status.

---

### Task 6: Hosted validation on one exact candidate SHA

**Files:**
- No source change unless a general-only failure requires a new TDD cycle.

**Interfaces:**
- Consumes: exact research branch candidate SHA.
- Produces: Hosted gate evidence for freeze eligibility.

- [ ] **Step 1: Record exact candidate SHA**

```bash
git rev-parse HEAD
```

- [ ] **Step 2: Run/observe the formal Validation workflow for that SHA**

Required same-SHA Hosted results:

```text
focused/general regression PASS
full repository regression PASS
AI distribution rebuild/check PASS
Python 3.9 compile PASS
Verify clean tree PASS
```

- [ ] **Step 3: If any Hosted general gate fails, STOP before private**

Classify the failure using general evidence only. If a fix changes behavior, return to RED before implementation. Every fix creates a new candidate SHA and requires the complete Hosted gate again.

- [ ] **Step 4: Freeze only after every Hosted gate is GREEN on one SHA**

Record the exact SHA in the research result/checkpoint. Do not merge/default-switch/tag/release yet.

---

### Task 7: Private external evaluation eligibility gate

**Files:**
- No policy/code change during evaluation.

**Interfaces:**
- Consumes: one frozen Hosted-GREEN candidate SHA.
- Produces: one external private evaluation result only.

- [ ] **Step 1: Verify all preconditions before reading private data**

Required:

```text
C1 focused GREEN
Coordination frozen regression GREEN
Interpretation v1/v2 GREEN
Hybrid contract GREEN
builder parity GREEN
full regression GREEN
compile GREEN
clean tree GREEN
Hosted all GREEN on exact frozen SHA
```

- [ ] **Step 2: Execute private evaluation once**

Private data is evaluation-only and may not select/tune C1.

- [ ] **Step 3: Apply stop rule**

If private PASS: record result for governance review; still no automatic promotion.

If private FAIL: record `STOP_CYCLE`. Do not alter C1, create C1.1, adjust reason codes, change domain mapping, or revise render policy using the private result. Any future attempt starts from a new independent research design.

---

## Self-review

- Spec coverage: all design sections map to Tasks 1-7; no upstream authority rewrite is required.
- Placeholder scan: no TODO/TBD behavior remains; all behavior-changing tasks specify test-first assertions and expected RED causes.
- Type consistency: the public builder name, bundle field names, decision labels, profile version, specificity field names, and Hybrid authority names are consistent across tasks.
