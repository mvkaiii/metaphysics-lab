# Ziwei Fine Cycle Stem Resolver v1 設計規格

- 日期：2026-08-21
- Branch：`design/ziwei-fine-cycle-stem-resolver`
- 狀態：Design spec，等待使用者 final review；尚未進入 implementation plan
- 分類：Architectural
- 階段：Phase 2B
- Base：Metaphysics Lab v1.2.0 release commit `e6ac041a16117402207e086b875904b41b674e59`
- 前置依賴：Calendar Resolver v1、Ziwei month/day/hour palace positioning、Transformation Core v1、Flying Core v1 均已在 `main`

---

## 一、目的

Phase 2B 的目的，是正式解決紫微細運目前缺少的「流月／流日／流時天干來源」，讓既有 stable Transformation/Flying Core 可以在不混用八字 policy、不依賴 runtime 第三方 JS 套件、且保留來源與版本的前提下，建立：

```text
CalendarContext
    ↓
Ziwei Fine Cycle Stem Resolver
    ├─ monthly stem / branch
    ├─ daily stem / branch
    └─ hourly stem / branch
            ↓
Transformation Core v1
            ↓
Flying Core v1
            ↓
monthly / daily / hourly CycleTransformationLayer
```

核心原則：

> Calendar Resolver 只提供 neutral civil/calendar facts。
>
> 紫微細運 Resolver 自己負責紫微的月份與日界 profile。
>
> 八字與紫微可以使用相同曆法數學，但不得共享未標示的命理 policy。
>
> 公開第三方來源只作 qualification，不成為 runtime dependency。
>
> Fine-cycle stem 先 Experimental / On-demand；不得因可執行就自動遍歷所有月份、日期或時辰。

---

## 二、Phase 2B 前置 Gate：正式規則來源 reconciliation

目前 `main` 的 executable capability 狀態已進入 v1.2.0，但部分 `core/` 規則文件仍保留 Phase 2A 前的舊敘述，例如：

- 將 Calendar / Input Resolver 寫成尚未實作。
- 將已完成的 Transformation/Flying Core 寫成 planned。
- 使用 `Project 紫微流月`、`Project Bazi Calendar Engine` 等已淘汰 capability 名稱。
- 流月／流日／流時規則文件對彼此 capability 狀態不同步。

Phase 2B implementation 的 Task 0 必須先同步正式規則來源，再開始 production code。Task 0 只做「現況 reconciliation」，不得偷偷啟用 fine-cycle 四化／飛化。

最低 Gate：

```text
RULE_SOURCE_RECONCILIATION_PASS
```

若規則文件與 capability registry 仍矛盾，Phase 2B 停止，不把問題帶進 resolver。

---

## 三、設計決策

### 3.1 採獨立 Ziwei resolver，不直接重用 Bazi engine

不採：

```text
engine.bazi.calendar → 紫微流月/流日/流時天干
```

原因：

- 八字流月採節氣月；紫微既有流月定位採農曆月。
- 八字已有 23:00 early-Zi day rollover policy。
- 直接呼叫 Bazi API 會把八字命理語意滲入紫微。

Phase 2B 可重用純 calendrical / sexagenary 數學，但 policy 必須由 Ziwei profile 明確套用。

### 3.2 不把 iztro / lunar-lite 變成 runtime dependency

公開 qualification 固定參考：

- `SylarLong/iztro`：commit `814b77e6371e1050cac31bbf674db3c3138fcfde`，package v2.6.0。
- `SylarLong/lunar-lite`：revision `1d104fffa31609e9f112898cc57545827e8d57ae`，package v0.2.8。

兩者用於：

- 規則交叉驗證。
- 固定 public vectors。
- late-Zi / month-divide 行為比對。

正式 Python engine 不 import Node/npm package，也不在 runtime 呼叫外部服務。

### 3.3 月、日、時 Resolver 與四化／飛化 orchestration 分離

預期模組：

