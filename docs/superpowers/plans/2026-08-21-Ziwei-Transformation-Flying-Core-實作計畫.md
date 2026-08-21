# Ziwei Transformation & Flying Core v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 依核准的 Phase 2A spec 建立可重現、可驗證、可追溯的紫微十干四化核心、宮干／運限飛化核心、跨 layer Composition 與 qualification / promotion gates，且不啟用流月／流日／流時四化或流曜。

**Architecture:** 四化規則、命盤基準資料、飛化與 Composition 分成獨立 pure modules。`Transformation Core` 只做天干→四化；`Flying Core` 只使用已校驗 natal star locations 產生 edges；`Composition` 只保存不同 scope 的 layer 並提供 readonly query，不做吉凶或權重。Capability 在 internal gates 通過後先進 `implemented / experimental / on_demand`，只有 external qualification、regression、privacy 與 main post-merge gates 全部通過才升 `stable / on_demand`。

**Tech Stack:** Python 3.9+、stdlib `dataclasses` / `enum` / `types.MappingProxyType` / `unittest`、既有 `engine.ziwei` package、GitHub Actions 僅用於臨時 final validation；無新增 runtime dependency。

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
- `engine/ziwei/__init__.py` — 僅 export stable/on-demand Phase 2A public contracts；不得 eager-import experimental fine timing。

### 新增 tests

- `tests/test_ziwei_phase2a_models.py`
- `tests/test_ziwei_basis.py`
- `tests/test_ziwei_transformations.py`
- `tests/test_ziwei_flying.py`
- `tests/test_ziwei_composition.py`
- `tests/test_ziwei_phase2a_capabilities.py`
- `tests/test_ziwei_phase2a_qualification_tools.py`

### 新增 qualification tooling / evidence

- `tools/qualify_ziwei_phase2a_public.py` — 只核對 pinned public 10-stem profile。
- `tools/qualify_ziwei_phase2a_private.py` — 接受 repo 外 private normalized input，輸出 aggregate evidence；不寫 raw values。
- `qualification/ziwei/phase2a/public-iztro-814b77e6.json` — 可重現公開 qualification metadata / 40-of-40 evidence。
- `qualification/ziwei/phase2a/private-astralium-summary.json` — 只含 source profile、digest、counts、status、timestamp 與非敏感 mismatch count；不得含 raw chart。

### 最終同步文件

- `README.md`
- `VERSION.md`
- `CHANGELOG.md`
- `docs/架構說明.md`
- `core/命理分析作業規範.md` 僅在 capability 描述需要同步時修改；不得改盲判／事件校準規則。

---

### Task 1: Phase 2A Error Contract 與 Immutable Core Models

**Files:**
- Create: `engine/ziwei/errors.py`
- Create: `engine/ziwei/models.py`
- Test: `tests/test_ziwei_phase2a_models.py`

**Interfaces:**
- Produces: `ZiweiPhase2AError(code, message, details=None)`
- Produces: `TransformationType`, `Transformation`, `TransformationSet`, `ChartIdentity`, `LayerProvenance`, `StarLocationRecord`, `StarLocationIndex`, `PalaceStemRecord`, `PalaceStemIndex`, `PalaceStemSource`, `CycleStemSource`, `GeometricRelation`, `FlyingEdge`, `LayerIdentity`, `CycleTransformationLayer`, `SmallLimitContext`
- Later tasks must import these types instead of redefining dict shapes。

- [ ] **Step 1: Write RED model/error tests**

```python
# tests/test_ziwei_phase2a_models.py
import unittest
from dataclasses import FrozenInstanceError

from engine.ziwei.errors import ZiweiPhase2AError
from engine.ziwei.models import (
    ChartIdentity,
    GeometricRelation,
    LayerProvenance,
    Transformation,
    TransformationType,
)


class ZiweiPhase2AModelTests(unittest.TestCase):
    def test_error_exposes_stable_code(self):
        err = ZiweiPhase2AError("invalid_palace", "bad palace", {"palace": "X"})
        self.assertEqual(err.code, "invalid_palace")
        self.assertEqual(err.details, {"palace": "X"})

    def test_transformation_type_serialized_values_are_stable(self):
        self.assertEqual(
            [item.value for item in TransformationType],
            ["祿", "權", "科", "忌"],
        )

    def test_transformation_is_immutable(self):
        item = Transformation(TransformationType.LU, "廉貞", 0)
        with self.assertRaises(FrozenInstanceError):
            item.star = "破軍"

    def test_chart_identity_uses_opaque_id(self):
        chart = ChartIdentity("chart-fixture-A", "natal", "synthetic-v1")
        self.assertEqual(chart.chart_id, "chart-fixture-A")

    def test_geometric_relation_values_are_neutral(self):
        self.assertEqual(
            {item.value for item in GeometricRelation},
            {"same_palace", "opposite_palace_incoming", "normal"},
        )
```

- [ ] **Step 2: Run RED and confirm missing module/type failure**

Run:

```bash
python -m unittest tests.test_ziwei_phase2a_models -v
```

Expected: FAIL with `ModuleNotFoundError` for `engine.ziwei.errors` or `engine.ziwei.models`。若因其他原因失敗，先修 test setup，不進 implementation。

- [ ] **Step 3: Add minimal error class**

```python
# engine/ziwei/errors.py
from __future__ import annotations

from typing import Any, Mapping


class ZiweiPhase2AError(ValueError):
    def __init__(
        self,
        code: str,
        message: str,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.details = dict(details or {})
        super().__init__(message)
```

For Python 3.9 compatibility, if `| None` syntax conflicts with repo policy, use `Optional[...]`; keep public semantics identical。

- [ ] **Step 4: Add frozen model definitions with exact enum values**

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
class Transformation:
    type: TransformationType
    star: str
    sequence: int


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
class ChartIdentity:
    chart_id: str
    chart_basis: str
    source_profile: str
