# 變更紀錄

這份文件保存正式版本與尚未發布變更的技術紀錄。第一次使用 Metaphysics Lab 請先看 `README.md`；目前正式版本為 **v1.5.0｜2026-08-29**，一般使用者發布說明見 `docs/發布說明-v1.5.0.md`。

## v1.5.0｜2026-08-29

### 林氏天機 v1.5 正式收斂

- 完成 Phase 1–6：prospective lock、evidence model、eligibility/ranking、historical personalization、interpretation contract、prospective evaluation。
- 新增可證偽 Claim 契約：Primary 最多 3、Secondary 最多 2，明確 `matched_if / partial_if / not_matched_if`，並分開記錄 domain / event-family / timing 結果。
- 保持 Legacy Phase 1 lock 可讀；新 Claim 欄位採向後相容擴充，不要求 Case Schema 1.1 migration。
- `project_instructions.txt` 取代一般使用者發行面的 `.md`，方便手機／電腦直接開啟與複製；repo 內權威來源仍為 Markdown。
- 新增 deterministic three-file User Package：`Metaphysics-Lab-v1.5.0-User-Package.zip`，ZIP 內只能有 `metaphysics_lab.py`、`metaphysics_core.md`、`project_instructions.txt`。
- 新增 12-case 林氏天機預測驗證、v1.5 發行面驗證、v1.5 隔離沙盒對話驗證門檻與最終發行資格 workflow。
- 正式 release target commit：`66f604222caadac0209125a78674c3f4491c4b99`。
- 正式 release full repository regression：926/926 PASS；林氏天機預測驗證 12/12 PASS；v1.5 發行面驗證 8/8 PASS；隔離沙盒 critical rubrics 8/8 PASS。
- 不修改八字／紫微公式、Phase 3 ranking authority、Phase 4/5 邊界或 capability maturity。

### v1.5 開發歷史｜Phase 5 Interpretation Contract

- 新增 `distribution.interpretation_contract` / `build_interpretation_contract`，固定 profile `lin_tianji_interpretation_contract_v1-exp`，`ranking_authority=false`。
- Phase 3 `lin_tianji_rank_v1-exp` 維持唯一 base ranking authority；Phase 5 不重算 score、rank、maturity、specificity 或事件機率，也不新增或刪除 domain / event-family candidates。
- Phase 4 Historical Personalization 維持 presentation-only；Phase 5 可驗證 personalization、local windows 與 locked forecast，但不得回寫上游 authority。
- Local-window boundary 只能保留或降低 forecast specificity；另將 forecast specificity 與 strategy specificity 分開，現實背景只可讓策略更具體。
- Stage 1 blind / locked forecast 不得被 Stage 2 改寫；known reality 不得被包裝成 prospective hit。
- 一般使用者輸出以台灣繁體中文自然語言為主；engineering weights、thresholds、digests 與內部 explanation metadata 預設不外露。
- 新增 deterministic `interpretation_contract_digest`、runtime capability/action 與 modular ↔ portable bundle parity qualification。
- 本階段不提升任何既有 capability maturity、不新增命理公式，也不把 historical support、activation 或 ordinal modifier 包裝成 probability / accuracy。

### v1.5 開發歷史｜Phase 4 Historical Personalization

- 新增 `distribution.historical_personalization`：`implemented / experimental / on_demand`，profile `lin_tianji_historical_personalization_v1-exp`，`ranking_authority=false`。
- Phase 4 僅在 Phase 3 `lin_tianji_rank_v1-exp` base ranking 完成後運作；不得修改 `EvidenceFeature`、base ordinal score、specificity ceiling 或 `base_ranking_digest`。
- 歷史來源限定為 finalized Historical Calibration 的結構化欄位；實際事件自由文字、盲判 hypothesis、研究筆記不進 scoring，也不進 personalization source identity / digest。
- Domain personalization 只可重排 Phase 3 已打開的 domain；history 不得建立新 domain。每個 domain 至少 2 筆 eligible samples 才啟動，ordinal modifier 固定 bounded `-2..+2`。
- Event-family personalization 只可在該 domain 的既有 base candidates 內重排；不得新增或刪除 family，也不得提高 `allowed_specificity`。
- 同一 flow year 只讓第一筆有效 blind high-activation record 投票；contaminated、cannot-recall、control、multi-domain / multi-family aggregate、unmapped 與 unscorable material 不灌票。
- 無歷史、未校準或資料不足時保持 deterministic no-op，完整退回 Phase 3.5 + Phase 3 cold-start ordering。
- Runtime 新增 `personalize_ranking` action，payload 採 closed contract；未知 training/research 欄位 fail closed。
- 新增 modular ↔ portable bundle parity tests，鎖定 `base_ranking_digest` 與 `personalization_digest` 一致性。
- 本階段不提升任何既有 capability maturity，也不把 historical match 包裝成事件機率或預測準確率。

