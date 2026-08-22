# Ziwei Flowing Stars v1｜Phase 2C 設計規格

- 日期：2026-08-22
- Branch：`design/ziwei-flowing-stars`
- 狀態：Design spec，等待使用者 final review；尚未進入 implementation plan
- 分類：Architectural
- 階段：Phase 2C
- Base：`main` commit `bb08ded1d8ed9b026bcd3d8719f00515da6054c3`
- 前置依賴：Phase 2A Transformation/Flying Core、Phase 2B Fine Cycle Stem Resolver、Phase 2C0 Natal Chart Foundation 均已在 `main`
- Public qualification oracle：`SylarLong/iztro` package v2.6.0 / pinned revision `814b77e6371e1050cac31bbf674db3c3138fcfde`

---

## 一、目的

Phase 2C 的目的，是完成 Metaphysics Lab 紫微動態時間層目前最後一塊尚未實作的正式 capability：

```text
ziwei.flowing_stars
```

它處理的是「運限／流年／流月／流日／流時的動態星曜位置」，不是重新排本命、不是四化、不是飛化，也不是歲前／將前十二神。

Phase 2C v1 的資料流固定為：

```text
Validated cycle source
        ↓
Flowing Star Source Adapter
        ↓
Pure Flowing Star Placement Core
        ↓
FlowingStarLayer
        ↓
Optional Materialized View
```

核心原則：

> 流曜核心只接受已解析的 scope + heavenly stem + earthly branch，不自行查日期、不自行推大限、不自行套 Calendar policy。
>
> 星曜位置的 canonical truth 是十二地支位置，不先綁定本命宮名或運限宮名。
>
> 四化／飛化與流曜重用相同 layer identity 型別與 chart/scope/reference 語意，但各自保有自己的 rule profile；資料模型彼此獨立，不修改 Stable Phase 2A core 的責任。
>
> Phase 2B 已解析的流月／流日／流時干支直接重用，不再重算。
>
> pinned iztro 只作 qualification oracle，不成為 Python runtime dependency，也不成為 Project output 的 source classification。
>
> v1 先 `implemented / experimental / on_demand / 1.0-exp`，不得因單一 private case或 public oracle PASS 自動升 Stable。

---

## 二、現況與 Phase 2C 前置 Gate

目前 `main` 已有：

- `ziwei.transformations` = implemented / stable / on_demand。
- `ziwei.flying` = implemented / stable / on_demand。
- `ziwei.flow_month_stem` = implemented / experimental / on_demand。
- `ziwei.flow_day_stem` = implemented / experimental / on_demand。
- `ziwei.flow_hour_stem` = implemented / experimental / on_demand。
- `ziwei.natal_chart` = implemented / experimental / on_demand。
- `ziwei.flowing_stars` = planned / on_demand。

目前 `engine/ziwei/capabilities.py` 中 `ziwei.flowing_stars` 只有 placeholder，`module = engine.ziwei.stars` 且尚無正式 dependency contract。

Phase 2C implementation 的 Task 0 必須先做 rule/capability reconciliation：

1. 確認 `main` 仍以 `bb08ded1...` 或其合法後繼為 base。
2. 確認 Phase 2A / 2B / 2C0 capability state 沒有被降級或漂移。
3. 將 `ziwei.flowing_stars` 的正式 module 指向 Phase 2C 實作模組。
4. 不把 `ziwei.flowing_stars` 的實作誤寫成 Phase 2B 或 Phase 2C0 已完成事項。
5. `VERSION.md`、tag、GitHub Release 不因 Unreleased Phase 2C 自動變更。

最低 Gate：

```text
PHASE2C_RULE_SOURCE_RECONCILIATION_PASS
```

若 capability registry、規則文件與實際 main 狀態矛盾，停止，不進 production implementation。

---

## 三、正式設計決策

### 3.1 採 Pure Core + Scope Adapter + Independent Layer

Phase 2C 不採「輸入日期後由 `stars.py` 一次把所有東西重算」的 monolithic 模式。

正式拆分：

```text
engine/ziwei/flowing_star_models.py
    immutable models / validation

engine/ziwei/flowing_star_sources.py
    decadal/yearly/monthly/daily/hourly source adapters

engine/ziwei/flowing_stars.py
    pure placement core + layer builder

engine/ziwei/flowing_star_view.py
    optional branch → palace materialization / query view
```

若 implementation plan 經 repo 現況檢查後發現其中兩個檔案可以安全合併，可縮減檔案數；但責任邊界不得合併。

### 3.2 不修改 Stable `CycleTransformationLayer` 語意

`CycleTransformationLayer` 繼續只代表：

