# Ziwei Transformation & Flying Core v1 設計規格

- 日期：2026-08-21
- Branch：`design/ziwei-transformation-flying-core`
- 狀態：Design spec，等待使用者 final review；尚未進入 implementation plan
- 分類：Architectural
- 階段：Phase 2A
- 架構定位：紫微四化規則核心、宮干飛化核心與跨運限 Composition Layer
- 前置依賴：Calendar Resolver v1 已進 `main`；既有 Ziwei month/day/hour 定位 capability 保持原責任

## 一、目的

Phase 2A 的目的，是把紫微斗數中目前散落在外部結構化資料裡的「十天干四化、四化星落宮、本命十二宮宮干飛化、大限／流年四化與飛化」建立成固定、可重現、可驗證、可追溯的 Project 核心能力。

本 subsystem 不重新排本命星盤，也不自行產生流月、流日、流時天干。它只處理已明確提供或已由上游合法解析的天干、已校驗本命星曜位置與宮干資料。

第一版資料流：

```text
已校驗本命資料
├─ StarLocationIndex
├─ PalaceStemIndex
└─ natal chart identity
        │
        ├─────────────────────────────┐
        │                             │
        ▼                             ▼
Transformation Core              Palace Flying
天干 → 祿/權/科/忌              十二宮宮干逐宮產生 edges
        │                             │
        ▼                             ▼
TransformationSet              NatalFlyingGraph
        │                             │
        ├──────────────┐              ├─ same_palace
        │              │              ├─ opposite_palace_incoming
        ▼              ▼              └─ normal
大限/流年 source    Flying Core
        │              │
        ▼              ▼
CycleTransformationLayer
        │
        ▼
ZiweiLayerStack / Composite View
        │
        ▼
AI interpretation（本 spec 不實作）
```

核心原則：

> 四化核心只回答「天干使哪些星化祿、權、科、忌」。
>
> 飛化核心只回答「該四化星依已校驗本命星曜位置落在哪個宮」。
>
> 自化／向心術語不得污染底層幾何事實。
>
> 不同時間層可以同時存在，但不得互相覆寫。
>
> 同一時間層的規則衝突必須 fail closed，不得當成兩個訊號一起解讀。
>
> Source fact、Project derived、qualification evidence 必須分開保存。

---

## 二、背景與現況

### 2.1 現有 Ziwei capability

目前 `engine/ziwei/capabilities.py` 已預留：

```text
ziwei.transformations = planned
ziwei.flowing_stars    = planned
ziwei.flying           = planned
```

既有時間定位能力：

```text
ziwei.flow_month_palaces = implemented / stable / default
ziwei.flow_day_palaces   = implemented / experimental / on_demand
ziwei.flow_hour_palaces  = implemented / experimental / on_demand
```

Phase 2A 沿用既有 capability 三軸模型，不把四化或飛化塞回 `month.py`、`day.py`、`hour.py`。

### 2.2 Project 現有規範

Project 規範要求：

- 原始盤面事實、已校驗資料與 Project 推導盤面分開。
- Project 推導必須由固定、可重現算法產生。
- 紫微流月／流日／流時及其細層四化／飛化在規則未固定前不得自行啟用。
- 不得把 Project 推導結果冒充 Astralium 或其他第三方原始輸出。
- 不同版本／規則來源衝突時，不得自行選擇最符合既有解讀的版本。

Phase 2A 只解決本命宮干、生年、大限與流年的四化／飛化核心，不解除細運限制。

---

## 三、Scope

### 3.1 v1 必須實作

1. 十天干四化 profile 與版本化。
2. `Transformation` / `TransformationSet` 結構化模型。
3. `StarLocationIndex` 輸入契約。
4. `PalaceStemSource` 與 `CycleStemSource` 明確分型。
5. `FlyingEdge` 與 `FlyingResult`。
6. 本命十二宮宮干飛化 `NatalFlyingGraph`。
7. 宮位幾何 relation：
   - `same_palace`
   - `opposite_palace_incoming`
   - `normal`
8. Astralium-compatible presentation mapping：
   - `same_palace` → `↓` / 離心自化
   - `opposite_palace_incoming` → `↑` / 向心自化
9. 生年、大限、流年 `CycleTransformationLayer`。
10. `ZiweiLayerStack` 與唯讀 `Composite View`。
11. 以宮位、星曜、四化類型查詢各 layer 的 read API。
12. provenance、qualification、availability、conflict metadata。
13. capability lifecycle 與 promotion gate。
14. 完整 automated tests、external qualification、full repo regression 與 main post-merge regression。

