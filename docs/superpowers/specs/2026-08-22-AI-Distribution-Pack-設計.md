# Metaphysics Lab AI Distribution Pack｜設計規格

- 日期：2026-08-22
- Branch：`design/ai-distribution-pack`
- 狀態：Design spec，等待使用者 final review；尚未進入 implementation plan
- 分類：Architectural
- Base：`main` commit `0e2493cb1ce3a30d0c12408f25755ddc8f50e5bc`
- 目標：將目前模組化 Metaphysics Lab 工程，發布成適合 ChatGPT／Claude Project、手機優先、AI-first 的可攜式使用包
- 核心原則：repo 內維持模組化；對外發布單檔 Python runtime + 固定 AI contract Markdown；私人 Case 以個別 Markdown 檔持續維護

---

## 一、目的

目前 Metaphysics Lab 已由早期「提示詞 + 少量規則檔」成長為包含 `engine/`、`tests/`、`qualification/`、`templates/`、`tools/` 與多個命理能力的正式工程。

這使得「把整個 repo 的 Python 全部上傳到 ChatGPT / Claude Project」不再是適合一般使用者的部署方式。

本設計的目標不是重寫既有命理引擎，而是新增一層 **AI Distribution / Portable Runtime**：

```text
Developer Source
├─ modular Python engine
├─ modular core Markdown
├─ tests / qualification
└─ build tools
        ↓ deterministic build
Mobile-first AI Release
├─ metaphysics_lab.py
├─ METAPHYSICS_CORE.md
├─ PROJECT_INSTRUCTIONS.md
└─ GitHub Release README / notes
        ↓ first-run workflow
Private Case Markdown
├─ 00_專案索引.md
├─ 01_命盤核心摘要.md
├─ 02_命盤資料校驗紀錄.md
├─ 03_八字結構化資料包.md
├─ 04_紫微基礎資料包.md
├─ 05_驗證事件紀錄.md
├─ 06_流年追蹤紀錄.md
├─ 07_問事追蹤紀錄.md
└─ 08_重大決策紀錄.md
```

產品心智模型固定為：

> **Python 算盤，AI 讀盤。**
>
> **核心 Markdown 定義 AI 怎麼工作；Python runtime 定義目前能算什麼、怎麼算。**
>
> **系統升級通常只替換 `metaphysics_lab.py`；私人 Case 更新只替換實際有變更的 Markdown。**

---

## 二、正式設計決策

### 2.1 AI-first 為主流程，本機 CLI 為正式 fallback

正式支援 C 方案，但 UX 以 AI-first 為預設：

1. 使用者建立 ChatGPT Project 或 Claude Project。
2. 將 `PROJECT_INSTRUCTIONS.md` 貼入 Project Instructions。
3. 上傳 `METAPHYSICS_CORE.md` 與 `metaphysics_lab.py`。
4. 建議正式分析使用 High reasoning 等級。
5. 使用者只需輸入：`開始建立我的命理專案。`
6. AI 接手 Input Resolution、runtime capability 檢查、命盤建立與 Case Markdown 建立。

若 AI host 無法執行 Python，必須 fail closed，不得假裝已執行；改走正式本機 fallback：

```text
python metaphysics_lab.py ...
```

同一支 `metaphysics_lab.py` 必須同時支援：

- AI host / Python sandbox 呼叫。
- 本機 CLI 呼叫。
- 相同 action contract。
- 相同 structured output schema。

不得為 ChatGPT 與 Claude 維護兩套算法。

### 2.2 開發版維持模組化；單檔 Python 是 build artifact

不得為了方便上傳，而把 repo 原始碼永久改成一支巨型 Python。

正式責任：

```text
engine/**
= canonical source / modular development

tests/**
= regression truth

metaphysics_lab.py
= generated distribution artifact
```

`metaphysics_lab.py` 必須由固定 build process 自動產生，不接受手工 copy/paste 維護。

build 後必須驗證單檔 runtime 與 canonical modular engine 對正式 fixtures 產生等價結果。

### 2.3 單檔 runtime 必須 self-describing

固定提供 runtime metadata action，例如：

```text
runtime_info
```

最低輸出：

