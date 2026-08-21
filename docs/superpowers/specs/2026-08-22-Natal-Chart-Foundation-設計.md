# Natal Chart Foundation v1 設計規格

- 日期：2026-08-22
- Branch：`design/natal-chart-foundation`
- 狀態：Design spec，等待使用者 final review；尚未進入 implementation plan
- 分類：Architectural
- 階段：Phase 2C0
- Base：`main` commit `dcb70947f53451c0a4760dc6231f95b901ef495e`
- 後續：原 Phase 2C `ziwei.flowing_stars` 延後到本 Foundation 穩定後再執行

---

## 一、目的

Phase 2C0 的目的，是讓 Metaphysics Lab 不再要求使用者先懂 Astralium 或自行準備完整八字／紫微命盤。

一般使用者只要提供：

```text
性別
＋陽曆出生年月日
＋出生時間
＋出生地
```

Project 就能完成：

```text
Birth Input Resolution
→ Location Resolution
→ Precision Gate
→ Calendar Resolver
→ Birth Time Views
→ Bazi Natal Builder
→ Ziwei Natal Builder
→ Normalized Natal Model
→ Cross-check / Qualification
→ Markdown Data Pack Export
```

同時保留既有外部盤面入口：

```text
Astralium PDF / MD / structured chart
→ External Chart Import
→ Normalized Natal Model
```

兩條路最後必須收斂到同一個標準化命盤模型，下游本命分析、Phase 2A、Phase 2B 與未來 Phase 2C 不維護兩套邏輯。

核心產品原則：

> External chart is optional; sufficiently precise birth data is enough to build a Project-native chart.
>
> Precision must be earned by input.
>
> Complexity belongs in provenance, not in the default user experience.
>
> Differences must be material before they become user-facing.

---

## 二、資料分類新增：Project 原生盤面

現行七種資料類型不足以精確區分「Project 從出生資料建立的本命盤」與「由本命盤再推導出的流月／流日／流時」。Phase 2C0 新增：

```text
Project 原生盤面
```

定義：

- 由 Metaphysics Lab 固定、可重現、版本化的 Natal Engine 從出生資料建立。
- 不得冒充 Astralium 或其他第三方直接輸出。
- 必須附 engine、profile、rule version、provider、qualification、provenance。

資料層級因此改為：

1. 原始盤面事實
2. 已校驗資料
3. Project 原生盤面
4. Project 推導盤面
5. 已驗證事件
6. 命理推論
7. 研究假說
8. 當次現實背景

其中：

- Astralium 直接輸出仍屬「原始盤面事實」。
- Project Natal Engine 建出的本命四柱／十二宮／星曜等屬「Project 原生盤面」。
- 本命之後的流月／流日／流時等仍屬「Project 推導盤面」。

---

## 三、正式輸入模式

### 3.1 Mode A：出生資料自動排盤

使用者最低輸入：

```text
sex
birth_date
birth_time
birth_place
```

一般自然語言可以是：

```text
男，1984年3月13日晚上7:20，台北市出生
```

LLM／上游 Input Resolver 負責抽取欄位，不直接進 deterministic chart engine。

### 3.2 Mode B：已知四柱匯入

例如：

```text
甲子 丁卯 丙午 戊戌
```

此模式可建立八字 external/imported natal input，但不能宣稱已具備完整紫微排盤所需 civil datetime identity。

若要建立紫微本命盤，必須再補：

```text
實際出生年月日
出生時間
出生地
性別
```

不得由八個干支字自由反推唯一出生 datetime。

### 3.3 Mode C：Astralium／其他外部命盤匯入

若偵測到外部命盤：

1. 先解析來源直接提供的欄位。
2. 保留來源名稱、版本／日期、原始分類。
3. 若出生資料也可取得，允許 Project 重算做 cross-check。
4. 外部盤不因 Project 重算而被覆寫。

### 3.4 缺欄位提示

系統不得要求使用者重填已知資料，只提示真正缺少且阻塞 target capability 的欄位。

例如缺少性別與時間：

