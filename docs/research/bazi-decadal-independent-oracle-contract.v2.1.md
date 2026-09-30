# Bazi decadal independent oracle execution contract v2.1

## 1. Input contract

Each case is an object with:

- `case_id`
- `input.birth_datetime`: timezone-aware ISO 8601 civil datetime
- `input.sex`: `male` or `female`
- `input.timezone`: `Asia/Taipei`
- `input_sha256`
- neutral `coverage_tags`

The executor must use the case values exactly as supplied. It must not add,
remove, replace or rename cases or input fields.

## 2. Astronomical Jie source

Use only the supplied raw Hong Kong Observatory files:

- `Solar_Term_2015.htm`
  SHA256 `60a45ab889ef436936571a04a49387c6f9ce8d43243fb21c64e3fcb0331c8320`
- `Solar_Term_2016.htm`
  SHA256 `84beb01553646b807a7c15d6efebdd7550af1ac6d7f06e07bfdd124dab9e443b`

The source pages publish Hong Kong Time / UTC+08:00 to minute precision.
Use the displayed minute exactly. Do not invent sub-minute precision.

For source-precision handling, treat the published time as having conservative
±60-second precision.

The 12 Jie used by this contract and their HKO English labels are:

| HKO label | Jie |
| --- | --- |
| Moderate cold | 小寒 |
| Spring commences | 立春 |
| Insects waken | 驚蟄 |
| Bright and clear | 清明 |
| Summer commences | 立夏 |
| Corn on ear | 芒種 |
| Moderate heat | 小暑 |
| Autumn commences | 立秋 |
| White dew | 白露 |
| Cold dew | 寒露 |
| Winter commences | 立冬 |
| Heavy snow | 大雪 |

The executor may parse all 24 solar terms from each page, but only these 12 Jie
participate in the calculations below.

## 3. Natal year pillar

Let `Y` be the Gregorian year of `birth_datetime`.

1. Resolve 立春 for Gregorian year `Y`.
2. If `birth_datetime >= 立春(Y)`, set `pillar_year = Y`.
3. Otherwise set `pillar_year = Y - 1`.
4. `year_gan_index = (pillar_year - 4) mod 10`.
5. `year_zhi_index = (pillar_year - 4) mod 12`.
6. Year pillar =
   `GAN[year_gan_index] + ZHI[year_zhi_index]`.

GAN order:

甲、乙、丙、丁、戊、己、庚、辛、壬、癸.

ZHI order:

子、丑、寅、卯、辰、巳、午、未、申、酉、戌、亥.

## 4. Natal month pillar

Define `month_index` in the range 0..11:

- 0 = 寅, beginning at 立春
- 1 = 卯, beginning at 驚蟄
- 2 = 辰, beginning at 清明
- 3 = 巳, beginning at 立夏
- 4 = 午, beginning at 芒種
- 5 = 未, beginning at 小暑
- 6 = 申, beginning at 立秋
- 7 = 酉, beginning at 白露
- 8 = 戌, beginning at 寒露
- 9 = 亥, beginning at 立冬
- 10 = 子, beginning at 大雪
- 11 = 丑, beginning at 小寒

Choose the latest Jie boundary `<= birth_datetime`. Include the previous
Gregorian year's 大雪 when required.

Let `year_gan_index` be the 0-based GAN index of the natal year pillar from
Section 3.

```text
start_gan_index = ((year_gan_index mod 5) * 2 + 2) mod 10
month_gan_index = (start_gan_index + month_index) mod 10
month_zhi_index = (2 + month_index) mod 12
month_pillar = GAN[month_gan_index] + ZHI[month_zhi_index]
```

## 5. Decadal direction

Yang stems:

甲、丙、戊、庚、壬.

Yin stems:

乙、丁、己、辛、癸.

Direction rule:

- Yang-year male → `forward`
- Yin-year female → `forward`
- Yin-year male → `reverse`
- Yang-year female → `reverse`

Derive direction from the natal year stem and supplied sex.

## 6. Start Jie and equality

- `forward`: first Jie instant `>= birth_datetime`
- `reverse`: last Jie instant `<= birth_datetime`

At exact equality:

```text
interval_seconds = 0
start_age_years = 0
start_datetime = birth_datetime
```

Otherwise:

- forward interval = selected Jie - birth
- reverse interval = birth - selected Jie

## 7. Three-days-one-year rule

```text
start_age_years = interval_seconds / (3 * 86400)
```

Do not round intermediate values.

Then:

```text
start_datetime =
    birth_datetime + start_age_years * 365.2425 days
```

For this contract, one day in this arithmetic is 86400 seconds.

## 8. Da Yun pillar sequence

Construct the 60 Jiazi cycle for `i = 0..59`:

```text
pillar(i) = GAN[i mod 10] + ZHI[i mod 12]
```

Find the natal month pillar's unique index in that cycle.

- forward first Da Yun pillar = cycle[(index + 1) mod 60]
- reverse first Da Yun pillar = cycle[(index - 1) mod 60]
- each later period advances one additional cycle step in the same direction
- materialize exactly 10 periods

## 9. Period ages and datetimes

For period index `i = 0..9`:

```text
period_start_age_years(i) = start_age_years + 10*i
period_end_age_years(i)   = start_age_years + 10*(i+1)

period_start_datetime(i) =
    birth_datetime + period_start_age_years(i) * 365.2425 days

period_end_datetime(i) =
    birth_datetime + period_end_age_years(i) * 365.2425 days
```

Period representation is:

```text
[start_datetime, end_datetime)
```

Each datetime must preserve the input UTC+08:00 offset.

## 10. Required oracle output paths

For each sealed case, produce expected values only for:

- `/decadal_direction`
- `/periods/0/pillar`
- `/periods/0/start_age_years`
- `/periods/0/start_datetime`
- `/periods/1/end_datetime`

Do not emit additional computed Bazi fields as comparison targets.

## 11. Precision limitation

The supplied astronomical source is minute-resolution. Therefore this packet
does not independently establish the exact sub-minute instant of a Jie.

The equality rule in Section 6 remains normative. The executor must not create
a synthetic sub-minute source time or alter the case census to manufacture an
exact-equality test.