## v1.4.0｜2026-08-26

v1.4.0 正式收斂 v1.3.0 之後已合併到 `main` 的 Project Contract / Case Schema 1.1、Portable Offline Natal、Historical Blind Calibration、Bazi / Ziwei 細時間 qualification 與一般使用者語言邊界。**本版不因發版提升任何既有 capability maturity，也不改寫歷史 v1.3.0 qualification snapshot。**

### 一般使用者摘要

- 同一個 Project 可以更安全地管理多位命主，避免不同人的 Case 混在一起。
- 新 Case 採漸進式建立：先建立基礎資料，需要追蹤時才新增事件、流年、問事與重大決策紀錄。
- 出生時間未知或只有範圍時，不會自己猜中點或任意時辰；可保留候選狀態，只使用真正一致的資料。
- 第一次做個人化未來分析時，流程維持「先盲判、再用已確認事件校準」，避免先知道歷史答案再改第一版判斷。
- 首次建立流程採 **Birth Data first**；支援的 offline registry 地點可在不需要網路、不需要額外 Python 套件的環境建立 Project Natal。
- Astralium 是**可選** External Natal Source／交叉校驗來源，不是 Project Natal calculation authority，也不是首次建盤必要前置步驟。
- Legacy Case 1.0 維持可讀與可遷移；不要求使用者破壞性重建舊 Case。
- 一般回答新增 user-facing language boundary：內部 calibration state、validator、schema、migration、raw JSON field 等工程詞不直接當作一般使用者結論；除非使用者明確要求技術檢查。
- 紫微月層與流日／流時、八字流日／流時新增可重現 qualification；其中閏十二月下半月已獲 pinned lunar-python 的實際月序 continuity 支持。

### Project Contract 1.1 / Case Schema 1.1

- Project Contract / Case Schema 正式為 `1.1`；Runtime Schema 為 `1.1`，AI Distribution Runtime 為 `1.1-exp`，Build Format 為 `1.1`。
- Subject Identity 使用 opaque `subject_id` 作為命主權威識別，顯示名稱與檔名 label 可改但不得改變 identity。
- 新 Case 採 Progressive Case：第一次建立只產生 `00`～`04` Base Case；`05`～`08` 有實際紀錄時才建立。
- Candidate Envelope 完整掃描 unknown / bounded birth-time uncertainty，不使用 midpoint、default time 或 majority voting 製造假精度。
- Case record 使用 JSON typed semantics；非標準 `NaN / Infinity / -Infinity` fail closed。
- Legacy Case 1.0 舊 record ID 仍可讀；遷移到 1.1 時不符合新規則的 ID 會 deterministic remap 為固定長度 safe ID。
- Project Contract / Case Schema 既有批次經 post-merge adversarial audit、RED→GREEN regression 與 exact-head immutable CI 驗證後合併 PR #166。

### Historical Blind Calibration

- 新增 `historical.activation_selector`：`implemented / experimental / on_demand / 1.0-exp`。
- Selector 使用最近 10 個已完整結束的立春流年期，canonical selection 固定為 Top 4 High + Bottom 1 Control；已知事件與對話內容不能改 canonical selection。
- Ziwei yearly context 僅作 `support_only / ranking_authority=false`，不得改 Bazi selection digest。
- 第一次校準仍採先鎖盲判、後收事件；歷史 ground truth 不得回流改寫同一次 selector truth。
- 一般使用者校準狀態固定白話化；例如 `basic` 對外說「已完成初步校準」，不直接暴露內部 state code。

