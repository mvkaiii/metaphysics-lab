# Portable Offline Natal Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 讓單一 `dist/ai/metaphysics_lab.py` 在 clean Python sandbox（包含 `python -S`、無 site-packages、無網路）中，對 offline registry 支援的出生地完成 Project 原生八字、紫微與 Normalized Natal；核心 calendar authority 固定來自 bundle 內的 `lunar-python==1.4.8` 與 `tzdata==2026.3`，不受 execution environment 預裝套件影響。

**Architecture:** 將兩個核心 calendar dependency 以 Project-private namespace `_metaphysics_lab_vendor` 納入 repo 與 generated bundle；將出生地解析加入版本化、可稽核的 offline registry，並固定 resolution precedence 為 explicit resolved location → offline registry → explicit network fallback → fail closed。Distribution builder 升級為 byte-oriented payload format 1.1，支援 tzdata binary TZif resources、vendor manifest/license、registry bytes 與完整 checksum；`runtime_info` 升 Runtime Schema 1.1，區分 bundled core 與 optional execution-environment integrations。

**Tech Stack:** Python 3.9-compatible syntax、stdlib `argparse/ast/base64/dataclasses/hashlib/importlib/json/pathlib/re/shutil/tarfile/tempfile/unicodedata/zipfile/zlib/zoneinfo`、existing `engine/birth` / `engine/calendar` / `engine/natal` / `engine/distribution`、`unittest`。Bundled third-party pins：`lunar-python==1.4.8`、`tzdata==2026.3` / IANA `2026c`；optional network integrations 保留 `geopy==2.5.0`、`timezonefinder==8.2.0`。

**Spec:** `docs/superpowers/specs/2026-08-24-Portable-Offline-Natal-Pipeline-設計.md`（approved on branch `design/portable-offline-natal-pipeline`; terminology revision commit `7e3f7e0766a6660d555a39af441ebbecb058dcb0`）

## Global Constraints

- Implementation must not start on `main` or the design branch. At execution time create `feature/portable-offline-natal-pipeline` from `design/portable-offline-natal-pipeline`, then merge the then-current `main` into the feature branch before writing code so the approved spec/plan and latest public documentation both travel with the implementation.
- `v1.3.0` tag, existing Release assets and existing release provenance are immutable in this plan.
- `PROJECT_CONTRACT_VERSION` remains `1.1`; `CASE_SCHEMA_VERSION` remains `1.1`.
- `RUNTIME_SCHEMA_VERSION` changes `1.0 → 1.1`; `DISTRIBUTION_RUNTIME_VERSION` changes `1.0-exp → 1.1-exp`; `BUILD_FORMAT_VERSION` changes `1.0 → 1.1`.
- Core Natal authority for lunar/calendar/timezone must come only from bundled Project-private bytes. Execution-environment packages with the same public names must never change Project core results.
- No runtime or normal distribution build may run `pip install`, download from PyPI/GitHub, geocode live, or auto-fetch third-party bytes.
- Vendor refresh is an explicit maintenance action only. It must use exact version pins and verify exact artifact SHA256 before changing committed vendor bytes.
- Private vendor imports must never rely on public top-level `lunar_python` or `tzdata` names.
- Offline location resolution must be deterministic and data-driven. No LLM coordinate/timezone guessing, fuzzy matching, spell correction, phonetic matching, implicit translation, or automatic administrative-area inference.
- Location resolution precedence is fixed: explicit `resolved_location` → Project Offline Registry → explicitly enabled network resolver → fail closed.
- Offline ambiguity returns `ambiguous_birth_place` and must never fall through to network resolution.
- Offline miss with network disabled returns `location_not_resolved`.
- `natal.candidate_envelope` keeps its existing pre-resolved-location requirement in this implementation. Do not expand scope unless a separate design change is approved.
- Generated `metaphysics_lab.py` must remain `<= 5 MiB`; exceeding the guard requires architecture review, not a larger threshold.
- Same source tree and supported build toolchain must produce byte-identical distribution artifacts.
- Astralium remains External Natal Source only. Portable implementation must not use Astralium as calculation authority.
- The temporary Astralium-first onboarding policy merged by PR #171 is removed only after clean-environment qualification passes; the final documentation task in this plan performs that switch back to Birth Data first.
- Every behavior-changing task uses RED → verify expected failure → minimal GREEN → focused regression → commit.
- No capability maturity promotion, Stable promotion, new tag, GitHub Release, or release-number decision is part of this plan.

---

## File Map

### Create

