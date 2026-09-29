# v1.8 next candidate verification checklist

狀態：**ENGINEERING CANDIDATE VERIFIED / READY FOR HUMAN REVIEW**  
Release authority：**NOT GRANTED**  
Merge authority：**NOT GRANTED**

本文件是 Task 10 的 verification-before-completion 清單。它記錄工程候選的驗證要求與目前證據，不是 Release note、Stable promotion decision、sandbox prediction evidence 或 research qualification PASS。

> Git commit 不能在自身內容中可靠地綁定自己的最終 SHA。本文件因此記錄「建立本清單前最後一個 code-bearing candidate」；本文件提交後的 exact PR HEAD 與 hosted run IDs 以 Draft PR #233 的 current metadata / body 為 authority，並必須 fresh verify。

## Candidate lineage

- Repository：`mvkaiii/metaphysics-lab`
- Working branch：`local/task0-2-capability-matrix`
- Base / formal main：`872c60b2e959ea48d25524b74686e488f576ec6f`
- Last code-bearing candidate before this checklist update：`b174bc79e57ac87f9c7750b4bfd7c0d0862cb9b2`
- PR：#233（Draft）
- Candidate User Package content SHA256：`cb175e2d482fe9ca8e2d46d6c55c4b0237f1cbb9a631e0d3c50aef75f8e1e0c4`
- Candidate package 不是正式 v1.7.1 asset，不得覆寫歷史 Release。

## Scope review

- [x] Capability evidence matrix / source snapshot / evidence index
- [x] Bazi decadal structural qualification packet
- [x] Visualization Chart Contract v1
- [x] Bazi decadal pure projection
- [x] Deterministic SVG / text renderer and CLI
- [x] Version-neutral read-only artifact inventory / lifecycle policy
- [x] v1.7 historical planning archive
- [x] Prospective pilot protocol / human review form（design only）
- [x] Sealed Bazi decadal reference comparison harness（engineering only; no oracle expected values）
- [x] Independent-oracle handoff boundary and HKO astronomical-source role documented
- [x] Prospective pilot public decision-receipt template / validator
- [x] D01–D12 approval gate separated from explicit pilot-start authorization
- [x] Windows vendor tree digest portability fix
- [x] Visualization authority coverage and multi-output preflight hardening
- [x] JSON Schema / semantic validator structural parity
- [x] No Case Schema migration
- [x] No selector / interpretation default promotion
- [x] No Stable promotion
- [x] No metaphysics algorithm change
- [x] No research raw data / real pilot outcomes committed

## Visualization contract review

- [x] Ready / unsupported discriminated status
- [x] `[start_at,end_at)` visualization interval convention
- [x] `continuous_years_from_jie_interval` age basis
- [x] Period semantic fields require `authority_refs`
- [x] Non-null optional `ten_god / elements` require authority
- [x] Missing optional source remains `null + machine-readable reason`
- [x] Blind contamination fails closed
- [x] Experimental limitation badge cannot be silently removed
- [x] Renderer does not recalculate Bazi / Ziwei / calendar algorithms
- [x] SVG rejects script / external href injection
- [x] CLI refuses existing output without explicit overwrite
- [x] Multi-output CLI preflights all targets before first write
- [x] Chart v1 annotations fail closed as empty until a supported producer + renderer exists
- [x] Chart v1 year overlays fail closed as empty until a supported producer + renderer exists
- [x] JSON Schema structural definitions cover age basis, time basis, period, authority refs, optional reasons and annotation shape
- [x] Cross-field / provenance / authority semantics remain Python validator responsibility

## Portability review

- [x] Vendor tree digest ordering uses relative POSIX path strings
- [x] No casefold
- [x] Vendor payload bytes are not normalized
- [x] Existing vendor manifest expected digests unchanged
- [x] lunar-python and tzdata verified separately
- [x] Generated distribution carries only the materializer portability delta
- [x] No vendor / requirements / metaphysics algorithm modification

## Hosted engineering verification

For the last code-bearing candidate `b174bc79e57ac87f9c7750b4bfd7c0d0862cb9b2`:

