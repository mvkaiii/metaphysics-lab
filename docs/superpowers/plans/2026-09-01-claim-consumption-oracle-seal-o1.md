# Claim Consumption Oracle Seal O1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立一套 candidate-independent 的 claim-level oracle sealing、驗證與 candidate-output join subsystem，讓未來 Q1 private evaluation 能證明 expectations 在 candidate scoring 前已封存，而且不修改 C1/Q1 scoring semantics。

**Architecture:** 新增單一 authority module `engine/distribution/claim_consumption_oracle_seal.py`，負責 strict schema validation、canonical digests、seal/verify/public receipt 與 deterministic join。CLI 僅包裝 `seal / verify / join` 三種模式；join 只組裝既有 `v1.6-claim-consumption-qualification-input.v1` 並呼叫唯讀 validator，不得執行 Q1 scoring。所有 O1 開發與測試只使用 synthetic fixtures；private oracle 與 joined private input 保持 git 外。

**Tech Stack:** Python 3.9、stdlib `json/hashlib/copy/argparse/pathlib/datetime`、`unittest`、既有 `claim_consumption_qualification` validator、formal AI distribution builder。

**Spec:** `docs/superpowers/specs/2026-09-01-claim-consumption-oracle-seal-o1-design.zh-TW.md`

## Global Constraints

- GitHub 上具權威性的 upstream frozen Q1 SHA 固定為 `4c5df745554b1d14a08b58aae45f4212b0162132`。
- `engine/distribution/claim_consumption_contract.py` 為 read-only。
- `engine/distribution/claim_consumption_qualification.py` scoring semantics 為 read-only。
- Coordination、Phase 3 ranking、Claim Evidence candidate sets、Interpretation ranking、Hybrid render policy 全部 read-only。
- 不得從既有 private Interpretation labels 或 aggregate outcomes 建立 O1 oracle expectations。
- O1 開發期間不得執行 Q1 private evaluation。
- private oracle、private seal、candidate-output package 與 joined private input 不得寫入 repo。
- public receipt 必須 aggregate-only，`promotion_allowed=false`。
- 所有 unknown fields、duplicate IDs、digest mismatch、rubric mismatch、case/claim-set mismatch、contamination 一律 fail closed。
- 所有 digests 採 `UTF-8 + sort_keys=True + separators=(",", ":") + ensure_ascii=False + allow_nan=False + SHA-256 lowercase hex`。
- Local hard gates 全綠後才允許 transport 至 GitHub；GitHub 僅作 Hosted same-SHA confirmation。

---

### Task 1: Freeze approved O1 specification and plan

**Files:**
- Add: `docs/superpowers/specs/2026-09-01-claim-consumption-oracle-seal-o1-design.md`
- Add: `docs/superpowers/specs/2026-09-01-claim-consumption-oracle-seal-o1-design.zh-TW.md`
- Add: `docs/superpowers/plans/2026-09-01-claim-consumption-oracle-seal-o1.md`

**Interfaces:**
- Consumes: approved design from the current conversation.
- Produces: frozen implementation contract for all later tasks.

- [ ] **Step 1: Verify upstream baseline**

Run:
```bash
git rev-parse HEAD
git status --porcelain
```
Expected: baseline lineage contains frozen Q1 source state and working tree is clean before adding O1 documents.

- [ ] **Step 2: Add both specs and this implementation plan**

Run:
```bash
git add docs/superpowers/specs/2026-09-01-claim-consumption-oracle-seal-o1-design.md \
        docs/superpowers/specs/2026-09-01-claim-consumption-oracle-seal-o1-design.zh-TW.md \
        docs/superpowers/plans/2026-09-01-claim-consumption-oracle-seal-o1.md
git diff --cached --check
```
Expected: no whitespace errors and no production files staged.

- [ ] **Step 3: Commit documents-only checkpoint**

```bash
git commit -m "docs: freeze claim consumption oracle seal O1 design"
```

---

### Task 2: RED — strict oracle sealing contract

**Files:**
- Create: `tests/fixtures/v1.6-claim-consumption-oracle.synthetic.v1.json`
- Create: `tests/test_v16_claim_consumption_oracle_seal.py`
- Production target, intentionally absent during RED: `engine/distribution/claim_consumption_oracle_seal.py`

**Interfaces:**
- Consumes: Q1 expectation shape (`claim_id`, `expected_authorization`, `minimum_acceptable_specificity`, `maximum_specificity`, `caveat_required`).
- Produces test expectations for:
  - `validate_claim_consumption_oracle(payload: object) -> dict`
  - `seal_claim_consumption_oracle(oracle: object, sealed_at: str) -> dict`
  - `verify_oracle_seal(oracle: object, seal: object) -> dict`
  - `build_public_oracle_seal_receipt(seal: object) -> dict`