- `_metaphysics_lab_vendor/__init__.py`
- `_metaphysics_lab_vendor/lunar_python/**` — vendored upstream `lunar-python==1.4.8` package bytes
- `_metaphysics_lab_vendor/tzdata/__init__.py`
- `_metaphysics_lab_vendor/tzdata/zoneinfo/**` — vendored `tzdata==2026.3` binary/resources
- `vendor/manifest.json`
- `vendor/licenses/lunar-python-LICENSE.txt`
- `vendor/licenses/tzdata-LICENSE.txt`
- `vendor/licenses/THIRD_PARTY_NOTICES.md`
- `engine/vendor/__init__.py`
- `engine/vendor/manifest.py`
- `engine/birth/offline_registry.py`
- `data/birth_places/registry.v1.json`
- `data/birth_places/schema.v1.json`
- `data/birth_places/SOURCES.md`
- `tools/vendor_refresh.py`
- `tests/test_vendor_manifest.py`
- `tests/test_vendor_import_isolation.py`
- `tests/test_offline_birth_place_registry.py`
- `tests/test_ai_distribution_portability.py`

### Modify

- `engine/calendar/lunar.py`
- `engine/calendar/timezone.py`
- `engine/distribution/dependencies.py`
- `engine/distribution/runtime.py`
- `engine/distribution/constants.py`
- `engine/distribution/natal.py`
- `tools/build_ai_distribution.py`
- `tests/test_distribution_runtime_info.py`
- `tests/test_distribution_natal.py`
- `tests/test_ai_distribution_build.py`
- `tests/test_ai_distribution_bundle.py`
- `README.md`
- `core/核心提示詞.md`
- `docs/發布說明-v1.3.0.md`
- `CHANGELOG.md`
- generated `dist/ai/metaphysics_lab.py`
- generated `dist/ai/project_instructions.md`

### Explicitly do not modify for metaphysical semantics

- Bazi natal rules
- Ziwei natal rules
- `engine/ziwei/transformations.py`
- `engine/ziwei/flying.py`
- `engine/ziwei/fine_cycle_stems.py`
- `engine/ziwei/flowing_stars.py`
- `VERSION.md`
- `v1.3.0` tag / release assets

---

### Task 1: Vendor Manifest, Refresh Tool and Private Package Trees

**Files:**
- Create: `tools/vendor_refresh.py`
- Create: `vendor/manifest.json`
- Create: `vendor/licenses/lunar-python-LICENSE.txt`
- Create: `vendor/licenses/tzdata-LICENSE.txt`
- Create: `vendor/licenses/THIRD_PARTY_NOTICES.md`
- Create: `_metaphysics_lab_vendor/__init__.py`
- Create: `_metaphysics_lab_vendor/lunar_python/**`
- Create: `_metaphysics_lab_vendor/tzdata/**`
- Create: `tests/test_vendor_manifest.py`
- Create: `tests/test_vendor_import_isolation.py`

**Interfaces:**
- Consumes two exact upstream artifacts during maintenance only: `lunar_python-1.4.8.tar.gz` and `tzdata-2026.3-py2.py3-none-any.whl`.
- Produces committed private package trees and `vendor/manifest.json` used by calendar providers, runtime-info and distribution builder.

**Exact artifact pins:**

```text
lunar-python 1.4.8 sdist SHA256
3aa11cc73c25e70ddf0ba5bdac7398c03acc9491a3aa512a91c9642973b669d6
source revision
000c8a3d74eed098d6256a28fdd51b869324c559
license
MIT

tzdata 2026.3 wheel SHA256
dc096730c87af6cab1b171c9d532be840741ff5d459015e7f6947bd7d7e54931
IANA tzdb
2026c
source revision
a44279419071b7aa41ebe7eca301ebb2e759571a
license
Apache-2.0
```

**Manifest package entry:**

```json
{
  "package_name": "lunar-python",
  "import_namespace": "_metaphysics_lab_vendor.lunar_python",
  "version": "1.4.8",
  "source_repository": "https://github.com/6tail/lunar-python",
  "source_revision": "000c8a3d74eed098d6256a28fdd51b869324c559",
  "source_artifact": "lunar_python-1.4.8.tar.gz",
  "artifact_sha256": "3aa11cc73c25e70ddf0ba5bdac7398c03acc9491a3aa512a91c9642973b669d6",
  "vendored_tree_sha256": "<computed by tool>",
  "license_spdx": "MIT",
  "license_file": "vendor/licenses/lunar-python-LICENSE.txt",
  "bundled": true,
  "runtime_authority": "bundled"
}
```

The implementation writes the computed hash value; the tool must never accept a caller-supplied tree hash.

- [ ] **Step 1: Write RED manifest/refresh tests.** Add tests that require both package entries, exact versions/artifact hashes/source revisions/licenses, `runtime_authority == "bundled"`, existing license files, and a deterministic package-tree hash.

