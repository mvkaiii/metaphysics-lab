# Pilot-4｜Complete window → structural snapshot enumeration preregistration

Status: **APPROVED_BY_HUMAN_DECISION_OWNER**  
Pilot ID: **Pilot-4**  
Preregistered at: `2026-09-28T20:07:32+08:00`  
Enumeration profile: `lin_tianji_complete_structural_snapshot_enumerator_v1`  
Enumeration rule: `complete_union_of_authoritative_yearly_monthly_time_boundaries_no_post_exposure_merge`  
Candidate case exposure: **PROHIBITED UNTIL SEPARATE START AUTHORIZATION + PCG READY**

## 1. Why Pilot-4 exists

Pilot-3 halted fail-closed at `STRUCTURAL_SNAPSHOT_MANIFEST` because the frozen protocol had not defined a deterministic complete window→snapshot enumerator before candidate exposure.

Pilot-4 is a new pilot ID/protocol. It does not repair or resume Pilot-3 and does not reuse its exposed case.

The only Pilot-3 information used here is the process-defect class: **the enumerator was missing**. No Pilot-3 snapshot count, snapshot identities, structural-state contents, EFA contents, claim counts, claim identities, rankings, predictions, or outcomes are inputs to this rule.

## 2. Frozen analysis scope

The Pilot-4 enumeration contract is limited to the existing prospective research scope:

- timezone: `Asia/Taipei`
- one civil year
- window claim scope: `yearly`
- timing scope: `monthly`
- dynamic requested scopes: exactly `["yearly", "monthly"]`
- Bazi current decadal context remains part of structural interpretation because the existing interpreter includes it even when the requested dynamic scopes are yearly/monthly.

Changing any of these assumptions requires a new enumeration profile/protocol version.

## 3. Complete authoritative boundary union

For a frozen window and frozen normalized natal basis, construct one ordered boundary set from **all** of the following sources.

### 3.1 Window fenceposts

The exact approved window start and end are immutable fenceposts.

### 3.2 Bazi Jie boundaries

For every Project Bazi `JIE` crossing that falls inside the window, include the exact `solar_term_time(...)` timestamp.

This captures the Project Bazi flow-year / flow-month transitions, including `立春`.

### 3.3 Bazi qualification-status boundaries

The current Project Bazi calendar marks targets within ±15 minutes of the nearest Jie boundary as `needs_external_verification`.

Therefore include:

- Jie time − 15 minutes;
- exact Jie time;
- Jie time + 15 minutes.

The exact term remains a separate boundary because the flow pillar may change inside the caution interval.

### 3.4 Stored Bazi decadal boundaries

Include every stored Project Bazi decadal `start_datetime` and `end_datetime` falling inside the window.

These values come only from the frozen normalized natal deterministic facts. The enumerator does not recalculate or choose a decadal period.

### 3.5 Ziwei yearly/monthly calendar-source changes

Ziwei monthly and yearly sources change on the neutral Calendar Resolver's local-civil-date basis.

For every local civil midnight inside the window:

1. resolve the previous and current civil dates with the Project Calendar Resolver;
2. resolve the canonical Ziwei month source;
3. compare the tuple:
   - lunar year;
   - monthly reference;
   - monthly stem;
   - monthly branch;
   - calendar validation status;
4. include that midnight only if the tuple changed.

This deterministically covers:

- ordinary lunar-month rollover;
- lunar-year rollover;
- leap-month source changes including the Project day-16 split;
- calendar `boundary_caution` / validation-state transitions.

It does not use a case outcome or EFA result to decide whether a midnight is kept.

## 4. Segment and representative rule

Sort and de-duplicate the boundary timestamps.

The interval between each adjacent pair of fenceposts is one mandatory segment. A segment's canonical representative is the UTC midpoint converted back to `Asia/Taipei`.

Important:

- segment boundaries are fixed **before EFA**;
- no segment may be deleted because a later structural digest matches its neighbor;
- no adjacent segments may be merged after case exposure;
- no segment may be split from EFA/claim observations;
- every enumerated segment must produce exactly one snapshot row before EFA aggregation.

The midpoint is used only to materialize a deterministic structural context away from exact boundary ambiguity. It does not redefine the approved outcome-window endpoint semantics.

## 5. Pre-EFA manifest binding

The public research implementation is:

`tools/pilot4_structural_snapshot_enumerator.py`

The private enumeration contains segment times and snapshot IDs and remains outside public Git.

After the frozen candidate materializes one pre-EFA structural state per canonical representative, exactly one structural-state digest must be supplied for every enumerated segment. The helper then builds the existing complete ordered yearly segment snapshot manifest.

A missing, extra, reordered, merged, duplicated, or manually substituted segment fails closed.

## 6. Aggregation after enumeration

Pilot-4 proposes to reuse the same general complete-census aggregation semantics:

`complete_union_of_all_manifested_efa_child_inventories`

This is a **fresh Pilot-4 AGG-01 decision** and is not inherited as approved from Pilot-3. Pilot-4 ENUM-01 and AGG-01 were explicitly approved by the human decision owner at `2026-09-28T21:41:06+08:00`.

Enumeration decides **which segments exist**. AGG-01 decides **how complete EFA membership across those segments is combined**. Neither rule may use EFA child counts/content to modify the other.

## 7. Privacy and exposure boundary

Before fresh Pilot-4 human approvals and a separate start authorization:

- no real Pilot-4 source census;
- no intake;
- no S1 manifest;
- no PCG READY;
- no candidate case exposure;
- no real segment enumeration using private natal facts;
- no EFA materialization;
- no claim lock or prediction lock.

Public Git contains only the rule, validator implementation, synthetic/public-calendar tests, and de-identified governance state.

## 8. Fail-closed conditions

Execution stops if:

- timezone/scope/window class differs from the frozen profile;
- calendar resolution is unavailable;
- Bazi decadal periods are absent, malformed, or overlapping;
- segment order/census is inconsistent;
- structural-state digest count differs from the enumerated segment count;
- any post-exposure merge/split/substitution is attempted;
- any EFA/claim/outcome observation is used to alter the snapshot census.

There is no manual override.


## 9. Human approval checkpoint

Pilot-4 D01-D12, ENUM-01, AGG-01, and the proposed window were explicitly approved by the human decision owner at `2026-09-28T21:41:06+08:00`.

This approval does **not** authorize Pilot-4 start. The next human gate is the separate final seal / start authorization. No private source census, intake, S1, PCG, real case-specific enumeration, candidate exposure, EFA, claim lock, prediction, or outcome workflow may begin before that separate authorization.