- scope/source stem
- 四化 set
- 四條 flying edges

Phase 2C 新增獨立：

```text
FlowingStarLayer
```

FlowingStarLayer **重用既有 `LayerIdentity` 型別**，但不與四化 layer 共用同一個 identity object，也不以完整 dataclass equality 作 join，因為兩個 capability 的 `rule_profile` 不同。

兩層必須對齊的 cycle join key 固定為：

```text
chart_id
scope
reference
```

各自 identity 的 `rule_profile` 則分別屬於 transformation profile 與 flowing-star profile。

因此：

```text
CycleTransformationLayer.identity.rule_profile != FlowingStarLayer.identity.rule_profile
```

可以是正常狀態，只要 `chart_id + scope + reference` 一致。

FlowingStarLayer 不塞進 `CycleTransformationLayer` 欄位，也不要求 Phase 2A Stable model 改成「四化 + 流曜大雜燴」。

### 3.3 canonical location 一律使用地支

Pure core 的正式輸出：

```text
target_branch
```

而不是先輸出：

```text
夫妻宮 / 官祿宮 / 財帛宮
```

原因：同一個物理地支位置，可以同時對應：

- 本命十二宮名稱。
- 大限十二宮名稱。
- 流年十二宮名稱。
- 流月／日／時十二宮名稱。

這些是 materialized view，不是星曜位置本身。

### 3.4 Public oracle 不成為 runtime dependency

pinned public oracle：

```text
SylarLong/iztro
package = 2.6.0
revision = 814b77e6371e1050cac31bbf674db3c3138fcfde
```

qualification target 取自：

- `src/star/horoscopeStar.ts`
- `src/star/location.ts`
- `src/astro/FunctionalAstrolabe.ts`
- pinned upstream tests

正式 Python runtime：

- 不 import Node/npm。
- 不 shell out 呼叫 iztro。
- 不從網路即時取得 oracle 結果。
- public vectors / pinned oracle runner 只在 qualification workflow 使用。
- Project rule profile 採中性名稱，不以第三方名稱冒充資料來源。

---

## 四、Phase 2C v1 Scope

### 4.1 v1 必須實作的流曜

核心十顆：

```text
天魁
天鉞
文昌
文曲
祿存
擎羊
陀羅
天馬
紅鸞
天喜
```

流年 scope 額外：

```text
年解
```

因此固定 star count：

```text
decadal = 10
yearly  = 11
monthly = 10
daily   = 10
hourly  = 10
```

### 4.2 v1 支援的 scopes

```text
decadal
yearly
monthly
daily
hourly
```

`origin` 不屬於 `ziwei.flowing_stars`；本命星曜已由 Natal Builder 負責。

### 4.3 v1 明確不實作

- 歲前十二神。
- 將前十二神。
- 博士十二神。
- 長生十二神。
- 小限流曜／小限星群。
- 大量雜曜。
- 流曜亮度。
- 流曜吉凶分數。
- 流曜格局自動命名。
- 新的四化算法。
- 新的飛化算法。
- 新的本命安星算法。
- 自動遍歷全年、每日、每時。
- AI 命理解讀。
- 奇門遁甲。
- 將 iztro 或 Astralium 宣稱為唯一紫微標準。
- 因 Phase 2C 完成而自動 promotion Phase 2B fine-cycle 或 Phase 2C0 Natal maturity。

特別說明：pinned iztro 的 `yearlyDecStar` / `getYearly12()` 是另一組動態年星資料，不屬於 `getHoroscopeStar()`；Phase 2C v1 不合併進 `ziwei.flowing_stars`。

---

## 五、資料模型

### 5.1 FlowingStarProfile

第一版固定：

```text
profile_id = ziwei-flowing-stars-common-v1
rule_version = 1.0-exp
canonical_location = earthly_branch
qualification_target = iztro-2.6.0-814b77e6
```

`qualification_target` 只說明 public oracle；Project 輸出分類仍為 `Project 推導盤面`，source_name 仍為 Metaphysics Lab，不得冒充 iztro direct output。

### 5.2 FlowingStarSource

預期 immutable model：

```text
FlowingStarSource
├─ chart_identity
├─ scope                    # decadal | yearly | monthly | daily | hourly
├─ reference                # stable source/layer reference
├─ heavenly_stem
├─ earthly_branch
├─ source_profile
├─ rule_version
├─ validation_status
└─ provenance
```

此 model 是 Phase 2C layer builder 唯一接受的「時間來源」。

FlowingStarSource 必須驗證：

1. stem 是十天干。
2. branch 是十二地支。
3. stem + branch 是合法六十甲子配對，而不是只有兩個字各自合法。
4. scope 合法。
5. reference 非空且與 adapter 來源一致。
6. chart_identity 明確，不從 global state 猜命盤。

