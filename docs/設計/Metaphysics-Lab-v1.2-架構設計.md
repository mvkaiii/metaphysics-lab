# Metaphysics Lab v1.2 架構設計

## 一、目的

v1.2 的核心目標是把八字、紫微與跨系統驗證拆成清楚、可獨立測試的模組，並建立「能力存在、成熟度、預設調度」彼此分離的執行模型。

本版架構目標：

- 八字與紫微引擎分離
- 紫微流月／流日／流時拆成同一 Ziwei Engine 下的不同 timing modules
- 紫微四化、流曜與細層飛化形成可獨立驗證的 capability modules
- 建立獨立 Cross-System Validation 層
- 保留既有 `project_bazi_calendar.py`、`project_ziwei_month.py` 作相容入口
- 為後續 Skill 封裝保留清楚模組邊界
- 細部能力完成實作與驗證後可按需調用，但不因能力存在就每次自動執行

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
└── project_ziwei_month.py
```

未來若奇門形成固定自動排盤規則，再另外建立 `engine/qimen/`，不與八字或紫微混寫。

---

## 四、能力狀態模型

Metaphysics Lab 不再只用 `enabled / disabled` 表示一個能力。

每個 capability 至少要描述三個維度：

### 1. Implementation

- `planned`：尚未有正式 Python 實作，不得宣稱可執行。
- `implemented`：已有固定程式實作，可進入測試與驗證。

### 2. Maturity

- `experimental`：已有固定算法、測試與外部校驗，可以執行，但分析權重較低，不能單獨支撐高確信結論。
- `stable`：算法與邊界已固定，測試與交叉驗證充分，可作正式分析依據。

研究中的想法若尚未成為可重現程式，不列入可執行 capability。

### 3. Routing

- `default`：符合該問題精度時預設調用。
- `on_demand`：能力存在且可執行，但只有需要提高解析度、比較日期／時段、處理訊號衝突或使用者明確要求時才調用。

示意：

```text
流月宮位：implemented / stable / default
流日：implemented / stable / on_demand
流時：implemented / experimental / on_demand
流月四化：implemented / stable 或 experimental / on_demand
流月流曜：implemented / experimental / on_demand
細層飛化：implemented / experimental / on_demand
```

實際成熟度只能依完成的驗證結果決定，不預先保證升為 Stable。

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

這部分由現有 `project_bazi_calendar.py` 的正式算法移入，保持輸出相容。

### `engine/bazi/interactions.py`

未來專門處理：

- 本命／大運／流年／流月／流日／流時的干支互動
- 合、沖、刑、害、破等已被正式定義的互動
- 必要的五行與十神衍生指標

在規則尚未固定以前，不把研究中的互動算法提前寫成正式輸出。

---

## 六、Ziwei Engine

紫微採單一 Ziwei Engine，下分月份、日期、時辰與細部推導模組，不建立互相重複的獨立引擎。

### `engine/ziwei/common.py`

集中保存共用基礎：

- 十二地支索引
- 十二宮名稱與排列
- 宮位移動工具
- 輸入驗證
- 農曆月／閏月相關基礎資料結構
- 共用輸出格式

不得在其他紫微模組複製相同索引與宮位邏輯。

### `engine/ziwei/capabilities.py`

負責描述紫微能力狀態，不重新定義命理算法。

每項能力至少保存：

- capability id
- implementation status
- maturity
- routing mode
- rule version
- engine/module path
- dependency capabilities

Router 與 Skill 依這份狀態決定某個能力是否可以執行、是否預設執行，以及輸出時應標示的成熟度。

### `engine/ziwei/month.py`

承接目前已完成的紫微流月定位層：

- 流年斗君
- 流月命宮
- 流月十二宮重排
- 農曆初一換月
- 閏月拆半

目前狀態：`implemented / stable / default`。

### `engine/ziwei/day.py`

紫微流日能力。

目標用途：

- 在月份已確認後，判斷指定日期較活躍的人生領域
- 比較候選日期
- 與八字流日做跨系統比對

成為可調用 capability 前必須完成：

- 固定流派與流日起法
- 固定農曆／日期邊界
- 固定宮位推進規則
- 處理跨日與時區問題
- 至少兩種可信外部排盤／文獻來源交叉校驗
- 建立單元測試與人工回歸案例

完成上述條件後可先成為 `implemented / experimental / on_demand`；若驗證充分，再升為 `stable / on_demand`。

### `engine/ziwei/hour.py`

紫微流時能力。

目標用途只限具體時間問題，例如：

- 面試時段
- 談判時段
- 會議時段
- 簽約時段
- 出行時間
- 同一日期不同時辰比較

流時不應用於一般年度或月份問事。

第一版完成固定算法、測試與外部校驗後，先標 `implemented / experimental / on_demand`；經足夠追蹤後再評估升為 Stable。

### `engine/ziwei/transformations.py`

負責可重現的四化推導能力。

細部層級是否能產生流月／流日／流時四化，必須依固定算法與規則版本分別驗證，不因已有本命或流年四化就自由延伸。

完成實作與驗證的細部四化能力採 `on_demand`，平常月份問事不必自動全部執行。

### `engine/ziwei/stars.py`

負責已被 Project 正式定義的流曜推導。

每一類流曜必須有明確來源、固定算法與回歸測試。未完成算法定義者不得由模型自行補造。

完成後原則上採 `on_demand`，並依驗證品質標示 Experimental 或 Stable。

### `engine/ziwei/flying.py`

負責細層飛化／飛星關係的可重現推導。

此模組只接受正式規則已定義的輸入，不為了配合事件或其他命理體系反向修改飛化結果。

第一版預設 `on_demand`，成熟度由實際算法校驗與案例驗證決定。

---

## 七、問題精度與引擎調度

Metaphysics Lab 不採「有多少層就全部算多少層」。

建議調度：

```text
本命問題
→ 八字本命 + 紫微本命

