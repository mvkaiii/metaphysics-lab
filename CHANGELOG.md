# 變更紀錄

## Unreleased｜Phase 2C0 Natal Chart Foundation

### Birth / Location / Time foundation

- 新增 structured birth input resolution 與 Precision Gate；原則為 **Precision must be earned by input**。
- 完整 Mode A 最低輸入：性別、Gregorian 出生日期、出生時間、出生地。
- 缺欄位只回 machine-readable `missing_fields` / `allowed_actions`；不自行補值。
- 新增 birthplace geocoding / timezone resolution，零候選或多個 material candidates fail closed。
- Calendar Resolver 保持 neutral；**Calendar Resolver 不負責真太陽時**。
- 保存 `reported_civil_time`、`normalized_civil_time`、`bazi_effective_time`、`ziwei_effective_time`。
- 真太陽時 profile 固定記錄「經度校正＋均時差」，八字與紫微 profile 獨立。

### Project 原生本命盤

- 新增八種資料類型中的 **Project 原生盤面**，與原始盤面事實、Project 推導盤面、命理推論分開。
- `bazi.natal_chart` = implemented / **Experimental** / on_demand / 1.0-exp。
- `ziwei.natal_chart` = implemented / **Experimental** / on_demand / 1.0-exp。
- Known Four Pillars 只建立 Bazi imported/external natal view，不反推完整 Ziwei natal。
- Astralium 為可選 external qualification source，不是 runtime dependency。

### Normalized Natal / reconciliation

- 新增 External / Project / Resolved 三層資料模型；raw views 永久分開，不互相覆寫。
- 固定 field status：`MATCH / EQUIVALENT / CONFLICT / NOT_COMPARABLE`。
- 固定 severity：`INFO / CAUTION / BLOCKING`。
- `natal.reconciliation` = implemented / stable / on_demand / 1.0。
- Experimental authority 發生實質 external conflict 時，Resolved 預設採 external；衝突狀態仍保留。

### Markdown / orchestration

- 新增 deterministic canonical Markdown exporter，只輸出 structured facts，不重算命盤、不猜 missing fields、不自動加入命理解讀。
- `natal.markdown_export` = implemented / stable / on_demand / 1.0。
- 新增 Mode A / B / C orchestration：Birth Data、Known Four Pillars、External + Project cross-check。

### Qualification / privacy

- 新增 Phase 2C0 aggregate qualification summary；只允許 aggregate counts、digests、versions、statuses。
- raw private birth input、full address、raw chart、external raw payload 不進 repo。
- Phase 2C0 final acceptance 仍由 Task 10 gate 決定；在正式 gate 前不宣稱 release PASS。
- `ziwei.flowing_stars` 仍為 **planned / on_demand**；Phase 2C0 不包含 moving stars。

## Unreleased｜Phase 2B

### Ziwei Fine Cycle Stem Resolver v1

- 新增 `engine/calendar/sexagenary.py` 中立干支 helper。
- 新增 `engine/ziwei/fine_cycle_stems.py`，固定 profile `ziwei-fine-cycle-lunar-late-zi-v1` / `1.0-exp`。
- 紫微流月 stem 採農曆月與閏月 15/16 分界；23:xx 不提前切換流月。
- 紫微流日固定 `late_zi_forward-v1`：22:59 舊日、23:00 effective date +1、00:00 不 double-rollover。
- 紫微流時使用 effective Ziwei day stem 起五鼠遁，hour branch 直接採 CalendarContext。
- 新增 `engine/ziwei/fine_cycle.py`，將 resolved stem 接入既有 Transformation / Flying Core。
- flow month/day/hour stem、transformations、flying = `implemented / experimental / on_demand / 1.0-exp`。
- Stable Transformation / Flying Core 與既有 palace maturity 不變；流曜仍 planned。

### Phase 2B qualification

```text
pinned lunar-lite 1d104fff...   18/18 PASS
pinned iztro 814b77e6...        integration PASS
Astralium fine-cycle             PENDING
```

- `leap_twelfth_month_second_half` 只有 synthetic internal coverage，為 not externally qualified。
- repo 不提交 Astralium raw private chart；只保存 aggregate PENDING state。
- 本段為 Unreleased 開發紀錄；`VERSION.md` 與 v1.2.0 release identity 不變。

## v1.2.0｜2026-08-21

v1.2.0 把引擎模組化、Calendar infrastructure、紫微細時間定位與 Ziwei Transformation & Flying Core v1 收斂成正式 release baseline。

### 引擎模組化

- 八字正式實作拆入 `engine/bazi/`。
- 紫微正式實作拆入 `engine/ziwei/`。
- Calendar Resolver 建立於 `engine/calendar/`。
- compatibility wrappers 保留既有入口；實際執行仍需同版 package modules。

### Capability 三軸模型

```text
implementation = planned / implemented
maturity       = experimental / stable
routing        = default / on_demand
```

正式狀態：

```text
紫微流月定位 = implemented / stable / default
紫微流日定位 = implemented / experimental / on_demand
紫微流時定位 = implemented / experimental / on_demand
Ziwei Transformation Core = implemented / stable / on_demand
Ziwei Flying Core = implemented / stable / on_demand
紫微流曜 = planned / on_demand
```

### Calendar Resolver v1

- structured civil datetime + IANA timezone → neutral `CalendarContext`。
- Runtime lunar provider 固定 `lunar-python==1.4.8`。
- Timezone data 固定 `tzdata==2026.3` / IANA 2026c。
- civil date 只在 00:00 換日；23:00 已屬子時，但 Resolver 不套命理日界。

### Ziwei Transformation / Flying Core

- 十天干四化 core。
- 本命十二宮宮干飛化。
- 生年、大限、流年四化／飛化。
- layer composition / conflict validation。

正式 v1.2.0 release identity 維持不變；後續 Unreleased Phase 2B / Phase 2C0 不提前改 VERSION、tag 或 GitHub Release。
