# Bazi decadal independent reference profile v1

Status: `DOMAIN_REVIEW_APPROVED`  
Approved at: `2026-09-29T19:39:00+08:00`  
Approved by role: `human_decision_owner`  
Task 3 qualification: `NEEDS_EVIDENCE`  
Oracle execution in the current implementation/review context: `PROHIBITED`

This document freezes the written Project contract that an independent Bazi decadal oracle may implement. It is not an oracle result, comparison result, qualification PASS, or maturity-promotion decision.

The current implementation/review context has seen production code/output and is ineligible to produce expected values later labeled independent.

## Normative identity

- profile_id: `bazi-natal-project-v1`
- rule_version: `1.0-exp`
- decadal_rule: `three-days-one-year-v1`
- Bazi effective-time basis: normalized civil time
- Bazi day-boundary baseline: 23:00
- output age basis: `continuous_years_from_jie_interval`
- maturity/routing: experimental / on-demand

## 1. Direction

Use the natal year heavenly-stem polarity and sex:

- Yang-year male or Yin-year female → `forward`
- Yin-year male or Yang-year female → `reverse`

Yang stems: 甲、丙、戊、庚、壬.  
Yin stems: 乙、丁、己、辛、癸.

For dates before 立春, the year polarity follows the Bazi year in effect before that 立春; Gregorian January 1 alone does not change the Bazi year stem.

## 2. Jie boundary set

The decadal-start interval uses the twelve minor solar terms (節), not the twelve major solar terms (中氣):

小寒、立春、驚蟄、清明、立夏、芒種、小暑、立秋、白露、寒露、立冬、大雪.

The astronomical instant must come from the sealed external source bound into the pre-oracle packet.

## 3. Boundary selection and equality-at-Jie rule

All birth and Jie instants must first be represented on the same absolute-time basis.

- `forward`: use the first Jie instant `>= birth instant`.
- `reverse`: use the last Jie instant `<= birth instant`.

Therefore, when the birth instant is exactly equal to a Jie instant, that current Jie is inclusive and:

```text
interval_seconds = 0
start_age_years = 0
start_datetime = birth_datetime
```

The approved 2015/2016 HKO packet does not contain an exact-equality test because the selected source displays solar-term times to minute precision. This is an explicit coverage limitation, not permission to change the equality rule after results are visible.

## 4. Three-days-one-year conversion

Let `interval_seconds` be the selected non-negative interval.

```text
start_age_years = interval_seconds / (3 * 86400)
```

Equivalent descriptive rule:

- 3 civil days of interval = 1 luck year
- 1 interval day = 4 luck months
- 2 interval hours = 10 luck days

Do not round `start_age_years` for engine/reference comparison.

## 5. Start datetime

Use a tropical-year duration of 365.2425 civil days:

```text
start_datetime =
    birth_datetime
    + start_age_years * 365.2425 civil days
```

This is elapsed-duration arithmetic, not calendar-year replacement.

## 6. Decadal pillar sequence

Starting from the natal month pillar:

- forward → first Da Yun pillar is one sexagenary step forward;
- reverse → first Da Yun pillar is one sexagenary step backward;
- subsequent periods continue one step in the same direction;
- v1 materializes exactly 10 periods.

## 7. Period age and datetime endpoints

For period index `i`, where `i = 0..9`:

```text
period_start_age_years(i) = start_age_years + 10 * i
period_end_age_years(i)   = start_age_years + 10 * (i + 1)

period_start_datetime(i) =
    birth_datetime
    + period_start_age_years(i) * 365.2425 civil days

period_end_datetime(i) =
    birth_datetime
    + period_end_age_years(i) * 365.2425 civil days
```

Each endpoint is calculated directly from the birth instant and its absolute age. Do not derive period `i+1` by repeatedly adding a rounded previous period duration.

Representation semantics are half-open:

```text
[start_datetime, end_datetime)
```

## 8. Approved independent-comparison fields

For every sealed case:

- `/decadal_direction` — exact
- `/periods/0/pillar` — exact
- `/periods/0/start_age_years` — numeric absolute tolerance
- `/periods/0/start_datetime` — datetime absolute-seconds tolerance
- `/periods/1/end_datetime` — datetime absolute-seconds tolerance

The endpoint field is included only because the endpoint-generation rule is now explicitly frozen above.

## 9. Approved HKO precision treatment

For this packet, HKO displayed minute precision is conservatively treated as `±60 seconds`. No assumption of nearest-minute rounding is made.

With the fixed conversion formula:

```text
start_age_years tolerance
= 60 / (3 * 86400)
= 0.0002314814814814815 years

start_datetime / endpoint tolerance
= 60 * 365.2425 / 3
= 7304.85 seconds
```

Approved tolerances:

- `/periods/0/start_age_years`: `0.0002314814814814815`
- `/periods/0/start_datetime`: `7304.85` seconds
- `/periods/1/end_datetime`: `7304.85` seconds

These tolerances are fixed before oracle expected values exist and must not be widened after comparison results are visible.

## 10. Approved external-source and case-census plan

External astronomical provider:

- Hong Kong Observatory
- role: `astronomical_input_only`
- approved archival years: 2015 and 2016
- timezone statement: Hong Kong Time / UTC+08:00

Approved source URLs:

- `https://www.hko.gov.hk/en/gts/astron2015/Solar_Term_2015.htm`
- `https://www.hko.gov.hk/en/gts/astron2016/Solar_Term_2016.htm`

The exact raw source bytes and SHA256 must still be captured before a pre-oracle seal may be created.

The approved case census is the 12-case census in `docs/research/bazi-decadal-preoracle-review-packet.v1.json`, selected before production comparison results and covering:

- male/female direction cases;
- pre-/post-Jie cases;
- common-year and leap-year cases;
- leap day;
- cross-year Jie lookup.

Exact-equality-at-Jie is recorded as a qualification coverage gap for this HKO minute-resolution packet.

## 11. Independence boundary

An independent oracle executor may receive only:

- this approved specification and its SHA256;
- the sealed case-input bundle;
- exact external source bytes and their SHA256;
- approved comparison paths and tolerances;
- canonical serialization/hash instructions.

The oracle executor must not receive:

- production Bazi implementation source;
- production Bazi output for the sealed cases;
- existing synthetic expected values;
- comparator results before oracle/reference sealing.

## 12. Evidence boundary

External astronomical data supports the Jie/time input layer only. It is not an independent Bazi decadal algorithm reference by itself.

An all-MATCH comparison remains evidence for human/domain review. It does not automatically promote `bazi.natal_chart` to Stable.