年度問題
→ 八字流年 + 紫微流年

月份問題
→ 八字流月 + 紫微流月主要層
→ 四化／流曜／細飛預設不額外執行

特定日期
→ 八字流日
→ 按需調用紫微流日
→ 必要時補四化／流曜／細飛

特定時間
→ 八字流時
→ 按需調用紫微流時
→ 必要時補細部 capability
→ 具體行動視需要加入奇門
```

### On-demand 觸發條件

可包括：

- 使用者明確要求細看某一天／時段
- 比較兩個以上日期或時間
- 八字與紫微主要層訊號出現衝突，需要提高解析度
- Cross-System Validation 判定需要補充較細證據
- 重大行動需要更精細的時間比較

若使用者只問月份，不應為了增加細節而自動跑全部流日、流時、四化、流曜與飛化。

---

## 八、Cross-System Validation

### `engine/validation/cross_system.py`

這一層只接受八字與紫微已完成的結構化結果。

不得：

- 為了讓兩套系統一致而修改八字結果
- 為了符合八字而重解紫微原始盤面
- 把兩套系統不同術語一對一硬配
- 把跨系統一致度寫成必然事件

### 比對維度

跨系統比較以語義層為主：

1. 人生領域
2. 方向：機會／壓力／混合／中性
3. 事件性質
4. 時間窗
5. 行動傾向：進攻／觀察／防守

例如：

- 八字：官殺與財星作用提高，時間壓力增加
- 紫微：官祿／遷移／財帛相關宮位活躍

可標記為「工作／資源交換主題跨系統一致度較高」。

不得寫成「因此一定會升職／簽約」。

### 建議輸出狀態

- 一致
- 部分一致
- 互補
- 衝突
- 資料不足

並可分開保存：

- 八字支持度
- 紫微支持度
- 跨系統一致度
- 事件驗證支持度

Experimental capability 可以參與比較，但必須降權並保留成熟度標示。

最後的命理信心仍依作業規範判斷，不由單一分數自動決定。

### 證據權重與成熟度規則

v1.2 採質性證據階層，不先指定「八字 60%、紫微 40%」或 `Stable = 1.0`、`Experimental = 0.5` 之類缺乏實證基礎的固定百分比。

正式判斷至少同時考慮五個維度：

1. **Data Quality｜資料品質**：原始命盤、出生時間、時區、曆法輸入、來源版本與邊界資料是否完整可靠。
2. **Capability Maturity｜能力成熟度**：`stable` 可作主要證據；`experimental` 可執行但降權；`planned`、純研究假說或尚未完成驗證的算法不得進入正式權重判斷。
3. **Time-Level Relevance｜時間層級相關性**：權重以使用者實際問題的時間粒度為準。年度問題以年／月層級為主，日期與時辰訊號只用於細化；特定日期或特定時段問題則可把對應的流日／流時提升為主要時間證據。更細層訊號不能在沒有充分理由時反向推翻較高層主軸。
4. **Cross-System Agreement｜跨系統一致度**：八字與紫微在事件領域、方向、時間窗與行動傾向上越一致，可提高該判斷的支持度；但一致不等於必然發生，也不得把不同術語硬做一對一映射。
5. **Personal Validation｜個人事件校準**：只在第二階段事件校準使用。已驗證事件可以提高或降低某類盤面訊號在該命主身上的個人化可信度，但不得修改第一階段盲判、原始盤面或正式算法。

質性證據層級建議使用：

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

同一個訊號同時受到多個因素影響時，不以單一欄位自動決定最終信心。例如 `stable` capability 若輸入資料品質不足，仍必須降權；`experimental` capability 即使與其他體系一致，也不得因此直接升為主證據。

Cross-System Validation 可以輸出分層支持度，但 v1.2 不把所有證據壓成單一總分。建議保留：

- 八字支持度
- 紫微支持度
- 跨系統一致度
- capability maturity
- 資料品質限制
- 事件驗證支持度
- 最終信心等級

若未來累積足夠的問事追蹤、已驗證事件與 GitHub issue 可重現案例，可以另外建立版本化 calibration model，從資料估計數值權重。數值權重必須有樣本、算法、測試與版本紀錄，不得由模型或維護者憑直覺指定。

---

## 九、相容入口

v1.2 不直接刪除：

```text
engine/project_bazi_calendar.py
engine/project_ziwei_month.py
```

第一階段讓它們成為 compatibility wrapper：

```text
project_bazi_calendar.py
→ engine/bazi/calendar.py

