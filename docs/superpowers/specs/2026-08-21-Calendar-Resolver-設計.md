# Calendar Resolver 設計規格

- 日期：2026-08-21
- Branch：`design/calendar-resolver`
- 狀態：Design spec，等待使用者 review；尚未進入 implementation plan
- 分類：Architectural
- 第一版服務對象：Ziwei adapter
- 架構定位：System-neutral Calendar / Input Resolver

## 一、目的

Calendar Resolver 的目的，是把「民用時間與曆法正規化」從八字、紫微與未來奇門的命理核心公式中抽離，提供一個固定、可追溯、可驗證的 `CalendarContext`。

第一版資料流：

```text
使用者自然語言
        ↓
ChatGPT / Skill / Agent
        ↓
已解析的 civil_datetime + IANA timezone + optional utc_offset_hint
        ↓
Calendar Resolver
        ↓
CalendarContext
        ↓
Ziwei Adapter
        ↓
既有 engine.ziwei.month / day / hour
```

本 subsystem 架構必須保持 system-neutral，但第一版只正式整合 Ziwei；不得為了同時接 Bazi 或 Qimen 而擴大第一版 scope。

核心原則：

> Resolver 處理民用 datetime、timezone、DST、Gregorian→Lunar 與時辰地支。
>
> 命理日界與各體系公式由各自 adapter / engine 負責。
>
> 「算得出來」與「Project 已驗證」必須分開表示。

---

## 二、Scope

### 2.1 第一版必須實作

Calendar Resolver 第一版接受：

```text
civil_datetime
IANA timezone
optional utc_offset_hint
```

並產生：

```text
normalized local datetime
UTC datetime
UTC offset
Gregorian civil date
hour branch
Gregorian → Lunar conversion
provider provenance
validation metadata
policy metadata
```

第一版並建立 Ziwei adapter，將 `CalendarContext` 中可信任的：

```text
lunar.month
lunar.day
lunar.is_leap_month
normalized_time.hour_branch
```

轉交既有 Ziwei month/day/hour core。

### 2.2 第一版不實作

以下明確 out of scope：

- 自然語言時間解析。
- timezone 自動猜測。
- `CST`、`EST`、`GMT+8`、`+08:00` 等非 IANA timezone 輸入。
- location geocoding。
- 真太陽時。
- 八字 engine refactor。
- 紫微 23:00 換日流派選擇。
- Qimen integration。
- 紫微四化。
- 流曜。
- 細層飛化。
- AI interpretation。
- 將官方 HKO / CWA 資料作為 runtime provider。

---

## 三、Architectural Boundaries

### 3.1 Resolver 負責

Resolver 只負責「民用時間與共用曆法上下文」：

- 驗證 `civil_datetime` 格式。
- 驗證 IANA timezone identifier。
- 使用 pinned timezone provider 建立 local datetime。
- 處理 DST nonexistent / ambiguous local time。
- 使用 optional `utc_offset_hint` 解析 ambiguous local time。
- 產生 local datetime、UTC datetime、UTC offset。
- 產生 Gregorian civil date。
- 依民用時鐘計算 `hour_branch`。
- Gregorian → Lunar conversion。
- 正規化閏月表示。
- 附加 provider provenance。
- 附加 validation status / profile / boundary metadata。
- 明確聲明 `metaphysics_day_boundary_applied = false`。

### 3.2 Resolver 不負責

Resolver 不得處理任何特定命理體系的日界：

- 不把八字 `23:00 early-Zi` 套到 Gregorian / Lunar civil date。
- 不決定紫微 23:00 是否換日。
- 不決定奇門日界。
- 不因 `hour_branch = 子` 就將日期自動推進一天。

因此：

```text
2026-09-18 23:30 Asia/Taipei
```

在 Resolver 中必須仍有：

```text
gregorian_date = 2026-09-18
hour_branch = 子
metaphysics_day_boundary_applied = false
```

若 Bazi 需要 23:00 換日，必須在 Bazi adapter / engine 層另外套用。

### 3.3 既有 Ziwei core 邊界不變

現有：

