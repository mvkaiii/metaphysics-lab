# 安裝到 ChatGPT Project

本文件說明如何把 Metaphysics Lab 的共用核心安裝到新的 ChatGPT Project，並與私人命盤資料分開管理。

核心原則：

> GitHub 保存系統核心；ChatGPT Project 保存實際分析環境與私人 Case。

GitHub 更新不應直接覆蓋命主私人資料。

---

## 一、建立新的 ChatGPT Project

先建立新的 ChatGPT Project。建議一位主要命主使用一個獨立 Project，或至少在 Project 內用明確檔名區分不同命主。

不要把多人命盤混在同一組未標示的檔案中。

---

## 二、設定 Project Instructions

開啟：

`core/核心提示詞.md`

把內容複製到 ChatGPT Project 的 Instructions／專案指示中。

這份提示詞負責：

- 角色定位
- 資料讀取順序
- 問事先盲判、後事件校準
- 八字／紫微／奇門分工
- 資料類型區分
- 高風險領域邊界
- 輸出格式與信心標示

若核心提示詞更新，Project Instructions 也需要同步更新。

---

## 三、上傳正式規則與引擎

### 基礎安裝：保留相容入口，但注意 package 依賴

一般 Project 基礎建議加入：

```text
core/命理分析作業規範.md
core/命理推導計算規則.md
core/紫微流月推導規則.md
engine/project_bazi_calendar.py
engine/project_ziwei_month.py
```

用途：

- `命理分析作業規範.md`：最高層分析流程與資料治理規則。
- `命理推導計算規則.md`：八字流年／流月／流日／流時與 Project 細時間 capability 的固定算法與邊界。
- `紫微流月推導規則.md`：紫微流月斗君、流月命宮、十二宮與月份邊界。
- `project_bazi_calendar.py`：八字相容入口。
- `project_ziwei_month.py`：紫微流月相容入口。

v1.2 模組化後，wrapper 已不是可獨立執行的單檔引擎。若只是讓 AI 閱讀正式入口，可以把 wrapper 當作入口索引；若環境要**實際執行**八字／流月 wrapper，還必須同步：

```text
engine/bazi/__init__.py
engine/bazi/calendar.py
engine/ziwei/__init__.py
engine/ziwei/common.py
engine/ziwei/month.py
```

只放 `project_bazi_calendar.py` 或 `project_ziwei_month.py` 而缺少 package，實際執行會因 import 依賴缺失而失敗。

### 要使用 v1.2 紫微流日 On-demand Capability

再加入：

```text
core/紫微流日推導規則.md
engine/project_ziwei_day.py
```

若實際環境要**執行**這支薄 wrapper，而不只是讓 AI 閱讀正式入口，還必須同時具備：

```text
engine/ziwei/__init__.py
engine/ziwei/common.py
engine/ziwei/capabilities.py
engine/ziwei/month.py
engine/ziwei/day.py
```

### 要使用 v1.2 紫微流時 On-demand Capability

再加入：

```text
core/紫微流時推導規則.md
engine/project_ziwei_hour.py
```

若實際環境要執行流時 wrapper，還必須同時具備同版：

```text
engine/ziwei/__init__.py
engine/ziwei/common.py
engine/ziwei/capabilities.py
engine/ziwei/month.py
engine/ziwei/day.py
engine/ziwei/hour.py
```

流時 core 仍只接受已解析的農曆日期與 `hour_branch`，不自行處理民用 datetime、timezone、DST 或國曆轉農曆。v1.2 開發線已由 Calendar Resolver v1 負責 structured civil datetime + IANA timezone → `CalendarContext`，再由 Ziwei Calendar Adapter 傳入既有流月／流日／流時 core。Resolver 不套用任何命理日界；23:00 是子時，但 civil date 只在 00:00 換日。

### 要使用 Calendar Resolver v1

實際 Python 執行環境必須同步並保持同版：

```text
requirements.txt
engine/calendar/__init__.py
engine/calendar/precision.py
engine/calendar/models.py
engine/calendar/timezone.py
engine/calendar/lunar.py
engine/calendar/resolver.py
engine/ziwei/calendar_adapter.py
```

並執行：

```bash
pip install -r requirements.txt
```

目前 exact runtime dependencies 為 `lunar-python==1.4.8` 與 `tzdata==2026.3`（IANA `2026c`）。缺少 exact dependencies 時，不得宣稱 Calendar Resolver 可執行。

Resolver v1 只接受 structured civil datetime、IANA timezone 與可選 `utc_offset_hint`；自然語言解析與命理日界 policy 都在 Resolver 外。

完整 Python 環境或未來 Skill 建議直接使用：

```text
engine.bazi.calendar
engine.ziwei.month
engine.ziwei.day
engine.ziwei.hour
engine.ziwei.capabilities
```

不要把 `project_*.py` 薄 wrapper 誤認為完全獨立、無依賴的單檔引擎；wrapper 與 package 應保持同版。

### Capability 語意

目前 v1.2 開發線：