```

Continue in this file with the remaining spec dataclasses using immutable tuple/mapping-facing fields. `FlyingEdge.geometric_relation` must be `Optional[GeometricRelation]`; `CycleStemSource` must not expose a palace field。

- [ ] **Step 5: Run model tests GREEN**

```bash
python -m unittest tests.test_ziwei_phase2a_models -v
```

Expected: PASS, 0 failures / 0 errors。

- [ ] **Step 6: Run existing Ziwei module-layout regression**

```bash
python -m unittest tests.test_engine_module_layout tests.test_ziwei_capabilities -v
```

Expected: all existing tests PASS；capability 尚未改動。

- [ ] **Step 7: Commit Task 1**

```bash
git add engine/ziwei/errors.py engine/ziwei/models.py tests/test_ziwei_phase2a_models.py
git commit -m "feat: add Ziwei Phase 2A core models"
```

---

### Task 2: Validated Natal Basis Builders — Duplicate-safe Records → Immutable Index

**Files:**
- Create: `engine/ziwei/basis.py`
- Modify: `engine/ziwei/common.py`
- Test: `tests/test_ziwei_basis.py`

**Interfaces:**
- Consumes: `ChartIdentity`, `LayerProvenance`, `StarLocationRecord`, `StarLocationIndex`, `PalaceStemRecord`, `PalaceStemIndex`, `ZiweiPhase2AError`
- Produces: `build_star_location_index(records, chart_identity, provenance) -> StarLocationIndex`
- Produces: `build_palace_stem_index(records, chart_identity, provenance) -> PalaceStemIndex`
- Produces: `validate_palace(palace) -> None`
- No dict input is accepted as the validation entry point。

- [ ] **Step 1: Write RED duplicate / completeness tests**

```python
# tests/test_ziwei_basis.py
import unittest

from engine.ziwei.basis import build_palace_stem_index, build_star_location_index
from engine.ziwei.common import PALACE_NAMES
from engine.ziwei.errors import ZiweiPhase2AError
from engine.ziwei.models import ChartIdentity, LayerProvenance, PalaceStemRecord, StarLocationRecord


CHART = ChartIdentity("chart-fixture-A", "natal", "synthetic-v1")
PROV = LayerProvenance("validated_source_fact", "synthetic", "1", None, None, None)


class ZiweiBasisTests(unittest.TestCase):
    def test_duplicate_star_is_rejected_even_when_same_palace(self):
        records = [
            StarLocationRecord("天機", "夫妻宮"),
            StarLocationRecord("天機", "夫妻宮"),
        ]
        with self.assertRaises(ZiweiPhase2AError) as cm:
            build_star_location_index(records, CHART, PROV)
        self.assertEqual(cm.exception.code, "duplicate_star_location")

    def test_conflicting_star_location_is_rejected(self):
        records = [
            StarLocationRecord("天機", "夫妻宮"),
            StarLocationRecord("天機", "官祿宮"),
        ]
        with self.assertRaises(ZiweiPhase2AError) as cm:
            build_star_location_index(records, CHART, PROV)
        self.assertEqual(cm.exception.code, "duplicate_star_location")

    def test_palace_stem_index_requires_all_twelve_unique_palaces(self):
        records = [PalaceStemRecord(name, "甲") for name in PALACE_NAMES[:-1]]
        with self.assertRaises(ZiweiPhase2AError) as cm:
            build_palace_stem_index(records, CHART, PROV)
        self.assertEqual(cm.exception.code, "invalid_palace_stem_index")

    def test_duplicate_palace_stem_is_rejected_before_materialization(self):
        records = [PalaceStemRecord(name, "甲") for name in PALACE_NAMES]
        records.append(PalaceStemRecord("命宮", "甲"))
        with self.assertRaises(ZiweiPhase2AError) as cm:
            build_palace_stem_index(records, CHART, PROV)
        self.assertEqual(cm.exception.code, "duplicate_palace_stem")
```

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_ziwei_basis -v
```

Expected: FAIL because `engine.ziwei.basis` does not exist。

- [ ] **Step 3: Add `validate_palace()` to common**

```python
# engine/ziwei/common.py

def validate_palace(palace: str) -> None:
    if palace not in PALACE_NAMES:
        raise ValueError("宮位必須為：" + "、".join(PALACE_NAMES))
```

`basis.py` catches/normalizes invalid palace into `ZiweiPhase2AError(code="invalid_palace", ...)` so Phase 2A error contract is stable while existing common helpers remain backward compatible。

- [ ] **Step 4: Implement record-first builders and immutable mappings**

```python
# engine/ziwei/basis.py
from types import MappingProxyType

from .common import PALACE_NAMES, validate_palace
from .errors import ZiweiPhase2AError
from .models import PalaceStemIndex, StarLocationIndex


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
            raise ZiweiPhase2AError(
                "duplicate_star_location",
                "duplicate star location input",
                {"star": record.star},
            )
        materialized[record.star] = record.palace
    return StarLocationIndex(chart_identity, MappingProxyType(materialized), "validated", provenance)
```

`build_palace_stem_index()` follows the same record-first pattern, rejects duplicate palaces before mapping creation, validates each stem against `甲乙丙丁戊己庚辛壬癸`, and requires `set(materialized) == set(PALACE_NAMES)`。

- [ ] **Step 5: Run basis tests GREEN**

```bash
python -m unittest tests.test_ziwei_basis -v
```

Expected: PASS。

- [ ] **Step 6: Run common/month regressions**

```bash
python -m unittest tests.test_engine_module_layout tests.test_project_ziwei_month -v
```

Expected: PASS；新增 `validate_palace()` 不改既有 `palaces_from_ming_branch()` 行為。

- [ ] **Step 7: Commit Task 2**

```bash
git add engine/ziwei/basis.py engine/ziwei/common.py tests/test_ziwei_basis.py
git commit -m "feat: add validated Ziwei natal basis indexes"
```

---

### Task 3: Versioned 10-Stem Transformation Profile 與 Pure Transformation Core

**Files:**
- Create: `engine/ziwei/transformation_profiles.py`
- Create: `engine/ziwei/transformations.py`
- Test: `tests/test_ziwei_transformations.py`

**Interfaces:**
- Consumes: `Transformation`, `TransformationSet`, `TransformationType`, `LayerProvenance`, `ZiweiPhase2AError`
- Produces: `PROFILE_ID = "metaphysics-lab-common-v1"`
- Produces: `RULE_VERSION = "1.0"`
- Produces: `validate_transformation_profile(profile_id, profile) -> None`
- Produces: `get_transformation_set(heavenly_stem, profile_id=PROFILE_ID) -> TransformationSet`

- [ ] **Step 1: Write RED exhaustive 40-assertion table test**

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
        assertions = 0
        for stem, stars in EXPECTED.items():
            result = get_transformation_set(stem)
            self.assertEqual(tuple(item.star for item in result.transformations), stars)
            self.assertEqual(tuple(item.sequence for item in result.transformations), (0, 1, 2, 3))
            assertions += 4
        self.assertEqual(assertions, 40)

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

Expected: FAIL because transformation modules do not exist。

- [ ] **Step 3: Implement exact profile data and validation**

```python
# engine/ziwei/transformation_profiles.py
PROFILE_ID = "metaphysics-lab-common-v1"
RULE_VERSION = "1.0"
TYPE_ORDER = ("祿", "權", "科", "忌")

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
```