```text
engine/ziwei/month.py
engine/ziwei/day.py
engine/ziwei/hour.py
```

仍然只接受已解析的農曆資料與時辰地支，不吸收 timezone / DST / Gregorian conversion 邏輯。

Calendar Resolver 的加入不得讓 `day.py` 或 `hour.py` 反向依賴 timezone provider。

---

## 四、Natural-Language Parsing Boundary

Calendar Resolver 不接受自然語言。

例如：

```text
「明天下午兩點」
「晚上七點左右」
「台灣時間下午兩點」
```

必須由 ChatGPT / Skill / Agent 上層先解析成：

```json
{
  "civil_datetime": "2026-09-18T14:00:00",
  "timezone": "Asia/Taipei"
}
```

Resolver 從結構化 civil input 開始。

第一版 `civil_datetime` 必須是不含 embedded UTC offset 的 local civil datetime；timezone 由獨立 `timezone` 欄位指定。

例如以下第一版不接受：

```text
2026-09-18T14:00:00+08:00
```

避免同時存在 embedded offset 與 IANA timezone 時發生來源衝突。

---

## 五、CalendarContext Data Contract

採用 B 型資料模型：**算法結果與驗證狀態完全分離。**

也就是：

```text
provider 能計算
```

不等於：

```text
Project 已驗證
```

第一版邏輯契約：

```text
CalendarContext
├─ schema_version
├─ resolver_version
│
├─ input
│  ├─ civil_datetime
│  ├─ timezone
│  └─ utc_offset_hint?
│
├─ normalized_time
│  ├─ local_datetime
│  ├─ utc_datetime
│  ├─ utc_offset
│  ├─ gregorian_date
│  ├─ timezone
│  └─ hour_branch
│
├─ lunar
│  ├─ year
│  ├─ month
│  ├─ day
│  └─ is_leap_month
│
├─ providers
│  ├─ lunar_calendar
│  │  ├─ name
│  │  ├─ version
│  │  └─ source_revision
│  │
│  └─ timezone_database
│     ├─ name
│     ├─ package_version
│     ├─ tzdb_version
│     └─ source_revision
│
├─ validation
│  ├─ calendar_conversion
│  │  ├─ status
│  │  └─ profile
│  ├─ timezone_normalization
│  │  ├─ status
│  │  └─ profile
│  ├─ overall_status
│  ├─ validated_range
│  ├─ boundary_id
│  └─ notes
│
└─ policies
   ├─ timezone_basis
   ├─ lunar_date_boundary
   ├─ hour_branch_basis
   └─ metaphysics_day_boundary_applied
```

### 5.1 Schema / resolver version

第一版必須從一開始保留：

```text
schema_version
resolver_version
```

兩者用途不同：

- `schema_version`：資料契約是否相容。
- `resolver_version`：實作版本與演算法行為追溯。

不得只用一個模糊 `version` 同時代表兩者。

### 5.2 Lunar 閏月表示

不得把 `lunar-python` 的負月份格式外洩。

禁止：

```json
{
  "month": -6
}
```

正式輸出：

```json
{
  "year": 2025,
  "month": 6,
  "day": 1,
  "is_leap_month": true
}
```

`month` 永遠是正整數 `1..12`，閏月狀態只由 `is_leap_month` 表示。

---

## 六、Lunar Provider Architecture

第一版採 provider interface：

```text
Calendar Resolver
        ↓
LunarCalendarProvider
        ↓
lunar-python 1.4.8
```

Provider interface 必須讓上層 Resolver 不依賴 `lunar-python` 的特殊資料表示法。

建議最小責任：

```text
Gregorian civil date
        ↓
LunarDate(year, month, day, is_leap_month)
```

Provider failure 必須轉換成 Resolver 的 error contract，不直接把第三方 exception 當 public API。

---

## 七、lunar-python Provenance

第一版 runtime provider 固定：

```text
name = lunar-python
version = 1.4.8
source_revision = 000c8a3d74eed098d6256a28fdd51b869324c559
```

版本資訊必須進 `CalendarContext.providers.lunar_calendar`。

不得只記 `lunar-python` 而漏掉 version / revision，否則未來 provider 升級後無法追溯舊結果。