```text
還需要：性別、出生時間。
若時間不確定，可提供大約時段或已知時辰；Project 會先判斷可達精度。
```

性別不得猜測。性別不足時，可建立不受性別影響的部分靜態欄位，但不得宣稱完整大運／大限已建立。

---

## 四、Input Resolution / Precision Gate

### 4.1 不補假值

出生時間為：

```text
晚上
大約七八點
媽媽說可能戌時
```

時，不得自行轉成任意精確分鐘。

只允許：

```text
ask
keep_candidates
downgrade
```

沿用 `engine/calendar/precision.py` 的 fail-closed 原則。

### 4.2 候選盤

若不精確時間跨越會改變命盤的邊界，例如：

```text
20:00–22:00
```

跨越戌／亥時，應保留候選 input／candidate chart，而非選中間值。

若模糊範圍仍落在同一有效時辰，則可在 provenance 中記錄 input precision，並繼續不依賴精確分鐘的 capability。

### 4.3 Target capability 驅動精度

- 只做部分八字靜態分析：依所需欄位判定最低精度。
- 建完整 Bazi Natal：需要能唯一決定四柱與性別相關運限。
- 建完整 Ziwei Natal：需要能唯一決定紫微有效時辰與性別相關大限。
- 若真太陽時修正可能跨時辰／跨日，必須視為 material boundary，不可忽略。

---

## 五、Location Resolver

Calendar Resolver v1 目前刻意不猜 timezone，也不解析自然語言地點。Phase 2C0 新增上游 Location Resolver。

輸入：

```text
birth_place = 台北市, 台灣
```

輸出至少：

```text
canonical_place_name
country / region
latitude
longitude
timezone              # IANA
provider
provider_version / source revision if available
resolution_status
```

規則：

- 使用者不需要自行輸入 latitude / longitude / IANA timezone。
- 底層 Natal Engine 不接受未解析的「台北」、「東京」字串作為最終時間依據。
- 多義地名無法唯一解析時必須 ask／keep candidates，不得靜默猜城市。
- timezone 必須可追溯到 provider／tzdb。
- 歷史出生時間應使用該日期有效的 timezone / DST 規則，不只使用今天的 UTC offset。

Location Resolver 是上游解析能力，不把地點猜測責任塞進 Calendar Resolver。

---

## 六、時間責任分層

### 6.1 原始 civil time 永久保留

至少保存：

```text
reported_civil_time
normalized_civil_time
bazi_effective_time
ziwei_effective_time
```

`reported_civil_time` 不得被真太陽時覆蓋。

### 6.2 Calendar Resolver 仍保持 neutral

Calendar Resolver 只處理：

- structured local civil datetime
- IANA timezone
- historical offset / DST contract
- Gregorian / lunar context
- civil hour branch

仍不負責：

- 真太陽時
- 八字日界
- 紫微日界
- Natal school profile

Phase 2C0 不得為了出生排盤把 Calendar Resolver 改成紫微或八字專用。

### 6.3 Birth Time Views

Natal Foundation 新增時間 view 層：

```text
reported civil
normalized civil
true solar
```

每個 view 都必須有：

```text
profile_id
rule_version
calculation_basis
adjustment_minutes
input longitude
standard meridian / timezone basis
provider/provenance
boundary_effect
```

---

## 七、真太陽時策略

### 7.1 紫微 default qualification target

Ziwei Natal v1 以「真太陽時＝經度校正＋均時差」作為第一個 default-profile qualification target，對齊目前 Astralium 已觀察到的排盤口徑。

紫微 profile 需明文標示：

```text
true_solar_time = enabled
longitude_correction = enabled
equation_of_time = enabled
maturity = experimental initially
qualification_target = Astralium-compatible behavior
```

不得把這個 profile 宣稱成唯一紫微標準。

精確 equation-of-time 算法必須在 capability 可執行前固定成可重現公式並版本化；若公式尚未固定或 qualification 未通過，該 capability 不得假裝 implemented。

### 7.2 八字獨立 profile

