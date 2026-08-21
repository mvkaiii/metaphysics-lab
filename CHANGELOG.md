# 變更紀錄

## Unreleased｜Phase 2B

### Ziwei Fine Cycle Stem Resolver v1

- 新增 `engine/calendar/sexagenary.py` 中立干支數學 helper，不 import 八字 policy。
- 新增 `engine/ziwei/fine_cycle_stems.py`，固定 profile `ziwei-fine-cycle-lunar-late-zi-v1` / `1.0-exp`。
- 紫微流月 stem 採農曆月與閏月 15/16 分界；23:xx 不提前切換流月。
- 紫微流日固定 `late_zi_forward-v1`：22:59 舊日、23:00 effective date +1、00:00 不 double-rollover。
- 紫微流時使用 effective Ziwei day stem 起五鼠遁，hour branch 直接採 CalendarContext。
- 新增 `engine/ziwei/fine_cycle.py`，把 resolved stem 接入既有 Transformation / Flying Core。
- Composition 支援 monthly / daily / hourly layer，保留 duplicate/conflict fail-closed semantics。
- 細運 stem／四化／飛化 capability 升為 `implemented / experimental / on_demand / 1.0-exp`；Stable Core 與既有 palace maturity 不變；流曜仍 planned。

### Phase 2B qualification

```text
pinned lunar-lite 1d104fff...   18/18 PASS
pinned iztro 814b77e6...        integration PASS
Astralium fine-cycle             PENDING
```

- `leap_twelfth_month_second_half` 目前只具 synthetic internal coverage，標記為 not externally qualified。
- Astralium PENDING 原因：目前沒有完整 fine-cycle stem/transformation/flying private source payload。
- repo 不提交 Astralium raw private chart；只保存 aggregate PENDING state。
- 本段為 Unreleased 開發紀錄；`VERSION.md` 與 v1.2.0 release identity 不變。

## v1.2.0｜2026-08-21

v1.2.0 把先前分散在開發線的模組化、Calendar infrastructure、紫微細時間定位 capability 與 Ziwei Transformation & Flying Core v1 正式收斂成同一個 release baseline。

### 引擎模組化

- 八字正式實作拆入 `engine/bazi/`。
- 紫微正式實作拆入 `engine/ziwei/`。
- Calendar Resolver 建立於 `engine/calendar/`。
- `engine/project_bazi_calendar.py`、`engine/project_ziwei_month.py`、`engine/project_ziwei_day.py`、`engine/project_ziwei_hour.py` 保留 compatibility wrapper。
- wrapper 不是獨立單檔引擎；實際執行仍需同版 package modules。

### Capability 三軸模型

紫微 capability 改採：

```text
implementation = planned / implemented
maturity       = experimental / stable
routing        = default / on_demand
```

正式狀態：

```text
紫微流月定位 = implemented / stable / default
紫微流日定位 = implemented / experimental / on_demand
紫微流時定位 = implemented / experimental / on_demand
Ziwei Transformation Core = implemented / stable / on_demand
Ziwei Flying Core = implemented / stable / on_demand
流月／流日／流時四化與飛化 = planned / on_demand
紫微流曜 = planned / on_demand
```

### 紫微流日與流時定位

- 新增 `engine/ziwei/day.py`：流月命宮起初一、順行一日一宮。
- 新增 `engine/ziwei/hour.py`：流日命宮起子時、每時辰順行一宮。
- 流日／流時第一版維持 Experimental / On-demand。
- 流日／流時只處理宮位定位，不自動啟用細運四化、飛化或流曜。

### Calendar Resolver v1

- 新增 `engine/calendar/precision.py`、`models.py`、`timezone.py`、`lunar.py`、`resolver.py`。
- structured civil datetime + IANA timezone → `CalendarContext`。
- Runtime lunar provider 固定 `lunar-python==1.4.8`。
- Timezone provider 固定 `tzdata==2026.3` / IANA `2026c`。
- HKO Gregorian→Lunar exhaustive validated range：`1901-01-01..2100-12-31`。
- `2057-09-28..2057-10-27` 固定 `boundary_conflict`。
- `2089-09-04`、`2097-08-07` 固定 `boundary_caution`。
- civil date 只在 00:00 換日；23:00 已屬子時，但 Resolver 不套用命理日界。
- 八字 early-Zi 仍由八字引擎負責；紫微 23:00 school policy 尚未固定。
- 新增 `engine/ziwei/calendar_adapter.py` 作為第一個正式 adapter。