```text
runtime_version
runtime_schema_version
case_schema_version
project_contract_compatibility
supported_actions
capabilities
implementation
maturity
routing
rule_version
rule_profile
required_inputs
qualification_status
output_classification
external_dependency_status
```

核心 Markdown 不再硬寫會快速過期的 capability status、rule profile 或演算法細節。

AI 必須以目前 `metaphysics_lab.py` 回報的 capability manifest 為 runtime truth，不得依舊 Prompt 記憶自行假定能力，也不得因讀過開發版規則文件而繞過 runtime 手算。

### 2.4 Project Contract 與 Runtime Version 分離

正式建立兩條版本線：

```text
Project Contract Version
= AI 工作治理契約
= 很少變

Runtime Version
= deterministic engine capability / calculation
= 可持續迭代
```

正常能力升級：

```text
只換 metaphysics_lab.py
```

不要求使用者重新貼 Project Instructions、不要求重上傳固定核心 MD、不要求重建私人 Case。

只有以下情況才形成 Project Contract Upgrade：

- 雙階段盲判／校準規則改變。
- 資料分類或 evidence governance 發生 breaking change。
- 多人資料隔離契約改變。
- AI 安全／高風險決策規則改變。
- AI workflow contract 發生 breaking change。

### 2.5 Mobile-first：主流程禁止要求 ZIP 解壓縮

GitHub Release 的一般使用路徑固定提供獨立 asset：

```text
metaphysics_lab.py
METAPHYSICS_CORE.md
PROJECT_INSTRUCTIONS.md
```

README / Release Notes 可直接在 GitHub 頁面閱讀，不要求手機使用者下載 README。

ZIP 只作：

- 桌機完整備份。
- offline archive。
- 非主流程。

私人 Case 正常更新也不得要求 ZIP；必須以個別 `.md` 提供下載與替換。

---

## 三、Release Markdown 責任邊界

### 3.1 `PROJECT_INSTRUCTIONS.md`

用途：Project 的最高層 AI contract。

Canonical source：由 repo 的核心提示詞來源 build / copy 產生，不另維護第二份手工 prompt。

只應包含長期穩定治理規則：

- 角色定位。
- 台灣繁體中文與務實輸出風格。
- 資料讀取優先順序。
- 問題類型判斷。
- Input Resolution / Precision Gate。
- 資料分類原則。
- External / Project / Resolved。
- 未來問事先盲判、後事件校準。
- 八字／紫微／奇門責任分工。
- Experimental capability 降權原則。
- 多人資料隔離。
- 現實背景權重。
- 高風險領域限制。
- 禁止事項。
- 信心表達與輸出格式。

不得長期硬寫：

- 現在有哪個 Phase。
- capability 當前 implementation / maturity。
- qualification case counts。
- pinned oracle revision。
- module path。
- 特定 runtime 的星曜清單或 scope support。
- 會隨 runtime 迭代的排盤算法細節。

以上動態資訊由 runtime manifest 與 runtime calculation 負責。

### 3.2 `METAPHYSICS_CORE.md`

用途：AI 執行工作時閱讀的**穩定工作契約與分析治理規範**。

它是 build artifact，不是 repo 內唯一 canonical source。

正式只組合相對穩定來源，例如：

```text
AI 工作流程
命理分析作業規範
資料證據層級與來源分類
問事盲判／事件校準流程
Case Markdown 更新規則
高風險與禁止事項
```

**不再把完整 `命理推導計算規則.md` 打包進一般使用者 Release Core。**

`命理推導計算規則.md` 繼續作為 repo 的工程／研究／qualification 文件；對一般 AI Project，deterministic algorithm truth 由當前 `metaphysics_lab.py` 負責。AI 可讀 runtime 的 rule version / profile / provenance，但不得自行重算 runtime 已負責的算法。

這個邊界確保正常 runtime 升級時：

```text
metaphysics_lab.py 更新
METAPHYSICS_CORE.md 不必更新
PROJECT_INSTRUCTIONS.md 不必更新
```

build 時每一段保留來源標記，例如：

```text
<!-- source: core/命理分析作業規範.md -->
```

不得將 README、release history、CHANGELOG、qualification raw evidence 或快速變動的 capability matrix 合併進去。

### 3.3 README / GitHub Release Notes

用途：只服務人類使用者。

必須做到手機第一屏就能知道怎麼開始。