`validate_transformation_profile()` must assert exactly 10 legal stems, exactly four stars for each stem, non-empty star strings, non-empty profile/version, and no hidden fallback。

- [ ] **Step 4: Implement pure core**

```python
# engine/ziwei/transformations.py
from .errors import ZiweiPhase2AError
from .models import LayerProvenance, Transformation, TransformationSet, TransformationType
from .transformation_profiles import PROFILE, PROFILE_ID, RULE_VERSION, validate_transformation_profile


def get_transformation_set(heavenly_stem: str, profile_id: str = PROFILE_ID) -> TransformationSet:
    if profile_id != PROFILE_ID:
        raise ZiweiPhase2AError("unknown_profile", "unknown Ziwei transformation profile", {"profile_id": profile_id})
    validate_transformation_profile(PROFILE_ID, PROFILE)
    if heavenly_stem not in PROFILE:
        raise ZiweiPhase2AError("invalid_heavenly_stem", "invalid heavenly stem", {"heavenly_stem": heavenly_stem})
    types = tuple(TransformationType)
    items = tuple(
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
    return TransformationSet(heavenly_stem, PROFILE_ID, RULE_VERSION, items, provenance)
```

- [ ] **Step 5: Run transformation tests GREEN and print gate evidence**

```bash
python -m unittest tests.test_ziwei_transformations -v
python - <<'PY'
from engine.ziwei.transformations import get_transformation_set
for stem in "甲乙丙丁戊己庚辛壬癸":
    assert len(get_transformation_set(stem).transformations) == 4
print("TRANSFORMATION_TABLE_PASS 40/40")
PY
```

Expected: unit tests PASS and exact marker `TRANSFORMATION_TABLE_PASS 40/40`。

- [ ] **Step 6: Commit Task 3**

```bash
git add engine/ziwei/transformation_profiles.py engine/ziwei/transformations.py tests/test_ziwei_transformations.py
git commit -m "feat: add versioned Ziwei transformation core"
```

---

### Task 4: Palace Geometry 與 4-edge Flying Core

**Files:**
- Modify: `engine/ziwei/common.py`
- Create: `engine/ziwei/flying.py`
- Test: `tests/test_ziwei_flying.py`

**Interfaces:**
- Consumes: `TransformationSet`, `StarLocationIndex`, `PalaceStemSource`, `CycleStemSource`, `FlyingEdge`, `GeometricRelation`
- Produces: `opposite_palace(palace) -> str`
- Produces: `classify_geometric_relation(source, target_palace) -> GeometricRelation | None`
- Produces: `fly_transformations(transformations, star_locations, source) -> tuple[FlyingEdge, ...]`

- [ ] **Step 1: Write RED exhaustive 144-geometry test and cycle exclusion test**

```python
# tests/test_ziwei_flying.py
import unittest

from engine.ziwei.common import PALACE_NAMES, opposite_palace
from engine.ziwei.flying import classify_geometric_relation
from engine.ziwei.models import ChartIdentity, CycleStemSource, GeometricRelation, PalaceStemSource


CHART = ChartIdentity("chart-fixture-A", "natal", "synthetic-v1")


class ZiweiFlyingGeometryTests(unittest.TestCase):
    def test_all_144_palace_pairs_classify_exactly(self):
        counts = {item: 0 for item in GeometricRelation}
        for source_palace in PALACE_NAMES:
            source = PalaceStemSource("palace_stem", CHART, source_palace, "甲")
            for target in PALACE_NAMES:
                relation = classify_geometric_relation(source, target)
                counts[relation] += 1
        self.assertEqual(counts[GeometricRelation.SAME_PALACE], 12)
        self.assertEqual(counts[GeometricRelation.OPPOSITE_PALACE_INCOMING], 12)
        self.assertEqual(counts[GeometricRelation.NORMAL], 120)

    def test_opposite_palace_is_symmetric(self):
        for palace in PALACE_NAMES:
            self.assertEqual(opposite_palace(opposite_palace(palace)), palace)

    def test_cycle_source_has_no_self_relation(self):
        source = CycleStemSource("cycle_stem", CHART, "yearly", "2026", "丙")
        self.assertIsNone(classify_geometric_relation(source, "田宅宮"))
```

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_ziwei_flying.ZiweiFlyingGeometryTests -v
```

Expected: FAIL due missing `opposite_palace` / `flying` module。

- [ ] **Step 3: Implement single-source opposite helper**

```python
# engine/ziwei/common.py

def opposite_palace(palace: str) -> str:
    validate_palace(palace)
    idx = PALACE_NAMES.index(palace)
    return PALACE_NAMES[(idx + 6) % 12]
```

- [ ] **Step 4: Implement relation classifier**

```python
# engine/ziwei/flying.py
from .common import opposite_palace
from .models import CycleStemSource, GeometricRelation, PalaceStemSource


def classify_geometric_relation(source, target_palace):
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

- [ ] **Step 5: Add RED 4-edge flying tests**

```python
class ZiweiFlyingEdgeTests(unittest.TestCase):
    def test_cycle_transformation_set_creates_exactly_four_edges(self):
        from engine.ziwei.basis import build_star_location_index
        from engine.ziwei.models import LayerProvenance, StarLocationRecord
        from engine.ziwei.transformations import get_transformation_set
        from engine.ziwei.flying import fly_transformations

        prov = LayerProvenance("validated_source_fact", "synthetic", "1", None, None, None)
        index = build_star_location_index([
            StarLocationRecord("天同", "遷移宮"),
            StarLocationRecord("天機", "夫妻宮"),
            StarLocationRecord("文昌", "疾厄宮"),
            StarLocationRecord("廉貞", "田宅宮"),
        ], CHART, prov)
        source = CycleStemSource("cycle_stem", CHART, "yearly", "2026", "丙")
        edges = fly_transformations(get_transformation_set("丙"), index, source)
        self.assertEqual(len(edges), 4)
        self.assertEqual(tuple(edge.target_palace for edge in edges), ("遷移宮", "夫妻宮", "疾厄宮", "田宅宮"))
        self.assertTrue(all(edge.geometric_relation is None for edge in edges))
```

Run and confirm RED specifically because `fly_transformations` is missing。

- [ ] **Step 6: Implement minimal flying and hard chart-basis checks**

`fly_transformations()` must:

```python
if source.chart_identity != star_locations.chart_identity:
    raise ZiweiPhase2AError("chart_basis_mismatch", "source and star index belong to different charts")

for transformation in transformations.transformations:
    if transformation.star not in star_locations.locations:
        raise ZiweiPhase2AError(
            "missing_star_location",
            "transformation star has no natal location",
            {"star": transformation.star},
        )
```