八字不得因紫微使用真太陽時，就被迫使用完全相同的 effective-time policy。

Bazi Natal v1 採：

```text
project default view = normalized civil time
existing day-boundary baseline = 23:00
```

並同時計算可比較的 true-solar candidate view 作 qualification。

若兩個 view 得到相同四柱：

```text
EQUIVALENT
```

若真太陽時造成時柱／日柱改變：

```text
TIME_PROFILE_CONFLICT
```

只有 material difference 才主動提示一般使用者。

八字 true-solar candidate 在 external qualification 足夠之前，不自動取代 Project default profile。

---

## 八、Bazi Natal Builder v1 Scope

### 8.1 必須產生

```text
四柱：年、月、日、時
日主
藏干
十神
五行基本資料
大運順逆
起運資訊
大運干支與區間
排盤時間口徑
provenance
validation
```

現有 `engine/bazi/calendar.py` 可作時間／干支 baseline，但 Natal Builder 必須有自己的 schema、profile 與 validation contract，不把「流運 Project 推導盤面」直接冒充「本命 Project 原生盤面」。

### 8.2 v1 不在 Builder 內自動宣稱

```text
身強弱
格局
喜用神
忌神
人生結論
AI吉凶分數
大量神煞
```

上述屬命理模型判定或後續 extension，不與 deterministic natal facts 混在同一層。

---

## 九、Ziwei Natal Builder v1 Scope

### 9.1 出生 basis

必須產生：

```text
原始出生年月日時
出生地 / 經緯度 / timezone
真太陽時
紫微 effective time / hour branch
農曆年月日
出生年干支
profile / rule version
```

### 9.2 本命骨架

必須產生：

```text
命宮
身宮
十二宮名稱／地支
十二宮宮干
五行局
命主
身主
```

### 9.3 星曜 Catalog

v1 不只做十四主星。

正式 star catalog 至少包含：

1. 十四主星完整唯一定位。
2. 所有現有 Transformation Profile 可能化祿／權／科／忌的星曜。
3. v1 明確選定的主要輔曜／煞曜。

大量雜曜可延後 extension。

每顆星至少保存：

```text
star
palace
catalog/profile
brightness if profile defines it
provenance
```

若 Transformation Core 需要的星曜沒有 natal location，則對應四化／飛化 capability 必須 fail closed。

### 9.4 星曜亮度

廟／旺／得／利／平／不／陷等亮度納入 v1 Natal Data，但必須由 versioned brightness profile 提供，不由 LLM 猜。

### 9.5 生年四化與本命飛化

Natal Builder 不複製四化表。

流程：

```text
birth-year stem
→ existing Ziwei Transformation Core v1
→ existing Ziwei Flying Core v1
```

Natal Builder 只提供正確的：

```text
StarLocationIndex
PalaceStemIndex
```

既有 stable Phase 2A 應產生本命：

```text
12 palace stems × 4 transformations = 48 FlyingEdge
```

### 9.6 大限

v1 必須產生：

```text
decadal direction
start basis
age range / reference
palace
palace stem-branch
```

大限四化／飛化仍透過既有 Phase 2A Composition，不在 Natal Builder 內複製 Transformation / Flying 規則。

### 9.7 v1 明確不實作

- 全量雜曜復刻。
- 全套神煞。
- 長生十二神／博士十二神／將前十二神／歲前十二神。
- 當前小限動態狀態與歷年小限列表。
- 歷年流年命宮列表。
- 七年流年快照。
- 流月／流日／流時快照。
- 流曜 moving stars（保留給正式 Phase 2C）。
- AI吉凶分數／格局自動命名／人生結論。

---

## 十、Normalized Natal Model

所有入口最後收斂成同一模型。概念結構：

