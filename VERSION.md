# Metaphysics Lab 版本

> `VERSION.md` 是給開發、驗證與版本治理看的**技術版本表**。第一次使用請先看 `README.md` 或 `docs/快速開始.md`；一般使用者版 v1.9.0 發布說明見 `docs/發布說明-v1.9.0.md`。
>
> 歷史 Release snapshot 不因後續 qualification 或文件更新回寫改造。正式發版只固定 release identity；**release 本身不改變 capability maturity**，目前執行能力仍以 `runtime_info` 為技術權威來源。

## v1.9.0 Release Snapshot

v1.9.0 的 release identity / scope、Fresh-host qualification與RC freeze已於 **2026-10-03** 完成。Product RC為 `6529d34eb047c6fbbda3d85be83e211566e69565`，qualification receipt head為 `d85386fca2f3afb08076c3629f095223f5614e33`；正式tag / GitHub Release只允許在merged main SHA通過 `release-v1.9.yml` 完整驗證後建立。

```text
Release Version            1.9.0
Project Contract           1.3
Runtime Schema             1.1
Case Schema                1.1
AI Distribution Runtime    1.5-exp
Capability Manifest        1.0
```

- Birth-Time Domain Foundation把出生時間狀態固定為 `exact / bounded / unknown_time`；range、DST fold / gap與候選展開由runtime authority處理。
- Candidate Envelope升為 **v2 / 2.0-exp**，明確記錄candidate domain、coverage、materialized/unresolved occurrence與invariant/variant/undetermined boundaries。
- Project Contract升到 **1.3**，新增 `natal_revision_id` 與 `base_case_digest`；Case Schema仍為 **1.1**。
- Case Revision Integrity提供 `case.replace_natal_base`；Base Case 00～04可安全換版，05～08與revision lineage保留。
- Lock Provenance v2為新lock綁定subject、natal revision、Base Case digest、canonical sources與method version；歷史lock維持原bytes，不回填、不重簽。
- Guided Natal Build以 `natal.guided_build_state` 作為流程authority；AI不能自行挑選fold、中點或candidate。
- Visualization P1新增 `render_candidate_envelope_summary`；Candidate Envelope摘要可輸出deterministic SVG/text，但無ranking、probability、candidate-selection或predictive-evidence authority。
- Instructions/Core已切到runtime-owned state authority；固定文件不硬編Candidate Envelope或prediction method的動態版本。
- selector v1 / interpretation v1仍為default；prospective method identity仍為 `lin_tianji_v1.5-exp`。
- Experimental capability不因v1.9軟體release自動升級maturity。
- deterministic v1.9.0 User Package SHA256：`e263c25ea6efb8184a2d66c2bc2ce3edf31b29324152b2bccb9f96333aa504fa`。
- Project Instructions：7998字元，維持在ChatGPT Project 8000字元限制內。

---

## v1.8.0 Release Snapshot

v1.8.0 的 release identity / scope、RC freeze 與 release execution 已於 **2026-09-30** 由人工核准。Frozen product RC 為 `a0e0a1ca668e022a7c13f35875803d968f7547df`；正式 tag / GitHub Release 只允許在 PR #233 merged SHA 通過 `release-v1.8.yml` 的完整驗證後建立。

```text
Release Version            1.8.0
Project Contract           1.2
Runtime Schema             1.1
Case Schema                1.1
AI Distribution Runtime    1.4-exp
Capability Manifest        1.0
```

- Bazi Calendar Engine 已是 **1.1.0**，節氣 authority 採 bundled `lunar-python==1.4.8` JieQi table；這是工程精度修正，HKO benchmark 與 Task3 evidence 另有正式紀錄。
- Task3 v2.1 sealed qualification identity仍為 `bazi-natal-project-v1 / 1.0-exp`；本 candidate **不重新命名 rule identity**，以 calendar engine/provider/release provenance 區分實作版本。
- `bazi.natal_chart` 維持 **Experimental / On-demand**；Task3 只支持已封存的大運 implementation-conformance scope，不構成整體 capability Stable promotion。
- Visualization Chart Contract、Bazi decadal projection與SVG/text renderer已接入三檔AI Distribution；public action為 `render_bazi_decadal_timeline`，但仍是Experimental presentation surface，不改 `bazi.natal_chart` maturity。
- 一般命理對話採 `compact` 預設、`explain` 按需展開、`audit` 僅技術稽核；收斂只影響呈現，不改ranking、盲判、claim consumption或confidence。
- Selector v1 / interpretation v1 default不變；Case Schema 1.1、Project Contract 1.2、Runtime Schema 1.1不變。
- Pilot-6仍為 `OBSERVATION_PENDING`；v1.8 軟體 release 不會把 prospective evidence waiting period改寫成 Stable evidence。
- frozen product RC：`a0e0a1ca668e022a7c13f35875803d968f7547df`；後續release-infrastructure/public-doc candidate不得改User Package bytes，且必須重新通過exact-head hosted gates。
- deterministic v1.8.0 User Package SHA256：`f9b22d4b97949b873261793c404d2530a0bc384d77e970e1bba7aec35edc82cf`；正式release workflow會在merged SHA再次重建並核對此digest後才publish。
- Project Instructions：7873 字元，維持在 ChatGPT Project 8000 字元限制內。