最低內容：

1. 這是什麼。
2. 不需要懂 Python。
3. ChatGPT / Claude 設定步驟。
4. 哪兩個檔案要上傳。
5. 哪一份內容要貼入 Project Instructions。
6. 建議 reasoning 等級。
7. 啟動句：`開始建立我的命理專案。`
8. Python 無法執行時的 fallback 指引。
9. 升級方式：通常只換 `metaphysics_lab.py`。

README 不得複製 capability matrix，不得成為 runtime status 的第二真相來源。

---

## 四、模型與推理強度政策

模型名稱與平台 UI 會變動，不得寫死在核心命理 contract。

永久規格只定義能力需求：

```text
Full natal / forecast / cross-system analysis:
recommended_reasoning = high
minimum_recommended = medium
instant_fast = not recommended for full analysis
```

平台 README 可提供「截至發行日」的當前建議模型名稱，但該區塊屬部署建議，可獨立更新，不改命理 Project Contract。

High reasoning 的理由不是命理神祕性，而是完整流程需要：

- 多步驟資料讀取。
- capability 選擇。
- evidence separation。
- 八字／紫微分層整合。
- 第一階段盲判隔離。
- 第二階段事件校準。
- 信心降權與策略化輸出。

Instant / fast 可用於：

- 安裝。
- 簡單檔案整理。
- 查詢已存在盤面 facts。
- 新增低複雜度紀錄。

---

## 五、`metaphysics_lab.py` 公開介面

### 5.1 統一 action dispatcher

單檔 runtime 對外只暴露少量高階 action；AI 不應理解內部 module graph。

最低 action family：

```text
runtime_info
validate_case
build_natal
reconcile_natal
resolve_forecast_context
export_case_markdown
migrate_case
```

implementation plan 可依既有 orchestration contract 將 action 拆細，但 public UX 不得要求使用者自己理解 `birth/calendar/bazi/ziwei/natal` module。

### 5.2 Python 只負責 deterministic work

可以：

- input validation。
- Calendar resolution。
- natal calculation。
- Bazi / Ziwei deterministic layers。
- transformations / flying / flowing stars 等 runtime 已宣告能力。
- reconciliation deterministic facts。
- schema validation。
- canonical Markdown data serialization。
- case migration。

不可以：

- 自由命理解讀。
- 決定使用者是否該離職／投資／結婚。
- 把某顆星自由對應成具體人生事件。
- 讀歷史事件後改寫第一階段盲判。
- 自動產生宿命式結論。

### 5.3 Dependency / host capability 必須顯式

目前 repo 有外部 dependency：

```text
lunar-python
tzdata
geopy
timezonefinder
```

而 location resolution 目前包含 Nominatim network provider。

因此 v1 distribution 不得假裝「一支 `.py` 在所有 AI sandbox 都 100% 無條件可執行」。

正式設計要求：

1. build artifact 必須包含全部 **Metaphysics Lab 自有 Python modules**。
2. 第三方 dependency 是否 vendor 進單檔，必須經 license / size / portability review；不得未審查直接內嵌。
3. runtime 啟動時檢查 external dependencies 與 network-required providers。
4. 缺 dependency 時回 machine-readable availability error，不得 crash 成不明例外。
5. 需要 location resolution 時，runtime 必須允許接受已解析的 `latitude / longitude / IANA timezone`，讓 AI host 或本機 adapter 可提供 pre-resolved location。
6. AI host 若代為解析 birthplace，必須保存 provenance，不能冒充 deterministic runtime 自己查到。
7. 無法可靠解析時必須追問或 fallback，不得猜 timezone / coordinates。

目標是「一般使用者無腦」，不是「隱藏失敗」。

---

## 六、單檔 build 策略

正式推薦使用 generated in-memory module bundle，而不是手工 concatenate。

概念：

```text
canonical engine modules
        ↓ build tool
module source manifest
        ↓
embedded/compressed module payload
        ↓
custom in-memory importer
        ↓
normal engine imports
        ↓
public dispatcher
```

優點：

- repo 仍維持小模組。
- 不必大量改寫 relative imports。
- build artifact 仍是一支 `.py`。
- 可產生 source manifest / digest。
- 可以對 modular runtime 與 bundled runtime 做 parity tests。

