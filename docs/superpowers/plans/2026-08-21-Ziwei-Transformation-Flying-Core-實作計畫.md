# Ziwei Transformation & Flying Core v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 依核准的 Phase 2A spec 建立可重現、可驗證、可追溯的紫微十干四化核心、宮干／運限飛化核心、跨 layer Composition 與 qualification / promotion gates，且不啟用流月／流日／流時四化或流曜。

**Architecture:** 四化規則、命盤基準資料、飛化與 Composition 分成獨立 pure modules。`Transformation Core` 只做天干→四化；`Flying Core` 只使用已校驗 natal star locations 產生 edges；`Composition` 只保存不同 scope 的 layer 並提供 readonly query，不做吉凶或權重。Capability 在 internal gates 通過後先進 `implemented / experimental / on_demand`，只有 external qualification、regression、privacy 與 main post-merge gates 全部通過才升 `stable / on_demand`。

**Tech Stack:** Python 3.9+、stdlib `dataclasses` / `enum` / `types.MappingProxyType` / `typing` / `unittest`、既有 `engine.ziwei` package；無新增 runtime dependency。

**Spec:** `docs/superpowers/specs/2026-08-21-Ziwei-Transformation-Flying-Core-設計.md`

## Global Constraints

- Spec 已由使用者於 2026-08-21 核准；implementation 不得自行擴 scope。
- 第一版 profile id 固定 `metaphysics-lab-common-v1`，不得命名為 standard / canonical / 唯一標準。
- Public qualification source 固定 `SylarLong/iztro` revision `814b77e6371e1050cac31bbf674db3c3138fcfde`；它只作 qualification，不是 runtime dependency。
- Flying target basis v1 只允許 `natal_star_location`；不得重新安星。
- `PalaceStemSource` 與 `CycleStemSource` 必須分型；cycle source 的 `geometric_relation` 必須為 `None`。
- 底層 relation 只允許 `same_palace` / `opposite_palace_incoming` / `normal`；`↑/↓` 是 presentation mapping。
- 本命十二宮 graph 必須 exactly 48 edges；每個可執行 cycle layer 必須 exactly 4 transformations + 4 flying edges。
- Different scopes coexist; same `LayerIdentity` conflicts fail closed。禁止 last-write-wins。
- `monthly/daily/hourly transformations` 在 Phase 2A 永遠 `unavailable`，reason 固定 `fine_cycle_stem_resolver_not_enabled`。
- Small limit v1 只作 context，不產生 transformation layer。
- 不新增四化 scoring、resonance 強弱、final transformation state 或 AI interpretation。
- 私人 Astralium raw chart、出生資料、完整十二宮 fixture 不得 commit；private qualification 只保存 aggregate evidence。
- 任何 RED 未證明就不得進 GREEN；任何 Gate FAIL 立即停止並查 root cause。
- 不修改 Bazi implementation、Calendar Resolver semantics、Qimen、moving stars、Ziwei fine-cycle stem policy。
- Feature branch 必須從本 design branch 核准 plan 的 exact head 建立；不得直接在 `main` 寫 implementation。
- 所有 production code 必須可在 Python 3.9 parse；不得使用 PEP 604 `X | None` type syntax。

---

## File Map

### 新增 production modules

- `engine/ziwei/errors.py` — Phase 2A stable error-code exception。
- `engine/ziwei/models.py` — enums / frozen dataclasses / immutable contracts；不做 orchestration。
- `engine/ziwei/basis.py` — `StarLocationRecord[]` / `PalaceStemRecord[]` 驗證與 immutable index materialization。
- `engine/ziwei/transformation_profiles.py` — versioned 10-stem rule data + profile validation。
- `engine/ziwei/transformations.py` — `heavenly_stem + profile_id -> TransformationSet`。
- `engine/ziwei/flying.py` — geometry、4-edge cycle flying、48-edge natal graph、presentation mapping。
- `engine/ziwei/composition.py` — layer construction、identity conflict、availability、readonly views。

### 修改 production modules

- `engine/ziwei/common.py` — 新增 `validate_palace()` 與 single-source `opposite_palace()`。
- `engine/ziwei/capabilities.py` — Phase 2A capability lifecycle；fine-cycle capability 只占位為 planned。
- `engine/ziwei/__init__.py` — 僅 export Phase 2A core public contracts；不得 export 不存在的 fine-cycle transformation API。

### 新增 tests / synthetic fixture

- `tests/ziwei_phase2a_fixtures.py` — 只放 synthetic chart / records；不含私人盤面。
- `tests/test_ziwei_phase2a_models.py`
- `tests/test_ziwei_basis.py`
- `tests/test_ziwei_transformations.py`
- `tests/test_ziwei_flying.py`
- `tests/test_ziwei_composition.py`
- `tests/test_ziwei_phase2a_capabilities.py`
- `tests/test_ziwei_phase2a_qualification_tools.py`

### 新增 qualification tooling / evidence

- `tools/qualify_ziwei_phase2a_public.py` — 解析 pinned iztro `heavenlyStems.ts` 並核對 40 個四化值。
- `tools/qualify_ziwei_phase2a_private.py` — 接受 repo 外 private normalized JSON，輸出 aggregate evidence；不寫 raw values。
- `qualification/ziwei/phase2a/public-iztro-814b77e6.json` — 40/40 public evidence。
- `qualification/ziwei/phase2a/private-astralium-summary.json` — 只含 digest、counts、status、timestamp 與非敏感 mismatch count。

### 最終同步文件

- `README.md`
- `VERSION.md`
- `CHANGELOG.md`
- `docs/架構說明.md`
- `core/命理分析作業規範.md` 僅在 capability 描述需要同步時修改；不得改盲判／事件校準規則。

---

### Task 1: Error Contract 與完整 Immutable Models

**Files:**
- Create: `engine/ziwei/errors.py`
- Create: `engine/ziwei/models.py`
- Test: `tests/test_ziwei_phase2a_models.py`

**Interfaces:**
- Produces: `ZiweiPhase2AError`
- Produces all shared model types used by later tasks。

- [ ] **Step 1: Write RED model tests**

```python
# tests/test_ziwei_phase2a_models.py
import unittest
from dataclasses import FrozenInstanceError

from engine.ziwei.errors import ZiweiPhase2AError
from engine.ziwei.models import (
    ChartIdentity,
    GeometricRelation,
    Transformation,
    TransformationType,
)


class ZiweiPhase2AModelTests(unittest.TestCase):
    def test_error_exposes_stable_code_and_details(self):
        err = ZiweiPhase2AError("invalid_palace", "bad palace", {"palace": "X"})
        self.assertEqual(err.code, "invalid_palace")
        self.assertEqual(err.details, {"palace": "X"})

    def test_transformation_values_are_stable(self):
        self.assertEqual([item.value for item in TransformationType], ["祿", "權", "科", "忌"])

    def test_transformation_is_immutable(self):
        item = Transformation(TransformationType.LU, "廉貞", 0)
        with self.assertRaises(FrozenInstanceError):
            item.star = "破軍"

    def test_geometric_relation_is_neutral(self):
        self.assertEqual(
            {item.value for item in GeometricRelation},
            {"same_palace", "opposite_palace_incoming", "normal"},
        )

    def test_chart_id_is_opaque_string(self):
        chart = ChartIdentity("chart-fixture-A", "natal", "synthetic-v1")
        self.assertEqual(chart.chart_id, "chart-fixture-A")
```

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_ziwei_phase2a_models -v
```

Expected: FAIL with missing `engine.ziwei.errors` or `engine.ziwei.models`。若是其他失敗，先修 test setup。

- [ ] **Step 3: Implement Python 3.9-safe error class**

```python
# engine/ziwei/errors.py
from __future__ import annotations

from typing import Any, Mapping, Optional


class ZiweiPhase2AError(ValueError):
    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self.code = code
        self.details = dict(details or {})
        super().__init__(message)
```

- [ ] **Step 4: Implement complete shared model contract**

```python
# engine/ziwei/models.py
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Optional, Tuple, Union


class TransformationType(str, Enum):
    LU = "祿"
    QUAN = "權"
    KE = "科"
    JI = "忌"


class GeometricRelation(str, Enum):
    SAME_PALACE = "same_palace"
    OPPOSITE_PALACE_INCOMING = "opposite_palace_incoming"
    NORMAL = "normal"


@dataclass(frozen=True)
class LayerProvenance:
    classification: str
    source_name: str
    source_version: Optional[str]
    rule_profile: Optional[str]
    rule_version: Optional[str]
    derived_by: Optional[str]
    qualified_against: Tuple[str, ...] = ()
    qualification_status: str = "not_run"


@dataclass(frozen=True)
class Transformation:
    type: TransformationType
    star: str
    sequence: int


@dataclass(frozen=True)
class TransformationSet:
    heavenly_stem: str
    profile_id: str
    rule_version: str
    transformations: Tuple[Transformation, ...]
    provenance: LayerProvenance


@dataclass(frozen=True)
class ChartIdentity:
    chart_id: str
    chart_basis: str
    source_profile: str


@dataclass(frozen=True)
class StarLocationRecord:
    star: str
    palace: str


@dataclass(frozen=True)
class StarLocationIndex:
    chart_identity: ChartIdentity
    locations: Mapping[str, str]
    validation_status: str
    provenance: LayerProvenance


@dataclass(frozen=True)
class PalaceStemRecord:
    palace: str
    heavenly_stem: str


@dataclass(frozen=True)
class PalaceStemIndex:
    chart_identity: ChartIdentity
    stems: Mapping[str, str]
    validation_status: str
    provenance: LayerProvenance


@dataclass(frozen=True)
class PalaceStemSource:
    kind: str
    chart_identity: ChartIdentity
    palace: str
    heavenly_stem: str


@dataclass(frozen=True)
class CycleStemSource:
    kind: str
    chart_identity: ChartIdentity
    scope: str
    reference: str
    heavenly_stem: str


