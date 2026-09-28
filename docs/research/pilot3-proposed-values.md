# Prospective Pilot-3 proposed approval values

Status: **PROPOSED_READY_FOR_HUMAN_APPROVAL**  
Protocol decisions: `PENDING_ITEM_APPROVAL`  
Pilot: `NOT_STARTED`

These values are a new Pilot-3 proposal. Nothing is inherited as an approval from Pilot-1 or Pilot-2.

## D01-D12 proposal

| ID | Proposed approval value | Start-time binding / limitation |
|---|---|---|
| D01 | Study owner and data subject are the same consenting human. Prediction execution and outcome adjudication use separate information contexts. | Public repo records roles only. Self-pilot cannot establish population-level efficacy. |
| D02 | Pilot-3 uses only the study owner's own data. Raw source, prediction, snapshot and outcome material stays in approved private storage. | Exact private location/access is bound before start; retention/withdrawal follows prospective governance. |
| D03 | Exactly one fresh future case/window packet; no replacement case after a failed gate. | Eligibility requires frozen census, valid intake, S1 source manifest and PCG READY before exposure. |
| D04 | Claim identity is the complete Pilot-3 multi-segment yearly universe defined by AGG-01. The ordered structural-snapshot manifest is frozen before EFA aggregation; every manifested snapshot contributes its complete EFA inventory. | No manual claim selection, intersection filtering, fixed reference snapshot substitution, or post-exposure aggregation-rule change. |
| D05 | Single candidate arm only. Exact candidate commit/package/manifest/profile versions are bound by a later start seal. | Any candidate/config change after authorization requires a new authorization or protocol version; no superiority claim. |
| D06 | Timezone `Asia/Taipei`. Proposed window `2027-03-01T00:00:00+08:00` through `2027-04-30T23:59:59+08:00`, plus 72-hour maturity. | Chosen as the next non-overlapping future calendar-aligned window, not from metaphysical output or Pilot-2 child-set data. |
| D07 | Outcome labels remain `SUPPORTED`, `CONTRADICTED`, `INDETERMINATE`, `OUT_OF_UNIVERSE`; evidence hierarchy remains predeclared and adjudication is blind until sealing. | No favorable reinterpretation or post-hoc family remapping. |
| D08 | Prediction execution cannot read outcome material; sealed prediction content is not shown before the outcome bundle is frozen. | Premature disclosure or contamination is a material deviation. |
| D09 | Primary success criterion is process conformance: valid PCG, pre-EFA snapshot manifest, complete per-snapshot EFA census, deterministic aggregate lock, exact S1 membership, compatible downstream provenance and valid pre-window prediction lock. | Predictive match/support rate is not the Pilot-3 success metric. |
| D10 | Fixed sample/stopping: exactly one planned real case. No replacement after failure. | Any aggregation/provenance/prediction-lock failure halts Pilot-3; retry requires a new pilot ID/version. |
| D11 | Withdrawal stops future collection. Missing, contradictory, indeterminate and deviation records are append-only and not silently deleted or rewritten. | Material integrity deviations can make the pilot non-qualifying. |
| D12 | Public disclosure is limited to protocol/governance artifacts and de-identified process status. | No claim IDs, snapshot IDs/digests, raw predictions/outcomes, birth data or private timestamps are published. |

## AGG-01 proposal

Proposed decision:

```text
APPROVE
profile = lin_tianji_multi_segment_yearly_claim_universe_v1
rule    = complete_union_of_all_manifested_efa_child_inventories
```

Selection basis: general Complete-Census semantics and existing authority boundaries only.

Explicit exclusion: Pilot-2 observed claim counts, union/intersection cardinalities, claim contents, and outcome information are not used to choose AGG-01.

Normative specification:

`docs/research/pilot3-yearly-claim-universe-aggregation-preregistration.md`

## Approval boundary

Human approval of D01-D12 and AGG-01 moves Pilot-3 only to `READY_FOR_START_AUTHORIZATION`.

A separate final seal/start authorization must later bind exact candidate commit, candidate package SHA256, capability manifest SHA256, final Pilot-3 protocol SHA256, window-policy SHA256, aggregation profile/rule identity, and the approved private storage/access record.

Until both human approval and later start authorization exist, no real Pilot-3 case may enter candidate processing.
