# Prospective Pilot-6 protocol — human-approved decisions pending start seal

**Protocol decision status:** `ALL_ITEMS_APPROVED`  
**Enumeration decision:** `ENUM-01 APPROVED`  
**Canonical manifest decision:** `MANIFEST-01 APPROVED`  
**Aggregation decision:** `AGG-01 APPROVED`  
**Downstream authority decision:** `AUTH-01 APPROVED`  
**Pilot status:** `READY_FOR_START_AUTHORIZATION`  
**Start authorization:** `NOT_AUTHORIZED`  
**Candidate case processing:** `PROHIBITED`

Pilot-6 is a new pilot/protocol version. It does not resume or repair Pilot-5 and inherits no prior pilot approval, start authorization, case identity, exposure state, private snapshot observation, EFA census, claim set, prediction, outcome or qualification state.

## Purpose

Pilot-6 preserves the already-preregistered ENUM-01, AGG-01 and AUTH-01 semantics, while adding the missing process gate exposed by the public Pilot-5 halt:

1. ENUM-01 creates the deterministic complete window→structural-snapshot census;
2. one frozen-candidate structural state is materialized for every enumerated segment;
3. **MANIFEST-01** must use the existing canonical helper/schema to materialize the exact ordered snapshot manifest;
4. MANIFEST-01 must validate the exact canonical manifest and digest while EFA execution is still `NOT_STARTED`;
5. only a `READY_FOR_EFA` MANIFEST-01 receipt permits any EFA execution;
6. AGG-01 remains complete-union membership only;
7. AUTH-01 remains unanimous segment-aware authority with no source synthesis;
8. the existing Pilot-5 prediction bridge remains unchanged.

Pilot-5 private snapshot count/content, EFA child count/content, claim contents and outcomes are not used to choose Pilot-6 rules.

## Proposed sequence

```text
D01-D12 + ENUM-01 + MANIFEST-01 + AGG-01 + AUTH-01 human approval
→ separate final seal / start authorization
→ private source census
→ private intake registry
→ schema-valid S1 source manifest
→ PCG READY
→ fresh Pilot-6 candidate exposure
→ deterministic complete window→snapshot enumeration
→ one pre-EFA structural state per enumerated segment
→ MANIFEST-01 canonical helper materialization
→ MANIFEST-01 exact schema/digest validation
→ freeze pre-EFA MANIFEST-01 READY receipt
→ only then permit one complete yearly EFA inventory per segment
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

Any failed gate halts Pilot-6. No replacement case is allowed under the same protocol after exposure.

## MANIFEST-01 hard boundary

The canonical manifest authority is the existing repository contract:

- builder: `tools.pilot4_structural_snapshot_enumerator.build_snapshot_manifest_from_enumeration`
- canonical manifest schema/builder: `tools.pilot3_yearly_claim_universe.build_yearly_segment_snapshot_manifest`

MANIFEST-01 requires exact byte-equivalent canonical JSON semantics, including the canonical schema/profile, window-policy digest, ordered snapshot rows, promotion=false and recomputed `snapshot_manifest_digest`.

The MANIFEST-01 gate must fail closed if:

- the supplied manifest differs from the canonical helper result;
- a required field is missing or an unknown field is present;
- snapshot order, identity or structural-state digest differs;
- the digest does not recompute;
- EFA execution has already started;
- claim/EFA/outcome content is injected into the pre-EFA manifest path.

A post-EFA repair cannot become pre-EFA authority.

## Proposed time scope

Timezone: `Asia/Taipei`.

Proposed outcome window:

`2027-09-01T00:00:00+08:00` → `2027-10-31T23:59:59+08:00`

Maturity delay: 72 hours.

Selection basis: the next non-overlapping future calendar-aligned same-year two-month window after Pilot-5. No prior-pilot private metaphysical output, snapshot count/content, EFA count/content, claim content, prediction or outcome observation is used.

Claim scope remains yearly; timing scope remains monthly; requested dynamic scopes remain exactly yearly + monthly.

## Current gate

The human decision owner explicitly approved Pilot-6 D01-D12, ENUM-01, MANIFEST-01, AGG-01, AUTH-01 and the proposed window at `2026-09-29T12:39:46+08:00`. Pilot-6 is now `READY_FOR_START_AUTHORIZATION`.

This approval has no start effect. Until a separate final seal / start authorization exists, no private Pilot-6 source census, intake, S1 source manifest, PCG receipt, real case exposure, case-specific enumeration, MANIFEST-01 execution, EFA, aggregation, downstream authority or prediction work is authorized.

Merge, tag, Release, Stable promotion and publish remain unauthorized.