Pure placement helper 可以為了 table/oracle exhaustive test 接受「各自合法的 stem + branch」；但正式 FlowingStarLayer 一律只能從 validated `FlowingStarSource` 建立。

Pure core 不接受散落的：

```text
2026-08-22
農曆七月
庚
辰
大概下午
```

作為彼此無關的參數。

### 5.3 FlowingStarPlacement

```text
FlowingStarPlacement
├─ base_star                # 天魁 / 文昌 / ...
├─ category                 # soft / lucun / tough / tianma / flower / helper
├─ scope
├─ target_branch
├─ sequence                 # deterministic output order
└─ provenance
```

`base_star` 是 canonical identity。`流魁 / 月魁 / 日魁 / 時魁 / 運魁` 等顯示名稱屬 presentation/view，不作核心 identity。

### 5.4 FlowingStarLayer

```text
FlowingStarLayer
├─ identity: LayerIdentity
├─ source: FlowingStarSource
├─ placements: tuple[FlowingStarPlacement, ...]
├─ profile_id
├─ rule_version
├─ classification = Project 推導盤面
├─ maturity = experimental
├─ validation
└─ provenance
```

固定 invariants：

1. `identity.chart_id == source.chart_identity.chart_id`。
2. `identity.scope == source.scope`。
3. `identity.reference == source.reference`。
4. `identity.rule_profile == layer.profile_id`。
5. 每個 `base_star` 在同一 layer 只能出現一次。
6. 非 yearly 必須正好 10 顆；yearly 必須正好 11 顆。
7. 每個 `target_branch` 必須是十二地支之一。
8. 不允許 unknown category。
9. source validation 若屬 blocking 狀態，不得 materialize 成 available layer。

### 5.5 FlowingStarMaterializedRecord

optional view 可產生：

```text
FlowingStarMaterializedRecord
├─ base_star
├─ display_name
├─ target_branch
├─ natal_palace             # optional
├─ scope_palace             # optional
├─ scope
└─ source_reference
```

Pure core 不依賴此 view 才能成立。

---

## 六、Pure Placement Core 規則

### 6.1 十二地支 canonical order

所有 branch calculation 使用 Project 已有 canonical `ZHI`：

```text
子 丑 寅 卯 辰 巳 午 未 申 酉 戌 亥
```

若需要對照 iztro array index，qualification adapter 必須明確轉換「iztro palace index（寅起）」到 canonical branch；不得把 array index 本身存成 Project truth。

### 6.2 天魁／天鉞

直接重用 2C0 已存在且 qualification 過的 deterministic rule；不得複製第二份 table。

固定結果：

```text
甲戊庚 → 魁丑、鉞未
乙己   → 魁子、鉞申
丙丁   → 魁亥、鉞酉
辛     → 魁午、鉞寅
壬癸   → 魁卯、鉞巳
```

### 6.3 祿存／擎羊／陀羅

直接重用 2C0 deterministic placement：

```text
甲祿寅
乙祿卯
丙戊祿巳
丁己祿午
庚祿申
辛祿酉
壬祿亥
癸祿子
```

擎羊＝祿存下一地支位；陀羅＝祿存上一地支位，以 Project 已有 placement helper 的 canonical rotation 為準。

### 6.4 天馬

直接重用 2C0 deterministic placement：

```text
寅午戌 → 申
申子辰 → 寅
巳酉丑 → 亥
亥卯未 → 巳
```

此處輸入的是「該動態 scope 的 earthly branch」，不是出生年支。

若既有 helper 參數名稱仍叫 `year_branch`，Phase 2C 只重用其純規則結果，不讓命名誤導資料 provenance；implementation plan 可用薄 wrapper 表達「cycle_branch」。

### 6.5 流昌／流曲：按該 scope 天干

Phase 2C 與 Natal 文昌文曲規則不同：Natal 昌曲依出生時支；Flowing Stars 昌曲依當層天干。

pinned iztro qualification target 固定為：

| 天干 | 昌 | 曲 |
|---|---|---|
| 甲 | 巳 | 酉 |
| 乙 | 午 | 申 |
| 丙 | 申 | 午 |
| 丁 | 酉 | 巳 |
| 戊 | 申 | 午 |
| 己 | 酉 | 巳 |
| 庚 | 亥 | 卯 |
| 辛 | 子 | 寅 |
| 壬 | 寅 | 子 |
| 癸 | 卯 | 亥 |

不得呼叫 Natal 的 `place_chang_qu(hour_branch)` 來假裝流昌流曲。

### 6.6 紅鸞／天喜：按該 scope 地支