### 3.2 v1 明確不實作

以下全部 out of scope：

- 流月天干算法。
- 流日天干算法。
- 流時天干算法。
- 紫微 23:00 換日派別選擇。
- 流月四化／飛化。
- 流日四化／飛化。
- 流時四化／飛化。
- 流曜／流魁／流鉞／流昌／流曲等 moving stars。
- 重新安十四主星或重排本命盤。
- 重新計算本命宮位。
- 修改 Calendar Resolver。
- 修改 Bazi engine。
- Qimen。
- 真太陽時。
- 吉凶量化分數。
- `祿 +3 / 忌 -3` 類 scoring。
- 自動判斷哪一層「比較強」。
- AI 命理解讀與事件預測。
- 將任何單一外部排盤系統宣稱成紫微唯一標準。

---

## 四、模組邊界

v1 預期新增／調整：

```text
engine/ziwei/
├─ common.py                     # 既有十二宮順序；新增共用 opposite helper 時須保持單一來源
├─ capabilities.py               # 更新 capability metadata
├─ models.py                     # Phase 2A typed models
├─ transformation_profiles.py    # 規則資料，不做 orchestration
├─ transformations.py            # 天干 → TransformationSet
├─ flying.py                     # TransformationSet + StarLocationIndex → Flying edges / graph
└─ composition.py                # layer stack + conflict/availability + readonly views
```

`month.py`、`day.py`、`hour.py`、`calendar_adapter.py` 第一版原則上不吸收 Phase 2A 邏輯；若 capability metadata 或 imports 需調整，必須保持其既有 timing responsibility 不變。

### 4.1 `transformation_profiles.py`

只保存版本化規則資料。

不得：

- 查命盤。
- 查宮位。
- 判斷運限。
- 產生飛化。
- 讀 CalendarContext。

第一個正式 profile：

```text
profile_id = metaphysics-lab-common-v1
```

此名稱刻意不使用 `standard`、`canonical_ziwei` 或「唯一標準」等字眼。

第一版十干四化表：

| 天干 | 化祿 | 化權 | 化科 | 化忌 |
|---|---|---|---|---|
| 甲 | 廉貞 | 破軍 | 武曲 | 太陽 |
| 乙 | 天機 | 天梁 | 紫微 | 太陰 |
| 丙 | 天同 | 天機 | 文昌 | 廉貞 |
| 丁 | 太陰 | 天同 | 天機 | 巨門 |
| 戊 | 貪狼 | 太陰 | 右弼 | 天機 |
| 己 | 武曲 | 貪狼 | 天梁 | 文曲 |
| 庚 | 太陽 | 武曲 | 太陰 | 天同 |
| 辛 | 巨門 | 太陽 | 文曲 | 文昌 |
| 壬 | 天梁 | 紫微 | 左輔 | 武曲 |
| 癸 | 破軍 | 巨門 | 太陰 | 貪狼 |

資格驗證基準：

- Project 私有 Astralium profile：`astralium-ziwei-v1-common`。
- 獨立公開 qualification source：`SylarLong/iztro`，固定 revision `814b77e6371e1050cac31bbf674db3c3138fcfde`，其中公開十天干 mutagen table 與本 profile 比對。

外部 source 只作 qualification，不是 runtime dependency，也不是 Project 唯一真理來源。

### 4.2 `transformations.py`

唯一主要責任：

```text
heavenly_stem + profile_id
→ TransformationSet
```

不得知道：

- 這是生年、大限、流年還是流月。
- 某顆星在哪個宮。
- 命主是誰。
- 目標年份。
- Astralium runtime。

因此不得建立：

```text
year_transform()
month_transform()
day_transform()
hour_transform()
```

這類重複 API。

### 4.3 `flying.py`

唯一主要責任：

```text
TransformationSet
+ StarLocationIndex
+ explicit source
→ FlyingEdge[] / FlyingResult
```

它不得自行安星、重新排盤或改寫 `StarLocationIndex`。

### 4.4 `composition.py`

只負責：

- 把已完成的 transformation / flying results 包裝成各 scope layer。
- 保留多層資料。
- 檢查 layer identity 與同層衝突。
- 提供 readonly query views。
- 附加 availability / provenance / qualification metadata。