FlyingSource = Union[PalaceStemSource, CycleStemSource]


@dataclass(frozen=True)
class FlyingEdge:
    edge_id: str
    source: FlyingSource
    heavenly_stem: str
    transformation_type: TransformationType
    star: str
    target_palace: str
    target_basis: str
    profile_id: str
    geometric_relation: Optional[GeometricRelation]
    provenance: LayerProvenance


@dataclass(frozen=True)
class NatalFlyingGraph:
    chart_identity: ChartIdentity
    edges: Tuple[FlyingEdge, ...]
    outgoing_index: Mapping[str, Tuple[FlyingEdge, ...]]
    incoming_index: Mapping[str, Tuple[FlyingEdge, ...]]


@dataclass(frozen=True)
class LayerIdentity:
    chart_id: str
    scope: str
    reference: str
    rule_profile: str


@dataclass(frozen=True)
class AvailabilityRecord:
    status: str
    reason: Optional[str]


@dataclass(frozen=True)
class CycleTransformationLayer:
    identity: LayerIdentity
    source: CycleStemSource
    heavenly_stem: str
    earthly_branch: Optional[str]
    transformations: TransformationSet
    flying_edges: Tuple[FlyingEdge, ...]
    provenance: LayerProvenance
    validation: str
    availability: AvailabilityRecord


@dataclass(frozen=True)
class SmallLimitContext:
    reference: str
    palace: str
    stem_branch: str
    provenance: LayerProvenance
    transformation_layer: None = None
```

- [ ] **Step 5: Run GREEN + Python 3.9 syntax check**

```bash
python -m unittest tests.test_ziwei_phase2a_models -v
python -m py_compile engine/ziwei/errors.py engine/ziwei/models.py
```

Expected: PASS / no syntax errors。

- [ ] **Step 6: Existing regression**

```bash
python -m unittest tests.test_engine_module_layout tests.test_ziwei_capabilities -v
```

Expected: PASS；capability 尚未改動。

- [ ] **Step 7: Commit**

```bash
git add engine/ziwei/errors.py engine/ziwei/models.py tests/test_ziwei_phase2a_models.py
git commit -m "feat: add Ziwei Phase 2A core models"
```

---

### Task 2: Duplicate-safe Natal Basis Builders 與 Synthetic Fixture

**Files:**
- Create: `engine/ziwei/basis.py`
- Modify: `engine/ziwei/common.py`
- Create: `tests/ziwei_phase2a_fixtures.py`
- Test: `tests/test_ziwei_basis.py`

**Interfaces:**
- `validate_palace(palace) -> None`
- `build_star_location_index(records, chart_identity, provenance) -> StarLocationIndex`
- `build_palace_stem_index(records, chart_identity, provenance) -> PalaceStemIndex`

- [ ] **Step 1: Add explicit synthetic fixture data used across all Phase 2A tests**

```python
# tests/ziwei_phase2a_fixtures.py
from engine.ziwei.common import PALACE_NAMES
from engine.ziwei.models import (
    ChartIdentity,
    LayerProvenance,
    PalaceStemRecord,
    StarLocationRecord,
)

CHART = ChartIdentity("chart-fixture-A", "natal", "synthetic-v1")
PROVENANCE = LayerProvenance(
    "validated_source_fact",
    "synthetic",
    "1",
    None,
    None,
    None,
)

TRANSFORMABLE_STARS = (
    "廉貞", "破軍", "武曲", "太陽", "天機",
    "天梁", "紫微", "太陰", "天同", "文昌",
    "貪狼", "右弼", "文曲", "巨門", "左輔",
)

SYNTHETIC_STAR_RECORDS = tuple(
    StarLocationRecord(star, PALACE_NAMES[idx % 12])
    for idx, star in enumerate(TRANSFORMABLE_STARS)
)

SYNTHETIC_PALACE_STEM_RECORDS = tuple(
    PalaceStemRecord(palace, "甲乙丙丁戊己庚辛壬癸甲乙"[idx])
    for idx, palace in enumerate(PALACE_NAMES)
)
```

This fixture is synthetic and must never be replaced by the private user chart。

- [ ] **Step 2: Write RED duplicate / completeness tests**

```python
# tests/test_ziwei_basis.py
import unittest

from engine.ziwei.basis import build_palace_stem_index, build_star_location_index
from engine.ziwei.errors import ZiweiPhase2AError
from engine.ziwei.models import PalaceStemRecord, StarLocationRecord
from tests.ziwei_phase2a_fixtures import CHART, PROVENANCE, SYNTHETIC_PALACE_STEM_RECORDS, SYNTHETIC_STAR_RECORDS


class ZiweiBasisTests(unittest.TestCase):
    def test_duplicate_star_same_palace_is_rejected(self):
        records = (StarLocationRecord("天機", "夫妻宮"), StarLocationRecord("天機", "夫妻宮"))
        with self.assertRaises(ZiweiPhase2AError) as cm:
            build_star_location_index(records, CHART, PROVENANCE)
        self.assertEqual(cm.exception.code, "duplicate_star_location")

    def test_duplicate_star_conflicting_palace_is_rejected(self):
        records = (StarLocationRecord("天機", "夫妻宮"), StarLocationRecord("天機", "官祿宮"))
        with self.assertRaises(ZiweiPhase2AError) as cm:
            build_star_location_index(records, CHART, PROVENANCE)
        self.assertEqual(cm.exception.code, "duplicate_star_location")

    def test_palace_stems_require_exactly_twelve_unique_palaces(self):
        with self.assertRaises(ZiweiPhase2AError) as cm:
            build_palace_stem_index(SYNTHETIC_PALACE_STEM_RECORDS[:-1], CHART, PROVENANCE)
        self.assertEqual(cm.exception.code, "invalid_palace_stem_index")

    def test_duplicate_palace_is_rejected_before_dict_materialization(self):
        records = SYNTHETIC_PALACE_STEM_RECORDS + (PalaceStemRecord("命宮", "甲"),)
        with self.assertRaises(ZiweiPhase2AError) as cm:
            build_palace_stem_index(records, CHART, PROVENANCE)
        self.assertEqual(cm.exception.code, "duplicate_palace_stem")

    def test_valid_indexes_are_materialized(self):
        stars = build_star_location_index(SYNTHETIC_STAR_RECORDS, CHART, PROVENANCE)
        stems = build_palace_stem_index(SYNTHETIC_PALACE_STEM_RECORDS, CHART, PROVENANCE)
        self.assertEqual(len(stars.locations), 15)
        self.assertEqual(len(stems.stems), 12)
```

- [ ] **Step 3: Run RED**

```bash
python -m unittest tests.test_ziwei_basis -v
```

Expected: FAIL because `basis.py` is missing。

- [ ] **Step 4: Add `validate_palace()` without changing existing palace placement semantics**

```python
# engine/ziwei/common.py

def validate_palace(palace: str) -> None:
    if palace not in PALACE_NAMES:
        raise ValueError("宮位必須為：" + "、".join(PALACE_NAMES))
```

- [ ] **Step 5: Implement record-first builders**

```python
# engine/ziwei/basis.py
from __future__ import annotations

from types import MappingProxyType

from .common import PALACE_NAMES, validate_palace
from .errors import ZiweiPhase2AError
from .models import PalaceStemIndex, StarLocationIndex

LEGAL_STEMS = tuple("甲乙丙丁戊己庚辛壬癸")


def build_star_location_index(records, chart_identity, provenance):
    materialized = {}
    for record in records:
        try:
            validate_palace(record.palace)
        except ValueError as exc:
            raise ZiweiPhase2AError("invalid_palace", str(exc), {"palace": record.palace}) from exc
        if not record.star:
            raise ZiweiPhase2AError("missing_star_location", "star must not be empty")
        if record.star in materialized:
            raise ZiweiPhase2AError("duplicate_star_location", "duplicate star input", {"star": record.star})
        materialized[record.star] = record.palace
    return StarLocationIndex(chart_identity, MappingProxyType(materialized), "validated", provenance)


def build_palace_stem_index(records, chart_identity, provenance):
    materialized = {}
    for record in records:
        try:
            validate_palace(record.palace)
        except ValueError as exc:
            raise ZiweiPhase2AError("invalid_palace", str(exc), {"palace": record.palace}) from exc
        if record.palace in materialized:
            raise ZiweiPhase2AError("duplicate_palace_stem", "duplicate palace stem input", {"palace": record.palace})
        if record.heavenly_stem not in LEGAL_STEMS:
            raise ZiweiPhase2AError("invalid_palace_stem_index", "invalid palace heavenly stem", {"stem": record.heavenly_stem})
        materialized[record.palace] = record.heavenly_stem
    if tuple(materialized.keys()) != PALACE_NAMES and set(materialized.keys()) != set(PALACE_NAMES):
        raise ZiweiPhase2AError("invalid_palace_stem_index", "all twelve canonical palaces are required")
    return PalaceStemIndex(chart_identity, MappingProxyType(materialized), "validated", provenance)
```

The final implementation may simplify the two completeness comparisons to a single `set` check; it must still accept all 12 canonical palaces regardless of input order and reject missing/extra/duplicate records。

- [ ] **Step 6: Run GREEN + existing month regression**

```bash
python -m unittest tests.test_ziwei_basis tests.test_engine_module_layout tests.test_project_ziwei_month -v
```

Expected: PASS。

- [ ] **Step 7: Commit**

```bash
git add engine/ziwei/basis.py engine/ziwei/common.py tests/ziwei_phase2a_fixtures.py tests/test_ziwei_basis.py
git commit -m "feat: add validated Ziwei natal basis indexes"
```

---

### Task 3: Versioned 10-Stem Profile 與 Pure Transformation Core

**Files:**
- Create: `engine/ziwei/transformation_profiles.py`
- Create: `engine/ziwei/transformations.py`
- Test: `tests/test_ziwei_transformations.py`

**Interfaces:**
- `PROFILE_ID = "metaphysics-lab-common-v1"`
- `RULE_VERSION = "1.0"`
- `validate_transformation_profile(profile_id, rule_version, table) -> None`
- `get_transformation_set(heavenly_stem, profile_id=PROFILE_ID) -> TransformationSet`

- [ ] **Step 1: Write RED exhaustive tests**

```python
# tests/test_ziwei_transformations.py
import unittest

