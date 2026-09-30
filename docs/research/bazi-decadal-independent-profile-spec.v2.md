# Bazi decadal independent reference profile v2

Status: `DOMAIN_REVIEW_APPROVED_V2_D1_D5`  
Task 3 qualification: `NEEDS_EVIDENCE`  
v1 seal: immutable historical evidence; no in-place repair.

This v2 profile exists because the v1 dry-run showed that an independent
executor could not derive the natal year/month pillars from the written
contract alone, and because v1 case metadata leaked the expected direction.

Human/domain decisions V2-D1 through V2-D5 were approved on
2026-09-30. This document is the approved written contract for the next
pre-oracle seal. Approval does not create expected values and does not itself
authorize oracle execution before the v2 seal is complete.

## 1. Inputs

Each case supplies only:

- timezone-aware normalized civil `birth_datetime`;
- `sex = male | female`;
- neutral coverage tags that do not encode expected Bazi results.

No year pillar, month pillar, direction, Da Yun pillar, expected value or
production-derived classification may appear in the clean-room case metadata.

## 2. Jie boundary source

The 12 Jie are:

小寒、立春、驚蟄、清明、立夏、芒種、小暑、立秋、白露、寒露、立冬、大雪.

### 2.1 Independent oracle source

For the v2 clean-room oracle, astronomical Jie inputs come only from the exact
raw HKO archival bytes already captured for 2015 and 2016. HKO is used here as
an official public astronomical reference source for this qualification cycle;
this does not claim that HKO is the unique or universal Bazi industry standard:

- 2015 source SHA256:
  `60a45ab889ef436936571a04a49387c6f9ce8d43243fb21c64e3fcb0331c8320`
- 2016 source SHA256:
  `84beb01553646b807a7c15d6efebdd7550af1ac6d7f06e07bfdd124dab9e443b`

The pages publish Hong Kong Time / UTC+08:00 to minute precision. The oracle
must use the displayed minute and must not invent sub-minute precision.

Published-source precision is conservatively treated as ±60 seconds.

### 2.2 Production engineering provider

The production engine separately uses the Project-private bundled
`lunar-python==1.4.8` JieQi table, source revision
`000c8a3d74eed098d6256a28fdd51b869324c559`.

That provider was selected only after the preregistered HKO embedded-static
benchmark passed 48/48 Jie points within ±60 seconds. This production provider
is not an allowed oracle input. The oracle therefore does not reproduce
production code or read production output.

Boundary comparison is inclusive:

- at exact equality the current Jie belongs to the new period;
- `birth >= Jie` means the birth is on/after that Jie.

## 3. Natal year pillar — self-contained rule

Let `Y` be the Gregorian year of the normalized birth datetime.

1. Resolve the exact 立春 instant for Gregorian year `Y`.
2. If `birth_datetime >= 立春(Y)`, set `pillar_year = Y`.
3. Otherwise set `pillar_year = Y - 1`.
4. Heavenly-stem index:
   `year_gan_index = (pillar_year - 4) mod 10`.
5. Earthly-branch index:
   `year_zhi_index = (pillar_year - 4) mod 12`.
6. Year pillar is:
   `GAN[year_gan_index] + ZHI[year_zhi_index]`.

GAN order:

甲、乙、丙、丁、戊、己、庚、辛、壬、癸.

ZHI order:

子、丑、寅、卯、辰、巳、午、未、申、酉、戌、亥.

## 4. Natal month pillar — self-contained rule

Define `month_index` in the range 0..11 where:

- 0 = 寅 month beginning at 立春
- 1 = 卯 month beginning at 驚蟄
- 2 = 辰 month beginning at 清明
- 3 = 巳 month beginning at 立夏
- 4 = 午 month beginning at 芒種
- 5 = 未 month beginning at 小暑
- 6 = 申 month beginning at 立秋
- 7 = 酉 month beginning at 白露
- 8 = 戌 month beginning at 寒露
- 9 = 亥 month beginning at 立冬
- 10 = 子 month beginning at 大雪
- 11 = 丑 month beginning at 小寒

Choose the latest Jie boundary `<= birth_datetime`, including the previous
Gregorian year's 大雪 when required.

Obtain the year heavenly stem using Section 3 and let
`year_gan_index` be its 0-based GAN index.

Then:

```text
start_gan_index = ((year_gan_index mod 5) * 2 + 2) mod 10
month_gan_index = (start_gan_index + month_index) mod 10
month_zhi_index = (2 + month_index) mod 12
month_pillar = GAN[month_gan_index] + ZHI[month_zhi_index]
```