```python
def test_vendor_manifest_pins_exact_core_dependencies(self):
    manifest = load_json(ROOT / "vendor" / "manifest.json")
    packages = {row["package_name"]: row for row in manifest["packages"]}
    self.assertEqual(packages["lunar-python"]["version"], "1.4.8")
    self.assertEqual(packages["tzdata"]["version"], "2026.3")
    self.assertEqual(packages["lunar-python"]["runtime_authority"], "bundled")
    self.assertEqual(packages["tzdata"]["runtime_authority"], "bundled")
```

- [ ] **Step 2: Write RED import-isolation tests.** AST-scan all vendored `.py` files and fail if any `Import` / `ImportFrom` references public top-level `lunar_python` or `tzdata`. Also reject symlinks anywhere under `_metaphysics_lab_vendor`.
- [ ] **Step 3: Run RED.**

```bash
python -m unittest tests.test_vendor_manifest tests.test_vendor_import_isolation -v
```

Expected: FAIL because vendor manifest/private trees do not exist.

- [ ] **Step 4: Implement `tools/vendor_refresh.py`.** Public entry point:

```python
def refresh_vendor(repo_root: Path, lunar_sdist: Path, tzdata_wheel: Path) -> dict:
    ...
```

Behavior: verify artifact SHA256 before extraction; extract only the upstream Python package subtree and license; reject absolute paths, `..`, symlinks and unexpected archive members; copy lunar package bytes to `_metaphysics_lab_vendor/lunar_python`; copy tzdata `__init__.py` plus complete `zoneinfo/**` resource tree to `_metaphysics_lab_vendor/tzdata`; run AST import scan; compute tree hashes; write manifest and notices only after all validation passes.
- [ ] **Step 5: Use an explicit maintenance command to obtain the pinned artifacts.** This network use is allowed only for vendor maintenance and is not part of normal build/runtime.

```bash
mkdir -p /tmp/metaphysics-vendor
python -m pip download --no-deps --no-binary :all: lunar-python==1.4.8 -d /tmp/metaphysics-vendor
python -m pip download --no-deps --only-binary=:all: tzdata==2026.3 -d /tmp/metaphysics-vendor
python tools/vendor_refresh.py \
  --lunar-sdist /tmp/metaphysics-vendor/lunar_python-1.4.8.tar.gz \
  --tzdata-wheel /tmp/metaphysics-vendor/tzdata-2026.3-py2.py3-none-any.whl
```

- [ ] **Step 6: GREEN vendor tests.**

```bash
python -m unittest tests.test_vendor_manifest tests.test_vendor_import_isolation -v
```

Expected: PASS and no public-name imports/symlinks.
- [ ] **Step 7: Commit.**

```bash
git add tools/vendor_refresh.py vendor _metaphysics_lab_vendor tests/test_vendor_manifest.py tests/test_vendor_import_isolation.py
git commit -m "build: vendor pinned calendar dependencies"
```

---

### Task 2: Bundled Vendor Metadata Authority and Calendar Provider Refactor

**Files:**
- Create: `engine/vendor/__init__.py`
- Create: `engine/vendor/manifest.py`
- Modify: `engine/calendar/lunar.py`
- Modify: `engine/calendar/timezone.py`
- Modify: `tests/test_vendor_manifest.py`
- Modify existing calendar tests that currently assume public installed packages.

**Interfaces:**
- Produces:

```python
def bundled_dependency(package_name: str) -> Mapping[str, object]:
    ...

def bundled_vendor_manifest() -> Mapping[str, object]:
    ...
```

- Calendar imports become:

```python
from _metaphysics_lab_vendor.lunar_python import Solar
from _metaphysics_lab_vendor import tzdata as bundled_tzdata
```

- [ ] **Step 1: RED lunar provider test.** Preload fake `sys.modules["lunar_python"]` with a wrong implementation/version and assert `LunarPythonProvider()` still reports `1.4.8` and returns the canonical fixture result.
- [ ] **Step 2: RED tzdata provider test.** Preload fake public `tzdata`, and patch execution-environment package metadata to an incorrect version; `PinnedTzdataProvider()` must still report package `2026.3`, IANA `2026c`, and resolve `Asia/Taipei` from private bundled resources.
- [ ] **Step 3: Run RED focused tests.** Expected failure: current providers import public packages and call `importlib.metadata.version()`.
- [ ] **Step 4: Implement `engine/vendor/manifest.py`.** Load `vendor/manifest.json` relative to repository/runtime root, validate schema/version/package uniqueness, and return immutable copies to callers. Never query `importlib.metadata` for bundled dependency authority.
- [ ] **Step 5: Refactor `engine/calendar/lunar.py`.** Replace public import and package-metadata lookup with private import plus `bundled_dependency("lunar-python")`. Preserve `EXPECTED_LUNAR_VERSION`, source revision, validation windows and all existing HKO semantics.
- [ ] **Step 6: Refactor `engine/calendar/timezone.py`.** Replace public `tzdata` import and metadata lookup with private package + manifest metadata. Change resource lookup to:

```python
resource = files("_metaphysics_lab_vendor.tzdata.zoneinfo").joinpath(*parts)
```

Preserve all ambiguous/nonexistent local-time logic unchanged.
- [ ] **Step 7: GREEN + calendar regression.**

```bash
python -m unittest tests.test_vendor_manifest -v
python -m unittest discover -s tests -p 'test_calendar*.py' -v
```

- [ ] **Step 8: Commit.**

```bash
git add engine/vendor engine/calendar tests
git commit -m "refactor: use bundled calendar provider authority"
```

---

### Task 3: Deterministic Offline Birth Place Registry

**Files:**
- Create: `data/birth_places/registry.v1.json`
- Create: `data/birth_places/schema.v1.json`
- Create: `data/birth_places/SOURCES.md`
- Create: `engine/birth/offline_registry.py`
- Create: `tests/test_offline_birth_place_registry.py`

**Interfaces:**

```python
def normalize_birth_place_alias(value: str) -> str:
    ...

def resolve_offline_birth_place(value: str) -> ResolvedBirthPlace:
    ...
```

`resolve_offline_birth_place` raises existing `BirthFoundationError` codes:
- `ambiguous_birth_place` with `query`, `candidate_count`, `candidates`.
- `location_not_resolved` with `query`.

Successful provenance:

```text
provider_name = metaphysics_lab_offline_registry
provider_version = 1.0
provider_reference = <record_id>|<source_reference>
resolution_status = resolved
```

**v1 guaranteed canonical coverage:** all 22 Taiwan county/city-level divisions, plus these explicitly supported international cities: Tokyo, Osaka, Seoul, Hong Kong, Singapore, Kuala Lumpur, Bangkok, Beijing, Shanghai, New York City, Los Angeles, San Francisco, Vancouver, Toronto, London, Paris, Sydney, Melbourne.

Taiwan records must all use `Asia/Taipei`. International records use canonical IANA zones (`Asia/Tokyo`, `Asia/Seoul`, `Asia/Hong_Kong`, `Asia/Singapore`, `Asia/Kuala_Lumpur`, `Asia/Bangkok`, `Asia/Shanghai`, `America/New_York`, `America/Los_Angeles`, `America/Vancouver`, `America/Toronto`, `Europe/London`, `Europe/Paris`, `Australia/Sydney`, `Australia/Melbourne`).

Each record must contain `record_id`, `canonical_name`, `country_code`, `admin_area`, numeric latitude/longitude, timezone, explicit `aliases`, `source`, `source_version`, and `source_reference`. Canonical coordinates and stable source IDs must be copied from a traceable geographic source; the committed `SOURCES.md` documents GeoNames CC BY 4.0 attribution and the curation date. Runtime never downloads GeoNames.

- [ ] **Step 1: RED schema/coverage tests.** Assert exact Taiwan 22 canonical set, exact international set above, unique `record_id`, coordinates in range, timezone non-empty, source provenance non-empty and no duplicate normalized alias within the same record.
- [ ] **Step 2: RED alias tests.** Require these aliases to resolve to the same Taipei record: `台北`, `臺北`, `台北市`, `臺北市`, `Taipei`, `Taipei City`.
- [ ] **Step 3: RED ambiguity/unknown tests.** Add one synthetic ambiguous fixture via an injected test registry and assert `ambiguous_birth_place`; unknown input returns `location_not_resolved`.
- [ ] **Step 4: RED normalization limits.** Assert normalization performs only Unicode NFKC, trim, case-fold, whitespace collapse and limited separator normalization. Inputs requiring fuzzy spelling or translation must not match unless explicitly listed as aliases.
- [ ] **Step 5: Run RED.**

```bash
python -m unittest tests.test_offline_birth_place_registry -v
```

- [ ] **Step 6: Implement registry loader/resolver.** Load committed JSON deterministically, validate schema at construction, build normalized alias → records index, preserve all candidates, never choose the first candidate when multiple match.
- [ ] **Step 7: Populate registry data and attribution.** Commit only curated records, not a global GeoNames dump.
- [ ] **Step 8: GREEN.**

```bash
python -m unittest tests.test_offline_birth_place_registry -v
```

- [ ] **Step 9: Commit.**

```bash
git add data/birth_places engine/birth/offline_registry.py tests/test_offline_birth_place_registry.py
git commit -m "feat: add deterministic offline birthplace registry"
```

---

### Task 4: Integrate Offline Location Resolution into `build_natal`

**Files:**
- Modify: `engine/distribution/natal.py`
- Modify: `tests/test_distribution_natal.py`

**Interfaces:** Existing `build_natal(payload)` response shape remains:

```text
input_resolution
resolved_location
project_natal
normalized_natal
```

Resolution decision:

```python
if payload.get("resolved_location") is not None:
    use explicit ResolvedBirthPlace
else:
    try offline registry
    if ambiguous: raise immediately
    if unique: use offline result
    if miss and network_location.enabled: use existing Nominatim provider
    if miss and network disabled: location_not_resolved
```

- [ ] **Step 1: RED explicit-location precedence test.** Provide a birth-place string that exists in registry plus an explicit different `resolved_location`; assert explicit location wins and offline resolver is not consulted as authority.
- [ ] **Step 2: RED offline happy path.** Payload contains only `birth` with `birth_place="台北市"`; assert success, full offline provenance, Bazi pillars, 12 Ziwei palaces and normalized model.
- [ ] **Step 3: RED ambiguity behavior.** Inject ambiguous offline registry result and set `network_location.enabled=true`; assert `ambiguous_birth_place` and network provider is never called.
- [ ] **Step 4: RED unknown behavior.** Unknown place + network disabled returns `location_not_resolved`, replacing the current `location_resolution_required` behavior for supplied birth-place misses.
- [ ] **Step 5: RED network fallback.** Offline miss + explicit network config calls existing provider path and preserves network provenance.
- [ ] **Step 6: Run RED.**

```bash
python -m unittest tests.test_distribution_natal -v
```

- [ ] **Step 7: Implement minimal integration.** Import `resolve_offline_birth_place` without importing `engine.birth.location`; keep network provider lazy so `geopy/timezonefinder` remain optional.
- [ ] **Step 8: Keep Candidate Envelope unchanged.** `build_candidate_natal` continues to require explicit `resolved_location`; add a regression assertion for `missing_candidate_location_basis` so scope cannot drift silently.
- [ ] **Step 9: GREEN + natal regression.**

```bash
python -m unittest tests.test_distribution_natal -v
python -m unittest discover -s tests -p 'test_*natal*.py' -v
```

- [ ] **Step 10: Commit.**

```bash
git add engine/distribution/natal.py tests/test_distribution_natal.py
git commit -m "feat: resolve supported birth places offline"
```

---

### Task 5: Runtime Schema 1.1 Dependency Contract

**Files:**
- Modify: `engine/distribution/constants.py`
- Modify: `engine/distribution/dependencies.py`
- Modify: `engine/distribution/runtime.py`
- Modify: `tests/test_distribution_runtime_info.py`

**Interfaces:** `runtime_info.data` adds:

```json
{
  "dependency_authority": {
    "calendar_core": "bundled",
    "network_location": "execution_environment_optional"
  },
  "bundled_dependencies": {
    "lunar-python": {
      "package": "lunar-python",
      "version": "1.4.8",
      "bundled": true,
      "available": true,
      "runtime_uses_environment_package": false,
      "source_revision": "000c8a3d74eed098d6256a28fdd51b869324c559",
      "artifact_sha256": "3aa11cc73c25e70ddf0ba5bdac7398c03acc9491a3aa512a91c9642973b669d6",
      "vendored_tree_sha256": "...",
      "license": "MIT",
      "role": "calendar",
      "required_for": ["calendar_resolution", "build_natal", "resolve_forecast_context"]
    }
  },
  "optional_external_dependencies": {
    "geopy": {"installed": false, "version": null, "matches_pin": false},
    "timezonefinder": {"installed": false, "version": null, "matches_pin": false}
  },
  "offline_location_registry": {
    "version": "1.0",
    "record_count": 40,
    "coverage_profile": "taiwan-admin1-plus-explicit-major-cities-v1",
    "source_profiles": ["geonames-curated-2026-08-24"],
    "bundled": true
  }
}
```

`record_count` above is exact for 22 Taiwan + 18 international records.

Backward-compatible `external_dependencies` remains for Runtime Schema 1.1 but becomes diagnostic-only execution-environment inspection; each row gains `deprecated=true` and `authority="diagnostic_only"`. It must not decide core calculation availability.

- [ ] **Step 1: RED version tests.** Assert Runtime Schema `1.1`, distribution runtime `1.1-exp`, Project Contract/Case Schema remain `1.1`.
- [ ] **Step 2: RED bundled dependency tests.** Under monkeypatched missing/wrong public packages, `bundled_dependencies["lunar-python"]` and `tzdata` remain `available=true` and `runtime_uses_environment_package=false`.
- [ ] **Step 3: RED optional external tests.** `geopy/timezonefinder` keep `installed/version/matches_pin` environment inspection.
- [ ] **Step 4: RED registry metadata tests.** Assert version, exact record count 40, coverage profile and bundled flag without returning full alias data.
- [ ] **Step 5: Run RED.**

```bash
python -m unittest tests.test_distribution_runtime_info -v
```

