# Claim Consumption Oracle Seal O1 Design

## Status and provenance

- Research cycle: `v1.6 Claim Consumption Oracle Seal O1`.
- Authoritative upstream frozen Q1 candidate on GitHub: `4c5df745554b1d14a08b58aae45f4212b0162132`.
- Authoritative upstream frozen C1 candidate on GitHub: `39a084b9e7e5d56f0d6ac0970ed5683258a4d402`.
- The local workspace contains byte-validated Q1/C1 source state but has reconstructed local commit lineage; local commit SHAs must not be presented as GitHub provenance.
- Q1 evaluator semantics and C1 production policy are read-only in O1.
- Coordination, Phase 3 ranking, Claim Evidence candidate sets, Interpretation ranking, and Hybrid render policy are read-only.
- No prior private aggregate outcome is an O1 policy-selection input.

## Problem

Q1 can deterministically score a complete `v1.6-claim-consumption-qualification-input.v1` payload, but that evaluator input contains both:

1. candidate-produced `claim_consumption_bundle`; and
2. independently adjudicated claim-level `expectations`.

That combined evaluator input cannot itself serve as the pre-candidate oracle seal. If the full evaluator input were prepared before candidate freeze, it would require candidate output that does not yet exist; if it were prepared after candidate freeze without an earlier expectation seal, the project could not prove that the claim-level answers were fixed before scoring.

The project therefore needs a separate sealing authority that freezes only the adjudicated oracle expectations and case-set identity before candidate scoring, while keeping private structured inputs outside git. After candidate freeze, a join step combines the sealed oracle with frozen candidate C1 output to form the existing Q1 evaluator input without changing Q1 scoring semantics.

## Goal

Add a deterministic, privacy-preserving Oracle Seal subsystem that can:

1. strictly validate a candidate-independent claim-level oracle;
2. compute deterministic case/oracle/rubric/set/seal digests;
3. emit an aggregate-only public seal receipt containing no case-level answers;
4. later verify that the same sealed oracle is being used;
5. join the sealed oracle with frozen candidate C1 output into the already-frozen Q1 evaluator input schema; and
6. preserve a clear audit boundary between adjudication, sealing, candidate execution, and private evaluation.

O1 establishes evaluation integrity. It does not define or tune C1 behavior and does not by itself authorize private evaluation, promotion, merge, default switch, tag, or release.

## Non-goals

O1 must not:

- modify `engine/distribution/claim_consumption_contract.py`;
- modify `engine/distribution/claim_consumption_qualification.py` scoring semantics;
- modify Coordination semantics;
- change Phase 3 ranking or Interpretation candidate sets;
- infer claim-level oracle labels from prior private Interpretation domain/event-family labels;
- derive oracle expectations from previous private aggregate PASS/FAIL results;
- place raw private oracle answers, private case identifiers, subject data, birth data, event text, or narrative adjudication into git;
- encrypt private answers into git as a substitute for keeping them outside git;
- define arbitrary non-zero release tolerances for under-render, caveat excess, or specificity downgrade;
- execute a private Q1 evaluation as part of O1 development;
- promote, merge, default-switch, tag, or release.

## Architecture

O1 has four isolated responsibilities.

### 1. Oracle contract and sealing

Create `engine/distribution/claim_consumption_oracle_seal.py`.

It owns:

- strict `v1.6-claim-consumption-oracle.v1` validation;
- canonical case digest computation;
- oracle expectation-set digest computation;
- rubric digest verification;
- deterministic seal construction;
- seal verification;
- aggregate-only seal-receipt construction.

It must not import private fixtures or call C1 policy.

### 2. Candidate-output join

The same module owns a deterministic join function that combines:

- one verified sealed oracle; and
- one candidate-output package produced by a frozen candidate;

into the existing Q1 input schema:

`v1.6-claim-consumption-qualification-input.v1`.

The join step does not score claims and does not reinterpret expectations. It only verifies identity/digests and assembles the already-frozen evaluator input.