from engine.ziwei.errors import ZiweiPhase2AError
from engine.ziwei.transformations import get_transformation_set

EXPECTED = {
    "甲": ("廉貞", "破軍", "武曲", "太陽"),
    "乙": ("天機", "天梁", "紫微", "太陰"),
    "丙": ("天同", "天機", "文昌", "廉貞"),
    "丁": ("太陰", "天同", "天機", "巨門"),
    "戊": ("貪狼", "太陰", "右弼", "天機"),
    "己": ("武曲", "貪狼", "天梁", "文曲"),
    "庚": ("太陽", "武曲", "太陰", "天同"),
    "辛": ("巨門", "太陽", "文曲", "文昌"),
    "壬": ("天梁", "紫微", "左輔", "武曲"),
    "癸": ("破軍", "巨門", "太陰", "貪狼"),
}


class ZiweiTransformationTests(unittest.TestCase):
    def test_all_ten_stems_match_exact_four_transformations(self):
        checked = 0
        for stem, expected_stars in EXPECTED.items():
            result = get_transformation_set(stem)
            self.assertEqual(tuple(item.star for item in result.transformations), expected_stars)
            self.assertEqual(tuple(item.type.value for item in result.transformations), ("祿", "權", "科", "忌"))
            self.assertEqual(tuple(item.sequence for item in result.transformations), (0, 1, 2, 3))
            checked += 4
        self.assertEqual(checked, 40)

    def test_invalid_stem_fails_closed(self):
        with self.assertRaises(ZiweiPhase2AError) as cm:
            get_transformation_set("A")
        self.assertEqual(cm.exception.code, "invalid_heavenly_stem")

    def test_unknown_profile_has_no_fallback(self):
        with self.assertRaises(ZiweiPhase2AError) as cm:
            get_transformation_set("甲", "unknown-v1")
        self.assertEqual(cm.exception.code, "unknown_profile")
```

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_ziwei_transformations -v
```

Expected: FAIL because modules are missing。

- [ ] **Step 3: Implement exact profile table + validation**

```python
# engine/ziwei/transformation_profiles.py
from .errors import ZiweiPhase2AError

PROFILE_ID = "metaphysics-lab-common-v1"
RULE_VERSION = "1.0"
LEGAL_STEMS = tuple("甲乙丙丁戊己庚辛壬癸")
PROFILE = {
    "甲": ("廉貞", "破軍", "武曲", "太陽"),
    "乙": ("天機", "天梁", "紫微", "太陰"),
    "丙": ("天同", "天機", "文昌", "廉貞"),
    "丁": ("太陰", "天同", "天機", "巨門"),
    "戊": ("貪狼", "太陰", "右弼", "天機"),
    "己": ("武曲", "貪狼", "天梁", "文曲"),
    "庚": ("太陽", "武曲", "太陰", "天同"),
    "辛": ("巨門", "太陽", "文曲", "文昌"),
    "壬": ("天梁", "紫微", "左輔", "武曲"),
    "癸": ("破軍", "巨門", "太陰", "貪狼"),
}


def validate_transformation_profile(profile_id, rule_version, table):
    if not profile_id or not rule_version:
        raise ZiweiPhase2AError("invalid_transformation_profile", "profile id and rule version are required")
    if set(table.keys()) != set(LEGAL_STEMS) or len(table) != 10:
        raise ZiweiPhase2AError("invalid_transformation_profile", "profile must contain exactly ten stems")
    for stem in LEGAL_STEMS:
        stars = tuple(table[stem])
        if len(stars) != 4 or any(not star for star in stars):
            raise ZiweiPhase2AError("invalid_transformation_profile", "each stem must provide exactly four non-empty stars", {"stem": stem})
```

- [ ] **Step 4: Implement pure transformation core**

```python
# engine/ziwei/transformations.py
from .errors import ZiweiPhase2AError
from .models import LayerProvenance, Transformation, TransformationSet, TransformationType
from .transformation_profiles import PROFILE, PROFILE_ID, RULE_VERSION, validate_transformation_profile


def get_transformation_set(heavenly_stem, profile_id=PROFILE_ID):
    if profile_id != PROFILE_ID:
        raise ZiweiPhase2AError("unknown_profile", "unknown Ziwei transformation profile", {"profile_id": profile_id})
    validate_transformation_profile(PROFILE_ID, RULE_VERSION, PROFILE)
    if heavenly_stem not in PROFILE:
        raise ZiweiPhase2AError("invalid_heavenly_stem", "invalid heavenly stem", {"heavenly_stem": heavenly_stem})
    types = tuple(TransformationType)
    transformations = tuple(
        Transformation(types[idx], star, idx)
        for idx, star in enumerate(PROFILE[heavenly_stem])
    )
    provenance = LayerProvenance(
        "project_derived",
        "Metaphysics Lab",
        None,
        PROFILE_ID,
        RULE_VERSION,
        "engine.ziwei.transformations",
    )
    return TransformationSet(heavenly_stem, PROFILE_ID, RULE_VERSION, transformations, provenance)
```

- [ ] **Step 5: GREEN + gate marker**

```bash
python -m unittest tests.test_ziwei_transformations -v
python - <<'PY'
from engine.ziwei.transformations import get_transformation_set
checked = 0
for stem in "甲乙丙丁戊己庚辛壬癸":
    assert len(get_transformation_set(stem).transformations) == 4
    checked += 4
assert checked == 40
print("TRANSFORMATION_TABLE_PASS 40/40")
PY
```

- [ ] **Step 6: Commit**

```bash
git add engine/ziwei/transformation_profiles.py engine/ziwei/transformations.py tests/test_ziwei_transformations.py
git commit -m "feat: add versioned Ziwei transformation core"
```

---

### Task 4: Exhaustive Palace Geometry 與 4-edge Flying

**Files:**
- Modify: `engine/ziwei/common.py`
- Create: `engine/ziwei/flying.py`
- Test: `tests/test_ziwei_flying.py`

**Interfaces:**
- `opposite_palace(palace) -> str`
- `classify_geometric_relation(source, target_palace) -> Optional[GeometricRelation]`
- `fly_transformations(transformations, star_locations, source) -> Tuple[FlyingEdge, ...]`

- [ ] **Step 1: Write RED 144-pair geometry tests**

```python
# tests/test_ziwei_flying.py
import unittest

from engine.ziwei.common import PALACE_NAMES, opposite_palace
from engine.ziwei.flying import classify_geometric_relation
from engine.ziwei.models import CycleStemSource, GeometricRelation, PalaceStemSource
from tests.ziwei_phase2a_fixtures import CHART


class ZiweiFlyingGeometryTests(unittest.TestCase):
    def test_all_144_palace_pairs_classify_exactly(self):
        counts = {item: 0 for item in GeometricRelation}
        for source_palace in PALACE_NAMES:
            source = PalaceStemSource("palace_stem", CHART, source_palace, "甲")
            for target in PALACE_NAMES:
                counts[classify_geometric_relation(source, target)] += 1
        self.assertEqual(counts[GeometricRelation.SAME_PALACE], 12)
        self.assertEqual(counts[GeometricRelation.OPPOSITE_PALACE_INCOMING], 12)
        self.assertEqual(counts[GeometricRelation.NORMAL], 120)

    def test_opposite_palace_is_symmetric(self):
        for palace in PALACE_NAMES:
            self.assertEqual(opposite_palace(opposite_palace(palace)), palace)

    def test_cycle_source_has_no_geometric_self_relation(self):
        source = CycleStemSource("cycle_stem", CHART, "yearly", "2026", "丙")
        self.assertIsNone(classify_geometric_relation(source, "田宅宮"))
```

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_ziwei_flying.ZiweiFlyingGeometryTests -v
```

Expected: FAIL because helper/module is missing。

- [ ] **Step 3: Implement one canonical opposite helper and classifier**

```python
# engine/ziwei/common.py

def opposite_palace(palace: str) -> str:
    validate_palace(palace)
    idx = PALACE_NAMES.index(palace)
    return PALACE_NAMES[(idx + 6) % 12]
```

```python
# engine/ziwei/flying.py
from .common import opposite_palace, validate_palace
from .errors import ZiweiPhase2AError
from .models import CycleStemSource, GeometricRelation, PalaceStemSource


def classify_geometric_relation(source, target_palace):
    try:
        validate_palace(target_palace)
    except ValueError as exc:
        raise ZiweiPhase2AError("invalid_palace", str(exc), {"palace": target_palace}) from exc
    if isinstance(source, CycleStemSource):
        return None
    if not isinstance(source, PalaceStemSource):
        raise ZiweiPhase2AError("unsupported_source", "unsupported flying source")
    if source.palace == target_palace:
        return GeometricRelation.SAME_PALACE
    if source.palace == opposite_palace(target_palace):
        return GeometricRelation.OPPOSITE_PALACE_INCOMING
    return GeometricRelation.NORMAL
```

- [ ] **Step 4: Add RED 4-edge synthetic flying test**

Append to `tests/test_ziwei_flying.py`:

```python
from engine.ziwei.basis import build_star_location_index
from engine.ziwei.flying import fly_transformations
from engine.ziwei.transformations import get_transformation_set
from tests.ziwei_phase2a_fixtures import PROVENANCE, SYNTHETIC_STAR_RECORDS