```text
紫微流月定位 = implemented / stable / default
紫微流日定位 = implemented / experimental / on_demand
紫微流時定位 = implemented / experimental / on_demand
紫微細部四化／流曜／細層飛化 = planned / on_demand
Calendar / Input Resolver = implemented (Calendar Resolver v1.0.0)
Ziwei Calendar Adapter = implemented
Cross-System Validation = planned
```

`on_demand` 的意思是能力可以執行，但一般年度／月份問事不預設跑。

Experimental 流日可用於指定日期、日期比較與細部驗證；Experimental 流時可用於指定時辰、時段比較與 hour-level 細化。兩者分析時都必須降權，不能單獨支撐高度確信。

### 建議加入的驗證資料

若 Project 檔案空間允許，也建議加入：

```text
tests/命理推導測試案例.md
tests/紫微流月推導測試案例.md
tests/紫微流日推導測試案例.md
tests/紫微流時推導測試案例.md
```

Python 單元測試主要供開發與回歸使用，不是一般問事的必要檔案。

---

## 四、建立私人 Case

從 `templates/` 複製空白模板到自己的私人環境，並把 `_TEMPLATE` 移除。

建議至少準備：

```text
命盤核心摘要.md
命盤資料校驗紀錄.md
驗證事件紀錄.md
流年追蹤紀錄.md
問事追蹤紀錄.md
重大決策紀錄.md
```

第一次建立時，不需要一次把每個檔案填滿。

優先順序是：

1. 出生資料與正式命盤來源
2. 命盤資料校驗
3. 命盤核心摘要
4. 已確認的重要事件
5. 之後再累積流年、問事與重大決策追蹤

詳細欄位請看 `docs/命盤資料準備指南.md`。

---

## 五、加入原始命盤資料

建議至少準備一份八字原始資料與一份紫微原始資料。

可使用 Astralium 或其他可靠排盤來源。若使用 Astralium，請看：

`docs/Astralium資料取得指南.md`

原始資料請保留來源名稱與產出日期，不要先自行刪改欄位後再交給 Project。

第三方排盤直接提供的內容屬於「原始盤面事實」；Metaphysics Lab 自己計算的流月、流日、流時等屬於「Project 推導盤面」，兩者不得混稱。

---

## 六、第一次啟動 Project

資料加入後，可先要求 Project 做「命盤建立／校驗」，不要直接跳到未來預測。

建議第一次對話確認：

- 是否成功讀到 `命理分析作業規範.md`
- 出生年月日時與出生地是否正確
- 八字四柱是否一致
- 日主與八字大運是否已確認
- 紫微十二宮、大限、流年等資料是否可讀
- 是否有不同來源的時間口徑差異
- 哪些欄位是原始來源，哪些是 Project 推導
- v1.2 capability registry 是否能區分 Stable / Experimental / Planned 與 Default / On-demand

確認完成後，再建立 `命盤核心摘要.md`。

---

## 七、Python 檔案放進 Project 代表什麼

把 `.py` 檔加入 Project，代表 Project 保存了正式算法來源。

**不代表每一個 ChatGPT 對話都會自動執行 Python。**

若當次環境能執行 Python，可依正式程式計算；若無法執行，AI 只能閱讀規則與程式內容，不得假裝已執行程式。

因此回答中若宣稱「程式已計算」「測試已通過」，必須真的有執行證據。

同樣地：

- `implemented` 代表程式能力存在。
- `on_demand` 代表不預設執行。
- 兩者不能混為一談。
- `project_*.py` 保留相容入口名稱，不代表單檔可執行；執行時會載入 package 內正式實作。

---

## 八、從 v1.1 升到 v1.2 細時間 Capability

如果原本 Project 已有 v1.1 流月能力，要加入紫微流日與流時，至少同步：

```text
core/紫微流月推導規則.md
core/紫微流日推導規則.md
core/紫微流時推導規則.md
engine/project_ziwei_month.py
engine/project_ziwei_day.py
engine/project_ziwei_hour.py
```

若需要在 Python 環境實際執行，再同步：

```text
engine/ziwei/__init__.py
engine/ziwei/common.py
engine/ziwei/capabilities.py
engine/ziwei/month.py
engine/ziwei/day.py
engine/ziwei/hour.py
```

並更新 Project Instructions 使用最新版 `core/核心提示詞.md`。

完成後 Project 應知道：

- 紫微流月：Stable / Default。
- 紫微流日：Experimental / On-demand，可執行但不預設跑。
- 紫微流時：Experimental / On-demand，可執行但不預設跑。
- Calendar Resolver v1：已實作；Ziwei Calendar Adapter 已實作。
- 流時四化、流曜、飛化：尚未實作。

---

## 九、更新時不要覆蓋私人資料

日後更新 Metaphysics Lab 時，只同步：

- `core/`
- `engine/`
- 必要的 `tests/`
- Project Instructions

不要用 GitHub 版本覆蓋自己的：

- 命盤核心摘要
- 命盤資料校驗紀錄
- 驗證事件紀錄
- 流年追蹤紀錄
- 問事追蹤紀錄
- 重大決策紀錄

詳細更新方式請看 `docs/更新與版本同步.md`。