- [ ] **Step 6: Refactor dependency inspection.** Keep a legacy diagnostic function for four public packages, add a dedicated optional-external inspector for geopy/timezonefinder, and derive bundled core facts only from `vendor/manifest.json` plus committed tree existence.
- [ ] **Step 7: Update constants and `runtime_info()`.** No heavy calendar/location imports in runtime-info path.
- [ ] **Step 8: GREEN.**

```bash
python -m unittest tests.test_distribution_runtime_info -v
```

- [ ] **Step 9: Commit.**

```bash
git add engine/distribution tests/test_distribution_runtime_info.py
git commit -m "feat: expose bundled dependency authority in runtime info"
```

---

### Task 6: Byte-Oriented Bundle Format 1.1

**Files:**
- Modify: `tools/build_ai_distribution.py`
- Modify: `tests/test_ai_distribution_build.py`
- Modify: `tests/test_ai_distribution_bundle.py`

**Interfaces:**

```python
BUILD_FORMAT_VERSION = "1.1"

def discover_bundle_inputs(repo_root: Path) -> List[str]:
    ...

def build_file_record(repo_root: Path, relative_path: str) -> Dict[str, str]:
    ...
```

Every embedded record is canonical JSON with:

```json
{
  "path": "_metaphysics_lab_vendor/tzdata/zoneinfo/Asia/Taipei",
  "sha256": "<sha256 of decoded bytes>",
  "encoding": "base64",
  "content": "<base64>"
}
```

Use base64 for all records. Existing first-party text newline normalization happens before base64 encoding; vendored source, vendor licenses, manifest, registry and TZif resources are preserved byte-for-byte.

Bundle input allowlist:
- `engine/**/*.py`
- `templates/**/*.tmpl`
- `_metaphysics_lab_vendor/**` regular files
- `vendor/manifest.json`
- `vendor/licenses/**` regular files
- `data/birth_places/registry.v1.json`
- `data/birth_places/schema.v1.json`
- `data/birth_places/SOURCES.md`

- [ ] **Step 1: RED binary-record test.** Build to temp dir, inspect decoded payload, assert a TZif resource is present, marked `base64`, decodes to non-text bytes and matches record SHA256.
- [ ] **Step 2: RED source-digest coverage test.** Mutate a copied vendor file, registry file and license file independently; each must change `SOURCE_DIGEST`.
- [ ] **Step 3: RED path-security tests.** Feed extraction records containing absolute path, `..`, duplicate target and checksum mismatch; bootstrap must reject each before writing outside runtime root.
- [ ] **Step 4: RED deterministic build test.** Existing byte-identical three-artifact test remains and now includes vendor/binary inputs.
- [ ] **Step 5: Run RED.**

```bash
python -m unittest tests.test_ai_distribution_build tests.test_ai_distribution_bundle -v
```

- [ ] **Step 6: Implement byte payload.** Replace text-only `_source_records` with allowlisted byte records; canonical JSON remains `sort_keys=True` and compact separators. Update bootstrap extraction to decode base64, validate each file SHA256, validate duplicate/unsafe paths, then write bytes.
- [ ] **Step 7: Preserve generated artifact names.** Only `metaphysics_lab.py`, `metaphysics_core.md`, `project_instructions.md` are emitted.
- [ ] **Step 8: GREEN build tests.**

```bash
python -m unittest tests.test_ai_distribution_build tests.test_ai_distribution_bundle -v
```

- [ ] **Step 9: Commit.**

```bash
git add tools/build_ai_distribution.py tests/test_ai_distribution_build.py tests/test_ai_distribution_bundle.py
git commit -m "build: support vendored binary resources in AI bundle"
```

---

### Task 7: Clean Sandbox and Environment-Pollution Qualification

**Files:**
- Create: `tests/test_ai_distribution_portability.py`
- Modify: `tests/test_ai_distribution_bundle.py`

**Interfaces:** test helper:

```python
def run_clean_bundle(action: str, payload: Mapping[str, object]) -> dict:
    ...
```

The helper creates a temporary directory containing only a copied `metaphysics_lab.py`, runs `[sys.executable, "-S", bundle, "request", "--input", "-"]` with `cwd=tempdir`, and parses one JSON object.

- [ ] **Step 1: Reverse the old contract in RED.** Replace `test_missing_core_dependency_returns_machine_readable_error` with a clean `python -S` happy-path test using only birth data for `台北市`; expected result is `ok=true`, not `dependency_unavailable`.
- [ ] **Step 2: RED one-file qualification.** Temp directory must contain only `metaphysics_lab.py`; no repo source tree, site-packages, resolved_location, Astralium or network config. Assert Bazi pillars, exactly 12 Ziwei palaces and normalized natal exist.
- [ ] **Step 3: RED runtime-info qualification.** `python -S` reports bundled lunar/tzdata available; optional geopy/timezonefinder may be absent.
- [ ] **Step 4: RED execution-environment pollution tests.** Use a subprocess launcher with temporary fake public `lunar_python` and `tzdata` packages representing missing/old/new/fake versions; also test public names preloaded in `sys.modules`. Full Project output must equal the clean baseline.
- [ ] **Step 5: RED network-block test.** In an in-process bundle launcher, replace `socket.socket` with a function that raises if called; offline-supported Taipei build must still succeed, proving no network attempt.
- [ ] **Step 6: GREEN.**