- [x] v1.5 Validation run `36305101236` — SUCCESS
- [x] v1.6 Validation run `36305101237` — SUCCESS
- [x] v1.7 Validation run `36305101234` — SUCCESS
- [x] v1.7 Plan 3 Focused run `36305101232` — SUCCESS
- [x] Full repository regression：1,389 tests PASS in all four hosted workflows
- [x] Python 3.9 workflow environment
- [x] release-surface verification PASS
- [x] deterministic candidate package verification PASS
- [x] legacy / prospective compatibility PASS
- [x] private outcome contamination scan PASS where defined by workflow
- [x] clean tree PASS in hosted workflow
- [x] hosted artifacts exist and are bound to the exact tested candidate

After this checklist is committed, the documentation-only descendant HEAD must receive its own hosted verification before it can replace the SHA above as the final PR review checkpoint.

## Formal release protection

- [x] Formal `main` remained `872c60b2e959ea48d25524b74686e488f576ec6f` at last fresh check
- [x] `v1.7.1` tag / Release target remained the same formal SHA
- [x] Formal v1.7.1 User Package SHA256 remained `771f8493cd07b298c7971f38c601ce17a8acfcce5dab43c72e245f7b282943e8`
- [x] Historical Release assets were not rebuilt or overwritten
- [x] Candidate artifact archive digests are not substituted for User Package content digest

## Evidence / research gates still open

### Task 3

Status：`NEEDS_EVIDENCE`

- [x] Comparator contract/harness fixed and hosted-tested; it cannot generate expected values or promote qualification
- [x] Independent-oracle information boundary documented
- [ ] Independent sealed oracle / reference comparison for the same Project age / endpoint profile
- [ ] External astronomical source bytes / version / digest sealed
- [ ] Case set and tolerance rules preregistered before comparison
- [ ] Independent implementation role separated from production / expected-output exposure
- [ ] Human review of resulting reference packet

Task 3 gap does not invalidate Experimental engineering delivery, but it blocks any claim of full independent qualification or maturity promotion.

### Task 9

Protocol decisions：`ALL_ITEMS_APPROVED`  
Pilot：`HALTED_NON_QUALIFYING`

Pilot-1 concrete proposed values are documented in
`docs/research/prospective-pilot-proposed-values.md` with status
`PROPOSED_READY_FOR_HUMAN_APPROVAL`. This proposal does not modify the public
decision receipt.

Fresh contract review supersedes the earlier conversational 7-day / 12-attempt
idea. The existing prospective-window research contract accepts only
calendar-aligned, same-civil-year, multi-month windows and maps them to yearly
claim authority with monthly timing. The current Pilot-1 proposal therefore uses
one real end-to-end case and proposes
`2026-11-01T00:00:00+08:00` through
`2026-12-31T23:59:59+08:00`. This timestamp convention belongs to that
research contract and is not relabeled as the Visualization `[start,end)`
contract.


- [x] D01 study owner / roles
- [x] D02 lawful data / consent / retention / withdrawal
- [x] D03 target population / eligibility / census
- [x] D04 claim universe
- [x] D05 arms / comparator
- [x] D06 time scope
- [x] D07 outcome definition
- [x] D08 blinding
- [x] D09 metrics
- [x] D10 sample / stopping
- [x] D11 withdrawal / deviation
- [x] D12 publication / privacy
- [x] Public decision receipt records D01–D12 all APPROVED by human decision owner
- [x] Validator enforces that ALL_ITEMS_APPROVED alone does not authorize pilot start
- [x] D01–D12 explicitly approved by human decision owner at `2026-09-27T17:55:00+08:00`
- [x] Protocol body synchronized with the approved D01–D12 receipt; stale PENDING language removed
- [x] Separate explicit human authorization granted at `2026-09-27T19:35:00+08:00`
- [x] Pilot-1 public start seal committed at `docs/research/pilot1-start-seal.v1.json`; private storage/access record verified outside public Git
- [x] Pilot-1 execution reached the S1 source-manifest gate and failed closed as `INELIGIBLE_PREVIOUSLY_EXPOSED`
- [x] Public de-identified execution checkpoint committed at `docs/research/pilot1-execution-checkpoint.v1.json`
- [x] Prediction lock remained `NOT_CREATED`; no outcome/adjudication/scoring/verified-event calibration occurred
- [x] D10 enforced: no replacement case under Pilot-1
- [x] Retry governance implemented as Pilot-2 with a new pilot ID/protocol and mandatory PCG-01 sequencing gate