### Portable Offline Natal Pipeline

- Core calendar authority 改為 bundle 內固定 bytes：`lunar-python==1.4.8`、`tzdata==2026.3` / IANA `2026c`；runtime 不以 host/public package metadata 決定 bundled core availability 或版本。
- 新增有限、版本化的 offline birth-place registry；支援 explicit aliases，unknown fail closed，ambiguous alias 不自動交給網路結果覆蓋。
- location resolution precedence 固定為：完整 `resolved_location` → offline registry → **explicit opt-in** network fallback。未啟用 network fallback 時，unsupported place 回 `location_not_resolved`。
- Runtime Schema 1.1 明確區分 bundled core 與 execution-environment optional integrations；`geopy` / `timezonefinder` 僅為可選 network location diagnostics／fallback，不是離線 Natal 必要 dependency。
- single-file bundle 採 byte-oriented base64 records、SOURCE_DIGEST、per-record SHA256、unsafe path pre-write guard、vendor/registry/license preflight 與固定 5 MiB size guard。
- clean `python -S` qualification 覆蓋 birth-only Taipei、bundled dependency availability、public-package pollution、preloaded `sys.modules` pollution 與 no-network socket guard。
- modular runtime 與 single-file bundle 對 birth-only Taipei `build_natal` 及 `runtime_info` 做完整 parity qualification。
- 公開 onboarding 採 Birth Data first；offline registry coverage 明確標示為有限且版本化。

### Bazi Flow Day / Hour qualification

- 既有 production 八字流日／流時公式未修改。
- qualification 覆蓋 deterministic day samples、23:00 early-Zi、Gregorian transition、五鼠遁、連續日、DST responsibility 與 modular ↔ generated runtime parity。
- qualification PASS 只代表指定公開 oracle / property / integration evidence 對得上，不宣稱命理預測準確率。

### Ziwei Flow Day / Hour qualification

- 既有 `ziwei-fine-cycle-lunar-late-zi-v1` / `late_zi_forward-v1` production formula 未修改。
- qualification 覆蓋 deterministic day samples、22:59 / 23:00 / 23:59 / 00:00 late-Zi boundary、五鼠遁、Gregorian transition、DST responsibility 與 modular ↔ generated runtime parity。
- Fine Cycle stem / transformations / flying 維持 `implemented / experimental / on_demand / 1.0-exp`。

### Ziwei Month-Layer qualification

- 新增 pinned `lunar-python==1.4.8` month-continuity qualification：**86 month-oracle checks、0 mismatch**。
- ordinary lunar months：72 cases。
- real leap-month day 15 / day 16：14 cases across 7 leap-month years。
- ordinal 13 → next lunar-year month 1：10/10 property PASS。
- `leap_twelfth_month_second_half` 不再只有 synthetic internal coverage；真實 1574 閏十二月 day 15 為 `丁丑`，下一個實際農曆月為 1575 正月 `戊寅`，Project day 16 effective month source 亦為 `戊寅`。
- pinned lunar-lite 對閏十二月下半月仍有 direct-runtime oracle limitation；這個來源限制保留，不把 lunar-python continuity 說成 lunar-lite 自己直接驗證。
- 相鄰 regression 鎖住一般換月、農曆跨年、閏月 15→16、23:00 不獨立換月、DST responsibility、same local civil time 不 fork、downstream source reuse 與 modular ↔ generated runtime parity。
- Astralium fine-cycle 維持 `PENDING`；沒有 maturity promotion。

### User-facing language boundary

- Project Instructions 固定將 `uncalibrated / basic / calibrated / scorable / unscorable` 轉成一般使用者白話。
- `runtime validator`、schema、migration、raw JSON field name 與 harmless internal field-name difference 不在一般回答直播。
- 若內部差異實際影響結果，回答必須說明實際後果與需要採取的行動，而不是只丟工程術語。
- 此行為有 repository UX regression test 鎖定。

### v1.4.0 release acceptance

正式 tag 前必須在 release candidate exact head / merged `main` 重新通過：

