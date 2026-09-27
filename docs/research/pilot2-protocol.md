# Prospective Pilot-2 protocol — sequencing-corrected draft

**Protocol decision status:** `PENDING_ITEM_APPROVAL`  
**Pilot status:** `NOT_STARTED`  
**Start authorization:** `NOT_AUTHORIZED`  
**Candidate case processing:** `PROHIBITED_UNTIL_PRE_CANDIDATE_GATE_READY`

Pilot-2 is a new pilot ID and protocol version. It does not inherit Pilot-1
start authorization, eligibility, case identity, or prediction state.

Pilot-1 ended `HALTED_NON_QUALIFYING` because a source-file census existed,
but a schema-valid S1 source manifest had not been frozen before candidate case
processing. Pilot-2 fixes this sequencing defect by creating a mandatory
pre-candidate gate.

## Purpose

Pilot-2 remains a single-subject, single-arm prospective **workflow feasibility**
pilot. It tests whether Metaphysics Lab can execute the complete prospective
sequence without retrospective repair:

`human approval → start seal → private source census → private intake registry → schema-valid S1 source manifest → pre-candidate gate → candidate execution → complete EFA child universe → claim-universe lock → prediction lock → wait → blind adjudication → process analysis`

Pilot-2 does not test population-level predictive validity, superiority,
calibration, or Stable maturity.

## New-case rule

Pilot-2 requires a **new future case/window packet**.

A new pilot ID, new opaque case ID, branch, digest, or registry snapshot does not
erase previous candidate exposure. The private intake/S1 chain must independently
support `candidate_exposure_status=UNEXPOSED` for the new case before the
candidate can process it.

The study owner may remain the same person only if the new future case/window is
independently eligible under the frozen intake/S1 rules. Pilot-1's Nov-Dec 2026
case/window is not reusable.

## Proposed time scope

Proposed timezone: `Asia/Taipei`.

Proposed new outcome window:

`2027-01-01T00:00:00+08:00` → `2027-02-28T23:59:59+08:00`

This matches the existing prospective-window resolver class:
calendar-aligned, same-civil-year, multi-month, yearly claim authority with
monthly timing. A 72-hour maturity delay follows the window end.

The window remains proposed until D06 is explicitly approved.

## Mandatory pre-candidate gate

No real candidate case processing is permitted until all of the following are
true and sealed:

1. D01-D12 are approved for Pilot-2.
2. A separate Pilot-2 start authorization binds exact candidate/package/
   capability-manifest/protocol identities.
3. The private source census for the new case is frozen.
4. The private prospective intake registry snapshot is built and validated.
5. Intake result is `ELIGIBLE_FOR_S1_SOURCE`.
6. A schema-valid S1 source manifest / eligible-set manifest is frozen from the
   same provenance chain.
7. S1 exposure status is explicitly `UNEXPOSED`.
8. S1 source-manifest creation time precedes every candidate processing
   timestamp for that case.
9. A public de-identified pre-candidate gate receipt validates as READY.

If any item is false, unknown, late, or unverifiable, the gate remains BLOCKED.
There is no manual override.

## Candidate and claim-universe sequence

Only after the pre-candidate gate is READY may the frozen candidate read the
case.

The candidate then:

1. materializes the approved yearly/monthly structural context;
2. builds the deterministic EFA child inventory;
3. locks the **complete** EFA child-ID universe, including opened and unopened
   children;
4. validates exact-match S1 claim-universe membership;
5. applies downstream HOC/render authority without using a render subset as the
   claim universe;
6. creates the prospective prediction lock before the outcome window starts.

Ranking/primary visibility may vary with timing state. That does not change
membership in the complete locked child universe.

## Privacy boundary

Real case identifiers, birth data, source records, private digests, claim IDs,
prediction text, outcome text, and private timestamps remain outside public Git.

Public Git may contain only:
- protocol/governance text;
- empty/de-identified templates;
- aggregate gate state;
- process-level deviations;
- tests using synthetic values.

## Pilot-2 decision gate

D01-D12 are not inherited automatically from Pilot-1. Proposed values are in
`pilot2-proposed-values.md`. The committed Pilot-2 decision receipt remains all
PENDING until the human decision owner explicitly approves Pilot-2.

Even after D01-D12 approval, a separate Pilot-2 start authorization is required.

Until both gates are complete, do not create a real intake record, S1 source
manifest, candidate output, claim lock, or prediction lock.
