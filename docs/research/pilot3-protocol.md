# Prospective Pilot-3 protocol — human-approved decisions pending start seal

**Protocol decision status:** `ALL_ITEMS_APPROVED`  
**Aggregation decision:** `AGG-01 APPROVED`  
**Pilot status:** `READY_FOR_START_AUTHORIZATION`  
**Start authorization:** `NOT_AUTHORIZED`  
**Candidate case processing:** `PROHIBITED`

Pilot-3 is a new pilot ID and protocol version. It does not inherit Pilot-1 or Pilot-2 approval, start authorization, case identity, exposure state, claim-universe lock, prediction state, or qualification state.

The human decision owner explicitly approved Pilot-3 D01-D12 and AGG-01 at `2026-09-28T13:57:00+08:00`. This approval does **not** authorize Pilot-3 start.

## Purpose

Pilot-3 remains a single-subject, single-arm prospective **workflow feasibility** pilot. Its new purpose is to verify that a multi-segment yearly window can freeze a complete deterministic yearly claim universe without retrospective rule invention.

The approved sequence is:

```text
D01-D12 + AGG-01 human approval
→ final seal / separate start authorization
→ private source census
→ private intake registry
→ schema-valid S1 source manifest
→ PCG READY
→ fresh candidate case exposure
→ freeze ordered structural-snapshot manifest
→ materialize one complete yearly EFA inventory per manifested snapshot
→ complete-union yearly claim-universe lock
→ exact S1 membership validation
→ segment-aware downstream authority compatibility gate
→ prediction lock
→ wait for window + maturity
→ blind adjudication
→ process analysis
```

Any failed gate halts the pilot. No failed Pilot-3 case may be replaced under the same protocol.

## New case and exposure rule

Pilot-3 requires a fresh future case/window packet. Renaming an old case, branch, digest, or registry record does not erase prior exposure.

The existing PCG-01 no-bypass sequencing principle remains mandatory: private census first; intake must be `ELIGIBLE_FOR_S1_SOURCE`; schema-valid S1 source manifest must be frozen before candidate processing; exposure must be `UNEXPOSED`; a de-identified PCG receipt must be READY; only then may the candidate inspect the fresh case.

## Approved time scope

Timezone: `Asia/Taipei`.

Approved outcome window:

`2027-03-01T00:00:00+08:00` → `2027-04-30T23:59:59+08:00`

Maturity delay: 72 hours.

This window was selected only because it is a new, future, calendar-aligned, same-civil-year, multi-month window after the Pilot-2 window. It was not selected from metaphysical output, claim counts, or Pilot-2 claim-set contents.

Window claim scope remains `yearly`; timing scope remains `monthly`.

The approved public window policy is `docs/research/pilot3-window-policy.v1.json`.

## AGG-01 mandatory contract

Pilot-3 AGG-01 is approved as:

`complete_union_of_all_manifested_efa_child_inventories`

Profile:

`lin_tianji_multi_segment_yearly_claim_universe_v1`

The normative design is `docs/research/pilot3-yearly-claim-universe-aggregation-preregistration.md`.

AGG-01 is mandatory, has no manual override, and has no start-authorization effect. The rule may not be changed after Pilot-3 case exposure. A change requires a new pilot ID/protocol version.

## Downstream compatibility gate

The aggregate universe preserves multiple source EFA authorities. Existing single-source research arm-freeze semantics must not be treated as compatible by assumption.

Before prediction lock, the downstream path must prove it can preserve aggregate membership and source provenance without silently selecting one snapshot or synthesizing a new EFA authority. If that proof is absent, Pilot-3 halts before prediction lock.

## Privacy boundary

Real case identifiers, birth data, source records, snapshot IDs/digests, EFA claim IDs, prediction text, outcome text, and private timestamps remain outside public Git.

Public Git may contain only protocol/governance text, empty/de-identified templates, synthetic tests, aggregate gate state, and process-level deviations.

## Current gate

Pilot-3 D01-D12 and AGG-01 are approved, but Pilot-3 is **not started**.

A separate final seal / start authorization is still required. Until that authorization exists, no private Pilot-3 source census, intake, S1 source manifest, PCG receipt, candidate processing, snapshot manifest, claim-universe lock, prediction lock, outcome collection, adjudication, or scoring is authorized.

The next human gate is the separate Pilot-3 final seal / start authorization.
