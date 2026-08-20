# Metaphysics Lab v1.2 架構設計

## 一、目的

v1.2 的核心目標是把八字、紫微與跨系統驗證拆成清楚、可獨立測試的模組，並建立「能力存在、成熟度、預設調度」彼此分離的執行模型。

本版架構目標：

- 八字與紫微引擎分離。
- 紫微流月／流日／流時拆成同一 Ziwei Engine 下的不同 timing modules。
- 紫微四化、流曜與細層飛化形成可獨立驗證的 capability modules。
- 建立獨立 Cross-System Validation 層。
- 保留 `project_*.py` 作相容入口。
- 為後續 Skill 封裝保留清楚模組邊界。
- 細部能力完成實作與驗證後可按需調用，但不因能力存在就每次自動執行。

重要原則：

> 「已實作」不等於「預設執行」；「Experimental」也不等於「不能執行」。

紫微細部能力必須先有可重現算法、測試與外部校驗，才能成為可調用能力。平常是否執行，由問題精度與 router 決定。

---

## 二、架構原則

1. 八字與紫微使用不同曆法與推導規則，不共用業務邏輯。
2. 各 timing module 只處理自己的時間層級。
3. 共用基礎邏輯集中，不在 month/day/hour 之間重複。
4. 紫微四化、流曜、飛化與 timing modules 分離，避免不同規則互相綁死。
5. Cross-System Validation 只比較兩套系統已完成的輸出，不回頭修改任何單一引擎結果。
6. 問題精度決定需要載入的模組，不因存在更細時間層級就每次全部執行。
7. 能力狀態至少分成：是否已實作、驗證成熟度、預設調度方式。
8. GitHub 繼續作為正式核心與版本來源；ChatGPT Project／Skill 只負責引用、調度與執行。
9. 人類友善時間輸入與命理核心公式分層；民用 datetime 解析不塞進 Ziwei timing core。

---

## 三、目標目錄

```text
engine/
├── bazi/
│   ├── __init__.py
│   ├── calendar.py
│   └── interactions.py
│
├── ziwei/
│   ├── __init__.py
│   ├── common.py
│   ├── capabilities.py
│   ├── month.py
│   ├── day.py
│   ├── hour.py
│   ├── transformations.py
│   ├── stars.py
│   └── flying.py
│
├── validation/
│   ├── __init__.py
│   └── cross_system.py
│
├── project_bazi_calendar.py
├── project_ziwei_month.py
├── project_ziwei_day.py
└── project_ziwei_hour.py
```

目前已實作：

- `engine/bazi/calendar.py`
- `engine/ziwei/common.py`
- `engine/ziwei/capabilities.py`
- `engine/ziwei/month.py`
- `engine/ziwei/day.py`
- `engine/ziwei/hour.py`
- 四支對應的 `project_*.py` 相容入口

`transformations.py`、`stars.py`、`flying.py`、Calendar / Input Resolver 與 `validation/cross_system.py` 仍是後續 capability / infrastructure PR。

未來若奇門形成固定自動排盤規則，再另外建立 `engine/qimen/`，不與八字或紫微混寫。

---

## 四、能力狀態模型

Metaphysics Lab 不再只用 `enabled / disabled` 表示一個能力。

### 1. Implementation

- `planned`：尚未有正式 Python 實作，不得宣稱可執行。
- `implemented`：已有固定程式實作，可進入正式測試與驗證。

### 2. Maturity

- `experimental`：已有固定算法、測試與外部校驗，可以執行，但分析權重較低，不能單獨支撐高度確信。
- `stable`：算法與邊界已固定，測試與交叉驗證充分，可作正式分析依據。

### 3. Routing

- `default`：符合該問題精度時預設調用。
- `on_demand`：能力存在且可執行，但只有需要提高解析度、比較日期／時段、處理訊號衝突或使用者明確要求時才調用。

目前狀態：

```text
紫微流月宮位：implemented / stable / default
紫微流日宮位：implemented / experimental / on_demand
紫微流時宮位：implemented / experimental / on_demand
紫微細部四化：planned / on_demand
紫微流曜：planned / on_demand
紫微細層飛化：planned / on_demand
Calendar / Input Resolver：planned
Cross-System Validation：planned
```

實際成熟度只能依完成的驗證結果決定，不預先保證任何 Experimental 能力升為 Stable。

---

## 五、Bazi Engine

### `engine/bazi/calendar.py`

負責目前已經正式穩定的八字時間推導：