- [ ] **Step 1: Build a positive synthetic oracle fixture**

Fixture top-level shape:
```json
{
  "schema_version": "v1.6-claim-consumption-oracle.v1",
  "oracle_profile": "lin_tianji_claim_consumption_oracle_v1",
  "rubric_digest": "<64 lowercase hex>",
  "cases": [
    {
      "case_id": "oracle-case-a",
      "expectations": [
        {
          "claim_id": "career",
          "expected_authorization": "render",
          "minimum_acceptable_specificity": "domain",
          "maximum_specificity": "event_family",
          "caveat_required": false
        }
      ],
      "cutoff_contamination": false,
      "oracle_case_digest": "<canonical digest>"
    }
  ]
}
```
Use a test helper implementing only canonical JSON/digest fixture construction; do not import the production module to generate expected answers.

- [ ] **Step 2: Add RED tests for seal behavior**

The test class must include assertions for all of these exact behaviors:
```text
valid oracle validates
case-order permutation yields identical expectation/set digests
expectation-order permutation yields identical case/seal digests
duplicate case_id fails closed
duplicate claim_id fails closed
unknown top-level/case/expectation fields fail closed
private-looking fields such as actual_event or subject_name fail closed
rubric_digest must be lowercase sha256
oracle_case_digest tampering fails closed
sealed_at must be UTC RFC3339 with Z suffix
seal_digest tampering fails closed
verify returns only {schema_version, status, seal_digest}
public receipt contains no case_id/claim_id/expectation contents
public receipt has status=SEALED and promotion_allowed=false
```

- [ ] **Step 3: Run RED test under Python 3.9**

Run:
```bash
python3.9 -m unittest -v tests.test_v16_claim_consumption_oracle_seal
```
Expected: ERROR only because `engine.distribution.claim_consumption_oracle_seal` does not exist. Syntax/fixture parsing must otherwise be valid.

- [ ] **Step 4: Commit RED-only checkpoint**

```bash
git add tests/fixtures/v1.6-claim-consumption-oracle.synthetic.v1.json \
        tests/test_v16_claim_consumption_oracle_seal.py
git commit -m "test: lock oracle seal O1 contract"
```

---

### Task 3: GREEN — oracle validation, sealing, verification, public receipt

**Files:**
- Create: `engine/distribution/claim_consumption_oracle_seal.py`
- Test: `tests/test_v16_claim_consumption_oracle_seal.py`

**Interfaces:**
- Produces constants:
```python
ORACLE_SCHEMA = "v1.6-claim-consumption-oracle.v1"
SEAL_SCHEMA = "v1.6-claim-consumption-oracle-seal.v1"
RECEIPT_SCHEMA = "v1.6-claim-consumption-oracle-seal-receipt.v1"
CANDIDATE_OUTPUT_SCHEMA = "v1.6-claim-consumption-candidate-output.v1"
VERIFICATION_SCHEMA = "v1.6-claim-consumption-oracle-seal-verification.v1"
```
- Produces functions:
```python
validate_claim_consumption_oracle(payload: object) -> dict
seal_claim_consumption_oracle(oracle: object, sealed_at: str) -> dict
verify_oracle_seal(oracle: object, seal: object) -> dict
build_public_oracle_seal_receipt(seal: object) -> dict
```

- [ ] **Step 1: Implement canonical helpers and strict validators**

Use module-local helpers equivalent to Q1 deterministic JSON convention:
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
Implement exact-field allowlists at top-level, case, expectation, seal, receipt and verification levels. Do not import Q1 private fixtures.

- [ ] **Step 2: Implement normalized expectation and case validation**

Reuse the frozen Q1 semantic constraints without changing Q1 source:
```text
expected_authorization ∈ render/render_with_caveat/abstain_claim
caveat_required iff expected_authorization == render_with_caveat
abstain_claim requires null specificity bounds
otherwise minimum <= maximum using domain < event_family < concrete_event < highly_specific_event
```
Canonical case digest payload must sort expectations by `claim_id` and exclude `oracle_case_digest`.

- [ ] **Step 3: Implement seal construction**

`seal_claim_consumption_oracle()` must:
```text
validate oracle
sort cases by case_id
count cases/claims/contamination
compute oracle_expectation_digest from normalized case payloads without oracle_case_digest
compute case_set_digest from sorted oracle_case_digest list
validate sealed_at is UTC RFC3339 with literal Z
compute seal_digest after all fields except seal_digest are populated
return deterministic deep-copied seal
```