D01–D12 approval and explicit pilot-start authorization were completed. During actual execution, Pilot-1 failed closed at the S1 source-manifest gate: a private source-file census existed before candidate processing, but the schema-valid S1 source manifest had not been frozen before the case was processed by the candidate. Frozen-contract validation therefore classified the case as previously exposed and excluded it. No prediction lock, outcome collection, adjudication, scoring, verified-event calibration, qualification evidence, or promotion evidence was created. D10 prohibits a replacement case under Pilot-1.

### Pilot-2

Protocol decisions：`ALL_ITEMS_APPROVED`  
Pilot：`HALTED_NON_QUALIFYING`  
Pre-candidate gate：`READY_BEFORE_HALT`

Pilot-2 is a new pilot ID/protocol version created from the Pilot-1 process
failure. It does not inherit Pilot-1 approval, start authorization, eligibility,
case identity, or exposure status.

- [x] New Pilot-2 protocol committed at `docs/research/pilot2-protocol.md`
- [x] Fresh D01-D12 proposed values committed at `docs/research/pilot2-proposed-values.md`
- [x] Fresh all-PENDING decision receipt committed at `docs/research/pilot2-decision-receipt.template.json`
- [x] PCG-01 pre-candidate gate template committed and defaults BLOCKED
- [x] Pre-candidate gate validator / tests added
- [x] Pilot-1 failure shape cannot open Pilot-2 candidate processing
- [x] Later prerequisite cannot be true while an earlier sequencing prerequisite is false
- [x] Manual override prohibited
- [x] Private-material disclosure prohibited in public gate
- [x] Candidate/public digest bindings required once start authorization is bound
- [x] Proposed future window is new and non-overlapping: `2027-01-01T00:00:00+08:00` → `2027-02-28T23:59:59+08:00`
- [x] Human approval of Pilot-2 D01-D12 + PCG-01 at `2026-09-27T23:00:15+08:00`
- [x] PCG-01 recorded as mandatory/no-bypass in `docs/research/pilot2-pcg01-decision.v1.json`
- [x] Separate Pilot-2 start authorization / final seal granted at `2026-09-27T23:23:47+08:00`
- [x] Pilot-2 public start seal committed at `docs/research/pilot2-start-seal.v1.json`; private storage/access record verified outside public Git
- [x] Private source census for the new case frozen before candidate processing
- [x] Private intake registry validated as `ELIGIBLE_FOR_S1_SOURCE`
- [x] Schema-valid S1 source manifest frozen before any candidate case processing
- [x] Candidate exposure validated as `UNEXPOSED` before candidate processing
- [x] PCG-01 READY receipt committed before candidate reads the case
- [x] PCG-01 READY at `2026-09-27T23:36:22+08:00`; supporting evidence remains private under D12
- [x] Candidate processing began only after PCG-01 READY
- [x] Yearly-only claim-universe scan confirmed five structural snapshots each with 28 EFA children but non-identical child sets
- [x] No approved multi-snapshot selector / union / intersection rule exists in the frozen prospective contracts
- [x] Pilot-2 halted fail-closed at `CLAIM_UNIVERSE_LOCK` before any prediction lock
- [x] Public de-identified halt checkpoint committed at `docs/research/pilot2-execution-checkpoint.v1.json`
- [x] No outcome/adjudication/scoring evidence created
- [ ] Any retry requires a new pilot ID/protocol version with claim-universe reference/aggregation semantics preregistered before candidate processing

Pilot-2 is closed as `HALTED_NON_QUALIFYING`. PCG-01 sequencing succeeded, but the pilot stopped at `CLAIM_UNIVERSE_LOCK` because the frozen protocol had no preregistered deterministic rule for a yearly claim universe spanning multiple structural snapshots. Pilot-2 may not resume and may not receive a replacement case.

### Pilot-3

Protocol decisions：`ALL_ITEMS_APPROVED`  
Aggregation decision：`AGG-01 APPROVED`  
Pilot：`HALTED_NON_QUALIFYING`

Pilot-3 is a new pilot ID/protocol. It exists to resolve the multi-segment yearly claim-universe contract before any new candidate case exposure.