Then create exactly four immutable `FlyingEdge` items with `target_basis="natal_star_location"` and relation from the classifier。

- [ ] **Step 7: Run full flying tests GREEN and gate evidence**

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

Expected: tests PASS + `GEOMETRY_144_PASS`。

- [ ] **Step 8: Commit Task 4**

```bash
git add engine/ziwei/common.py engine/ziwei/flying.py tests/test_ziwei_flying.py
git commit -m "feat: add Ziwei flying geometry and edges"
```

---

### Task 5: 48-edge NatalFlyingGraph 與 Astralium-compatible Presentation Mapping

**Files:**
- Modify: `engine/ziwei/flying.py`
- Extend: `tests/test_ziwei_flying.py`

**Interfaces:**
- Consumes: `PalaceStemIndex`, `StarLocationIndex`, `get_transformation_set()`
- Produces: `build_natal_flying_graph(palace_stems, star_locations, profile_id=PROFILE_ID) -> NatalFlyingGraph`
- Produces: `presentation_relation(edge, profile_id="astralium-compatible-v1") -> str | None`

- [ ] **Step 1: Write RED synthetic 48-edge graph test**

```python
class ZiweiNatalFlyingGraphTests(unittest.TestCase):
    def test_twelve_palaces_create_exactly_forty_eight_edges(self):
        from engine.ziwei.basis import build_palace_stem_index, build_star_location_index
        from engine.ziwei.flying import build_natal_flying_graph
        from engine.ziwei.models import LayerProvenance, PalaceStemRecord, StarLocationRecord

        prov = LayerProvenance("validated_source_fact", "synthetic", "1", None, None, None)
        palace_records = [PalaceStemRecord(name, "甲") for name in PALACE_NAMES]
        star_records = [
            StarLocationRecord("廉貞", "命宮"),
            StarLocationRecord("破軍", "遷移宮"),
            StarLocationRecord("武曲", "官祿宮"),
            StarLocationRecord("太陽", "財帛宮"),
        ]
        graph = build_natal_flying_graph(
            build_palace_stem_index(palace_records, CHART, prov),
            build_star_location_index(star_records, CHART, prov),
        )
        self.assertEqual(len(graph.edges), 48)
        self.assertEqual(sum(len(v) for v in graph.outgoing_index.values()), 48)
        self.assertEqual(sum(len(v) for v in graph.incoming_index.values()), 48)
```

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_ziwei_flying.ZiweiNatalFlyingGraphTests -v
```

Expected: FAIL because graph builder is missing。

- [ ] **Step 3: Implement graph builder without re-placing stars**

```python
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
    return _materialize_graph(tuple(edges), palace_stems.chart_identity)
```

`_materialize_graph()` builds immutable outgoing/incoming indexes from the already-created edges only；不得 call transformation core again。

- [ ] **Step 4: Add RED presentation tests from neutral geometry**

```python
class ZiweiPresentationRelationTests(unittest.TestCase):
    def test_same_palace_maps_to_down_arrow(self):
        edge = make_synthetic_edge(GeometricRelation.SAME_PALACE)
        self.assertEqual(presentation_relation(edge), "↓")

    def test_opposite_incoming_maps_to_up_arrow(self):
        edge = make_synthetic_edge(GeometricRelation.OPPOSITE_PALACE_INCOMING)
        self.assertEqual(presentation_relation(edge), "↑")

    def test_normal_and_cycle_edges_have_no_arrow(self):
        self.assertIsNone(presentation_relation(make_synthetic_edge(GeometricRelation.NORMAL)))
        self.assertIsNone(presentation_relation(make_synthetic_edge(None)))
```

The test helper must construct only synthetic `FlyingEdge` values and contain no private chart data。

- [ ] **Step 5: Implement presentation mapping as a separate function/profile**

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

Do not rename enum values to `outward_self` / `inward_self`。

- [ ] **Step 6: Run Task 5 tests GREEN**

```bash
python -m unittest tests.test_ziwei_flying -v
```

Expected: PASS，synthetic graph exactly 48 edges。

- [ ] **Step 7: Commit Task 5**

```bash
git add engine/ziwei/flying.py tests/test_ziwei_flying.py
git commit -m "feat: add Ziwei natal flying graph"
```

---

### Task 6: Composition Layer — No-overwrite, Conflict, Availability, Readonly Queries

**Files:**
- Create: `engine/ziwei/composition.py`
- Test: `tests/test_ziwei_composition.py`

**Interfaces:**
- Consumes: `ChartIdentity`, `LayerIdentity`, `CycleStemSource`, `TransformationSet`, `FlyingEdge`, `NatalFlyingGraph`, `SmallLimitContext`
- Produces: `build_cycle_layer(identity, source, transformations, flying_edges, provenance, earthly_branch=None) -> CycleTransformationLayer`
- Produces: `build_layer_stack(chart_identity, natal, cycles=(), small_limit=None) -> ZiweiLayerStack`
- Produces: `ZiweiCompositeView(stack).for_palace(palace)` / `.for_star(star)` / `.for_transformation(type)`
- Produces constant unavailable fine-cycle reason `fine_cycle_stem_resolver_not_enabled`。

- [ ] **Step 1: Write RED no-overwrite and conflict tests**

```python
# tests/test_ziwei_composition.py
import unittest

from engine.ziwei.composition import build_layer_stack
from engine.ziwei.errors import ZiweiPhase2AError


class ZiweiCompositionTests(unittest.TestCase):
    def test_same_star_transformations_from_different_scopes_all_survive(self):
        stack = make_stack_with_star_layers(
            star="天機",
            entries=(("birth_year", "祿"), ("decadal", "科"), ("yearly", "權")),
        )
        result = stack.view().for_star("天機")
        self.assertEqual(
            tuple((item.scope, item.transformation_type.value) for item in result.transformations),
            (("birth_year", "祿"), ("decadal", "科"), ("yearly", "權")),
        )

    def test_same_layer_identity_conflicting_stem_fails_closed(self):
        layer_a = make_year_layer("2026", "丙")
        layer_b = make_year_layer("2026", "丁")
        with self.assertRaises(ZiweiPhase2AError) as cm:
            build_layer_stack(CHART, make_natal_context(), (layer_a, layer_b))
        self.assertEqual(cm.exception.code, "layer_conflict")

    def test_exact_duplicate_layer_identity_is_not_silently_collapsed(self):
        layer = make_year_layer("2026", "丙")
        with self.assertRaises(ZiweiPhase2AError) as cm:
            build_layer_stack(CHART, make_natal_context(), (layer, layer))
        self.assertEqual(cm.exception.code, "duplicate_layer_identity")