### Ziwei Transformation & Flying Core v1（Phase 2A）

- 新增 `engine/ziwei/transformation_profiles.py` 與 `engine/ziwei/transformations.py`。
- 第一版 rule profile：`metaphysics-lab-common-v1`。
- 十天干四化核心只處理 `heavenly_stem → 祿／權／科／忌`，不自行判斷時間 scope。
- 新增 `engine/ziwei/errors.py`、`models.py`、`basis.py`，建立 immutable models 與 duplicate-safe natal basis builders。
- 新增 `engine/ziwei/flying.py`，只用已校驗 natal star location 建立飛化落宮。
- 本命十二宮宮干形成 48-edge `NatalFlyingGraph`。
- 底層 geometry 固定 `same_palace / opposite_palace_incoming / normal`。
- `↑/↓` 只作 Astralium-compatible presentation mapping。
- 新增 `engine/ziwei/composition.py`，保留 birth-year / decadal / yearly layers，不互相覆寫。
- 同一 layer identity、source、stem、profile 或 edge 不一致時 fail closed。
- 不提供四化 scoring、resonance、final transformation state 或自動吉凶解讀。

### Phase 2A qualification

```text
pinned iztro 十干四化             40/40 PASS
私有 Astralium 十干四化           40/40 PASS
Astralium 本命飛化                48/48 PASS
Astralium 大限飛化                 4/4 PASS
Astralium 2023–2029 流年飛化      28/28 PASS
Astralium flying total             80/80 PASS
Astralium-compatible presentation  11/11 PASS
```

repo 只保存 aggregate qualification summary 與 digest，不保存私人 raw chart、出生資料或 normalized private input。

### v1.2.0 release regression baseline

main post-merge verified：

```text
Phase 2A internal  43/43 PASS
Ziwei              83/83 PASS
Calendar           35/35 PASS
Bazi               10/10 PASS
Full repository   132/132 PASS
```

### 文件與版本治理

- `README.md` 改成目前正式能力矩陣，移除舊開發線標示與重複 capability 描述。
- `VERSION.md` 正式發布 v1.2.0，區分目前狀態與歷史版本。
- `CHANGELOG.md` 成為 release 歷程主檔。
- `docs/更新與版本同步.md` 負責 migration / Project 檔案替換清單。
- `docs/快速開始.md`、`docs/安裝到ChatGPT-Project.md`、`docs/架構說明.md` 同步目前正式能力。

### 仍未實作

- Ziwei Fine Cycle Stem Resolver（流月／流日／流時天干）
- 紫微 23:00 命理日界 school policy
- 流月／流日／流時四化與飛化
- 紫微流曜（moving stars）
- Cross-System Validation 正式引擎
- 完整干支互動引擎
- 奇門自動排盤引擎

上述能力不得因 Phase 2A 已完成就推定可用。

---

## v1.1.0｜2026-08-20

### 新增

- 啟用紫微流月定位層。
- 新增流年斗君、流月命宮與流月十二宮重排。
- 新增 `engine/project_ziwei_month.py`。
- 新增紫微流月自動測試與人工測試紀錄。
- 新增 `core/紫微流月推導規則.md`。

### 文件與安裝流程

- 新增 `docs/安裝到ChatGPT-Project.md`。
- 新增 `docs/命盤資料準備指南.md`。
- 新增 `docs/Astralium資料取得指南.md`。
- 新增 `docs/更新與版本同步.md`。
- 重寫 README 與快速開始。

### 固定邊界

- 紫微流月採農曆月，農曆初一換月。
- 閏月採初一至十五歸原月、十六起歸下一月。
- 八字流月採節氣月；兩者不同步不是 bug。
- 紫微流月引擎當時不負責國曆轉農曆。

---

## v1.0.0｜2026-08-20

### 新增

- 建立 Metaphysics Lab 共用核心架構。
- 建立命理分析作業規範。
- 建立問事「先盲判、後事件校準」雙階段制度。
- 建立七種資料類型分層。
- 建立八字流年、流月、流日、流時固定算法。
- 建立八字 23:00 early-Zi、五虎遁、五鼠遁、天干十神與節氣交界規則。
- 建立測試與問事追蹤制度。