pinned profile 固定「卯上起子逆數，天喜為紅鸞對宮」。

canonical table：

| scope 地支 | 紅鸞 | 天喜 |
|---|---|---|
| 子 | 卯 | 酉 |
| 丑 | 寅 | 申 |
| 寅 | 丑 | 未 |
| 卯 | 子 | 午 |
| 辰 | 亥 | 巳 |
| 巳 | 戌 | 辰 |
| 午 | 酉 | 卯 |
| 未 | 申 | 寅 |
| 申 | 未 | 丑 |
| 酉 | 午 | 子 |
| 戌 | 巳 | 亥 |
| 亥 | 辰 | 戌 |

### 6.7 年解：yearly only

pinned iztro `getNianjieIndex()` qualification target：

| 流年地支 | 年解 |
|---|---|
| 子 | 戌 |
| 丑 | 酉 |
| 寅 | 申 |
| 卯 | 未 |
| 辰 | 午 |
| 巳 | 巳 |
| 午 | 辰 |
| 未 | 卯 |
| 申 | 寅 |
| 酉 | 丑 |
| 戌 | 子 |
| 亥 | 亥 |

只有 `scope == yearly` 才建立年解。

對 decadal/monthly/daily/hourly 強行要求年解必須 fail closed 或不在 catalog 中；不得默默多一顆。

### 6.8 category

固定 canonical category：

```text
天魁 / 天鉞 / 文昌 / 文曲 = soft
祿存                   = lucun
擎羊 / 陀羅             = tough
天馬                   = tianma
紅鸞 / 天喜             = flower
年解                   = helper
```

category 用於結構化查詢，不代表吉凶評分。

### 6.9 deterministic ordering

固定 output sequence：

```text
1 天魁
2 天鉞
3 文昌
4 文曲
5 祿存
6 擎羊
7 陀羅
8 天馬
9 紅鸞
10 天喜
11 年解（yearly only）
```

任何 input ordering、dict ordering、oracle ordering 都不得改變 Project output ordering。

---

## 七、Scope Source Adapters

### 7.1 共通規則

Source adapter 負責「取得可靠干支」；Pure core 不負責。

所有 adapter 必須產生同一型別 `FlowingStarSource`，並保留來源 maturity / validation / provenance。

所有正式 adapter 都必須顯式取得 `ChartIdentity`；`ResolvedCycleStem` 本身沒有命主 identity，因此不得從 module global state、最近一次排盤或 singleton 猜 chart。

概念介面：

```text
from_decadal(chart_identity, decadal_period, ...)
from_yearly_calendar(chart_identity, calendar_context, ...)
from_resolved_cycle_stem(chart_identity, resolved_cycle_stem, ...)
from_explicit_structured_source(chart_identity, scope, reference, stem, branch, provenance, ...)
```

最後一個只供已結構化、已驗證的 external/imported cycle source；它不是 raw text parser。

Precision Gate：

> Precision must be earned by input.

若輸入只足夠定位流年，不得包裝成流月／流日／流時流曜。

### 7.2 Decadal adapter

Project-native 來源：Phase 2C0 `ZiweiDecadalPeriod`。

使用：

- `index`
- `age_start`
- `age_end`
- `stem_branch`
- `palace`
- `direction`

其中 `stem_branch` 的第一字為天干、第二字為地支，並必須通過合法六十甲子 pair validation。

不得重新用出生年、性別再推一次大限干支。

stable reference 必須包含至少：

```text
decadal index + age range + stem_branch
```

並在 layer identity 中與 source 完全一致。

若使用 external natal chart，只有 external decadal source 已結構化、可驗證且含完整合法干支時，才可由 `from_explicit_structured_source()` 建立 Project-derived flowing-star layer；不能從缺失資料猜大限，也不把 external source 轉寫成 Project-native natal fact。

### 7.3 Yearly adapter

Phase 2C v1 的 common/iztro-qualified yearly source 採：

```text
lunar year stem + lunar year branch
```

不是八字立春流年。

理由：pinned iztro horoscope default `horoscopeDivide = normal`，其 normal 定義為農曆正月初一分界；`exact` 才是立春分界。

Project 必須建立/重用 system-neutral lunar-year sexagenary helper，例如：

```text
lunar_year_stem(lunar_year)
lunar_year_branch(lunar_year)
```

helper 放在 Calendar neutral layer，不放在 Bazi，也不讓 `flowing_stars.py` 自己硬編年份 `%` 公式。

Yearly adapter 最低輸入為可用的 `CalendarContext` + explicit `ChartIdentity`，使用：

- `context.lunar.year`
- calendar validation
- normalized civil date（只作 provenance/reference，不決定干支公式）

