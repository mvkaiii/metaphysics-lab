# Metaphysics Lab

Metaphysics Lab 是一套以「可重現、可驗證、以決策為導向」為核心的命理分析框架。

它把命理分析拆成可管理的層級：原始盤面、資料校驗、固定算法推導、第一階段盲判、第二階段事件校準、現實決策策略與後續結果驗證。

## 第一次使用，從這裡開始

- 想先快速了解怎麼用 → [快速開始](docs/快速開始.md)
- 要裝進 ChatGPT Project → [安裝到 ChatGPT Project](docs/安裝到ChatGPT-Project.md)
- 不知道要準備哪些出生／命盤／事件資料 → [命盤資料準備指南](docs/命盤資料準備指南.md)
- 還沒有八字或紫微結構化資料 → [Astralium 資料取得指南](docs/Astralium資料取得指南.md)
- GitHub 更新後，不知道 Project 哪些檔案要換 → [更新與版本同步](docs/更新與版本同步.md)
- 想了解資料分類與隱私 → [資料治理](docs/資料治理.md)
- 想了解整體設計 → [架構說明](docs/架構說明.md)

---

## 核心理念

- 命盤提供模型。
- Project 推導提供時間層級。
- 事件提供證據。
- 現實背景決定策略。
- 問事先盲判，再校準。
- 原始盤面、Project 推導盤面與命理推論必須分開。
- 系統核心與私人個案資料必須分開保存。

## 目前能力

Metaphysics Lab v1.1 正式版目前納入：

- 子平八字本命與運限分析規範
- 紫微斗數本命、大限、小限、流年資料使用規範
- Project 紫微流月：斗君、流月命宮、流月十二宮重排
- 問事雙階段流程：先盲判、後事件校準
- Project 八字流年、流月、流日、流時推導
- 八字 23:00 early-Zi 換日（八字引擎責任，不是 Resolver 的 civil date policy）
- 五虎遁與五鼠遁
- 天干十神推導
- 節氣交界警告
- 問事追蹤與結果驗證制度

v1.2 開發線另已加入：

- 紫微 capability registry：把「是否已實作」「成熟度」「預設調度」分開管理
- Project 紫微流日定位：`implemented / experimental / on_demand`
- 流日命宮與流日十二宮重排
- 紫微流日自動測試、人工回歸與外部來源交叉校驗紀錄
- Project 紫微流時定位：`implemented / experimental / on_demand`
- 流時命宮與流時十二宮重排
- 紫微流時自動測試、人工回歸與外部來源交叉校驗紀錄
- Calendar Resolver v1：`implemented`，將 structured civil datetime + IANA timezone 正規化為可追溯 `CalendarContext`
- Input Resolution / Precision Gate：上游 pure policy，先判斷問題所需最低時間精度，不足時追問／保留候選／降級
- Ziwei Calendar Adapter：`implemented`，第一個正式 adapter；Bazi refactor 不包含在本次變更

目前尚未具備：

- 紫微細部四化／流曜／細層飛化
- Cross-System Validation 正式引擎
- 完整 Project 干支互動引擎
- 奇門自動排盤引擎

---

## v1.2 Capability 模型

v1.2 不再把「能力存在」和「這次要不要執行」混成同一個 enabled / disabled 開關。

每個 capability 分別記錄：

```text
implementation = planned / implemented
maturity       = experimental / stable
routing        = default / on_demand
```

例如：

```text
紫微流月定位 = implemented / stable / default
紫微流日定位 = implemented / experimental / on_demand
紫微流時定位 = implemented / experimental / on_demand
```

`On-demand` 的意思是：**Python 已經能執行，但一般問題不預設跑；只有需要提高解析度時才調用。**

`Experimental` 也能實際執行與累積驗證，只是分析權重較低，不能單獨支撐高度確信。

---

## v1.2 引擎模組化

目前開發線已把正式 Python 實作拆成：

```text
engine/bazi/      八字正式模組
engine/calendar/  system-neutral Calendar Resolver
engine/ziwei/     紫微正式模組（含 Calendar adapter）
```

八字與紫微維持不同曆法與推導邏輯，不混寫在同一支 Python。

既有／相容入口：

```text
engine/project_bazi_calendar.py
engine/project_ziwei_month.py
engine/project_ziwei_day.py
engine/project_ziwei_hour.py
```

