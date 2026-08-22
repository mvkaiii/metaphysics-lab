# Natal Chart Foundation 01 — Birth, Location & Time Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立可追溯、fail-closed 的出生資料解析、出生地解析與時間 view 基礎層，讓後續 Bazi / Ziwei Natal Builder 只接收結構化且精度足夠的輸入。

**Architecture:** 新增 `engine/birth/`，把自然語言抽取之後的 structured birth fields 正規化；Location Resolver 透過 provider protocol 解析 coordinates，並用 offline timezone polygon lookup 得到 IANA timezone；Calendar Resolver 仍只接 structured civil datetime + timezone；true-solar view 在 birth layer 計算，不修改 CalendarContext。

**Tech Stack:** Python 3.9-compatible syntax、`geopy==2.5.0`、`timezonefinder==8.2.0`、`lunar-python==1.4.8`、`tzdata==2026.3`、stdlib `zoneinfo` / `dataclasses` / `datetime` / `math` / `typing.Protocol`。

**Spec:** `docs/superpowers/specs/2026-08-22-Natal-Chart-Foundation-設計.md`

## Global Constraints

- 不解析自由文字命理內容；LLM/上游先抽取欄位，本層只驗證 structured payload。
- 不補假時間、假地點或假 timezone。
- `reported_civil_time` 永久保留。
- Location Provider 可以是 network-backed，但 deterministic chart math 不依賴網路；測試使用 fake provider。
- `timezonefinder==8.2.0` 固定用於 coordinates → IANA timezone，避免 Python 3.9 support 漂移。
- true-solar profile 第一版 `true-solar-noaa-gamma-v1`，使用 longitude correction + equation-of-time；結果 Experimental。
- Calendar validation metadata 必須完整傳遞。

---

### Task 1: Add Birth package, dependency pins, and capability contract

**Files:**
- Create: `engine/birth/__init__.py`
- Create: `engine/birth/errors.py`
- Create: `engine/birth/capabilities.py`
- Modify: `requirements.txt`
- Modify: `tests/test_engine_module_layout.py`
- Create: `tests/test_birth_capabilities.py`

**Interfaces:**
- Produces: `BirthFoundationError(code: str, message: str, details: dict | None = None)`
- Produces: `engine.birth.capabilities.get_capability(capability_id: str) -> dict`
- Produces capability ids: `birth.input_resolution`, `birth.location_resolution`, `birth.true_solar_time`

- [ ] **Step 1: Write failing package/capability tests**

```python
import unittest
from engine.birth.capabilities import get_capability

class BirthCapabilityTests(unittest.TestCase):
    def test_phase2c0_birth_capabilities_start_without_false_promotion(self):
        expected = {
            'birth.input_resolution': ('implemented', 'experimental', 'on_demand', '1.0-exp'),
            'birth.location_resolution': ('implemented', 'experimental', 'on_demand', '1.0-exp'),
            'birth.true_solar_time': ('implemented', 'experimental', 'on_demand', '1.0-exp'),
        }
        for capability_id, state in expected.items():
            cap = get_capability(capability_id)
            self.assertEqual(
                (cap['implementation'], cap['maturity'], cap['routing'], cap['rule_version']),
                state,
            )
```

- [ ] **Step 2: Run tests and verify import/capability failure**

Run:

```bash
python -m unittest tests.test_birth_capabilities tests.test_engine_module_layout -v
```

Expected: FAIL because `engine.birth` does not exist.

- [ ] **Step 3: Add exact dependency pins**

`requirements.txt` must become:

```text
lunar-python==1.4.8
tzdata==2026.3
geopy==2.5.0
timezonefinder==8.2.0
```

- [ ] **Step 4: Implement package/error/capability registry**

```python
class BirthFoundationError(ValueError):
    def __init__(self, code, message, details=None):
        self.code = code
        self.details = details or {}
        super().__init__(message)
```

Registry entries must include `id`, `implementation`, `maturity`, `routing`, `rule_version`, `module`, `dependencies`.

- [ ] **Step 5: Run focused tests**

```bash
python -m unittest tests.test_birth_capabilities tests.test_engine_module_layout -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add requirements.txt engine/birth tests/test_birth_capabilities.py tests/test_engine_module_layout.py
git commit -m "feat: add birth foundation capability shell"
```

---

### Task 2: Define immutable birth input and precision models

**Files:**
- Create: `engine/birth/models.py`
- Create: `tests/test_birth_models.py`

**Interfaces:**
- Produces: `Sex(str, Enum)` values `male`, `female`
- Produces: `BirthDateInput(value: date, precision: TimePrecision)`
- Produces: `BirthTimeInput(start: time, end: time | None, precision: TimePrecision, label: str | None)`
- Produces: `BirthPlaceInput(label: str)`
- Produces: `BirthInput(sex, birth_date, birth_time, birth_place, calendar_kind='gregorian')`
- Produces: `BirthInputCandidate(input: BirthInput, reason: str)`
- Produces: `BirthInputResolution(ok, input, candidates, missing_fields, error_code)`