reference 固定表達 lunar-year basis，例如：

```text
lunar-year:2026
```

若未來新增 `exact/立春` profile，必須是新 profile/version，不覆寫 v1。

Public iztro runner 每次執行 qualification 前必須明確 reset / set `horoscopeDivide = normal` 等本設計依賴的 default config，不能繼承前一個 test case 的 mutable global config。

### 7.4 Monthly adapter

接受 explicit `ChartIdentity` + Phase 2B `ResolvedCycleStem(scope="monthly")`。

不得重算：

- 農曆月干支。
- 閏月 15/16 分界。
- 五虎遁。

FlowingStarSource.reference 必須沿用 `ResolvedCycleStem.reference`。

### 7.5 Daily adapter

接受 explicit `ChartIdentity` + Phase 2B `ResolvedCycleStem(scope="daily")`。

不得重算：

- JDN。
- 干支日。
- 23:00 `late_zi_forward-v1` effective date。

reference 必須沿用 Phase 2B day reference。

### 7.6 Hourly adapter

接受 explicit `ChartIdentity` + Phase 2B `ResolvedCycleStem(scope="hourly")`。

不得重算：

- effective Ziwei day stem。
- 五鼠遁。
- hour branch。
- 23:00 day boundary。

reference 必須沿用 Phase 2B hour reference。

### 7.7 validation propagation

固定：

```text
validated
    → 可建立 Experimental layer

boundary_caution
    → 可建立 layer，但 validation/provenance 必須保留 caution

boundary_conflict
    → fail closed

out_of_validated_range
    → Phase 2C v1 fail closed，不產生 available layer
```

Phase 2C 不擴張 Calendar Resolver validated range。

---

## 八、Layer Identity 與 Composition

### 8.1 與四化／飛化共享 cycle join key，不共享完整 identity equality

若同一 target scope/reference 已有：

```text
CycleTransformationLayer
```

Phase 2C 的：

```text
FlowingStarLayer
```

兩者 join 只比較固定 key：

```text
chart_id
scope
reference
```

兩個 layer 各自使用自己的 `rule_profile`；不得把完整 `LayerIdentity` equality 當 join 條件。

實作可使用 tuple 或小型 immutable `CycleJoinKey` view；若新增 model，不能改掉既有 `LayerIdentity` equality 語意。

### 8.2 不把 FlowingStarLayer 塞進 `ZiweiLayerStack.cycles`

Phase 2C v1 不改變 `ZiweiLayerStack.cycles` 的既有四化語意。

可新增 read-only composite/query view，例如：

```text
ZiweiDynamicCycleView
├─ transformation_layer
├─ flowing_star_layer
└─ materialized palace records
```

或功能等價的 query helper。

### 8.3 join fail closed

若兩層：

- chart_id 不同。
- scope 不同。
- reference 不同。

不得合併。

錯誤必須指出 mismatch field，不得只回 generic invalid state。

---

## 九、Materialized Palace View

### 9.1 Natal palace mapping

若有 validated natal twelve-palace map，可將 `target_branch` 對應到：

```text
natal_palace
```

但這只是 view；不得改寫 placement.target_branch。

### 9.2 Scope palace mapping

若 caller 另提供與同一 scope/reference 對應的完整十二宮 mapping，可產生：

```text
scope_palace
```

Phase 2C 不要求所有 scope 在 v1 都必須已有完整 scope-palace map，因為核心流曜位置不依賴宮名才能成立。

若 scope palace mapping 缺失：

```text
scope_palace = unavailable / None
```

不是 placement failure。

若 mapping 自稱存在但：

- 少於十二宮。
- branch 重複。
- scope/reference 不匹配。

則 materialization fail closed，不猜宮名。

---

## 十、Display Name 與 Localization 邊界

核心 identity 一律是本體星名：

```text
天魁 / 天鉞 / 文昌 / ...
```

顯示層才依 scope 產生：

```text
decadal → 運魁 / 運鉞 / 運昌 / ...
yearly  → 流魁 / 流鉞 / 流昌 / ...
monthly → 月魁 / 月鉞 / 月昌 / ...
daily   → 日魁 / 日鉞 / 日昌 / ...
hourly  → 時魁 / 時鉞 / 時昌 / ...
```

年解保留 `年解`。

v1 不建立多語 i18n subsystem；qualification 比較 canonical base identity + branch + category + scope，不比較第三方 UI 翻譯字串。

---

## 十一、錯誤與 Fail-closed

Phase 2C 至少固定 machine-readable error codes：

