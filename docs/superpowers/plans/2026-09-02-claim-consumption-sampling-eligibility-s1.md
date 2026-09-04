# Claim Consumption Sampling Eligibility S1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立 general-only、prospective-only、deterministic 的 Complete-Census Sampling Eligibility S1 authority，能驗證 private source manifest / outcome-free claim universe、機械建立 sampling frame、輸出 frozen T1 可直接消費的 sampling receipt，並在後續 oracle seal 前做 identity-only verification。

**Architecture:** 新增獨立 `engine/distribution/claim_consumption_sampling_eligibility.py`。S1 只消費公開 protocol 與 private opaque structured artifacts；所有 schema 使用 exact-fields + canonical SHA-256 fail-closed validation。S1 不執行 Q1/T1/C1 scoring；frame status 完全由 source manifest eligibility facts 與固定 precedence 推導，claim set 完全由 outcome-free claim-universe lock 提供。

**Tech Stack:** Python 3.9、stdlib (`json`, `hashlib`, `datetime`, `argparse`, `pathlib`)、`unittest`、既有 `tools/build_ai_distribution.py`。

**Spec:** `docs/superpowers/specs/2026-09-01-claim-consumption-sampling-eligibility-s1-design.zh-TW.md`

## Global Constraints

- Upstream frozen T1 GitHub SHA：`2fd80d234a04d40bafe66db21aa96c4a2594e2a1`，tree `19d1829d926132202e42778f1ab8975e41a19cd4`。
- Approved S1 spec SHA256：`5e0a7f161b088c55b85e9606ddb04a428fdfe174d82eae6b0a11c391538d882e`。
- T1 policy profile 固定：`lin_tianji_claim_consumption_private_strict_zero_v1`。
- T1 policy digest 固定：`65a072b2de63d6f509cc79139442263695589feca28ee99da0ab976ba0c3118a`。
- S1 sampling profile 固定：`lin_tianji_claim_consumption_complete_census_v1`。
- `promotion_allowed=false` 必須存在於 public protocol、sampling receipt、oracle identity verification。
- Real private source manifest / claim universe / frame / case IDs / claim IDs 不得進 git；tests 僅能使用 synthetic opaque IDs。
- S1 不 import / 呼叫 `evaluate_claim_consumption_qualification`、`evaluate_claim_consumption_private_threshold`、C1 decision builder 或 candidate-output generation。
- O1/Q1/C1/T1/Coordination/Phase 3 semantics read-only。
- 本 cycle 不執行 real private sampling、Q1 private evaluator、T1 private gate、claim-level adjudication 或 oracle seal。
- S1 protocol freeze timestamp 必須在 implementation 中以 UTC 實際時間捕捉一次並固定；不得回填成較早時間。

---

## File Structure

- Create `engine/distribution/claim_consumption_sampling_eligibility.py`：S1 schemas、canonical digests、strict validators、source→status precedence、frame builder、receipt builder/verifier、oracle identity verifier。
- Create `qualification/claim_consumption/v1.6/sampling-protocol.complete-census.v1.json`：general/public frozen S1 protocol。
- Create `tests/fixtures/v1.6-claim-consumption-sampling-eligibility.synthetic.v1.json`：純 synthetic protocol/source/claim-universe/oracle fixtures。
- Create `tests/test_v16_claim_consumption_sampling_eligibility.py`：S1-G1…G22 general conformance + CLI parity + mutation/private contamination guards。
- Create `tools/evaluate_v16_claim_consumption_sampling_eligibility.py`：thin multi-command CLI。
- Create `docs/research/2026-09-02-v1.6-claim-consumption-sampling-eligibility-s1.md`：general governance method / prospective-only boundaries。
- Modify only through formal builder: `dist/ai/metaphysics_lab.py` if builder includes the new module.

---

### Task 1: Approved-spec and plan checkpoint