- 流年
- 流月
- 流日
- 流時
- 節氣邊界
- 23:00 換日
- 五虎遁
- 五鼠遁
- 天干十神
- 時區處理

正式實作由原本 `project_bazi_calendar.py` 移入，保持既有輸出相容。

### `engine/bazi/interactions.py`

未來專門處理本命／大運／流年／流月／流日／流時的干支互動。規則尚未固定以前，不把研究中的互動算法提前寫成正式輸出。

---

## 六、Ziwei Engine

紫微採單一 Ziwei Engine，下分月份、日期、時辰與細部推導模組，不建立互相重複的獨立引擎。

### `engine/ziwei/common.py`

集中保存：十二地支索引、十二宮名稱與排列、宮位移動／重排工具、輸入驗證與共用基礎。

流月、流日與流時共用 `palaces_from_ming_branch()`，不得各自複製不同方向的十二宮邏輯。

### `engine/ziwei/capabilities.py`

每項能力至少保存：capability id、implementation、maturity、routing、rule version、module path、dependencies。Router 與 Skill 依此決定能力是否可執行、是否預設執行，以及輸出時的成熟度標示。

### `engine/ziwei/month.py`

已完成流年斗君、流月命宮、流月十二宮重排、農曆初一換月與閏月拆半。

```text
implemented / stable / default
```

流月輸出保留 `flow_day_enabled = false` 表示本次月度預設路徑不執行流日；另以 availability 欄位表示細層 capability 是否存在，避免把 routing 與 implementation 混為一談。

### `engine/ziwei/day.py`

固定 Project 方法：

1. 先依正式流月規則取得目標日期的流月命宮。
2. 流月命宮作為農曆初一的流日命宮。
3. 每增加一日，順行一宮。
4. 十二宮循環。

```text
flow_day_index = (flow_month_index + lunar_day - 1) mod 12
```

目前：

```text
implemented / experimental / on_demand
```

正式規則與來源驗證見 `core/紫微流日推導規則.md`。本模組只做流日命宮與流日十二宮定位，不包含流日四化、流曜或細層飛化。

流日 structured output 現在也明確表示 flow-hour capability 已存在但預設不跑：

```text
flow_hour_implemented = true
flow_hour_default_routing = false
```

### `engine/ziwei/hour.py`

紫微流時定位已完成第一版正式 Python 實作。

固定 Project 方法：

1. 先由 `engine.ziwei.day` 取得目標日期的流日命宮。
2. 流日命宮作子時的流時命宮。
3. 每增加一個時辰，順行一宮。
4. 十二宮循環。

```text
flow_hour_index = (flow_day_index + hour_branch_index) mod 12
```

目前：

```text
implemented / experimental / on_demand
```

正式規則與來源驗證見 `core/紫微流時推導規則.md`。

流時採 1.5 架構：core 只接受已確認的農曆日期與 `hour_branch`。它不把民用 datetime、timezone、DST、國曆轉農曆或 23:00 日界 policy 包進 `hour.py`；這些責任留給未來 Calendar / Input Resolver。

用途只限具體時間問題，例如面試、談判、會議、簽約、出行與同日不同時辰比較。一般本命、年度、月份或一般單日問事不自動遍歷十二時辰。

本模組目前不包含流時天干、流時四化、流曜或細層飛化。

### `engine/ziwei/transformations.py`

未來負責可重現的四化推導能力。細部層級能否產生流月／流日／流時四化，必須依固定算法與規則版本分別驗證，不因已有本命或流年四化就自由延伸。完成實作與驗證後原則上採 `on_demand`。

### `engine/ziwei/stars.py`

未來負責已被 Project 正式定義的流曜推導。每一類流曜必須有明確來源、固定算法與回歸測試。

### `engine/ziwei/flying.py`

未來負責細層飛化／飛星關係的可重現推導，不為了配合事件或其他命理體系反向修改飛化結果。

---

## 七、問題精度與引擎調度

Metaphysics Lab 不採「有多少層就全部算多少層」。

```text
本命問題
→ 八字本命 + 紫微本命

年度問題
→ 八字流年 + 紫微流年

月份問題
→ 八字流月 + 紫微流月主要層
→ 不自動遍歷全部流日／流時

特定日期
→ 八字流日
→ 按需調用紫微流日（Experimental）

特定時間
→ 八字流時
→ 按需調用紫微流時（Experimental）
→ 具體行動視需要加入奇門
```