禁止：

- 手工維護一支重複邏輯的 `metaphysics_lab.py`。
- build 後單檔另有未回寫 canonical engine 的 bugfix。
- 單檔與 modular source capability registry 分叉。

---

## 七、第一次使用完整 UX

### 7.1 GitHub Release

使用者看到：

```text
1. metaphysics_lab.py        [直接下載]
2. METAPHYSICS_CORE.md       [直接下載]
3. PROJECT_INSTRUCTIONS.md   [開啟並複製]
```

另外可提供：

```text
Metaphysics-Lab-AI-Pack.zip  [optional desktop backup]
```

### 7.2 建立 Project

README 指示：

1. 建立新的 ChatGPT / Claude Project。
2. 將 `PROJECT_INSTRUCTIONS.md` 全文貼入 Project Instructions。
3. 上傳 `METAPHYSICS_CORE.md`。
4. 上傳 `metaphysics_lab.py`。
5. 正式分析建議選 High reasoning。
6. 輸入：`開始建立我的命理專案。`

### 7.3 AI first-run workflow

AI 必須：

1. 確認 `METAPHYSICS_CORE.md` 可讀。
2. 確認 `metaphysics_lab.py` 存在。
3. 取得 `runtime_info`；若不能執行，立即進 fallback。
4. 判斷是否已有 Case Markdown。
5. 若沒有，開始 Input Resolution。
6. 只詢問缺少的必要出生資訊。
7. 資料足夠後建立 Project deterministic natal facts。
8. 有 external chart 時做 reconciliation；沒有則不要求一定去第三方排盤。
9. AI 依正式規範建立命盤摘要與 case records。
10. 產出 Case Markdown files。
11. 將每份 `.md` 作為個別下載檔提供。
12. 清楚告訴使用者將所有 Case MD 加入同一 Project。
13. 使用者加入後，AI 執行 `validate_case` / file presence check。
14. 完成後才進一般本命、流年、決策分析。

### 7.4 Python 不可執行 fallback

AI 必須明確說明「目前環境沒有實際執行證據」，並提供一條最簡單本機指令。

不得：

- 假裝已執行。
- 自行手算並冒充 runtime output。
- 要使用者理解整個 repo module graph。

---

## 八、私人 Case Markdown 正式責任邊界

所有 Case Markdown 都必須有最低 metadata header：

```text
case_schema_version
project_contract_version
record_type
subject_id
created_at
last_updated_at
last_modified_by
runtime_version_if_applicable
source_classification
mutation_policy
```

其中 `last_modified_by` 可為 runtime / AI workflow / user import；不是每份檔案都假裝由 Python 產生。`runtime_version_if_applicable` 在純事件紀錄沒有 runtime 參與時可標示 `not_applicable`。

`subject_id` 應為 Case 內穩定匿名識別，不要求真實姓名。

### 8.1 `00_專案索引.md`

用途：Case manifest / schema entry point。

包含：

- case schema version。
- subject id。
- Case 檔案清單。
- 每個 record type 的用途。
- Project Contract compatibility。
- privacy reminder。

不包含：

- 命理解讀。
- 每次問事結果。
- 動態 runtime capability matrix。

Mutation policy：只有 case schema migration、檔案新增／移除或 subject metadata material correction 時更新；**不因每一筆事件而強迫一起更新**，避免 incremental update 永遠需要兩個檔案。

### 8.2 `01_命盤核心摘要.md`

用途：AI 每次分析優先讀取的高訊號本命摘要。

包含：

- 已解析／已校驗出生基礎。
- Resolved natal key facts。
- 八字與紫微的核心結構化摘要。
- 長期穩定、已確認的分析框架。
- provenance / confidence boundary。

不得包含：

- 尚未發生的流年預測紀錄。
- 每次問事流水帳。
- 為配合事件而修改的原始盤面。

Mutation policy：本命重新校驗、authority resolution 變更、runtime migration 導致 material natal output change 時才更新。

### 8.3 `02_命盤資料校驗紀錄.md`

用途：保存「為什麼這份盤可信／哪裡仍有衝突」。

包含：