---

## v1.7.1 Release Snapshot

v1.7.1 是已正式發布的 **release identity metadata patch**，發布日期為 **2026-09-25**（Asia/Taipei）。它不新增命理算法、不改 capability maturity，也不改 Case Schema；重點是讓 runtime 可以直接區分「整體 Release 版本」與「內部 Runtime component 版本」。

```text
Release Version            1.7.1
Project Contract           1.2
Runtime Schema             1.1
Case Schema                1.1
AI Distribution Runtime    1.2-exp
Capability Manifest        1.0
```

- `runtime_info` 新增 `release_version: 1.7.1`；`distribution_runtime_version` 仍為 `1.2-exp`。
- v1.7.0 → v1.7.1 只需要替換 `metaphysics_lab.py`；核心規則與 Project Instructions 不變。
- v1.6/v1.7 時期建立的 Case metadata 保留歷史 provenance，不因 patch 強制批次改寫。
- Selector v1、Interpretation v1 與所有 Experimental capability maturity / routing 全部維持 v1.7.0 狀態。
- deterministic v1.7.1 User Package SHA256：`771f8493cd07b298c7971f38c601ce17a8acfcce5dab43c72e245f7b282943e8`。
- 正式 release target 以 Git tag `v1.7.1` 指向的 commit 為 authority；歷史 `v1.7.0` tag / Release / assets 不回寫改造。

---

## v1.7.0 Release Snapshot

v1.7.0 是已正式發布的**可靠性與可用性版本**。正式 release target 為 `24760aa8766eb2691c8878f2cd8b97f0b37f8964`，受測 software candidate 為 `3153d5a49909094e16151c2cbbc487c2579dbff4`；發布日期為 **2026-09-24**（Asia/Taipei）。

```text
Project Contract          1.2
Runtime Schema            1.1
Case Schema               1.1
AI Distribution Runtime   1.2-exp
Capability Manifest       1.0
```

- **Case Schema 1.1 維持不變**；既有 Case 不需要破壞性重建，也不需要 schema migration。
- Historical Activation **selector v1** 與 Interpretation Contract **interpretation v1** 繼續作為正式 default；v1.7 發布本身不構成 v2 promotion。
- **Guided Inquiry** 是建議式導覽與追問導航，**不是新的命理證據**，不得提高既有盤面或 capability 的 specificity / confidence authority。
- Capability Manifest、Case Doctor、Prospective Validation 2.0 與 Guided Inquiry 的加入不會自動提升任何 Experimental capability maturity。

---

## 最新正式發布

- Metaphysics Lab Core：**v1.9.0**
- 發布日期：**2026-10-03**
- Git tag / GitHub Release：`v1.9.0`由 `release-v1.9.yml` 在merged main SHA完整驗證後建立；tag target是正式release identity authority。
- Product RC：`6529d34eb047c6fbbda3d85be83e211566e69565`；qualification receipt head：`d85386fca2f3afb08076c3629f095223f5614e33`。
- Project Contract / Runtime Schema / Case Schema：`1.3 / 1.1 / 1.1`。
- AI Distribution Runtime：`1.5-exp`。
- Candidate Envelope v2、Case Revision Integrity、Lock Provenance v2、Guided Natal Build與Visualization P1已進User Package runtime。
- 既有Project Contract 1.2 Case仍可讀；舊lock保持不可變，不回填provenance、不重簽、不重算digest。
- Selector v1 / interpretation v1保持default；prospective method identity仍為 `lin_tianji_v1.5-exp`。
- 未另行promotion的capability維持既有maturity；軟體release不等於預測效度promotion。
- deterministic v1.9.0 User Package SHA256：`e263c25ea6efb8184a2d66c2bc2ce3edf31b29324152b2bccb9f96333aa504fa`。

主要元件：

- 命理推導計算規則：v1.4
- Bazi Calendar Engine：v1.1.0
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
- AI Distribution Runtime：v1.5-exp
- Runtime Schema：v1.1
- Build Format：v1.1
- Project Contract：v1.3
- Case Schema：v1.1
- Capability Manifest：v1.0
- 問事追蹤制度：v1.0

---

## v1.6.0 Release Snapshot