### 3. Thin CLI surface

Create `tools/seal_v16_claim_consumption_oracle.py` with three explicit modes:

- `seal`: validate oracle and write private seal plus optional public receipt;
- `verify`: verify an oracle against a seal and emit a status-only verification report;
- `join`: combine a verified sealed oracle with candidate output and write Q1 evaluator input.

The CLI does not automatically commit, upload, or copy private input into repository paths.

### 4. Synthetic-only fixtures and tests

Create synthetic fixtures and tests for:

- valid sealing;
- order-independent digests;
- tamper detection;
- unknown/private-field rejection;
- rubric mismatch;
- case-set mismatch;
- candidate-output mismatch;
- exact join behavior;
- no-answer public receipt;
- no scoring changes to Q1.

No real private case content is used during O1 development.

## Data contracts

### Oracle schema

Schema version:

`v1.6-claim-consumption-oracle.v1`

Top-level fields are exactly:

```text
schema_version
oracle_profile
rubric_digest
cases
```

`oracle_profile` is a non-empty versioned identifier such as:

`lin_tianji_claim_consumption_oracle_v1`

`rubric_digest` is a lowercase SHA-256 digest of the frozen human/machine adjudication rubric artifact used to create the expectations.

Each case contains exactly:

```text
case_id
expectations
cutoff_contamination
oracle_case_digest
```

The `expectations` shape is exactly the frozen Q1 expectation contract:

```text
claim_id
expected_authorization
minimum_acceptable_specificity
maximum_specificity
caveat_required
```

No `claim_consumption_bundle` is allowed in the oracle schema. Candidate output is intentionally absent from the seal.

### Oracle case identity

`oracle_case_digest` is SHA-256 of the canonical case payload excluding `oracle_case_digest`.

It covers:

- opaque `case_id`;
- ordered-normalized expectations;
- `cutoff_contamination`.

Expectation order is normalized by `claim_id` before digesting. Duplicate `claim_id` values fail closed.

### Oracle seal schema

Schema version:

`v1.6-claim-consumption-oracle-seal.v1`

Fields are exactly:

```text
schema_version
oracle_profile
case_count
claim_count
rubric_digest
oracle_expectation_digest
case_set_digest
cutoff_contamination_count
sealed_at
seal_digest
```

Definitions:

- `oracle_expectation_digest`: SHA-256 of the canonical list of normalized case payloads with `oracle_case_digest` removed, cases sorted by `case_id`, and each case's expectations sorted by `claim_id`. It therefore covers opaque case identity, all expectation answers, and cutoff contamination while remaining invariant to input list order.
- `case_set_digest`: SHA-256 of the sorted list of `oracle_case_digest` values. This is intentionally redundant with `oracle_expectation_digest` so audits can distinguish whole-oracle expectation drift from case-set identity drift.
- `cutoff_contamination_count`: aggregate count only.
- `sealed_at`: externally supplied UTC RFC3339 timestamp recorded for audit; it is part of `seal_digest` but not used to decide semantic correctness.
- `seal_digest`: SHA-256 over the complete seal object excluding `seal_digest`.

The seal may remain private because it contains digests tied to the private oracle, but it contains no raw event text or subject data.

### Public seal receipt schema

Schema version:

`v1.6-claim-consumption-oracle-seal-receipt.v1`

Fields are exactly:

```text
schema_version
status
oracle_profile
case_count
claim_count
rubric_digest
case_set_digest
oracle_expectation_digest
cutoff_contamination_count
sealed_at
seal_digest
promotion_allowed
```

Required values:

```text
status = SEALED
promotion_allowed = false
```

The public receipt must not contain:

- `case_id`;
- `claim_id`;
- `expected_authorization`;
- specificity bounds;
- domains;
- reason codes;
- subject/birth/event data;
- free-form adjudication text.

A receipt with `cutoff_contamination_count > 0` may still prove that a seal exists, but it is not eligible for later private qualification execution. The join step must fail closed on a contaminated seal.