```text
NatalChart
├─ identity
│  ├─ chart_id
│  ├─ person_label
│  └─ sex
├─ birth
│  ├─ reported_datetime
│  ├─ birthplace
│  ├─ coordinates
│  ├─ timezone
│  └─ calendar_input_kind
├─ time_basis
│  ├─ normalized_civil
│  ├─ true_solar
│  ├─ bazi_effective
│  └─ ziwei_effective
├─ bazi
│  ├─ pillars
│  ├─ hidden_stems
│  ├─ ten_gods
│  └─ decadal_luck
├─ ziwei
│  ├─ lunar_birth
│  ├─ ming_palace
│  ├─ body_palace
│  ├─ five_element_bureau
│  ├─ life_master
│  ├─ body_master
│  ├─ palaces[12]
│  ├─ stars[]
│  ├─ birth_transformations
│  ├─ natal_flying
│  └─ decadal_cycles
└─ validation / provenance
```

所有重要欄位都必須能追到：

```text
value
source_type
source_name
source_version
rule_profile
rule_version
maturity
validation_status
```

---

## 十一、三個內部 View

同一命主可同時存在：

```text
External View
Project View
Resolved View
```

### External View

保存 Astralium 或其他正式外部來源的直接結果。

### Project View

保存 Metaphysics Lab 依出生資料重算結果。

### Resolved View

只負責告訴下游「目前分析採哪個值」，不得刪除或改寫前兩個 view。

範例：

```text
Astralium 命宮 = 巳
Project 命宮 = 午
Resolved status = CONFLICT
selected source = Astralium
reason = project_natal_engine_experimental
```

---

## 十二、Reconciliation 狀態

欄位級比對結果固定為：

```text
MATCH
EQUIVALENT
CONFLICT
NOT_COMPARABLE
```

### MATCH

值相同。

### EQUIVALENT

技術輸出不同，但對 target chart component 無實質差異。例如：

```text
civil 19:20
true solar 19:16
```

兩者皆為戌時，且未改變目標盤面。

### CONFLICT

差異會改變命盤或同一欄位不能同時為真。

### NOT_COMPARABLE

某一來源沒有提供該欄位，不能視為 FAIL。

---

## 十三、Conflict Severity

```text
INFO
CAUTION
BLOCKING
```

### INFO

有技術差異但不改盤，例如校正分鐘不同但時辰不變。

### CAUTION

影響非核心 extension 或不同 profile 顯示，例如部分亮度／輔曜差異。

### BLOCKING

至少包括：

- 四柱不同。
- 出生有效時辰不同。
- 命宮不同。
- 身宮不同。
- 五行局不同。
- 十四主星落宮不同。
- Transformation-required star location 不同。
- 生年四化不同。
- 大運／大限順逆或核心宮位不同。

BLOCKING CONFLICT 不得被靜默吞掉。

---

## 十四、Authority Rule

### 14.1 Project Natal Engine = Experimental 時

只有出生資料：

```text
Project View 可作分析 basis
classification = Project 原生盤面
maturity = experimental
```

若同時有 Astralium：

- MATCH / EQUIVALENT：confidence 提升。
- CONFLICT：Project 結果仍保留，但 Resolved View 預設選用已提供的 Astralium 原始盤面。
- 不得為了 match Astralium 反向修改 Project raw result。

### 14.2 Project Natal Engine = Stable 後

Project 原生盤面可成為 default source，Astralium主要作 cross-check。

即使 stable，若出現 BLOCKING CONFLICT：

- 仍需保留衝突。
- 不得靜默宣稱「已校驗一致」。
- 應觸發診斷：出生資料、地點、timezone、DST、真太陽時、school/profile、provider、algorithm version。

---

## 十五、Capability Registry 建議

第一版新增 capability：

```text
birth.input_resolution
birth.location_resolution
birth.true_solar_time
bazi.natal_chart
ziwei.natal_chart
natal.reconciliation
natal.markdown_export
```

Lifecycle：

- `birth.input_resolution`：implemented 前需有 precision / ambiguity tests。
- `birth.location_resolution`：依 provider 可用性與 qualification 決定 maturity；不得假裝已知地點。
- `birth.true_solar_time`：第一版 experimental，需版本化公式與 boundary tests。
- `bazi.natal_chart`：implemented / experimental / on_demand 起步。
- `ziwei.natal_chart`：implemented / experimental / on_demand 起步。
- `natal.reconciliation`：implemented 後可 stable，但不等於 chart engines stable。
- `natal.markdown_export`：schema 穩定後可 stable。