- Metaphysics Lab Core：**v1.6.0**
- 發布日期：**2026-09-05**
- 正式 release commit：`c325d754112df71c6747e17262d2e781d2864441`
- 軟體 release 與 research-model promotion 分開管理；`promotion_allowed=false` 不因 v1.6.0 發布而改變。
- Historical Activation Selector 正式 default 仍是 v1；Interpretation Contract 正式 default 仍是 v1。
- Y1 年度紫微四化已納入正式軟體，但定位仍為 **Experimental / Project-derived**；這只證明 calculation path 可執行、可重現、受版本管理，不代表預測效度已被證明。
- Historical Calibration public runtime 現在要求 authoritative Case persistence；只有 blind set 真正持久化後，AI 才能說「已鎖定」並要求歷史事件。
- 正式受測 candidate：`b38cdf2bf9d2259d54b093adec03d960fa214733`；正式 release target：`c325d754112df71c6747e17262d2e781d2864441`。
- v1.6 isolated sandbox：Setup + P01～P11 PASS，八項 critical rubrics 全 PASS。
- deterministic v1.6.0 User Package SHA256：`30c6a4ff1dade6da2cdbf1b9d53463df4936c8a5b887d8a73cb1fbd2359c83eb`。

---

## v1.5.0 Capability Snapshot

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

## v1.5.0 Distribution / Contract Snapshot

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

## v1.5.0 Qualification Snapshot

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

```text
pinned lunar-lite 1d104fff...   18/18 PASS
pinned iztro 814b77e6...        integration PASS
Astralium fine-cycle             PENDING
```

Fine Cycle stem / transformations / flying 仍是 Experimental / On-demand。

### Ziwei Month Boundary

v1.4.0 納入的月層 qualification 保持有效歷史來源：

```text
month-oracle checks              86
unexpected mismatch              0
ordinary lunar months            72 cases
real leap day15/day16            14 cases / 7 leap-month years
ordinal 13 -> next year month 1  10/10 property PASS
```

`leap_twelfth_month_second_half` 已有 pinned `lunar-python==1.4.8` 的實際月序 continuity 支持；Astralium fine-cycle 仍為 `PENDING`，不因此 promotion。

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

## v1.5.0 Release Acceptance Gate｜已完成

正式 v1.5.0 已在 exact release candidate / merged `main` 完成：

```text
Bazi flow-time qualification --check       PASS
Ziwei flow-time qualification --check      PASS
Ziwei month-boundary qualification --check PASS
Deterministic distribution build/check     PASS
林氏天機 v1.5 focused regression           PASS
Full repository regression                 926/926 PASS
Python 3.9 compile check                    PASS
Clean validation tree                      PASS
林氏天機預測驗證                           12/12 PASS
v1.5 發行面驗證                            8/8 PASS
v1.5 隔離沙盒對話驗證                      8/8 critical rubrics PASS
```

正式 release target：`66f604222caadac0209125a78674c3f4491c4b99`。

AI distribution digest：`868d4e565715b8a35acbffe87ec41bf346b761decb4b29d4b6824311597946df`。

User Package SHA256：`a7fe693a8bd91f6b720409e5e23e655cc3bf13396e21c8b7f99f79bc2b23cbfc`。

---

## AI Distribution Pack

v1.6.0 正式沿用 mobile-first AI release surface：

```text
dist/ai/metaphysics_lab.py
dist/ai/metaphysics_core.md
dist/ai/project_instructions.txt
```

一般使用者不需要理解 repo modules。前兩個檔案上傳到 ChatGPT / Claude Project，`project_instructions.txt` 內容貼入 Project Instructions。

從 v1.5.0 升級到 v1.6.0 時，Project Contract / Case Schema 仍維持 1.1；建議同步三個發行檔，既有私人 Case、Historical Calibration 紀錄與 prospective lock 不要求清空、破壞性重建或 schema migration。

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

### v1.5.0｜2026-08-29

- 完成林氏天機 Phase 1–6、deterministic 三檔 User Package、12-case 預測驗證、發行面驗證與隔離沙盒 release gate。
- 正式 release target：`66f604222caadac0209125a78674c3f4491c4b99`。
- 一般使用者版歷史發布說明：`docs/發布說明-v1.5.0.md`。
- v1.5.0 的歷史 qualification / maturity snapshot 不因 v1.6.0 發布而回寫。

### v1.4.0｜2026-08-26

- 收斂 Project Contract / Case Schema 1.1、Portable Offline Natal、Historical Blind Calibration、Bazi / Ziwei 細時間 qualification 與一般使用者語言邊界。
- 規則與 capability maturity 的歷史狀態不因後續 v1.5.0 發布而回寫。
- 一般使用者版歷史發布說明：`docs/發布說明-v1.4.0.md`。

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