- [x] Current prospective-window / EFA / C2 / S1 exact-match contracts audited
- [x] Prior single-source window-scope / arm-freeze research boundary audited read-only
- [x] Deterministic alternatives compared without using Pilot-2 observed claim-set cardinalities or contents for rule selection
- [x] Proposed AGG-01 preregistered as complete set union across every manifested complete yearly EFA inventory
- [x] Synthetic TDD contract added for exact snapshot census, digest validation, union determinism and S1 exact match
- [x] Pilot-3 D01-D12 proposed values created
- [x] Pilot-3 all-PENDING public decision receipt created
- [x] Proposed new non-overlapping future window recorded
- [x] Human approval of Pilot-3 D01-D12 at `2026-09-28T13:57:00+08:00`
- [x] Human approval of AGG-01 at `2026-09-28T13:57:00+08:00`; no start-authorization effect
- [x] Final seal / separate start authorization at `2026-09-28T14:12:31+08:00`; frozen candidate `4b18d74b3e12ca3a1f0946a708099aaca155fd92`
- [x] Private census → intake → S1 source manifest → PCG READY at `2026-09-28T16:11:22+08:00`
- [x] Pilot-3 halted at `STRUCTURAL_SNAPSHOT_MANIFEST` with `STRUCTURAL_SNAPSHOT_SEGMENTATION_RULE_UNRESOLVED`; no retrospective segmentation rule invented after exposure
- [x] Fresh Pilot-3 candidate processing began only after PCG READY; frozen runtime candidate used
- [ ] Snapshot manifest → complete EFA census → aggregate claim-universe lock — **HALTED before manifest**: no preregistered deterministic complete window→snapshot enumerator
- [ ] Segment-aware downstream authority compatibility proven — not reached
- [ ] Prediction lock — not created

D01-D12, AGG-01, separate start authorization, private census/intake/S1, and PCG READY all completed in sequence. Candidate processing then began with the frozen runtime candidate. Pilot-3 halted fail-closed at `STRUCTURAL_SNAPSHOT_MANIFEST`: the approved contracts define yearly claim authority, monthly timing, and the manifest schema, but do not preregister a deterministic complete window-to-structural-snapshot enumeration rule. No snapshot manifest, EFA census, claim-universe lock, prediction lock, outcome collection, adjudication, or scoring was created.

## Final gate

Current engineering interpretation:

**READY FOR HUMAN REVIEW**

Not authorized by this status:

- merge to `main`
- Stable promotion
- Case migration
- selector / interpretation default change
- tag
- GitHub Release
- publish
- historical Release / asset mutation
- automatic outcome collection/adjudication/scoring without the approved sequence

Any new commit after the currently verified candidate invalidates reuse of its exact-SHA hosted evidence for the new HEAD; rerun and record fresh verification.


### Pilot-4

Protocol decisions：`ALL_ITEMS_APPROVED`  
Enumeration decision：`ENUM-01 APPROVED`  
Aggregation decision：`AGG-01 APPROVED`  
Pilot：`HALTED_NON_QUALIFYING`

Pilot-4 is a new pilot/protocol version created after Pilot-3 halted at the structural-snapshot-manifest gate. It does not resume or repair Pilot-3.

