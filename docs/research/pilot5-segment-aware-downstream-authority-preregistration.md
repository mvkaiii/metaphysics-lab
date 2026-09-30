# Pilot-5｜Segment-aware downstream authority preregistration

Status: **PENDING_HUMAN_APPROVAL**  
Pilot ID: **Pilot-5**  
Preregistered at: `2026-09-29T11:28:05+08:00`  
Authority profile: `lin_tianji_segment_aware_window_authority_v1`  
Authority rule: `unanimous_stable_render_unit_across_all_manifested_segments_no_authority_synthesis`  
Prediction bridge: `full_window_single_child_exact_identity_all_eligible_claims_no_confidence_uplift`

## 1. Purpose

Pilot-4 established one process-defect class: complete multi-segment membership can be frozen, while the existing downstream Claim Evidence/C1/C2/HCC/HOC chain still carries one ranking/structural/EFA provenance path at a time.

Pilot-5 fixes that missing contract **before any Pilot-5 case exposure**.

Pilot-4 private snapshot counts, snapshot identities, structural contents, EFA contents, claim counts, claim identities, render decisions, or outcomes are not inputs to this rule selection.

## 2. Source contracts preserved

AUTH-01 does not replace or rewrite the existing single-segment chain. Every manifested segment must first independently produce its ordinary frozen chain:

`Claim Evidence → C1 → EFA → C2/HCA → Interpretation v1 → HCC → HOC`.

Every digest link remains segment-local and must validate. No aggregate ranking digest, aggregate structural digest, aggregate EFA digest, or “best snapshot” is created.

AGG-01 remains membership-only.

## 3. Window-level authority rule

For every HOC render unit, define its composition identity only from:

- primary domain;
- composition type;
- ordered member child claim IDs.

A window render unit exists only if the **identical composition identity is renderable in every manifested segment**.

If a unit is missing in any segment, changes composition, or contains a child that is not renderable in every segment, it is not authorized as a full-window render unit.

For an authorized full-window unit:

- specificity = the most conservative specificity observed across segments;
- visibility = the most conservative visibility observed across segments;
- required caveats = sorted unique union across segments;
- cross-system relations are preserved as an observed set, not converted into extra confidence;
- every segment's ranking, structural, Claim Evidence, C1, EFA, C2, Interpretation, HCC and HOC digests remain explicitly bound;
- causality remains prohibited;
- repeated appearance across segments never increases weight, confidence, rank or specificity.

## 4. Abstention reasons

A union-member child that is not window-renderable receives one deterministic reason in this precedence:

1. `not_in_every_segment_universe`;
2. `not_renderable_in_every_segment`;
3. `unstable_render_unit_composition`.

No manual override exists.

## 5. Prediction-lock bridge

The existing prospective forecast contract has one event-family string and one contiguous forecast window per claim. Pilot-5 therefore does **not** invent segment-qualified claim IDs.

A yearly child is prediction-lock eligible only when:

- it belongs to a full-window authorized render unit;
- that render unit contains exactly one child.

Stable multi-member render units remain valid presentation authority but are prediction-lock ineligible under the current one-event-family forecast-claim schema.

For every eligible claim:

- existing yearly `child_claim_id` is preserved exactly;
- primary domain and event family must match the frozen child identity;
- forecast window must equal the entire approved Pilot-5 outcome window;
- confidence may not exceed the lowest parent Claim Evidence confidence across all manifested segments;
- confidence mapping is fixed: low_confidence→low, moderate_confidence→medium, high_confidence→high;
- `priority` / `partial_if` are prohibited in Pilot-5 so the 3-primary/2-secondary optional truncation path cannot create a post-exposure subset;
- the final prediction lock must contain **all and only** eligible claim IDs;
- if the eligible set is empty, execution halts before prediction lock.

Prediction wording and match criteria remain governed by the existing prospective forecast contract and must not exceed the authorized specificity ceiling.

## 6. No authority synthesis

AUTH-01 explicitly prohibits:

- choosing a best or representative segment after exposure;
- taking “any segment renderable” as full-window authority;
- voting/majority rules;
- confidence uplift from repeated segments;
- specificity uplift from repeated segments;
- merging multiple source digests into a synthetic single-source authority;
- creating new child claim identities;
- splitting yearly claims into segment-qualified scoring units.

## 7. Public implementation

Research-only implementation:

`tools/pilot5_segment_aware_downstream_authority.py`

Synthetic conformance tests:

`tests/test_pilot5_segment_aware_downstream_authority.py`

Real Pilot-5 segment outputs, IDs, counts and digests remain outside public Git.

## 8. Human gate

AUTH-01 is preregistered but **not approved**.

Pilot-5 D01-D12, ENUM-01, AGG-01, AUTH-01 and the proposed outcome window all require explicit human decision-owner approval. Approval has no start effect. A later separate start authorization is still required before private census/intake/S1, and candidate processing remains blocked until PCG READY.


## 9. Human approval checkpoint

Pilot-5 D01-D12, ENUM-01, AGG-01, AUTH-01 and the proposed window were explicitly approved by the human decision owner at `2026-09-29T11:43:28+08:00`.

AUTH-01 remains mandatory, has no manual override and has no start-authorization effect. Real Pilot-5 private processing remains prohibited until a separate final seal/start authorization and later PCG READY.


## 10. Start authorization checkpoint

A separate Pilot-5 start authorization was explicitly granted by the human decision owner at `2026-09-29T11:52:02+08:00`.

AUTH-01 remains unchanged and frozen by the start seal. Private source census, intake and S1 preparation may proceed; real candidate processing and segment-aware authority execution remain prohibited until PCG READY.