- 原始出生輸入與 precision 狀態。
- reported / normalized / Bazi / Ziwei time views。
- location provenance。
- External / Project / Resolved。
- MATCH / EQUIVALENT / CONFLICT / NOT_COMPARABLE。
- INFO / CAUTION / BLOCKING。
- external source metadata。
- material conflict 與 unresolved item。

Mutation policy：新增 external source、修正出生資料、reconciliation 結果改變時更新。

### 8.4 `03_八字結構化資料包.md`

用途：八字 deterministic facts 的 portable structured record。

包含 runtime 已正式支援且屬本命／長週期基礎的八字 facts；具體欄位由 runtime schema 定義。

原則：

- 盤面事實與命理解讀分開。
- 必須標 source classification / rule profile / runtime version。
- 不把臨時流日問事結果永久塞進本檔。

Mutation policy：八字本命／長週期 deterministic output material change 或 schema migration 時重產。

### 8.5 `04_紫微基礎資料包.md`

用途：紫微 deterministic natal / stable base facts 的 portable structured record。

包含 runtime 正式輸出的本命宮位、星曜、四化／飛化基礎與必要長週期基礎；具體欄位由 runtime schema 定義。

不得把每次流月／流日／流時 transient layer 無限制累積進本檔。

Mutation policy：紫微本命／基礎 deterministic output material change 或 schema migration 時重產。

### 8.6 `05_驗證事件紀錄.md`

用途：只保存已經發生、且使用者確認的重要事件，用於第二階段事件校準。

固定 append-first：

- 新事件追加。
- 原事件若需更正，以 correction record 保留歷史；不靜默覆寫。
- AI 不得把預測內容提前寫成已驗證事件。
- 研究假說不得寫入此檔。

AI 在第一階段盲判時不得先讀本檔事件內容。

### 8.7 `06_流年追蹤紀錄.md`

用途：年度／半年／月份等可驗證 forecast 的追蹤歷史。

每筆至少分：

```text
第一版盲判（immutable after record）
事件校準
後續實際結果
命中／失準檢討
```

不得事後重寫第一版盲判。

Mutation policy：append/update outcome sections；blind forecast section immutable。

### 8.8 `07_問事追蹤紀錄.md`

用途：具體未來問事、短期行動與可驗證預測的 record。

包含：

- 問題與當時現實背景。
- 使用的時間範圍。
- 第一階段盤面判斷。
- event calibration。
- 策略與觀察指標。
- 後續結果。

一般低價值聊天不必全部寫入。

Mutation policy：append-first；第一版判斷不得事後覆寫。

### 8.9 `08_重大決策紀錄.md`

用途：保存高影響決策脈絡，不等同一般問事流水帳。

適用：

- 轉職／創業。
- 房產。
- 大額資源配置。
- 搬遷。
- 長期合作。
- 其他使用者認定重大決策。

包含：

- 現實限制與選項。
- 命理只作何種層級參考。
- 進攻／防守／停損條件。
- 決策結果與事後回顧。

高風險領域仍需遵守專業意見優先規則。

---

## 九、Case incremental update 規則

正式 UX：

> 哪份資料改了，就只產生哪份新版 Markdown。

例如：

```text
新增已確認人生事件
→ 只更新 05_驗證事件紀錄.md

新增一筆年度 forecast 結果
→ 只更新 06_流年追蹤紀錄.md

一般問事要永久追蹤
→ 只更新 07_問事追蹤紀錄.md

重大決策
→ 只更新 08_重大決策紀錄.md

本命出生時間被更正
→ 可能需要 01 / 02 / 03 / 04 material regeneration
```

AI 不得只說「我已幫你記錄」。

只要涉及永久 Case 資料變更，就必須：

1. 實際產生新版 `.md`。
2. 提供下載。
3. 明確指出 Project 中要替換哪個舊檔。
4. 若只是 append，可說明舊資料已保留。

ZIP 只有使用者明確要求完整備份／export 時才產生。

---

## 十、Case schema 與 migration

每份 Case Markdown 必須可 machine-read metadata header，讓新版 runtime 判斷相容性。

例如：

```text
case_schema_version: 1.0
project_contract_version: 1.0
runtime_version_if_applicable: 1.x
```

新版 runtime 開啟舊 Case：

```text
compatible
→ 直接使用

migration_available
→ 產生新版 MD，不覆寫使用者唯一副本

unsupported_breaking
→ 明確停止並說明需要的 migration path
```

