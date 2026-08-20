# 紫微流時 Capability 設計規格

- 日期：2026-08-20
- 對應工作：PR #3
- Branch：`feature/ziwei-flow-hour-capability`
- 狀態：聊天室設計已核准；等待書面 spec review，尚未進入 implementation plan
- 目標 capability：`ziwei.flow_hour_palaces`

## 一、目的

PR #3 只實作「紫微流時命宮定位＋流時十二宮重排」。

本 PR 不處理流時天干、流時四化、流曜、細層飛化，也不把民用 datetime、時區、國曆轉農曆或子時換日政策塞進 `hour.py`。

核心設計採 1.5 架構：

```text
人類／AI 友善輸入
        ↓
未來 Calendar / Input Resolver
        ↓
已解析的農曆日期＋時辰地支
        ↓
Ziwei Flow-Hour Core
        ↓
Project 推導盤面
```

目的不是犧牲使用體驗，而是將「輸入解析」與「命理公式」分離。未來 ChatGPT、其他 AI Skill、CLI、API 或 agent 都可以提供國曆時間的便利入口，但底層 Ziwei Core 永遠使用固定、可重現的結構化輸入。

## 二、Capability 狀態目標

目前 `engine/ziwei/capabilities.py` 中：

```text
ziwei.flow_hour_palaces
implementation = planned
maturity = null
routing = on_demand
```

PR #3 完成並通過最低驗證門檻後，目標狀態為：

```text
ziwei.flow_hour_palaces
implementation = implemented
maturity = experimental
routing = on_demand
rule_version = 1.0-exp
module = engine.ziwei.hour
dependencies = (ziwei.flow_day_palaces,)
```

`Experimental / On-demand` 的意思是：

- Python 已有固定可執行實作。
- 已通過自動測試、人工回歸與最低外部交叉驗證。
- 一般本命、年度、月份問事不預設執行。
- 指定時段、候選時辰比較或需要提高到時辰解析度時才調用。
- 分析時必須降權，不得單獨支撐「高度確信」。

## 三、核心責任邊界

### 3.1 `engine/ziwei/hour.py` 負責

- 接受已確認的紫微流時必要輸入。
- 取得既有流日命宮。
- 依固定時辰地支 offset 推導流時命宮。
- 以既有 `palaces_from_ming_branch()` 重排流時十二宮。
- 回傳結構化 `Project 推導盤面`。
- 回傳 capability maturity / routing 與未實作功能標記。

### 3.2 `engine/ziwei/hour.py` 不負責

- 國曆 → 農曆。
- timezone / UTC offset / DST 處理。
- 將 `14:00`、`下午兩點` 等民用時間解析成時辰。
- 判斷 23:00 是否換日。
- 早子／晚子／子初換日等流派政策。
- 流時天干。
- 流時四化。
- 流時流曜。
- 細層飛化。
- Cross-System Validation。

這些責任不得因方便而偷偷加入 `hour.py`。

## 四、輸入介面

核心函式至少接受：

```text
birth_lunar_month
birth_hour_branch
flow_year_branch
lunar_month
lunar_day
is_leap_month
hour_branch
```

其中：

- `birth_lunar_month`：出生農曆月 1–12。
- `birth_hour_branch`：出生時辰地支。
- `flow_year_branch`：目標流年地支。
- `lunar_month`：已由可信上游確認的目標農曆月。
- `lunar_day`：已由可信上游確認的目標農曆日。
- `is_leap_month`：已確認的閏月狀態。
- `hour_branch`：已解析的目標時辰地支，必須是 `子丑寅卯辰巳午未申酉戌亥` 之一。

### 4.1 拒絕模糊輸入

以下不得由 core 自行轉換：

```text
hour_branch = "14:00"
hour_branch = "下午兩點"
hour_branch = "2pm"
hour_branch = ""
```

如果呼叫端只有民用時間，必須先由 Resolver 或其他可信上游解析後，再呼叫 flow-hour core。

## 五、固定算法

### 5.1 地支索引

沿用 `engine/ziwei/common.py`：

```text
子 = 0
丑 = 1
寅 = 2
卯 = 3
辰 = 4
巳 = 5
午 = 6
未 = 7
申 = 8
酉 = 9
戌 = 10
亥 = 11
```

### 5.2 流時命宮

先依正式的 `engine.ziwei.day` 取得目標日期的 `flow_day_ming_branch`。

固定 Project 公式：

```text
flow_hour_index
= (flow_day_index + hour_branch_index) mod 12
```

白話：

- 流日命宮為子時的流時命宮。
- 丑時順行一宮。
- 寅時順行兩宮。
- ……
- 亥時順行十一宮。
- 十二宮循環。

例如：