不得重新計算四化或飛化，也不得進行吉凶解讀。

---

## 五、核心資料模型

### 5.1 TransformationType

```text
TransformationType = 祿 | 權 | 科 | 忌
```

實際 Python enum 命名可採 ASCII identifier，但 serialized public value 必須穩定且可讀。

每個有效 profile 對每個天干必須正好提供四種 type，各 type 恰好一次。

不得要求四個 `star` 一定互不重複；profile invariant 只約束 transformation type 完整性，不額外發明流派未要求的星曜唯一性規則。

### 5.2 Transformation

```text
Transformation
├─ type
├─ star
└─ sequence
```

`sequence` 固定：

```text
0 = 祿
1 = 權
2 = 科
3 = 忌
```

### 5.3 TransformationSet

```text
TransformationSet
├─ heavenly_stem
├─ profile_id
├─ rule_version
├─ transformations[4]
└─ provenance
```

`TransformationSet` 不含年份或 scope；它是純規則輸出。

### 5.4 ChartIdentity

所有 star / palace 基準都必須綁 chart identity，避免跨命盤混用。

```text
ChartIdentity
├─ chart_id
├─ chart_basis
└─ source_profile
```

`chart_id` 是 opaque identifier；不得要求包含姓名、生日或其他個資。

### 5.5 StarLocationIndex

```text
StarLocationIndex
├─ chart_identity
├─ locations: star -> palace
├─ validation_status
└─ provenance
```

第一版 target basis 僅允許：

```text
target_basis = natal_star_location
```

禁止流月重安星、運限星曜重排或其他 target basis。

同一個 index 中同一顆星不得指向兩個不同宮位；若發現：

```text
天機 -> 夫妻宮
天機 -> 官祿宮
```

必須報資料衝突，不得猜測。

一個宮可包含多顆星，這不構成衝突。

### 5.6 PalaceStemIndex

```text
PalaceStemIndex
├─ chart_identity
└─ palace -> heavenly_stem
```

本命十二宮飛化必須明確使用 PalaceStemIndex；不得從流年命宮干支、流年天干或其他 cycle metadata 反推本命宮干。

### 5.7 Source type

#### PalaceStemSource

```text
PalaceStemSource
├─ kind = palace_stem
├─ chart_identity
├─ palace
└─ heavenly_stem
```

只有此 source type 可以進宮位自化幾何 classifier。

#### CycleStemSource

```text
CycleStemSource
├─ kind = cycle_stem
├─ chart_identity
├─ scope
├─ reference
└─ heavenly_stem
```

第一版正式支援 scope：

```text
birth_year
decadal
yearly
```

`monthly / daily / hourly` schema 可以在 type system 中預留，但 availability 必須維持 unavailable，且不得由 v1 runtime 產生。

### 5.8 FlyingEdge

```text
FlyingEdge
├─ edge_id
├─ source
├─ heavenly_stem
├─ transformation_type
├─ star
├─ target_palace
├─ target_basis = natal_star_location
├─ profile_id
├─ geometric_relation
└─ provenance
```

`edge_id` 必須可在一次結果內穩定識別，但不要求跨 rule version 永久不變。

### 5.9 Palace geometric relation

底層 enum 僅描述幾何事實：

```text
same_palace
opposite_palace_incoming
normal
```

判定僅適用 `PalaceStemSource`。

對 `CycleStemSource`：

```text
geometric_relation = null
```

不得因 cycle 的四化星落在某宮，就把該宮標成自化。

### 5.10 Presentation relation

Astralium-compatible presentation profile：

```text
same_palace
→ 離心自化
→ ↓

opposite_palace_incoming
→ 向心自化
→ ↑
```

`normal` 不產生自化箭頭。

此 mapping 是 presentation / terminology profile，不是 Flying Engine 的物理真理。未來若其他流派術語不同，只改 presentation mapping，不改底層 edge。

### 5.11 NatalFlyingGraph

```text
NatalFlyingGraph
├─ chart_identity
├─ edges[48]
├─ outgoing_index: palace -> edge[]
├─ incoming_index: palace -> edge[]
└─ derived_relations
```

十二宮每宮四化，因此完整 graph 必須 exactly 48 edges。

### 5.12 LayerProvenance

```text
LayerProvenance
├─ classification
├─ source_name
├─ source_version
├─ rule_profile
├─ rule_version
├─ derived_by
├─ qualified_against[]
└─ qualification_status
```