```text
Bazi flow-time qualification --check       PASS
Ziwei flow-time qualification --check      PASS
Ziwei month-boundary qualification --check PASS
Deterministic distribution build/check     PASS
Focused historical/progressive suite       PASS
Full repository regression                 PASS
Python 3.9 compileall                       PASS
Clean validation tree                      PASS
```

最終 test count、workflow run 與 artifact digest 以 release-preparation PR 的 exact-head verification 為準；驗證前不預填成功數字。

## v1.3.0｜2026-08-23

### 一般使用者摘要

v1.3.0 把本命建立、紫微較細時間層與 AI Project 使用方式正式收斂成同一個版本。

- 可以只用出生資料建立 Project 八字／紫微本命。
- Astralium 或其他第三方八字／紫微排盤是**可選**交叉校驗來源，不是 runtime dependency。
- 支援更細的紫微時間層與流曜相關計算；實際可執行範圍由 `runtime_info` 判斷。
- 一般使用者只需要 `metaphysics_lab.py`、`metaphysics_core.md`、`project_instructions.md` 三個檔案。
- GitHub Release 的一般流程是從下載區取得這三個檔案，不需要使用 Source code ZIP。
- Python 負責固定計算，AI 負責命理解讀；缺少出生資料時不得自行猜值。

完整一般使用者版 GitHub Release 文案來源：`docs/發布說明-v1.3.0.md`。

正式 release **不因發版而自動提升 capability maturity**；當前 implementation / maturity / routing 仍以 `runtime_info` 為技術權威來源。

### AI Distribution Pack

- 正式提供 AI-first / mobile-first 發行形式：`metaphysics_lab.py`、`metaphysics_core.md`、`project_instructions.md`。
- 前兩個檔案加入 Project；`project_instructions.md` 內容貼入 Project Instructions。
- `dist/ai/metaphysics_lab.py` 為 deterministic single-file runtime；第三方 package source 不 vendor 進 bundle。
- 新增 `runtime_info`、portable natal / reconciliation、forecast context、Case export、single-file CLI 與 modular ↔ bundled parity tests。
- pre-resolved location path 可在沒有 location network packages 的環境使用；無可靠地點來源時 fail closed，不猜地點。
- forecast context 只建立 requested scopes；月／日／時 transformation/flying 與 flowing stars 共用同一 resolved source。
- 一般 Runtime 更新預設只替換 `metaphysics_lab.py`；Project Contract 或 Case Schema 只有在明確 migration 通知時才同步。
- AI Distribution Runtime 仍為 `1.0-exp`；正式 GitHub Release 不把 experimental metaphysics capability 自動升 Stable。

### Phase 2C｜Ziwei Flowing Stars

- `ziwei.flowing_stars` = `implemented / experimental / on_demand / 1.0-exp`；profile `ziwei-flowing-stars-common-v1`。
- 流曜屬 **Project 推導盤面**，canonical location 固定為 Earthly Branch。
- 支援 decadal / yearly / monthly / daily / hourly 五種 scope。
- 月日時重用 Phase 2B `ResolvedCycleStem`；大限重用 `ZiweiDecadalPeriod.stem_branch`；流年採 lunar-year neutral source，不重算上游 boundary policy。
- 核心 10 顆為天魁、天鉞、文昌、文曲、祿存、擎羊、陀羅、天馬、紅鸞、天喜；yearly 額外加入年解。
- `FlowingStarLayer` 與 Stable transformation/flying layer 分離，join key 為 `chart_id + scope + reference`。
- pinned iztro 2.6.0 revision `814b77e6371e1050cac31bbf674db3c3138fcfde` qualification：600/600 source cases、6120 placements、0 unexpected mismatch。
- Astralium flowing-stars private qualification 維持 `PENDING`；沒有沿用 Natal private PASS，也沒有 promotion。
- 明確排除**歲前十二神**、**將前十二神**、博士十二神、長生十二神、小限流曜、流曜亮度、scoring、AI interpretation。

### Phase 2C0｜Natal Chart Foundation

#### Birth / Location / Time foundation