---

## 八、HKO Exhaustive Validation Evidence

Provider qualification 已完成兩階段驗證；這些 probe 是一次性研究證據，不進 `main`。

正式可採信的 exhaustive profile：

```text
1901-01-01 ～ 2100-12-31
```

共：

```text
73,049 daily rows
```

兩條 provider 安裝路徑各自完整執行：

```text
PyPI lunar_python==1.4.8
exact source commit 000c8a3d74eed098d6256a28fdd51b869324c559
```

結果：

```text
strict mismatches = 0
```

因此 Project 可正式定義：

> `1901-01-01 ～ 2100-12-31` 為 Gregorian→Lunar 的 HKO exhaustive validated range，但必須排除／標示已知 HKO boundary cases；不得延伸宣稱 2100 年以後亦已驗證。

Validation profile 名稱第一版固定：

```text
hko-gregorian-lunar-1901-2100-v1
```

---

## 九、CWA Secondary Validation Role

台灣中央氣象署 CWA 定位為：

```text
Taiwan official secondary/manual validation source
```

第一版不把 CWA 當 runtime dependency，也不宣稱已完成 CWA exhaustive automation。

CWA 用途：

- 台灣場景的官方 secondary validation。
- 重要 boundary case 的人工覆核。
- 未來新增 validation profile 時的交叉來源。

HKO 與 CWA 的角色不得混稱。

---

## 十、Validated Range 與 Status Model

第一版 validation status 固定四種：

```text
validated
boundary_caution
boundary_conflict
out_of_validated_range
```

### 10.1 `validated`

條件：

- Gregorian date 落在 `1901-01-01 ～ 2100-12-31`。
- 不屬已知 boundary caution / conflict。
- Provider 正常產生結果。

### 10.2 `boundary_caution`

官方資料已標記天文敏感點，但目前 exhaustive comparison 沒有 provider mismatch。

目前已知：

```text
2089-09-04
2097-08-07
```

這些日期必須保留 warning metadata，不可因「目前剛好一致」就當作普通 validated date。

### 10.3 `boundary_conflict`

實際 exhaustive comparison 已確認 provider 與 HKO oracle 不同。

目前固定 conflict window：

```text
2057-09-28 ～ 2057-10-27
```

共 30 天。

行為：

- Resolver 仍可回傳 runtime provider 的 lunar result。
- `ok = true`。
- `validation.calendar_conversion.status = boundary_conflict`。
- `overall_status` 不得為 `validated`。
- 必須附 `boundary_id` 與說明 provider / oracle 已知衝突。
- 不得偷偷改用 HKO 結果覆蓋 runtime provider。
- 不得偷偷忽略差異。

第一版建議 boundary id：

```text
hko-new-moon-2057-09-28-conflict
```

### 10.4 `out_of_validated_range`

例如：

```text
2150-03-01
```

如果 provider 仍可計算：

```text
ok = true
validation.calendar_conversion.status = out_of_validated_range
```

不能把「沒有 Project validation evidence」誤寫成 provider error。

如果 provider 根本不能計算，才回：

```text
ok = false
error.code = provider_unsupported_date
```

---

## 十一、Timezone Provider Architecture

第一版使用：

```text
Python zoneinfo
+
pinned tzdata package
```

Provider provenance 固定：

```text
package = tzdata
package_version = 2026.3
IANA tzdb version = 2026c
source_revision = a44279419071b7aa41ebe7eca301ebb2e759571a
```

Qualification 已使用：

```text
PYTHONTZPATH=""
```

並確認：

```text
ZoneInfo TZPATH = ()
```

代表驗證使用 pinned `tzdata`，而不是 GitHub runner 的 system tzdb。

Implementation / CI 必須保留同等級的可重現性；不得在測試結果中混用未知版本的 OS timezone database，卻仍宣稱符合 pinned timezone profile。

---

## 十二、Timezone Input Contract

第一版只接受 IANA timezone identifier，例如：

```text
Asia/Taipei
America/New_York
Europe/London
Asia/Tokyo
```

第一版拒絕：

```text
CST
EST
台灣時間
GMT+8
+08:00
```

