# Ziwei Month-Boundary Qualification

This directory contains reproducible qualification evidence for the existing Project Ziwei month-layer rules. It is evidence, not a second normative rule source.

## Production authority

The production formulas remain in:

- `engine/ziwei/month.py` for effective lunar-month palace semantics;
- `engine/ziwei/fine_cycle_stems.py` for the Phase 2B monthly stem/branch source;
- `core/命理推導計算規則.md` for the normative Project rule description.

This qualification does not change those formulas and does not promote capability maturity.

## Rule under qualification

- Ordinary lunar month: use that lunar month.
- Leap month day 1 through 15: use the original month.
- Leap month day 16 onward: use the following effective lunar month.
- A leap twelfth month therefore continues into the next lunar year's first month for the second-half month source.
- The Ziwei 23:00 day rollover does not independently advance the month layer. Month changes remain owned by the neutral lunar conversion supplied by Calendar Resolver.

## Public evidence

The broader executable oracle is pinned `lunar-python==1.4.8`, source revision `000c8a3d74eed098d6256a28fdd51b869324c559`.

The qualifier compares Project monthly stem/branch output with `LunarMonth.getGanZhi()` for ordinary and leap-first-half cases. For leap-second-half cases it compares with the actual following lunar month returned by `LunarMonth.next(1)`.

The matrix includes the historical lunar year 1574, which the pinned lunar-python source explicitly lists as a leap-twelfth year. This permits a real leap-12 continuity check: the second half of leap twelfth must agree with the following lunar year’s month 1.

## lunar-lite limitation

The existing Phase 2B anchor remains pinned to `SylarLong/lunar-lite` revision `1d104fffa31609e9f112898cc57545827e8d57ae`, package `0.2.8`, with 18/18 existing checks passing.

Its normal lunar-month formula adds `fixLeap` to `abs(lunarMonth) - 1` and then indexes `MONTHLY_EARTHLY_BRANCHES`, which contains 12 entries. A leap-twelfth second-half case reaches zero-based index 12, outside that table. Therefore lunar-lite is retained as a source-contract anchor but is **not** represented as a direct executable oracle for this rare case.

The Project does not silently patch or reinterpret that external source.

## Adjacent boundaries

Regression tests in `tests/test_ziwei_month_boundary_qualification.py` are responsible for locking the surrounding integration boundaries:

- leap day 15/16 split;
- ordinary lunar month end and next-month start;
- lunar year month 12 to next year month 1;
- 23:00 month neutrality;
- DST nonexistent/ambiguous local-time ownership by Calendar Resolver;
- downstream monthly source reuse by transformations/flying/flowing-star layers;
- modular versus generated single-file runtime parity for representative supported targets.

## Reproducibility

Generate evidence:

```bash
python tools/build_ziwei_month_boundary_qualification.py
```

Verify committed evidence without mutation:

```bash
python tools/build_ziwei_month_boundary_qualification.py --check
```

The qualification requires `lunar-python==1.4.8` and fails if the installed oracle version differs.

## Interpretation limit

A PASS means the existing deterministic month-layer calculation matched the stated pinned public evidence and boundary properties. It does not establish metaphysical predictive accuracy, does not validate every historical calendar edge case, and does not convert an experimental fine-cycle capability into a stable/default capability.
