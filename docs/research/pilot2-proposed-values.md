# Pilot-2 proposed approval values

Status: **PROPOSED_READY_FOR_HUMAN_APPROVAL**  
Protocol decisions: `PENDING_ITEM_APPROVAL`  
Pilot: `NOT_STARTED`

Pilot-2 carries forward the parts of Pilot-1 that were not implicated in the
failure, but it is a new protocol and requires fresh human approval.

| ID | Proposed Pilot-2 value | Material delta from Pilot-1 |
| --- | --- | --- |
| D01 | Same self-pilot role model; prediction and outcome/adjudication contexts remain information-separated. | No material change. |
| D02 | Owner-only data; private raw material outside public Git; approved private storage/access record required before start. | No material change. |
| D03 | One consenting study owner, **one new future case/window packet**, no replacement. Eligibility additionally requires formal intake + S1 source manifest frozen before candidate processing. | Adds sequencing prerequisite learned from Pilot-1. |
| D04 | `future_forecast`; complete deterministic EFA child inventory only; no cherry-picking/free-text addition. S1 exact-match claim-universe validation occurs only after pre-candidate gate READY. | Explicitly separates source eligibility lock from later claim-universe generation. |
| D05 | Single candidate arm; no superiority claim. Exact candidate/package/manifest/protocol bindings occur at separate Pilot-2 start authorization. | Fresh Pilot-2 seal required; Pilot-1 seal is not inherited. |
| D06 | `Asia/Taipei`; proposed window `2027-01-01T00:00:00+08:00` → `2027-02-28T23:59:59+08:00`; 72-hour maturity delay. | New non-overlapping future case/window; Pilot-1 Nov-Dec window prohibited. |
| D07 | `SUPPORTED / CONTRADICTED / INDETERMINATE / OUT_OF_UNIVERSE`; same evidence hierarchy; no favorable reinterpretation. | No material change. |
| D08 | Prediction context cannot access outcomes; outcome collection remains prediction-blind; adjudication after outcome seal. | Adds rule that no prediction context may exist before pre-candidate gate READY. |
| D09 | Primary success = complete process conformance; secondary = provenance/outcome/adjudication completeness and deviations. Hit rate is descriptive only, not success criterion. | Adds explicit pre-candidate gate conformance as a primary requirement. |
| D10 | Exactly one new real case; no replacement; no result-dependent stop. Failure at pre-candidate gate halts Pilot-2. | Same stopping rule, now applied earlier. |
| D11 | Append-only deviations; no retrospective repair of intake/S1 timestamps or exposure status. | Explicitly forbids backfilling the Pilot-1 sequencing gap. |
| D12 | Public output limited to de-identified process summary; no claim/outcome-level disclosure for n=1. | No material change. |

## Additional Pilot-2 sequencing decision

Pilot-2 adds one mandatory governance invariant outside the twelve substantive
study decisions:

**PCG-01 — Pre-Candidate Gate**

`candidate_case_processing_allowed` may become true only when protocol
approval, start authorization, private source census, validated intake,
schema-valid S1 source manifest, and UNEXPOSED exposure evidence are all sealed
in the correct chronological order.

PCG-01 has no human bypass. If it fails, Pilot-2 halts before candidate case
processing.

Approval of D01-D12 should also explicitly approve PCG-01.