```text
engine/calendar/sexagenary.py       # 純 calendrical sexagenary helper；不套八字/紫微日界
engine/ziwei/fine_cycle_stems.py    # CalendarContext + Ziwei profile → resolved month/day/hour stems
engine/ziwei/fine_cycle.py          # resolved stem → Transformation/Flying/Composition thin orchestration
```

不得把四化表複製進 `fine_cycle_stems.py`，也不得把 date calculation 塞進 `transformations.py`。

---

## 四、Scope

### 4.1 Phase 2B v1 必須實作

1. Ziwei fine-cycle rule profile 與版本。
2. `ResolvedCycleStem` immutable model。
3. 流月干支 resolver。
4. 流日干支 resolver。
5. 流時干支 resolver。
6. late-Zi day-boundary profile。
7. CalendarContext validation / double-boundary protection。
8. stable reference identity for monthly/daily/hourly layers。
9. fine-cycle stem → existing Transformation Core v1 orchestration。
10. fine-cycle TransformationSet → existing Flying Core v1 orchestration。
11. Composition 支援 `monthly / daily / hourly` scopes。
12. capability lifecycle：fine-cycle stems、fine-cycle transformations、fine-cycle flying 全部第一版 `implemented / experimental / on_demand`。
13. public qualification、negative cases、full regression、privacy/scope gates。
14. private Astralium fine-cycle qualification 明確記為 pending，不偽造 PASS。

### 4.2 Phase 2B v1 明確不實作

- 流曜／流魁／流鉞／流昌／流曲／流羊／流陀／流馬等 moving stars。
- 新的本命安星算法。
- 重排本命星曜位置。
- 自動選擇哪個流派 profile「比較準」。
- 吉凶 scoring / resonance / final state。
- 自動遍歷全年每日每時。
- 奇門遁甲。
- AI 命理解讀。
- 將 iztro、lunar-lite 或 Astralium 宣稱為唯一紫微標準。
- 因 Phase 2B 完成而把既有流日／流時 palace positioning 自動升 Stable。

Phase 2C 才處理 flowing stars。

---

## 五、資料責任與模型

### 5.1 CalendarContext 是唯一 civil/calendar entry point

Fine-cycle resolver 不接受散落的：

```text
2026-09-18
23:30
農曆八月初八
子時
```

作為彼此無關的 raw arguments。

正式 orchestration 入口接受已由 Calendar Resolver 建立的 `CalendarContext`，至少使用：

- `normalized_time.local_datetime`
- `normalized_time.gregorian_date`
- `normalized_time.hour_branch`
- `lunar.year / month / day / is_leap_month`
- calendar validation metadata
- `policies.metaphysics_day_boundary_applied`

如果 Calendar Resolver 已先套用 metaphysics day boundary，Fine-cycle resolver 必須 fail closed，避免 double rollover。

### 5.2 ResolvedCycleStem

預期模型：

```text
ResolvedCycleStem
├─ scope                    # monthly | daily | hourly
├─ reference                # stable layer reference
├─ heavenly_stem
├─ earthly_branch
├─ profile_id
├─ rule_version
├─ civil_date
├─ effective_date           # day/hour 使用；month 可等於 civil date
├─ hour_branch              # hourly 才有
├─ calendar_validation_status
└─ provenance
```

`ResolvedCycleStem` 不含 chart identity；它是「日期／時間規則輸出」，不是某命主的盤面資料。

後續 `fine_cycle.py` 才把它與 `ChartIdentity` 組成既有 `CycleStemSource`。

### 5.3 FineCycleStemProfile

第一個正式 profile：

```text
profile_id = ziwei-fine-cycle-lunar-late-zi-v1
rule_version = 1.0-exp
month_basis = lunar_month
leap_month_policy = split_after_day_15
lunar_year_basis = lunar_year
ziwei_day_boundary = late_zi_forward-v1
hour_stem_basis = effective_ziwei_day_stem
```

名稱刻意包含 boundary policy；未來若新增 midnight-only 或其他流派，不覆寫 v1。

---

## 六、流月干支規則

### 6.1 年干來源

流月五虎遁使用 `CalendarContext.lunar.year` 所屬農曆年的天干，不使用八字立春流年干。

十天干索引：

