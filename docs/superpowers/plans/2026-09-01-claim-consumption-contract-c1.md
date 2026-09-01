# Claim Consumption Contract C1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic Python-owned claim-consumption authority between frozen Claim Evidence / Coordination output and Hybrid AI rendering, without changing upstream ranking, candidates, confidence, or Coordination semantics.

**Architecture:** A new downstream module validates immutable Claim Evidence and Coordination bundles, joins them by `primary_domain`, computes conservative authorized specificity, and emits `render`, `render_with_caveat`, or `abstain_claim`. Interpretation v2 exposes the result; Hybrid AI only consumes it.

**Tech Stack:** Python 3.9, pytest/unittest, deterministic canonical JSON + SHA-256, GitHub Actions, existing AI distribution builder.

**Spec:** `docs/research/2026-09-01-v1.6-claim-consumption-contract-c1-design.md`

## Global Constraints

- Base SHA: `fff3eee3be8d5c7dca28a00df68228a48e261292`.
- Branch: `research/v1.6-claim-consumption-contract-c1`.
- `engine/distribution/coordination_policy_v2.py` is frozen/read-only.
- Phase 3 remains the only base ranking authority.
- Claim Evidence candidate sets and legacy fields remain immutable.
- C1 may preserve/lower specificity only; never raise it or confidence.
- C1 never creates/reorders/removes domains or event-family candidates.
- No probability semantics.
- No private/Kai data before all general Hosted gates are GREEN.
- No merge/default switch/tag/release/private evaluation before exact-SHA Hosted GREEN.
- TDD mandatory: no production code before observed RED.

---

### Task 1: Synthetic/general RED gate

**Files:**
- Create: `tests/test_v16_claim_consumption_contract.py`

**Produces:** desired API:

```python
from engine.distribution.claim_consumption_contract import (
    CLAIM_CONSUMPTION_PROFILE_VERSION,
    build_claim_consumption_bundle,
)
```

- [ ] Write synthetic fixtures only; no private imports.
- [ ] Add direct convergence test: no caveat => `render`.
- [ ] Add layered complement test: `render_with_caveat`, reason includes `layered_complement`.
- [ ] Add parallel-signals test: disjoint valid domains both remain, both caveated, legacy conflict cannot override.
- [ ] Add single-system test: caveated, no invented cross-system support.
- [ ] Add malformed digest/source mismatch tests: `ValueError` fail-closed.
- [ ] Add specificity downgrade test: `concrete_event -> event_family` and `specificity_downgraded`.
- [ ] Add attempted specificity upgrade test: fail-closed.
- [ ] Add deterministic repeatability test: calling builder twice with the exact same valid source bundles yields identical result/digest; decisions are canonical `primary_domain` order. Do **not** require artificially reordered/re-digested upstream bundles to share a digest because that changes source identity.
- [ ] Add mutation test: both source bundles unchanged.
- [ ] Add zero-target-support test: `abstain_claim`, reason exactly `no_same_scope_target_support`.
- [ ] Run:

```bash
python -m pytest tests/test_v16_claim_consumption_contract.py -q
```

Expected RED: `ModuleNotFoundError: engine.distribution.claim_consumption_contract`. Syntax/fixture failures do not count.

- [ ] Commit RED only:

```bash
git add tests/test_v16_claim_consumption_contract.py
git commit -m "test: define claim consumption contract c1 red gate"
```

---

### Task 2: Minimal C1 implementation

**Files:**
- Create: `engine/distribution/claim_consumption_contract.py`
- Test: `tests/test_v16_claim_consumption_contract.py`

**Public interface:**

```python
CLAIM_CONSUMPTION_PROFILE_VERSION = "lin_tianji_claim_consumption_v1-exp"

def build_claim_consumption_bundle(
    *,
    claim_evidence_bundle: Mapping[str, object],
    coordination_bundle: Mapping[str, object],
) -> dict:
    ...
```

- [ ] Implement canonical JSON/SHA-256 helpers using sorted keys, compact separators, UTF-8, `allow_nan=False`.
- [ ] Recompute/validate both source digests.
- [ ] Require matching target scope, ranking digest, structural interpretation digest, and unique equal domain sets.
- [ ] Allow only Coordination labels:

```python
{
    "direct_domain_convergence",
    "layered_complement",
    "parallel_signals",
    "parallel_context",
    "single_system_support",
}
```

- [ ] Compute `authorized_specificity` as the most conservative of packet effective specificity and Coordination cap; reject cap > packet authority.
- [ ] Decision precedence:

```text
system_support_count == 0 -> abstain_claim
else any caveat -> render_with_caveat
else -> render
```

- [ ] Canonical caveat order:

```python
(
    "single_system_support",
    "parallel_context",
    "parallel_signals",
    "layered_complement",
    "specificity_downgraded",
    "low_confidence",
    "existing_abstention",
)
```

- [ ] Emit decisions sorted by `primary_domain` and bundle fields:

```text
profile_version
claim_evidence_digest
coordination_digest
target_scope
decisions
claim_consumption_digest
```

- [ ] Run focused GREEN:

```bash
python -m pytest tests/test_v16_claim_consumption_contract.py -q
```

- [ ] Run frozen upstream regressions:

```bash
python -m pytest tests/test_distribution_claim_evidence.py tests/test_v16_coordination_policy_v2.py -q
```

- [ ] Commit:

```bash
git add engine/distribution/claim_consumption_contract.py tests/test_v16_claim_consumption_contract.py
git commit -m "feat: add deterministic claim consumption contract c1"
```

---

### Task 3: Interpretation v2 integration

**Files:**
- Modify: `tests/test_v16_coordination_wrapper_integration.py`
- Modify: `engine/distribution/interpretation_contract_v2.py`

- [ ] First add RED assertions for:

```text
claim_consumption_profile_version
claim_consumption_digest
claim_consumption_decisions
```

- [ ] Disjoint-domain wrapper fixture must remain `parallel_signals` and decisions must be `render_with_caveat`.
- [ ] Existing v1 deterministic equality/mutation guard remains unchanged.
- [ ] Run wrapper test and observe missing-field RED.
- [ ] Integrate `build_claim_consumption_bundle` after Coordination, copy only public C1 output into v2, then recompute v2 digest.
- [ ] Run focused suite:

```bash
python -m pytest tests/test_v16_claim_consumption_contract.py tests/test_v16_coordination_wrapper_integration.py tests/test_v16_coordination_policy_v2.py tests/test_distribution_claim_evidence.py -q
```

- [ ] Commit:

```bash
git add engine/distribution/interpretation_contract_v2.py tests/test_v16_coordination_wrapper_integration.py
git commit -m "feat: expose claim consumption authority in interpretation v2"
```

---

### Task 4: Hybrid AI guardrail TDD

**Files:**
- Modify: `tests/test_ai_contract_docs.py`
- Modify: `core/AI工作流程.md`
- Modify: `core/核心提示詞.md`

- [ ] Add RED doc assertions requiring:

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

- [ ] Run `python -m pytest tests/test_ai_contract_docs.py -q` and observe RED.
- [ ] Add minimal fixed-contract rules: AI consumes Python decision; may not recompute from raw Bazi/Ziwei; must preserve caveat; must not render `abstain_claim` prospectively; may not raise confidence/specificity; reality context remains strategy-only and cannot reopen an abstained forecast claim.
- [ ] Re-run GREEN.
- [ ] Commit docs/tests.

---

### Task 5: Distribution + local hard gates

- [ ] Rebuild only via:

```bash
python tools/build_ai_distribution.py
python tools/build_ai_distribution.py --check
```

- [ ] Inspect `git status --porcelain`, `git diff --stat`, generated-file diff. Do not hand-edit generated files.
- [ ] Run focused regressions.
- [ ] Run repository Hosted-equivalent full regression, including unittest discovery and pytest-only suites required by Validation workflow.
- [ ] Run:

```bash
python -m compileall -q engine tools tests
```

- [ ] Commit deterministic generated artifacts only.
- [ ] After commit require:

```bash
python tools/build_ai_distribution.py --check
git diff --exit-code
git status --porcelain
```

Expected: check PASS, empty diff, empty status.

---

### Task 6: Hosted exact-SHA gate

- [ ] Record candidate SHA.
- [ ] Require same SHA Hosted:

```text
focused/general regression PASS
full repository regression PASS
AI distribution rebuild/check PASS
Python 3.9 compile PASS
Verify clean tree PASS
```

- [ ] Any failure => STOP before private; behavior fixes return to RED and create a new SHA.
- [ ] Freeze candidate only after all Hosted gates are GREEN on one SHA.

---

### Task 7: Private external evaluation

- [ ] Recheck every general/Hybrid/builder/full/compile/clean-tree Hosted gate on frozen SHA.
- [ ] Only then execute private evaluation once.
- [ ] Private PASS: record for governance review; no automatic promotion.
- [ ] Private FAIL: `STOP_CYCLE`; no C1 retuning, no C1.1, no reason-code/domain/render-policy adjustment from private evidence.

## Self-review

- Spec coverage: Tasks 1-7 cover deterministic policy, integration, Hybrid guardrails, Hosted gates, and private stop rule.
- Placeholder scan: no TODO/TBD behavior.
- Type consistency: API name, profile version, decision labels, digest fields, and Hybrid authority names match the design.