- [ ] **Step 4: Implement verification and public receipt**

`verify_oracle_seal()` must recompute the seal from oracle using `seal["sealed_at"]`, compare every semantic field and `seal_digest`, and return only:
```python
{
    "schema_version": VERIFICATION_SCHEMA,
    "status": "VALID",
    "seal_digest": seal["seal_digest"],
}
```
On any mismatch raise `ValueError`.

`build_public_oracle_seal_receipt()` must strictly validate the seal and return exactly the receipt schema fields, with `status="SEALED"` and `promotion_allowed=False`.

- [ ] **Step 5: Run O1 tests GREEN**

```bash
python3.9 -m unittest -v tests.test_v16_claim_consumption_oracle_seal
```
Expected: all current O1 seal tests PASS.

- [ ] **Step 6: Run frozen Q1/C1 regression**

```bash
python3.9 -m unittest -v \
  tests.test_v16_claim_consumption_qualification \
  tests.test_v16_claim_consumption_contract
```
Expected: PASS with no Q1/C1 changes.

- [ ] **Step 7: Commit minimal seal implementation**

```bash
git add engine/distribution/claim_consumption_oracle_seal.py \
        tests/test_v16_claim_consumption_oracle_seal.py \
        tests/fixtures/v1.6-claim-consumption-oracle.synthetic.v1.json
git commit -m "feat: add deterministic claim consumption oracle sealing"
```

---

### Task 4: RED→GREEN — candidate-output validation and deterministic join

**Files:**
- Create: `tests/fixtures/v1.6-claim-consumption-candidate-output.synthetic.v1.json`
- Modify: `tests/test_v16_claim_consumption_oracle_seal.py`
- Modify: `engine/distribution/claim_consumption_oracle_seal.py`

**Interfaces:**
- Produces:
```python
validate_claim_consumption_candidate_output(payload: object) -> dict
join_sealed_oracle_with_candidate(
    oracle: object,
    seal: object,
    candidate_output: object,
) -> dict
```
- Imports only the frozen Q1 validator:
```python
from engine.distribution.claim_consumption_qualification import (
    INPUT_SCHEMA,
    validate_claim_consumption_qualification_input,
)
```
- Must not import/call `evaluate_claim_consumption_qualification`.

- [ ] **Step 1: Add RED fixture and tests**

Candidate fixture schema:
```json
{
  "schema_version": "v1.6-claim-consumption-candidate-output.v1",
  "candidate_sha": "0123456789abcdef0123456789abcdef01234567",
  "cases": [
    {
      "case_id": "oracle-case-a",
      "claim_consumption_bundle": { "...": "existing valid C1 bundle" },
      "candidate_case_digest": "<canonical digest>"
    }
  ]
}
```

Add tests for:
```text
candidate_sha exactly 40 lowercase hex
candidate unknown fields rejected
candidate_case_digest tampering rejected
duplicate candidate case_id rejected
oracle/candidate case sets must match exactly
oracle/candidate claim_id sets must match exactly
contaminated seal cannot join
unsealed/tampered oracle cannot join
joined cases sorted by case_id
joined expectations preserve normalized oracle semantics
joined claim_consumption_bundle preserves candidate semantics
joined input_digest is newly recomputed using Q1 case rule
joined payload classification=private_external_evaluation
joined payload passes unchanged Q1 validator
join never executes Q1 scoring
case/expectation input permutations yield byte-identical joined payload
```
For the “never executes Q1 scoring” test, patch `engine.distribution.claim_consumption_qualification.evaluate_claim_consumption_qualification` to raise if called; join must still PASS.

- [ ] **Step 2: Run targeted RED**

```bash
python3.9 -m unittest -v \
  tests.test_v16_claim_consumption_oracle_seal.ClaimConsumptionOracleSealTests.test_valid_join_builds_q1_private_input
```
Expected: FAIL because candidate validation/join functions are missing.

- [ ] **Step 3: Implement candidate-output validator**

Strictly validate:
```text
schema_version
candidate_sha
cases non-empty
case_id unique
claim_consumption_bundle using frozen Q1/C1 public bundle validation path
candidate_case_digest = digest(case_id + claim_consumption_bundle)
unknown fields fail closed
```
Do not reinterpret C1 decisions.

- [ ] **Step 4: Implement join**