```text
甲0 乙1 丙2 丁3 戊4 己5 庚6 辛7 壬8 癸9
```

農曆年干：

```text
year_stem_index = (lunar_year - 4) mod 10
```

### 6.2 五虎遁

正月寅月起干：

```text
甲己 → 丙
乙庚 → 戊
丙辛 → 庚
丁壬 → 壬
戊癸 → 甲
```

可用固定表，不以模糊文字規則在 runtime 推測。

### 6.3 月份邊界

流月 stem 與既有 Ziwei flow-month palace positioning 採同一月份語意：

- 一般月份：農曆初一換月。
- 閏月初一至十五：仍視為原月。
- 閏月十六日起：進入下一 effective month。

定義：

```text
effective_month_ordinal
= lunar_month + (1 if is_leap_month and lunar_day >= 16 else 0)
```

`effective_month_ordinal` 可為 1..13。

月干：

```text
month_stem_index
= (first_month_stem_index + effective_month_ordinal - 1) mod 10
```

月支：

```text
寅、卯、辰、巳、午、未、申、酉、戌、亥、子、丑
```

以 `(effective_month_ordinal - 1) mod 12` 循環。

### 6.4 閏十二月後半

若 `effective_month_ordinal = 13`：

- 月支循環回寅。
- 月干繼續向前一位，不先把 ordinal 重設成 1。

這能保持月干連續性，也等價於跨入下一輪寅月 stem sequence。

由於公開 upstream 對「閏十二月後半」未提供足夠固定 test vector，本 edge case 第一版必須：

- 有 synthetic invariant tests。
- 保留 `experimental`。
- qualification 報告單獨標示 public evidence coverage，不得寫成 external PASS if upstream 未覆蓋。

### 6.5 23:00 不提前切換流月

`late_zi_forward-v1` 只作用於流日／流時 stem。

即使 civil time 是 23:30，流月仍使用 CalendarContext 當下的農曆月／日，不因日干提前進一天而提前換月。

這是刻意把：

```text
month boundary
```

與：

```text
day-stem boundary
```

分離，避免月底 23:00 產生未定義的隱性跨月。

---

## 七、流日干支規則

### 7.1 Gregorian date → sexagenary day

Phase 2B 建立純 calendrical helper：

```text
Gregorian date
→ Julian Day Number
→ sexagenary day index
```

其數學結果應與現有 Project Bazi JDN 基線在「相同 effective Gregorian date」時一致，但 Ziwei 不 import Bazi engine，也不繼承 Bazi boundary policy。

固定 sexagenary offset 必須以 regression vectors 鎖定，不接受 runtime heuristic。

### 7.2 late_zi_forward-v1

第一版 Ziwei day-boundary profile：

```text
00:00–22:59 → effective_date = civil gregorian date
23:00–23:59 → effective_date = civil gregorian date + 1 day
```

白話：23 點晚子時開始，日干支進到下一日；00 點之後 civil date 本身已是下一天，不再額外 +1。

此 profile 名稱與規則必須出現在 provenance，不得只輸出「子時換日」。

### 7.3 Calendar Resolver 不被修改成紫微專用

Calendar Resolver 仍維持：

```text
civil date at midnight
metaphysics_day_boundary_applied = false
```

Fine-cycle resolver 在自己的 profile 層套用 23:00 policy。

若輸入 context：

```text
metaphysics_day_boundary_applied = true
```

必須拒絕，error code：

```text
calendar_boundary_already_applied
```

---

## 八、流時干支規則

### 8.1 時支來源

時支唯一來源：

```text
CalendarContext.normalized_time.hour_branch
```

Fine-cycle resolver 不自行重新解析 `23:30`、`下午兩點` 等民用文字。

### 8.2 五鼠遁

以已套用 `late_zi_forward-v1` 後的 effective day stem 起子時：

```text
甲己日 → 甲子
乙庚日 → 丙子
丙辛日 → 戊子
丁壬日 → 庚子
戊癸日 → 壬子
```

之後每一時支天干順行一位。

公式可固定為 lookup + branch offset；不得自行從 Bazi hour object 取值。

