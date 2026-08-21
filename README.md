# Metaphysics Lab

Metaphysics Lab 是一套以「可重現、可驗證、可追溯、以決策為導向」為核心的命理分析框架。

目前正式版本：**v1.2.0｜2026-08-21**。

它把命理分析拆成可管理的資料層、固定算法、盲判／校準流程與驗證機制，避免把原始盤面、Project 推導、命理推論與已知事件混在一起。

## 第一次使用

- [快速開始](docs/快速開始.md)
- [安裝到 ChatGPT Project](docs/安裝到ChatGPT-Project.md)
- [命盤資料準備指南](docs/命盤資料準備指南.md)
- [Astralium 資料取得指南](docs/Astralium資料取得指南.md)
- [更新與版本同步](docs/更新與版本同步.md)
- [資料治理](docs/資料治理.md)
- [架構說明](docs/架構說明.md)
- [版本狀態](VERSION.md)
- [變更紀錄](CHANGELOG.md)

---

## 核心原則

- 命盤提供模型。
- Project 推導提供時間層級。
- 事件提供證據。
- 現實背景決定策略。
- 問事先盲判，再校準。
- 原始盤面、已校驗資料、Project 推導盤面、已驗證事件、命理推論、研究假說、當次現實背景必須分開。
- 系統核心與私人個案資料必須分開保存。
- 能力存在、成熟度與是否預設執行必須分開管理。
- 沒有固定算法或 qualification 的細運能力，不得假裝已實作。

## v1.2.0 能力矩陣

| Capability | Implementation | Maturity | Routing / Role |
|---|---|---|---|
| 八字時間推導（流年／流月／流日／流時） | implemented | stable | default |
| 紫微流月定位 | implemented | stable | default |
| 紫微流日定位 | implemented | experimental | on_demand |
| 紫微流時定位 | implemented | experimental | on_demand |
| Calendar Resolver v1 | implemented | stable infrastructure | upstream |
| Ziwei Calendar Adapter | implemented | stable infrastructure | adapter |
| Ziwei Transformation Core v1 | implemented | stable | on_demand |
| Ziwei Flying Core v1 | implemented | stable | on_demand |
| 紫微流月／流日／流時四化與飛化 | planned | — | on_demand |
| 紫微流曜（moving stars） | planned | — | on_demand |
| Cross-System Validation | planned | — | — |
| 奇門自動排盤引擎 | planned | — | — |

`on_demand` 代表能力可執行，但一般問事不預設跑；只有問題需要更高時間解析度或明確指定該能力時才調用。

`experimental` 代表已有可執行程式與測試，但分析時必須降權，不得單獨支撐高度確信。

---

## v1.2.0 已正式完成

### 八字

正式模組：

```text
engine/bazi/calendar.py
```

相容入口：

```text
engine/project_bazi_calendar.py
```

可建立流年、流月、流日、流時、天干十神等 Project 推導盤面。八字流月採節氣月；23:00 early-Zi 換日仍由八字引擎自己負責。

### Calendar Resolver v1

正式模組：

```text
engine/calendar/
```

責任：

- structured local civil datetime + IANA timezone 正規化
- DST ambiguous / nonexistent local time contract
- Gregorian civil date
- Gregorian → Lunar
- hour branch
- provenance / validation metadata
- 產出 `CalendarContext`

固定 runtime：

```text
lunar-python==1.4.8
tzdata==2026.3
IANA 2026c
```

Calendar Resolver civil date 只在 `00:00` 換日。23:00 已屬子時，但 Resolver 不套用任何命理換日規則。

### 紫微流月／流日／流時定位

```text
engine/ziwei/month.py   # stable / default
engine/ziwei/day.py     # experimental / on_demand
engine/ziwei/hour.py    # experimental / on_demand
```

目前這三層只處理宮位定位。紫微流月採農曆月，初一換月；閏月採初一至十五歸原月、十六起歸下一月。

### Ziwei Transformation & Flying Core v1

正式模組：

```text
engine/ziwei/errors.py
engine/ziwei/models.py
engine/ziwei/basis.py
engine/ziwei/transformation_profiles.py
engine/ziwei/transformations.py
engine/ziwei/flying.py
engine/ziwei/composition.py
```

Transformation Core：

- 固定版本化十天干四化 profile `metaphysics-lab-common-v1`
- 純粹處理 `heavenly_stem → 祿／權／科／忌`
- 不自行判斷生年、大限、流年、流月、流日、流時