Algorithm:
```python
verify_oracle_seal(oracle, seal)
if seal["cutoff_contamination_count"] != 0:
    raise ValueError(...)
validated_oracle = validate_claim_consumption_oracle(oracle)
validated_candidate = validate_claim_consumption_candidate_output(candidate_output)
# compare exact case sets, then exact claim sets per case
# construct Q1 cases and recompute input_digest using Q1 canonical convention
# sort cases by case_id
joined = {
    "schema_version": INPUT_SCHEMA,
    "classification": "private_external_evaluation",
    "cases": joined_cases,
}
validate_claim_consumption_qualification_input(joined)
return copy.deepcopy(joined)
```
No scoring call is permitted.

- [ ] **Step 5: Run O1 + Q1/C1 focused tests**

```bash
python3.9 -m unittest -v \
  tests.test_v16_claim_consumption_oracle_seal \
  tests.test_v16_claim_consumption_qualification \
  tests.test_v16_claim_consumption_contract
```
Expected: PASS.

- [ ] **Step 6: Commit join implementation**

```bash
git add engine/distribution/claim_consumption_oracle_seal.py \
        tests/test_v16_claim_consumption_oracle_seal.py \
        tests/fixtures/v1.6-claim-consumption-candidate-output.synthetic.v1.json
git commit -m "feat: join sealed oracle with frozen candidate output"
```

---

### Task 5: RED→GREEN — CLI and governance method documentation

**Files:**
- Create: `tools/seal_v16_claim_consumption_oracle.py`
- Create: `docs/research/2026-09-01-v1.6-claim-consumption-oracle-seal-o1.md`
- Modify: `tests/test_v16_claim_consumption_oracle_seal.py`

**Interfaces:**
- CLI modes:
```text
seal   --oracle PATH --sealed-at TIMESTAMP --seal-out PATH [--receipt-out PATH]
verify --oracle PATH --seal PATH [--output PATH]
join   --oracle PATH --seal PATH --candidate-output PATH --output PATH
```
- Stdout must remain empty when an explicit output path is provided.
- CLI must never default private outputs into repository paths.

- [ ] **Step 1: Add RED CLI tests**

Add tests that invoke the tool with `subprocess.run(..., check=True, capture_output=True, text=True)` and assert:
```text
seal output JSON bytes are deterministic
receipt output exactly matches direct API receipt
verify report contains only minimal verification fields
join output exactly matches direct API join
explicit output paths are required for seal/join private artifacts
CLI has no commit/upload/network side effect
unknown mode/args return non-zero
```
Also assert the research doc includes these exact governance phrases:
```text
PRIVATE_ORACLE_OUTSIDE_GIT
CANDIDATE_OUTPUT_AFTER_FREEZE
JOIN_DOES_NOT_SCORE
PRIVATE_Q1_NOT_EXECUTED
promotion_allowed=false
```

- [ ] **Step 2: Run CLI RED**

```bash
python3.9 -m unittest -v \
  tests.test_v16_claim_consumption_oracle_seal.ClaimConsumptionOracleSealTests.test_cli_seal_verify_join_matches_direct_api
```
Expected: FAIL because CLI/doc do not exist.

- [ ] **Step 3: Implement CLI**

Use `argparse` subparsers. Read/write JSON with UTF-8 and deterministic serialization:
```python
json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
```
For `verify`, stdout JSON is allowed only when `--output` is omitted. For `seal` and `join`, require explicit output path(s); never invent repo-relative defaults.

- [ ] **Step 4: Write method/governance doc**

Document:
```text
purpose and architecture
frozen upstream Q1 SHA
schema identities
seal workflow
private data boundary
candidate freeze boundary
one-run future private rule
what O1 does NOT authorize
local/Hosted gate checklist
```
No private case content or prior private aggregate metrics may appear.

- [ ] **Step 5: Run CLI/doc tests GREEN**

```bash
python3.9 -m unittest -v tests.test_v16_claim_consumption_oracle_seal
```
Expected: PASS.

- [ ] **Step 6: Commit CLI/documentation**

```bash
git add tools/seal_v16_claim_consumption_oracle.py \
        docs/research/2026-09-01-v1.6-claim-consumption-oracle-seal-o1.md \
        tests/test_v16_claim_consumption_oracle_seal.py
git commit -m "feat: add oracle seal CLI and governance contract"
```

---

### Task 6: Formal builder parity and local hard gates

**Files:**
- Modify only if generated by formal builder: `dist/ai/metaphysics_lab.py`
- No C1/Q1 source semantic edits allowed in this task.

**Interfaces:**
- Consumes completed O1 source/tests/docs.
- Produces locally verified exact candidate tree ready for GitHub transport.

- [ ] **Step 1: Rebuild formal AI distribution**