`classification` 至少區分：

```text
source_fact
validated_source_fact
project_derived
```

`qualification_status` 至少：

```text
not_run
exact_match
mismatch
```

即使 Project 結果與 Astralium 完全一致，也不得把 Project result 改標成 Astralium source fact。

### 5.13 LayerIdentity

```text
LayerIdentity
├─ chart_id
├─ scope
├─ reference
└─ rule_profile
```

第一版 examples：

```text
birth_year / natal

decadal / 43-52-virtual-age

yearly / 2026
```

未來 monthly identity 必須包含可消除年份／閏月歧義的 reference；Phase 2A 不定義細運 reference 格式。

### 5.14 CycleTransformationLayer

```text
CycleTransformationLayer
├─ identity
├─ source
├─ heavenly_stem
├─ earthly_branch?    # 有可信來源才放
├─ transformations
├─ flying_edges[4]
├─ provenance
├─ validation
└─ availability
```

每個可執行 cycle layer 必須 exactly 4 transformations 與 4 flying edges。

### 5.15 SmallLimitContext

小限不自動轉成 TransformationLayer。

```text
SmallLimitContext
├─ reference
├─ palace
├─ stem_branch
├─ provenance
└─ transformation_layer = null
```

第一版不因為資料包提供小限干支，就自行啟用小限四化。

### 5.16 ZiweiLayerStack

```text
ZiweiLayerStack
├─ chart_identity
├─ natal
│  ├─ star_locations
│  ├─ palace_stems
│  ├─ birth_year_transformations
│  ├─ natal_flying_graph
│  └─ presentation_relations
├─ cycles
│  ├─ decadal?
│  └─ yearly?
├─ small_limit?
├─ availability
└─ provenance
```

本命 `natal` 是 reference frame，不視為普通 cycle。

---

## 六、Transformation Profile contract

### 6.1 Profile validation

任何 profile 載入前必須驗：

1. 正好 10 個合法天干。
2. 每干正好四個 transformation。
3. 祿／權／科／忌各一次。
4. sequence 為 0/1/2/3。
5. star 非空。
6. profile_id 非空。
7. rule_version 非空。
8. 不允許未識別的額外 transformation type 靜默忽略。

不符合即 `invalid_transformation_profile`。

### 6.2 No hidden fallback

未知 profile：

```text
unknown_profile
```

不得 fallback 到 `metaphysics-lab-common-v1`。

未知天干：

```text
invalid_heavenly_stem
```

不得採模糊字串匹配或自動修正。

---

## 七、Flying Graph 與自化判定

### 7.1 Opposite palace

十二宮 canonical order 沿用既有 `engine/ziwei/common.py`：

```text
命宮, 兄弟宮, 夫妻宮, 子女宮, 財帛宮, 疾厄宮,
遷移宮, 交友宮, 官祿宮, 田宅宮, 福德宮, 父母宮
```

對宮 helper 必須由單一共用函式提供：

```text
opposite_index = (index + 6) mod 12
```

得到：

```text
命宮   <-> 遷移宮
兄弟宮 <-> 交友宮
夫妻宮 <-> 官祿宮
子女宮 <-> 田宅宮
財帛宮 <-> 福德宮
疾厄宮 <-> 父母宮
```

不得在多個 module 重複 hardcode 六組對宮。

### 7.2 Relation classification

若 source 是 `PalaceStemSource`：

```text
source_palace == target_palace
→ same_palace

source_palace == opposite(target_palace)
→ opposite_palace_incoming

otherwise
→ normal
```

判斷順序應先 same，再 opposite，再 normal；雖然十二宮中 same 與 opposite 不會同時成立，仍保持 deterministic contract。

### 7.3 Cycle source exclusion

若 source 是 `CycleStemSource`：

```text
geometric_relation = null
```

例如：

```text
2026 yearly stem = 丙
廉貞化忌 -> 田宅宮
```

只表示 `yearly/忌/廉貞 -> 田宅宮`，不得被命名為「田宅宮自化忌」。

### 7.4 Self-transformation is edge-derived

不得把：

```text
天梁.self_transform = 科
```

存成星曜永久屬性。

正確方式：

```text
命宮己干
→ 天梁化科
→ 天梁本命位置 = 命宮
→ 該 edge relation = same_palace
→ presentation profile 顯示 ↓科
```

同一星曜在另一條 edge 可有完全不同 relation。

