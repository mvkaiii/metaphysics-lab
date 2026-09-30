# Bazi decadal independent reference profile — domain-review candidate

Status: `DRAFT_PENDING_DOMAIN_REVIEW`  
Task 3 qualification: `NEEDS_EVIDENCE`  
Oracle execution: `NOT_AUTHORIZED_FROM_THIS_CONTEXT`

This document is a review candidate assembled from the already approved Project design/implementation plan and the 2026-09-27 Task 3 methodology decision. It is **not** an independent oracle, a qualification result, or a maturity-promotion decision.

The current implementation/review context has seen production code/output and is therefore ineligible to produce expected values that are later labeled independent.

## Normative identity proposed for review

- profile_id: `bazi-natal-project-v1`
- rule_version: `1.0-exp`
- decadal_rule: `three-days-one-year-v1`
- Bazi effective-time basis: normalized civil time
- Bazi day boundary baseline: 23:00
- output age basis: `continuous_years_from_jie_interval`
- maturity/routing: experimental / on-demand

## Proposed decadal algorithm text

### 1. Direction

Use the natal year heavenly-stem polarity and sex:

- Yang-year male or Yin-year female → `forward`
- Yin-year male or Yang-year female → `reverse`

Yang stems: 甲、丙、戊、庚、壬.  
Yin stems: 乙、丁、己、辛、癸.

### 2. Jie boundary set

The decadal-start interval uses the twelve minor solar terms (節), not the twelve major solar terms (中氣):

小寒、立春、驚蟄、清明、立夏、芒種、小暑、立秋、白露、寒露、立冬、大雪.

The astronomical instant must come from the sealed external source bound into the pre-oracle packet.

### 3. Boundary selection

- `forward`: measure from the birth instant to the next Jie.
- `reverse`: measure from the previous Jie to the birth instant.

The birth instant and the Jie instant must be converted to the same absolute-time basis before subtraction.

### 4. Three-days-one-year conversion

Let `interval_seconds` be the selected non-negative interval.

```text
start_age_years = interval_seconds / (3 * 86400)
```

Equivalent descriptive rule:

- 3 civil days of interval = 1 luck year
- 1 interval day = 4 luck months
- 2 interval hours = 10 luck days

Do not round `start_age_years` for engine/reference comparison.

### 5. Start datetime

The proposed Project profile uses a tropical-year duration of 365.2425 civil days:

```text
start_datetime =
    birth_datetime
    + start_age_years * 365.2425 civil days
```

The calculation uses elapsed duration, not calendar-year replacement.

### 6. Decadal pillar sequence

Starting from the natal month pillar:

- forward → first Da Yun pillar is one sexagenary step forward;
- reverse → first Da Yun pillar is one sexagenary step backward;
- subsequent periods continue one step in the same direction;
- v1 materializes exactly 10 periods.

### 7. Comparison fields proposed for independent qualification

For every sealed case:

- `/decadal_direction` — exact
- `/periods/0/pillar` — exact
- `/periods/0/start_age_years` — numeric absolute tolerance
- `/periods/0/start_datetime` — datetime absolute-seconds tolerance

Subsequent endpoint comparisons remain blocked until the endpoint-generation rule below is resolved by domain review.

## Source-precision propagation proposal

The selected HKO archival solar-term pages publish times to minute granularity and state that times are Hong Kong Time (UTC+08:00).

Until HKO rounding semantics or a higher-precision source is sealed, this proposal uses a conservative `±60 seconds` source-instant uncertainty for review purposes only.

Under the fixed conversion formula above, a 60-second Jie uncertainty propagates to:

```text
start_age_years tolerance
= 60 / (3 * 86400)
= 0.0002314814814814815 years

start_datetime tolerance
= 60 * 365.2425 / 3
= 7304.85 seconds
```

These are **proposed pre-result tolerances**, not approved tolerances. They must be accepted or replaced by the domain reviewer before a pre-oracle seal may be created.

## Blocking domain decisions

The following are intentionally unresolved and prevent sealing:

1. **Equality-at-Jie rule**  
   The approved plan requires an equality rule, but the currently selected HKO archival pages expose minute-resolution timestamps. A domain reviewer must decide whether:
   - equality means equality to the published minute;
   - a higher-precision source is mandatory; or
   - equality cases are excluded from the independent packet and reported as a qualification gap.

2. **Subsequent endpoint-generation rule**  
   The approved plan defines 10-year age spans and the visualization contract uses `[start,end)`, but the independent-reference text must explicitly define how each period's datetime endpoint is calculated. It must not be inferred from production code.

3. **Published-time precision semantics**  
   HKO displays minute precision, but the review must decide whether the qualification tolerance should treat that as ±30 seconds, ±60 seconds, or use a separately documented higher-precision source.

Until all three items are resolved, this document remains `DRAFT_PENDING_DOMAIN_REVIEW`.

## Independence boundary

An independent oracle executor may receive only:

- this document after human/domain approval and digest freeze;
- the sealed case census;
- exact external source bytes and their SHA256;
- approved tolerances and comparison paths;
- canonical serialization/hash instructions.

The oracle executor must not receive:

- production Bazi implementation source;
- production Bazi output for the sealed cases;
- existing synthetic expected values;
- comparator results before oracle/reference sealing.

## Evidence boundary

External astronomical data supports the Jie/time input layer only. It is not an independent Bazi decadal algorithm reference by itself.

Even an all-MATCH comparison remains evidence for human review and does not automatically promote `bazi.natal_chart` to Stable.
