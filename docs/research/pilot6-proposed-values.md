# Pilot-6 proposed values

Status: **PENDING HUMAN APPROVAL**  
Preregistered at: `2026-09-29T12:27:00+08:00`

Pilot-6 is a fresh protocol. No prior pilot approval, case identity or exposure state is inherited.

## Governance

- D01-D12: all PENDING.
- ENUM-01: PENDING.
- MANIFEST-01: PENDING.
- AGG-01: PENDING.
- AUTH-01: PENDING.
- Manual override: prohibited.
- Promotion effect: none.
- Start authorization: NOT_AUTHORIZED.
- Candidate processing: prohibited until a later separate start authorization + PCG READY.

## Proposed window

- timezone: `Asia/Taipei`
- start: `2027-09-01T00:00:00+08:00`
- end: `2027-10-31T23:59:59+08:00`
- maturity delay: 72 hours
- claim scope: yearly
- timing scope: monthly
- requested dynamic scopes: yearly + monthly
- selection basis: `NEXT_NON_OVERLAPPING_FUTURE_CALENDAR_WINDOW_ONLY`

No prior-pilot private snapshot, EFA, claim, prediction or outcome observation is used.

## ENUM-01 proposed value

Profile: `lin_tianji_complete_structural_snapshot_enumerator_v1`

Rule: `complete_union_of_authoritative_yearly_monthly_time_boundaries_no_post_exposure_merge`

Fresh Pilot-6 approval is required.

## MANIFEST-01 proposed value

Profile: `lin_tianji_canonical_pre_efa_snapshot_manifest_gate_v1`

Rule: `canonical_helper_materialize_exact_schema_validate_digest_before_any_efa`

The exact canonical manifest must be materialized and validated before any EFA execution. A later repair cannot be backdated into pre-EFA authority.

## AGG-01 proposed value

Profile: `lin_tianji_multi_segment_yearly_claim_universe_v1`

Rule: `complete_union_of_all_manifested_efa_child_inventories`

Membership only; no authority synthesis. Fresh Pilot-6 approval is required.

## AUTH-01 proposed value

Profile: `lin_tianji_segment_aware_window_authority_v1`

Rule: `unanimous_stable_render_unit_across_all_manifested_segments_no_authority_synthesis`

Prediction bridge:

`full_window_single_child_exact_identity_all_eligible_claims_no_confidence_uplift`

No best-snapshot selection, voting, repetition uplift or synthetic single-source authority.
