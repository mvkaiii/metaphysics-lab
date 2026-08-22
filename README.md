# Metaphysics Lab

Metaphysics Lab 是一套以「可重現、可驗證、可追溯、以決策為導向」為核心的命理分析框架。

目前正式版本：**v1.2.0｜2026-08-21**。

目前工作樹另包含 **Unreleased Phase 2B**、**Unreleased Phase 2C0｜Natal Chart Foundation** 與 **Unreleased Phase 2C Ziwei Flowing Stars**；這些 Unreleased 能力不改寫 `VERSION.md` 的正式 release identity。

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
- Project 原生盤面提供可重現的本命基礎。
- Project 推導盤面提供時間層級。
- 事件提供證據。
- 現實背景決定策略。
- 問事先盲判，再校準。
- `Precision must be earned by input`：輸入不足只能追問、保留候選或降級；不得自行補值。
- 八種資料類型必須分開：原始盤面事實、已校驗資料、Project 原生盤面、Project 推導盤面、已驗證事件、命理推論、研究假說、當次現實背景。
- 系統核心與私人個案資料必須分開保存。
- capability implementation / maturity / routing 必須分開管理。

---

## Unreleased Phase 2C Ziwei Flowing Stars

Phase 2C Ziwei Flowing Stars capability：

```text
ziwei.flowing_stars = implemented / experimental / on_demand / 1.0-exp
profile = ziwei-flowing-stars-common-v1
classification = Project 推導盤面
```

支援 `decadal / yearly / monthly / daily / hourly` 五種 scope。核心流曜固定10顆：天魁、天鉞、文昌、文曲、祿存、擎羊、陀羅、天馬、紅鸞、天喜；`yearly` 額外加入年解。

月／日／時重用 Phase 2B resolved source；大限直接重用既有 `ZiweiDecadalPeriod.stem_branch`；流年使用 lunar-year neutral source。不得重算上游干支或套另一套 boundary policy。

Public qualification：pinned iztro 2.6.0 revision `814b77e6371e1050cac31bbf674db3c3138fcfde`，600/600 source cases、6120 placements、0 unexpected mismatch。Astralium flowing-stars private qualification = **PENDING**。

本階段不包含歲前十二神、將前十二神、博士十二神、長生十二神、小限流曜、流曜亮度、scoring 或 AI interpretation，也不升 Stable。

---

## Unreleased Phase 2C0｜Natal Chart Foundation

Phase 2C0 讓使用者可以直接用出生基本資料建立 Project 原生本命盤，也可匯入已知四柱或 Astralium structured chart 做 external cross-check。

完整 Mode A 最低輸入：性別、Gregorian 出生日期、出生時間、出生地。

例如：

> 男，1984年3月13日19:20，台北市出生

若缺欄位，只追問缺少內容；若時間是「大概晚上7、8點」，不得自行取中點，應保留候選或降級。

### Phase 2C0 capability matrix（歷史快照）

| Capability | Implementation | Maturity | Routing |
|---|---|---|---|
| `birth.input_resolution` | implemented | experimental | on_demand |
| `birth.location_resolution` | implemented | experimental | on_demand |
| `birth.true_solar_time` | implemented | experimental | on_demand |
| `bazi.natal_chart` | implemented | **Experimental** | on_demand |
| `ziwei.natal_chart` | implemented | **Experimental** | on_demand |
| `natal.reconciliation` | implemented | stable | on_demand |
| `natal.markdown_export` | implemented | stable | on_demand |
| `ziwei.flowing_stars` | planned | — | on_demand |

Bazi / Ziwei Natal 目前可以執行但仍為 Experimental，沒有獨立 promotion 決策前不得升 Stable。

### External / Project / Resolved

本命資料固定保留：

```text
External / Project / Resolved
MATCH / EQUIVALENT / CONFLICT / NOT_COMPARABLE
```

External / Project raw views 不互相覆寫。Experimental Project 與 Astralium 等 external source 發生實質衝突時，Resolved 預設採 external，但 CONFLICT 狀態仍保留。

Astralium 為可選 external qualification source，不是 runtime dependency。

### Time basis

Phase 2C0 保留 `reported_civil_time`、`normalized_civil_time`、`bazi_effective_time`、`ziwei_effective_time`。Calendar Resolver 不負責真太陽時；八字與紫微使用獨立 time profile。

---

## v1.2.0 正式能力基線

| Capability | Implementation | Maturity | Routing / Role |
|---|---|---|---|
| 八字時間推導（流年／流月／流日／流時） | implemented | stable | default |
| 紫微流月定位 | implemented | stable | default |
| 紫微流日定位 | implemented | experimental | on_demand |
| 紫微流時定位 | implemented | experimental | on_demand |
| Calendar Resolver v1 | implemented | stable infrastructure | neutral |
| Ziwei Transformation Core | implemented | stable | on_demand |
| Ziwei Flying Core | implemented | stable | on_demand |

Calendar Resolver 接受 structured local civil datetime + IANA timezone；civil date 在 00:00 換日，23:00 已屬子時，但 Resolver 不套八字或紫微命理日界。

---

## Unreleased Phase 2B｜Ziwei Fine Cycle

Fine Cycle 固定 profile：

```text
ziwei-fine-cycle-lunar-late-zi-v1
late_zi_forward-v1
```

flow month/day/hour stem、transformations、flying 為：

```text
implemented / experimental / on_demand
```

Calendar Resolver 維持 **neutral**；23:00 紫微 effective-day 前進只由 fine-cycle profile 套用。

Qualification：

```text
pinned lunar-lite 1d104fff...   18/18 PASS
pinned iztro 814b77e6...        integration PASS
Astralium fine-cycle             PENDING
```

`leap_twelfth_month_second_half` 只有 synthetic internal coverage，為 **not externally qualified**。

在 Phase 2B／Phase 2C0 歷史快照中，`ziwei.flowing_stars` 仍為 planned / on_demand；目前狀態請以 Phase 2C 區段為準。

---

## 資料分類

### 原始盤面事實

第三方／原始來源直接提供的資料，例如 Astralium、原始 PDF 或 imported structured chart。

### 已校驗資料

經來源比對與規則確認後的穩定資料。

### Project 原生盤面

由出生資料經 Metaphysics Lab deterministic Natal Engine 建立的本命八字／紫微。

### Project 推導盤面

由本命／運限／目標時間經固定算法建立的流年、流月、流日、流時、四化／飛化等衍生資料。

### 命理推論

對盤面的解讀，不是盤面事實。

---

## Privacy / Qualification

共用 repo 不提交真實命主 raw birth input、full address、raw Astralium chart、PDF 或私人事件資料。

Qualification 只保存 public/synthetic cases、opaque case ids、aggregate counts、digests、versions 與 status。Infrastructure outage 必須與 algorithm failure 分開報告。

---

## 專案方向

Metaphysics Lab 的目標不是讓 AI 自由「算命」，而是把命盤建立、時間算法、來源、maturity、qualification、事件校準與策略輸出拆成可重現的工程流程。
