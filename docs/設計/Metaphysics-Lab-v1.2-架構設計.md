# Metaphysics Lab v1.2 架構設計

## 一、目的

v1.2 的核心目標是把八字、紫微與跨系統驗證拆成清楚、可獨立測試的模組，避免所有時間推導與分析邏輯塞在同一支 Python 裡。

本版優先處理：

- 八字與紫微引擎分離
- 紫微流月／流日／流時拆成同一 Ziwei Engine 下的不同 timing modules
- 建立獨立 Cross-System Validation 層
- 保留既有 `project_bazi_calendar.py`、`project_ziwei_month.py` 作相容入口
- 為後續 Skill 封裝保留清楚模組邊界

本設計不代表流日、流時已正式啟用。流日與流時仍需先完成規則研究、交叉校驗與測試後，才可改變正式啟用狀態。

---

## 二、架構原則

1. 八字與紫微使用不同曆法與推導規則，不共用業務邏輯。
2. 各 timing module 只處理自己的時間層級。
3. 共用基礎邏輯集中，不在 month/day/hour 之間重複。
4. Cross-System Validation 只比較兩套系統已完成的輸出，不回頭修改任何單一引擎結果。
5. 問題精度決定需要載入的模組，不因存在更細時間層級就每次全部執行。
6. GitHub 繼續作為正式核心與版本來源；ChatGPT Project／Skill 只負責引用與執行。

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
│   ├── month.py
│   ├── day.py
│   └── hour.py
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

## 四、Bazi Engine

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

這部分應由現有 `project_bazi_calendar.py` 的正式算法逐步移入，先保持輸出相容。

### `engine/bazi/interactions.py`

未來專門處理：

- 本命／大運／流年／流月／流日／流時的干支互動
- 合、沖、刑、害、破等已被正式定義的互動
- 必要的五行與十神衍生指標

在規則尚未固定以前，不應把研究中的互動算法提前寫成正式輸出。

---

## 五、Ziwei Engine

紫微採單一 Ziwei Engine，下分月份、日期與時辰模組，不建立三套互相重複的獨立引擎。

### `engine/ziwei/common.py`

集中保存共用基礎：

- 十二地支索引
- 十二宮名稱與排列
- 宮位移動工具
- 輸入驗證
- 農曆月／閏月相關基礎資料結構
- 共用輸出格式

不得在 `month.py`、`day.py`、`hour.py` 複製相同索引與宮位邏輯。

### `engine/ziwei/month.py`

承接目前已啟用的紫微流月定位層：

- 流年斗君
- 流月命宮
- 流月十二宮重排
- 農曆初一換月
- 閏月拆半

目前狀態：Stable。

### `engine/ziwei/day.py`

規劃中的紫微流日層。

目標用途：

- 在月份已確認後，判斷某些日期較活躍的人生領域
- 與八字流日做跨系統比對

正式啟用前必須完成：

- 固定流派與流日起法
- 固定農曆／日期邊界
- 固定宮位推進規則
- 處理跨日與時區問題
- 以至少兩種可信外部來源交叉校驗
- 建立單元測試與人工回歸案例

在上述條件完成前，狀態維持 Disabled／Research。

### `engine/ziwei/hour.py`

規劃中的紫微流時層。

目標用途只限具體時間問題，例如：

- 面試時段
- 談判時段
- 會議時段
- 簽約時段
- 出行時間

流時不應用於一般年度或月份問事。

第一版即使完成算法，也建議先標 Experimental；必須經足夠測試與實際追蹤後，才可升為 Stable。

---

## 六、問題精度與引擎調度

Metaphysics Lab 不採「有多少層就全部算多少層」。

建議調度：

```text
本命問題
→ 八字本命 + 紫微本命

年度問題
→ 八字流年 + 紫微流年

月份問題
→ 八字流月 + 紫微流月

特定日期
→ 八字流日 + 紫微流日（正式啟用後）

特定時間
→ 八字流時 + 紫微流時（符合啟用狀態時）
→ 具體行動視需要加入奇門
```

若使用者只問月份，不應為了增加細節而自動跑全部流日與流時。

---

## 七、Cross-System Validation

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

最後的命理信心仍依作業規範判斷，不由單一分數自動決定。

---

## 八、相容入口

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

## 九、錯誤與邊界處理

每個引擎輸出都必須包含：

- 引擎名稱與版本
- 規則版本
- 啟用狀態
- 資料分類：原始盤面事實／Project 推導盤面
- 輸入時間與時區
- 相關邊界警告

若輸入不足：

- 不自行補造
- 明確回報缺少欄位
- 降低時間精度

若接近節氣、農曆換月、換日或其他邊界：

- 先標示 boundary warning
- 必要時要求可信曆法來源交叉確認

---

## 十、測試策略

重構時必須先保持既有行為。

### Bazi

現有 10 項測試全部保留，重構後結果必須一致。

### Ziwei Month

現有 10 項流月測試全部保留，重構後結果必須一致。

### Ziwei Day

正式啟用前至少需要：

- 一般日期
- 農曆初一
- 月底
- 閏月前半／後半
- 跨國曆日／農曆日邊界
- 不同時區
- 與外部排盤來源交叉比對

### Ziwei Hour

正式啟用前至少需要：

- 十二時辰
- 子時跨日
- 不同時區
- 流日與流時層級接續
- 外部排盤來源交叉比對

### Cross-System Validation

必須測：

- 一致
- 部分一致
- 衝突
- 單一系統缺資料
- 兩套系統使用不同月份邊界的正常差異

---

## 十一、Skill 封裝預留

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
- 決定要叫 Bazi、Ziwei、Validation 或 Qimen
- 執行盲判／事件校準流程
- 套用信心與輸出規則

Skill 不重新定義曆法算法；正式算法仍以 repo 的 rules 與 engine 為唯一來源。

---

## 十二、版本與遷移順序

建議實作順序：

1. 先建立新的 `engine/bazi/`、`engine/ziwei/`、`engine/validation/` 目錄。
2. 重構八字到 `bazi/calendar.py`，保持 10/10 舊測試一致。
3. 重構紫微流月到 `ziwei/month.py`，保持 10/10 舊測試一致。
4. 將舊兩支 Python 改成 compatibility wrapper。
5. 研究並固定紫微流日算法。
6. 完成流日測試後才標 Stable。
7. 研究並固定紫微流時算法。
8. 流時第一版先標 Experimental。
9. 建立 Cross-System Validation。
10. 更新 Instructions、README、安裝與版本同步文件。
11. 最後再封裝 Metaphysics Lab Skill v1.0。

---

## 十三、v1.2 非目標

本階段不處理：

- 紫微流月四化
- 紫微流日／流時四化與流曜
- 奇門自動排盤
- 自動產生宿命式事件結論
- 用單一總分取代八字、紫微與事件的分層證據
- 將私人 Case 納入 GitHub 共用核心

---

## 十四、最終設計結論

Metaphysics Lab v1.2 採：

```text
Bazi Engine
+
Ziwei Engine
+
Cross-System Validation
+
Advisor / Skill Layer
```

八字與紫微分開計算；紫微內部以 common + month/day/hour 模組化；跨系統比較獨立處理；上層再依問題精度決定實際載入與分析流程。

這個架構的目的不是增加計算複雜度，而是讓每一層都能被獨立理解、測試、替換與校驗。