```

Helpers in this test file use synthetic models only；they may call public builders from Tasks 2–5 but may not use private chart fixtures。

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_ziwei_composition -v
```

Expected: FAIL because `composition.py` does not exist。

- [ ] **Step 3: Implement strict cycle-layer construction**

```python
def build_cycle_layer(identity, source, transformations, flying_edges, provenance, earthly_branch=None):
    if len(transformations.transformations) != 4 or len(flying_edges) != 4:
        raise ZiweiPhase2AError("unsupported_scope", "cycle transformation layer requires exactly four transformations and four edges")
    if source.chart_identity.chart_id != identity.chart_id:
        raise ZiweiPhase2AError("chart_basis_mismatch", "layer identity and source chart mismatch")
    if source.scope not in {"birth_year", "decadal", "yearly"}:
        raise ZiweiPhase2AError("unsupported_scope", "Phase 2A does not execute fine-cycle transformations", {"scope": source.scope})
    return CycleTransformationLayer(...)
```

The actual constructor uses the exact dataclass field order from Task 1; do not introduce dict-only layer shapes。

- [ ] **Step 4: Implement `ZiweiLayerStack` conflict checks**

Use an identity-key map only after all input layer records have been inspected. If an identity repeats:

```python
if existing is not None:
    if existing == layer:
        raise ZiweiPhase2AError("duplicate_layer_identity", "duplicate layer identity")
    raise ZiweiPhase2AError("layer_conflict", "conflicting facts for one layer identity")
```

Do not let a dict assignment decide which layer survives。

- [ ] **Step 5: Add RED availability and query tests**

```python
class ZiweiCompositeViewTests(unittest.TestCase):
    def test_fine_cycle_transformations_remain_unavailable(self):
        stack = make_minimal_stack()
        self.assertEqual(stack.availability["monthly_transformations"].status, "unavailable")
        self.assertEqual(stack.availability["monthly_transformations"].reason, "fine_cycle_stem_resolver_not_enabled")
        self.assertEqual(stack.availability["daily_transformations"].status, "unavailable")
        self.assertEqual(stack.availability["hourly_transformations"].status, "unavailable")

    def test_for_transformation_keeps_scope_identity(self):
        view = make_multi_layer_stack().view()
        rows = view.for_transformation(TransformationType.JI)
        self.assertEqual(tuple(row.scope for row in rows), ("birth_year", "decadal", "yearly"))

    def test_for_palace_never_returns_score_or_resonance(self):
        palace_view = make_multi_layer_stack().view().for_palace("夫妻宮")
        self.assertFalse(hasattr(palace_view, "score"))
        self.assertFalse(hasattr(palace_view, "resonance"))
```

- [ ] **Step 6: Implement readonly view and availability records**

`ZiweiCompositeView` may calculate indexes at construction time, but returned collections must be tuples / frozen records. It must not mutate `ZiweiLayerStack` or create new metaphysical facts。

Fine-cycle availability must be hard-coded to `unavailable` in Phase 2A runtime; no caller flag may override it。

- [ ] **Step 7: Run Composition tests GREEN**

```bash
python -m unittest tests.test_ziwei_composition -v
```

Expected: PASS and no output field representing `final_transformation`, `score`, or `resonance`。

- [ ] **Step 8: Run Phase 2A internal suite so far**

```bash
python -m unittest \
  tests.test_ziwei_phase2a_models \
  tests.test_ziwei_basis \
  tests.test_ziwei_transformations \
  tests.test_ziwei_flying \
  tests.test_ziwei_composition \
  -v
```

Expected: 0 failures / 0 errors。

- [ ] **Step 9: Commit Task 6**

```bash
git add engine/ziwei/composition.py tests/test_ziwei_composition.py
git commit -m "feat: add Ziwei transformation layer composition"
```

---

### Task 7: Capability Lifecycle 與 Public Package Boundary

**Files:**
- Modify: `engine/ziwei/capabilities.py`
- Modify: `engine/ziwei/__init__.py`
- Create: `tests/test_ziwei_phase2a_capabilities.py`
- Modify only if needed for export regression: `tests/test_engine_module_layout.py`

**Interfaces:**
- `ziwei.transformations` and `ziwei.flying` become `implemented / experimental / on_demand` after Tasks 1–6 internal gates PASS。
- Fine-cycle transformation/flying capability ids are added only as `planned / on_demand` with explicit dependencies。
- `ziwei.flowing_stars` remains planned。

- [ ] **Step 1: Write RED capability-state tests**

```python
# tests/test_ziwei_phase2a_capabilities.py
import unittest

from engine.ziwei.capabilities import can_execute, get_capability, should_run_by_default


class ZiweiPhase2ACapabilityTests(unittest.TestCase):
    def test_core_capabilities_are_experimental_on_demand_after_internal_gates(self):
        for capability_id in ("ziwei.transformations", "ziwei.flying"):
            cap = get_capability(capability_id)
            self.assertEqual(cap["implementation"], "implemented")
            self.assertEqual(cap["maturity"], "experimental")
            self.assertEqual(cap["routing"], "on_demand")
            self.assertTrue(can_execute(capability_id))
            self.assertFalse(should_run_by_default(capability_id))

    def test_fine_cycle_transformations_remain_planned(self):
        for capability_id in (
            "ziwei.flow_month_transformations",
            "ziwei.flow_day_transformations",
            "ziwei.flow_hour_transformations",
            "ziwei.flow_month_flying",
            "ziwei.flow_day_flying",
            "ziwei.flow_hour_flying",
        ):
            cap = get_capability(capability_id)
            self.assertEqual(cap["implementation"], "planned")
            self.assertFalse(can_execute(capability_id))

    def test_flowing_stars_remain_planned(self):
        self.assertEqual(get_capability("ziwei.flowing_stars")["implementation"], "planned")
```

- [ ] **Step 2: Run RED and verify current planned state is the reason**

```bash
python -m unittest tests.test_ziwei_phase2a_capabilities -v
```

Expected: FAIL because transformations/flying are still `planned` and fine-cycle capability ids do not yet exist。

- [ ] **Step 3: Update registry to experimental/on-demand only**

Set:

```python
"ziwei.transformations": {
    "implementation": "implemented",
    "maturity": "experimental",
    "routing": "on_demand",
    "rule_version": "1.0-exp",
    "module": "engine.ziwei.transformations",
    "dependencies": (),
}
```