### 8.3 late-Zi consistency

在 23:00–23:59：

- day stem 使用下一 effective date。
- hour branch 為子。
- hour stem 必須以「下一 effective date 的 day stem」起五鼠遁。

因此 daily / hourly 不允許一個用舊日干、一個用新日干。

此 coherence 必須是 model/orchestration invariant，而非只靠 caller 約定。

---

## 九、Stable reference identity

為避免同一 scope last-write-wins 或不同 boundary profile 混用，reference 必須可重現。

### 9.1 Monthly

建議：

```text
lunar:YYYY-MM
lunar:YYYY-LMM-A     # 閏月初一至十五
lunar:YYYY-LMM-B     # 閏月十六日起
```

reference 保留「實際農曆 segment」，effective month 另存在 resolved metadata；不能只把閏月後半改名成下一月，否則來源資訊會消失。

### 9.2 Daily

```text
ziwei-day:YYYY-MM-DD@late_zi_forward-v1
```

日期為 `effective_date`。

### 9.3 Hourly

```text
ziwei-hour:YYYY-MM-DD:<branch>@late_zi_forward-v1
```

例如：

```text
ziwei-hour:2026-08-22:子@late_zi_forward-v1
```

23:30 on 2026-08-21 與 00:30 on 2026-08-22 在此 profile 下可落到同一 effective day + 子時 layer，屬預期行為。

---

## 十、Error Contract 與 fail-closed 規則

新增 `ZiweiFineCycleError(code, message, details=None)`，不改寫既有 Phase 2A error contract。

至少固定：

```text
invalid_fine_cycle_scope
invalid_fine_cycle_profile
calendar_context_unusable
calendar_boundary_already_applied
fine_cycle_stem_mismatch
fine_cycle_reference_conflict
```

規則：

- Calendar `boundary_conflict` → fail closed。
- `metaphysics_day_boundary_applied = true` → fail closed。
- 不明 profile → fail closed，沒有 silent fallback。
- downstream source stem 與 resolved stem 不一致 → fail closed。
- layer scope / reference / profile 不一致 → fail closed。
- 同 identity 不同內容 → `layer_conflict`，沿用 Phase 2A conflict semantics。

`boundary_caution` / `out_of_validated_range` 可產生結果，但 validation / provenance 必須保留，不能靜默標成 fully validated。

---

## 十一、Transformation / Flying Integration

### 11.1 不新增 month_transform/day_transform/hour_transform 規則表

Fine-cycle integration 必須重用：

```text
resolve_transformations(heavenly_stem, profile_id)
fly_transformations(...)
build_cycle_layer(...)
```

Phase 2B 只補足合法 `CycleStemSource`。

### 11.2 新 orchestration

`engine/ziwei/fine_cycle.py` 只做：

```text
ResolvedCycleStem
+ ChartIdentity
+ StarLocationIndex
+ Transformation profile
→ CycleTransformationLayer
```

流程：

1. 將 resolution 包成 `CycleStemSource`。
2. 呼叫 Transformation Core。
3. 呼叫 Flying Core。
4. 呼叫 Composition builder。
5. 驗證 scope / reference / stem / profile coherence。

不得在 orchestration 重新算干支或四化。

### 11.3 Composition scopes

`SUPPORTED_SCOPES` 從：

```text
birth_year / decadal / yearly
```

正式擴充：

```text
birth_year / decadal / yearly / monthly / daily / hourly
```

fine-cycle layer 必須保留與 higher layers 同樣的 duplicate/conflict protections。

`availability()` 更新後：

- monthly/daily/hourly transformations = available when matching resolved stem exists。
- 若沒有 resolution，不得自行猜 stem。

---

## 十二、Capability Lifecycle

新增／調整：

```text
ziwei.flow_month_stem
ziwei.flow_day_stem
ziwei.flow_hour_stem
```

Phase 2B v1：

```text
implementation = implemented
maturity = experimental
routing = on_demand
rule_version = 1.0-exp
```

既有：