```bash
python -m unittest tests.test_ai_distribution_portability tests.test_ai_distribution_bundle -v
```

- [ ] **Step 7: Commit.**

```bash
git add tests/test_ai_distribution_portability.py tests/test_ai_distribution_bundle.py
git commit -m "test: qualify single-file offline natal runtime"
```

---

### Task 8: Integrity, License, Reproducibility and Size Guards

**Files:**
- Modify: `tools/build_ai_distribution.py`
- Modify: `tests/test_vendor_manifest.py`
- Modify: `tests/test_ai_distribution_build.py`
- Modify: `tests/test_ai_distribution_portability.py`

**Interfaces:**

```python
MAX_BUNDLE_BYTES = 5 * 1024 * 1024

def verify_vendor_inputs(repo_root: Path) -> None:
    ...
```

`verify_vendor_inputs` runs before render/build and rejects missing manifest/license/package tree, tree-hash mismatch, symlinks, unexpected vendor path or residual public-package imports.

- [ ] **Step 1: RED tamper tests.** Copy repo inputs to temp fixture, alter one vendored source/resource byte, registry byte and manifest tree hash; each build must fail closed before artifact emission.
- [ ] **Step 2: RED license guard.** Delete either required license file in temp fixture; build must fail with a deterministic validation error.
- [ ] **Step 3: RED size guard.** Add enough temporary allowlisted bytes to make rendered `metaphysics_lab.py` exceed 5 MiB; build must fail with the measured byte count and fixed limit.
- [ ] **Step 4: RED absolute-host-data guard.** Existing build test continues forbidding absolute repo paths, `/home/runner/`, tests and qualification corpus in generated bundle.
- [ ] **Step 5: Implement verification gate and size check.** Do not make limit configurable through normal build flags.
- [ ] **Step 6: GREEN focused tests.**

```bash
python -m unittest tests.test_vendor_manifest tests.test_ai_distribution_build tests.test_ai_distribution_portability -v
```

- [ ] **Step 7: Commit.**

```bash
git add tools/build_ai_distribution.py tests
git commit -m "build: enforce portable bundle integrity guards"
```

---

### Task 9: Regenerate Distribution and Prove Modular ↔ Bundle Parity

**Files:**
- Modify generated: `dist/ai/metaphysics_lab.py`
- Modify generated only if source changed: `dist/ai/project_instructions.md`
- Modify: `tests/test_ai_distribution_bundle.py`

- [ ] **Step 1: Build generated artifacts.**

```bash
python tools/build_ai_distribution.py
```

- [ ] **Step 2: Verify no drift.**

```bash
python tools/build_ai_distribution.py --check
```

Expected: `AI distribution is up to date`.
- [ ] **Step 3: Extend parity assertions.** For the same birth-only Taipei payload, compare complete modular `dispatch("build_natal", payload)` result to clean bundled result; compare `runtime_info` including bundled dependency and registry metadata.
- [ ] **Step 4: Run parity tests.**

```bash
python -m unittest tests.test_ai_distribution_bundle tests.test_ai_distribution_portability -v
```

- [ ] **Step 5: Commit.**

```bash
git add dist/ai tests/test_ai_distribution_bundle.py
git commit -m "build: regenerate portable offline AI distribution"
```

---

### Task 10: Switch Public Onboarding Back to Birth Data First

**Files:**
- Modify: `README.md`
- Modify: `core/核心提示詞.md`
- Modify: `docs/發布說明-v1.3.0.md`
- Modify generated: `dist/ai/project_instructions.md`
- Modify: `CHANGELOG.md`
- Modify relevant docs tests if they assert the temporary onboarding text.

**Purpose:** Remove the temporary Astralium-first policy only after Tasks 1–9 prove the single-file clean-sandbox path.

**Required resulting user flow:**

```text
開始建立我的命理專案
↓
AI asks only for missing birth fields
↓
sex + Gregorian date + exact time + birth place
↓
Project offline Natal for supported registry place
↓
Astralium remains optional External cross-check
```