只有 qualification gate 達標後，`bazi.natal_chart` / `ziwei.natal_chart` 才能升：

```text
implemented / stable / default
```

---

## 十六、Qualification Gate

Project Natal Engine 不因單一命盤 PASS 即升 Stable。

至少覆蓋：

```text
一般非邊界出生時間
時辰邊界
真太陽時跨時辰
真太陽時跨日
23:00附近
節氣交界
農曆閏月
不同出生年天干
男女大運／大限順逆
不同經度
不同timezone
DST地區
歷史timezone
```

### 16.1 Bazi qualification

至少逐項比對：

```text
四柱
日主
藏干
十神
大運順逆
起運
大運干支／區間
```

並單獨記錄：

```text
civil default vs true-solar candidate
```

哪些案例造成 material chart difference。

### 16.2 Ziwei qualification

至少逐項比對：

```text
農曆出生資料
真太陽時
採用時辰
命宮
身宮
五行局
十二宮
十二宮宮干
十四主星
Transformation-required stars
主要輔煞曜
亮度
命主 / 身主
生年四化
本命48條飛化
大限
```

Astralium是主要 private qualification source之一，但不得宣稱為唯一紫微標準。

### 16.3 Public qualification

若可取得固定版本的公開排盤 library／資料集，可作 secondary qualification；正式 Python engine 不應因 qualification 而被迫增加 runtime 第三方服務依賴。

### 16.4 Privacy

延續 Phase 2A／2B：

- 共用 repo 不保存私人 raw birth chart。
- qualification repo artifact 只保存 aggregate summary、case id、digest、pass/fail counts、版本資訊。
- 私人出生時間、地址、命盤全文不得因測試方便進共用 repo。

---

## 十七、Fail-Closed Error Contract

至少定義：

```text
missing_required_birth_field
ambiguous_birth_date
ambiguous_birth_time
ambiguous_birth_place
location_not_resolved
timezone_not_resolved
historical_timezone_unavailable
calendar_resolution_failed
true_solar_profile_unavailable
true_solar_boundary_conflict
bazi_time_profile_conflict
ziwei_time_profile_conflict
incomplete_star_catalog
missing_transformation_star_location
external_project_blocking_conflict
invalid_natal_schema
```

任何 BLOCKING 狀態都不能靠 LLM 自行補值來讓下游跑通。

---

## 十八、Markdown Data Pack Exporter

LLM不負責重新計算命盤，只負責將 validated structured model 轉成標準文件。

預期輸出：

```text
八字_四柱_AI解讀資料包_<date>.md
紫微_基礎資料包_<date>.md
命盤資料校驗紀錄.md
命盤核心摘要.md        # 若 workflow 需要
```

每份 MD 至少包含：

```text
資料來源
資料分類
engine
profile
rule version
出生資料
時間校正摘要
validation / reconciliation status
正式盤面欄位
provenance 摘要
```

一般使用者預設顯示：

```text
命盤建立完成
資料完整度
時間校正是否造成盤面變更
若有外部盤：核心盤面是否一致
```

只有 material conflict 才展開技術細節。

---

## 十九、UX 原則

### 19.1 一般使用者不用選流派 profile

一般模式：

```text
Project使用目前 default profile
```

進階使用者明確要求時，才允許查看／override profile。

### 19.2 不把技術複雜度丟給使用者

不預設詢問：

```text
你要不要真太陽時？
早子還是晚子？
八字與紫微要選哪一派？
```

而是：

- Project自動套目前可執行的default profile。
- 詳細規則留在 provenance。
- 只有不同profile真的改變命盤時，才主動提示。

### 19.3 真正改盤才提示

例如：

```text
19:20 → 19:16，仍為戌時
```

預設只需顯示：

```text
已完成出生地時間校正，未造成時辰變更。
```

若：

```text
19:02 → 18:56，戌時 → 酉時
```