理由：

- 縮寫可能有多重地理意義。
- 固定 offset 無法表達 DST 與歷史規則。
- Resolver 不猜 location / timezone。

`Asia/Taipei` 也不得寫死為 `+08:00`；必須透過 timezone database 取得目標日期的正確 historical offset。

---

## 十三、DST Nonexistent / Ambiguous Rules

### 13.1 Nonexistent local time

例如：

```text
America/New_York
2026-03-08 02:30
```

spring-forward gap 中此 local time 不存在。

Resolver 必須：

```text
ok = false
error.code = nonexistent_local_time
```

不得自動：

```text
02:30 → 03:30
```

因為自動修正會改變使用者實際指定的時間語意。

### 13.2 Ambiguous local time

例如：

```text
America/New_York
2026-11-01 01:30
```

此 local time 存在兩次：

```text
-04:00 → 2026-11-01T05:30:00Z
-05:00 → 2026-11-01T06:30:00Z
```

如果沒有 `utc_offset_hint`：

```text
ok = false
error.code = ambiguous_local_time
```

`error.details` 必須列出所有合法候選 offset / UTC instant，讓呼叫端可以選擇。

Resolver 不得自己選 fold=0 或 fold=1。

---

## 十四、utc_offset_hint Contract

`utc_offset_hint` 只用於 ambiguous local time 消歧義。

例如：

```json
{
  "civil_datetime": "2026-11-01T01:30:00",
  "timezone": "America/New_York",
  "utc_offset_hint": "-04:00"
}
```

若 `-04:00` 是合法候選，Resolver 使用對應 instant。

若 hint 格式合法，但不是該 ambiguous local time 的候選 offset：

```text
ok = false
error.code = invalid_utc_offset_hint
```

如果 local time 本身不 ambiguous，`utc_offset_hint` 不得成為另一條強制覆寫 timezone database 的路徑；timezone database 仍是 authoritative source。

---

## 十五、Historical Timezone Support

第一版不得把 timezone support 定義成只支援現代日期。

Qualification 已確認 `Asia/Taipei` 包含歷史 offset 變化，例如：

```text
1937 前後 UTC+8 / UTC+9 變化
1945 回到 UTC+8
歷史 Taiwan DST cases
```

因此 Resolver 必須永遠依 IANA tzdb target-date rule 正規化時間，而不是依現在時區狀態回填歷史日期。

---

## 十六、23:00 / 00:00 Rule

Calendar Resolver 的 hour-branch mapping：

```text
23:00–00:59 = 子
01:00–02:59 = 丑
03:00–04:59 = 寅
05:00–06:59 = 卯
07:00–08:59 = 辰
09:00–10:59 = 巳
11:00–12:59 = 午
13:00–14:59 = 未
15:00–16:59 = 申
17:00–18:59 = 酉
19:00–20:59 = 戌
21:00–22:59 = 亥
```

Boundary examples：

```text
22:59 → 亥
23:00 → 子
23:59 → 子
00:00 → 子
00:59 → 子
01:00 → 丑
```

但 Gregorian civil date 只在 local `00:00` 換日。

因此：

```text
23:30
```

只能代表：

```text
hour_branch = 子
gregorian_date = 當日
```

不能在 Resolver 內變成隔日。

---

## 十七、Metaphysical Day-Boundary Separation

`CalendarContext.policies.metaphysics_day_boundary_applied` 第一版固定：

```text
false
```

目的：防止任何 consumer 誤以為 Resolver 已替某個命理體系處理換日。

後續責任：

```text
CalendarContext
        ↓
Bazi Adapter
→ 八字 23:00 early-Zi policy

CalendarContext
        ↓
Ziwei Adapter
→ 紫微未來正式驗證後的 day-boundary policy

CalendarContext
        ↓
Qimen Adapter
→ 奇門自己的時間／日界規則
```

Architecture hard rule：

> 不得把八字 `23:00` policy 自動套到紫微或其他體系。

---

## 十八、Error Contract

第一版 public error code 固定：

