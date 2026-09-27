# Prospective Pilot-1 proposed approval values

Status: **PROPOSED_READY_FOR_HUMAN_APPROVAL**
Protocol: `DRAFT_PENDING_HUMAN_APPROVAL`
Pilot: `NOT_STARTED`

This file records proposed values for D01-D12. It does not change the committed
decision receipt, does not approve any item, and does not authorize pilot start.

## Design correction from earlier discussion

An earlier conversational proposal mentioned a 7-day outcome window and 12
attempted locks. That is **not** adopted here. Fresh review of the existing
`prospective_window_scope` research contract shows that v1 accepts only
calendar-aligned, same-civil-year, multi-month windows and resolves them to
yearly claim authority with monthly timing. The existing tests use
`2026-10-01T00:00:00+08:00` through `2026-12-31T23:59:59+08:00` as the Q4
shape. Pilot-1 therefore uses one real end-to-end case and a compatible
Nov-Dec 2026 window instead of inventing a 7-day profile.

## Proposed D01-D12

| ID | Proposed approval value | Start-time binding / limitation |
| --- | --- | --- |
| D01 | Study owner and data subject are the same consenting human. Data custodian may be the same human. Prediction execution and outcome adjudication must use separate information contexts; the prediction context cannot read outcome material, and the adjudication context cannot see prediction content until the outcome bundle is sealed. | Public repo stores role names only, not personal identity. A conflict-of-interest note states that a self-pilot cannot establish population-level efficacy. |
| D02 | Pilot-1 uses only the study owner's own data. No third-party participant or third-party private record is enrolled. Raw inputs, source records, predictions and outcomes stay outside public Git in an approved private workspace. Raw private material is retained through final adjudication plus 30 days, then deleted unless the owner explicitly extends retention. | Exact private storage location/access list is recorded privately before pilot-start authorization. Withdrawal may stop future collection at any time. |
| D03 | Target population is one consenting study owner. Unit of analysis is one prospectively locked case/window packet. Pilot-1 has exactly one planned real case and no replacement case. Eligibility requires resolved input, complete source/provenance authority and a valid pre-window lock; unresolved or late-lock material is recorded as an attempted process failure, not silently replaced. | The private census is frozen before lock. Public Git receives no row-level census. |
| D04 | Question mode is `future_forecast`. No free-text claim invention is allowed. The claim universe is the complete deterministic child-claim inventory produced by the frozen candidate's existing EFA/claim contract for the case; no manual cherry-picking or post-lock additions/removals. Claim IDs, source authority and universe digest are sealed before the outcome window. | Exact claim IDs are generated from the frozen candidate and sealed privately; the governance rule, not a hand-picked static list, is approved here. No validity claim is inferred from claim count. |
| D05 | Single candidate arm only. No Legacy-vs-Candidate comparison and no superiority claim in Pilot-1. Candidate configuration/profile/rule versions are frozen once, before the prediction lock. | Exact candidate commit, package SHA256 and manifest SHA256 are bound later by the separate pilot-start authorization; a later code/config change requires a new authorization/protocol version. |
| D06 | Timezone `Asia/Taipei`. Proposed outcome window: `2026-11-01T00:00:00+08:00` through `2026-12-31T23:59:59+08:00`, matching the existing calendar-aligned same-year multi-month resolver shape (yearly claim authority, monthly timing). Lock must be strictly earlier than window start. Outcome adjudication waits an additional 72 hours after window end. | This Pilot-1 proposal uses the research resolver's existing timestamp convention as-is; it does not reinterpret that older contract as the Visualization `[start,end)` convention. |
| D07 | Private adjudication labels are `SUPPORTED`, `CONTRADICTED`, `INDETERMINATE`, `OUT_OF_UNIVERSE`. Evidence priority: contemporaneous timestamped objective record > independently timestamped digital record > contemporaneous structured self-record > retrospective self-report. Missing/conflicting evidence becomes `INDETERMINATE`; no favorable reinterpretation. | Pilot-1 does not automatically map these labels into main `prospective_validation` verification states because that contract has different semantics (`matched/partial/not_matched/cannot_recall`). Such mapping requires separate integration review. |
| D08 | Outcome material is unavailable to prediction execution. The study owner is not shown the sealed prediction content before the outcome bundle is frozen. Outcome collection proceeds without prediction text. After the window and 72-hour maturity delay, the outcome bundle is sealed; only then may the adjudication context receive the minimum claim text required for labeling. Prediction/candidate identity is disclosed after labels are sealed. | Any premature prediction disclosure, outcome leakage or cross-context contamination is a blind violation and is recorded as a protocol deviation. |
| D09 | Primary success criterion is end-to-end protocol conformance for the one planned case: a valid pre-window lock exists, required source/claim/candidate/time provenance is complete, and no blind violation occurs. Report `valid_lock_count / attempted_lock_count` descriptively (planned denominator 1). Secondary process measures: provenance completeness, outcome-bundle completeness, adjudication completeness and deviation count. | Match/support rate is not a Pilot-1 success metric. No probability calibration or superiority statistic is reported. |
| D10 | Fixed sample/stopping: exactly one real end-to-end planned case; no replacement after a failed lock. Enrollment closes when that case is sealed or when the proposed window can no longer be validly locked, whichever occurs first. No result-dependent early stop. Safety/privacy/integrity failure may stop the pilot and must be reported. | A failed pre-window lock is a process failure, not permission to substitute another case under the same protocol. A retry requires a new protocol version/pilot identifier. |
| D11 | Withdrawal or stop request ends future collection immediately. Late, missing, contradictory, indeterminate and deviation records are not silently deleted or rewritten. Private raw material is removed according to the owner's withdrawal/retention decision; only the minimum de-identified audit fact needed to explain denominator/deviation accounting may remain. | All protocol deviations are append-only with time, reason and affected stage. Material blind/integrity deviations can make the pilot non-qualifying. |
| D12 | Public disclosure is limited to protocol/governance artifacts and a de-identified process summary. Because Pilot-1 is n=1, no claim-level or outcome-level result, exact private timestamp, case ID, private digest, birth data or source-record detail is published. Public result may state only process counts/status, deviations and whether the predeclared feasibility gates were met. | Any broader disclosure requires a new privacy review. No predictive-validity or Stable-promotion claim follows from Pilot-1. |

## Proposed feasibility interpretation

Pilot-1 is a **single-subject, single-arm, prospective workflow feasibility
pilot**. It tests whether Metaphysics Lab can freeze a claim universe, bind an
exact candidate, lock before the outcome window, preserve blinding, collect a
mature outcome bundle and produce an auditable adjudication trail.

It is not powered or designed to establish predictive validity, calibration,
generalization, superiority, or Experimental-to-Stable promotion.

## Approval boundary

If the human approves these values, D01-D12 may be converted from `PENDING` to
`APPROVED` in the public decision receipt with de-identified summaries. That
still does **not** authorize real pilot execution.

Before pilot start, the separate start authorization must additionally bind:

- exact candidate commit;
- candidate package SHA256;
- manifest SHA256;
- final sealed protocol SHA256;
- approved private storage/access record;
- start authorizer role and timestamp.

Until that separate authorization exists, `pilot_status` remains no further than
`READY_FOR_START_AUTHORIZATION` and no real case, prediction lock, outcome
collection or scoring may begin.
