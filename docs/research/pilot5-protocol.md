# Prospective Pilot-5 protocol — preregistered, not approved

**Protocol decision status:** `PENDING_ITEM_APPROVAL`  
**Enumeration decision:** `ENUM-01 PENDING`  
**Aggregation decision:** `AGG-01 PENDING`  
**Downstream authority decision:** `AUTH-01 PENDING`  
**Pilot status:** `NOT_STARTED`  
**Start authorization:** `NOT_AUTHORIZED`  
**Candidate case processing:** `PROHIBITED`

Pilot-5 is a new pilot/protocol version. It inherits no Pilot-1/2/3/4 approval, start authorization, case identity, exposure state, private snapshot observation, EFA census, claim lock, prediction, outcome or qualification state.

## Purpose

Pilot-5 preregisters the complete multi-segment path before any case exposure:

1. ENUM-01 complete deterministic window→structural-snapshot census;
2. AGG-01 complete-union yearly claim membership;
3. AUTH-01 segment-aware full-window downstream authority without source synthesis;
4. exact bridge from AUTH-01 to the existing prospective forecast lock.

Normative AUTH-01 document:

`docs/research/pilot5-segment-aware-downstream-authority-preregistration.md`

## Proposed sequence

```text
D01-D12 + ENUM-01 + AGG-01 + AUTH-01 human approval
→ separate final seal / start authorization
→ private source census
→ private intake registry
→ schema-valid S1 source manifest
→ PCG READY
→ fresh Pilot-5 candidate exposure
→ deterministic complete window→snapshot enumeration
→ one pre-EFA structural state per enumerated segment
→ freeze exact ordered snapshot manifest
→ one complete yearly EFA inventory per segment
→ AGG-01 complete-union claim-universe lock
→ exact S1 membership validation
→ independently materialize complete single-source downstream chain per segment
→ AUTH-01 unanimous stable render-unit window authority
→ exact prediction-lock eligibility bridge
→ prediction lock containing all and only eligible claims
→ wait for outcome window + maturity
→ blind adjudication
→ process analysis
```

Any failed gate halts Pilot-5. No replacement case is allowed under the same protocol after exposure.

## Proposed time scope

Timezone: `Asia/Taipei`.

Proposed outcome window:

`2027-07-01T00:00:00+08:00` → `2027-08-31T23:59:59+08:00`

Maturity delay: 72 hours.

Selection basis: the next non-overlapping future calendar-aligned same-year multi-month window after Pilot-4 only. No metaphysical output or Pilot-1/2/3/4 private case observation is used.

Claim scope remains yearly; timing scope remains monthly; requested dynamic scopes remain exactly yearly + monthly.

## Current gate

No Pilot-5 decision is approved. No start authorization exists. No real Pilot-5 source census, intake, S1, candidate case exposure, case-specific enumeration, EFA, downstream authority or prediction work is authorized.

Merge, tag, Release, Stable promotion and publish remain unauthorized.