**Files:**
- Modify: `docs/superpowers/specs/2026-09-01-claim-consumption-sampling-eligibility-s1-design.zh-TW.md` only to match the exact user-approved review copy already supplied.
- Create: `docs/superpowers/plans/2026-09-02-claim-consumption-sampling-eligibility-s1.md`

**Interfaces:**
- Consumes: approved S1 design spec.
- Produces: executable task sequence only; no production semantics.

- [ ] **Step 1: Verify approved spec and current branch**

```bash
sha256sum docs/superpowers/specs/2026-09-01-claim-consumption-sampling-eligibility-s1-design.zh-TW.md
git branch --show-current
git status --short
```

Expected: spec SHA256 equals `5e0a7f161b088c55b85e9606ddb04a428fdfe174d82eae6b0a11c391538d882e`; branch is `research/v1.6-claim-consumption-sampling-eligibility-s1`.

- [ ] **Step 2: Plan self-review**

```bash
python - <<'PY'
from pathlib import Path
p = Path('docs/superpowers/plans/2026-09-02-claim-consumption-sampling-eligibility-s1.md')
text = p.read_text(encoding='utf-8')
for forbidden in ('T'+'BD', 'T'+'ODO', 'implement'+' later', 'fill in'+' details'):
    assert forbidden not in text, forbidden
for required in (
    'Complete-Census',
    'source manifest',
    'claim universe',
    'EXCLUDE_PREVIOUSLY_EXPOSED',
    'verify_oracle_identity_against_sampling_frame',
    'promotion_allowed=false',
):
    assert required in text, required
print('S1_PLAN_SELF_REVIEW=PASS')
PY
```

Expected: `S1_PLAN_SELF_REVIEW=PASS`.

- [ ] **Step 3: Commit documents-only checkpoint**

```bash
git add docs/superpowers/specs/2026-09-01-claim-consumption-sampling-eligibility-s1-design.zh-TW.md \
        docs/superpowers/plans/2026-09-02-claim-consumption-sampling-eligibility-s1.md
git commit -m 'docs: plan complete-census sampling eligibility s1'
```

---

### Task 2: Synthetic contracts — protocol, source manifest, claim universe RED

**Files:**
- Create: `tests/fixtures/v1.6-claim-consumption-sampling-eligibility.synthetic.v1.json`
- Create: `tests/test_v16_claim_consumption_sampling_eligibility.py`

**Interfaces:**
- Consumes later API names exactly:
  - `validate_sampling_protocol(payload) -> dict`
  - `validate_sampling_source_manifest(payload, protocol) -> dict`
  - `validate_claim_universe_lock(payload, source_manifest, protocol) -> dict`
- Produces RED evidence before module exists.

- [ ] **Step 1: Create synthetic fixture**

Fixture root keys:

```json
{
  "protocol": {},
  "source_manifest": {},
  "claim_universe_lock": {},
  "oracle": {}
}
```

Synthetic case universe must include at least:

```text
case-a = UNEXPOSED + CONFIRMED + VALID + IN_SCOPE + within cutoff -> INCLUDE
case-b = UNEXPOSED + CONFIRMED + VALID + IN_SCOPE + within cutoff -> INCLUDE
case-c = PREVIOUSLY_EXPOSED -> EXCLUDE_PREVIOUSLY_EXPOSED
case-d = after cutoff + PREVIOUSLY_EXPOSED -> EXCLUDE_AFTER_CUTOFF by precedence
case-e = NON_CONFIRMATION -> EXCLUDE_NON_CONFIRMATION
case-f = INVALID -> EXCLUDE_INPUT_INVALID
case-g = OUT_OF_SCOPE -> EXCLUDE_OUT_OF_SCOPE
```

Only `case-a` and `case-b` appear in `claim_universe_lock.cases`, each with non-empty unique synthetic claim IDs.

All digests are canonical SHA-256 of the exact payloads defined by the approved spec.

- [ ] **Step 2: Write first RED tests**

Tests must cover:

```text
S1-G1 protocol/source/claim-universe baseline validates
S1-G7 included case with empty claims fails closed
S1-G8 duplicate claim ID fails closed
S1-G9 duplicate source case ID fails closed
S1-G10 protocol digest tamper fails closed
S1-G10a source manifest digest tamper fails closed
S1-G10c deterministic exclusion precedence helper returns AFTER_CUTOFF first
S1-G10d claim universe missing INCLUDE case fails closed
S1-G10e claim universe contains excluded case fails closed
S1-G13 T1 policy digest mismatch fails closed
S1-G14 unknown fields fail closed at protocol/source/record/claim-universe/case levels
S1-G15 permutations preserve canonical validation/digests
```

The test module imports the three API names above from `engine.distribution.claim_consumption_sampling_eligibility`.

- [ ] **Step 3: Verify RED is exact**

```bash
LD_LIBRARY_PATH=/mnt/data/python39-ready/lib \
/mnt/data/python39-ready/bin/python3.9 -m py_compile \
  tests/test_v16_claim_consumption_sampling_eligibility.py
python -m json.tool tests/fixtures/v1.6-claim-consumption-sampling-eligibility.synthetic.v1.json >/dev/null
LD_LIBRARY_PATH=/mnt/data/python39-ready/lib \
/mnt/data/python39-ready/bin/python3.9 -m unittest -v \
  tests.test_v16_claim_consumption_sampling_eligibility
```

Expected: import-time RED only because `engine.distribution.claim_consumption_sampling_eligibility` does not exist.

- [ ] **Step 4: Commit RED-only checkpoint**

```bash
git add tests/fixtures/v1.6-claim-consumption-sampling-eligibility.synthetic.v1.json \
        tests/test_v16_claim_consumption_sampling_eligibility.py
git commit -m 'test: define sampling eligibility s1 red gate'
```

---

### Task 3: Strict protocol/source/claim-universe authority GREEN

**Files:**
- Create: `engine/distribution/claim_consumption_sampling_eligibility.py`
- Create: `qualification/claim_consumption/v1.6/sampling-protocol.complete-census.v1.json`
- Test: `tests/test_v16_claim_consumption_sampling_eligibility.py`

**Interfaces:**
- Produces:
  - `validate_sampling_protocol`
  - `validate_sampling_source_manifest`
  - `validate_claim_universe_lock`
  - internal deterministic `_derive_case_status(record)`

- [ ] **Step 1: Implement canonical helpers and exact schemas**

Use the repository pattern:

```python
def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()
```

Reject unknown and missing fields at every level. Validate RFC3339 UTC `Z` timestamps, lower-case SHA-256 text, booleans, enums, unique IDs and canonical digest identities.

- [ ] **Step 2: Implement fixed exclusion precedence**

```python
def _derive_case_status(record: Mapping[str, object]) -> tuple[str, str | None]:
    if record["within_cutoff"] is False:
        return "EXCLUDE_AFTER_CUTOFF", "after_cutoff"
    if record["candidate_exposure_status"] == "PREVIOUSLY_EXPOSED":
        return "EXCLUDE_PREVIOUSLY_EXPOSED", "previously_exposed"
    if record["confirmation_status"] == "NON_CONFIRMATION":
        return "EXCLUDE_NON_CONFIRMATION", "non_confirmation"
    if record["input_validity_status"] == "INVALID":
        return "EXCLUDE_INPUT_INVALID", "input_invalid"
    if record["scope_status"] == "OUT_OF_SCOPE":
        return "EXCLUDE_OUT_OF_SCOPE", "out_of_scope"
    return "INCLUDE", None
```

No caller-supplied status is accepted in source manifest.

- [ ] **Step 3: Implement manifest / claim-universe completeness**

`validate_claim_universe_lock` must derive the INCLUDE set from validated manifest and require exact equality with the lock case set. For each INCLUDE case require non-empty, unique `locked_claim_ids`; canonical validation accepts arbitrary input ordering but digests are computed from sorted case/claim identity.

- [ ] **Step 4: Freeze public protocol at actual implementation time**

Capture once:

```bash
S1_FROZEN_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf '%s\n' "$S1_FROZEN_AT"
```

Create `qualification/claim_consumption/v1.6/sampling-protocol.complete-census.v1.json` with:

```text
schema_version = v1.6-claim-consumption-sampling-protocol.v1
sampling_profile = lin_tianji_claim_consumption_complete_census_v1
required_t1_policy_profile = lin_tianji_claim_consumption_private_strict_zero_v1
required_t1_policy_digest = 65a072b2de63d6f509cc79139442263695589feca28ee99da0ab976ba0c3118a
complete_census_required = true
candidate_exposure_must_be_unexposed = true
claim_universe_must_be_outcome_free = true
minimum_case_count_rule = at_least_one_if_eligible
minimum_claim_count_rule = at_least_one_if_eligible
promotion_allowed = false
```

`allowed_case_statuses` and `allowed_exclusion_reason_codes` must exactly match the approved spec. Compute `protocol_digest` after removing that field.

Update the synthetic fixture `protocol` to match this frozen general protocol, while keeping all case data synthetic.

- [ ] **Step 5: Run S1 tests and upstream T1 focused**

```bash
LD_LIBRARY_PATH=/mnt/data/python39-ready/lib \
/mnt/data/python39-ready/bin/python3.9 -m unittest -v \
  tests.test_v16_claim_consumption_sampling_eligibility \
  tests.test_v16_claim_consumption_private_threshold
```

Expected: all GREEN.

- [ ] **Step 6: Commit authority checkpoint**

```bash
git add engine/distribution/claim_consumption_sampling_eligibility.py \
        qualification/claim_consumption/v1.6/sampling-protocol.complete-census.v1.json \
        tests/fixtures/v1.6-claim-consumption-sampling-eligibility.synthetic.v1.json \
        tests/test_v16_claim_consumption_sampling_eligibility.py
git commit -m 'feat: add complete-census sampling authority s1'
```

---

### Task 4: Deterministic frame + T1-compatible receipt RED→GREEN

**Files:**
- Modify: `engine/distribution/claim_consumption_sampling_eligibility.py`
- Modify: `tests/test_v16_claim_consumption_sampling_eligibility.py`

**Interfaces:**
- Produces:
  - `build_sampling_frame(source_manifest, claim_universe_lock, protocol, locked_at) -> dict`
  - `validate_sampling_frame(payload, source_manifest, claim_universe_lock, protocol) -> dict`
  - `build_sampling_eligibility_receipt(frame, source_manifest, claim_universe_lock, protocol, sealed_at) -> dict`
  - `verify_sampling_eligibility_receipt(receipt) -> dict`

- [ ] **Step 1: Add frame/receipt RED tests before functions exist**

Cover:

```text
S1-G1 baseline frame contains every source case exactly once; receipt ELIGIBLE with 2 included cases
S1-G2 all PREVIOUSLY_EXPOSED -> valid INELIGIBLE receipt, case_count=0 claim_count=0
S1-G3 manually mutated exposed case to INCLUDE -> fail closed
S1-G4/5/6 status/reason mapping exact
S1-G10b frame/source case-set mismatch -> fail closed
S1-G10f included frame claims differ from claim-universe -> fail closed
S1-G11 frame_digest tamper -> fail closed
S1-G12 case_digest tamper -> fail closed
S1-G15 case/claim permutations -> same frame_digest / receipt_digest
S1-G16 delete one manifest case from frame -> fail closed even if included counts unchanged
receipt schema is byte-compatible with frozen T1 validate_sampling_eligibility_receipt
```

- [ ] **Step 2: Verify RED only due missing frame/receipt APIs**

```bash
LD_LIBRARY_PATH=/mnt/data/python39-ready/lib \
/mnt/data/python39-ready/bin/python3.9 -m unittest -v \
  tests.test_v16_claim_consumption_sampling_eligibility
```

Expected: missing-import/function RED, with Task 3 tests still green if isolated.

- [ ] **Step 3: Implement deterministic frame builder**