---

## 八、Composition Layer

### 8.1 No final transformation state

禁止提供：

```text
star.final_transformation
resolve_final_transformation()
```

若同一顆星存在：

```text
birth_year -> 祿
decadal    -> 科
yearly     -> 權
```

Composition 必須完整保留三條 layer facts，不得只留下最後一條。

### 8.2 Layer coexistence vs conflict

以下可以共存：

```text
decadal / 貪狼忌
yearly  / 廉貞忌
```

因為 scope 不同。

以下是 conflict：

```text
yearly / 2026 / stem = 丙
yearly / 2026 / stem = 丁
```

同一 LayerIdentity 對同一欄位出現互斥事實，必須：

```text
layer_conflict
```

並保留候選與 provenance；不得 last-write-wins。

### 8.3 Qualification mismatch is not a second layer

若同一 profile／同一丙干：

```text
Project: 祿 = 天同
External: 祿 = 另一星
```

這是：

```text
qualification_status = mismatch
```

不得把兩份結果同時疊入 2026 當作兩個「命理訊號」。

### 8.4 Small limit

小限可以放進 `ZiweiLayerStack` 的 context，但不轉成 transformation layer，直到未來正式 design 定義並驗證其算法。

### 8.5 Availability

Phase 2A 完成後：

```text
birth_year_transformations = available
natal_palace_flying        = available
decadal_transformations    = available when trusted decadal stem exists
yearly_transformations     = available when trusted yearly stem exists

monthly_transformations = unavailable
daily_transformations   = unavailable
hourly_transformations  = unavailable

reason = fine_cycle_stem_resolver_not_enabled
```

schema 預留不得被視為 capability 已啟用。

---

## 九、Composite View

`Composite View` 是唯讀 read model，不保存新的命盤事實。

第一版只需要三種核心 query。

### 9.1 `for_palace(palace)`

回傳該宮相關：

- natal stars / basis reference。
- natal outgoing palace-stem flying edges。
- natal incoming palace-stem flying edges。
- derived same/opposite relations。
- birth-year incoming transformations。
- decadal incoming transformations。
- yearly incoming transformations。
- unavailable fine-cycle markers。

不得回傳自動吉凶總分。

### 9.2 `for_star(star)`

回傳：

- natal location。
- 各 scope 對該星的 transformation records。
- 每條 record 的 target palace / provenance。

不得覆寫成單一 `current_mutagen`。

### 9.3 `for_transformation(type)`

回傳各 scope 的該類四化，例如所有：

```text
birth_year / 忌
decadal / 忌
yearly / 忌
```

用於 AI 後續檢查多層落點，但 Core 不判斷哪個忌「比較大」。

### 9.4 No resonance interpretation

Composite View 可以提供：

```text
same_target_palace = true
layer_count = 2
scopes = [decadal, yearly]
```

不得直接提供：

```text
resonance = strong_negative
```

「共振」、「加強」、「吉凶」屬 interpretation layer。

---

## 十、Data Classification 與 Qualification

### 10.1 Source fact

外部資料包直接提供的：

- 本命十二宮宮干。
- 本命星曜位置。
- 生年四化。
- 大限四化。
- 流年四化。
- 飛化落宮。

若原始來源確實提供，可標示 `source_fact` 或經 Project 校驗後 `validated_source_fact`。

### 10.2 Project derived

Phase 2A 根據固定 profile 與已校驗 input 推導的結果一律：

```text
classification = project_derived
```

不得因 external qualification exact match 而改稱 Astralium result。

### 10.3 Qualification evidence

Qualification evidence 必須記錄：

```text
source_profile
source_revision / digest
rule_profile
rule_version
cases_checked
cases_matched
mismatches
status
run_timestamp
```

私有 Astralium 原始盤面不得 commit 到 repo。

repo 可以保存：

- synthetic fixtures。
- qualification runner。
- 非個資 source profile id。
- private source digest。
- aggregate pass counts。
- mismatch summary 不含私人命盤值。

不得保存：

- 使用者姓名。
- 出生年月日時。
- 私人整張十二宮盤。
- raw Astralium export。
- 可反推出個人命盤的完整 private fixture。

---

## 十一、Error Contract

Phase 2A 至少定義以下 stable error codes：