- 新增 structured birth input resolution 與 Precision Gate；原則為 **Precision must be earned by input**。
- 完整 Mode A 最低輸入：性別、Gregorian 出生日期、出生時間、出生地。
- 缺欄位只回 machine-readable `missing_fields` / `allowed_actions`，不自行補值。
- birthplace geocoding / timezone resolution 零候選或多個 material candidates fail closed。
- Calendar Resolver 保持 neutral；**Calendar Resolver 不負責真太陽時**。
- 保存 `reported_civil_time`、`normalized_civil_time`、`bazi_effective_time`、`ziwei_effective_time`。
- 真太陽時 profile 固定記錄「經度校正＋均時差」，八字與紫微 profile 獨立。

#### Project 原生本命盤

- 新增八種資料類型中的 **Project 原生盤面**，與原始盤面事實、Project 推導盤面、命理推論分開。
- `bazi.natal_chart` = implemented / **Experimental** / on_demand / 1.0-exp。
- `ziwei.natal_chart` = implemented / **Experimental** / on_demand / 1.0-exp。
- Known Four Pillars 只建立 Bazi imported/external natal view，不反推完整 Ziwei natal。
- Astralium 為可選 external qualification source，不是 runtime dependency。

#### Normalized Natal / reconciliation

- 新增 External / Project / Resolved 三層資料模型，raw views 永久分開、不互相覆寫。
- 固定 field status：`MATCH / EQUIVALENT / CONFLICT / NOT_COMPARABLE`。
- 固定 severity：`INFO / CAUTION / BLOCKING`。
- `natal.reconciliation` = implemented / stable / on_demand / 1.0。
- Experimental authority 發生實質 external conflict 時，Resolved 預設採 external；衝突狀態仍保留。

#### Markdown / orchestration

- 新增 deterministic canonical Markdown exporter，只輸出 structured facts，不重算命盤、不猜 missing fields、不自動加入命理解讀。
- `natal.markdown_export` = implemented / stable / on_demand / 1.0。
- 新增 Mode A / B / C orchestration：Birth Data、Known Four Pillars、External + Project cross-check。

#### Qualification / privacy

- private aggregate qualification：Bazi **PASS**（6 direct matches、3 explicit profile differences、0 unexpected mismatch）；Ziwei Astralium natal **PASS**（129 matches、1 equivalent、0 unexpected mismatch）。
- raw private birth input、full address、raw chart、external raw payload 不進 repo。
- 單一 private case 不構成 promotion 依據；`bazi.natal_chart` / `ziwei.natal_chart` 仍為 Experimental，`promotion_allowed = false`。

### Phase 2B｜Ziwei Fine Cycle Stem Resolver v1

- 新增 `engine/calendar/sexagenary.py` 中立干支 helper。
- 新增 `engine/ziwei/fine_cycle_stems.py`，profile `ziwei-fine-cycle-lunar-late-zi-v1` / `1.0-exp`。
- 紫微流月 stem 採農曆月與閏月 15/16 分界；23:xx 不提前切換流月。
- 紫微流日固定 `late_zi_forward-v1`：22:59 舊日、23:00 effective date +1、00:00 不 double-rollover。
- 紫微流時使用 effective Ziwei day stem 起五鼠遁，hour branch 直接採 CalendarContext。
- 新增 `engine/ziwei/fine_cycle.py`，將 resolved stem 接入既有 Transformation / Flying Core。
- flow month/day/hour stem、transformations、flying = `implemented / experimental / on_demand / 1.0-exp`。
- Stable Transformation / Flying Core 與既有 palace maturity 不變。

#### Phase 2B qualification

```text
pinned lunar-lite 1d104fff...   18/18 PASS
pinned iztro 814b77e6...        integration PASS
Astralium fine-cycle             PENDING
```

- `leap_twelfth_month_second_half` 只有 synthetic internal coverage，為 **not externally qualified**。
- repo 不提交 Astralium raw private chart，只保存 aggregate PENDING state。

### v1.3.0 release acceptance

```text
Focused AI Distribution   56/56 PASS
Deterministic build check       PASS
Full repository           488/488 PASS
Python 3.9 compileall            PASS
```

這裡保存的是 v1.3.0 發布當時的 acceptance snapshot；後續 main 的測試數量增加，不回寫改造歷史 release evidence。

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
