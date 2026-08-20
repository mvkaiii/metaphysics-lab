# Metaphysics Lab 引擎重構 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不改變現有八字與紫微流月計算結果的前提下，把兩套引擎拆成 `engine/bazi/` 與 `engine/ziwei/` 模組，並保留既有兩支 Python 作相容入口。

**Architecture:** 八字時間推導移到 `engine/bazi/calendar.py`；紫微共用索引與驗證移到 `engine/ziwei/common.py`，流月邏輯移到 `engine/ziwei/month.py`。原有 `engine/project_bazi_calendar.py` 與 `engine/project_ziwei_month.py` 改為薄相容層，繼續輸出相同 API 與 CLI 行為。本階段不建立流日、流時或 Cross-System Validation 的正式功能。

**Tech Stack:** Python 3.9+、標準函式庫 `unittest`、`zoneinfo`；不新增第三方執行期相依套件。

**Spec:** `docs/設計/Metaphysics-Lab-v1.2-架構設計.md`

## Global Constraints

- 八字既有 10 項測試結果必須維持一致。
- 紫微流月既有 10 項測試結果必須維持一致。
- `engine/project_bazi_calendar.py` 與 `engine/project_ziwei_month.py` 不刪除。
- 不改變 Project 推導盤面的欄位名稱、月份邊界、23:00 換日或流月閏月規則。
- 紫微流日、流時仍維持未啟用；本次不新增其算法。
- 不建立尚未有正式行為的 `cross_system.py`、`day.py`、`hour.py` 空殼，避免把設計目標誤認為已實作功能。
- 共用紫微索引、宮名與輸入驗證只放在 `engine/ziwei/common.py`，不在流月模組重複。

---

### Task 1: 建立新模組路徑的失敗測試

**Files:**
- Create: `tests/test_engine_module_layout.py`
- Test: `tests/test_project_bazi_calendar.py`
- Test: `tests/test_project_ziwei_month.py`

**Interfaces:**
- Consumes: 現有 `engine.project_bazi_calendar` 與 `engine.project_ziwei_month` 公開函式。
- Produces: 新模組預期介面 `engine.bazi.calendar.bazi_pillars`、`engine.bazi.calendar.project_derived`、`engine.ziwei.month.project_derived_ziwei_month`、`engine.ziwei.common.ZHI`、`engine.ziwei.common.PALACE_NAMES`。

- [ ] **Step 1: 新增新路徑等價測試**

```python
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from engine.project_bazi_calendar import bazi_pillars as legacy_bazi_pillars
from engine.project_ziwei_month import project_derived_ziwei_month as legacy_ziwei_month
from engine.bazi.calendar import bazi_pillars as modular_bazi_pillars
from engine.ziwei.common import ZHI, PALACE_NAMES
from engine.ziwei.month import project_derived_ziwei_month as modular_ziwei_month


class EngineModuleLayoutTests(unittest.TestCase):
    def test_bazi_modular_path_matches_legacy_path(self):
        dt = datetime(2026, 8, 20, 17, 12, tzinfo=ZoneInfo("Asia/Taipei"))
        self.assertEqual(modular_bazi_pillars(dt), legacy_bazi_pillars(dt))

    def test_ziwei_modular_path_matches_legacy_path(self):
        kwargs = dict(
            birth_lunar_month=5,
            birth_hour_branch="戌",
            flow_year_branch="酉",
            lunar_month=2,
            lunar_day=1,
            is_leap_month=False,
        )
        self.assertEqual(modular_ziwei_month(**kwargs), legacy_ziwei_month(**kwargs))

    def test_ziwei_common_owns_shared_constants(self):
        self.assertEqual(ZHI, tuple("子丑寅卯辰巳午未申酉戌亥"))
        self.assertEqual(PALACE_NAMES[0], "命宮")
        self.assertEqual(PALACE_NAMES[-1], "父母宮")
```

- [ ] **Step 2: 執行新測試並確認因模組不存在而失敗**

Run:

```bash
python -m unittest -v tests/test_engine_module_layout.py
```

Expected: FAIL/ERROR，原因為 `engine.bazi` 或 `engine.ziwei` 尚不存在，而不是測試語法錯誤。

- [ ] **Step 3: 執行既有 20 項測試確認重構前基準**

Run:

```bash
python -m unittest -v tests/test_project_bazi_calendar.py tests/test_project_ziwei_month.py
```

Expected: 20 tests，0 failures，0 errors。

- [ ] **Step 4: Commit**

```bash
git add tests/test_engine_module_layout.py
git commit -m "test: 新增引擎模組化路徑測試"
```

---

### Task 2: 重構 Bazi Engine 並保留相容入口