```text
unsupported_flowing_star_scope
missing_cycle_stem_source
cycle_scope_mismatch
cycle_reference_mismatch
chart_basis_mismatch
invalid_flowing_star_stem
invalid_flowing_star_branch
invalid_flowing_star_stem_branch_pair
calendar_boundary_conflict
calendar_out_of_validated_range
decadal_source_not_resolved
incomplete_flowing_star_catalog
duplicate_flowing_star_identity
invalid_flowing_star_layer
flowing_star_materialization_mismatch
flowing_star_oracle_mismatch
```

### 11.1 不允許 LLM 補值

例如：

- 不知道大限干支。
- 日期只有年份卻要求流日。
- 「晚上」但無法確定時辰卻要求流時。
- Calendar boundary conflict。

一律 upstream ask / keep candidates / downgrade；engine 不用自然語言猜一個值塞進 resolver。

### 11.2 source scope mismatch

例如：

```text
ResolvedCycleStem.scope = daily
request = monthly
```

即使干支本身合法，也必須 `cycle_scope_mismatch`。

### 11.3 reference mismatch

若 caller 嘗試把「2026-08-22 流日」的四化 layer 與「2026-08-23 流日」的 flowing-star layer 疊在一起，必須拒絕。

### 11.4 sexagenary pair mismatch

Pure placement oracle 可以測所有 10×12 stem/branch component combinations；但正式 source 若為：

```text
甲丑
乙子
```

等不屬於六十甲子的配對，必須 `invalid_flowing_star_stem_branch_pair`，不能因兩個字個別合法就接受。

---

## 十二、Capability Lifecycle

Phase 2C v1 implementation 完成且 acceptance PASS 後：

```text
ziwei.flowing_stars
implementation = implemented
maturity       = experimental
routing        = on_demand
rule_version   = 1.0-exp
module         = engine.ziwei.flowing_stars
```

### 12.1 Static dependencies 不假裝成所有 scope 的 AND 條件

不同 scope 的 source prerequisite 不同：

```text
decadal → resolved decadal stem_branch
yearly  → validated lunar-year Calendar source
monthly → ziwei.flow_month_stem
daily   → ziwei.flow_day_stem
hourly  → ziwei.flow_hour_stem
```

因此 registry 的普通 `dependencies` 不應錯誤填成「三個 fine-cycle capability 全部必須存在才能算任何流曜」。

Phase 2C 採非破壞性 metadata：

```text
conditional_dependencies = {
  decadal: (resolved_decadal_source,),
  yearly: (validated_lunar_year_source,),
  monthly: (ziwei.flow_month_stem,),
  daily: (ziwei.flow_day_stem,),
  hourly: (ziwei.flow_hour_stem,),
}
```

這些是 capability metadata，不把前兩個 symbolic prerequisite 假裝成可直接 `can_execute()` 的 capability ID。

既有 `dependencies` 保持空 tuple；`can_execute()` 的既有語意保持「implementation == implemented」，真正執行時由 source adapter fail closed。

### 12.2 不做 maturity cascade

Phase 2C PASS 不代表：

- `ziwei.flow_day_stem` 升 Stable。
- `ziwei.flow_hour_stem` 升 Stable。
- `ziwei.natal_chart` 升 Stable。
- Astralium fine-cycle qualification 自動 PASS。

各 capability 獨立治理。

---

## 十三、Public Qualification

### 13.1 Pure core exhaustive oracle matrix

pinned iztro `getHoroscopeStar()` 將 stem 與 branch 視為兩個獨立合法 component；為完整驗證 placement table，Pure core qualification 穷舉：

```text
10 heavenly stems
× 12 earthly branches
× 5 scopes
= 600 component combinations
```

每組 exact compare：

- scope。
- base star identity。
- target branch。
- category。
- star count。

預期：

```text
decadal 120 component pairs × 10 stars
yearly  120 component pairs × 11 stars
monthly 120 component pairs × 10 stars
daily   120 component pairs × 10 stars
hourly  120 component pairs × 10 stars
```

PASS 條件：

```text
600/600 pure-core combinations PASS
0 unexpected mismatch
```

這個 600 matrix **不是**在宣稱 120 組 stem/branch 都是合法六十甲子；它只窮舉純函式兩個 component 的規則域。

### 13.2 Valid source matrix

正式 `FlowingStarSource` 只接受六十甲子合法 pair。

另外必須測：

```text
60 valid sexagenary pairs × 5 scopes = 300 valid sources
60 invalid parity pairs × 5 scopes = 300 rejected sources
```

合法來源全部可建立；非法 pair 全部以 `invalid_flowing_star_stem_branch_pair` fail closed。

### 13.3 Upstream pinned vectors

另外保留 pinned iztro upstream tests 中具代表性的 golden vectors，例如：