- [x] Pilot-3 halt retained as `HALTED_NON_QUALIFYING`; no replacement/resume under Pilot-3
- [x] Complete window→structural-snapshot defect class identified without using exposed snapshot/claim results
- [x] ENUM-01 rule preregistered before any Pilot-4 case exposure at `2026-09-28T20:07:32+08:00`
- [x] Research-only deterministic enumerator implemented at `tools/pilot4_structural_snapshot_enumerator.py`
- [x] Enumerator binds Bazi Jie, ±15-minute qualification transitions, stored Bazi decadal boundaries, and Ziwei local-midnight month/year source changes
- [x] No post-exposure segment merge/split/substitution permitted
- [x] Exact one structural-state digest required per enumerated segment before EFA
- [x] Fresh Pilot-4 D01–D12 receipt created with all decisions PENDING
- [x] Fresh Pilot-4 ENUM-01 decision created PENDING human approval
- [x] Fresh Pilot-4 AGG-01 decision created PENDING human approval; Pilot-3 approval not inherited
- [x] Proposed non-overlapping window: `2027-05-01T00:00:00+08:00` → `2027-06-30T23:59:59+08:00`
- [x] Human approval of Pilot-4 D01–D12 at `2026-09-28T21:41:06+08:00`
- [x] Human approval of ENUM-01 at `2026-09-28T21:41:06+08:00`
- [x] Human approval of AGG-01 at `2026-09-28T21:41:06+08:00`
- [x] Separate Pilot-4 final seal / start authorization at `2026-09-28T22:02:42+08:00`; frozen candidate `f94318651d065a3e677993fb6044518e31c7754c`
- [x] Private source census → intake → S1 → PCG READY at `2026-09-28T22:20:22+08:00`
- [x] Fresh Pilot-4 candidate exposure / processing began only after PCG READY; frozen candidate used
- [x] Deterministic segment enumeration → exact ordered snapshot manifest frozen before EFA
- [x] Complete yearly EFA census across every frozen snapshot
- [x] Complete-union claim-universe lock → exact S1 membership
- [x] Segment-aware downstream authority compatibility assessed — **FAILED_CLOSED**: frozen downstream requires single-source ranking/structural/EFA provenance and no preregistered multi-segment adapter exists
- [ ] Prediction lock — **NOT CREATED; Pilot-4 halted before prediction lock**

Pilot-4 D01–D12, ENUM-01, AGG-01 and separate start authorization are complete. Private source-census → intake → S1 preparation may proceed in order. Candidate case exposure/processing remains prohibited until PCG READY.


Pilot-4 halted fail-closed at `DOWNSTREAM_AUTHORITY_COMPATIBILITY` on `2026-09-29T08:25:30+08:00`. ENUM-01, complete snapshot manifest, complete yearly EFA census, AGG-01 union, and exact S1 membership all completed before the halt. The aggregate yearly universe is membership-only; the frozen Claim Evidence/C1/C2/HCC/HOC chain requires one ranking/structural/EFA provenance path and contains no preregistered segment-aware adapter. Pilot-4 may not resume and may not receive a replacement case. Any retry requires a new pilot/protocol version with the downstream authority path fixed before case exposure.


### Pilot-5

Protocol decisions: `ALL_ITEMS_APPROVED`  
Enumeration decision: `ENUM-01 APPROVED`  
Aggregation decision: `AGG-01 APPROVED`  
Downstream authority decision: `AUTH-01 APPROVED`  
Pilot: `HALTED_NON_QUALIFYING`

Pilot-5 is a fresh protocol created after Pilot-4 halted at downstream authority compatibility.

- [x] Pilot-4 halt retained as `HALTED_NON_QUALIFYING`; no resume/replacement under Pilot-4
- [x] Missing segment-aware downstream authority defect class identified without using Pilot-4 private snapshot/claim contents
- [x] AUTH-01 rule preregistered before any Pilot-5 case exposure at `2026-09-29T11:28:05+08:00`
- [x] Research-only adapter implemented at `tools/pilot5_segment_aware_downstream_authority.py`
- [x] Window-level authority requires identical render-unit composition across every manifested segment
- [x] No best-snapshot selection, vote/majority rule, confidence uplift, specificity uplift, or synthetic single-source authority
- [x] Prediction bridge preserves existing yearly child claim IDs and requires all-and-only eligible claims
- [x] Stable multi-member render units are prediction-lock ineligible under the current one-event-family forecast schema
- [x] Fresh Pilot-5 D01-D12, ENUM-01, AGG-01 and AUTH-01 created PENDING
- [x] Proposed non-overlapping window: `2027-07-01T00:00:00+08:00` → `2027-08-31T23:59:59+08:00`
- [x] Human approval of Pilot-5 D01-D12 at `2026-09-29T11:43:28+08:00`
- [x] Human approval of ENUM-01 at `2026-09-29T11:43:28+08:00`
- [x] Human approval of AGG-01 at `2026-09-29T11:43:28+08:00`
- [x] Human approval of AUTH-01 at `2026-09-29T11:43:28+08:00`
- [x] Separate Pilot-5 final seal / start authorization at `2026-09-29T11:52:02+08:00`; frozen candidate `fe6975f0dc223a27a1e885f50c9f111ee24d68d4`
- [x] Private source census → intake → S1 → PCG READY at `2026-09-29T12:00:14+08:00`
- [x] Fresh candidate exposure / processing began only after PCG READY; frozen candidate used
- [x] Deterministic segment enumeration and structural snapshot rows frozen before EFA
- [x] Private yearly EFA census executed after the frozen rows
- [x] Canonical snapshot-manifest validation — **FAILED_CLOSED** before AGG-01: pre-EFA serialized manifest was not schema-valid under the already-approved canonical manifest contract
- [ ] AGG-01 claim universe — **NOT CREATED**
- [ ] Per-segment downstream chains → AUTH-01 window authority — **NOT REACHED**
- [ ] Exact prediction-lock bridge → prediction lock — **NOT CREATED**