```text
invalid_datetime
invalid_timezone
nonexistent_local_time
ambiguous_local_time
invalid_utc_offset_hint
provider_unsupported_date
provider_failure
```

基本格式：

```json
{
  "ok": false,
  "error": {
    "code": "...",
    "message": "...",
    "details": {}
  }
}
```

### 18.1 `invalid_datetime`

包含：

- 無法解析的 structured datetime。
- embedded UTC offset 不符合第一版 contract。
- 缺少必要 local civil time components。

### 18.2 `invalid_timezone`

包含：

- 非 IANA identifier。
- IANA identifier 不存在於 pinned tzdb。

### 18.3 `provider_failure`

只用於不可預期 provider failure。

不得把：

- out-of-validated-range
- boundary conflict
- DST ambiguity

都粗暴包成 `provider_failure`。

---

## 十九、Validation 必須拆兩層

Calendar validation 與 timezone validation 不得共用一個模糊 PASS。

正式結構：

```text
validation
├─ calendar_conversion
│  ├─ status
│  └─ profile
│
├─ timezone_normalization
│  ├─ status
│  └─ profile
│
└─ overall_status
```

Calendar profile：

```text
hko-gregorian-lunar-1901-2100-v1
```

Timezone profile 第一版固定命名：

```text
tzdata-2026.3-iana-2026c-v1
```

`overall_status` 必須由兩個子 validation 組合，不可只因 lunar conversion 是 `validated` 就宣稱整個 `CalendarContext` 已驗證。

第一版 overall status precedence：

```text
boundary_conflict
    > boundary_caution
    > out_of_validated_range
    > validated
```

若任一子系統產生 fatal error，則不建立成功的 `CalendarContext`，直接使用 error contract。

---

## 二十、Ziwei First-Adapter Scope

第一版只正式建立 Ziwei adapter。

資料流：

```text
CalendarContext
        ↓
Ziwei Calendar Adapter
        ↓
trusted lunar_month
trusted lunar_day
trusted is_leap_month
trusted hour_branch
        ↓
engine.ziwei.month / day / hour
```

### 20.1 Adapter 可以做

- 從 `CalendarContext` 取出 Ziwei core 已需要的欄位。
- 檢查 CalendarContext 是否成功解析。
- 檢查 calendar conversion validation metadata。
- 將 validation / boundary metadata保留在上層 structured output。
- 呼叫現有 Ziwei core。

### 20.2 Adapter 不可以做

- 修改 lunar date。
- 自己再算 Gregorian→Lunar。
- 自己重新解析 timezone。
- 套用八字 23:00 policy。
- 決定尚未正式驗證的紫微 23:00 換日規則。

### 20.3 Boundary conflict 對 Ziwei 的行為

`boundary_conflict` 代表 provider 與 validation oracle 已知不一致。

第一版 adapter 不得偷偷替使用者選另一份 lunar date。

建議：

- Resolver 成功回傳 provider result + conflict metadata。
- Ziwei adapter 預設拒絕把 `boundary_conflict` 當成無警告 trusted input 執行高精度推導。
- 若未來要支援 explicit override，另開 design，不在第一版新增隱藏開關。

---

## 二十一、建議模組邊界

Implementation plan 可依 repo 現況調整實際檔名，但責任邊界應維持：

```text
engine/calendar/
├── __init__.py
├── resolver.py
├── models.py
├── timezone.py
└── lunar.py

engine/ziwei/
└── calendar_adapter.py
```

概念責任：

- `models.py`：CalendarContext / error / provider metadata / validation models。
- `timezone.py`：IANA timezone normalization、DST ambiguity/nonexistence、offset hint、hour branch。
- `lunar.py`：LunarCalendarProvider abstraction 與 lunar-python implementation。
- `resolver.py`：orchestration；組合 timezone + lunar + validation metadata。
- `ziwei/calendar_adapter.py`：只把 CalendarContext 對接既有 Ziwei core。

不得把全部邏輯塞進一支大型 `resolver.py`。

---

## 二十二、Dependency / Reproducibility Policy

目前 repo 的八字 engine 可自包含執行，但 Calendar Resolver 第一版允許新增 runtime dependency，因已明確選定：

