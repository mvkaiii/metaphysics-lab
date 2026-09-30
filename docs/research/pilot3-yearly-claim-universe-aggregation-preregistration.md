# Pilot-3｜Multi-segment yearly authority / claim-universe preregistration

Status: **APPROVED_BY_HUMAN_DECISION_OWNER**  
Pilot ID: **Pilot-3**  
Aggregation profile: `lin_tianji_multi_segment_yearly_claim_universe_v1`  
Aggregation rule: `complete_union_of_all_manifested_efa_child_inventories`  
Candidate case exposure: **PROHIBITED UNTIL SEPARATE START AUTHORIZATION + PCG READY**

## 1. Problem statement

Pilot-3 is a new pilot. It does not repair or resume Pilot-2.

The research contract already fixes a window-level claim scope of `yearly`, monthly timing, and S1 exact matching against a complete EFA child inventory. The unresolved point is how one window-wide yearly claim universe is determined when the frozen candidate materializes more than one structural snapshot inside the same prospective window.

This preregistration fixes that rule **before any Pilot-3 case is exposed to the candidate**.

## 2. Evidence boundary for rule selection

The selection basis is limited to general contract semantics and architecture invariants:

- S1 requires a complete, outcome-free claim-identity census.
- EFA child identity is deterministic from yearly scope, domain, and event family.
- EFA preserves both opened and unopened child candidates from its source snapshot.
- C2 / HOC are downstream authorities and may not redefine the upstream claim census.
- Existing research arm-freeze work assumes one already-selected structural source and therefore cannot silently decide a multi-snapshot case.

Pilot-2 is used only to establish the **process defect class**: a multi-segment yearly universe rule was missing. Pilot-2 observed child-set cardinalities, set composition, union size, intersection size, or any claim identity are **not inputs to this rule selection**.

## 3. Deterministic options considered

| Option | Deterministic if preregistered? | Complete-census semantics | Decision |
|---|---:|---:|---|
| One fixed reference snapshot (start / end / midpoint) | yes | no, unless the estimand is redefined as a single-reference snapshot | reject |
| Intersection of all snapshot child sets | yes | no; it removes claims authorized in only some segments | reject |
| Union of all complete snapshot child sets | yes | yes; every manifested segment contributes membership | **select** |
| Segment-qualified new claim IDs | yes | potentially, but changes claim ontology, denominator, downstream contracts and scoring unit | defer to a separate future protocol |

The selected rule is based on completeness semantics, not on empirical claim counts.

## 4. Frozen aggregation contract

### 4.1 Pre-EFA snapshot manifest

After Pilot-3 PCG is READY and the fresh case may be processed, the candidate must first freeze an ordered **yearly segment snapshot manifest** before claim-universe aggregation.

The manifest binds:

- the approved window-policy digest;
- a contiguous canonical snapshot index;
- an opaque snapshot ID;
- a structural-state digest.

The manifest schema intentionally accepts no EFA child IDs, child counts, render decisions, outcomes, oracle labels, scores, or qualification results.

No snapshot may be added, removed, reordered, or replaced after EFA contents are inspected.

### 4.2 Complete EFA census per snapshot

For every manifest snapshot, exactly one canonical EFA bundle must be supplied.

Each bundle must:

- use the frozen EFA profile;
- use `target_scope=yearly`;
- have a valid canonical EFA digest;
- contain a non-empty, internally unique complete child inventory;
- preserve opened and unopened child identities.

Missing, extra, duplicated, reordered, non-yearly, or digest-invalid snapshots fail closed.

### 4.3 Yearly universe membership

The Pilot-3 yearly claim universe is:

```text
sorted_unique_union(
  complete_EFA_children(snapshot_0),
  complete_EFA_children(snapshot_1),
  ...,
  complete_EFA_children(snapshot_n)
)
```

A child appearing in multiple snapshots contributes **one** yearly claim identity. Repetition across snapshots does not increase evidence weight, confidence, rank, specificity, or probability.

### 4.4 Authority provenance

The union operation determines **membership only**.

It does not merge EFA evidence, average or maximize ranking scores, select a “best” snapshot, upgrade C1/C2/HOC authority, turn timing into yearly target authority, or rewrite event-family semantics.

The aggregate lock preserves every source snapshot's EFA digest and child-set digest. No single snapshot is retrospectively elevated as the yearly authority winner.

Any downstream component that requires one EFA/ranking/structural digest must not silently consume the aggregate lock as though it came from one snapshot. Pilot-3 prediction locking requires a segment-aware downstream adapter or another preregistered compatible authority path. Otherwise execution fails closed before prediction lock.

### 4.5 S1 exact match

S1 locked claim IDs must exactly equal the aggregate `locked_claim_ids` set. No render subset, intersection subset, or single-snapshot subset can substitute for that set.

## 5. Validator and fail-closed rules

The public research validator at `tools/pilot3_yearly_claim_universe.py` enforces:

- exact manifest schema and digest;
- exact snapshot census and order;
- current EFA profile and yearly scope;
- EFA digest integrity;
- no duplicate child identity inside one snapshot;
- deterministic sorted set union;
- exact S1 locked-ID match;
- `promotion_allowed=false`.

Any unknown or unverifiable prerequisite is a hard stop. There is no manual override.

## 6. Scope not solved by this contract

This contract does **not** yet authorize a real Pilot-3 case, a start seal, a prediction lock, single-source arm-freeze reuse, outcome collection, adjudication, scoring, qualification, or Stable promotion.

Pilot-3 D01-D12 and AGG-01 were explicitly approved by the human decision owner at `2026-09-28T13:57:00+08:00`. This approval has no start-authorization effect. The next human gate is the separate Pilot-3 final seal / start authorization.