```text
ziwei.flow_month_transformations
ziwei.flow_day_transformations
ziwei.flow_hour_transformations
ziwei.flow_month_flying
ziwei.flow_day_flying
ziwei.flow_hour_flying
```

由 `planned` 升為：

```text
implemented / experimental / on_demand
```

但：

```text
ziwei.flowing_stars
```

仍維持 `planned / on_demand`。

不得因 fine-cycle transformations/flying 實作就改成 default routing。

---

## 十三、Public Qualification

### 13.1 lunar-lite pinned source

固定來源：

```text
SylarLong/lunar-lite
revision 1d104fffa31609e9f112898cc57545827e8d57ae
package 0.2.8
```

其公開 `ganzhi.ts` 提供：

- 五虎遁表。
- `month = normal` 時農曆月起月干支。
- 閏月後半 `fixLeap`。
- exact day stem/branch。
- time stem/branch。

其 upstream `ganzhi.test.ts` 提供可固定的日／時與 month-divide vectors，包括 late-Zi 的 `timeIndex=12` 案例。

### 13.2 iztro integration reference

固定來源：

```text
SylarLong/iztro
commit 814b77e6371e1050cac31bbf674db3c3138fcfde
package 2.6.0
```

該版本在 Horoscope 中直接以 yearly/monthly/daily/hourly stems 產生各層 mutagen，證明「fine-cycle stem → 四化」是其可重現 integration 行為。

### 13.3 Qualification 方法

不得要求 production runtime 安裝 Node。

建議 qualification artifact：

```text
qualification/ziwei/phase2b/public-lunar-lite-1d104fff.json
qualification/ziwei/phase2b/public-iztro-814b77e6.json
```

內容只保存：

- source revision / package version
- test vector input
- expected GanZhi / transformation
- comparison result
- source digest / evidence metadata

公開 qualification 至少覆蓋：

- 五種年干 group 的月份起干。
- 一般農曆月。
- 閏月前半／後半。
- civil midnight 前後。
- 22:59 / 23:00 / 23:59 / 00:00 boundary。
- late-Zi day/hour coherence。
- 不同 hour branches。
- fine-cycle stem → 4 transformations。
- fine-cycle flying → 4 edges。

若 upstream 沒有某 edge（例如閏十二月後半）的獨立 expected vector，報告必須標示 `not externally covered`，不能用 Project synthetic test 冒充 external qualification。

---

## 十四、Private Astralium Qualification

目前 Project 私有 Astralium 基礎資料沒有正式提供流月／流日／流時細運天干與相應四化／飛化完整 payload。

因此 Phase 2B v1：

```text
Astralium fine-cycle qualification = pending
```

允許：

- 保存「尚無足夠 private evidence」的 aggregate summary。
- 未來使用者提供進階附錄後再建立 local-only private normalized input。
- repo 只 commit aggregate result / digest，不 commit raw chart。

禁止：

- 從既有 Astralium 年層資料反推 fine-cycle expected values，再宣稱 private PASS。
- 因 public iztro/lunar-lite PASS 就寫成 Astralium PASS。

最低 marker：

```text
ASTRALIUM_FINE_CYCLE_PENDING
PRIVACY_PASS
```

---

## 十五、Testing Strategy

### 15.1 Unit invariants

- immutable models。
- invalid scope/profile fail closed。
- no silent fallback。
- lunar year stem 60-year cycle invariants。
- 五虎遁 10 stems × 12 months。
- leap split day 15/16 boundary。
- JDN sexagenary day cycle consecutive dates +1。
- 22:59 / 23:00 boundary。
- 五鼠遁 10 day stems × 12 branches。
- late-Zi daily/hourly same effective date stem coherence。

### 15.2 Integration

- CalendarContext → month stem。
- CalendarContext → day stem。
- CalendarContext → hour stem。
- resolved stem → exactly 4 transformations。
- transformations → exactly 4 flying edges。
- monthly/daily/hourly layers coexist with birth_year/decadal/yearly without overwrite。
- duplicate/conflicting layer identity fail closed。
- chart mismatch fail closed。

### 15.3 Regression

每個 Gate 都必須重跑：

