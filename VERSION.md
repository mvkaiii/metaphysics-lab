# Metaphysics Lab 版本

> `VERSION.md` 是給開發、驗證與版本治理看的**技術版本表**。第一次使用請先看 `README.md` 或 `docs/快速開始.md`；一般使用者版 v1.5.0 發布說明見 `docs/發布說明-v1.5.0.md`。
>
> v1.3.0 與更早版本屬歷史 Release snapshot，不因後續 qualification 或文件更新回寫改造。v1.4.0 收斂 v1.3.0 之後已合併到 `main` 的 Project Contract / Case Schema 1.1、Portable Offline Natal、Historical Blind Calibration 與細時間 qualification；release 本身不改變 capability maturity。

## 最新正式發布

- Metaphysics Lab Core：**v1.4.0**
- 發布日期：**2026-08-26**
- v1.4.0 為目前已建立 Git tag / GitHub Release 的正式版本。

## 目前發行候選

- **v1.5.0 Release Candidate**
- 狀態：`PENDING_FINAL_QUALIFICATION`
- Release baseline：林氏天機 v1.5 Phase 1–6 + 林氏天機預測驗證 + v1.5 發行面驗證 + v1.5 隔離沙盒對話驗證 + v1.5 最終發行資格驗證

主要元件：

- 命理推導計算規則：v1.4
- 八字時間推導引擎：v1.0.0
- 紫微流月定位引擎：v1.0.0
- 紫微流日定位引擎：v1.0.0-exp
- 紫微流時定位引擎：v1.0.0-exp
- Calendar Resolver：v1.0.0
- Ziwei Transformation Core：v1.0.0
- Ziwei Flying Core：v1.0.0
- Natal Foundation：v1.0-exp
- Ziwei Fine Cycle：v1.0-exp
- Ziwei Flowing Stars：v1.0-exp
- Historical Activation Selector：v1.0-exp
- AI Distribution Runtime：v1.1-exp
- Runtime Schema：v1.1
- Build Format：v1.1
- Project Contract：v1.1
- Case Schema：v1.1
- 問事追蹤制度：v1.0

---

## v1.5.0 Release Candidate Capability 狀態

目前執行能力的權威來源是 `runtime_info`。以下是本次 Release Candidate snapshot；**release 本身不改變 capability maturity**。

| Capability / Layer | Implementation | Maturity | Routing / Role |
|---|---|---|---|
| 八字時間推導（流年／流月／流日／流時） | implemented | stable | default |
| Birth input / location / true solar time | implemented | experimental | on_demand |
| `bazi.natal_chart` | implemented | experimental | on_demand |
| `ziwei.natal_chart` | implemented | experimental | on_demand |
| `natal.reconciliation` | implemented | stable | on_demand |
| `natal.markdown_export` | implemented | stable | on_demand |
| `historical.activation_selector` | implemented | experimental | on_demand |
| `ziwei.flow_month_palaces` | implemented | stable | default |
| `ziwei.flow_day_palaces` | implemented | experimental | on_demand |
| `ziwei.flow_hour_palaces` | implemented | experimental | on_demand |
| `ziwei.transformations` | implemented | stable | on_demand |
| `ziwei.flying` | implemented | stable | on_demand |
| 紫微流月／流日／流時 stem | implemented | experimental | on_demand |
| 紫微流月／流日／流時 transformations | implemented | experimental | on_demand |
| 紫微流月／流日／流時 flying | implemented | experimental | on_demand |
| `ziwei.flowing_stars` | implemented | experimental | on_demand |
| Cross-System Validation | planned | — | — |
| 奇門自動排盤引擎 | planned | — | — |

`Experimental / On-demand` 代表能力已有可執行 Python 與驗證紀錄，但一般問事不預設執行，分析時必須依 evidence / qualification 降權。

`Stable / On-demand` 代表能力已通過既定 promotion gate，但仍不代表每次問事都要預設執行。

---

## v1.5.0 Release Candidate Distribution / Contract Snapshot

v1.5.0 Release Candidate 收斂下列 distribution / data contract：

```text
Project Contract          1.1
Case Schema               1.1
Runtime Schema            1.1
AI Distribution Runtime   1.1-exp
Build Format              1.1
```

Project Contract 1.1 / Case Schema 1.1 的重點：

