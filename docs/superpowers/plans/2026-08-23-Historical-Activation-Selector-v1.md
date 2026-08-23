# Historical Activation Selector v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增 `historical.activation_selector` deterministic capability，逐年計算最近 10 個已完成 Li-Chun flow-year periods 的八字結構 activation，透明產生 Tier 1/2/3 evidence、rank vector、真正 Top 4 high + Bottom 1 control。

**Architecture:** 新增 `engine/historical/` 專責 historical selector，避免把研究性 ranking 規則塞進 Bazi calendar/natal engine。Selector 只消費 Project natal structured facts與既有 `solar_term_time` / `flow_year_pillar`; relation tables與 suppression/ranking profile都版本化。v1 selection authority 是 Bazi；Ziwei只輸出 selected-year context/support metadata，不可改 canonical ranking。

**Tech Stack:** Python stdlib dataclasses/datetime/hashlib/json、existing `engine.bazi.calendar`、existing Project natal JSON、`unittest`。

**Spec:** `docs/superpowers/specs/2026-08-23-Historical-Activation-Selector-v1-設計.md` + Progressive Case amendment.

## Global Constraints

- Capability id = `historical.activation_selector`; profile = `historical-activation-bazi-v1`; rule version = `1.0-exp`; maturity = `experimental`; routing = `on_demand`.
- Selector never accepts known-event years, preferred years, event keywords, manual rank override, or any 05–08 data.
- Ranking unit is Bazi flow-year period from Li-Chun to next Li-Chun; only fully completed periods are eligible.
- Same normalized natal + same `as_of_date` + same timezone/profile must produce byte-equivalent selector output/digest.
- Tier names are exactly Tier 1 strongest, Tier 2 medium, Tier 3 auxiliary. Tier is activation, not auspiciousness.
- v1 relation tables are frozen exactly as the approved spec: six clashes, six combinations, three harmonies, three meetings, punishment sets, harms, breaks, heavenly-stem combinations.
- v1 excludes heavenly-stem clashes, generic five-element generation/control, standalone ten-god strength, favorable/unfavorable gods, pattern strength scores and spirits.
- Suppression prevents one structural fact from inflating multiple lower-tier counts.
- Canonical selection is true Top 4 + true Bottom 1 after deterministic ranking; no spacing, cycle coverage, contamination or UX override.
- Control quality = `strong_control | acceptable_control | relative_low`; `relative_low` must never imply a stable year.
- Ziwei v1 may enrich selected-year evidence only; it cannot change canonical selection.
- No maturity promotion from event matching.
- Every production change follows TDD RED → GREEN.

---

## File Map

**Create:**
- `engine/historical/__init__.py`
- `engine/historical/capabilities.py`
- `engine/historical/relations.py`
- `engine/historical/models.py`
- `engine/historical/selector.py`
- `tests/test_historical_activation_relations.py`
- `tests/test_historical_activation_selector.py`
- `tests/test_historical_activation_capabilities.py`

**Modify:**
- `engine/distribution/manifest.py` — include historical registry.
- `engine/distribution/constants.py` — add `prepare_historical_calibration` action if not added by plan 1.
- `engine/distribution/runtime.py` — route selector action.
- `tests/test_distribution_runtime_info.py` — capability/action manifest.
- `core/命理推導計算規則.md` — deterministic selector boundary.
- `dist/ai/*` — generated after all implementation.

---

### Task 1: Frozen Relation Profile

**Files:** create `engine/historical/relations.py`, `tests/test_historical_activation_relations.py`.

**Interfaces:** frozen canonical unordered sets:

```python
CLASH_PAIRS = frozenset({frozenset(("子", "午")), ...})
COMBINATION_PAIRS = frozenset(...)
THREE_HARMONY_SETS = frozenset({frozenset(("申", "子", "辰")), ...})
THREE_MEETING_SETS = frozenset(...)
FULL_PUNISHMENT_SETS = frozenset({frozenset(("寅", "巳", "申")), frozenset(("丑", "戌", "未"))})
PAIR_PUNISHMENTS = frozenset({frozenset(("子", "卯"))})
SELF_PUNISHMENTS = frozenset(("辰", "午", "酉", "亥"))
HARM_PAIRS = frozenset(...)
BREAK_PAIRS = frozenset(...)
STEM_COMBINATION_PAIRS = frozenset(...)
```