```text
流日命宮 = 卯
子時 → 卯
丑時 → 辰
寅時 → 巳
...
亥時 → 寅
```

### 5.3 流時十二宮

取得流時命宮後，直接共用：

```python
palaces_from_ming_branch(flow_hour_ming_branch)
```

不得在 `hour.py` 重新複製另一套十二宮方向算法。

## 六、日界與子時政策

PR #3 不定義民用時鐘的換日規則。

核心原則：

> `hour.py` 相信呼叫端已經解析好「這是哪一個農曆日的哪一個時辰」。

如果輸入是：

```text
lunar_day = 初八
hour_branch = 子
```

core 就視為「初八子時」，不自行改成初九。

原因是早子、晚子、23:00 換日等問題屬於不同流派／排盤口徑的 `day-boundary policy`，應由未來 Calendar Resolver 明確版本化，而不是藏在命理公式裡。

未來 Resolver 必須以可測試規則表示政策，例如：

```text
policy A:
23:00–23:59 → 仍使用民用日期所對應的命理日
00:00–00:59 → 使用當下民用日期所對應的命理日
```

或：

```text
policy B:
23:00 起 → 命理有效日期切換到下一日
```

不得只用模糊名稱如「早子派」「晚子派」而沒有明確時間區間與日期歸屬。

## 七、模組與 API

PR #3 預計新增：

```text
engine/ziwei/hour.py
engine/project_ziwei_hour.py
core/紫微流時推導規則.md
tests/test_project_ziwei_hour.py
tests/test_project_ziwei_hour_wrapper.py
tests/test_ziwei_hour_cli.py
tests/紫微流時推導測試案例.md
```

並更新：

```text
engine/ziwei/capabilities.py
engine/ziwei/common.py（只有真的需要共用 helper 時才動）
VERSION.md
CHANGELOG.md
README.md
core/命理分析作業規範.md
core/核心提示詞.md
core/命理推導計算規則.md
docs/架構說明.md
docs/快速開始.md
docs/安裝到ChatGPT-Project.md
docs/更新與版本同步.md
docs/設計/Metaphysics-Lab-v1.2-架構設計.md
```

### 7.1 預計核心函式

```python
flow_hour_ming_branch(...)
flow_hour_palaces(...)
project_derived_ziwei_hour(...)
```

API 風格應與 `engine/ziwei/day.py` 保持一致。

### 7.2 Package export 邊界

`engine.ziwei` root package 目前以 Stable／主要 API 為主，Experimental flow-day 採明確 module import，以避免 eager import 與 CLI `runpy` warning。

PR #3 應沿用同樣原則：Experimental flow-hour 預設由 `engine.ziwei.hour` 明確 import，不因便利而強制加入 package root eager import。

## 八、結構化輸出

`project_derived_ziwei_hour()` 至少回傳：

```text
engine
version
classification = Project 推導盤面
scope = 紫微流時
rule
capability
inputs
effective_lunar_month
flow_month_ming_branch
flow_day_ming_branch
flow_hour_ming_branch
flow_hour_palaces
source_note
confidence_note
features
```

`features` 必須明確表示：

```text
flow_hour_implemented = true
flow_hour_default_routing = false
hourly_four_transformations_implemented = false
hourly_flowing_stars_implemented = false
fine_flying_implemented = false
calendar_resolver_implemented = false
```

輸出不得冒充 Astralium、iztro 或其他第三方排盤系統直接結果。

## 九、Calendar / Input Resolver 的後續接口

Resolver 不在 PR #3 實作，但 PR #3 必須保持可被它乾淨呼叫。

未來高階輸入可能是：

```text
civil_datetime = 2026-09-18 14:00
timezone = Asia/Taipei
ziwei_day_boundary_policy = ziwei.day_boundary.v1
```

Resolver 的輸出至少應可形成：

```text
lunar_month
lunar_day
is_leap_month
hour_branch
resolver_version
day_boundary_policy
```

再交給 day/hour core。

這使 ChatGPT、其他 AI Skill、CLI、API 可以提供「直接輸入國曆時間」的使用體驗，同時保持 Ziwei Core 不依賴特定 AI、UI 或時間解析實作。

## 十、錯誤處理

- 非法 `hour_branch`：`ValueError`，不得猜測。
- 非法農曆月／日：沿用既有 common validation。
- 非法出生時辰／流年地支：沿用既有 branch validation。
- 缺少必要欄位：由 Python 呼叫介面／CLI 明確報錯。
- 民用時間字串誤傳給 `hour_branch`：拒絕，不自動轉換。
- 上游沒有固定日界政策時：core 不代替上游決定日期。

## 十一、測試策略

### 11.1 自動測試

至少包含：