Builder ignores caller status input because no frame input exists yet: it derives every status from source facts. Frame cases are emitted sorted by `opaque_case_id`. INCLUDE cases copy exact sorted `locked_claim_ids` from claim-universe lock; every excluded case has `locked_claim_ids=[]`.

- [ ] **Step 4: Implement strict frame validator**

Require exact source case set, exact `source_record_digest`, derived status/reason equality, exact INCLUDE claim sets and zero claims for excluded cases. Recompute each `case_digest` and root `frame_digest` canonicalized by case ID.

- [ ] **Step 5: Implement receipt builder/verifier**

Receipt uses existing T1 schema exactly:

```text
v1.6-claim-consumption-sampling-eligibility-receipt.v1
```

Status is `ELIGIBLE` iff included case_count > 0 and claim_count > 0; otherwise valid complete census yields `INELIGIBLE` with zero/derived counts. `sampling_protocol_digest` must equal frozen protocol digest and `promotion_allowed=false`.

`verify_sampling_eligibility_receipt` is schema/digest-only because T1 later binds it to oracle counts/timing.

- [ ] **Step 6: Run S1 + frozen T1 tests**

```bash
LD_LIBRARY_PATH=/mnt/data/python39-ready/lib \
/mnt/data/python39-ready/bin/python3.9 -m unittest -v \
  tests.test_v16_claim_consumption_sampling_eligibility \
  tests.test_v16_claim_consumption_private_threshold
```

Expected: GREEN.

- [ ] **Step 7: Commit frame/receipt checkpoint**

```bash
git add engine/distribution/claim_consumption_sampling_eligibility.py \
        tests/test_v16_claim_consumption_sampling_eligibility.py
git commit -m 'feat: add deterministic sampling frame and receipt s1'
```

---

### Task 5: Oracle identity verifier + CLI/governance RED→GREEN

**Files:**
- Modify: `engine/distribution/claim_consumption_sampling_eligibility.py`
- Modify: `tests/test_v16_claim_consumption_sampling_eligibility.py`
- Create: `tools/evaluate_v16_claim_consumption_sampling_eligibility.py`
- Create: `docs/research/2026-09-02-v1.6-claim-consumption-sampling-eligibility-s1.md`

**Interfaces:**
- Produces `verify_oracle_identity_against_sampling_frame(frame, oracle) -> dict`.
- CLI commands exactly:
  - `validate-protocol`
  - `validate-source-manifest`
  - `validate-claim-universe-lock`
  - `build-frame`
  - `validate-frame`
  - `seal-receipt`
  - `verify-receipt`
  - `verify-oracle-identity`

- [ ] **Step 1: Add oracle identity + CLI/doc RED tests**

Cover:

```text
S1-G17 oracle missing claim -> fail closed
S1-G18 oracle extra claim -> fail closed
S1-G19 oracle missing/extra case -> fail closed
S1-G20 authorization/specificity changes with identical case/claim sets -> identical VALID identity result
S1-G21 source/tests/docs contain no real private workspace path, prior private aggregate filename/digest, real case IDs or real claim IDs
S1-G22 compare upstream files from frozen T1 baseline: no Q1/O1/C1/T1/Coordination/Phase3 production file modification
CLI direct-API byte parity for build-frame/seal-receipt/verify-oracle-identity
private-output modes require explicit --output and do not write defaults into repo
method doc contains prospective-only, complete-census, previously-exposed, outcome-free, promotion_allowed=false
```

- [ ] **Step 2: Verify RED because oracle API / CLI / doc do not exist**

```bash
LD_LIBRARY_PATH=/mnt/data/python39-ready/lib \
/mnt/data/python39-ready/bin/python3.9 -m unittest -v \
  tests.test_v16_claim_consumption_sampling_eligibility
```

- [ ] **Step 3: Implement identity-only verifier**

It must parse only:

```text
oracle case_id
oracle expectation claim_id
```

It may validate minimum structure needed for identity comparison, but must not compare `expected_authorization`, specificity or caveat semantics. Output:

```text
schema_version = v1.6-claim-consumption-sampling-oracle-identity-verification.v1
status = VALID
case_count
claim_count
sampling_frame_digest
oracle_identity_digest
verification_digest
promotion_allowed = false
```

`oracle_identity_digest` is canonical SHA-256 over sorted `(case_id, sorted claim_ids)` only.

- [ ] **Step 4: Implement thin CLI**

CLI loads JSON and delegates to production APIs. `build-frame`, `seal-receipt`, and `verify-oracle-identity` must require explicit `--output`; validation-only commands may emit canonical JSON to stdout. CLI never searches for private inputs and never calls Q1/T1.

- [ ] **Step 5: Write general governance method doc**

Document only public protocol / schemas / sequencing / hard gates. State explicitly:

```text
S1 is prospective-only.
Complete census means every source-manifest case is represented exactly once.
Previously exposed cases are permanently excluded.
Claim universe is outcome-free and candidate-independent.
Real private artifacts stay outside git.
S1 does not execute Q1 or T1.
promotion_allowed=false.
```

- [ ] **Step 6: Run S1 + frozen upstream focused suite**

```bash
LD_LIBRARY_PATH=/mnt/data/python39-ready/lib \
/mnt/data/python39-ready/bin/python3.9 -m unittest -v \
  tests.test_v16_claim_consumption_sampling_eligibility \
  tests.test_v16_claim_consumption_private_threshold \
  tests.test_v16_claim_consumption_oracle_seal \
  tests.test_v16_claim_consumption_qualification \
  tests.test_v16_claim_consumption_contract \
  tests.test_v16_coordination_wrapper_integration \
  tests.test_v16_coordination_policy_v2
```

Expected: GREEN.

- [ ] **Step 7: Commit CLI/governance checkpoint**

```bash
git add engine/distribution/claim_consumption_sampling_eligibility.py \
        tests/test_v16_claim_consumption_sampling_eligibility.py \
        tools/evaluate_v16_claim_consumption_sampling_eligibility.py \
        docs/research/2026-09-02-v1.6-claim-consumption-sampling-eligibility-s1.md
git commit -m 'feat: add sampling identity verification and cli s1'
```

---

### Task 6: Formal distribution build and local hard gates

**Files:**
- Modify only through builder: `dist/ai/metaphysics_lab.py`

**Interfaces:**
- Consumes completed S1 implementation.
- Produces exact locally qualified candidate tree.

- [ ] **Step 1: Run formal builder and scope check**

```bash
LD_LIBRARY_PATH=/mnt/data/python39-ready/lib \
/mnt/data/python39-ready/bin/python3.9 tools/build_ai_distribution.py
LD_LIBRARY_PATH=/mnt/data/python39-ready/lib \
/mnt/data/python39-ready/bin/python3.9 tools/build_ai_distribution.py --check
git diff --check
git status --short
```

Expected: builder drift only in formal generated artifacts actually controlled by builder; no unrelated file.

- [ ] **Step 2: Run official validation-equivalent pre-full gates**

Use commands from `.github/workflows/lin-tianji-v1.5-validation.yml` verbatim for:

```text
Bazi flow-day/hour qualification
Ziwei flow-day/hour qualification
Ziwei month-boundary qualification
formal builder/check
official focused regression
prediction validation
v1.5 release surface
three-file deterministic package
```

Every command must exit 0.

- [ ] **Step 3: Run full repository regression**

```bash
TERM=xterm LD_LIBRARY_PATH=/mnt/data/python39-ready/lib \
/mnt/data/python39-ready/bin/python3.9 -m unittest discover -v
```

Expected: all tests `OK` with exit 0; record exact test count.

- [ ] **Step 4: Python 3.9 compile and contamination scan**