- [ ] **Step 1: RED tests** assert exact tables, symmetry through unordered representation, and that unsupported relations are absent.
- [ ] **Step 2: Verify RED** module missing.
- [ ] **Step 3: GREEN** implement constants only; no interpretation.
- [ ] **Step 4: GREEN** `python -m unittest tests.test_historical_activation_relations -v`.
- [ ] **Step 5: Commit** `feat: freeze historical activation relation profile`.

### Task 2: Selector Models and Rank Vector

**Files:** create `engine/historical/models.py`, add tests in `test_historical_activation_selector.py`.

**Interfaces:**

```python
@dataclass(frozen=True)
class ActivationEvidence:
    evidence_id: str
    tier: int
    relation_family: str
    source_scope: str
    target_scope: str
    participants: tuple[str, ...]
    metadata: Mapping[str, object]

@dataclass(frozen=True, order=True)
class ActivationRankVector:
    tier1_family_count: int
    tier1_evidence_count: int
    cross_layer_tier1: int
    tier2_family_count: int
    tier2_evidence_count: int
    tier3_family_count: int
    tier3_evidence_count: int
```

Sort key used for descending rank must preserve the field priority above; final deterministic tie-break is label year descending or ascending exactly as fixed in spec (choose one and test it; v1 uses most recent label year as final tie-break to keep deterministic UX).

- [ ] **Step 1: RED** model validation tests reject tier outside 1–3 and blank relation family; ranking tests prove Tier 1 family count outranks any Tier 2 count.
- [ ] **Step 2: Verify RED**.
- [ ] **Step 3: GREEN** minimal frozen models and serialization helpers.
- [ ] **Step 4: GREEN** focused tests.
- [ ] **Step 5: Commit** `feat: add historical activation evidence models`.

### Task 3: Completed Li-Chun Window and Decadal Resolution

**Files:** create/modify `engine/historical/selector.py`, `tests/test_historical_activation_selector.py`.

**Interfaces:**

```python
def completed_flow_year_periods(as_of: datetime, count: int = 10) -> tuple[dict, ...]
def resolve_decadal_for_period(project_bazi: Mapping[str, object], period: Mapping[str, object]) -> dict
```

Each period returns `label_year`, `period_start`, `period_end`, `flow_year_pillar`. The period is eligible only if `period_end <= as_of`.

- [ ] **Step 1: RED**: `2026-08-23 Asia/Taipei` returns labels 2016–2025; `2026-01-15` excludes unfinished 2025 and shifts window backward; boundaries equal `solar_term_time(year,"立春",tz)`.
- [ ] **Step 2: RED** decadal resolution selects stored period covering a period midpoint and emits boundary metadata when a decadal transition occurs inside the flow-year interval.
- [ ] **Step 3: Verify RED**.
- [ ] **Step 4: GREEN** use existing solar-term engine; never approximate Feb 4 by date-only constants.
- [ ] **Step 5: GREEN** focused tests.
- [ ] **Step 6: Commit** `feat: resolve historical flow year window`.

### Task 4: Tier 1 Evidence and Suppression

**Files:** modify `selector.py`, tests.

**Tier 1 families:** `decadal_boundary`, `sui_yun_bing_lin`, `natal_pillar_repeat`, `branch_clash_natal`, `branch_clash_decadal`, `completes_three_harmony`, `completes_three_meeting`, `completes_three_punishment`.

- [ ] **Step 1: RED tests** one fixture per family using synthetic natal/decadal facts. Assert canonical pattern evidence is counted once even when duplicate branches exist.
- [ ] **Step 2: RED suppression tests**: sui-yun-bing-lin suppresses lower stem/branch repeat for the same decadal target; natal full-pillar repeat suppresses its stem/branch repeat for that natal component.
- [ ] **Step 3: Verify RED**.
- [ ] **Step 4: GREEN** implement Tier 1 evidence builders with stable evidence ids and participants.
- [ ] **Step 5: GREEN** focused tests.
- [ ] **Step 6: Commit** `feat: calculate tier 1 historical activation`.

### Task 5: Tier 2 and Tier 3 Evidence

**Files:** modify `selector.py`, tests.

**Tier 2:** branch six-combination; half-three-harmony; half-three-meeting; pairwise punishment / self-punishment; branch repeat; heavenly-stem five-combination.

**Tier 3:** six harm; six break; heavenly-stem repeat.

- [ ] **Step 1: RED tests** each family; ensure half-pattern evidence is suppressed when the same year completes the full Tier 1 pattern.
- [ ] **Step 2: Verify RED**.
- [ ] **Step 3: GREEN** implement lower-tier builders and suppression map.
- [ ] **Step 4: GREEN** focused tests.
- [ ] **Step 5: Commit** `feat: calculate lower-tier historical activation`.