```text
lunar-python 1.4.8
tzdata 2026.3
```

Implementation 前必須先確認 repo 採用哪一種 Python dependency manifest；若 repo 尚未有正式 dependency management，implementation plan 必須先定義最小、單一、可重現的安裝方式，不得同時加入多套互相競爭的 manifest。

CI qualification / unit test 若要宣稱 reproducible profile，必須確保實際使用 pinned provider versions。

---

## 二十三、Testing Strategy

測試分四層，且每個小流程必須 PASS 才能進下一層。

### Gate 1｜Pure unit tests

至少涵蓋：

- valid IANA timezone。
- invalid timezone。
- ordinary local→UTC conversion。
- Gregorian civil midnight date boundary。
- hour branch boundaries：22:59 / 23:00 / 00:00 / 00:59 / 01:00。
- leap-month normalization。
- provider metadata。
- validation status mapping。
- error contract。

**Gate 1 PASS 才能進 Gate 2。**

### Gate 2｜DST / Historical timezone tests

至少涵蓋：

- New York spring-forward nonexistent time。
- New York fall-back ambiguous time。
- ambiguous candidates exact offsets / UTC instants。
- valid `utc_offset_hint`。
- invalid `utc_offset_hint`。
- local→UTC→local round-trip。
- Asia/Taipei historical offset cases。

**Gate 2 PASS 才能進 Gate 3。**

### Gate 3｜Lunar validation contract tests

至少涵蓋：

- ordinary validated date。
- leap month case。
- validated-range first day。
- validated-range last day。
- 2057 conflict window start / middle / end。
- 2057 conflict window +1 day outside。
- 2089 caution date。
- 2097 caution date。
- date outside validated range but provider succeeds。
- provider unsupported date。

此 gate 不要求把 73,049-row exhaustive probe 永久塞進一般 unit test；exhaustive evidence 已在 qualification PR 留存。正式 repo 測試需保留 deterministic regression cases，避免 CI 成本失控。

**Gate 3 PASS 才能進 Gate 4。**

### Gate 4｜Ziwei adapter integration tests

至少涵蓋：

```text
civil datetime + timezone
        ↓
CalendarContext
        ↓
Ziwei adapter
        ↓
existing Ziwei month/day/hour result
```

需要確認：

- ordinary date 可正確傳入 lunar month/day/leap/hour branch。
- Resolver 沒有套用 metaphysical day boundary。
- `23:xx` 只改 hour branch，不偷改 lunar/civil date。
- `boundary_conflict` 不被 adapter 靜默視為 normal trusted input。
- existing Ziwei month/day/hour unit tests 全部維持 PASS。

**Gate 4 PASS 才視為第一版 implementation candidate 完成。**

---

## 二十四、Acceptance Gates

本 subsystem 強制採「小流程完成 → 實際驗證 → PASS → 下一步」規則。

禁止：

- 一次把 timezone、lunar、resolver、adapter 全部寫完後才第一次測。
- 前一層 FAIL 時先跳去做下一層。
- 為讓新程式通過而直接修改既有測試預期值。
- 把 provider qualification 證據當作 implementation tests 已通過。

每個 gate 的必要證據至少包含：

```text
執行指令
實際 test count / assertion groups
failures
errors
exit status
```

如果 FAIL：

1. 停在當前 gate。
2. 找 root cause。
3. 修正。
4. 重跑當前 gate。
5. PASS 後才繼續。

最後還必須跑完整 repo test suite，確認沒有 regression。

---

## 二十五、Provider Qualification 與 Product Tests 的區別

已完成的 temporary qualification PR：

```text
PR #4 lunar provider sample qualification
PR #5 lunar provider exhaustive qualification
PR #6 timezone normalization qualification
```

共同特徵：

- 都是研究／供應商 qualification。
- 都是 `closed`。
- 都是 `merged = false`。
- 不屬於產品 runtime code。

正式 implementation 不應把這些 temporary workflows / probe files 原封不動搬進 `main`。

需要保存的是：

- 已確認的 provider version。
- source revision。
- validation profile。
- validated range。
- boundary evidence。
- regression cases。