- [ ] **Step 1: Write model serialization tests**

```python
def test_birth_input_preserves_reported_values():
    birth = BirthInput(
        sex=Sex.MALE,
        birth_date=BirthDateInput(date(1984, 3, 13), TimePrecision.DAY),
        birth_time=BirthTimeInput(time(19, 20), None, TimePrecision.HOUR, '19:20'),
        birth_place=BirthPlaceInput('台北市'),
    )
    payload = birth.to_dict()
    assert payload['birth_time']['label'] == '19:20'
    assert payload['birth_place']['label'] == '台北市'
```

- [ ] **Step 2: Run and verify failure**

```bash
python -m unittest tests.test_birth_models -v
```

Expected: FAIL because models are missing.

- [ ] **Step 3: Implement frozen dataclasses and deterministic `to_dict()` methods**

Use `@dataclass(frozen=True)` for all value objects. Do not accept naive `datetime` here; date/time are reported local civil components until Location Resolver supplies timezone.

- [ ] **Step 4: Add invariants**

`BirthTimeInput` must reject `end < start` for same-day ranges and reject second-level precision beyond the current contract. `BirthPlaceInput` must reject blank labels. `calendar_kind` v1 accepts only `gregorian` for Mode A.

- [ ] **Step 5: Run focused tests**

```bash
python -m unittest tests.test_birth_models -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add engine/birth/models.py tests/test_birth_models.py
git commit -m "feat: define birth input models"
```

---

### Task 3: Implement structured Birth Input Resolver and Precision Gate

**Files:**
- Create: `engine/birth/input_resolution.py`
- Create: `tests/test_birth_input_resolution.py`

**Interfaces:**
- Consumes: `engine.calendar.precision.TimePrecision`, `assess_precision()`
- Consumes: `BirthInput*` models
- Produces: `resolve_birth_input(payload: Mapping[str, object], *, target: str) -> BirthInputResolution`
- Supported targets: `bazi_static`, `bazi_natal`, `ziwei_natal`

- [ ] **Step 1: Write missing-field and ambiguity tests**

```python
def test_complete_mode_a_input_resolves():
    result = resolve_birth_input({
        'sex': 'male',
        'birth_date': '1984-03-13',
        'birth_time': '19:20',
        'birth_place': '台北市',
    }, target='ziwei_natal')
    assert result.ok is True
    assert result.input.birth_place.label == '台北市'


def test_missing_sex_blocks_full_natal_but_not_static_candidate():
    result = resolve_birth_input({
        'birth_date': '1984-03-13',
        'birth_time': '19:20',
        'birth_place': '台北市',
    }, target='ziwei_natal')
    assert result.ok is False
    assert result.missing_fields == ('sex',)


def test_time_range_is_not_collapsed_to_midpoint():
    result = resolve_birth_input({
        'sex': 'female',
        'birth_date': '1990-05-06',
        'birth_time_range': ['20:00', '22:00'],
        'birth_place': '高雄市',
    }, target='ziwei_natal')
    assert result.ok is False
    assert result.error_code == 'ambiguous_birth_time'
```

- [ ] **Step 2: Run and verify failure**

```bash
python -m unittest tests.test_birth_input_resolution -v
```

Expected: FAIL because resolver is missing.

- [ ] **Step 3: Implement exact parsing contract**

Accepted structured keys:

```text
sex: male | female
birth_date: YYYY-MM-DD
birth_time: HH:MM
birth_time_range: [HH:MM, HH:MM]
birth_place: non-empty string
calendar_kind: gregorian (optional, default)
```

Do not parse words such as `晚上七點`; that stays an upstream LLM responsibility.

- [ ] **Step 4: Map target to minimum requirements**

`bazi_static`: date + time sufficient to determine pillars; sex optional if Da Yun not requested.

`bazi_natal` / `ziwei_natal`: sex + exact day + time candidate that can ultimately resolve to one effective chart + place.

Return allowed actions `('ask', 'keep_candidates', 'downgrade')` on ambiguity.

- [ ] **Step 5: Run focused + Calendar precision regression**

```bash
python -m unittest tests.test_birth_input_resolution tests.test_calendar_precision -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add engine/birth/input_resolution.py tests/test_birth_input_resolution.py
git commit -m "feat: add birth input precision gate"
```

---

### Task 4: Implement LocationProvider protocol and deterministic location result model

**Files:**
- Modify: `engine/birth/models.py`
- Create: `engine/birth/location.py`
- Create: `tests/test_birth_location.py`

