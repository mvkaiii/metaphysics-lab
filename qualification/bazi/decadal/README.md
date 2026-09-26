# Bazi decadal qualification

Status: `NEEDS_EVIDENCE`. This packet audits the structure of the existing
Project Bazi natal decadal output. It does not promote `bazi.natal_chart` or
claim event-prediction validity.

Source binding:

- baseline commit: `872c60b2e959ea48d25524b74686e488f576ec6f`
- engine entry point: `engine.bazi.natal.build_bazi_natal`
- serializer: `engine.natal.orchestration._serialize_bazi`
- baseline source blobs: pinned by Git blob SHA-1 and committed-byte SHA-256 in the fixture and packet
- fixture digest: SHA256 of UTF-8 text after universal newline normalization, stable across Windows `autocrlf` and LF checkouts
- profile: `bazi-natal-project-v1`, rule `1.0-exp`
- fixture: `synthetic-engine-view.v1.json`
- report: `public-project-contract-v1.json`

The public Taipei birth vector is reproducible through the existing engine and
serializer; the focused test compares every serialized decadal period with the
fixture. The packet builder reads each pinned baseline blob with `git cat-file`
and verifies its Git object ID and raw-byte SHA-256. It does not use working-tree
line endings for that source check.

The fixture preserves ten contiguous engine periods and their continuous age
values. It rejects non-sexagenary pillar pairs, malformed numeric/date fields,
non-contiguous time or age intervals, unknown IANA zones, and UTC offsets that
do not match the named zone. It deliberately leaves interval semantics
(`inclusive` versus `[start, end)`) as `needs_confirmation`. No independent
reference is bound to the same age and endpoint profile, so this is structural
evidence only. Qualification remains `NEEDS_EVIDENCE`; no maturity promotion
is recorded.

Reproducibility commands:

```text
python tools/build_bazi_decadal_qualification.py --check
python -m tools.build_bazi_decadal_qualification --check
python -m unittest tests.test_bazi_decadal_qualification -v
```

The required hosted validation environment is Python 3.9. This packet does not
claim its verification commands passed; exact-candidate workflow results and
test counts are reported separately. The source-reproduction test cannot
complete in the current Windows checkout while private vendored tzdata
materialization fails its integrity check.

The packet contains no case, event, prospective outcome, ten-god overlay or
element overlay.