class ZiweiFlyingEdgeTests(unittest.TestCase):
    def test_cycle_transformations_create_exactly_four_edges(self):
        index = build_star_location_index(SYNTHETIC_STAR_RECORDS, CHART, PROVENANCE)
        source = CycleStemSource("cycle_stem", CHART, "yearly", "2026", "丙")
        edges = fly_transformations(get_transformation_set("丙"), index, source)
        expected_targets = tuple(index.locations[star] for star in ("天同", "天機", "文昌", "廉貞"))
        self.assertEqual(len(edges), 4)
        self.assertEqual(tuple(edge.target_palace for edge in edges), expected_targets)
        self.assertTrue(all(edge.geometric_relation is None for edge in edges))
        self.assertTrue(all(edge.target_basis == "natal_star_location" for edge in edges))
```

- [ ] **Step 5: Run RED only for new edge test**

```bash
python -m unittest tests.test_ziwei_flying.ZiweiFlyingEdgeTests -v
```

Expected: FAIL because `fly_transformations` is missing。

- [ ] **Step 6: Implement 4-edge flying with chart/missing-star fail closed**

```python
# engine/ziwei/flying.py
from .models import FlyingEdge


def fly_transformations(transformations, star_locations, source):
    if source.chart_identity != star_locations.chart_identity:
        raise ZiweiPhase2AError("chart_basis_mismatch", "source and star index belong to different charts")
    edges = []
    for item in transformations.transformations:
        if item.star not in star_locations.locations:
            raise ZiweiPhase2AError("missing_star_location", "transformation star has no natal location", {"star": item.star})
        target = star_locations.locations[item.star]
        edge_id = "%s:%s:%s:%s" % (source.kind, source.heavenly_stem, item.type.value, item.sequence)
        edges.append(FlyingEdge(
            edge_id,
            source,
            source.heavenly_stem,
            item.type,
            item.star,
            target,
            "natal_star_location",
            transformations.profile_id,
            classify_geometric_relation(source, target),
            transformations.provenance,
        ))
    if len(edges) != 4:
        raise ZiweiPhase2AError("invalid_transformation_profile", "flying requires exactly four transformations")
    return tuple(edges)
```

- [ ] **Step 7: GREEN + GEOMETRY marker**

```bash
python -m unittest tests.test_ziwei_flying -v
python - <<'PY'
from engine.ziwei.common import PALACE_NAMES
from engine.ziwei.flying import classify_geometric_relation
from engine.ziwei.models import ChartIdentity, GeometricRelation, PalaceStemSource
chart = ChartIdentity("gate", "natal", "synthetic")
counts = {item: 0 for item in GeometricRelation}
for source_palace in PALACE_NAMES:
    source = PalaceStemSource("palace_stem", chart, source_palace, "甲")
    for target in PALACE_NAMES:
        counts[classify_geometric_relation(source, target)] += 1
assert counts[GeometricRelation.SAME_PALACE] == 12
assert counts[GeometricRelation.OPPOSITE_PALACE_INCOMING] == 12
assert counts[GeometricRelation.NORMAL] == 120
print("GEOMETRY_144_PASS")
PY
```

- [ ] **Step 8: Commit**

```bash
git add engine/ziwei/common.py engine/ziwei/flying.py tests/test_ziwei_flying.py
git commit -m "feat: add Ziwei flying geometry and edges"
```

---

### Task 5: 48-edge NatalFlyingGraph 與 Presentation Relation

**Files:**
- Modify: `engine/ziwei/flying.py`
- Extend: `tests/test_ziwei_flying.py`

**Interfaces:**
- `build_natal_flying_graph(palace_stems, star_locations, profile_id=PROFILE_ID) -> NatalFlyingGraph`
- `presentation_relation(edge, profile_id="astralium-compatible-v1") -> Optional[str]`

- [ ] **Step 1: Write RED 48-edge graph test**

```python
from engine.ziwei.basis import build_palace_stem_index
from tests.ziwei_phase2a_fixtures import SYNTHETIC_PALACE_STEM_RECORDS


class ZiweiNatalFlyingGraphTests(unittest.TestCase):
    def test_twelve_palaces_create_exactly_forty_eight_edges(self):
        stars = build_star_location_index(SYNTHETIC_STAR_RECORDS, CHART, PROVENANCE)
        stems = build_palace_stem_index(SYNTHETIC_PALACE_STEM_RECORDS, CHART, PROVENANCE)
        graph = build_natal_flying_graph(stems, stars)
        self.assertEqual(len(graph.edges), 48)
        self.assertEqual(sum(len(v) for v in graph.outgoing_index.values()), 48)
        self.assertEqual(sum(len(v) for v in graph.incoming_index.values()), 48)
        self.assertEqual(set(graph.outgoing_index.keys()), set(PALACE_NAMES))
```

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_ziwei_flying.ZiweiNatalFlyingGraphTests -v
```

Expected: FAIL because graph builder is missing。

- [ ] **Step 3: Implement graph builder**

```python
from types import MappingProxyType
from .common import PALACE_NAMES
from .models import NatalFlyingGraph, PalaceStemSource
from .transformation_profiles import PROFILE_ID
from .transformations import get_transformation_set


def build_natal_flying_graph(palace_stems, star_locations, profile_id=PROFILE_ID):
    if palace_stems.chart_identity != star_locations.chart_identity:
        raise ZiweiPhase2AError("chart_basis_mismatch", "natal indexes belong to different charts")
    edges = []
    for palace in PALACE_NAMES:
        stem = palace_stems.stems[palace]
        source = PalaceStemSource("palace_stem", palace_stems.chart_identity, palace, stem)
        edges.extend(fly_transformations(get_transformation_set(stem, profile_id), star_locations, source))
    if len(edges) != 48:
        raise ZiweiPhase2AError("invalid_palace_stem_index", "natal flying graph must contain exactly 48 edges")
    outgoing = {palace: [] for palace in PALACE_NAMES}
    incoming = {palace: [] for palace in PALACE_NAMES}
    for edge in edges:
        outgoing[edge.source.palace].append(edge)
        incoming[edge.target_palace].append(edge)
    return NatalFlyingGraph(
        palace_stems.chart_identity,
        tuple(edges),
        MappingProxyType({key: tuple(value) for key, value in outgoing.items()}),
        MappingProxyType({key: tuple(value) for key, value in incoming.items()}),
    )
```

- [ ] **Step 4: Write explicit RED presentation mapping tests without undefined helpers**

```python
from engine.ziwei.models import FlyingEdge, TransformationType


def _synthetic_edge(relation):
    source = PalaceStemSource("palace_stem", CHART, "命宮", "甲")
    return FlyingEdge(
        "edge-test",
        source,
        "甲",
        TransformationType.LU,
        "廉貞",
        "命宮",
        "natal_star_location",
        "metaphysics-lab-common-v1",
        relation,
        PROVENANCE,
    )


class ZiweiPresentationRelationTests(unittest.TestCase):
    def test_same_palace_maps_down(self):
        self.assertEqual(presentation_relation(_synthetic_edge(GeometricRelation.SAME_PALACE)), "↓")

    def test_opposite_incoming_maps_up(self):
        self.assertEqual(presentation_relation(_synthetic_edge(GeometricRelation.OPPOSITE_PALACE_INCOMING)), "↑")

    def test_normal_and_cycle_none_have_no_arrow(self):
        self.assertIsNone(presentation_relation(_synthetic_edge(GeometricRelation.NORMAL)))
        self.assertIsNone(presentation_relation(_synthetic_edge(None)))
```

- [ ] **Step 5: Run RED for presentation tests**

```bash
python -m unittest tests.test_ziwei_flying.ZiweiPresentationRelationTests -v
```

Expected: FAIL because presentation function is missing。

- [ ] **Step 6: Implement isolated presentation mapping**

```python
PRESENTATION_PROFILE_ID = "astralium-compatible-v1"


def presentation_relation(edge, profile_id=PRESENTATION_PROFILE_ID):
    if profile_id != PRESENTATION_PROFILE_ID:
        raise ZiweiPhase2AError("unknown_profile", "unknown presentation profile", {"profile_id": profile_id})
    mapping = {
        GeometricRelation.SAME_PALACE: "↓",
        GeometricRelation.OPPOSITE_PALACE_INCOMING: "↑",
        GeometricRelation.NORMAL: None,
        None: None,
    }
    return mapping[edge.geometric_relation]
```

- [ ] **Step 7: GREEN**

```bash
python -m unittest tests.test_ziwei_flying -v
```

Expected: PASS；graph exactly 48 edges。

- [ ] **Step 8: Commit**

```bash
git add engine/ziwei/flying.py tests/test_ziwei_flying.py
git commit -m "feat: add Ziwei natal flying graph"
```

---

### Task 6: Composition — No-overwrite, Conflict, Availability, Readonly Queries

**Files:**
- Modify: `engine/ziwei/models.py` — add `NatalContext`, `ZiweiLayerStack`, query result records。
- Create: `engine/ziwei/composition.py`
- Test: `tests/test_ziwei_composition.py`

**Interfaces:**
- `build_cycle_layer(...) -> CycleTransformationLayer`
- `build_layer_stack(chart_identity, natal, cycles=(), small_limit=None) -> ZiweiLayerStack`
- `ZiweiCompositeView(stack).for_palace()` / `.for_star()` / `.for_transformation()`

- [ ] **Step 1: Add exact composition model records to `models.py` under RED tests**

Add tests first:

```python
# tests/test_ziwei_composition.py
import unittest

from engine.ziwei.models import AvailabilityRecord, NatalContext, ZiweiLayerStack


class ZiweiCompositionModelTests(unittest.TestCase):
    def test_fine_cycle_availability_record_is_explicit(self):
        item = AvailabilityRecord("unavailable", "fine_cycle_stem_resolver_not_enabled")
        self.assertEqual(item.status, "unavailable")
```

Run and confirm RED because `NatalContext` / `ZiweiLayerStack` do not yet exist。

Then add:

```python
# append to engine/ziwei/models.py
@dataclass(frozen=True)
class NatalContext:
    star_locations: StarLocationIndex
    palace_stems: PalaceStemIndex
    natal_flying_graph: NatalFlyingGraph
    birth_year_layer: Optional[CycleTransformationLayer]


@dataclass(frozen=True)
class ZiweiLayerStack:
    chart_identity: ChartIdentity
    natal: NatalContext
    cycles: Tuple[CycleTransformationLayer, ...]
    small_limit: Optional[SmallLimitContext]
    availability: Mapping[str, AvailabilityRecord]
    provenance: LayerProvenance


@dataclass(frozen=True)
class TransformationOccurrence:
    scope: str
    reference: str
    transformation_type: TransformationType
    star: str
    target_palace: str
    provenance: LayerProvenance
```

- [ ] **Step 2: Define explicit synthetic stack helper in the test file**

```python
from engine.ziwei.basis import build_palace_stem_index, build_star_location_index
from engine.ziwei.flying import build_natal_flying_graph, fly_transformations
from engine.ziwei.models import CycleStemSource, LayerIdentity, NatalContext
from engine.ziwei.transformations import get_transformation_set
from tests.ziwei_phase2a_fixtures import CHART, PROVENANCE, SYNTHETIC_PALACE_STEM_RECORDS, SYNTHETIC_STAR_RECORDS


def _natal_context():
    stars = build_star_location_index(SYNTHETIC_STAR_RECORDS, CHART, PROVENANCE)
    stems = build_palace_stem_index(SYNTHETIC_PALACE_STEM_RECORDS, CHART, PROVENANCE)
    return NatalContext(stars, stems, build_natal_flying_graph(stems, stars), None)


def _cycle_components(scope, reference, stem):
    natal = _natal_context()
    source = CycleStemSource("cycle_stem", CHART, scope, reference, stem)
    transformations = get_transformation_set(stem)
    edges = fly_transformations(transformations, natal.star_locations, source)
    identity = LayerIdentity(CHART.chart_id, scope, reference, transformations.profile_id)
    return natal, source, transformations, edges, identity
```

- [ ] **Step 3: Write RED strict layer tests**

```python
from engine.ziwei.composition import build_cycle_layer, build_layer_stack
from engine.ziwei.errors import ZiweiPhase2AError


class ZiweiCompositionTests(unittest.TestCase):
    def test_supported_cycle_layer_has_exactly_four_edges(self):
        natal, source, transformations, edges, identity = _cycle_components("yearly", "2026", "丙")
        layer = build_cycle_layer(identity, source, transformations, edges, PROVENANCE)
        self.assertEqual(len(layer.flying_edges), 4)

    def test_fine_cycle_scope_is_rejected(self):
        natal, source, transformations, edges, identity = _cycle_components("monthly", "2026-L07", "丙")
        with self.assertRaises(ZiweiPhase2AError) as cm:
            build_cycle_layer(identity, source, transformations, edges, PROVENANCE)
        self.assertEqual(cm.exception.code, "unsupported_scope")

    def test_same_identity_exact_duplicate_is_rejected(self):
        natal, source, transformations, edges, identity = _cycle_components("yearly", "2026", "丙")
        layer = build_cycle_layer(identity, source, transformations, edges, PROVENANCE)
        with self.assertRaises(ZiweiPhase2AError) as cm:
            build_layer_stack(CHART, natal, (layer, layer))
        self.assertEqual(cm.exception.code, "duplicate_layer_identity")

    def test_same_identity_conflicting_stem_is_layer_conflict(self):
        natal, source_a, trans_a, edges_a, identity = _cycle_components("yearly", "2026", "丙")
        layer_a = build_cycle_layer(identity, source_a, trans_a, edges_a, PROVENANCE)
        source_b = CycleStemSource("cycle_stem", CHART, "yearly", "2026", "丁")
        trans_b = get_transformation_set("丁")
        edges_b = fly_transformations(trans_b, natal.star_locations, source_b)
        layer_b = build_cycle_layer(identity, source_b, trans_b, edges_b, PROVENANCE)
        with self.assertRaises(ZiweiPhase2AError) as cm:
            build_layer_stack(CHART, natal, (layer_a, layer_b))
        self.assertEqual(cm.exception.code, "layer_conflict")
```

- [ ] **Step 4: Run RED**

```bash
python -m unittest tests.test_ziwei_composition -v
```

Expected: FAIL because composition functions are missing。

- [ ] **Step 5: Implement strict builders and hard availability**

```python
# engine/ziwei/composition.py
from __future__ import annotations

from types import MappingProxyType

from .errors import ZiweiPhase2AError
from .models import (
    AvailabilityRecord,
    CycleTransformationLayer,
    TransformationOccurrence,
    ZiweiLayerStack,
)

SUPPORTED_SCOPES = {"birth_year", "decadal", "yearly"}
FINE_CYCLE_REASON = "fine_cycle_stem_resolver_not_enabled"


def build_cycle_layer(identity, source, transformations, flying_edges, provenance, earthly_branch=None):
    if source.scope not in SUPPORTED_SCOPES:
        raise ZiweiPhase2AError("unsupported_scope", "Phase 2A does not execute fine-cycle transformations", {"scope": source.scope})
    if source.chart_identity.chart_id != identity.chart_id:
        raise ZiweiPhase2AError("chart_basis_mismatch", "layer identity and source chart mismatch")
    if len(transformations.transformations) != 4 or len(flying_edges) != 4:
        raise ZiweiPhase2AError("invalid_transformation_profile", "cycle layer requires exactly four transformations and four edges")
    return CycleTransformationLayer(
        identity,
        source,
        source.heavenly_stem,
        earthly_branch,
        transformations,
        tuple(flying_edges),
        provenance,
        "validated",
        AvailabilityRecord("available", None),
    )


def _availability():
    return MappingProxyType({
        "birth_year_transformations": AvailabilityRecord("available", None),
        "natal_palace_flying": AvailabilityRecord("available", None),
        "decadal_transformations": AvailabilityRecord("conditional", "trusted_decadal_stem_required"),
        "yearly_transformations": AvailabilityRecord("conditional", "trusted_yearly_stem_required"),
        "monthly_transformations": AvailabilityRecord("unavailable", FINE_CYCLE_REASON),
        "daily_transformations": AvailabilityRecord("unavailable", FINE_CYCLE_REASON),
        "hourly_transformations": AvailabilityRecord("unavailable", FINE_CYCLE_REASON),
    })


def build_layer_stack(chart_identity, natal, cycles=(), small_limit=None):
    if natal.star_locations.chart_identity != chart_identity or natal.palace_stems.chart_identity != chart_identity:
        raise ZiweiPhase2AError("chart_basis_mismatch", "natal basis and stack chart mismatch")
    seen = {}
    ordered = []
    for layer in cycles:
        key = layer.identity
        if key in seen:
            if seen[key] == layer:
                raise ZiweiPhase2AError("duplicate_layer_identity", "duplicate layer identity")
            raise ZiweiPhase2AError("layer_conflict", "conflicting facts for one layer identity")
        seen[key] = layer
        ordered.append(layer)
    return ZiweiLayerStack(chart_identity, natal, tuple(ordered), small_limit, _availability(), PROVENANCE_FOR_STACK)
```

Define `PROVENANCE_FOR_STACK` in the same module as a `LayerProvenance("project_derived", "Metaphysics Lab", None, None, "1.0", "engine.ziwei.composition")` constant；do not import test provenance into production。

- [ ] **Step 6: Write explicit RED query / no-overwrite tests**

```python
from engine.ziwei.composition import ZiweiCompositeView
from engine.ziwei.models import TransformationType


class ZiweiCompositeViewTests(unittest.TestCase):
    def test_multiple_scopes_are_not_overwritten(self):
        natal = _natal_context()
        layers = []
        for scope, reference, stem in (
            ("birth_year", "natal", "乙"),
            ("decadal", "43-52-virtual-age", "丙"),
            ("yearly", "2026", "丁"),
        ):
            source = CycleStemSource("cycle_stem", CHART, scope, reference, stem)
            trans = get_transformation_set(stem)
            edges = fly_transformations(trans, natal.star_locations, source)
            identity = LayerIdentity(CHART.chart_id, scope, reference, trans.profile_id)
            layers.append(build_cycle_layer(identity, source, trans, edges, PROVENANCE))
        stack = build_layer_stack(CHART, natal, tuple(layers))
        rows = ZiweiCompositeView(stack).for_transformation(TransformationType.JI)
        self.assertEqual(tuple(row.scope for row in rows), ("birth_year", "decadal", "yearly"))

    def test_fine_cycle_availability_is_unavailable(self):
        stack = build_layer_stack(CHART, _natal_context())
        self.assertEqual(stack.availability["monthly_transformations"].status, "unavailable")
        self.assertEqual(stack.availability["monthly_transformations"].reason, "fine_cycle_stem_resolver_not_enabled")
        self.assertEqual(stack.availability["daily_transformations"].status, "unavailable")
        self.assertEqual(stack.availability["hourly_transformations"].status, "unavailable")
```

- [ ] **Step 7: Implement readonly query view**

```python
class ZiweiCompositeView:
    def __init__(self, stack):
        self._stack = stack

    def _occurrences(self):
        rows = []
        all_layers = []
        if self._stack.natal.birth_year_layer is not None:
            all_layers.append(self._stack.natal.birth_year_layer)
        all_layers.extend(self._stack.cycles)
        for layer in all_layers:
            for edge in layer.flying_edges:
                rows.append(TransformationOccurrence(
                    layer.identity.scope,
                    layer.identity.reference,
                    edge.transformation_type,
                    edge.star,
                    edge.target_palace,
                    layer.provenance,
                ))
        return tuple(rows)

    def for_transformation(self, transformation_type):
        return tuple(row for row in self._occurrences() if row.transformation_type == transformation_type)

    def for_star(self, star):
        return tuple(row for row in self._occurrences() if row.star == star)

    def for_palace(self, palace):
        return tuple(row for row in self._occurrences() if row.target_palace == palace)
```