Flying Core：

- 只使用已校驗本命星曜位置
- 本命十二宮宮干建立 48-edge flying graph
- 支援生年、大限、流年四化落宮
- 底層只保存 `same_palace / opposite_palace_incoming / normal`
- `↑/↓` 只屬 Astralium-compatible presentation mapping

Composition：

- 生年、大限、流年保留各自 layer
- 不互相覆寫
- 同一 layer identity 或 component 不一致時 fail closed
- 不提供祿權科忌分數、共振分數、最終 transformation state 或自動吉凶解讀

---

## Phase 2A qualification

v1.2.0 的 Ziwei Transformation & Flying Core 已通過：

```text
pinned iztro 十干四化             40/40 PASS
私有 Astralium 十干四化           40/40 PASS
Astralium 本命飛化                48/48 PASS
Astralium 大限飛化                 4/4 PASS
Astralium 2023–2029 流年飛化      28/28 PASS
Astralium flying total             80/80 PASS
Astralium-compatible presentation  11/11 PASS
```

repo 只保存 aggregate qualification evidence 與 digest，不保存私人 raw chart、出生資料、完整十二宮 fixture 或 normalized private input。

v1.2.0 release baseline 的 post-main regression：

```text
Phase 2A internal  43/43 PASS
Ziwei              83/83 PASS
Calendar           35/35 PASS
Bazi               10/10 PASS
Full repository   132/132 PASS
```

---

## 目前仍未實作

- 紫微 Fine Cycle Stem Resolver（流月／流日／流時天干）
- 紫微 23:00 命理日界 school policy
- 流月／流日／流時四化與飛化
- 紫微流曜（moving stars）
- Cross-System Validation 正式引擎
- 完整干支互動引擎
- 奇門自動排盤引擎

上述能力必須依序走「規則固定 → Python 實作 → 自動測試 → 外部 qualification → capability promotion」，不得因 Phase 2A 已完成就推定細運能力也已完成。

---

## Capability 三軸模型

```text
implementation = planned / implemented
maturity       = experimental / stable
routing        = default / on_demand
```

「預設不跑」不等於「能力不存在」。

---

## Python 模組

```text
engine/
├── bazi/
├── calendar/
├── ziwei/
├── project_bazi_calendar.py
├── project_ziwei_month.py
├── project_ziwei_day.py
└── project_ziwei_hour.py
```

`project_*.py` 是 compatibility wrapper，不是完全獨立的單檔引擎。實際執行時，必須同時具備同版 package modules 與 runtime dependencies。

完整 Python 環境可直接使用：

```text
engine.bazi.calendar
engine.calendar.resolver
engine.ziwei.month
engine.ziwei.day
engine.ziwei.hour
engine.ziwei.capabilities
engine.ziwei.transformations
engine.ziwei.flying
engine.ziwei.composition
```

---

## 最短建置流程

1. 準備出生年月日、時間、地點、性別與原始命盤資料。
2. 把 `core/核心提示詞.md` 同步到 ChatGPT Project Instructions。
3. 加入正式規則與需要的 Python modules。
4. 建立私人 `命盤資料校驗紀錄.md` 與 `命盤核心摘要.md`。
5. 先完成命盤校驗，再開始本命／流年／問事。
6. 未來問事採「第一階段盲判 → 第二階段事件校準」。

完整同步清單請看 [安裝到 ChatGPT Project](docs/安裝到ChatGPT-Project.md)。

---

## 資料治理

本 repo 只保存可共用的系統核心，不應提交真實命主的：

- 出生資料
- 原始命盤
- 醫療／家庭／工作／資產／感情資料
- 驗證事件
- 問事紀錄
- 其他可識別私人資訊

私人 Case 應保存在自己的 ChatGPT Project、私人知識庫或其他受控環境。

---

## 版本治理

- `VERSION.md`：目前正式版本與 capability 狀態。
- `CHANGELOG.md`：每個 release 的變更歷程與 qualification。
- `docs/更新與版本同步.md`：從舊版升級時應替換哪些檔案。
- Git tag / GitHub Release：正式 release merge 且 main 驗證完成後建立，不提前指向尚未完成的文件整理 commit。

任何會改變命盤計算結果、時間邊界、rule profile、資料 contract 或 capability maturity 的變更，都必須留下版本歷程並重新跑對應 gate。