這些 `project_*.py` 保留相容呼叫名稱，但已是薄 wrapper，**不是可獨立執行的單檔引擎**。若要實際執行 Python，必須同時具備對應 package；只複製 wrapper 而缺少 `engine/bazi/` 或 `engine/ziwei/` 會因 import 依賴缺失而失敗。

完整 Python 環境與未來 Skill 可直接使用：

```text
engine.bazi.calendar
engine.ziwei.month
engine.ziwei.day
engine.ziwei.hour
engine.ziwei.capabilities
```

能力存在不代表每次問事都要把所有細層全部執行；router / Skill 仍依問題時間粒度決定實際調用。

---

## 最短建置流程

### 1. 建立命盤資料

建議先準備：

- 出生年月日、時間、出生地與性別
- 八字結構化資料
- 紫微結構化資料

可使用 [Astralium](https://getastralium.com/) 取得可複製給 AI 的結構化命盤資料；也可以使用其他可靠排盤來源，但必須保留來源與時間口徑。

### 2. 建立 ChatGPT Project

將 `core/核心提示詞.md` 內容同步到 Project Instructions。

Project 基礎檔案至少加入：

```text
core/命理分析作業規範.md
core/命理推導計算規則.md
core/紫微流月推導規則.md
engine/project_bazi_calendar.py
engine/project_ziwei_month.py
```

如果只是讓 AI 閱讀正式入口，上述 wrapper 可作為索引；如果環境要**實際執行**八字／流月 wrapper，還要同步：

```text
engine/bazi/__init__.py
engine/bazi/calendar.py
engine/ziwei/__init__.py
engine/ziwei/common.py
engine/ziwei/month.py
```

若要使用 v1.2 紫微流日 on-demand capability，再同步：

```text
core/紫微流日推導規則.md
engine/project_ziwei_day.py
engine/ziwei/capabilities.py
engine/ziwei/day.py
```

`project_ziwei_day.py` 同樣依賴 `engine/ziwei/` package，不是獨立單檔。

若要使用 v1.2 紫微流時 on-demand capability，再同步：

```text
core/紫微流時推導規則.md
engine/project_ziwei_hour.py
engine/ziwei/hour.py
engine/ziwei/day.py
engine/ziwei/month.py
engine/ziwei/common.py
engine/ziwei/capabilities.py
```

`project_ziwei_hour.py` 同樣依賴同版 `engine/ziwei/` package，不是獨立單檔。一般問題不預設跑流時；只有指定時辰、時段比較或需要 hour-level precision 時才按需調用。

詳細步驟請看 [安裝到 ChatGPT Project](docs/安裝到ChatGPT-Project.md)。

### 3. 建立私人 Case

從 `templates/` 複製需要的模板，建立自己的：

```text
命盤核心摘要.md
命盤資料校驗紀錄.md
驗證事件紀錄.md
流年追蹤紀錄.md
問事追蹤紀錄.md
重大決策紀錄.md
```

這些是私人資料，不應提交回共用 GitHub repo。

### 4. 先校驗，再問事

第一次使用先確認出生資料、四柱、大運、紫微宮位與時間口徑；確認後再建立核心摘要。

未來問事採：

**第一階段盲判 → 第二階段事件校準**

---

## 目錄

```text
core/           核心規範、推導規則、系統提示詞
engine/bazi/    八字正式 Python 模組
engine/ziwei/   紫微正式 Python 模組
engine/*.py     既有相容入口
tests/          自動測試與人工回歸測試紀錄
templates/      新命主建立私人 Case 時使用的空白模板
docs/           安裝、資料準備、更新、架構與資料治理說明
```

## 重要邊界

本儲存庫只保存可共用的系統核心，不應提交真實命主的出生資料、命盤、醫療、家庭、工作、資產、感情、問事與其他可識別私人事件。

個人資料應保存在自己的私人 ChatGPT Project、私人知識庫或其他受控環境中。

---

## 八字時間推導

正式模組：

`engine/bazi/calendar.py`

相容入口：

`engine/project_bazi_calendar.py`

規則：

`core/命理推導計算規則.md`

所有細部時間計算結果都必須標示為「Project 推導盤面」，不得冒充 Astralium、原始 PDF 或其他第三方排盤系統的直接輸出。

## 紫微流月

正式模組：

`engine/ziwei/month.py`

相容入口：

`engine/project_ziwei_month.py`

規則：

`core/紫微流月推導規則.md`

Metaphysics Lab 已有 Stable 紫微流月定位：斗君、流月命宮與流月十二宮。

- 紫微流月採農曆月，農曆初一換月。
- 閏月採初一至十五歸原月、十六起歸下一月。
- 八字流月採節氣月。

因此同一個國曆日期的八字流月與紫微流月可能不同，這是兩套系統的月份邊界差異，**不是 bug**。

流月結構化輸出中的 `flow_day_enabled = false` 只代表「本次流月預設路徑不自動跑流日」；v1.2 同時標示 `flow_day_available_on_demand = true`。

## 紫微流日

正式模組：

`engine/ziwei/day.py`

相容入口：

`engine/project_ziwei_day.py`

規則：

`core/紫微流日推導規則.md`

目前狀態：

```text
implementation = implemented
maturity = experimental
routing = on_demand
```

固定定位法：先取得目標日期的流月命宮，再以流月命宮起農曆初一，每日順行一宮。

一般年度／月份問事不預設執行流日。適合在：

- 指定某一天細看
- 比較兩個以上候選日期
- 月份主軸確認後需要提高日期解析度
- 之後 Cross-System Validation 需要補流日層證據

時按需調用。

目前流日只做命宮與十二宮定位；流日四化、流曜與細層飛化仍是後續 capability。

## 紫微流時

正式模組：

`engine/ziwei/hour.py`

相容入口：

`engine/project_ziwei_hour.py`

規則：

`core/紫微流時推導規則.md`

目前狀態：

```text
implementation = implemented
maturity = experimental
routing = on_demand
```

固定定位法：先取得流日命宮，以流日命宮起子時，之後每個時辰順行一宮。

流時 core 只接受已解析的農曆日期與 `hour_branch`，不自行處理國曆轉農曆、timezone、DST 或 23:00 日界。一般問題不預設遍歷十二時辰；只在指定時辰、時段比較或確實需要提高到時辰解析度時按需調用。

目前流時只做命宮與十二宮定位；流時天干、流時四化、流曜與細層飛化仍是後續 capability。Calendar Resolver v1 已實作，並以 `engine/ziwei/calendar_adapter.py` 對接既有流月／流日／流時 core。

---

## Calendar Resolver v1

目前 v1.2 開發線的 Calendar Resolver v1 已實作。它是 system-neutral 的民用時間／曆法 context 層，不是八字或紫微本身的命理日界引擎。

固定契約：

```text
Calendar Resolver v1 = implemented
Input Resolution / Precision Gate = upstream pure policy
natural-language parsing = outside Resolver
runtime lunar = lunar-python 1.4.8
HKO validated range = 1901-01-01..2100-12-31
2057-09-28..2057-10-27 = boundary_conflict
2089-09-04 / 2097-08-07 = boundary_caution
timezone = pinned tzdata 2026.3 / IANA 2026c
Ziwei = first adapter
Bazi refactor = not included
```

時間邊界固定為：**23:00 已屬子時，但 civil date 只在 00:00 換日**。Resolver 的 `metaphysics_day_boundary_applied = false`，因此不會把八字的 23:00 early-Zi 換日自動套到紫微。紫微自己的命理日界若未來要版本化，仍需另行定義與驗證。

Resolver 第一版只接受 structured local civil datetime、IANA timezone 與可選 `utc_offset_hint`；自然語言時間解析、timezone 猜測、真太陽時、紫微 23:00 學派選擇都在 Resolver 外。

---

## Python 檔案與 ChatGPT Project

把 `.py` 放進 Project，代表 Project 保存正式算法來源；**不代表每次對話都會自動執行 Python**。

如果 GitHub 的引擎更新，Project 中的 Python 副本也需要同步更新。若使用 compatibility wrapper 執行程式，wrapper 與其 package 依賴必須保持同版。詳細規則請看 [更新與版本同步](docs/更新與版本同步.md)。

---

## 使用提醒

命理只能提供趨勢、時間壓力、決策風險與策略參考。醫療、法律、稅務、保險、房產、大額投資與高槓桿事項，仍應以相關專業人士的判斷為準。
