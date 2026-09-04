# Claim Consumption Qualification Q1 Design

## Status and provenance

- Research cycle: `v1.6 Claim Consumption Qualification Q1`.
- Authoritative upstream frozen candidate on GitHub: `39a084b9e7e5d56f0d6ac0970ed5683258a4d402`.
- Local workspace contains the byte-validated C1/Hybrid source state but has reconstructed local commit lineage; local commit SHAs must not be presented as GitHub provenance.
- Upstream Claim Consumption C1 is read-only in this cycle.
- Coordination C, Phase 3 ranking, Claim Evidence candidate sets, and Interpretation domain/event-family candidates are read-only.
- Prior private aggregate outcomes are not policy-selection inputs for Q1.

## Problem

Claim Consumption C1 now owns deterministic Python render authorization (`render`, `render_with_caveat`, `abstain_claim`) and authorized specificity, but the existing v1.6 private qualification contract scores only selector and Interpretation domain/event-family/false-positive/abstention metrics. It does not score C1 decisions.

Therefore the project currently has a production authority without a matching qualification authority. Reusing the old Interpretation labels as if they were claim-level authorization labels would conflate two different contracts and would be especially unsafe because the approved strict private JSON is intentionally not retained in the current workspace.

## Goal

Add an independent, deterministic Claim Consumption qualification subsystem that can score C1 render authorization and specificity against an independently adjudicated structured oracle without exposing raw personal/event text or changing C1 behavior.

Q1 is a qualification/evaluation subsystem only. It does not tune C1 and does not authorize release promotion by itself.

## Non-goals

Q1 must not:

- change `engine/distribution/claim_consumption_contract.py`;
- change Coordination semantics;
- change Phase 3 ranking;
- add/remove/reorder domains or event-family candidates;
- reinterpret prior private domain/event-family labels as claim-level authorization labels;
- infer private labels from previous aggregate FAILs;
- define a private release tolerance for under-render or unnecessary caveats from prior private outcomes;
- run a private Q1 evaluation before an independently prepared claim-level oracle has been sealed;
- merge, default-switch, tag, or release.

## Architecture

The subsystem has four isolated pieces:

1. `engine/distribution/claim_consumption_qualification.py`
   - owns strict input-schema validation, C1-bundle digest validation, deterministic scoring, aggregation, and report digest;
   - has no imports from private data files;
   - does not call or modify C1 production policy.

2. `tools/evaluate_v16_claim_consumption_qualification.py`
   - thin CLI wrapper around the deterministic evaluator;
   - reads one JSON fixture/input and writes canonical JSON to stdout or an optional output file;
   - never writes case-level private content into repository paths automatically.

3. `tests/fixtures/v1.6-claim-consumption-qualification.synthetic.v1.json`
   - synthetic-only oracle and synthetic C1 decision bundles;
   - contains no real subject, birth, event, or prior private case data.

4. `tests/test_v16_claim_consumption_qualification.py`
   - locks schema rejection, scoring semantics, hard general conformance, determinism, CLI parity, and no-private-field rules.

Production C1 remains an upstream source, not a dependency to be retuned.

## Input contract

Schema version:

`v1.6-claim-consumption-qualification-input.v1`

Top-level fields are exactly:

```text
schema_version
classification
cases
```

`classification` is one of:

```text
synthetic_validation
private_external_evaluation
```

Each case contains exactly:

```text
case_id
claim_consumption_bundle
expectations
cutoff_contamination
input_digest
```

No name, birth data, raw event text, narrative notes, or free-form adjudication text is allowed.

### `claim_consumption_bundle`

This is the public C1 output shape and must include exactly the C1 public fields needed for qualification:

```text
profile_version
claim_evidence_digest
coordination_digest
target_scope
decisions
claim_consumption_digest
```

The evaluator recomputes `claim_consumption_digest` over the bundle excluding the digest field and rejects mismatch.

Each decision must expose the existing C1 public decision fields:

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

The evaluator does not recompute the C1 decision from Bazi/Ziwei evidence. It qualifies the frozen C1 output.

### `expectations`

Each expectation contains exactly:

```text
claim_id
expected_authorization
minimum_acceptable_specificity
maximum_specificity
caveat_required
```

`expected_authorization` is one of:

```text
render
render_with_caveat
abstain_claim
```

For `render` and `render_with_caveat`, both specificity bounds are required and must satisfy:

```text
domain <= event_family <= concrete_event <= highly_specific_event
minimum_acceptable_specificity <= maximum_specificity
```

For `abstain_claim`, both specificity fields must be `null` because specificity is not rendered.

`caveat_required` is deliberately redundant and fail-closed:

```text
render              -> false
render_with_caveat  -> true
abstain_claim       -> false
```

This redundancy prevents an internally contradictory oracle from silently entering qualification.

### Why `minimum_acceptable_specificity` exists

The approved design requires both specificity-overreach and excessive-downgrade metrics. A maximum alone can detect overreach but cannot distinguish a legitimate conservative downgrade from excessive downgrade. Q1 therefore adds `minimum_acceptable_specificity` as a necessary internal-consistency correction.

## Identity and contamination controls