**Files:**
- Create: `engine/bazi/__init__.py`
- Create: `engine/bazi/calendar.py`
- Modify: `engine/project_bazi_calendar.py`
- Test: `tests/test_engine_module_layout.py`
- Test: `tests/test_project_bazi_calendar.py`

**Interfaces:**
- Consumes: 現有 `project_bazi_calendar.py` 的公開函式名稱與 CLI 參數。
- Produces: `engine.bazi.calendar` 提供 `BaziCalendarError`、`solar_term_time`、`flow_year_pillar`、`flow_month_pillar`、`day_pillar`、`time_pillar`、`bazi_pillars`、`ten_god`、`project_derived`、`main`；舊入口重新匯出相同名稱。

- [ ] **Step 1: 將現有八字正式實作完整搬到 `engine/bazi/calendar.py`**

實作要求：

```python
ENGINE_NAME = "Project Bazi Calendar Engine"
ENGINE_VERSION = "1.0.0"
REFERENCE_ENGINE = "6tail/lunar-python v1.4.8 (commit 000c8a3)"
DAY_ROLLOVER = "23:00"
SOLAR_TERM_BOUNDARY_CAUTION_MINUTES = 15
```

所有既有函式的演算法與輸出欄位保持原樣，只把檔頭品牌文字統一成 `Metaphysics Lab`。

- [ ] **Step 2: 建立 `engine/bazi/__init__.py` 公開 API**

```python
from .calendar import (
    BaziCalendarError,
    bazi_pillars,
    day_pillar,
    flow_month_pillar,
    flow_year_pillar,
    project_derived,
    solar_term_time,
    ten_god,
    time_pillar,
)

__all__ = [
    "BaziCalendarError",
    "bazi_pillars",
    "day_pillar",
    "flow_month_pillar",
    "flow_year_pillar",
    "project_derived",
    "solar_term_time",
    "ten_god",
    "time_pillar",
]
```

- [ ] **Step 3: 將舊檔改成薄相容入口**

`engine/project_bazi_calendar.py` 只負責：

```python
from engine.bazi.calendar import *
from engine.bazi.calendar import main

if __name__ == "__main__":
    main()
```

若直接以 `python engine/project_bazi_calendar.py ...` 執行時因 Python import path 無法找到頂層 `engine`，相容入口需加入只影響直接執行模式的專案根目錄 path bootstrap，不改變套件 import 行為。

- [ ] **Step 4: 執行 Bazi 新舊路徑測試**

Run:

```bash
python -m unittest -v tests/test_engine_module_layout.py tests/test_project_bazi_calendar.py
```

Expected: Bazi modular/legacy 等價測試與原 10 項 Bazi 測試皆 PASS；Ziwei 新模組測試此時仍可因尚未實作而失敗，需分開解讀。

- [ ] **Step 5: Commit**

```bash
git add engine/bazi engine/project_bazi_calendar.py tests/test_engine_module_layout.py
git commit -m "refactor: 拆分八字時間推導引擎"
```

---

### Task 3: 重構 Ziwei Month 並抽出共用基礎

**Files:**
- Create: `engine/ziwei/__init__.py`
- Create: `engine/ziwei/common.py`
- Create: `engine/ziwei/month.py`
- Modify: `engine/project_ziwei_month.py`
- Test: `tests/test_engine_module_layout.py`
- Test: `tests/test_project_ziwei_month.py`

**Interfaces:**
- Consumes: 現有紫微流月函式與 CLI 參數。
- Produces: `engine.ziwei.common` 提供 `ZHI`、`PALACE_NAMES`、`validate_month`、`validate_day`、`validate_branch`；`engine.ziwei.month` 提供 `effective_lunar_month`、`annual_doujun_branch`、`flow_month_ming_branch`、`flow_month_palaces`、`project_derived_ziwei_month`、`main`；舊入口重新匯出既有公開函式。

- [ ] **Step 1: 建立 `engine/ziwei/common.py`**

```python
ZHI = tuple("子丑寅卯辰巳午未申酉戌亥")
PALACE_NAMES = (
    "命宮", "兄弟宮", "夫妻宮", "子女宮", "財帛宮", "疾厄宮",
    "遷移宮", "交友宮", "官祿宮", "田宅宮", "福德宮", "父母宮",
)


def validate_month(month: int) -> None:
    if not 1 <= month <= 12:
        raise ValueError("農曆月必須介於 1 到 12")


def validate_day(day: int) -> None:
    if not 1 <= day <= 30:
        raise ValueError("農曆日必須介於 1 到 30")


def validate_branch(branch: str) -> None:
    if branch not in ZHI:
        raise ValueError("地支必須為：" + "、".join(ZHI))
```

- [ ] **Step 2: 將流月正式邏輯搬到 `engine/ziwei/month.py`**