On-demand 可由下列情況觸發：使用者明確要求細看某一天／時段、比較兩個以上日期或時間、主要層訊號衝突需要提高解析度、未來 Cross-System Validation 需要較細證據、重大行動需要更精細的時間比較。

若使用者只問月份，不應為了增加細節而自動跑全部流日、流時、四化、流曜與飛化。

---

## 八、Cross-System Validation

`engine/validation/cross_system.py` 目前仍是 planned，後續只接受八字與紫微已完成的結構化結果。

不得為了讓兩套系統一致而修改任何單一引擎結果，也不得把不同術語一對一硬配。

跨系統比較以人生領域、方向、事件性質、時間窗、行動傾向為主，建議輸出：一致／部分一致／互補／衝突／資料不足。

Experimental capability 可以參與比較，但必須降權並保留成熟度標示。

### 證據權重與成熟度規則

v1.2 採質性證據階層，不先指定固定百分比。正式判斷至少同時考慮：

1. Data Quality｜資料品質。
2. Capability Maturity｜能力成熟度。
3. Time-Level Relevance｜時間層級相關性。
4. Cross-System Agreement｜跨系統一致度。
5. Personal Validation｜第二階段個人事件校準。

質性證據層級：

```text
主證據
→ 資料品質可靠 + 對應問題時間層級 + Stable capability

輔助證據
→ Stable capability，但屬較細或補充層級
→ 或跨系統另一體系提供方向一致的支持

降權證據
→ Experimental capability
→ 或存在明確 boundary warning、資料品質限制

不可使用
→ Planned / 未實作 / 未完成最低驗證門檻
→ 純研究假說但沒有固定可重現算法
```

細時間層是否成為主要時間證據，取決於使用者問題本身是否就是特定日期／時段；解析度更細不代表信心自動更高。

---

## 九、相容入口

目前保留：

```text
engine/project_bazi_calendar.py
engine/project_ziwei_month.py
engine/project_ziwei_day.py
engine/project_ziwei_hour.py
```

對應：

```text
project_bazi_calendar.py → engine/bazi/calendar.py
project_ziwei_month.py   → engine/ziwei/month.py
project_ziwei_day.py     → engine/ziwei/day.py
project_ziwei_hour.py    → engine/ziwei/hour.py
```

wrapper 主要維持既有 import / CLI 路徑，不是完整單檔引擎。完整 Python 環境以 package modules 為正式實作來源。

Experimental flow-day / flow-hour 不因便利而 eager import 到 `engine.ziwei` root；應由對應 module 明確 import，避免 CLI runpy warning 與 package 邊界混亂。

---

## 十、錯誤與邊界處理

每個引擎／capability 輸出都必須包含或可追溯：引擎名稱與版本、規則版本、implementation、maturity、routing、資料分類、輸入時間／曆法口徑與相關限制。

若輸入不足，不自行補造；明確回報缺少欄位並降低時間精度。

紫微流日第一版不自行從國曆時刻推導農曆日期。紫微流時則再要求上游提供已解析 `hour_branch`，同樣不自行宣稱子時換日規則。

民用 datetime → 農曆日期／時辰的便利入口，未來由版本化 Calendar / Input Resolver 處理；Resolver 必須明確保存 day-boundary policy，而不是只寫模糊流派名稱。

---

## 十一、驗證與升級門檻

任何新的紫微細部 capability，要成為可按需調用能力，至少必須具備：

1. 固定且可重現的算法。
2. 明確輸入、輸出與時間邊界。
3. 自動測試。
4. 人工回歸案例。
5. 至少兩個可信外部排盤／文獻來源交叉驗證。

達成以上條件後，可進入 `implemented / experimental`。是否升為 Stable，再依更廣泛邊界案例、實際問事追蹤、已發生事件驗證與 Issue 可重現案例決定。

紫微流日與紫微流時目前都已通過第一階段最低門檻，因此為 `implemented / experimental / on_demand`；尚未達 Stable。

---

## 十二、測試策略

### Bazi

既有八字測試全部保留，後續 Ziwei capability 不得破壞其結果。

### Ziwei Month

既有流月回歸測試保留，availability 標記不得改變既有流月算法結果。

### Ziwei Day

至少測：初一、初二、十二宮循環、閏月前半／後半、十二宮重排、非法日期／地支、capability metadata、wrapper、CLI、外部來源比對。

### Ziwei Hour

第一版至少測：