project_ziwei_month.py
→ engine/ziwei/month.py
```

原本 Project Instructions、文件與既有使用者不用立刻更換呼叫方式。

只有在未來大版本正式公告 deprecated 後，才考慮移除舊入口。

---

## 十、錯誤與邊界處理

每個引擎／capability 輸出都必須包含或可追溯：

- 引擎名稱與版本
- 規則版本
- implementation status
- maturity
- routing mode
- 資料分類：原始盤面事實／Project 推導盤面
- 輸入時間與時區
- 相關邊界警告

不再用單一 `enabled: true/false` 同時代表「有沒有實作」與「這次要不要執行」。

若輸入不足：

- 不自行補造
- 明確回報缺少欄位
- 降低時間精度

若接近節氣、農曆換月、換日或其他邊界：

- 先標示 boundary warning
- 必要時要求可信曆法來源交叉確認

---

## 十一、驗證與升級門檻

任何新的紫微細部 capability，要成為可按需調用能力，至少必須具備：

1. 固定且可重現的算法。
2. 明確輸入、輸出與時間邊界。
3. 自動測試。
4. 人工回歸案例。
5. 至少兩個可信外部排盤／文獻來源交叉驗證。

達成以上條件後，可進入 `implemented / experimental`。

是否升為 Stable，再依：

- 更廣泛邊界案例
- 不同年份／時區測試
- 實際問事追蹤
- 已發生事件的事後驗證
- issue 回報中的可重現案例

決定。

不能因為某一個歷史事件吻合，就直接把研究算法升為 Stable。

---

## 十二、測試策略

重構時先保持既有行為，新增 capability 再各自擴充測試。

### Bazi

現有 10 項測試全部保留，重構後結果必須一致。

### Ziwei Month

現有 10 項流月測試全部保留，重構後結果必須一致。

### Ziwei Day

至少需要：

- 一般日期
- 農曆初一
- 月底
- 閏月前半／後半
- 跨國曆日／農曆日邊界
- 不同時區
- 外部排盤來源交叉比對

### Ziwei Hour

至少需要：

- 十二時辰
- 子時跨日
- 不同時區
- 流日與流時層級接續
- 外部排盤來源交叉比對

### Transformations / Stars / Flying

每個 capability 必須：

- 有獨立規則版本
- 有正常案例
- 有邊界案例
- 有至少一個明確失敗／拒絕輸入案例
- 有外部來源交叉比對

### Cross-System Validation

必須測：

- 一致
- 部分一致
- 衝突
- 單一系統缺資料
- Experimental capability 降權
- 兩套系統使用不同月份邊界的正常差異

---

## 十三、Issue 驅動演進

Metaphysics Lab 可以透過 GitHub Issues 累積外部案例與功能需求。

Issue 適合回報：

- 排盤來源結果差異
- 節氣／農曆／換日／閏月等邊界案例
- 某個 capability 與外部排盤不一致
- 新流派或算法候選
- 可重現的錯誤案例
- 新功能需求

Issue 本身不是驗證證據。合併修正前仍需：

- 重現問題
- 確認資料來源與版本
- 新增或修正測試
- 更新算法／規則文件
- 記錄成熟度是否受影響

真實命主資料不應直接貼入公開 Issue；需要案例時應匿名化並移除可識別資訊。

---

## 十四、Skill 封裝預留

v1.2 的模組設計應讓未來 Skill 可以依問題載入必要資源，而不是一次把所有內容放進上下文。

預期結構：

```text
skills/metaphysics-lab/
├── SKILL.md
├── references/
├── scripts/
└── templates/
```

Skill 層負責：

- 問題分類
- 資料讀取順序
- 讀取 capability 狀態
- 決定要叫 Bazi、Ziwei、Validation 或 Qimen
- 只按問題精度調用必要 capability
- 執行盲判／事件校準流程
- 套用信心與輸出規則

Skill 不重新定義曆法算法；正式算法仍以 repo 的 rules 與 engine 為唯一來源。

---

## 十五、版本與遷移順序

建議實作順序：

1. 建立 `engine/bazi/` 與 `engine/ziwei/` 模組化基礎。
2. 重構八字到 `bazi/calendar.py`，保持舊測試一致。
3. 重構紫微流月到 `ziwei/month.py`，保持舊測試一致。
4. 將舊兩支 Python 改成 compatibility wrapper。
5. 建立 `ziwei/capabilities.py` 狀態模型。
6. 研究、固定、實作並驗證紫微流日；先成為 on-demand capability。
7. 研究、固定、實作並驗證紫微流時；第一版可先為 Experimental on-demand。
8. 依序實作與驗證四化、流曜、細層飛化 capability，全部採按需調用。
9. 建立 Cross-System Validation，納入 capability maturity 權重。
10. 更新 Instructions、README、安裝與版本同步文件。
11. 最後封裝 Metaphysics Lab Skill v1.0。

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

這個架構的目的不是每次增加更多計算，而是確保需要提高解析度時，系統真的有已實作、可驗證、可調用的能力可以使用。