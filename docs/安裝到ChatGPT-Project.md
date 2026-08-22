# 安裝到 ChatGPT Project

本文件說明如何把 Metaphysics Lab 正式核心與 **Unreleased Phase 2C0｜Natal Chart Foundation** 安裝到 ChatGPT Project，同時把共用程式與私人 Case 分開管理。

核心原則：

> GitHub 保存系統核心；ChatGPT Project 保存實際分析環境與私人 Case。

GitHub 更新不應直接覆蓋命主私人資料。

---

## 一、Project Instructions

把：

```text
core/核心提示詞.md
```

同步到 ChatGPT Project Instructions。

核心提示詞負責：

- 資料讀取順序
- 問事先盲判、後事件校準
- 八字／紫微／奇門分工
- **八種資料類型**，包含 Project 原生盤面
- Input Resolution / Precision Gate
- External / Project / Resolved
- 高風險領域與信心邊界

若提示詞更新，Project Instructions 也要同步。

---

## 二、基礎規則

至少加入：

```text
core/命理分析作業規範.md
core/命理推導計算規則.md
core/紫微流月推導規則.md
```

需要流日／流時時再加入：

```text
core/紫微流日推導規則.md
core/紫微流時推導規則.md
```

固定原則：**Precision must be earned by input.** 輸入不足只能追問、保留候選或降級；不得自行補值。

---

## 三、Phase 2C0 Natal Foundation modules

若環境要真正執行 Project 原生本命盤，至少同步同版：

```text
requirements.txt

engine/birth/
engine/calendar/
engine/bazi/
engine/ziwei/
engine/natal/

templates/natal/
```

其中：

- `engine/birth/`：輸入、地點、時間 views。
- `engine/calendar/`：neutral civil/calendar infrastructure。
- `engine/bazi/natal.py`：Project Bazi Natal。
- `engine/ziwei/natal.py`：Project Ziwei Natal。
- `engine/natal/`：External import、Normalized Natal Model、reconciliation、authority、orchestration、Markdown export。

Phase 2C0 capability：

```text
birth.input_resolution    = implemented / experimental / on_demand / 1.0-exp
birth.location_resolution = implemented / experimental / on_demand / 1.0-exp
birth.true_solar_time     = implemented / experimental / on_demand / 1.0-exp
bazi.natal_chart          = implemented / experimental / on_demand / 1.0-exp
ziwei.natal_chart         = implemented / experimental / on_demand / 1.0-exp
natal.reconciliation      = implemented / stable / on_demand / 1.0
natal.markdown_export     = implemented / stable / on_demand / 1.0
ziwei.flowing_stars       = planned / on_demand
```

Bazi / Ziwei Natal 目前仍是 **Experimental**，不要因 orchestration 可用就升 Stable。

---

## 四、使用者最小輸入

完整 Mode A：

- 性別
- Gregorian 出生日期
- 出生時間
- 出生地

例如：

> 男，1984年3月13日19:20，台北市出生

如果使用者說：

> 1990年5月6日，高雄出生

只追問缺少的性別與出生時間。

如果使用者說：

> 大概晚上7、8點

不得猜中點；保留候選。候選跨越改盤邊界時追問，未跨 material boundary 時可在現有精度下繼續。

---

## 五、Location / Calendar / time views

使用者不必手動輸入經緯度或 timezone。Location Resolver 解析 birthplace name；Calendar Resolver 接受 structured civil datetime + IANA timezone。

**Calendar Resolver 不負責真太陽時。**

Phase 2C0 至少保留：

```text
reported_civil_time
normalized_civil_time
bazi_effective_time
ziwei_effective_time
```

八字與紫微使用獨立 time profile。Ziwei Natal ordinary UX 使用 Project default true-solar profile；原始 civil time 不會被覆蓋。

---

## 六、External / Project / Resolved

有 Astralium 或其他 structured external chart 時，不要把它覆蓋 Project 自算結果。

固定三層：

```text
External / Project / Resolved
```

固定 status：

```text
MATCH / EQUIVALENT / CONFLICT / NOT_COMPARABLE
```

Astralium 為可選 external qualification source，不是 runtime dependency。Experimental Project 與 external 發生實質衝突時，Resolved 預設採 external；原 conflict 仍保留。

---

## 七、既有八字／Calendar／Ziwei modules

Compatibility wrapper：

```text
engine/project_bazi_calendar.py
engine/project_ziwei_month.py
engine/project_ziwei_day.py
engine/project_ziwei_hour.py
```

wrapper 不是獨立單檔引擎；要實際執行仍需同版 package modules。

Calendar Resolver：structured local civil datetime + IANA timezone → `CalendarContext`。civil date 在 00:00 換日；23:00 已屬子時但 Resolver 不套命理日界。

---

## 八、Ziwei Transformation / Flying / Fine Cycle

Ziwei Transformation Core 與 Flying Core 已 Stable / On-demand。

Unreleased Phase 2B Fine Cycle：

```text
profile      = ziwei-fine-cycle-lunar-late-zi-v1
day_boundary = late_zi_forward-v1
stem / transformations / flying = implemented / experimental / on_demand
```

Calendar Resolver 保持 neutral；23:00 紫微 effective-day 前進只由 fine-cycle profile 套用。

Qualification：

```text
pinned lunar-lite 1d104fff...   18/18 PASS
pinned iztro 814b77e6...        integration PASS
Astralium fine-cycle             PENDING
```

`leap_twelfth_month_second_half` 為 synthetic internal coverage，not externally qualified。`ziwei.flowing_stars`／流曜仍 planned / on_demand。

---

## 九、私人 Case

從 templates 建立自己的：

```text
命盤核心摘要.md
命盤資料校驗紀錄.md
驗證事件紀錄.md
流年追蹤紀錄.md
問事追蹤紀錄.md
重大決策紀錄.md
```

私人出生資料、原始八字／紫微資料、Astralium raw chart、PDF、截圖不要提交回共用 repo。

第一次啟動先做命盤建立／校驗，確認 source classification、External / Project / Resolved、時間 profile 與 BLOCKING conflict，再進未來預測。

---

## 十、Python 執行與驗證

把 `.py` 放進 Project 代表保存正式算法來源，不代表每個 ChatGPT 對話都會自動執行 Python。

只有真的有執行證據時，才可宣稱「程式已計算」「測試已通過」。

Phase 2C0 qualification summary 只能保存 aggregate counts、digest、versions、status；私人 raw payload 不進 repo。

完整升級流程請看 [更新與版本同步](更新與版本同步.md)。