### Task 6: Rank, Top 4, Bottom 1, Control Quality

**Files:** modify `selector.py`, tests.

**Interfaces:**

```python
def select_historical_activation(payload: Mapping[str, object]) -> dict
```

Output includes all 10 ranked periods, each evidence list and rank vector, `high_years[4]`, `control_year`, `control_quality`, `major_cycle_coverage`, `profile_id`, `rule_version`, `selection_digest`.

- [ ] **Step 1: RED ranking tests** prove true Top 4 preserved even when consecutive and even when all are in one decadal cycle; contamination fields are not accepted as input and cannot change selection.
- [ ] **Step 2: RED control tests**:
  - `strong_control`: bottom has no Tier 1/2 and materially fewer Tier 3 than neighbors.
  - `acceptable_control`: bottom has no Tier 1 but some Tier 2.
  - `relative_low`: bottom still has Tier 1 or no meaningful separation from the window.
- [ ] **Step 3: RED digest test** identical input produces identical digest; one natal pillar change changes digest.
- [ ] **Step 4: Verify RED**.
- [ ] **Step 5: GREEN** rank lexicographically by rank vector, apply only documented deterministic tie-break, select indices 0:4 and last, classify control, serialize canonical selection and hash it.
- [ ] **Step 6: GREEN** focused selector suite.
- [ ] **Step 7: Commit** `feat: select canonical historical activation years`.

### Task 7: Capability and Distribution Runtime Integration

**Files:** create `engine/historical/capabilities.py`, `__init__.py`; modify `engine/distribution/manifest.py`, `runtime.py`, `constants.py`, runtime tests.

- [ ] **Step 1: RED capability tests** assert manifest contains:

```python
{
  "id": "historical.activation_selector",
  "implementation": "implemented",
  "maturity": "experimental",
  "routing": "on_demand",
  "rule_version": "1.0-exp",
  "profile_id": "historical-activation-bazi-v1",
  "module": "engine.historical.selector",
}
```

- [ ] **Step 2: RED runtime test** `prepare_historical_calibration` returns selector result and rejects payloads containing forbidden ranking hints (`preferred_years`, `known_event_years`, `event_keywords`, `manual_rank_override`).
- [ ] **Step 3: Verify RED**.
- [ ] **Step 4: GREEN** add historical registry to manifest, runtime route, structured `DistributionError` translation.
- [ ] **Step 5: GREEN** capability/runtime tests.
- [ ] **Step 6: Commit** `feat: expose historical activation selector`.

### Task 8: Ziwei Supporting Context Without Ranking Authority

**Files:** modify `engine/distribution/calibration.py` or add a narrow adapter in `engine/historical/selector.py`; tests.

- [ ] **Step 1: RED** assert selected-year output may include `ziwei_support` derived from existing annual context, but removing/changing that support does not alter `high_years`, `control_year`, or `selection_digest` of the Bazi canonical selection.
- [ ] **Step 2: Verify RED**.
- [ ] **Step 3: GREEN** attach optional support after selection, clearly classified `support_only`, maturity/provenance preserved.
- [ ] **Step 4: GREEN** tests.
- [ ] **Step 5: Commit** `feat: attach ziwei support to historical selection`.

### Task 9: Rules Documentation, Distribution Rebuild, Full Verification

**Files:** modify `core/命理推導計算規則.md`; regenerate `dist/ai/*` after plan 1 and plan 2 code are both green.

- [ ] **Step 1: RED doc assertions** for capability id, profile, Tier 1/2/3 direction, Li-Chun period, Top4+Bottom1 no overrides, Bazi selection authority and Ziwei support-only.
- [ ] **Step 2: GREEN docs**.
- [ ] **Step 3: Focused selector suite**: `python -m unittest tests.test_historical_activation_relations tests.test_historical_activation_selector tests.test_historical_activation_capabilities tests.test_distribution_runtime_info -v`.
- [ ] **Step 4: Build distribution** `python tools/build_ai_distribution.py --output-dir dist/ai` then `--check`.
- [ ] **Step 5: Full regression** `python -m unittest discover -s tests -v`.
- [ ] **Step 6: Compile** `python -m compileall engine tools dist/ai/metaphysics_lab.py`.
- [ ] **Step 7: Commit** `build: publish historical activation selector runtime`.