1. 子時與流日命宮同宮。
2. 丑時順行一宮。
3. 亥時順行十一宮。
4. 十二宮循環。
5. 不同流日命宮的 offset 結果可重現。
6. `month → day → hour` 鏈結一致。
7. `flow_hour_palaces()` 與共用 `palaces_from_ming_branch()` 一致。
8. 非法時辰地支拒絕。
9. `14:00`、`下午兩點` 等字串不被 core 偷偷解析。
10. compatibility wrapper 與 modular API 輸出一致。
11. CLI 可執行且 stderr 無意外 warning。
12. capability registry 正確為 `implemented / experimental / on_demand`。
13. Stable flow-month、Experimental flow-day 與 Bazi 既有測試全部不得 regression。

### 11.2 人工回歸

新增 `tests/紫微流時推導測試案例.md`，使用公開或合成案例，不使用真實命主私人出生資料。

人工案例至少涵蓋：

- 子／丑／午／亥四個代表時辰。
- 十二宮跨界循環。
- 一般月。
- 閏月前半與後半各至少一例，確認 hour 只繼承 day 結果，不自行重做閏月判斷。

## 十二、外部驗證門檻

PR #3 在標記 `implemented / experimental / on_demand` 之前，至少必須完成：

1. 固定、可重現的算法。
2. 自動測試。
3. 人工回歸案例。
4. 至少兩個可信外部來源交叉驗證流時起法。

### Source A：iztro 固定程式版本

Metaphysics Lab 對 PR #3 的第一個可重現程式來源固定使用與流日驗證相同的 iztro commit：

```text
814b77e6371e1050cac31bbf674db3c3138fcfde
```

該版本運限實作採等價公式：

```text
hourlyIndex = fixIndex(dailyIndex + hourBranchIndex)
```

正式規則文件必須引用固定 commit URL，不得只引用 mutable `main`。

### Source B：獨立外部來源

實作完成前必須再找到至少一個獨立於 iztro 的公開排法、文件或可重現輸出，交叉驗證「流日命宮起子時、每時辰順行一宮」的流時起法，並在 `core/紫微流時推導規則.md` 中標示來源層級。

若 Source B 只有二手資料，可作佐證，但不得被描述成一手程式輸出或 Stable 的充分依據。

若最低兩來源門檻未達成，PR #3 不得把 capability 從 `planned` 提升為可正式調用的 `implemented / experimental`。

## 十三、調用政策

flow-hour 只在需要時調用，例如：

- 使用者明確指定某個時辰。
- 比較同一天兩個以上時段。
- 流日層主軸已確定，需要提高到時辰解析度。
- 未來 Cross-System Validation 需要補充 hour-level evidence。
- 重大行動需要比較時段，並已確認現實條件。

一般本命、年度、月份，甚至一般「某一天如何」的問事，都不因 flow-hour capability 存在就自動遍歷十二時辰。

## 十四、證據權重

第一版 maturity 固定為 Experimental。

因此：

- 可以作時段比較與補充證據。
- 不能單獨推翻 Stable 的高層主軸。
- 不能因解析度更細就自動提高信心。
- 不得單獨支撐「高度確信」。
- 第二階段事件校準可以調整個人化可信度，但不能反向修改公式或第一階段盲判。

## 十五、PR #3 明確 Non-goals

不在 PR #3：

- 流時天干。
- 流時四化。
- 流月／流日四化。
- 流曜。
- 細層飛化。
- Calendar Resolver 實作。
- 國曆轉農曆。
- timezone / DST。
- 23:00 換日政策。
- 早子／晚子 policy 實作。
- Cross-System Validation 正式引擎。
- Skill orchestration 實作。

上述能力應以後續獨立 PR 處理，避免不同算法與驗證風險綁在同一個變更中。

## 十六、完成定義

PR #3 只有在以下條件全部成立才算完成：

- `engine/ziwei/hour.py` 有固定、可重現實作。
- compatibility wrapper 可用。
- capability registry 狀態正確。
- 自動測試全綠，既有測試無 regression。
- 人工回歸案例完成。
- 至少兩個可信外部來源完成交叉驗證。
- 規則文件明確區分 Project 推導與第三方來源。
- 最高層 Project 規則允許 flow-hour 作 Experimental / On-demand 使用。
- 文件不再存在「程式已實作但最高規則禁止使用」的矛盾。
- Calendar Resolver、四化、流曜、飛化等未實作能力仍被清楚標為未實作。

完成後使用者與 AI 的語意應一致：

> 紫微流時宮位定位已可執行，但屬 Experimental / On-demand。核心只接受已解析農曆日期與時辰地支；民用 datetime、時區與日界政策由外層 Resolver 負責。