`month.py` 從 `.common` 匯入 `ZHI`、`PALACE_NAMES` 與三個驗證函式；斗君、有效流月、流月命宮、十二宮重排、結構化輸出與 CLI 行為保持原樣。

固定輸出仍包含：

```python
"features": {
    "flow_month_enabled": True,
    "flow_day_enabled": False,
    "flow_hour_enabled": False,
    "monthly_four_transformations_enabled": False,
    "monthly_flowing_stars_enabled": False,
}
```

- [ ] **Step 3: 建立 `engine/ziwei/__init__.py` 公開 API**

```python
from .common import PALACE_NAMES, ZHI
from .month import (
    annual_doujun_branch,
    effective_lunar_month,
    flow_month_ming_branch,
    flow_month_palaces,
    project_derived_ziwei_month,
)

__all__ = [
    "PALACE_NAMES",
    "ZHI",
    "annual_doujun_branch",
    "effective_lunar_month",
    "flow_month_ming_branch",
    "flow_month_palaces",
    "project_derived_ziwei_month",
]
```

- [ ] **Step 4: 將舊紫微檔改成薄相容入口**

```python
from engine.ziwei.month import *
from engine.ziwei.month import main

if __name__ == "__main__":
    main()
```

同樣保留直接執行 `python engine/project_ziwei_month.py ...` 的相容性。

- [ ] **Step 5: 執行全部模組與既有測試**

Run:

```bash
python -m unittest -v tests/test_engine_module_layout.py tests/test_project_bazi_calendar.py tests/test_project_ziwei_month.py
```

Expected: 23 tests，0 failures，0 errors。

- [ ] **Step 6: Commit**

```bash
git add engine/ziwei engine/project_ziwei_month.py tests/test_engine_module_layout.py
git commit -m "refactor: 拆分紫微流月引擎"
```

---

### Task 4: 更新文件與相容性說明

**Files:**
- Modify: `README.md`
- Modify: `docs/架構說明.md`
- Modify: `docs/安裝到ChatGPT-Project.md`
- Modify: `docs/更新與版本同步.md`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: Task 2、3 的新目錄與舊相容入口。
- Produces: 使用者仍可照舊上傳 `project_bazi_calendar.py`、`project_ziwei_month.py`；開發者可使用新模組路徑。

- [ ] **Step 1: README 說明新目錄與相容入口**

文件需明確寫：

```text
engine/bazi/   八字正式模組
engine/ziwei/  紫微正式模組
```

並說明 `project_bazi_calendar.py` 與 `project_ziwei_month.py` 在 v1.2 重構期間保留作 compatibility wrapper，既有 ChatGPT Project 不需因這次內部重構立即更換檔名。

- [ ] **Step 2: 更新安裝與版本同步指南**

仍以兩支 compatibility wrapper 作一般 Project 最小安裝入口，避免一次要求使用者上傳整個 package；若未來 Skill 或完整 Python 環境使用新 package，再由 Skill／執行層引用 `engine.bazi` 與 `engine.ziwei`。

- [ ] **Step 3: CHANGELOG 新增未發布重構紀錄**

新增區段：

```markdown
## 未發布｜v1.2 引擎重構準備

- 八字正式實作拆入 `engine/bazi/`。
- 紫微流月正式實作拆入 `engine/ziwei/`。
- 舊 Python 路徑保留為相容入口。
- 本次只重構模組，不啟用紫微流日、流時或 Cross-System Validation。
```

- [ ] **Step 4: 執行完整回歸測試**

Run:

```bash
python -m unittest -v tests/test_engine_module_layout.py tests/test_project_bazi_calendar.py tests/test_project_ziwei_month.py
```

Expected: 23 tests，0 failures，0 errors。

- [ ] **Step 5: 檢查未誤啟用功能**

Run:

```bash
grep -R "flow_day_enabled.*True\|flow_hour_enabled.*True" engine tests
```

Expected: 無匹配結果。

- [ ] **Step 6: Commit**

```bash
git add README.md docs CHANGELOG.md
git commit -m "docs: 更新 v1.2 引擎模組化說明"
```

---

## 最終驗證

- [ ] `python -m unittest -v tests/test_engine_module_layout.py tests/test_project_bazi_calendar.py tests/test_project_ziwei_month.py` → 23/23 PASS。
- [ ] 新模組路徑與舊相容路徑對同一輸入輸出相同。
- [ ] 直接 CLI 舊入口仍可使用。
- [ ] `flow_day_enabled`、`flow_hour_enabled` 仍為 `False`。
- [ ] README、安裝指南與更新指南沒有要求現有使用者立即改檔名。
- [ ] `VERSION.md` 不升版；此分支仍屬 v1.2 未發布重構準備。