### Candidate-output package schema

Schema version:

`v1.6-claim-consumption-candidate-output.v1`

Top-level fields are exactly:

```text
schema_version
candidate_sha
cases
```

Each case contains exactly:

```text
case_id
claim_consumption_bundle
candidate_case_digest
```

`candidate_sha` must be a 40-character lowercase Git commit SHA. O1 does not decide whether that SHA passed Hosted validation; governance checks that separately before private execution.

`claim_consumption_bundle` is the existing frozen C1 public bundle shape accepted by Q1.

`candidate_case_digest` is SHA-256 of canonical `case_id + claim_consumption_bundle`, excluding `candidate_case_digest`.

Unknown fields fail closed.

### Join output

The join function emits exactly:

```text
schema_version = v1.6-claim-consumption-qualification-input.v1
classification = private_external_evaluation
cases = [...]
```

Each joined case contains exactly the Q1 input fields:

```text
case_id
claim_consumption_bundle
expectations
cutoff_contamination
input_digest
```

`input_digest` is recomputed using the existing Q1 canonical case rule. O1 must not reuse an oracle or candidate digest as `input_digest`.

## Canonicalization rules

All O1 digests use the same deterministic JSON convention already used in v1.6 qualification code:

```text
UTF-8
sort_keys=True
separators=(",", ":")
ensure_ascii=False
allow_nan=False
SHA-256 lowercase hexadecimal
```

Order normalization:

- top-level case order is semantically irrelevant;
- cases are canonicalized by `case_id` for aggregate digest construction;
- expectations are canonicalized by `claim_id`;
- candidate cases are canonicalized by `case_id`;
- duplicate IDs fail closed rather than being deduplicated.

## Strict validation and privacy controls

O1 rejects unknown fields at every schema level.

Explicitly prohibited examples include:

```text
subject_name
birth_date
birth_time
full_address
actual_event
event_text
narrative
notes
raw_chart
```

The list is illustrative, not exhaustive; strict allowlists provide the actual enforcement.

The public receipt and verification outputs are aggregate-only. They must not serialize case IDs or expectation contents.

The join output is private structured evaluation input and must remain outside git. No CLI default may target a repository path for joined private output.

## Seal workflow

The valid workflow is:

```text
1. Freeze adjudication rubric
2. Prepare claim-level expectations without candidate output
3. Validate oracle schema
4. Seal oracle
5. Store oracle + seal outside git
6. Commit only aggregate seal receipt if desired
7. Freeze candidate SHA independently
8. Pass local + Hosted general gates
9. Export candidate C1 output for the same opaque case set
10. Verify oracle seal
11. Verify candidate-output package
12. Join oracle + candidate output
13. Run Q1 private evaluator exactly once
14. Publish aggregate-only Q1 result
```

Invalid workflows include:

- modifying expectations after candidate output is observed;
- resealing after seeing private evaluation results and treating it as the same evaluation cycle;
- using prior Interpretation private labels as Q1 claim expectations;
- joining an unsealed oracle;
- joining a candidate case set that differs from the sealed oracle case set;
- running Q1 private evaluation before candidate freeze or Hosted qualification.

## Seal verification semantics

`verify_oracle_seal(oracle, seal)` must fail closed if any of these differ:

- schema/profile;
- rubric digest;
- case count;
- claim count;
- any case digest;
- case-set digest;
- oracle-expectation digest;
- contamination count;
- seal digest.

Verification returns a minimal status object and never returns oracle answers.

## Join semantics

`join_sealed_oracle_with_candidate(oracle, seal, candidate_output)` must:

1. verify the seal against the oracle;
2. reject `cutoff_contamination_count > 0`;
3. validate the candidate package and candidate SHA format;
4. require exact equality of oracle and candidate `case_id` sets;
5. for each case, require exact equality of oracle expectation `claim_id` set and candidate C1 decision `claim_id` set;
6. preserve the oracle expectations byte-semantically after canonical normalization;
7. preserve the candidate C1 bundle byte-semantically after validation;
8. compute a fresh Q1 `input_digest` for each joined case;
9. emit deterministic case ordering by `case_id`;
10. call the existing read-only `validate_claim_consumption_qualification_input()` on the completed joined payload; and
11. never call `evaluate_claim_consumption_qualification()` or any Q1 scoring function during join.

The validated joined input is then passed separately to the unchanged Q1 evaluator. This lets O1 prove schema compatibility without changing or pre-running qualification scoring.

## Rubric identity

O1 requires an explicit `rubric_digest` but does not create the rubric content.

The rubric must be frozen before private adjudication and must define at least:

- the three authorization labels;
- caveat-required semantics;
- specificity scale and minimum/maximum rules;
- claim-id matching rules;
- cutoff/contamination handling;
- adjudicator disagreement resolution process.

A future private oracle is not valid unless its seal references a frozen rubric digest.

O1 development tests use a synthetic rubric digest only; they do not create a private adjudication rubric.

## General hard gates

O1 general/synthetic conformance requires:

```text
all positive synthetic seal/verify/join fixtures pass
all tamper fixtures fail closed
unknown/private fields rejected
public receipt contains no case/claim answers
case/expectation ordering does not change digests
oracle/candidate case-set mismatch rejected
oracle/candidate claim-set mismatch rejected
contaminated oracle cannot join
joined Q1 input passes the unchanged Q1 validator
generated AI distribution parity passes
full repository regression passes
Python 3.9 compile passes
clean tree passes
Hosted same-SHA validation passes
```

No private result is needed to make O1 general-qualified.

## Private threshold boundary

O1 does not define performance thresholds for Q1 private metrics.

The only safety preconditions enforced by O1 before a private run are structural/integrity constraints:

```text
seal valid
rubric identity valid
case/claim set identity valid
cutoff contamination = 0
candidate frozen and externally qualified by project governance
```

Q1 private performance thresholds, if introduced later, require a separate prospective research decision based on general rationale and must be frozen before any private result is inspected.

## Failure and cycle semantics

- Seal verification failure: do not join; no private evaluation.
- Candidate-output identity failure: do not join; no private evaluation.
- Contaminated oracle: do not join; no private evaluation.
- Joined-input validation failure: stop and debug infrastructure/contracts before any private evaluation.
- Once a valid frozen candidate is evaluated against a valid sealed private oracle, that private evaluation is exactly once for that candidate/oracle pair.
- A failed private performance gate, if one exists in a future cycle, cannot be used to edit the sealed oracle, C1 policy, Q1 scoring, or thresholds within the same cycle.

## Files expected in implementation

Create:

```text
engine/distribution/claim_consumption_oracle_seal.py
tools/seal_v16_claim_consumption_oracle.py
tests/fixtures/v1.6-claim-consumption-oracle.synthetic.v1.json
tests/fixtures/v1.6-claim-consumption-candidate-output.synthetic.v1.json
tests/test_v16_claim_consumption_oracle_seal.py
docs/research/2026-09-01-v1.6-claim-consumption-oracle-seal-o1.md
```

Modify only if the formal builder requires it:

```text
dist/ai/metaphysics_lab.py
```

The implementation must not modify C1 or Q1 evaluator semantics.

## Success criteria

O1 is successful when the project can demonstrate, using only synthetic/general evidence, that:

1. claim-level expectations can be frozen independently of candidate output;
2. a later oracle mutation is detectable;
3. a later candidate-output mutation is detectable;
4. a candidate cannot be joined to a different sealed case/claim set;
5. the public seal receipt proves seal identity without exposing answers;
6. the joined private input is exactly the existing Q1 contract;
7. Q1 scoring remains unchanged;
8. local and Hosted hard gates pass on one frozen candidate SHA; and
9. no private Q1 evaluation is executed during O1 development.