## 5. Direction

Yang stems: 甲、丙、戊、庚、壬.  
Yin stems: 乙、丁、己、辛、癸.

- Yang-year male or Yin-year female → `forward`
- Yin-year male or Yang-year female → `reverse`

The independent executor must derive this from Sections 3 and 5. Case metadata
must not reveal the expected direction.

## 6. Start boundary and equality rule

- forward: first Jie instant `>= birth_datetime`
- reverse: last Jie instant `<= birth_datetime`

At exact equality:

```text
interval_seconds = 0
start_age_years = 0
start_datetime = birth_datetime
```

## 7. Three-days-one-year

```text
start_age_years = interval_seconds / (3 * 86400)
start_datetime =
    birth_datetime + start_age_years * 365.2425 civil days
```

Do not round intermediate values.

## 8. Da Yun pillar sequence

Construct the 60 Jiazi cycle by index `i = 0..59`:

```text
pillar(i) = GAN[i mod 10] + ZHI[i mod 12]
```

Find the natal month pillar's unique index in that 60-cycle.

- forward first Da Yun pillar = cycle[index + 1 mod 60]
- reverse first Da Yun pillar = cycle[index - 1 mod 60]
- each subsequent period moves one additional step in the same direction
- materialize exactly 10 periods.

## 9. Period endpoints

For period index `i = 0..9`:

```text
period_start_age_years(i) = start_age_years + 10*i
period_end_age_years(i)   = start_age_years + 10*(i+1)

period_start_datetime(i) =
    birth_datetime + period_start_age_years(i) * 365.2425 civil days

period_end_datetime(i) =
    birth_datetime + period_end_age_years(i) * 365.2425 civil days
```

Representation is `[start_datetime, end_datetime)`.

## 10. v2 case-metadata prohibition

Clean-room case metadata MUST NOT include strings or fields equivalent to:

- `forward_direction_expected_from_contract`
- `reverse_direction_expected_from_contract`
- expected year/month/Da Yun pillars
- expected Jie identity
- expected comparison status
- production output-derived labels.

Neutral tags such as `common_year`, `leap_year`, `leap_day`,
`before_published_jie_minute`, `after_published_jie_minute`,
`cross_gregorian_year_lookup` are allowed only when they do not reveal the
result being independently computed.

### 10.1 Equality coverage limitation

The HKO archival pages used by the oracle publish minute precision only.
Therefore the v2 independent case census does not claim to test an exact
sub-minute astronomical equality instant. Exact-equality semantics remain a
written-contract rule and are covered by deterministic Project unit tests.
This coverage limitation must be explicitly accepted during domain review; it
must not be hidden by widening tolerances or fabricating a sub-minute HKO time.

## 11. Approved domain decisions and remaining seal gate

Approved human/domain decisions:

1. **V2-D1** — HKO 2015/2016 exact raw bytes are accepted as the official
   public astronomical reference source for the independent oracle in this
   qualification cycle, with conservative ±60-second published precision.
   This is not a claim that HKO is the unique or universal Bazi industry
   standard.
2. **V2-D2** — Sections 3 and 4 are accepted as the self-contained natal
   year-pillar and natal month-pillar derivation rules.
3. **V2-D3** — the same 12 birth/sex inputs selected before v1 result exposure
   are accepted with opaque IDs and neutral metadata only; no cases may be
   added, removed or replaced in this cycle.
4. **V2-D4** — comparison paths are frozen as direction exact, first Da Yun
   pillar exact, start-age absolute tolerance
   `0.0002314814814814815`, and datetime endpoint absolute tolerance
   `7304.85` seconds.
5. **V2-D5** — exact-Jie equality remains the inclusive written rule:
   forward uses first Jie `>= birth`, reverse uses last Jie `<= birth`.
   The independent HKO packet does not claim sub-minute exact-equality coverage;
   that limitation remains explicit.

Completed engineering prerequisites:

- the preregistered 2013–2016 HKO embedded-static benchmark passed;
- production timing is fixed to the Project-private bundled
  `lunar-python==1.4.8` authority;
- post-change repository regressions passed;
- the non-independent 12-case diagnostic improved to
  `48 MATCH / 0 MISMATCH / 12 MISSING_REFERENCE`.

Remaining mechanical gates before oracle execution:

1. freeze this exact written specification SHA256;
2. bind the approved production candidate commit;
3. materialize and digest the v2 no-answer-leakage case bundle;
4. create and validate a fresh v2 pre-oracle seal;
5. only then hand that sealed packet to an independent oracle executor.