則必須顯示明確 boundary warning，並視 authority / external source 決定 resolved basis。

---

## 二十、Architectural Dependency Graph

```text
Natural-language / file input
        ↓
Birth Input Resolver
        ↓
Precision Gate
        ↓
Location Resolver
        ↓
Calendar Resolver v1
        ↓
Birth Time Views
   ├───────────────┐
   ↓               ↓
Bazi Natal      Ziwei Natal
Builder          Builder
   ↓               ↓
   └──────┬────────┘
          ↓
Normalized Natal Model
          ↓
Reconciliation / Validation
          ↓
Resolved View
          ↓
Markdown Exporter
          ↓
Analysis Orchestration
   ├─ Bazi analysis
   ├─ Ziwei Phase 2A
   ├─ Ziwei Phase 2B
   └─ future Phase 2C Flowing Stars
```

---

## 二十一、預期模組邊界

最終實作計畫可依 repo 現況微調檔名，但責任邊界必須維持：

```text
engine/birth/
├─ models.py
├─ input_resolution.py
├─ location.py
├─ time_views.py
└─ reconciliation.py

engine/bazi/
├─ natal_models.py
└─ natal.py

engine/ziwei/
├─ natal_models.py
├─ natal_profiles.py
├─ natal.py
└─ star_catalog.py

engine/natal/
└─ export.py
```

原則：

- `engine/calendar/` 不吸收真太陽時與 school policy。
- `engine/birth/` 不知道命宮、十神等命理規則。
- `engine/bazi/natal.py` 不 import Ziwei profile。
- `engine/ziwei/natal.py` 不 import Bazi day-boundary policy。
- Transformation/Flying 仍 reuse Phase 2A stable core。
- LLM 不作 deterministic chart math。

---

## 二十二、Acceptance Criteria

Phase 2C0 v1 只有在以下全部成立時才算功能完成：

1. 使用者只提供完整出生資料即可建立 Bazi Project-native natal chart。
2. 使用者只提供完整出生資料即可建立 Ziwei Project-native natal chart。
3. 使用者提供模糊資料時，Precision Gate 不補假值。
4. Location Resolver 能提供可追溯的 coordinates + historical timezone，或 fail closed。
5. `reported_civil_time` 永遠保留。
6. Ziwei true-solar profile 為 versioned、可重現並通過既定 qualification gate。
7. Bazi default 與 true-solar candidate 差異可被偵測，不靜默改柱。
8. Bazi v1 scope 可產四柱、藏干、十神與大運核心資料。
9. Ziwei v1 scope 可產命身宮、十二宮、宮干、五行局、核心星曜／亮度、命主身主、生年四化、本命48飛化與大限。
10. Astralium匯入與Project重算可同時保留，不互相覆寫。
11. reconciliation 可輸出 MATCH / EQUIVALENT / CONFLICT / NOT_COMPARABLE。
12. BLOCKING CONFLICT 不被靜默吞掉。
13. Experimental期間外部 Astralium 與Project BLOCKING衝突時，Resolved View 預設保留外部盤作分析basis。
14. MD Exporter只從 structured validated model 產文件，不重新排盤。
15. 共用repo不保存私人raw chart。
16. Phase 2A / 2B regression 必須全綠。
17. `ziwei.flowing_stars` 仍保持 planned，2C0不得偷做 Phase 2C。

---

## 二十三、Phase 2C0 後的 Roadmap

只有 Phase 2C0 通過正式 validation / promotion gate 後，才回到原本：

```text
Phase 2C
Ziwei Flowing Stars
```

Phase 2C 可以直接依賴：

```text
Normalized Natal Model
StarLocationIndex
PalaceStemIndex
Phase 2A Transformation/Flying Core
Phase 2B Fine Cycle layers
```

因此 future user flow 最終變成：

```text
「我是1990年5月6日15:20，高雄出生，女生，幫我看2027工作。」
        ↓
Project先自動建立／確認命盤
        ↓
再進正式流年問事流程
```

不再要求一般使用者先去第三方網站排盤。