```bash
LD_LIBRARY_PATH=/mnt/data/python39-ready/lib \
/mnt/data/python39-ready/bin/python3.9 -m compileall -q engine tools tests
python - <<'PY'
from pathlib import Path
for root in ('engine', 'tools', 'tests', 'docs/research', 'qualification'):
    for p in Path(root).rglob('*'):
        if not p.is_file():
            continue
        low = str(p).lower()
        assert 'q1-private-adjudication' not in low
        assert 'private_equivalence_evaluation' not in low
print('S1_PRIVATE_ARTIFACT_SCAN=PASS')
PY
```

- [ ] **Step 5: Commit generated runtime and verify fresh clean candidate**

```bash
git add dist/ai/metaphysics_lab.py
git commit -m 'build(ai): sync sampling eligibility s1 runtime'
LD_LIBRARY_PATH=/mnt/data/python39-ready/lib \
/mnt/data/python39-ready/bin/python3.9 -m unittest -v tests.test_v16_claim_consumption_sampling_eligibility
LD_LIBRARY_PATH=/mnt/data/python39-ready/lib \
/mnt/data/python39-ready/bin/python3.9 tools/build_ai_distribution.py --check
git diff --exit-code
test -z "$(git status --short)"
git rev-parse HEAD
git rev-parse HEAD^{tree}
```

Expected: S1 tests GREEN, builder parity PASS, clean tree. Record exact local HEAD/tree.

---

### Task 7: Exact-tree GitHub transport and Hosted qualification

**Files:**
- No S1 candidate semantic changes allowed after local hard-gate freeze.
- Temporary helper branch/workflow may be used only for byte transport and must not enter research PR diff.

**Interfaces:**
- Consumes exact clean local candidate.
- Produces GitHub research commit with identical tree and Hosted same-SHA evidence.

- [ ] **Step 1: Build SHA-locked transport payload**

Package all non-generated files changed relative to frozen T1 `2fd80d234a04d40bafe66db21aa96c4a2594e2a1`. Record each SHA256 and tar SHA256. Do not transport real private artifacts.

- [ ] **Step 2: Helper transport guards**

Helper must:

```text
checkout frozen T1 exact SHA
verify source tar SHA
verify every transported file SHA
setup Python 3.9
rebuild formal AI runtime
verify generated runtime SHA equals local candidate runtime SHA
run S1 + frozen upstream focused tests
verify exact changed-file scope
commit/push research branch only after every guard PASS
```

- [ ] **Step 3: Verify GitHub tree identity**

Compare research branch commit tree SHA to local candidate tree SHA. Require parent ancestry from frozen T1 and expected changed-file set only.

- [ ] **Step 4: Create Draft research PR + main CI carrier**

Authoritative PR base:

```text
research/v1.6-claim-consumption-private-threshold-t1
```

Carrier base:

```text
main
```

Both head the exact same frozen S1 candidate SHA. Carrier is Draft/never-merge.

- [ ] **Step 5: Hosted same-SHA Validation**

Require formal `林氏天機 v1.5 Validation` on exact candidate SHA to PASS:

```text
Confirm validation SHA
Bazi/Ziwei qualifications
formal builder/upload
focused regression
prediction validation
release surface
package determinism
full repository regression
Python 3.9 compile
clean tree
```

- [ ] **Step 6: Freeze governance state**

If Hosted succeeds:

```text
GENERAL_HOSTED_QUALIFIED / S1_INFRASTRUCTURE_FROZEN / REAL_SAMPLING_NOT_EXECUTED
```

Update research PR and add freeze audit comment. Close carrier without merge. Keep research PR Draft/unmerged. Do not create real source manifest/frame in this task.

---

## Completion Evidence

S1 infrastructure may be called complete only when all are true:

```text
approved spec exact SHA recorded
synthetic RED captured before production module
S1 general tests GREEN
frozen T1/Q1/O1/C1/Coordination regressions GREEN
CLI/docs GREEN
formal builder parity GREEN
full repository regression GREEN
Python 3.9 compile GREEN
private-artifact contamination scan GREEN
local clean tree GREEN
GitHub tree == local tree
Hosted same-SHA Validation GREEN
real private sampling not executed
no merge/default switch/tag/release
```