- 使用 opaque `subject_id` 與 subject-aware filenames，降低多人 Case 混用風險。
- 新 Case 採 Progressive Case：`00`～`04` 為 Base Case；`05`～`08` 有實際紀錄才 materialize。
- Legacy Case 1.0 保持 readable；升級不要求破壞性重建或強制 rename。
- Candidate Envelope 對 unknown / bounded birth-time uncertainty 不使用 midpoint、default time 或 majority voting 製造假精度。
- Historical Blind Calibration 先建立可重現的 canonical selection 與 blind lock，再使用已確認事件校準。
- 一般使用者回答將內部 calibration state 與工程實作詞翻成白話；只有明確要求技術檢查時才展開 schema / validator / raw field 等細節。

Portable Offline Natal：

- bundled core 固定 `lunar-python==1.4.8`。
- bundled timezone data 固定 `tzdata==2026.3` / IANA `2026c`。
- 內建有限、版本化的 offline birth-place registry。
- location precedence：完整 `resolved_location` → offline registry → explicit opt-in network fallback。
- offline registry miss 預設 fail closed；ambiguous alias 不讓網路結果偷偷覆蓋。
- single-file bundle 使用固定 source digest、per-record SHA256、preflight 與 5 MiB size guard。
- clean `python -S`、no-network、public-package pollution 與 modular ↔ bundled parity 已納入 qualification / regression。

---

## v1.5.0 Release Candidate Qualification Snapshot

### Natal Foundation

```text
Bazi private case       PASS：6 direct matches / 3 explicit profile differences / 0 unexpected mismatch
Ziwei private case      PASS：129 matches / 1 equivalent / 0 unexpected mismatch
promotion_allowed       false
```

單一 private case 不構成 capability promotion 依據；`bazi.natal_chart` 與 `ziwei.natal_chart` 仍為 Experimental。

### Bazi Flow Day / Hour

現有八字流日／流時公式沒有因 qualification 被改寫。公開 qualification 已鎖定代表日期、23:00 early-Zi、Gregorian transition、五鼠遁、連續日、DST responsibility 與 modular ↔ generated runtime parity；qualification PASS 不等於命理預測正確性的證明。

### Ziwei Fine Cycle Day / Hour

現有 `ziwei-fine-cycle-lunar-late-zi-v1` / `late_zi_forward-v1` 維持：

```text
pinned lunar-lite 1d104fff...   18/18 PASS
pinned iztro 814b77e6...        integration PASS
Astralium fine-cycle             PENDING
```

另有 pinned `lunar-python==1.4.8` 的流日／流時 qualification，覆蓋 late-Zi、五鼠遁、Gregorian transition、DST responsibility 與 modular ↔ generated runtime parity。Fine Cycle stem / transformations / flying 仍是 Experimental / On-demand。

### Ziwei Month Boundary

v1.4.0 納入 PR #175 已合併的月層 qualification：

```text
month-oracle checks              86
unexpected mismatch              0
ordinary lunar months            72 cases
real leap day15/day16            14 cases / 7 leap-month years
ordinal 13 -> next year month 1  10/10 property PASS
```

`leap_twelfth_month_second_half` 已不再只有 synthetic internal coverage：pinned `lunar-python==1.4.8` 對真實 1574 閏十二月顯示 day 15 為 `丁丑`，下一個實際農曆月為 1575 正月 `戊寅`，Project day 16 effective month source 亦為 `戊寅`。

Pinned lunar-lite 對閏十二月下半月本身仍有 direct-runtime oracle 限制；這個來源限制保留，不冒充已由 lunar-lite 直接驗證。Astralium fine-cycle 仍為 `PENDING`，也不因此 promotion。

### Ziwei Flowing Stars

```text
pinned iztro 2.6.0 / 814b77e6...   600/600 source cases PASS
placements                         6120
unexpected mismatch                0
Astralium flowing-stars            PENDING
promotion_allowed                  false
```

### Ziwei Transformation & Flying Core

```text
pinned iztro 十干四化             40/40 PASS
私有 Astralium 十干四化           40/40 PASS
Astralium 本命飛化                48/48 PASS
Astralium 大限飛化                 4/4 PASS
Astralium 2023–2029 流年飛化      28/28 PASS
Astralium flying total             80/80 PASS
Astralium-compatible presentation  11/11 PASS
```

Private Astralium raw chart、raw birth input、完整住址與 normalized private qualification input 不存共用 repo；repo 只保存 aggregate evidence、digests、versions 與 statuses。

---

## v1.5.0 Release Acceptance Gate

正式 tag 前必須在 release candidate exact head / merged `main` 上重新確認：

