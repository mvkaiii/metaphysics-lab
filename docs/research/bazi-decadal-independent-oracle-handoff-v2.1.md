# Bazi decadal Task 3 v2.1 clean independent-oracle handoff

Status: `READY_FOR_INDEPENDENT_ORACLE_EXECUTOR`

This v2.1 handoff replaces the v2 execution handoff because the v2 written
specification mixed normative rules with prior engineering and diagnostic
results. The v2 handoff was halted before oracle execution.

The v2.1 change is sanitization-only: it removes non-normative history and
makes the HKO English-to-Jie mapping explicit. The approved domain rules and
12-case census are unchanged.

## Clean bindings

- execution contract:
  `docs/research/bazi-decadal-independent-oracle-contract.v2.1.md`
- execution contract SHA256:
  `b47de7809cadb82159c272b2d2d7fb3bbc7ffc99d9e8ed6c1fa60a1bf3c900e4`
- case bundle canonical SHA256:
  `939f8e29123acabfc16366b05622d1d3598b6aa72c4cc54cf96db3ce6e35128e`
- pre-oracle seal canonical SHA256:
  `53f4e249f4f6e13fd26e9859101cceeaac31a1f186c155653a24e79f02dd4a27`
- HKO 2015 raw-byte SHA256:
  `60a45ab889ef436936571a04a49387c6f9ce8d43243fb21c64e3fcb0331c8320`
- HKO 2016 raw-byte SHA256:
  `84beb01553646b807a7c15d6efebdd7550af1ac6d7f06e07bfdd124dab9e443b`

## Clean handoff ZIP

File:

`Bazi-Decadal-Independent-Oracle-Cleanroom-v2.1-20260930.zip`

SHA256:

`5674a7d943e14e841d17d3ae9d0bab650912524ac93a9b1b334c92381d135304`

Packaging evidence:

- workflow run: `36665923915`
- packaging HEAD: `c20fafb818e5ee31d0f95d13c5e17019651ab1b9`
- artifact id: `11076158110`
- artifact name: `task3-v2-1-clean-oracle-handoff`
- outer artifact digest:
  `sha256:5383e599cf16d2cea9d10fa7a575b9030629047471e97f467876707476589b26`

The ZIP contains exactly 9 files:

1. `README_FIRST.md`
2. `SHA256SUMS`
3. `Solar_Term_2015.htm`
4. `Solar_Term_2016.htm`
5. `bazi-decadal-independent-oracle-contract.v2.1.md`
6. `bazi-decadal-oracle-case-inputs.v2.1.json`
7. `bazi-decadal-preoracle-seal.v2.1.json`
8. `handoff-manifest.v2.1.json`
9. `source-bindings.json`

Automated checks before packaging:

- exact execution-contract SHA: PASS
- pre-oracle seal validator: PASS
- HKO source-byte SHA checks: PASS
- 12-case census: PASS
- expected-values absent: PASS
- prior-result leakage scan: PASS
- deterministic ZIP creation: PASS
- SHA256SUMS verification after download: PASS

The downloaded ZIP was independently re-opened after packaging; all 9 files
were present, all SHA256SUMS entries verified, and the prior-result leakage scan
returned no hits.

Oracle execution status: `NOT_STARTED`.

The current Project context is not eligible to execute the independent oracle.