- Phase 2B internal tests。
- all Ziwei tests。
- Calendar regression。
- Bazi regression。
- full repository regression。
- Python supported-version syntax check。

Phase 2B 不得改變既有 Bazi outputs。

---

## 十六、Acceptance Markers

implementation plan 必須安排可重現 Gate，至少包含：

```text
RULE_SOURCE_RECONCILIATION_PASS
FINE_CYCLE_MODEL_INVARIANTS_PASS
MONTH_STEM_INVARIANTS_PASS
LEAP_MONTH_BOUNDARY_PASS
DAY_STEM_BOUNDARY_PASS
HOUR_STEM_INVARIANTS_PASS
LATE_ZI_COHERENCE_PASS
CALENDAR_BOUNDARY_DOUBLE_APPLY_REJECTED
FINE_CYCLE_TRANSFORMATIONS_PASS
FINE_CYCLE_FLYING_PASS
FINE_CYCLE_COMPOSITION_PASS
FINE_CYCLE_NEGATIVE_CASES_PASS
PUBLIC_LUNAR_LITE_QUALIFICATION_PASS
PUBLIC_IZTRO_INTEGRATION_PASS
ASTRALIUM_FINE_CYCLE_PENDING
CAPABILITY_EXPERIMENTAL_ON_DEMAND_PASS
ZIWEI_REGRESSION_PASS
CALENDAR_REGRESSION_PASS
BAZI_REGRESSION_PASS
FULL_REPO_PASS
SCOPE_PASS
PRIVACY_PASS
```

不得在對應 assertion / command 未成功時先印 marker。

---

## 十七、預期檔案邊界

Phase 2B implementation 預期主要新增／修改：

```text
core/命理分析作業規範.md
core/命理推導計算規則.md
core/核心提示詞.md
core/紫微流月推導規則.md
core/紫微流日推導規則.md
core/紫微流時推導規則.md

engine/calendar/sexagenary.py
engine/ziwei/errors.py
engine/ziwei/models.py
engine/ziwei/capabilities.py
engine/ziwei/fine_cycle_stems.py
engine/ziwei/fine_cycle.py
engine/ziwei/composition.py

qualification/ziwei/phase2b/*
tools/qualify_ziwei_phase2b_public.py
tests/test_ziwei_fine_cycle_stems.py
tests/test_ziwei_fine_cycle_integration.py
tests/test_ziwei_phase2b_capabilities.py
tests/test_ziwei_phase2b_qualification.py
```

可能需要 README/VERSION/CHANGELOG/架構文件同步，但只能在 capability 實際完成並通過 promotion gate 後更新，不提前宣稱 implemented。

以下預設不修改：

```text
engine/bazi/*
engine/ziwei/month.py
engine/ziwei/day.py
engine/ziwei/hour.py
engine/ziwei/transformation_profiles.py
```

若 implementation 發現必須修改上述檔案，需先說明理由並升級 scope review，不得順手改。

---

## 十八、Release / Promotion Policy

Phase 2B 第一版即使所有 internal + public qualification PASS，fine-cycle stems / transformations / flying 仍先維持：

```text
experimental / on_demand
```

升 Stable 至少另需：

- 更多公開獨立來源或原始排盤依據。
- 跨年份、閏月、late-Zi 邊界案例。
- private Astralium 或另一個可信排盤來源 fine-cycle output qualification。
- 問事追蹤與可重現 Issue evidence。

不能因單一命盤吻合或單一事件發生就升 Stable。

---

## 十九、Implementation Gate

本文件通過使用者 review 後，下一步才可呼叫 `writing-plans` 產出 Phase 2B implementation plan。

在 implementation plan 被使用者再次明確核准前：

- 不新增 production code。
- 不 promotion capabilities。
- 不修改 main。
- 不建立 fine-cycle 四化／飛化結果作為正式 Project 能力。

流程固定：

```text
Design spec approval
→ Implementation plan
→ User approval
→ RED/GREEN implementation
→ Qualification
→ Exact-head final validation
→ feature→design approval
→ design post-merge validation
→ design→main approval
→ main post-merge validation
```