**Interfaces:**
- Produces: `GeocodeCandidate(name, latitude, longitude, country_code, raw_id)`
- Produces: `ResolvedBirthPlace(canonical_name, latitude, longitude, timezone, provider_name, provider_version, resolution_status)`
- Produces Protocol: `LocationProvider.geocode(query: str) -> tuple[GeocodeCandidate, ...]`
- Produces: `resolve_birth_place(place: BirthPlaceInput, provider: LocationProvider) -> ResolvedBirthPlace`
- Produces: `NominatimLocationProvider(user_agent: str, timeout_seconds: float = 10.0)`

- [ ] **Step 1: Write fake-provider unit tests**

```python
class FakeProvider:
    def geocode(self, query):
        return (GeocodeCandidate('Taipei City, Taiwan', 25.0375, 121.5637, 'tw', 'fake:1'),)


def test_unique_place_resolves_coordinates_and_iana_timezone():
    result = resolve_birth_place(BirthPlaceInput('台北市'), FakeProvider())
    assert result.timezone == 'Asia/Taipei'
    assert result.provider_name == 'fake'
```

Also test zero candidates → `location_not_resolved`, two materially distinct candidates → `ambiguous_birth_place`.

- [ ] **Step 2: Run and verify failure**

```bash
python -m unittest tests.test_birth_location -v
```

Expected: FAIL.

- [ ] **Step 3: Implement provider protocol and timezone lookup**

Use `timezonefinder.TimezoneFinder().timezone_at(lng=..., lat=...)`; if it returns `None`, raise `timezone_not_resolved`.

- [ ] **Step 4: Implement Nominatim adapter without leaking raw address into canonical model**

Use `geopy.geocoders.Nominatim(user_agent=user_agent, timeout=timeout_seconds)` and `exactly_one=False`, `limit=5`. Convert provider results into minimal `GeocodeCandidate` fields; retain only provider raw id/string needed for provenance, not full street address.

- [ ] **Step 5: Add provider-offline behavior test**

Network exceptions from `geopy` must become `location_provider_unavailable`, not an empty-success result.

- [ ] **Step 6: Run focused tests**

```bash
python -m unittest tests.test_birth_location -v
```

Expected: PASS with fake provider; no live network required.

- [ ] **Step 7: Commit**

```bash
git add engine/birth/models.py engine/birth/location.py tests/test_birth_location.py
git commit -m "feat: add birth location resolution"
```

---

### Task 5: Add Birth → Calendar orchestration with historical timezone validation

**Files:**
- Create: `engine/birth/calendar_adapter.py`
- Create: `tests/test_birth_calendar_integration.py`

**Interfaces:**
- Consumes: exact `BirthInput`, `ResolvedBirthPlace`
- Produces: `resolve_birth_calendar(input: BirthInput, location: ResolvedBirthPlace) -> CalendarResolution`

- [ ] **Step 1: Write Taipei and DST edge tests**

Taipei vector:

```python
resolution = resolve_birth_calendar(birth_input_1984_03_13_1920, taipei_location)
assert resolution.ok
assert resolution.context.input.timezone == 'Asia/Taipei'
assert resolution.context.input.civil_datetime == '1984-03-13T19:20:00'
```

DST ambiguous/nonexistent tests should use an IANA timezone already covered by `engine/calendar/timezone.py` and assert existing Calendar error codes are preserved.

- [ ] **Step 2: Run and verify failure**

```bash
python -m unittest tests.test_birth_calendar_integration -v
```

- [ ] **Step 3: Implement adapter as a thin wrapper**

Do not modify `engine/calendar/resolver.py` semantics. Construct `CalendarInput` from reported local date/time and resolved IANA timezone, then call existing Calendar Resolver.

- [ ] **Step 4: Propagate validation unchanged**

Assert `validated`, `boundary_caution`, `boundary_conflict`, `out_of_validated_range` pass through. The adapter must not rename them to generic success/failure.

- [ ] **Step 5: Run Calendar regression**

```bash
python -m unittest discover -s tests -p 'test_calendar*.py' -v
python -m unittest tests.test_birth_calendar_integration -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add engine/birth/calendar_adapter.py tests/test_birth_calendar_integration.py
git commit -m "feat: connect birth input to calendar resolver"
```

---

### Task 6: Implement versioned true-solar time profile and time views

**Files:**
- Create: `engine/birth/time_views.py`
- Modify: `engine/birth/models.py`
- Create: `tests/test_birth_time_views.py`