```bash
python3.9 tools/build_ai_distribution.py
python3.9 tools/build_ai_distribution.py --check
git status --short
```
Expected: only builder-authorized generated artifact drift. If any source/test/doc changes appear, stop and investigate.

- [ ] **Step 2: Run O1 focused regression**

```bash
python3.9 -m unittest -v \
  tests.test_v16_claim_consumption_oracle_seal \
  tests.test_v16_claim_consumption_qualification \
  tests.test_v16_claim_consumption_contract \
  tests.test_v16_coordination_wrapper_integration \
  tests.test_v16_coordination_policy_v2
```
Expected: PASS.

- [ ] **Step 3: Run repository validation-equivalent pre-gates**

Run the same commands used by `.github/workflows/lin-tianji-v1.5-validation.yml` for:
```text
Bazi flow-day/hour qualification
Ziwei flow-day/hour qualification
Ziwei month-boundary qualification
focused regression
prediction validation
v1.5 release surface
deterministic three-file package
```
Expected: all PASS.

- [ ] **Step 4: Run full repository regression once to completion**

```bash
python3.9 -m unittest discover -s tests -p 'test_*.py' -v
```
Expected: `OK`, no failures/errors.

- [ ] **Step 5: Run Python 3.9 compile and final builder parity**

```bash
python3.9 -m compileall -q engine tools tests
python3.9 tools/build_ai_distribution.py --check
git diff --check
```
Expected: PASS.

- [ ] **Step 6: Commit generated artifact if and only if builder changed it**

```bash
git add dist/ai/metaphysics_lab.py
git commit -m "build(ai): sync oracle seal O1 runtime distribution"
```
Skip this commit if builder produced no diff.

- [ ] **Step 7: Verify clean candidate**

```bash
python3.9 tools/build_ai_distribution.py --check
git diff --exit-code
git status --porcelain
```
Expected: empty status.

---

### Task 7: GitHub transport and Hosted same-SHA confirmation

**Files:**
- No candidate semantic changes permitted.
- Helper/CI carrier infrastructure must remain outside the authoritative research diff.

**Interfaces:**
- Consumes: local fully-GREEN O1 candidate bytes.
- Produces: GitHub Draft research PR and Hosted Validation evidence on one exact SHA.

- [ ] **Step 1: Create GitHub research branch from frozen Q1 SHA**

Branch:
```text
research/v1.6-claim-consumption-oracle-seal-o1
```
Base SHA:
```text
4c5df745554b1d14a08b58aae45f4212b0162132
```

- [ ] **Step 2: Transport locally verified files with byte-hash guards**

Before push, verify every transported file SHA256 against the local candidate. Transport must fail before branch mutation if any byte or path differs.

- [ ] **Step 3: Open authoritative Draft PR**

Base:
```text
research/v1.6-claim-consumption-qualification-q1
```
PR body must state:
```text
GENERAL_ONLY
PRIVATE_Q1_NOT_EXECUTED
C1_Q1_READ_ONLY
promotion_allowed=false
```

- [ ] **Step 4: Trigger formal Validation only after exact candidate tree is on GitHub**

Use a separate Draft main CI carrier if repository workflow triggers require it. Carrier must say `Never merge` and must not alter the candidate tree.

- [ ] **Step 5: Require all Hosted gates on one exact SHA**

Expected PASS:
```text
Bazi qualification
Ziwei qualification
builder rebuild/upload
focused regression
prediction validation
release surface
deterministic package
full repository regression
Python 3.9 compile
clean tree
```

- [ ] **Step 6: Freeze O1 candidate and close CI carrier**

Update authoritative PR status to:
```text
GENERAL_HOSTED_QUALIFIED / PRIVATE_NOT_EXECUTED
```
Keep PR Draft/open/not merged. Close CI carrier unmerged.

- [ ] **Step 7: Explicitly do not run private Q1**

No private oracle currently exists that was adjudicated and sealed before this O1 candidate cycle. O1 completion therefore stops after general/Hosted qualification. Any future real oracle creation/evaluation is a separate authorized workflow.

---

## Plan Self-Review Result

- Spec coverage: every architecture responsibility, schema, digest, privacy rule, sealing workflow, verification rule, join rule, general hard gate, private threshold boundary and failure semantic is mapped to Tasks 2–7.
- Placeholder scan: no implementation placeholder or unspecified “handle later” step remains.
- Type consistency: function names and schema names are identical across Tasks 2–5; join targets the frozen Q1 `INPUT_SCHEMA` and validator only.
- Scope: one subsystem only — Oracle Seal O1. No C1/Q1 scoring, Coordination, ranking, Hybrid or private-evaluation changes are included.