`ziwei.flying` depends on `ziwei.transformations`。Fine-cycle transformation capabilities depend on their corresponding existing palace timing capability plus `ziwei.transformations`, but stay `planned` with `maturity=None`。Fine-cycle flying depends on corresponding fine-cycle transformations plus `ziwei.flying`, but stays `planned`。

- [ ] **Step 4: Add only intended package exports**

`engine/ziwei/__init__.py` may export stable structural contracts such as `get_transformation_set`, but must not make fine-cycle transformation functions appear because they do not exist. Existing stable month exports remain unchanged。

- [ ] **Step 5: Run capability + existing Ziwei regressions GREEN**

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

Expected: PASS；existing month/day/hour maturity/routing unchanged。

- [ ] **Step 6: Commit Task 7**

```bash
git add engine/ziwei/capabilities.py engine/ziwei/__init__.py tests/test_ziwei_phase2a_capabilities.py tests/test_engine_module_layout.py
git commit -m "feat: register Ziwei Phase 2A capabilities"
```

If `tests/test_engine_module_layout.py` required no change, omit it from `git add`。

---

### Task 8: Public Pinned Qualification Tool — iztro 40/40

**Files:**
- Create: `tools/qualify_ziwei_phase2a_public.py`
- Create: `tests/test_ziwei_phase2a_qualification_tools.py`
- Create after successful run: `qualification/ziwei/phase2a/public-iztro-814b77e6.json`

**Interfaces:**
- Produces CLI:
  `python tools/qualify_ziwei_phase2a_public.py --source-json <path> --output <path>`
- `source-json` is a local extraction of pinned `SylarLong/iztro@814b77e6.../src/data/heavenlyStems.ts` converted to neutral JSON by the validation workflow; runtime library does not fetch network。
- Output evidence schema: `source_name`, `source_revision`, `rule_profile`, `rule_version`, `cases_checked=40`, `cases_matched`, `mismatches`, `status`, `run_timestamp`。

- [ ] **Step 1: Write RED evidence-schema / mismatch tests**

```python
# tests/test_ziwei_phase2a_qualification_tools.py
import json
import tempfile
import unittest
from pathlib import Path

from tools.qualify_ziwei_phase2a_public import qualify_public_profile


class ZiweiPublicQualificationToolTests(unittest.TestCase):
    def test_exact_public_profile_produces_40_of_40_pass(self):
        source = {
            "甲": ["廉貞", "破軍", "武曲", "太陽"],
            "乙": ["天機", "天梁", "紫微", "太陰"],
            "丙": ["天同", "天機", "文昌", "廉貞"],
            "丁": ["太陰", "天同", "天機", "巨門"],
            "戊": ["貪狼", "太陰", "右弼", "天機"],
            "己": ["武曲", "貪狼", "天梁", "文曲"],
            "庚": ["太陽", "武曲", "太陰", "天同"],
            "辛": ["巨門", "太陽", "文曲", "文昌"],
            "壬": ["天梁", "紫微", "左輔", "武曲"],
            "癸": ["破軍", "巨門", "太陰", "貪狼"],
        }
        evidence = qualify_public_profile(source, "814b77e6371e1050cac31bbf674db3c3138fcfde")
        self.assertEqual(evidence["cases_checked"], 40)
        self.assertEqual(evidence["cases_matched"], 40)
        self.assertEqual(evidence["mismatches"], [])
        self.assertEqual(evidence["status"], "PASS")

    def test_one_public_mismatch_fails_closed(self):
        source = exact_public_source_fixture()
        source["丙"][3] = "天機"
        evidence = qualify_public_profile(source, "814b77e6371e1050cac31bbf674db3c3138fcfde")
        self.assertEqual(evidence["status"], "FAIL")
        self.assertEqual(evidence["cases_matched"], 39)
```

`exact_public_source_fixture()` returns the same explicit 10-stem neutral fixture in this test module；do not import the production profile as the expected oracle。

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_ziwei_phase2a_qualification_tools.ZiweiPublicQualificationToolTests -v
```

Expected: FAIL because tool does not exist。

- [ ] **Step 3: Implement public qualification as comparison, not fallback**

```python
def qualify_public_profile(source_table, source_revision):
    mismatches = []
    checked = 0
    matched = 0
    for stem in "甲乙丙丁戊己庚辛壬癸":
        project = tuple(item.star for item in get_transformation_set(stem).transformations)
        external = tuple(source_table[stem])
        for idx, (actual, expected) in enumerate(zip(project, external)):
            checked += 1
            if actual == expected:
                matched += 1
            else:
                mismatches.append({"stem": stem, "sequence": idx, "project": actual, "external": expected})
    return {
        "source_name": "SylarLong/iztro",
        "source_revision": source_revision,
        "rule_profile": PROFILE_ID,
        "rule_version": RULE_VERSION,
        "cases_checked": checked,
        "cases_matched": matched,
        "mismatches": mismatches,
        "status": "PASS" if not mismatches and checked == 40 else "FAIL",
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
    }
```

The CLI exits non-zero on `FAIL`。

- [ ] **Step 4: Run tests GREEN**

```bash
python -m unittest tests.test_ziwei_phase2a_qualification_tools.ZiweiPublicQualificationToolTests -v
```

Expected: PASS。

- [ ] **Step 5: Run pinned public qualification in a temporary validation workflow**

The workflow must fetch the exact raw source at commit `814b77e6371e1050cac31bbf674db3c3138fcfde`, transform only the `mutagen` arrays to the neutral JSON schema, then run:

```bash
python tools/qualify_ziwei_phase2a_public.py \
  --source-json /tmp/iztro-mutagen.json \
  --output /tmp/public-iztro-evidence.json