- [ ] **Step 1: RED docs test.** Assert public README and generated Project Instructions no longer say AI should first direct every new user to Astralium; assert they instead say supported offline registry places can build Project Natal without network or extra Python packages.
- [ ] **Step 2: Remove `2.2.1 過渡期首次建立流程` from `core/核心提示詞.md`.** Restore Birth Data first while preserving External / Project / Resolved governance and Astralium optionality.
- [ ] **Step 3: Update README.** Document offline coverage as finite/versioned, exact fallback order, ambiguity fail-closed behavior and the option to provide pre-resolved location or explicitly enable network resolution for unsupported places.
- [ ] **Step 4: Remove the temporary 2026-08-24 Astralium-first banner from `docs/發布說明-v1.3.0.md`.** Do not rewrite v1.3.0 tag/assets; this repo file is the maintained user-facing source only.
- [ ] **Step 5: Add Unreleased CHANGELOG entry.** State bundled calendar dependencies, offline registry, Runtime Schema 1.1, distribution runtime 1.1-exp and restored Birth Data first onboarding; explicitly state no Stable promotion/release/tag change.
- [ ] **Step 6: Regenerate instructions and bundle.**

```bash
python tools/build_ai_distribution.py
python tools/build_ai_distribution.py --check
```

- [ ] **Step 7: Run docs/build tests.**

```bash
python -m unittest tests.test_ai_contract_docs tests.test_ai_distribution_build -v
```

- [ ] **Step 8: Commit.**

```bash
git add README.md core/核心提示詞.md docs/發布說明-v1.3.0.md CHANGELOG.md dist/ai
git commit -m "docs: restore birth-data-first portable onboarding"
```

---

### Task 11: Final Acceptance and Release Gate Evidence

**Files:** no new feature files unless a failing test requires a scoped fix. Do not tag or release.

- [ ] **Step 1: Focused portable suite.**

```bash
python -m unittest \
  tests.test_vendor_manifest \
  tests.test_vendor_import_isolation \
  tests.test_offline_birth_place_registry \
  tests.test_distribution_runtime_info \
  tests.test_distribution_natal \
  tests.test_ai_distribution_build \
  tests.test_ai_distribution_bundle \
  tests.test_ai_distribution_portability -v
```

Expected: 0 failures / 0 errors.

- [ ] **Step 2: Full repository regression.**

```bash
python -m unittest discover -s tests -v
```

Expected: 0 failures / 0 errors.

- [ ] **Step 3: Deterministic distribution check.**

```bash
python tools/build_ai_distribution.py --check
```

Expected: `AI distribution is up to date`.

- [ ] **Step 4: Python 3.9 compile qualification.**

```bash
python3.9 -m compileall -q engine tools _metaphysics_lab_vendor
```

Expected: exit 0.

- [ ] **Step 5: Clean single-file proof.** Run the portability test directly and retain its output in the PR evidence:

```bash
python -m unittest tests.test_ai_distribution_portability.AIDistributionPortabilityTests.test_clean_python_s_builds_taipei_natal_from_birth_only -v
```

Expected: PASS.

- [ ] **Step 6: Verify bundle size.**

```bash
python - <<'PY'
from pathlib import Path
p = Path('dist/ai/metaphysics_lab.py')
print(p.stat().st_size)
assert p.stat().st_size <= 5 * 1024 * 1024
PY
```

- [ ] **Step 7: Review exact diff against the approved spec.** Confirm no metaphysical algorithm changes, no Astralium authority change, no tag/release asset change, no maturity promotion, and no global geodata dump.
- [ ] **Step 8: Request code review.** Use `superpowers:requesting-code-review` on the exact feature head and fix only verified issues.
- [ ] **Step 9: Re-run Steps 1–6 after review fixes.** Fresh evidence is required before any completion claim.
- [ ] **Step 10: Prepare implementation PR only.** PR body must include exact head SHA, focused/full test counts, clean `python -S` proof, bundle byte size, Runtime Schema/Runtime version changes, vendor provenance/hashes, offline coverage profile and explicit statement that release/tag/Stable promotion remain out of scope.

---

## Acceptance Mapping

- Spec Hard Invariants 4.1–4.6 → Tasks 1, 2, 6, 7, 8.
- Vendor provenance/license/checksum → Tasks 1, 8.
- Binary TZif payload / BUILD_FORMAT 1.1 → Task 6.
- Offline registry / aliases / ambiguity / unknown → Tasks 3, 4.
- Resolution precedence / optional network boundary → Task 4.
- Bundled lunar/tzdata calendar authority → Task 2.
- `runtime_info` 1.1 / compatibility diagnostics → Task 5.
- Clean `python -S`, no-network, environment-pollution qualification → Task 7.
- Modular/bundle parity → Task 9.
- 5 MiB guard / reproducibility / integrity → Task 8.
- Temporary Astralium-first rollback to Birth Data first → Task 10.
- Full regression / Python 3.9 / no release or Stable promotion → Task 11.

## Execution Boundary

This plan authorizes implementation only after the human explicitly chooses an execution mode. It does not itself authorize merging the future feature branch into `main`, creating a release, moving `v1.3.0`, or promoting any Experimental capability.
