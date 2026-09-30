# Prospective Pilot-4 protocol — start authorized, candidate processing gated

**Protocol decision status:** `ALL_ITEMS_APPROVED`  
**Enumeration decision:** `ENUM-01 APPROVED`  
**Aggregation decision:** `AGG-01 APPROVED`  
**Pilot status:** `AUTHORIZED_NOT_STARTED`  
**Start authorization:** `AUTHORIZED`  
**Candidate case processing:** `PROHIBITED_UNTIL_PCG_READY`

Pilot-4 is a new pilot ID/protocol version. It does not inherit Pilot-1, Pilot-2, or Pilot-3 approval, start authorization, case identity, exposure state, snapshot manifest, EFA census, claim lock, prediction state, or qualification state.

## Purpose

Pilot-4 tests whether the full prospective workflow can preregister both missing multi-segment contracts before a fresh case is exposed:

1. deterministic complete window→structural-snapshot enumeration;
2. complete-union yearly claim-universe membership across every manifested segment.

The intended sequence is:

```text
D01-D12 + ENUM-01 + AGG-01 human approval
→ separate final seal / start authorization
→ private source census
→ private intake registry
→ schema-valid S1 source manifest
→ PCG READY
→ fresh candidate case exposure
→ deterministic complete window→snapshot enumeration
→ materialize exactly one pre-EFA structural state per enumerated segment
→ freeze exact ordered snapshot manifest
→ one complete yearly EFA inventory per manifested segment
→ complete-union yearly claim-universe lock
→ exact S1 membership validation
→ segment-aware downstream authority compatibility gate
→ prediction lock
→ wait for outcome window + maturity
→ blind adjudication
→ process analysis
```

Any failed gate halts Pilot-4. No replacement case is allowed under the same protocol after exposure.

## ENUM-01

Approved profile:

`lin_tianji_complete_structural_snapshot_enumerator_v1`

Approved rule:

`complete_union_of_authoritative_yearly_monthly_time_boundaries_no_post_exposure_merge`

Normative preregistration:

`docs/research/pilot4-structural-snapshot-enumeration-preregistration.md`

ENUM-01 was explicitly approved by the human decision owner at `2026-09-28T21:41:06+08:00`. It is mandatory, has no manual override, and has no start-authorization effect. Actual case-specific enumeration remains prohibited before separate start authorization and PCG READY.

## AGG-01

Pilot-4 separately approves:

`complete_union_of_all_manifested_efa_child_inventories`

Profile:

`lin_tianji_multi_segment_yearly_claim_universe_v1`

This is a fresh Pilot-4 decision. Pilot-3's prior approval is not inherited. AGG-01 was explicitly approved by the human decision owner at `2026-09-28T21:41:06+08:00`; it has no start-authorization effect.

## Approved time scope

Timezone: `Asia/Taipei`.

Approved outcome window:

`2027-05-01T00:00:00+08:00` → `2027-06-30T23:59:59+08:00`

Maturity delay: 72 hours.

The approved window is the next non-overlapping future calendar-aligned same-year multi-month window after the closed Pilot-3 window. It was not selected from metaphysical output, snapshot counts, claim counts, or outcome information.

Window claim scope remains `yearly`; timing scope remains `monthly`.

## Evidence isolation

Rule selection may use only frozen general runtime semantics and architecture contracts.

Pilot-1/2/3 may establish process-defect classes. Their exposed case identities, snapshot counts, structural contents, EFA child inventories, claim sets, prediction material, and outcomes must not be used to tune ENUM-01 or AGG-01.

## Current gate

The enumeration rule was preregistered in public Git before any Pilot-4 case exposure.

The human decision owner explicitly approved Pilot-4 D01-D12, ENUM-01, AGG-01, and the proposed window at `2026-09-28T21:41:06+08:00`. A separate explicit Pilot-4 start authorization was granted at `2026-09-28T22:02:42+08:00`. Pilot-4 is now `AUTHORIZED_NOT_STARTED`.

The start authorization opens only the private source-census → intake → S1 → PCG preparation chain. Candidate case processing remains prohibited until every Pilot-4 PCG prerequisite is true and the public de-identified gate validates `READY`.

Real case-specific structural-snapshot enumeration, EFA materialization, claim-universe locking, downstream compatibility, and prediction locking remain downstream of PCG READY and their declared gates.

No merge, tag, Release, Stable promotion, or publication authority is created by Pilot-4 start authorization.