而不是保存一次性的 research scaffolding。

---

## 二十六、Migration / Future Bazi Integration

第一版**不得 refactor Bazi**。

現況：

```text
engine/bazi/calendar.py
```

已有自己的：

- 立春年界。
- 十二節月界。
- 23:00 early-Zi day rollover。
- 流時。
- timezone-aware calculation。

其中：

> 八字 `23:00` 換日是 Bazi Engine responsibility，不是 Calendar Resolver 共用 policy。

未來 Bazi integration 的正確方向：

```text
CalendarContext
        ↓
Bazi Adapter
        ↓
Bazi-specific effective date / solar-term policies
        ↓
engine.bazi.calendar
```

未來 migration 必須另外 design，逐步抽離重複的 civil-time normalization；不得在 Calendar Resolver 第一版同時改寫八字 engine。

---

## 二十七、Future Qimen Integration

Qimen 只列為未來 consumer，不在第一版實作。

Resolver 可以提供共用：

- normalized civil datetime。
- UTC instant。
- timezone provenance。
- Gregorian / Lunar context。
- hour branch。

但 Qimen 若需要：

- 特定日界。
- 真太陽時。
- 節氣遁局。
- 地點／方位。

皆由未來 Qimen adapter / engine 自行定義，不能預先塞進 neutral Resolver。

---

## 二十八、Failure / Risk Analysis

### 28.1 最大架構風險：日界污染

如果 Resolver 把 23:00 直接當「下一日」，會立即把 Bazi 特定政策污染到 Ziwei / Qimen。

防護：

```text
metaphysics_day_boundary_applied = false
```

加上 23:00 / 00:00 regression tests。

### 28.2 最大曆法風險：validation 與 computation 混為一談

如果 provider 算得出 2150，就寫成 validated，會製造不存在的驗證證據。

防護：

- computation result 與 validation metadata 分層。
- explicit `out_of_validated_range`。

### 28.3 最大 provider 風險：版本漂移

如果 runtime 自動升級 lunar-python / tzdata，歷史輸出可能改變但 provenance 無法追蹤。

防護：

- pinned versions。
- source revision metadata。
- deterministic tests。

### 28.4 最大 DST 風險：默默猜 fold / shift nonexistent time

防護：

- nonexistent → error。
- ambiguous → error + candidates。
- explicit offset hint only。

### 28.5 最大 scope 風險：第一版同時改 Bazi

防護：

- 第一版只接 Ziwei。
- Bazi migration 明確列入 future design。

---

## 二十九、Implementation Plan 前置條件

只有在本 spec 被使用者 review 並明確核准後，才可進入 `writing-plans`。

Implementation plan 必須：

1. 先確認 dependency manifest 策略。
2. 依 Gate 1 → Gate 4 拆成可獨立驗證的小步驟。
3. 每一步先寫／調整測試，再做實作。
4. 每個 gate PASS 才能進下一步。
5. 最後跑完整 repo test suite。
6. 不碰 Bazi refactor、Qimen、紫微 transformations / 流曜 / 細飛。

在 spec review 前不得開始 coding。

---

## 三十、第一版成功定義

Calendar Resolver v1 第一版只有在以下條件全部成立時才算完成：

- structured local civil datetime + IANA timezone 可正常解析。
- DST nonexistent / ambiguous 行為符合 contract。
- optional `utc_offset_hint` 可正確消歧義。
- Gregorian→Lunar 使用 pinned lunar-python 1.4.8。
- provider provenance 完整。
- validated range 與 boundary metadata 正確。
- 2057 conflict 不被隱藏。
- 2089 / 2097 caution 不被忽略。
- out-of-range 與 provider error 分開。
- hour branch 23:00 / civil date 00:00 邊界正確。
- `metaphysics_day_boundary_applied = false`。
- Ziwei adapter 可接現有 month/day/hour core。
- 不對 Bazi 進行 refactor。
- Gate 1～4 全部 PASS。
- 完整 repo test suite PASS。
- 文件與實際 contract 一致。

完成以上條件後，Calendar Resolver 才具備進入後續紫微 transformations roadmap 的 infrastructure 基礎。