```

Expected evidence: `cases_checked=40`, `cases_matched=40`, `mismatches=[]`, `status=PASS`。If network fetch, parse, revision, or 40/40 check fails, stop before committing evidence。

- [ ] **Step 6: Commit only sanitized public evidence**

Copy the successful evidence payload to:

```text
qualification/ziwei/phase2a/public-iztro-814b77e6.json
```

Then:

```bash
git add tools/qualify_ziwei_phase2a_public.py tests/test_ziwei_phase2a_qualification_tools.py qualification/ziwei/phase2a/public-iztro-814b77e6.json
git commit -m "test: qualify Ziwei transformation profile"
```

Do not commit downloaded iztro source code or temporary workflow unless the final design explicitly needs a reusable non-product validation workflow。

---

### Task 9: Private Astralium Qualification — 48 + 4 + 28 Exact Flying Edges Without Committing Chart Data

**Files:**
- Create: `tools/qualify_ziwei_phase2a_private.py`
- Extend: `tests/test_ziwei_phase2a_qualification_tools.py`
- Create after successful private run: `qualification/ziwei/phase2a/private-astralium-summary.json`
- No private input file may be added to git。

**Interfaces:**
- CLI:
  `python tools/qualify_ziwei_phase2a_private.py --input <private-json-outside-repo> --output <summary-json>`
- Private normalized input schema contains `chart_identity`, `star_locations`, `palace_stems`, `natal_expected_edges`, `decadal`, `yearly[]`, and optional `presentation_relations`。
- Output summary contains no stars/palaces/stems from the private chart；only source profile id, SHA-256 of normalized input bytes, counts, status, timestamp, and mismatch count by gate。

- [ ] **Step 1: Write RED privacy-preserving summary tests with synthetic private-shaped input**

```python
class ZiweiPrivateQualificationToolTests(unittest.TestCase):
    def test_summary_contains_counts_and_digest_but_no_private_edges(self):
        private_fixture = synthetic_private_qualification_fixture()
        evidence = qualify_private(private_fixture, raw_digest="abc123")
        self.assertEqual(evidence["natal"]["checked"], 48)
        self.assertEqual(evidence["decadal"]["checked"], 4)
        self.assertEqual(evidence["yearly"]["checked"], 28)
        self.assertEqual(evidence["flying_total"]["checked"], 80)
        self.assertNotIn("star_locations", evidence)
        self.assertNotIn("palace_stems", evidence)
        self.assertNotIn("expected_edges", json.dumps(evidence, ensure_ascii=False))
        self.assertEqual(evidence["source_digest_sha256"], "abc123")
```

`synthetic_private_qualification_fixture()` must generate a synthetic 12-palace chart and 7 synthetic yearly layers; it must not copy the user chart。

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_ziwei_phase2a_qualification_tools.ZiweiPrivateQualificationToolTests -v
```

Expected: FAIL because private tool does not exist。

- [ ] **Step 3: Implement private qualification runner**

The runner must:

1. Build `StarLocationIndex` and `PalaceStemIndex` through production builders。
2. Build the 48-edge natal graph and compare exact edge tuples `(source_palace, source_stem, transformation_type, star, target_palace)` against private expected data。
3. Build one decadal 4-edge cycle and compare exact tuples。
4. Build seven yearly 4-edge cycles and compare exact tuples, requiring `7 * 4 = 28`。
5. Record presentation relation qualification separately from flying correctness。
6. Return `FAIL` if any of 80 flying edges mismatch。
7. Never copy raw private tuples into output summary；only mismatch counts and gate names。

- [ ] **Step 4: Run synthetic tool tests GREEN**

```bash
python -m unittest tests.test_ziwei_phase2a_qualification_tools -v
```

Expected: PASS。

- [ ] **Step 5: Prepare the real private normalized input outside git from the Project source**

Use the Project source `紫微_基礎資料包_2026-08-19.md` only in the execution environment. Normalize it to a temporary file such as:

```text
/tmp/ziwei-phase2a-astralium-private.json
```

Before running qualification, verify:

```bash
git status --short
```

Expected: the `/tmp` file does not appear in git status。

The normalized input must encode exactly the externally supplied facts required by the spec: 12 palace stems, natal star locations needed by all transformed stars, 48 natal expected edges, one 4-edge decadal result, and 2023–2029 seven yearly 4-edge results. Do not infer missing private facts from the new engine; qualification inputs must come from the external Project source only。

- [ ] **Step 6: Run real private qualification and require exact gates**

```bash
python tools/qualify_ziwei_phase2a_private.py \
  --input /tmp/ziwei-phase2a-astralium-private.json \
  --output /tmp/private-astralium-summary.json
```

Expected:

```text
ASTRALIUM_NATAL_48_PASS
ASTRALIUM_DECADAL_4_PASS
ASTRALIUM_YEARLY_28_PASS
flying_total = 80 / 80
status = PASS
```

Any 79/80 or lower result stops promotion. Do not modify private expected values to make the gate green before root-cause review。

- [ ] **Step 7: Privacy review the summary before commit**

Run:

```bash
python - <<'PY'
import json
from pathlib import Path
p = Path('/tmp/private-astralium-summary.json')
data = json.loads(p.read_text())
for forbidden in ('star_locations', 'palace_stems', 'expected_edges', 'birth_datetime', 'name'):
    assert forbidden not in json.dumps(data, ensure_ascii=False)
assert data['flying_total']['checked'] == 80
assert data['flying_total']['matched'] == 80
assert data['status'] == 'PASS'
print('PRIVACY_PASS')
PY
```

Expected: `PRIVACY_PASS`。

- [ ] **Step 8: Commit runner + aggregate summary only**

```bash
mkdir -p qualification/ziwei/phase2a
cp /tmp/private-astralium-summary.json qualification/ziwei/phase2a/private-astralium-summary.json
git add tools/qualify_ziwei_phase2a_private.py tests/test_ziwei_phase2a_qualification_tools.py qualification/ziwei/phase2a/private-astralium-summary.json
git commit -m "test: add Ziwei private qualification evidence"
```

Before commit, run `git diff --cached --name-only` and manually confirm the temporary private input path is absent。

---

### Task 10: Stable Promotion, Documentation Sync, and Full Regression

**Files:**
- Modify: `engine/ziwei/capabilities.py`
- Modify: `README.md`
- Modify: `VERSION.md`
- Modify: `CHANGELOG.md`
- Modify: `docs/架構說明.md`
- Modify only if capability wording requires it: `core/命理分析作業規範.md`
- Extend: `tests/test_ziwei_phase2a_capabilities.py`

**Interfaces:**
- After all Task 1–9 internal + external gates PASS, promote only:
  - `ziwei.transformations = implemented / stable / on_demand`
  - `ziwei.flying = implemented / stable / on_demand`
- All fine-cycle transformation/flying and `ziwei.flowing_stars` remain planned。

- [ ] **Step 1: Write RED stable-promotion assertions before changing registry**

```python
class ZiweiPhase2AStablePromotionTests(unittest.TestCase):
    def test_core_capabilities_are_stable_but_still_on_demand(self):
        for capability_id in ("ziwei.transformations", "ziwei.flying"):
            cap = get_capability(capability_id)
            self.assertEqual(cap["implementation"], "implemented")
            self.assertEqual(cap["maturity"], "stable")
            self.assertEqual(cap["routing"], "on_demand")
            self.assertFalse(should_run_by_default(capability_id))
```

- [ ] **Step 2: Run RED and confirm only maturity is still experimental**

```bash
python -m unittest tests.test_ziwei_phase2a_capabilities.ZiweiPhase2AStablePromotionTests -v
```