```text
Bazi flow-time qualification --check       PASS
Ziwei flow-time qualification --check      PASS
Ziwei month-boundary qualification --check PASS
Deterministic distribution build/check     PASS
林氏天機 v1.5 focused regression       PASS
Full repository regression                 PASS
Python 3.9 compileall                       PASS
Clean validation tree                      PASS
林氏天機預測驗證                           PASS
v1.5 發行面驗證                            PASS
v1.5 隔離沙盒對話驗證                     PASS
```

實際最終 test count、workflow run 與 artifact digest 以 release-preparation PR 的最終驗證紀錄為準；不得在驗證前預填成功數字。

---

## AI Distribution Pack

v1.5.0 Release Candidate 提供 mobile-first AI release surface：

```text
dist/ai/metaphysics_lab.py
dist/ai/metaphysics_core.md
dist/ai/project_instructions.txt
```

一般使用者不需要理解 repo modules。前兩個檔案上傳到 ChatGPT / Claude Project，`project_instructions.txt` 內容貼入 Project Instructions；完整分析若平台提供，可優先使用較高推理強度模式。

從 v1.4.0 升級到 v1.5.0 時，Project Contract / Case Schema 仍維持 1.1；同步三個發行檔即可，既有私人 Case 與舊 prospective lock 不要求清空、破壞性重建或 schema migration。

AI Distribution Runtime 目前版本為 `1.1-exp`；正式 GitHub Release 不把它或任何 experimental metaphysics capability 自動升 Stable。

---

## Runtime / Compatibility

- Python：3.9 以上
- Calendar Resolver lunar provider：`lunar-python==1.4.8`
- Timezone provider：`tzdata==2026.3` / IANA `2026c`
- Optional location packages：`geopy==2.5.0`、`timezonefinder==8.2.0`
- Calendar Resolver Gregorian→Lunar HKO validated range：`1901-01-01..2100-12-31`
- `2057-09-28..2057-10-27`：`boundary_conflict`
- `2089-09-04`、`2097-08-07`：`boundary_caution`
- 23:00 已屬子時，但 Resolver civil date 只在 00:00 換日
- 八字 23:00 early-Zi 仍由八字引擎負責
- 紫微 fine-cycle 日界採其固定 profile，不讓 Calendar Resolver 代替決定命理日界

---

## 版本治理規則

`VERSION.md` 只回答「目前正式有效的是什麼」。歷史與尚未發布變更請看 `CHANGELOG.md`，升級操作請看 `docs/更新與版本同步.md`。

以下變更必須留下版本歷程並重新跑對應 gate：

- 會改變命盤計算結果的規則
- 時間／日期邊界
- rule profile
- schema / data contract
- capability implementation / maturity / routing
- qualification source 或 promotion gate
- Project Contract / Distribution Runtime release surface

建議版本語意：

- patch：不改演算法語意的修正、文件錯誤、測試補強
- minor：新增正式 capability、啟用新的可執行規則層或正式 distribution surface
- major：破壞性 schema／API／核心規則相容性變更

正式 Git tag / GitHub Release 應在 release 文件 merge、main regression 完成後建立，避免 tag 指向尚未收斂的中間狀態。

---

## 歷史版本

### v1.3.0｜2026-08-23

- 把本命建立、Ziwei Fine Cycle / Flowing Stars 與 AI Distribution Pack 收斂成正式 release baseline。
- v1.3.0 發布當時 AI Distribution Runtime 為 `1.0-exp`，Project Contract / Case Schema 為 `1.0`。
- v1.3.0 發布當時 `leap_twelfth_month_second_half` 仍只有 synthetic internal coverage；這是歷史 snapshot，後續 v1.4.0 qualification 不回寫改造當時證據。
- 一般使用者版歷史發布說明：`docs/發布說明-v1.3.0.md`。

### v1.2.0｜2026-08-21

- 引擎正式模組化為 `engine/bazi/`、`engine/ziwei/` 與 `engine/calendar/`。
- 建立 Calendar Resolver v1。
- 收斂 Ziwei Transformation Core / Flying Core v1。
- 正式建立 implementation / maturity / routing 三軸 capability 模型。

### v1.1.0｜2026-08-20

- 正式加入紫微流月定位。
- 建立流年斗君、流月命宮、流月十二宮重排。
- 建立安裝、資料準備、更新同步與快速開始文件。

### v1.0.0｜2026-08-20

- 建立 Metaphysics Lab 共用核心架構。
- 建立問事「先盲判、後事件校準」制度。
- 建立八字流年、流月、流日、流時固定算法與測試基線。
