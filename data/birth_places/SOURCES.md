# Offline Birth Place Registry Sources

## Scope

`registry.v1.json` is a deliberately curated, finite offline registry for Metaphysics Lab portable natal calculation. It is **not** a global gazetteer and must not be treated as one.

v1 guarantees exactly:

- Taiwan: the 22 current county/city-level administrative divisions represented by the selected GeoNames administrative records.
- International: Tokyo, Osaka, Seoul, Hong Kong, Singapore, Kuala Lumpur, Bangkok, Beijing, Shanghai, New York City, Los Angeles, San Francisco, Vancouver, Toronto, London, Paris, Sydney, and Melbourne.

The coverage profile identifier is:

`taiwan-admin1-plus-explicit-major-cities-v1`

The historical profile name is retained for compatibility even though GeoNames currently represents Taiwan's selected 22 county/city records as second-order administrative divisions under its hierarchy.

## Upstream source

Primary geographic authority: **GeoNames**.

- Project: https://www.geonames.org/
- Gazetteer downloads: https://download.geonames.org/export/dump/
- Taiwan administrative-division browser: https://www.geonames.org/TW/administrative-division-taiwan.html
- License: Creative Commons Attribution 4.0 (CC BY 4.0)
- License text: https://creativecommons.org/licenses/by/4.0/

GeoNames states that its gazetteer dump is available under CC BY 4.0. Metaphysics Lab therefore preserves GeoNames attribution here and stores a stable GeoNames identifier in every committed record.

## Curation snapshot

Curation date: **2026-08-24**.

Each registry row uses:

- `source = geonames-curated`
- `source_version = 2026-08-24`
- `source_reference = geonames:<geonameid>`

The `source_reference` identifies the upstream GeoNames feature, for example:

- Taipei City: `geonames:1668338`
- New Taipei City: `geonames:1665148`
- New York City: `geonames:5128581`
- London: `geonames:2643743`

Coordinates are WGS84 point coordinates associated with the selected GeoNames feature. During this curation pass, GeoNames detail/search pages were preferred; where the execution environment could not retrieve a detail page directly, the same GeoNames ID and its coordinates were cross-checked through a source that explicitly identifies GeoNames as its geographic source. The committed GeoNames ID remains the authoritative record reference.

This curation statement does **not** claim that the implementation environment downloaded or reproduced the complete GeoNames country dump byte-for-byte. Runtime never downloads GeoNames.

## Alias policy

Aliases are Project-curated inputs, not a copy of the complete GeoNames alternate-name corpus.

Only explicit aliases committed in `registry.v1.json` may match. Runtime normalization is intentionally limited to Unicode NFKC, trimming/case-folding, whitespace collapse, and a small set of separator normalizations.

The registry deliberately does not implement:

- fuzzy spelling correction
- phonetic matching
- AI/LLM coordinate guessing
- implicit translation
- automatic administrative-area inference

Some short names are intentionally ambiguous. In v1, bare `Chiayi` / `嘉義` and bare `Hsinchu` / `新竹` are attached to both the city and county records. Runtime must therefore return `ambiguous_birth_place` rather than choosing one candidate.

## Maintenance

A registry update must be a reviewable repository change. It must preserve stable source references, update this document when the source or curation method changes, and keep resolver behavior deterministic.

Adding a place to the registry is a data-governance decision; it must not be performed automatically by the runtime or by an LLM during a natal request.