任何 migration：

- 不得刪除 raw external facts。
- 不得把 CONFLICT 改成 MATCH。
- 不得改寫 blind forecast history。
- 不得把推論變成已驗證事件。

---

## 十一、Build / Release 驗收標準

最低必須有以下 gate。

### 11.1 Modular → Single-file parity

同一 fixtures：

```text
modular engine output == bundled metaphysics_lab.py output
```

比較 normalized structured output，不以 Python object repr 作 truth。

### 11.2 Runtime manifest test

確認：

- 所有 canonical implemented capabilities 在 bundle 中正確出現。
- maturity / routing / rule version 不漂移。
- unavailable external dependency 正確回報，而不是 capability silently disappear。

### 11.3 Stable Contract test

一般 runtime capability／演算法升級時，應能只替換 `metaphysics_lab.py`。

測試必須防止 build process 因 capability matrix、rule profile 或演算法細節變更而無故改寫：

```text
PROJECT_INSTRUCTIONS.md
METAPHYSICS_CORE.md
```

只有 Project Contract source 本身變更時，才允許固定核心 MD digest 改變。

### 11.4 Case Markdown golden tests

固定 input + 固定 generated timestamp：

```text
byte-identical Markdown
```

並測：

- 9 檔檔名固定。
- metadata header 完整。
- privacy-sensitive raw payload 不被意外寫入不該存在的檔案。

### 11.5 Incremental mutation tests

例如新增一筆 verified event：

- `05_驗證事件紀錄.md` 改變。
- `01/02/03/04` 不應無故改變。
- blind forecast 不被覆寫。

### 11.6 Mobile release asset test

GitHub Release 必須能獨立取得：

```text
metaphysics_lab.py
METAPHYSICS_CORE.md
PROJECT_INSTRUCTIONS.md
```

不得要求使用者解壓縮才能開始。

### 11.7 Existing regression

本階段是 distribution / orchestration architecture，不得降低既有命理 capability regression。

完整 repo tests 必須全過。

---

## 十二、版本與 release policy

本設計不自動：

- 升任何 Experimental capability 為 Stable。
- 完成 Astralium PENDING qualification。
- 建 Git tag。
- 建正式 GitHub Release。
- 修改 `VERSION.md` release identity。

implementation 完成並通過獨立 acceptance gate 後，若使用者要將 AI Distribution Pack 納入正式 release，再另走 release/version gate。

Project Contract 初版可標 `1.0`，但不代表 Metaphysics Lab Core runtime 必須同時改成 v2 或其他 major。

---

## 十三、明確排除範圍

本階段不做：

- Remote MCP server。
- 公開 HTTP API service。
- ChatGPT 專屬 app。
- Claude 專屬 remote connector。
- 自動同步 Project files 到雲端。
- 私人 Case 上傳 GitHub。
- 讓 Python 自由進行命理解讀。
- 為了 single-file 而重寫所有 canonical engine modules。
- 未審查 license 就 vendor 第三方 dependency。
- 強迫手機使用者下載 ZIP。
- 將快速變動的演算法規則複製進固定 AI Core，造成每次 runtime 升級都要重傳 MD。

---

## 十四、成功條件

本階段成功後，一般使用者應能達成：

```text
GitHub Release
→ 手機直接下載 2 個檔案
→ 複製 1 份 Project Instructions
→ 建立 ChatGPT / Claude Project
→ 說「開始建立我的命理專案」
→ AI 自動判斷 runtime 可用性
→ 收集缺少出生資料
→ Python deterministic calculation
→ AI 解讀 / reconciliation workflow
→ 產生個別 Case Markdown
→ 使用者直接下載並加入 Project
```

日後正常升級：

```text
新的 runtime capability / algorithm
→ 換 metaphysics_lab.py
→ 固定核心 MD 原則不動
→ 私人 Case 原則不重建
```

日後私人資料更新：

```text
只替換實際變動的 Case Markdown
```

最終產品原則：

> 使用者不需要理解 Phase、module、dependency graph 或 schema internals 才能開始。
>
> 工程複雜度留在 repo；使用複雜度由 build artifact、AI workflow 與清楚的責任邊界吸收。