```text
getHoroscopeStar("庚", "辰", "decadal")
getHoroscopeStar("癸", "卯", "yearly")
```

目的是讓 qualification runner 自身也有 regression anchor，避免 600-case converter 寫錯卻彼此自洽。

### 13.4 Adapter qualification

至少覆蓋：

1. Decadal `ZiweiDecadalPeriod.stem_branch` → FlowingStarSource。
2. Lunar new year 前／後 yearly source。
3. Leap-month day 15 / 16 monthly source reuse。
4. 22:59 / 23:00 daily source reuse。
5. 22:59 / 23:00 hourly source reuse。
6. 正常時辰切換。
7. `boundary_caution` propagation。
8. `boundary_conflict` fail closed。
9. `out_of_validated_range` fail closed。
10. scope mismatch。
11. reference mismatch。
12. chart mismatch。
13. external structured source valid/invalid pair。

### 13.5 Property / invariant tests

至少：

- 非 yearly 永遠 10 顆 canonical identities。
- yearly 永遠多且只多 `年解`。
- 天喜永遠與紅鸞相差六支。
- 擎羊／陀羅永遠位於祿存相鄰兩位。
- 天馬永遠只在寅／申／巳／亥。
- sequence deterministic。
- 同一 input/profile/version byte-equivalent structured output。

---

## 十四、Private Astralium Qualification

Phase 2C0 private Natal qualification 已有一案 PASS，但那只驗證本命盤，不等於 Phase 2C 流曜已驗證。

Phase 2B Astralium fine-cycle 目前仍為 PENDING；Phase 2C 不得借用 Natal private PASS 宣稱流曜 private PASS。

Phase 2C v1 初始狀態：

```text
Astralium flowing-stars = PENDING
```

若日後使用者提供可合法校驗的 Astralium 動態流曜資料：

- raw chart 不提交 repo。
- raw birth input 不提交 repo。
- repo 只存 aggregate count / status / digest / version。
- private PASS 仍不自動 promotion Stable。

---

## 十五、Privacy

Phase 2C public qualification 本身不需要私人出生資料。

任何 repo qualification artifact 不得含：

```text
full_name
full_address
hospital
raw_birth_input
raw_chart
external_raw
private path
```

如使用 private qualification，只允許 privacy-safe aggregate evidence。

---

## 十六、文件與 Release 邊界

Phase 2C implementation 完成後，需同步：

- `命理推導計算規則.md`
- `命理分析作業規範.md`（只有在工作流程規則需要新增明示邊界時才改）
- `core/核心提示詞.md`
- `docs/架構說明.md`
- `README.md`
- `CHANGELOG.md`
- capability registry documentation

CHANGELOG 新增：

```text
Unreleased｜Phase 2C Ziwei Flowing Stars
```

不得提前修改：

```text
VERSION.md
Git tag
GitHub Release
```

正式 release identity 仍維持 v1.2.0，直到另有 release approval。

---

## 十七、預期程式邊界

### 17.1 主要新增／修改

預期新增：

```text
engine/ziwei/flowing_star_models.py
engine/ziwei/flowing_star_sources.py
engine/ziwei/flowing_stars.py
engine/ziwei/flowing_star_view.py
```

預期小幅修改：

```text
engine/calendar/sexagenary.py        # neutral lunar_year_branch + legal pair helper
engine/ziwei/capabilities.py
engine/ziwei/__init__.py             # public exports if needed
```

必要測試／qualification：

```text
tests/test_ziwei_flowing_star_models.py
tests/test_ziwei_flowing_stars.py
tests/test_ziwei_flowing_star_sources.py
tests/test_ziwei_flowing_star_view.py
tests/test_ziwei_phase2c_capabilities.py
tests/test_ziwei_phase2c_qualification.py
qualification/ziwei/phase2c-*.json
tools/qualify_ziwei_phase2c.py
```

實際檔名可由 implementation plan 依 repo pattern 微調，但不得改責任分層。

### 17.2 不碰的正式核心

除非 RED test 證明必要且經重新設計，不修改：

```text
engine/ziwei/transformations.py
engine/ziwei/flying.py
CycleTransformationLayer semantics
Natal star placement formulas
Bazi engine
Calendar civil-date policy
```

可以重用 Natal deterministic placement helper，但不得為了 Phase 2C 改變既有 Natal output。

---

## 十八、Testing / Acceptance Gates

Phase 2C implementation 採 TDD；每個 task 都遵守：

```text
RED → 確認預期 failure → 最小 GREEN → focused regression → commit
```

Final Acceptance 至少包含：

### Gate A｜Rule / capability reconciliation