**Interfaces:**
- Produces: `TrueSolarTimeProfile(profile_id, rule_version, longitude_correction, equation_of_time)`
- Produces: `TimeView(kind, local_datetime, adjustment_minutes, profile_id, rule_version, calculation_basis, boundary_effect, provenance)`
- Produces: `BirthTimeViews(reported_civil, normalized_civil, true_solar)`
- Produces: `build_birth_time_views(calendar: CalendarContext, location: ResolvedBirthPlace, profile=TRUE_SOLAR_NOAA_GAMMA_V1) -> BirthTimeViews`

- [ ] **Step 1: Write fixed equation-of-time vectors**

Use the NOAA fractional-year approximation:

```python
gamma = 2 * pi / 365 * (day_of_year - 1 + (hour - 12) / 24)
eot = 229.18 * (
    0.000075
    + 0.001868 * cos(gamma)
    - 0.032077 * sin(gamma)
    - 0.014615 * cos(2 * gamma)
    - 0.040849 * sin(2 * gamma)
)
```

Longitude correction in minutes:

```python
standard_meridian = utc_offset_hours * 15.0
longitude_minutes = 4.0 * (longitude - standard_meridian)
true_solar = normalized_civil + timedelta(minutes=longitude_minutes + eot)
```

Test Taipei 1984-03-13 19:20 UTC+8: the adjustment must be negative and the resulting time remain in 戌時; exact expected second-level value is frozen from the formula in the test, not from Astralium text rounding.

- [ ] **Step 2: Write material boundary test**

Construct a longitude/date/time vector whose correction crosses 19:00 so `boundary_effect` records `hour_branch_changed=True`; do not silently choose the corrected branch as Bazi or Ziwei policy here.

- [ ] **Step 3: Run and verify failure**

```bash
python -m unittest tests.test_birth_time_views -v
```

- [ ] **Step 4: Implement pure functions**

Create:

```python
def equation_of_time_minutes(dt: datetime) -> float: ...
def standard_meridian_degrees(dt: datetime) -> float: ...
def true_solar_adjustment_minutes(dt: datetime, longitude: float) -> float: ...
```

`dt` must be timezone-aware. Use the actual offset at the birth instant, including historical DST.

- [ ] **Step 5: Preserve source time and detect day/hour crossing**

`reported_civil` comes from the user input label/value; `normalized_civil` comes from `CalendarContext`; `true_solar` is a third view. Record `date_changed` and `hour_branch_changed` in `boundary_effect`.

- [ ] **Step 6: Run focused tests**

```bash
python -m unittest tests.test_birth_time_views -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add engine/birth/time_views.py engine/birth/models.py tests/test_birth_time_views.py
git commit -m "feat: add true solar birth time views"
```

---

### Task 7: Workstream 01 acceptance and live-provider qualification boundary

**Files:**
- Create: `tools/qualify_birth_location_provider.py`
- Create: `qualification/birth/location-provider-summary.json`
- Create: `tests/test_birth_location_qualification.py`

**Interfaces:**
- Tool accepts explicit public place labels only, never private birth records.
- Summary stores provider name/version, query labels, result status, coordinates rounded to 4 decimals, timezone id, timestamp, pass/fail counts.

- [ ] **Step 1: Add deterministic qualification-summary schema test**

Ensure no fields named `full_address`, `birth_datetime`, `person_name`, `raw_response` are allowed.

- [ ] **Step 2: Implement live qualification tool**

Public cases:

```text
台北市, 台灣
高雄市, 台灣
Tokyo, Japan
New York, NY, USA
London, UK
```

Require unique city-level resolution and non-empty IANA timezone. A provider outage must exit nonzero with marker `LOCATION_PROVIDER_INFRA_FAIL`, not `LOCATION_ALGORITHM_FAIL`.

- [ ] **Step 3: Run deterministic focused suites**

```bash
python -m unittest \
  tests.test_birth_models \
  tests.test_birth_input_resolution \
  tests.test_birth_location \
  tests.test_birth_calendar_integration \
  tests.test_birth_time_views \
  tests.test_birth_location_qualification -v
```

- [ ] **Step 4: Run Calendar regression and Python 3.9 syntax gate**

```bash
python -m unittest discover -s tests -p 'test_calendar*.py' -v
python - <<'PY'
import ast
from pathlib import Path
for path in list(Path('engine/birth').rglob('*.py')) + list(Path('tests').glob('test_birth*.py')):
    ast.parse(path.read_text(encoding='utf-8'), feature_version=(3, 9))
print('PYTHON39_BIRTH_PASS')
PY
```

- [ ] **Step 5: Commit workstream evidence scaffolding**

```bash
git add tools/qualify_birth_location_provider.py qualification/birth/location-provider-summary.json tests/test_birth_location_qualification.py
git commit -m "test: qualify birth location foundation"
```

Workstream 01 is accepted only if deterministic tests pass and any live-provider failure is clearly classified as infrastructure rather than chart math.