Do not add `score`, `resonance`, `current_mutagen`, or `final_transformation` fields/methods。

- [ ] **Step 8: GREEN + internal suite**

```bash
python -m unittest tests.test_ziwei_composition -v
python -m unittest \
  tests.test_ziwei_phase2a_models \
  tests.test_ziwei_basis \
  tests.test_ziwei_transformations \
  tests.test_ziwei_flying \
  tests.test_ziwei_composition \
  -v
```

Expected: 0 failures / 0 errors。

- [ ] **Step 9: Commit**

```bash
git add engine/ziwei/models.py engine/ziwei/composition.py tests/test_ziwei_composition.py
git commit -m "feat: add Ziwei transformation layer composition"
```

---

### Task 7: Capability Lifecycle 與 Package Boundary

**Files:**
- Modify: `engine/ziwei/capabilities.py`
- Modify: `engine/ziwei/__init__.py`
- Create: `tests/test_ziwei_phase2a_capabilities.py`

**Interfaces:**
- Internal gates passed → `ziwei.transformations` / `ziwei.flying` become `implemented / experimental / on_demand`。
- Fine-cycle transformation/flying ids exist only as `planned`。
- `ziwei.flowing_stars` remains `planned`。

- [ ] **Step 1: Write RED capability tests**

```python
# tests/test_ziwei_phase2a_capabilities.py
import unittest

from engine.ziwei.capabilities import can_execute, get_capability, should_run_by_default


class ZiweiPhase2ACapabilityTests(unittest.TestCase):
    def test_phase2a_core_is_experimental_on_demand_after_internal_gates(self):
        for capability_id in ("ziwei.transformations", "ziwei.flying"):
            cap = get_capability(capability_id)
            self.assertEqual(cap["implementation"], "implemented")
            self.assertEqual(cap["maturity"], "experimental")
            self.assertEqual(cap["routing"], "on_demand")
            self.assertTrue(can_execute(capability_id))
            self.assertFalse(should_run_by_default(capability_id))

    def test_fine_cycle_capabilities_are_planned(self):
        ids = (
            "ziwei.flow_month_transformations",
            "ziwei.flow_day_transformations",
            "ziwei.flow_hour_transformations",
            "ziwei.flow_month_flying",
            "ziwei.flow_day_flying",
            "ziwei.flow_hour_flying",
        )
        for capability_id in ids:
            self.assertEqual(get_capability(capability_id)["implementation"], "planned")
            self.assertFalse(can_execute(capability_id))

    def test_flowing_stars_remain_planned(self):
        self.assertEqual(get_capability("ziwei.flowing_stars")["implementation"], "planned")
```

- [ ] **Step 2: Run RED and confirm failure matches current planned registry**

```bash
python -m unittest tests.test_ziwei_phase2a_capabilities -v
```

- [ ] **Step 3: Update registry to experimental/on-demand and planned fine-cycle ids**

Use exact metadata:

```python
"ziwei.transformations": {
    "id": "ziwei.transformations",
    "implementation": "implemented",
    "maturity": "experimental",
    "routing": "on_demand",
    "rule_version": "1.0-exp",
    "module": "engine.ziwei.transformations",
    "dependencies": (),
},
"ziwei.flying": {
    "id": "ziwei.flying",
    "implementation": "implemented",
    "maturity": "experimental",
    "routing": "on_demand",
    "rule_version": "1.0-exp",
    "module": "engine.ziwei.flying",
    "dependencies": ("ziwei.transformations",),
},
```

Fine-cycle capability records use `implementation="planned"`, `maturity=None`, `routing="on_demand"`, `rule_version=None`。Existing month/day/hour records must not change。

- [ ] **Step 4: Update `engine/ziwei/__init__.py` conservatively**

Add only existing Phase 2A core exports such as:

```python
from .transformations import get_transformation_set
from .flying import build_natal_flying_graph, fly_transformations
```

Do not export monthly/daily/hourly transformation or flying functions because they do not exist。

- [ ] **Step 5: GREEN + existing Ziwei regressions**

```bash
python -m unittest \
  tests.test_ziwei_phase2a_capabilities \
  tests.test_ziwei_capabilities \
  tests.test_project_ziwei_month \
  tests.test_project_ziwei_day \
  tests.test_project_ziwei_hour \
  tests.test_ziwei_calendar_adapter \
  tests.test_engine_module_layout \
  -v
```

Expected: PASS and existing timing maturity/routing unchanged。

- [ ] **Step 6: Commit**

```bash
git add engine/ziwei/capabilities.py engine/ziwei/__init__.py tests/test_ziwei_phase2a_capabilities.py
git commit -m "feat: register Ziwei Phase 2A capabilities"
```

---

### Task 8: Public iztro Qualification 40/40

**Files:**
- Create: `tools/qualify_ziwei_phase2a_public.py`
- Create: `tests/test_ziwei_phase2a_qualification_tools.py`
- Create after successful external run: `qualification/ziwei/phase2a/public-iztro-814b77e6.json`

**Interfaces:**
- Parser: `parse_iztro_heavenly_stems(source_text) -> dict[str, tuple[str, ...]]`
- Qualifier: `qualify_public_profile(source_table, source_revision, run_timestamp) -> dict`
- CLI accepts `--source-ts`, `--output`, `--source-revision`。

- [ ] **Step 1: Write RED parser and qualification tests with an independent TypeScript fragment**

```python
# tests/test_ziwei_phase2a_qualification_tools.py
import unittest

from tools.qualify_ziwei_phase2a_public import parse_iztro_heavenly_stems, qualify_public_profile

IZTRO_FRAGMENT = """
export const heavenlyStems = {
  jiaHeavenly: { mutagen: ['lianzhenMaj', 'pojunMaj', 'wuquMaj', 'taiyangMaj'] },
  yiHeavenly: { mutagen: ['tianjiMaj', 'tianliangMaj', 'ziweiMaj', 'taiyinMaj'] },
  bingHeavenly: { mutagen: ['tiantongMaj', 'tianjiMaj', 'wenchangMin', 'lianzhenMaj'] },
  dingHeavenly: { mutagen: ['taiyinMaj', 'tiantongMaj', 'tianjiMaj', 'jumenMaj'] },
  wuHeavenly: { mutagen: ['tanlangMaj', 'taiyinMaj', 'youbiMin', 'tianjiMaj'] },
  jiHeavenly: { mutagen: ['wuquMaj', 'tanlangMaj', 'tianliangMaj', 'wenquMin'] },
  gengHeavenly: { mutagen: ['taiyangMaj', 'wuquMaj', 'taiyinMaj', 'tiantongMaj'] },
  xinHeavenly: { mutagen: ['jumenMaj', 'taiyangMaj', 'wenquMin', 'wenchangMin'] },
  renHeavenly: { mutagen: ['tianliangMaj', 'ziweiMaj', 'zuofuMin', 'wuquMaj'] },
  guiHeavenly: { mutagen: ['pojunMaj', 'jumenMaj', 'taiyinMaj', 'tanlangMaj'] },
};
"""


class ZiweiPublicQualificationTests(unittest.TestCase):
    def test_parser_extracts_ten_stems_without_using_project_profile(self):
        table = parse_iztro_heavenly_stems(IZTRO_FRAGMENT)
        self.assertEqual(len(table), 10)
        self.assertEqual(table["丙"], ("天同", "天機", "文昌", "廉貞"))

    def test_exact_external_table_is_40_of_40_pass(self):
        table = parse_iztro_heavenly_stems(IZTRO_FRAGMENT)
        evidence = qualify_public_profile(table, "814b77e6371e1050cac31bbf674db3c3138fcfde", "2026-08-21T00:00:00Z")
        self.assertEqual(evidence["cases_checked"], 40)
        self.assertEqual(evidence["cases_matched"], 40)
        self.assertEqual(evidence["mismatches"], [])
        self.assertEqual(evidence["status"], "PASS")

    def test_one_external_mismatch_is_fail(self):
        table = parse_iztro_heavenly_stems(IZTRO_FRAGMENT)
        table = dict(table)
        table["丙"] = ("天同", "天機", "文昌", "天機")
        evidence = qualify_public_profile(table, "814b77e6371e1050cac31bbf674db3c3138fcfde", "2026-08-21T00:00:00Z")
        self.assertEqual(evidence["cases_matched"], 39)
        self.assertEqual(evidence["status"], "FAIL")
```

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_ziwei_phase2a_qualification_tools.ZiweiPublicQualificationTests -v
```

- [ ] **Step 3: Implement deterministic parser with explicit key maps**

Production tool must define explicit maps for all 10 stem keys and 15 star keys used by the pinned source, for example:

```python
STEM_KEYS = {
    "jiaHeavenly": "甲", "yiHeavenly": "乙", "bingHeavenly": "丙", "dingHeavenly": "丁", "wuHeavenly": "戊",
    "jiHeavenly": "己", "gengHeavenly": "庚", "xinHeavenly": "辛", "renHeavenly": "壬", "guiHeavenly": "癸",
}
STAR_KEYS = {
    "lianzhenMaj": "廉貞", "pojunMaj": "破軍", "wuquMaj": "武曲", "taiyangMaj": "太陽", "tianjiMaj": "天機",
    "tianliangMaj": "天梁", "ziweiMaj": "紫微", "taiyinMaj": "太陰", "tiantongMaj": "天同", "wenchangMin": "文昌",
    "tanlangMaj": "貪狼", "youbiMin": "右弼", "wenquMin": "文曲", "jumenMaj": "巨門", "zuofuMin": "左輔",
}
```

Use a regex that extracts each named object’s `mutagen: [...]` array; require exactly 10 recognized stems and exactly 4 recognized star keys per stem。Unknown/missing keys must raise `ZiweiPhase2AError("qualification_mismatch", ...)` rather than being ignored。

- [ ] **Step 4: Implement comparison evidence**

`qualify_public_profile()` calls production `get_transformation_set()` for each stem, compares 40 positions, and returns:

```python
{
    "source_name": "SylarLong/iztro",
    "source_revision": source_revision,
    "rule_profile": "metaphysics-lab-common-v1",
    "rule_version": "1.0",
    "cases_checked": 40,
    "cases_matched": matched,
    "mismatches": mismatches,
    "status": "PASS" if matched == 40 and not mismatches else "FAIL",
    "run_timestamp": run_timestamp,
}
```

CLI exits 0 only on PASS。

- [ ] **Step 5: GREEN unit tests**

```bash
python -m unittest tests.test_ziwei_phase2a_qualification_tools.ZiweiPublicQualificationTests -v
```

- [ ] **Step 6: External exact-revision run**

In a temporary validation workflow or verified local checkout, download exactly:

```text
https://raw.githubusercontent.com/SylarLong/iztro/814b77e6371e1050cac31bbf674db3c3138fcfde/src/data/heavenlyStems.ts
```

Then run:

```bash
python tools/qualify_ziwei_phase2a_public.py \
  --source-ts /tmp/heavenlyStems.ts \
  --source-revision 814b77e6371e1050cac31bbf674db3c3138fcfde \
  --output /tmp/public-iztro-evidence.json