- `case_id` values must be unique.
- Within a case, expectation `claim_id` values must be unique.
- Actual C1 decision `claim_id` values must be unique.
- Actual and expected claim-id sets must match exactly; missing or extra rendered claims fail closed instead of being silently ignored.
- `input_digest` is SHA-256 of the canonical case payload excluding `input_digest`.
- Canonical JSON uses UTF-8, sorted keys, compact separators, `ensure_ascii=False`, and `allow_nan=False`.
- Unknown top-level/case/expectation/bundle/decision fields are rejected.
- Fields such as `subject_name`, `birth_date`, `actual_event`, `event_text`, or `notes` are therefore rejected rather than redacted after ingestion.
- Any `cutoff_contamination=true` is counted and makes general synthetic conformance fail.

## Scoring semantics

Evaluation is per expected claim.

### Authorization alignment

`matched`:
- actual decision exactly matches expected authorization;
- caveat status is correct;
- rendered specificity lies within the accepted range when applicable.

`partial`:
- actual and expected are both renderable but differ only in caveat requirement; or
- authorization is otherwise correct but specificity is outside the accepted band.

`missed`:
- expected `abstain_claim`, actual is renderable; or
- expected renderable, actual is `abstain_claim`.

### Safety / quality counters

`over_render_count`
- expected `abstain_claim`, actual `render` or `render_with_caveat`.

`under_render_count`
- expected `render` or `render_with_caveat`, actual `abstain_claim`.

`caveat_omission_count`
- expectation requires caveat, actual is plain `render`.

`unnecessary_caveat_count`
- expectation is plain `render`, actual is `render_with_caveat`.

`specificity_overreach_count`
- rendered `authorized_specificity` is above `maximum_specificity`.

`specificity_excessive_downgrade_count`
- rendered `authorized_specificity` is below `minimum_acceptable_specificity`.

Specificity counters are not evaluated for `abstain_claim` expectations.

## Report contract

Schema version:

`v1.6-claim-consumption-qualification-report.v1`

Report fields:

```text
schema_version
classification
case_count
claim_count
decision_alignment
  matched
  partial
  missed
over_render_count
under_render_count
caveat_omission_count
unnecessary_caveat_count
specificity_overreach_count
specificity_excessive_downgrade_count
cutoff_contamination_count
input_set_digest
general_conformance_status
promotion_allowed
report_digest
```

`promotion_allowed` is always `false` in Q1. Q1 creates measurement authority, not release authority.

`input_set_digest` is computed from ordered case `input_digest` values after canonical case-id sorting. `report_digest` is computed over the report excluding `report_digest`.

No case ID, claim ID, reason code, domain, or private text is emitted into the aggregate report.

## General synthetic conformance gate

For `classification=synthetic_validation`, `general_conformance_status=PASS` requires all of:

```text
cutoff_contamination_count == 0
over_render_count == 0
specificity_overreach_count == 0
decision_alignment.partial == 0
decision_alignment.missed == 0
```

Unknown-field leakage never reaches the report because schema validation rejects it before evaluation.

The synthetic fixture contains only exact expected matches so that the baseline report is PASS. Tests mutate copies of the fixture to prove each negative counter and rejection path.

For `classification=private_external_evaluation`, Q1 still computes the aggregate metrics but `promotion_allowed` remains false. This design intentionally does not define acceptable private under-render/unnecessary-caveat thresholds. Those thresholds must be frozen in a separate general-only governance step before a sealed Q1 private oracle is opened.

## Synthetic matrix

The baseline fixture covers:

1. plain render within specificity band;
2. render-with-caveat within specificity band;
3. legitimate abstain;
4. event-family lower/upper band exact match;
5. concrete-event bounded render;
6. multiple cases to lock ordering/digest determinism.

Mutation tests cover:

1. over-render;
2. under-render;
3. caveat omission;
4. unnecessary caveat;
5. specificity overreach;
6. specificity excessive downgrade;
7. malformed C1 digest;
8. malformed input digest;
9. unknown/private fields;
10. duplicate/missing/extra claim IDs;
11. case-order permutation producing identical aggregate report digest.

## Private-evaluation governance

Q1 does not authorize an immediate private run.

A future Q1 private evaluation requires, in order:

1. an independently adjudicated claim-level oracle using this schema;
2. the oracle sealed before candidate scoring;
3. private thresholds for metrics not already strict-zero frozen from general rationale only;
4. a frozen candidate SHA with local + Hosted general GREEN;
5. exactly one external private evaluation;
6. aggregate-only public output;
7. any release-gate FAIL stops that cycle with no private-result retuning.

The previous v1.6 private domain/event-family aggregate is not a substitute for this oracle.

## Test and release gates

Q1 implementation is complete only when all are true on the same candidate content:

- synthetic RED observed before evaluator production code;
- Q1 focused tests PASS;
- C1 production tests PASS unchanged;
- Coordination / Interpretation wrapper regressions PASS;
- AI contract docs PASS;
- deterministic CLI output PASS;
- AI distribution builder parity PASS (Q1 engine module will be included in runtime bundle if under `engine/`);
- repository full regression PASS on Python 3.9;
- Python 3.9 compile PASS;
- clean tree PASS;
- Hosted exact-SHA confirmation PASS;
- no private Q1 evaluation executed in this cycle unless a separately sealed Q1 oracle and pre-frozen thresholds exist.