- 子／丑／午／亥代表時辰。
- 十二宮循環。
- 流日與流時層級接續。
- 閏月完全繼承 day engine 結果。
- 非法時辰地支。
- `14:00`、`下午兩點` 等民用時間字串拒絕。
- wrapper / modular path 一致。
- CLI 無 `RuntimeWarning`。
- capability metadata。
- 固定程式來源與獨立公開文字來源交叉比對。

子時跨日與不同時區不由 `hour.py` 測試決策；它們屬未來 Resolver 的測試範圍。

### Transformations / Stars / Flying

每個 capability 必須有獨立規則版本、正常案例、邊界案例、明確拒絕輸入案例與外部來源交叉比對。

### Cross-System Validation

必須測：一致、部分一致、衝突、單一系統缺資料、Experimental capability 降權，以及兩套系統使用不同月份邊界的正常差異。

---

## 十三、Issue 驅動演進

Metaphysics Lab 可以透過 GitHub Issues 累積外部案例與功能需求，包括排盤來源差異、節氣／農曆／換日／閏月邊界、capability 不一致、新流派或算法候選、可重現錯誤與新功能需求。

Issue 本身不是驗證證據。合併修正前仍需重現問題、確認資料來源與版本、新增或修正測試、更新算法／規則文件並記錄成熟度是否受影響。

真實命主資料不應直接貼入公開 Issue；需要案例時應匿名化並移除可識別資訊。

---

## 十四、Skill 封裝預留

預期結構：

```text
skills/metaphysics-lab/
├── SKILL.md
├── references/
├── scripts/
└── templates/
```

Skill 層負責問題分類、資料讀取順序、讀取 capability 狀態、決定要叫 Bazi／Ziwei／Validation／Qimen、按問題精度調用必要 capability、執行盲判／事件校準、套用信心與輸出規則。

未來人類友善輸入由 Skill / Router 配合 Calendar Resolver 轉成核心所需結構化資料；Skill 不重新定義曆法算法。正式算法仍以 repo 的 rules 與 engine 為唯一來源。

---

## 十五、版本與遷移順序

目前進度與建議順序：

1. ✅ 建立 `engine/bazi/` 與 `engine/ziwei/` 模組化基礎。
2. ✅ 重構八字到 `bazi/calendar.py`，保持既有測試一致。
3. ✅ 重構紫微流月到 `ziwei/month.py`，保持既有測試一致。
4. ✅ 保留 compatibility wrappers。
5. ✅ 建立 `ziwei/capabilities.py` 狀態模型。
6. ✅ 研究、固定、實作並驗證紫微流日；第一版為 Experimental on-demand。
7. ✅ 研究、固定、實作並驗證紫微流時定位；第一版為 Experimental on-demand。
8. 後續建立 Calendar / Input Resolver，使 ChatGPT／其他 AI／Skill 可直接輸入民用 datetime 而不污染 timing core。
9. 依序實作與驗證四化、流曜、細層飛化 capability，全部採按需調用。
10. 建立 Cross-System Validation，納入 capability maturity 權重。
11. 更新 Instructions、安裝與版本同步流程，使 router 能正確辨識 capability。
12. 最後封裝 Metaphysics Lab Skill v1.0。

每一項 capability 都可獨立 PR，不需要等全部完成才開始合併已驗證能力。

---

## 十六、v1.2 非目標

本階段不處理：

- 奇門自動排盤
- 未經固定算法與驗證的紫微細部推導
- 自動產生宿命式事件結論
- 用單一總分取代八字、紫微與事件的分層證據
- 將私人 Case 納入 GitHub 共用核心

---

## 十七、最終設計結論

Metaphysics Lab v1.2 採：

```text
Bazi Engine
+
Ziwei Engine（完整 capability modules，按需調度）
+
Cross-System Validation
+
Advisor / Skill Layer
```

八字與紫微分開計算；紫微內部以 common + timing + transformations + stars + flying 模組化；每項細部能力先完成實作與驗證，再依成熟度標為 Experimental 或 Stable；是否在當次問題執行，則由 routing mode 與問題精度決定。

目前紫微流日與流時定位都已落地為 Fine Timing on-demand capability：Python 可執行，但一般問事不預設執行。流時另外把「人類友善輸入」與「命理核心公式」分層，為未來 ChatGPT、其他 AI Skill、CLI/API 共用 Resolver 保留乾淨邊界。

這個架構的目的不是每次增加更多計算，而是確保需要提高解析度時，系統真的有已實作、可驗證、可調用的能力可以使用。
