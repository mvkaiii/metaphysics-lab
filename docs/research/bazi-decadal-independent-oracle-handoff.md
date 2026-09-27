# Bazi decadal independent oracle handoff

Status: PREPARED_FOR_INDEPENDENT_EXECUTOR
Reference packet: NOT_SEALED
Comparison: NOT_STARTED
Task 3 qualification: NEEDS_EVIDENCE

This handoff defines the information boundary for an independent oracle. It does
not contain oracle expected values and does not authorize a qualification PASS.

## Why a separate oracle role is required

The current implementation/review agent has read production code and existing
synthetic engine output. It may build the comparison harness, but it cannot
create expected values and then label those values independent.

The independent oracle executor must not receive production Bazi implementation
source, committed synthetic expected values, or comparison results before seal.
It may receive only the human-approved written Project profile specification,
the preregistered sealed case inputs, sealed external astronomical source bytes,
the packet contract, and canonical serialization/hash instructions.

## External astronomical source role

Candidate provider: Hong Kong Observatory (HKO).

Official source pages:
- https://www.hko.gov.hk/en/gts/astronomy/Solar_Term.htm
- https://www.hko.gov.hk/en/publica/pubgen.htm

The HKO solar-term page states that its astronomical information is based on
data provided by the HM Nautical Almanac Office (United Kingdom) and the United
States Naval Observatory, and that displayed times are Hong Kong Time (UTC+08:00).
The HKO publication catalogue lists the Hong Kong Observatory Almanac from 1984
onwards.

HKO is therefore suitable as an external astronomical input source. It is not
an independent Bazi decadal algorithm reference. For historical cases, the exact
year-specific HKO source bytes must be acquired and sealed; a current webpage or
a catalogue entry is not a substitute for the exact bytes used by the oracle.

## Before the oracle may run

Freeze all of the following before expected values are produced:
1. Complete written profile specification reviewed by a human/domain reviewer:
   direction rule; three-days-one-year conversion; continuous-year denominator
   and precision; jie selection; equality-at-jie rule; timezone/date arithmetic;
   first pillar and subsequent sexagenary sequence; endpoint generation.
2. Case census selected without consulting production results.
3. Exact external source bytes, provenance, precision and SHA256.
4. Tolerances fixed before results are visible.
5. Oracle implementation identifier and code SHA256.
6. Independence attestation with all exposure flags false.

If any item is missing, keep the packet NOT_SEALED.

## Comparator contract

Comparator: tools/compare_bazi_decadal_reference.py

It does not calculate metaphysics values. It consumes a sealed reference packet
and a separately prepared actual bundle with the same case IDs and input digests.
Each comparison uses a JSON Pointer with one of: exact, number_abs,
datetime_abs_seconds, not_comparable, or missing_reference.

The comparator rejects invalid source/oracle digests, exposure flags inconsistent
with independence, missing tolerances, duplicate case/path comparisons, case census
mismatch, and input digest mismatch.

Comparison result is MATCH, MISMATCH, or PARTIAL. Regardless of result it always
emits qualification_decision=HUMAN_REVIEW_REQUIRED and maturity_promotion=false.
An all-MATCH report is evidence for human review, not an automatic Task 3 PASS.

## Independence caveat

The comparator validates the shape of the independence attestation but cannot
prove that role isolation actually occurred. Access control and timing of the seal
remain governance facts requiring human review.

## Current blockers

- Complete written algorithm/profile specification is not yet sealed by a domain reviewer.
- Historical year-specific HKO source bytes and digest are not selected/sealed.
- Case census and tolerances are not sealed.
- No independent oracle implementation or expected values exist.

Task 3 therefore remains NEEDS_EVIDENCE.