```text
invalid_heavenly_stem
unknown_profile
invalid_transformation_profile
invalid_palace
missing_star_location
duplicate_star_location
chart_basis_mismatch
invalid_palace_stem_index
unsupported_source
unsupported_scope
layer_conflict
duplicate_layer_identity
qualification_mismatch
```

### 11.1 Fail closed

- 缺星曜位置：不得跳過該 edge 後返回 3/4 結果。
- chart identity 不一致：不得跨盤組合。
- 未支援 scope：不得降級成 yearly。
- qualification mismatch：不得自動改 expected external result 或自動選 Project 結果升 stable。

---

## 十二、Capability lifecycle

### 12.1 Design 階段

在 implementation 之前仍維持：

```text
ziwei.transformations = planned
ziwei.flying           = planned
```

新增細運 capability 若需在 registry 先占位，仍為 `planned`：

```text
ziwei.flow_month_transformations
ziwei.flow_day_transformations
ziwei.flow_hour_transformations
ziwei.flow_month_flying
ziwei.flow_day_flying
ziwei.flow_hour_flying
```

`ziwei.flowing_stars` 繼續 `planned`。

### 12.2 Implemented / experimental gate

只有在 internal implementation gates 全 PASS 後，才可：

```text
implementation = implemented
maturity = experimental
routing = on_demand
```

### 12.3 Stable gate

只有所有 external qualification + regression + privacy + post-merge main gates 全 PASS，才可：

```text
ziwei.transformations:
  implementation = implemented
  maturity = stable
  routing = on_demand

ziwei.flying:
  implementation = implemented
  maturity = stable
  routing = on_demand
```

v1 不因 stable 就自動改成 default routing。Default integration 另開獨立 routing/interpretation design，避免此 PR 改變既有分析行為。

---

## 十三、Validation & Promotion Gate

任何一 Gate FAIL：停止，不進下一 Gate。

### Gate 1：Transformation Rule Correctness

必須 exhaustively 測：

```text
10 stems × 4 transformations = 40 exact assertions
```

通過條件：

```text
TRANSFORMATION_TABLE_PASS
40 / 40 exact
```

另外驗 profile invariants：

- 10 stems exact。
- 每干 4 types exact。
- 祿權科忌各一次。
- sequence 正確。
- profile/version 完整。
- unknown profile / invalid stem fail closed。

### Gate 2A：Flying synthetic invariants

使用 synthetic `StarLocationIndex`，不得使用私人命盤 fixture。

每個 TransformationSet：

```text
4 transformations
→ exactly 4 FlyingEdges
```

每條 edge 的：

- type。
- star。
- target palace。
- target_basis。
- source。
- profile。

必須 exact。

### Gate 2B：Palace geometry exhaustive

測所有：

```text
12 source palaces × 12 target palaces = 144 combinations
```

期望 exact count：

```text
same_palace                = 12
opposite_palace_incoming   = 12
normal                     = 120
TOTAL                      = 144
```

通過條件：

```text
GEOMETRY_144_PASS
```

### Gate 2C：Cycle source exclusion

對 `CycleStemSource` 驗：

```text
geometric_relation = null
```

任何 yearly/decadal/birth-year edge 都不得誤判成 `same_palace` 或 `opposite_palace_incoming`。

### Gate 2D：Negative / error cases

至少測：

```text
invalid_heavenly_stem
unknown_profile
invalid_palace
missing_star_location
duplicate_star_location
chart_basis_mismatch
invalid_palace_stem_index
incomplete_transformation_profile
unsupported_source
unsupported_scope
layer_conflict
duplicate_layer_identity
```

不得 silent fallback。

### Gate 2E：Composition no-overwrite

建立同星多 layer synthetic case，例如：

```text
birth_year -> 祿
decadal    -> 科
yearly     -> 權
```

Composite result 必須保留全部三筆，且 query 可分 scope 取回。

另驗同一 LayerIdentity 矛盾時必須 `layer_conflict`。

### Gate 2F：Availability

必須驗：

```text
monthly_transformations = unavailable
daily_transformations   = unavailable
hourly_transformations  = unavailable
reason = fine_cycle_stem_resolver_not_enabled
```

並確認既有 `month.py` / `day.py` / `hour.py` 不因 schema 預留而宣稱細運四化已啟用。

### Gate 3A：Astralium private natal qualification

目前 Project 私有資料可提供本命十二宮宮干飛化：

```text
12 palaces × 4 = 48 edges
```

要求：

```text
ASTRALIUM_NATAL_48_PASS
48 / 48 exact match
```

