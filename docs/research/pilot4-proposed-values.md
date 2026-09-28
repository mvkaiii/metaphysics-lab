# Pilot-4 proposed values

Status: **APPROVED_BY_HUMAN_DECISION_OWNER / READY_FOR_START_AUTHORIZATION**  
Preregistered at: `2026-09-28T20:07:32+08:00`  
Approved at: `2026-09-28T21:41:06+08:00`

Pilot-4 is a new protocol. No Pilot-1/2/3 approval or exposure state is inherited.

## Proposed governance values

- D01–D12: fresh Pilot-4 decisions, all `APPROVED`.
- ENUM-01: mandatory complete window→structural-snapshot enumeration; `APPROVED`.
- AGG-01: mandatory complete-union yearly claim-universe aggregation; `APPROVED`.
- Manual override: prohibited.
- Promotion effect: none.
- Separate start authorization: required after all mandatory decisions are approved.

## Proposed window

- timezone: `Asia/Taipei`
- start: `2027-05-01T00:00:00+08:00`
- end: `2027-06-30T23:59:59+08:00`
- maturity delay: 72 hours
- claim scope: yearly
- timing scope: monthly
- requested dynamic scopes: yearly + monthly

Selection basis is only the next non-overlapping future calendar-aligned same-year multi-month window after Pilot-3. No metaphysical output or prior pilot case observation is used.

## ENUM-01 proposed value

Profile:

`lin_tianji_complete_structural_snapshot_enumerator_v1`

Rule:

`complete_union_of_authoritative_yearly_monthly_time_boundaries_no_post_exposure_merge`

The exact normative rule is in:

`docs/research/pilot4-structural-snapshot-enumeration-preregistration.md`

## AGG-01 proposed value

Profile:

`lin_tianji_multi_segment_yearly_claim_universe_v1`

Rule:

`complete_union_of_all_manifested_efa_child_inventories`

This is a fresh Pilot-4 approval item. It is not inherited from Pilot-3. It was approved at `2026-09-28T21:41:06+08:00`.

## Hard boundary

D01-D12, ENUM-01, AGG-01, and the window are approved. This approval moves Pilot-4 only to `READY_FOR_START_AUTHORIZATION`.

A separate final seal/start authorization must bind the exact candidate commit, candidate package SHA256, capability manifest SHA256, final Pilot-4 protocol SHA256, approved window-policy SHA256, ENUM-01 identity, AGG-01 identity, and the approved private storage/access record.

Until that separate authorization exists, source census, intake, S1, PCG, case exposure, case-specific enumeration, EFA, claim locking, prediction, outcome collection, adjudication, merge, tag, Release, or publish remain unauthorized.