Pilot-5 D01-D12, ENUM-01, AGG-01, AUTH-01 and the proposed window are approved. No start authorization exists. The next valid gate is a separate Pilot-5 final seal/start authorization; private source census and all candidate processing remain prohibited until that later gate and PCG sequence.


Pilot-5 halted fail-closed at `SNAPSHOT_MANIFEST_CANONICAL_VALIDATION_BEFORE_AGGREGATION` on `2026-09-29T12:15:23+08:00` with `PRE_EFA_SNAPSHOT_MANIFEST_SCHEMA_INVALID`. The structural snapshot rows were frozen before EFA and were not changed afterward, but the pre-EFA private manifest serialization did not conform to the already-approved canonical snapshot-manifest schema. EFA had already begun before this was detected, so a new canonical manifest digest cannot be created retrospectively and treated as pre-EFA authority. AGG-01, S1 claim membership, AUTH-01 and prediction lock were not created. Pilot-5 may not resume and may not receive a replacement case; any retry requires a new pilot/protocol version whose gate validates the canonical manifest before EFA execution.


### Pilot-6

Protocol decisions: `ALL_ITEMS_APPROVED`  
Enumeration decision: `ENUM-01 APPROVED`  
Canonical manifest decision: `MANIFEST-01 APPROVED`  
Aggregation decision: `AGG-01 APPROVED`  
Downstream authority decision: `AUTH-01 APPROVED`  
Pilot: `READY_FOR_START_AUTHORIZATION`

Pilot-6 is a fresh protocol version created after Pilot-5 halted on a noncanonical pre-EFA snapshot-manifest serialization. It does not resume or repair Pilot-5.

- [x] Pilot-5 halt retained as `HALTED_NON_QUALIFYING`; no resume/replacement under Pilot-5
- [x] Pilot-5 public defect class isolated without using private snapshot/EFA/claim contents
- [x] MANIFEST-01 preregistered at `2026-09-29T12:27:00+08:00`
- [x] MANIFEST-01 requires canonical helper materialization + exact schema/digest validation before any EFA
- [x] EFA-before-MANIFEST-01-READY fails closed
- [x] Retrospective manifest repair after EFA is prohibited
- [x] Fresh Pilot-6 D01-D12 / ENUM-01 / MANIFEST-01 / AGG-01 / AUTH-01 created PENDING
- [x] Proposed new non-overlapping window: `2027-09-01T00:00:00+08:00` → `2027-10-31T23:59:59+08:00`
- [x] Human approval of Pilot-6 D01-D12 at `2026-09-29T12:39:46+08:00`
- [x] Human approval of ENUM-01 at `2026-09-29T12:39:46+08:00`
- [x] Human approval of MANIFEST-01 at `2026-09-29T12:39:46+08:00`
- [x] Human approval of AGG-01 at `2026-09-29T12:39:46+08:00`
- [x] Human approval of AUTH-01 at `2026-09-29T12:39:46+08:00`
- [ ] Separate Pilot-6 final seal / start authorization
- [ ] Private census → intake → S1 → PCG READY
- [ ] Fresh Pilot-6 candidate exposure / processing
- [ ] ENUM-01 complete enumeration
- [ ] MANIFEST-01 canonical pre-EFA READY receipt
- [ ] Complete EFA census → AGG-01 claim universe
- [ ] Per-segment downstream chains → AUTH-01
- [ ] Prediction lock


Pilot-6 D01-D12, ENUM-01, MANIFEST-01, AGG-01, AUTH-01 and the proposed window are approved. No start authorization exists. The next valid gate is a separate Pilot-6 final seal/start authorization; private source census and all candidate processing remain prohibited until that later gate and PCG sequence.