47/48 不算 PASS。

比較欄位至少：

- source palace。
- source stem。
- transformation type。
- star。
- target palace。

Presentation relation `↑/↓` 另做 qualification，不取代底層 edge check。

### Gate 3B：Astralium decadal qualification

目前私有資料提供一組大限四化／飛化：

```text
4 edges
```

要求：

```text
ASTRALIUM_DECADAL_4_PASS
4 / 4 exact match
```

### Gate 3C：Astralium yearly qualification

目前私有資料提供 2023–2029 共七年：

```text
7 years × 4 = 28 edges
```

要求：

```text
ASTRALIUM_YEARLY_28_PASS
28 / 28 exact match
```

不得只驗 2026。

### Gate 3D：Astralium presentation qualification

根據私有資料中 `↑/↓` 標記，比對：

```text
same_palace -> ↓
opposite_palace_incoming -> ↑
```

必須以 geometric relation 為底層 truth，presentation mapping 為 qualification target。

若術語 mapping mismatch，但 48 flying edges 正確：

- Flying Core 不因此判錯。
- presentation profile 保持 experimental / mismatch。
- 不可為了符合 display 符號修改幾何規則。

### Gate 3E：Independent transformation qualification

使用 pinned public source：

```text
SylarLong/iztro
revision = 814b77e6371e1050cac31bbf674db3c3138fcfde
```

只驗十干四化 profile 層，不把 iztro 當 runtime dependency。

要求：

```text
10 stems × 4 = 40 / 40 exact match
EXTERNAL_PROFILE_PASS
```

若公開 source 未來更新，現有 qualification 必須仍以 pinned revision 重現；升版必須開新 qualification run，不可靜默跟隨 main。

### Gate 4A：Ziwei regression

必須跑全部既有 Ziwei tests，包括：

- stable/default 流月 capability。
- experimental/on_demand 流日能力。
- experimental/on_demand 流時能力。
- month/day/hour placement。
- Calendar adapter integration。
- wrapper compatibility。

Phase 2A 不得將既有細運定位能力的 maturity/routing 偷改。

### Gate 4B：Calendar regression

Calendar Resolver 全套 tests 必須 PASS。

Phase 2A 不得修改：

- civil date semantics。
- DST contract。
- lunar provider contract。
- `metaphysics_day_boundary_applied=false`。

### Gate 4C：Bazi regression

既有 Bazi tests 全部 PASS。

Phase 2A 不得 refactor 或修改 Bazi day-boundary behavior。

### Gate 4D：Full repo regression

```text
python -m unittest discover -v
```

或 repo 當時正式 full-suite command 必須 0 failures / 0 errors。

### Gate 4E：Scope gate

feature diff 必須限制於：

- Phase 2A Ziwei modules。
- Phase 2A tests。
- capability registry。
- approved docs / version / changelog。
- qualification tooling / non-private evidence。

不得進入：

- Bazi implementation。
- Qimen。
- flow month/day/hour stem resolver。
- moving stars。
- user private chart fixture。

### Gate 4F：Privacy gate

自動或人工檢查 diff：

- 無 raw Astralium export。
- 無出生日期／出生時間 fixture。
- 無私人十二宮完整 chart fixture。
- 無可識別使用者資料。

Qualification evidence 只允許 aggregate count、source profile、digest、status 與非敏感 mismatch summary。

### Gate 5：Promotion

#### Transformations stable 必要條件

```text
40 / 40 internal transformation table PASS
40 / 40 pinned iztro qualification PASS
Astralium profile qualification covers all 10 stems with 0 mismatch
negative cases PASS
full repo PASS
privacy PASS
main post-merge PASS
```

#### Flying stable 必要條件

```text
synthetic invariants PASS
geometry 144 / 144 PASS
Astralium natal 48 / 48 PASS
Astralium decadal 4 / 4 PASS
Astralium yearly 28 / 28 PASS
presentation qualification status recorded
composition PASS
negative cases PASS
full repo PASS
privacy PASS
main post-merge PASS
```

Astralium flying qualification合計：

```text
48 + 4 + 28 = 80 exact edges
```

只要 80 中任何一條 mismatch，`ziwei.flying` 不得升 stable。

---

## 十四、Mutation Gate

未來任何修改下列項目，都必須重跑 Phase 2A 全套 internal tests + external qualification + full regression：

