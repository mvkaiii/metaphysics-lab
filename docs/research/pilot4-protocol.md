# Prospective Pilot-4 protocol — enumeration preregistered, human decisions pending

**Protocol decision status:** `PENDING_ITEM_APPROVAL`  
**Enumeration decision:** `ENUM-01 PENDING`  
**Aggregation decision:** `AGG-01 PENDING`  
**Pilot status:** `NOT_STARTED`  
**Start authorization:** `NOT_AUTHORIZED`  
**Candidate case exposure:** `PROHIBITED`

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

Proposed profile:

`lin_tianji_complete_structural_snapshot_enumerator_v1`

Proposed rule:

`complete_union_of_authoritative_yearly_monthly_time_boundaries_no_post_exposure_merge`

Normative preregistration:

`docs/research/pilot4-structural-snapshot-enumeration-preregistration.md`

ENUM-01 is mandatory, has no manual override, and must be approved before start authorization. Its actual case-specific enumeration is prohibited before PCG READY.

## AGG-01

Pilot-4 separately proposes:

`complete_union_of_all_manifested_efa_child_inventories`

Profile:

`lin_tianji_multi_segment_yearly_claim_universe_v1`

This is a fresh Pilot-4 decision. Pilot-3's prior approval is not inherited.

## Proposed time scope

Timezone: `Asia/Taipei`.

Proposed new outcome window:

`2027-05-01T00:00:00+08:00` → `2027-06-30T23:59:59+08:00`

Maturity delay: 72 hours.

The proposal is the next non-overlapping future calendar-aligned same-year multi-month window after the closed Pilot-3 window. It is not selected from metaphysical output, snapshot counts, claim counts, or outcome information.

Window claim scope remains `yearly`; timing scope remains `monthly`.

## Evidence isolation

Rule selection may use only frozen general runtime semantics and architecture contracts.

Pilot-1/2/3 may establish process-defect classes. Their exposed case identities, snapshot counts, structural contents, EFA child inventories, claim sets, prediction material, and outcomes must not be used to tune ENUM-01 or AGG-01.

## Current gate

The enumeration rule is preregistered in public Git before any Pilot-4 case exposure.

D01-D12, ENUM-01, AGG-01, the proposed window, and a separate start authorization still require explicit human decisions. Until those gates are complete, no private Pilot-4 census/intake/S1 work or real candidate processing is authorized.

No merge, tag, Release, Stable promotion, or publication authority is created by this preregistration.