```text
PHASE2C_RULE_SOURCE_RECONCILIATION_PASS
```

### Gate B｜Models / pure core

- immutable model validation。
- legal sexagenary pair validation。
- 10/11 star catalog invariants。
- deterministic ordering。
- invalid stem/branch/scope fail closed。

### Gate C｜Source adapters

- decadal/yearly/monthly/daily/hourly 全部來源契約。
- explicit chart identity。
- precision gate。
- boundary propagation。
- scope/reference/chart mismatch。

### Gate D｜Materialization / composition

- branch → natal palace。
- optional scope palace。
- same `chart_id + scope + reference` join key。
- rule_profile 可不同但不能破壞 join。
- mismatch fail closed。
- Stable Phase 2A model regression unchanged。

### Gate E｜Pinned public oracle

```text
IZTRO_FLOWING_STARS_600_600_PASS
IZTRO_FLOWING_STARS_0_UNEXPECTED_MISMATCH
FLOWING_STAR_VALID_SOURCE_300_300_PASS
FLOWING_STAR_INVALID_SOURCE_300_300_REJECTED
```

### Gate F｜Existing regression

至少：

- Calendar suite。
- Bazi suite。
- Ziwei Phase 2A。
- Ziwei Phase 2B。
- Phase 2C0 Natal。
- full repository regression。

### Gate G｜Python compatibility

```text
Python 3.9 syntax PASS
```

不得引入只有 Python 3.10+ 才支援的 production annotation syntax。

### Gate H｜Privacy / scope

確認：

- 無 private raw data。
- 無 temporary validation workflow 混入 formal feature tree。
- 無 Qimen 變更。
- 無 VERSION/tag/release 變更。
- 無歲前／將前十二神偷渡。
- 無 Phase 2B/2C0 maturity promotion。

### Gate I｜Capability state

最終應為：

```text
ziwei.flowing_stars = implemented / experimental / on_demand / 1.0-exp
```

並明確確認：

```text
ziwei.transformations = stable unchanged
ziwei.flying = stable unchanged
ziwei.flow_month_stem = experimental unchanged
ziwei.flow_day_stem = experimental unchanged
ziwei.flow_hour_stem = experimental unchanged
ziwei.natal_chart = experimental unchanged
```

### Gate J｜Final marker

全部前置 gate 成功後才可產生：

```text
PHASE2C_ACCEPTANCE_PASS
```

任何 Gate FAIL 都停止 downstream；validation infrastructure failure 與 product algorithm failure 必須分開標示。

---

## 十九、Branch / Review / Merge Governance

Phase 2C 沿用既定治理：

```text
main
  ↓
design/ziwei-flowing-stars
  ↓（written spec approval 後）
implementation plan
  ↓（implementation approval 後）
feature/ziwei-flowing-stars-v1
  ↓
validation branches / MUST NEVER MERGE PRs
```

硬性規則：

1. Written spec 未獲明確批准前，不 invoke implementation workflow。
2. Implementation plan 需獨立 review / approval。
3. feature → design 需獨立明確批准。
4. design → main 需第二次獨立明確批准。
5. temporary validation workflows / PR 不得 merge。
6. ambiguous「繼續」不得推定 merge approval。
7. final integration 必須用 exact-head evidence，不混用舊 head 的 GREEN。

---

## 二十、成功定義

Phase 2C v1 只有在下列全部成立時才算完成：

1. 使用者可以對已解析的大限／流年／流月／流日／流時來源取得 deterministic 流曜位置。
2. 核心十顆流曜與 yearly 年解的 branch placement 全部版本化。
3. Phase 2B monthly/daily/hourly source 被重用，不重算。
4. Decadal 使用 2C0 decadal stem_branch，不重算。
5. Yearly 使用明示 lunar-year profile，不混用 Bazi 立春口徑。
6. FlowingStarLayer 與 Stable transformation/flying layer 可按 `chart_id + scope + reference` 安全 join，但資料模型與 rule profile 分離。
7. pinned iztro 600/600 pure-core combinations 全部 match，0 unexpected mismatch。
8. 正式 FlowingStarSource 只接受60合法六十甲子 pair，非法 pair 全部 fail closed。
9. boundary / mismatch / insufficient precision 全部 fail closed。
10. private Astralium 流曜若未提供，誠實維持 PENDING。
11. capability 只升到 implemented / experimental / on_demand，不提前 Stable。
12. full repo regression、Python 3.9、privacy/scope gates 全 PASS。
13. final formal feature tree 不含 temporary validation workflows。

Phase 2C 的定位因此是：

> **補上紫微動態星曜的 deterministic layer；不重做時間、不重做四化、不重做飛化、不擴張成雜曜大全。**
