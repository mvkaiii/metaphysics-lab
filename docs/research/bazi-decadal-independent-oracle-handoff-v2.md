# Bazi decadal Task 3 v2 independent-oracle handoff

Status: `READY_FOR_INDEPENDENT_ORACLE_EXECUTOR`

Task 3 qualification remains `NEEDS_EVIDENCE`.

This handoff was built only after human/domain approval of V2-D1 through V2-D5,
freezing the v2 written contract, case bundle and pre-oracle seal.

## Frozen bindings

- production candidate SHA:
  `6280c29b0a493e4b27379948c8cc82ba94bfa04f`
- approved v2 spec SHA256:
  `24825b1c2c850873f54e117c53c13932a8a730dc3a245a1c5e7e2599259c3305`
- v2 case-bundle canonical SHA256:
  `939f8e29123acabfc16366b05622d1d3598b6aa72c4cc54cf96db3ce6e35128e`
- v2 pre-oracle seal canonical SHA256:
  `56f63fbe9561a9216e2f6e597d0f76ca4006af0ffd09a775f4da0d980e13ae0c`
- HKO 2015 raw-byte SHA256:
  `60a45ab889ef436936571a04a49387c6f9ce8d43243fb21c64e3fcb0331c8320`
- HKO 2016 raw-byte SHA256:
  `84beb01553646b807a7c15d6efebdd7550af1ac6d7f06e07bfdd124dab9e443b`

HKO is used as an official public astronomical reference source for this
qualification cycle. This does **not** assert that HKO is the unique or
universal Bazi industry standard.

## Handoff ZIP

Inner handoff ZIP:

`Bazi-Decadal-Independent-Oracle-Handoff-v2-20260930.zip`

SHA256:

`6a1a92e79b1fa26c5527874c86feecc0436ac7cdd825e51b6b5d3e696a5c0be7`

GitHub Actions packaging evidence:

- workflow run: `36659028255`
- artifact id: `11073676130`
- artifact name: `task3-v2-independent-oracle-handoff`
- outer artifact digest:
  `sha256:3a154796e9cf2239c9d6b1423bf8bc90c2c24984692bb6c11de85fa61946d664`

The inner ZIP contains exactly 9 files:

1. `README_FIRST.md`
2. `SHA256SUMS`
3. `Solar_Term_2015.htm`
4. `Solar_Term_2016.htm`
5. `bazi-decadal-independent-profile-spec.v2.md`
6. `bazi-decadal-oracle-case-inputs.v2.json`
7. `bazi-decadal-preoracle-seal.v2.json`
8. `handoff-manifest.v2.json`
9. `source-bindings.json`

No production implementation, production output, dry-run output, comparator
output, qualification result or expected value is included.

## Executor boundary

The current Project / PR context is ineligible to act as the independent
oracle because it has seen production code/output and prior diagnostics.

A valid executor must receive only the v2 handoff boundary, must have no
Metaphysics Lab production code/output or prior Task 3 result exposure, and
must fail closed if that condition is not true.

The executor must independently implement only the approved written contract,
freeze the oracle source SHA256 before expected-value production, emit the
oracle output bundle plus sealing receipt, and stop before production
comparison.

Oracle execution status: `NOT_STARTED`.
