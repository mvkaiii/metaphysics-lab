# Bazi decadal independent oracle handoff

Status: `READY_FOR_INDEPENDENT_ORACLE_EXECUTOR`  
Pre-oracle seal: `SEALED`  
Oracle: `NOT_STARTED`  
Comparison: `NOT_STARTED`  
Task 3 qualification: `NEEDS_EVIDENCE`

This handoff defines the exact clean-room boundary for the independent oracle.
It contains no oracle expected values and does not authorize a qualification PASS.

## Exact sealed identities

- approved profile spec:
  - path: `docs/research/bazi-decadal-independent-profile-spec.v1.md`
  - SHA256: `0757d1275e55b84e2424d6131e9dbdc73e029e1b619f900147be928cc7e5e01d`
- case-input bundle:
  - path: `docs/research/bazi-decadal-oracle-case-inputs.v1.json`
  - canonical bundle SHA256: `ab7ebd72671c3020d67444f720c6f3645111005348efd56efe91ffd2ee699d3f`
  - cases: 12
- pre-oracle seal:
  - path: `docs/research/bazi-decadal-preoracle-seal.v1.json`
  - seal SHA256: `db32a95bc41a54531907e7e059655c094b1b1234a533770a88f2e3a52712874e`
- HKO 2015 raw source:
  - `Solar_Term_2015.htm`
  - SHA256: `60a45ab889ef436936571a04a49387c6f9ce8d43243fb21c64e3fcb0331c8320`
  - byte count: 16070
- HKO 2016 raw source:
  - `Solar_Term_2016.htm`
  - SHA256: `84beb01553646b807a7c15d6efebdd7550af1ac6d7f06e07bfdd124dab9e443b`
  - byte count: 12079

## Why a separate oracle role is required

The current implementation/review context has read production code and existing
synthetic/production outputs. It may validate seals and later run the comparator,
but it cannot create expected values and label those values independent.

The independent oracle executor must not receive production Bazi implementation
source, production output for the 12 sealed cases, committed synthetic expected
values, or comparison results before the oracle bundle is sealed.

## Inputs the independent executor MAY receive

Only:

1. the approved written profile specification;
2. the 12-case sealed synthetic input bundle;
3. the exact HKO 2015 and 2016 raw source bytes;
4. the pre-oracle seal;
5. canonical serialization/hash instructions;
6. this handoff document / handoff manifest.

The source pages are astronomical-input evidence only; they are not an independent
Bazi decadal algorithm by themselves.

## Inputs the independent executor MUST NOT receive

- `engine/bazi/` production source;
- production Bazi results for any sealed case;
- existing synthetic expected outputs;
- comparator output;
- qualification outcome;
- any post-hoc tolerance adjustment;
- any replacement case or changed source bytes.

If any prohibited material is exposed before oracle sealing, the independent
oracle attempt is contaminated and must fail closed.

## Oracle implementation requirements

The independent executor must implement the approved written contract from
scratch without reading production implementation.

It must record:

- oracle builder identifier;
- exact oracle source/code bytes;
- lowercase SHA256 of those oracle code bytes;
- exposure flags, all false;
- attestation;
- sealed_at and sealed_by;
- every exact case_id and input_sha256 from the sealed case bundle;
- every required comparison path.

For each path the oracle may emit either:

- `status=provided` plus `expected`; or
- `status=missing_reference` plus an explicit reason.

It may not alter case IDs, input digests, comparison paths, or tolerances.

## Required comparison census for every case

- `/decadal_direction`
- `/periods/0/pillar`
- `/periods/0/start_age_years`
- `/periods/0/start_datetime`
- `/periods/1/end_datetime`

The independent executor does not decide the tolerances; those are already sealed.

## Oracle output envelope

The output must use schema version `1.0` and contain:

```text
schema_version
preoracle_seal_sha256
oracle_builder_id
oracle_code_sha256
production_code_access=false
production_output_access=false
comparison_result_access_before_seal=false
attestation
sealed_at
sealed_by
cases[]
```

Each case contains:

```text
case_id
input_sha256
comparisons[]
```

Each comparison contains:

```text
path
status = provided | missing_reference
expected  # only when provided
reason    # only when missing_reference
```

The oracle output must bind:

`preoracle_seal_sha256=db32a95bc41a54531907e7e059655c094b1b1234a533770a88f2e3a52712874e`

## What happens after oracle sealing

The oracle bundle is returned to a non-clean-room comparison context.

There:

1. `tools/finalize_bazi_decadal_reference_packet.py` validates exact seal/case/path binding and emits the sealed reference packet.
2. A separately prepared production actual bundle with the same case IDs/input digests is generated.
3. `tools/compare_bazi_decadal_reference.py` performs deterministic comparison.
4. Result remains `HUMAN_REVIEW_REQUIRED`; even all-MATCH does not automatically promote maturity.

## Coverage limitation

D1 equality-at-Jie is normatively frozen as current-Jie-inclusive with interval zero.
The selected HKO pages display minute precision, so the 12-case packet does not claim
an exact-equality qualification case. This remains a disclosed coverage gap rather
than a post-hoc rule change.
