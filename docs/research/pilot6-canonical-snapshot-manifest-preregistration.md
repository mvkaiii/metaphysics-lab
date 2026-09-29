# Pilot-6 MANIFEST-01 preregistration

Preregistered at: `2026-09-29T12:27:00+08:00`  
Status: **PENDING HUMAN APPROVAL**

## Defect class addressed

Pilot-5 publicly halted because structural snapshot rows had been frozen before EFA, but the authoritative manifest serialization had not itself been materialized and validated under the existing canonical schema before EFA began.

Pilot-6 addresses only this public process/gate defect class. Pilot-5 private snapshot cardinality/content, EFA cardinality/content and claim contents are not used.

## Frozen proposed contract

Profile:

`lin_tianji_canonical_pre_efa_snapshot_manifest_gate_v1`

Rule:

`canonical_helper_materialize_exact_schema_validate_digest_before_any_efa`

Canonical builder:

`tools.pilot4_structural_snapshot_enumerator.build_snapshot_manifest_from_enumeration`

Canonical manifest contract:

`tools.pilot3_yearly_claim_universe.build_yearly_segment_snapshot_manifest`

## Required ordering

1. ENUM-01 is complete.
2. Every enumerated segment has exactly one pre-EFA structural-state digest.
3. Build the manifest only through the canonical helper.
4. Recompute and validate exact canonical equality/digest.
5. Record a MANIFEST-01 `READY_FOR_EFA` receipt while `efa_execution_started=false`.
6. Only then may any EFA function execute.

## Fail-closed conditions

Any of the following halts the pilot before EFA:

- missing/extra manifest field;
- wrong schema or profile;
- non-canonical snapshot order;
- missing/duplicate snapshot identity;
- structural-state digest mismatch;
- window-policy digest mismatch;
- manifest digest mismatch;
- supplied manifest differs from canonical helper output;
- EFA execution already started;
- any claim/EFA/outcome material appears in the manifest path.

No manual override. No retrospective repair. No promotion effect.