```

Expected: `40 / 40`, `mismatches=[]`, `status=PASS`。Network/revision/parser failure is a gate failure, not permission to substitute another revision。

- [ ] **Step 7: Commit public tool + sanitized evidence**

```bash
mkdir -p qualification/ziwei/phase2a
cp /tmp/public-iztro-evidence.json qualification/ziwei/phase2a/public-iztro-814b77e6.json
git add tools/qualify_ziwei_phase2a_public.py tests/test_ziwei_phase2a_qualification_tools.py qualification/ziwei/phase2a/public-iztro-814b77e6.json
git commit -m "test: qualify Ziwei transformation profile"
```

Do not commit the downloaded TypeScript source or temporary validation workflow。

---

### Task 9: Private Astralium Qualification 48 + 4 + 28 = 80 Without Raw Chart in Git

**Files:**
- Create: `tools/qualify_ziwei_phase2a_private.py`
- Extend: `tests/test_ziwei_phase2a_qualification_tools.py`
- Create after successful real run: `qualification/ziwei/phase2a/private-astralium-summary.json`

**Private normalized input schema:**

```json
{
  "source_profile": "astralium-ziwei-v1-common",
  "chart_id": "opaque-private-chart-id",
  "star_locations": [{"star": "...", "palace": "..."}],
  "palace_stems": [{"palace": "...", "heavenly_stem": "..."}],
  "natal_expected_edges": [{"source_palace": "...", "source_stem": "...", "type": "...", "star": "...", "target_palace": "..."}],
  "decadal": {"reference": "...", "stem": "...", "expected_edges": []},
  "yearly": [{"reference": "2023", "stem": "...", "expected_edges": []}],
  "presentation_expected": [{"source_palace": "...", "type": "...", "arrow": "..."}]
}
```

This schema is documented for an untracked `/tmp` file only. The literal `...` in this schema denotes private values supplied by the Project source and is not production code or a committed fixture。

**Output summary must contain no star/palace/stem values from private input.**

- [ ] **Step 1: Add an exact synthetic private-shaped fixture builder in tests**

Append to `tests/test_ziwei_phase2a_qualification_tools.py`:

```python
from engine.ziwei.basis import build_palace_stem_index, build_star_location_index
from engine.ziwei.flying import build_natal_flying_graph, fly_transformations
from engine.ziwei.models import CycleStemSource
from engine.ziwei.transformations import get_transformation_set
from tests.ziwei_phase2a_fixtures import CHART, PROVENANCE, SYNTHETIC_PALACE_STEM_RECORDS, SYNTHETIC_STAR_RECORDS


def synthetic_private_shape():
    stars = build_star_location_index(SYNTHETIC_STAR_RECORDS, CHART, PROVENANCE)
    stems = build_palace_stem_index(SYNTHETIC_PALACE_STEM_RECORDS, CHART, PROVENANCE)
    graph = build_natal_flying_graph(stems, stars)
    natal_expected = [
        {
            "source_palace": edge.source.palace,
            "source_stem": edge.source.heavenly_stem,
            "type": edge.transformation_type.value,
            "star": edge.star,
            "target_palace": edge.target_palace,
        }
        for edge in graph.edges
    ]
    decadal_source = CycleStemSource("cycle_stem", CHART, "decadal", "43-52-virtual-age", "癸")
    decadal_edges = fly_transformations(get_transformation_set("癸"), stars, decadal_source)
    yearly = []
    year_stems = (("2023", "癸"), ("2024", "甲"), ("2025", "乙"), ("2026", "丙"), ("2027", "丁"), ("2028", "戊"), ("2029", "己"))
    for reference, stem in year_stems:
        source = CycleStemSource("cycle_stem", CHART, "yearly", reference, stem)
        edges = fly_transformations(get_transformation_set(stem), stars, source)
        yearly.append({
            "reference": reference,
            "stem": stem,
            "expected_edges": [
                {"type": edge.transformation_type.value, "star": edge.star, "target_palace": edge.target_palace}
                for edge in edges
            ],
        })
    return {
        "source_profile": "synthetic-private-shape-v1",
        "chart_id": CHART.chart_id,
        "star_locations": [{"star": r.star, "palace": r.palace} for r in SYNTHETIC_STAR_RECORDS],
        "palace_stems": [{"palace": r.palace, "heavenly_stem": r.heavenly_stem} for r in SYNTHETIC_PALACE_STEM_RECORDS],
        "natal_expected_edges": natal_expected,
        "decadal": {
            "reference": "43-52-virtual-age",
            "stem": "癸",
            "expected_edges": [
                {"type": edge.transformation_type.value, "star": edge.star, "target_palace": edge.target_palace}
                for edge in decadal_edges
            ],
        },
        "yearly": yearly,
        "presentation_expected": [],
    }
```

This synthetic input deliberately uses production output to test the private runner’s counting/privacy mechanics only；it is not external qualification evidence。

- [ ] **Step 2: Write RED private-summary test**

```python
from tools.qualify_ziwei_phase2a_private import qualify_private


class ZiweiPrivateQualificationTests(unittest.TestCase):
    def test_summary_has_80_counts_and_no_private_payload(self):
        evidence = qualify_private(synthetic_private_shape(), "abc123", "2026-08-21T00:00:00Z")
        self.assertEqual(evidence["natal"]["checked"], 48)
        self.assertEqual(evidence["decadal"]["checked"], 4)
        self.assertEqual(evidence["yearly"]["checked"], 28)
        self.assertEqual(evidence["flying_total"]["checked"], 80)
        self.assertEqual(evidence["flying_total"]["matched"], 80)
        serialized = json.dumps(evidence, ensure_ascii=False)
        for forbidden in ("star_locations", "palace_stems", "expected_edges", "birth_datetime"):
            self.assertNotIn(forbidden, serialized)
        self.assertEqual(evidence["source_digest_sha256"], "abc123")
        self.assertEqual(evidence["status"], "PASS")
```

- [ ] **Step 3: Run RED**

```bash
python -m unittest tests.test_ziwei_phase2a_qualification_tools.ZiweiPrivateQualificationTests -v
```

- [ ] **Step 4: Implement private runner from external facts only**

`qualify_private(payload, digest, run_timestamp)` must:

1. Convert `payload["star_locations"]` and `payload["palace_stems"]` to records and production indexes。
2. Build `NatalFlyingGraph` and compare exactly 48 tuples `(source_palace, source_stem, type, star, target_palace)`。
3. Build one decadal cycle from the supplied external `stem` and compare exactly 4 tuples。
4. Require exactly seven yearly entries and compare exactly 28 tuples。
5. Run presentation comparison separately if `presentation_expected` is non-empty。
6. Return aggregate counts only；mismatch output is `{gate, mismatch_count}` without raw values。
7. Return FAIL unless natal=48/48, decadal=4/4, yearly=28/28。

Use `hashlib.sha256(raw_input_bytes).hexdigest()` in CLI mode; the caller cannot provide a fake digest via CLI。

- [ ] **Step 5: GREEN synthetic tool tests**

```bash
python -m unittest tests.test_ziwei_phase2a_qualification_tools -v
```

- [ ] **Step 6: Prepare real private normalized input outside git**

Use only the Project source `紫微_基礎資料包_2026-08-19.md` and already-validated Project metadata. Create:

```text
/tmp/ziwei-phase2a-astralium-private.json
```

Every expected edge in this file must be transcribed/extracted from the external Project source, never generated by the new engine. Before qualification:

```bash
git status --short
```

Expected: `/tmp` input absent from git status。

- [ ] **Step 7: Run real private qualification**

```bash
python tools/qualify_ziwei_phase2a_private.py \
  --input /tmp/ziwei-phase2a-astralium-private.json \
  --output /tmp/private-astralium-summary.json
```

Required markers:

```text
ASTRALIUM_NATAL_48_PASS
ASTRALIUM_DECADAL_4_PASS
ASTRALIUM_YEARLY_28_PASS
ASTRALIUM_FLYING_80_PASS
```

79/80 or lower stops promotion。Do not edit private expected values before root-cause review。

- [ ] **Step 8: Privacy gate summary before commit**

```bash
python - <<'PY'
import json
from pathlib import Path
p = Path('/tmp/private-astralium-summary.json')
data = json.loads(p.read_text())
serialized = json.dumps(data, ensure_ascii=False)
for forbidden in ('star_locations', 'palace_stems', 'expected_edges', 'birth_datetime', 'name'):
    assert forbidden not in serialized