```text
十干四化表
profile selection
PALACE_NAMES 順序
opposite_palace()
TransformationSet contract
StarLocationIndex contract
PalaceStemIndex contract
FlyingEdge contract
geometric relation classifier
presentation relation mapping
LayerIdentity
Composition conflict logic
availability logic
provenance / qualification model
```

若修改造成既有 qualification FAIL：

1. 停止 promotion。
2. 先確認是 Project bug、外部 source profile 差異、輸入版本差異或原 spec 錯誤。
3. 不得先改 expected output 讓 CI 變綠。
4. 若確認採用新規則，必須新 rule/profile version，保留舊版 provenance。

---

## 十五、Implementation workflow 約束

本 spec 核准後才可進 implementation plan。

正式開發仍採：

```text
design branch
↓
approved spec
↓
implementation plan
↓
feature branch
↓
每個 flow：RED → GREEN → verification evidence
↓
full review
↓
exact-head final validation
↓
feature → design PR
↓
squash merge
↓
design post-merge regression
↓
design → main PR
↓
main post-merge regression
```

### 15.1 TDD hard gate

每一個可獨立驗證 flow：

1. 先寫 test。
2. 證明 RED 確實因缺功能／錯誤行為而失敗。
3. 才寫最小 implementation。
4. GREEN 後再進下一 flow。

不得先寫完整 implementation 再補測試。

### 15.2 No silent test rewrite

若現有 test / qualification 因新 code 失敗：

- 先查 root cause。
- 只有正式 design/spec 或已證實舊 expected 錯誤時，才能修改 expected。
- 修改 expected 必須有 review note 與來源證據。

---

## 十六、Acceptance Criteria

Phase 2A implementation 只有同時滿足以下條件才可視為正式完成：

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
MAIN_POST_MERGE_PASS
```

最終 capability target：

```text
ziwei.transformations = implemented / stable / on_demand
ziwei.flying           = implemented / stable / on_demand
```

細運四化、細運飛化與流曜仍保持 planned。

---

## 十七、後續 Phase 邊界

Phase 2A 完成後才進：

### Phase 2B：Ziwei Fine Cycle Stem Resolver v1

負責：

- 流月天干 policy/profile。
- 流日天干 policy/profile。
- 流時天干 policy/profile。
- 閏月 reference identity。
- 紫微 23:00 日界 policy。
- 將合法 stem 結果送入 Phase 2A Transformation Core。

Phase 2B 不應重新實作四化表或 Flying Core。

### Phase 2C：Ziwei Flowing Stars v1

獨立負責：

- 流曜規則 profile。
- 各流曜起法與 scope。
- school/profile versioning。
- moving-star qualification。

Phase 2C 不應把流曜規則綁入 Transformation Core。

---

## 十八、設計決策摘要

v1 正式鎖定：

1. 採方案 B：四化核心 → 飛化核心 → Composition → 細運 stem resolver → 流曜，分層開發。
2. `metaphysics-lab-common-v1` 是版本化 profile，不宣稱紫微唯一標準。
3. Transformation Core 不知道時間 scope。
4. Flying Core 不重新安星。
5. 第一版 Flying target 只使用已校驗本命星曜位置。
6. `PalaceStemSource` 與 `CycleStemSource` 必須分型。
7. 自化是 edge relation 的衍生結果，不是星曜永久屬性。
8. 底層保存 `same_palace / opposite_palace_incoming / normal`；`↑/↓` 屬 presentation profile。
9. Cycle source 不進自化 classifier。
10. 本命十二宮形成 exactly 48-edge NatalFlyingGraph。
11. 大限／流年各自形成 4-edge CycleTransformationLayer。
12. 不同時間層共存、不覆寫；同層矛盾 fail closed。
13. Small limit v1 只作 context，不自行推小限四化。
14. Composite View 只供查詢，不做吉凶、共振或權重判定。
15. monthly/daily/hourly transformation availability 必須明確 unavailable。
16. Private Astralium 只作 external qualification，不 commit raw chart。
17. Stable promotion 需要 40 項四化、144 宮位幾何、80 條 private external flying edge、獨立公開 profile、全 repo 與 main post-merge 全部通過。
18. 任一 mismatch 不得硬升 stable。
19. v1 stable 後仍先保持 `on_demand`，不在本 phase 改 default analysis routing。
20. Phase 2A 不改 Calendar Resolver、Bazi、Qimen、流曜或紫微細運 stem policy。