Expected: FAIL with `experimental != stable`。If failure is different, investigate before promotion。

- [ ] **Step 3: Promote registry to stable/on_demand**

Change only `maturity` / final `rule_version` metadata for the two core capabilities. Do not change routing to default and do not touch existing month/day/hour states。

- [ ] **Step 4: Update documentation to match implemented capability exactly**

Required statements:

```text
Ziwei transformations: implemented / stable / on_demand
Ziwei flying: implemented / stable / on_demand
Fine-cycle transformations/flying: planned
Flowing stars: planned
Private Astralium flying qualification: 80 / 80 exact
Public pinned transformation qualification: 40 / 40 exact
No private raw chart is stored in repo
```

`VERSION.md` remains on the existing v1.2 development line unless a separate release decision exists; do not invent a new Core release number in this task。

- [ ] **Step 5: Run Phase 2A internal suite**

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

- [ ] **Step 6: Run all Ziwei regression tests**

```bash
python -m unittest discover -s tests -p 'test_*ziwei*.py' -v
```

Expected: 0 failures / 0 errors；month/day/hour capability states unchanged。

- [ ] **Step 7: Run Calendar regression**

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

Expected: 0 failures / 0 errors。

- [ ] **Step 8: Run Bazi regression**

```bash
python -m unittest tests.test_project_bazi_calendar -v
```

Then include any additional Bazi-named tests returned by `python -m unittest discover -s tests -p 'test_*bazi*.py' -v`。Expected: all PASS。

- [ ] **Step 9: Run full repository regression**

```bash
python -m unittest discover -v
```

Expected: 0 failures / 0 errors。Record the exact total test count in PR evidence；do not hardcode a predicted count in docs before execution。

- [ ] **Step 10: Run scope and privacy gates**

Compare feature branch against its exact design-branch base. Allowed diff categories:

```text
engine/ziwei/* Phase 2A files
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

Reject any diff under Bazi implementation, Qimen, moving stars, fine-cycle stem resolver, or private fixture paths。

- [ ] **Step 11: Commit stable promotion/docs only after all gates above pass**

```bash
git add engine/ziwei/capabilities.py README.md VERSION.md CHANGELOG.md docs/架構說明.md tests/test_ziwei_phase2a_capabilities.py
git add core/命理分析作業規範.md 2>/dev/null || true
git commit -m "docs: promote Ziwei Phase 2A capabilities"
```

If `core/命理分析作業規範.md` was unchanged, it must not appear in the commit。

---

### Task 11: Exact-head Review, Feature→Design PR, Post-merge Validation, and Main Integration

**Files:**
- No product code should be newly authored in this task。
- Temporary validation workflow may exist only on temporary validation branches and must not enter the product branch unless separately approved。

**Interfaces:**
- Consumes: exact final feature head and all evidence from Tasks 1–10。
- Produces: reviewed feature→design PR, squash merge, design post-merge PASS, design→main PR, main post-merge PASS。

- [ ] **Step 1: Freeze exact feature head and verify clean working tree**

```bash
git status --short
git rev-parse HEAD
```

Expected: clean tree and one exact feature SHA recorded in review notes。

- [ ] **Step 2: Re-run all final gates on exact feature head**

Required markers:

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

If any marker is absent or any command exits non-zero, do not open the integration PR as ready。

- [ ] **Step 3: Review the complete diff against approved design branch**

Reviewer must verify:

```text
no scoring
no default routing
no fine-cycle transformation runtime
no moving stars
no Calendar/Bazi semantic changes
no raw private chart
no last-write-wins conflict path
cycle sources never receive geometric self relation
```

Any blocking review finding returns to the responsible Task and repeats its RED→GREEN gate。

- [ ] **Step 4: Open formal feature→design PR**

PR body must include exact head SHA, changed-file count, internal test count, 40/40 public qualification, 80/80 private flying qualification, scope/privacy results, and known architectural boundaries。

Do not merge automatically。

- [ ] **Step 5: After explicit approval, squash merge feature→design using expected head SHA**

Use squash title:

```text
feat: implement Ziwei Transformation & Flying Core v1
```

If PR head changed after review, stop and rerun exact-head verification before merge。

- [ ] **Step 6: Run design post-merge validation from exact merged design commit**

Create a temporary validation branch from the exact design merge SHA, add only a validation workflow, run the full gate suite, capture artifacts, then close the validation PR without merge。

Expected: all gates PASS on merged design state。

- [ ] **Step 7: Compare design→main scope before opening final integration PR**

Require:

```text
behind_by = 0
merge-base = current main head used by this design cycle or reviewed divergence explicitly resolved
```

Review every changed file category again；no temporary validation workflow may appear in the formal design diff。

- [ ] **Step 8: Open design→main PR and wait for explicit approval**

PR body must state that Phase 2A adds stable/on-demand transformations and flying only；fine-cycle transformations/flying and flowing stars remain planned。

- [ ] **Step 9: Merge design→main only after approval, then run main post-merge validation**

Create a temporary validation branch from the exact merged `main` SHA and rerun the complete suite。Expected final marker:

```text
MAIN_POST_MERGE_PASS
```

Close the temporary validation PR without merge。

- [ ] **Step 10: Declare Phase 2A complete only after main post-merge evidence exists**

Completion statement must include:

```text
main merge SHA
full test count
40/40 public transformation qualification
80/80 private Astralium flying qualification
privacy/scope PASS
MAIN_POST_MERGE_PASS
```

Do not call Phase 2A complete before this step。

---

## Plan Self-Review Checklist

Before execution begins, verify this plan against the approved spec:

- [ ] Every spec production responsibility maps to Tasks 1–7。
- [ ] Every validation/promotion requirement maps to Tasks 8–11。
- [ ] No task implements monthly/daily/hourly stems, transformations, flying, or moving stars。
- [ ] `StarLocationIndex` / `PalaceStemIndex` validate records before mapping materialization。
- [ ] Cycle sources are excluded from geometric self-relation classification。
- [ ] Composition never provides final transformation state / score / resonance。
- [ ] Stable promotion occurs only after public + private qualification passes。
- [ ] Private raw data never appears in repo；only aggregate evidence is committed。
- [ ] Full Ziwei / Calendar / Bazi / repo regression and exact merged-main validation are explicit gates。
- [ ] No step permits silent expected-value rewrite after a failure。

## Execution Boundary

Implementation must not start from this plan until the user has reviewed and approved this written implementation plan. After approval, create an isolated feature worktree/branch from the exact `design/ziwei-transformation-flying-core` head and execute Task 1 first under TDD. Do not batch Tasks 1–11 into one commit or bypass RED evidence.