assert data['flying_total']['checked'] == 80
assert data['flying_total']['matched'] == 80
assert data['status'] == 'PASS'
print('PRIVACY_PASS')
PY
```

- [ ] **Step 9: Commit only runner + aggregate summary**

```bash
mkdir -p qualification/ziwei/phase2a
cp /tmp/private-astralium-summary.json qualification/ziwei/phase2a/private-astralium-summary.json
git add tools/qualify_ziwei_phase2a_private.py tests/test_ziwei_phase2a_qualification_tools.py qualification/ziwei/phase2a/private-astralium-summary.json
git diff --cached --name-only
git commit -m "test: add Ziwei private qualification evidence"
```

Confirm no `/tmp` input, raw Astralium export, birthday/time, or private chart fixture appears in staged files。

---

### Task 10: Stable Promotion + Documentation + Full Regression

**Files:**
- Modify: `engine/ziwei/capabilities.py`
- Modify: `README.md`
- Modify: `VERSION.md`
- Modify: `CHANGELOG.md`
- Modify: `docs/架構說明.md`
- Modify only if wording must sync: `core/命理分析作業規範.md`
- Extend: `tests/test_ziwei_phase2a_capabilities.py`

- [ ] **Step 1: Add RED stable-promotion test**

```python
class ZiweiPhase2AStablePromotionTests(unittest.TestCase):
    def test_core_is_stable_but_remains_on_demand(self):
        for capability_id in ("ziwei.transformations", "ziwei.flying"):
            cap = get_capability(capability_id)
            self.assertEqual(cap["implementation"], "implemented")
            self.assertEqual(cap["maturity"], "stable")
            self.assertEqual(cap["routing"], "on_demand")
            self.assertFalse(should_run_by_default(capability_id))
```

- [ ] **Step 2: Run RED and verify only maturity is experimental**

```bash
python -m unittest tests.test_ziwei_phase2a_capabilities.ZiweiPhase2AStablePromotionTests -v
```

If failure is not `experimental != stable`, investigate before promotion。

- [ ] **Step 3: Promote only the two core capability records**

Set `maturity="stable"`, `routing="on_demand"`, and final `rule_version="1.0"` for `ziwei.transformations` and `ziwei.flying`。Do not change fine-cycle or flowing-stars states。

- [ ] **Step 4: Synchronize docs with exact capability/evidence claims**

Docs must state:

```text
Ziwei transformations = implemented / stable / on_demand
Ziwei flying = implemented / stable / on_demand
Fine-cycle transformations/flying = planned
Flowing stars = planned
Public pinned transformation qualification = 40 / 40
Private Astralium flying qualification = 80 / 80
Private raw chart is not stored in repo
```

`VERSION.md` remains on the current v1.2 development line unless a separate release decision exists；do not invent a release version。

- [ ] **Step 5: Internal Phase 2A suite**

```bash
python -m unittest \
  tests.test_ziwei_phase2a_models \
  tests.test_ziwei_basis \
  tests.test_ziwei_transformations \
  tests.test_ziwei_flying \
  tests.test_ziwei_composition \
  tests.test_ziwei_phase2a_capabilities \
  tests.test_ziwei_phase2a_qualification_tools \
  -v
```

Expected: 0 failures / 0 errors。

- [ ] **Step 6: Existing Ziwei regression**

```bash
python -m unittest discover -s tests -p 'test_*ziwei*.py' -v
```

Expected: 0 failures / 0 errors；existing month/day/hour behavior unchanged。

- [ ] **Step 7: Calendar regression**

```bash
python -m unittest \
  tests.test_calendar_precision \
  tests.test_calendar_models \
  tests.test_calendar_timezone \
  tests.test_calendar_lunar \
  tests.test_calendar_resolver \
  tests.test_calendar_package_exports \
  -v
```

Expected: PASS。

- [ ] **Step 8: Bazi regression**

```bash
python -m unittest discover -s tests -p 'test_*bazi*.py' -v
```

Expected: PASS。

- [ ] **Step 9: Full repo regression**

```bash
python -m unittest discover -v
```

Expected: 0 failures / 0 errors。Record actual test count in PR evidence；do not predeclare a count。

- [ ] **Step 10: Scope + privacy diff gate**

Compare feature branch to exact approved design head. Allowed categories:

```text
engine/ziwei/ Phase 2A files
tests/ziwei_phase2a_fixtures.py
tests/test_ziwei_phase2a_*.py
tests/test_ziwei_basis.py
tests/test_ziwei_transformations.py
tests/test_ziwei_flying.py
tests/test_ziwei_composition.py
tools/qualify_ziwei_phase2a_*.py
qualification/ziwei/phase2a/*.json
README.md
VERSION.md
CHANGELOG.md
docs/架構說明.md
core/命理分析作業規範.md
```

Reject Bazi implementation changes, Qimen, fine-cycle stem resolver, moving stars, raw private fixtures, or temporary validation workflow in product diff。

- [ ] **Step 11: Commit promotion/docs only after all gates are green**

```bash
git add engine/ziwei/capabilities.py README.md VERSION.md CHANGELOG.md docs/架構說明.md tests/test_ziwei_phase2a_capabilities.py
if git diff --quiet -- core/命理分析作業規範.md; then
  true
else
  git add core/命理分析作業規範.md
fi
git commit -m "docs: promote Ziwei Phase 2A capabilities"
```

---

### Task 11: Exact-head Review → Feature→Design → Main Post-merge

**Files:**
- No new product code should be authored in this task。
- Temporary validation workflow exists only on temporary validation branches and is never merged into product branches。

- [ ] **Step 1: Freeze exact feature head**

```bash
git status --short
git rev-parse HEAD
```

Expected: clean tree + recorded exact SHA。

- [ ] **Step 2: Re-run and capture every required marker on exact head**

Required evidence:

```text
TRANSFORMATION_TABLE_PASS
MODEL_INVARIANTS_PASS
GEOMETRY_144_PASS
FLYING_SYNTHETIC_PASS
COMPOSITION_PASS
NEGATIVE_CASES_PASS
PROVENANCE_PASS
AVAILABILITY_PASS
ASTRALIUM_NATAL_48_PASS
ASTRALIUM_DECADAL_4_PASS
ASTRALIUM_YEARLY_28_PASS
ASTRALIUM_PRESENTATION_QUALIFICATION_RECORDED
EXTERNAL_PROFILE_PASS
ZIWEI_REGRESSION_PASS
CALENDAR_REGRESSION_PASS
BAZI_REGRESSION_PASS
FULL_REPO_PASS
SCOPE_PASS
PRIVACY_PASS
```

The validation workflow/script must print each marker only after its underlying check exits successfully；do not print unconditional markers。

- [ ] **Step 3: Full diff review against approved design base**

Reviewer checks:

```text
no scoring or resonance interpretation
no default routing
no fine-cycle transformation runtime
no moving stars
no Calendar/Bazi semantic change
no raw private chart
no last-write-wins input path
cycle source geometric_relation always None
private evidence contains aggregate data only
```

Blocking finding returns to the owning Task and repeats RED→GREEN + regression。

- [ ] **Step 4: Open formal feature→design PR**

PR body includes exact head SHA, changed-file count, actual full test count, 40/40 public qualification, 80/80 private flying qualification, scope/privacy PASS, and explicit out-of-scope list。Do not merge automatically。

- [ ] **Step 5: After explicit approval, squash merge with expected head SHA**

Squash title:

```text
feat: implement Ziwei Transformation & Flying Core v1
```

If head moved after review, stop and repeat exact-head verification。

- [ ] **Step 6: Design post-merge validation**

Create temporary validation branch from exact merged design SHA, add only validation workflow, run complete gates, collect evidence, close validation PR without merge。

- [ ] **Step 7: Compare design→main**

Require `behind_by=0` unless divergence has been explicitly reviewed and resolved。No temporary validation workflow may appear in formal diff。

- [ ] **Step 8: Open design→main PR and wait for explicit approval**

PR must state stable/on-demand core only；fine-cycle transformations/flying and flowing stars remain planned。

- [ ] **Step 9: Merge only after approval, then main post-merge validation**

Temporary branch starts from exact merged main SHA and reruns the complete gate suite。Required final marker:

```text
MAIN_POST_MERGE_PASS
```

Close validation PR without merge。

- [ ] **Step 10: Completion evidence**

Only declare Phase 2A complete when the final record includes:

```text
main merge SHA
actual full test count
public qualification 40/40
private Astralium flying qualification 80/80
SCOPE_PASS
PRIVACY_PASS
MAIN_POST_MERGE_PASS
```

---

## Plan Self-Review Checklist

- [ ] All spec production responsibilities map to Tasks 1–7。
- [ ] All validation/promotion requirements map to Tasks 8–11。
- [ ] Python snippets are Python 3.9 parseable。
- [ ] Every test helper referenced in the plan is explicitly defined。
- [ ] Error codes use the spec contract；profile-shape errors use `invalid_transformation_profile`。
- [ ] Star/palace records are validated before mapping materialization。
- [ ] Cycle sources never enter same/opposite relation classification。
- [ ] Composition never exposes final transformation, score, resonance, or automatic weighting。
- [ ] Fine-cycle transformations/flying and moving stars remain planned/unavailable。
- [ ] Stable promotion occurs only after 40/40 public + 80/80 private qualification + regressions。
- [ ] Private raw chart never enters repo；only aggregate evidence is committed。
- [ ] Existing Ziwei, Calendar, Bazi, full repo, scope/privacy and merged-main validation are hard gates。
- [ ] No failure path permits silent expected-value rewrite。

## Execution Boundary

Implementation must not start until the user reviews and approves this written implementation plan. After approval, create an isolated feature worktree/branch from the exact `design/ziwei-transformation-flying-core` head and execute Task 1 first under TDD. Do not batch Tasks 1–11 into one commit or bypass RED evidence.