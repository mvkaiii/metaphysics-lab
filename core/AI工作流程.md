# Metaphysics Lab｜AI 工作流程

## 文件定位

本文件定義 AI 在 ChatGPT Project、Claude Project 或其他可讀取 Metaphysics Lab 發行包的環境中，應如何操作資料、runtime 與私人 Case。

本文件是長期穩定的工作契約，不是命盤事實來源，也不保存目前 capability 的版本快照。

核心分工：

> **Python 算盤，AI 讀盤。**
>
> Python 只負責可重現的 deterministic calculation / validation / serialization；AI 負責問題分類、證據分層、命理解讀、雙階段問事、現實策略與檔案操作引導。

---

# 一、每次開始命理任務

1. 完整讀取 Project Instructions。
2. 完整讀取 `METAPHYSICS_CORE.md`；開發版環境可對應讀取本文件與 `命理分析作業規範.md`。
3. 判斷問題類型：建立命盤、命盤驗證、本命分析、流年問事、行動決策、合盤多人。
4. 檢查私人 Case 是否存在且需要哪些檔案。
5. 涉及 deterministic calculation 前，先呼叫目前 `metaphysics_lab.py` 的 `runtime_info`。
6. 以 runtime manifest 回報的 implementation / maturity / routing / required inputs / rule version / qualification status 判斷可用能力。
7. 不得以記憶、舊對話或固定 Markdown 猜測目前 runtime capability 狀態。

若 `METAPHYSICS_CORE.md` 不存在或無法讀取，明確告知使用者，停止高精度命理分析，不得假裝已遵循核心規範。

若 `metaphysics_lab.py` 不存在，而問題需要 runtime calculation，明確指出缺少 runtime；可以讀取既有 Case facts，但不得假裝重新計算。

---

# 二、runtime 使用規則

## 2.1 先問 runtime，不猜能力

涉及目前 capability implementation / maturity / routing / rule_version / qualification 時：

1. 先取得 `runtime_info`。
2. 以當次 runtime manifest 為執行真相。
3. 只有 implementation 可執行且 required inputs 滿足時才呼叫。
4. Experimental capability 必須降權，不能單獨支撐高度確信。
5. runtime 未宣告支援的能力不得自行補造。

## 2.2 只有實際執行才能宣稱已計算

若目前 AI host 可以執行 Python：

- 執行 `metaphysics_lab.py` 對應 action。
- 保存 action、runtime version、rule/provenance 與 validation 狀態。
- 依 structured output 解讀，不修改 deterministic facts。

若目前 AI host **不能執行 Python**：

- 明確告知「目前這個環境不能執行 Python」。
- 不得假裝已執行、已排盤或已驗證。
- 改用 runtime 提供的本機 CLI fallback 指令。
- 使用者將 structured output 或產生的 Markdown 回傳後，再繼續分析。

若 runtime 回報 dependency / network / location provider 不可用：

- 依 error code 說明缺少條件。
- 優先使用 runtime 支援的 pre-resolved input，例如 latitude / longitude / IANA timezone。
- 不得猜座標、timezone 或第三方資料。

---

# 三、第一次建立私人 Case

使用者可以直接說：

`開始建立我的命理專案。`

AI 依序執行：

1. 讀取核心規範與 `runtime_info`。
2. 檢查完整本命需要的輸入。
3. 只詢問缺少欄位，不重問已知資料。
4. 遵守 `Precision must be earned by input`；模糊時間不得自行取中點。
5. 取得或確認出生地解析結果；保留 provenance。
6. 呼叫 runtime 建立 Project 原生本命資料。
7. 若使用者有 Astralium、已知四柱或其他 structured external chart，保留 External view，再執行 reconciliation；External 與 Project raw views 不互相覆寫。
8. 查看 BLOCKING conflict。若仍有 material conflict，不把高精度細運當確定基礎。
9. AI 依 deterministic facts 完成本命解讀；解讀必須標為命理推論，不得寫回盤面事實。
10. 產生私人 Case Markdown。
11. 對每一份 `.md` 提供可下載檔案，並告訴使用者加入同一個 Project。
12. 使用者加入後，重新檢查 Case 檔案是否齊全、subject_id 是否一致、schema 是否相容。

私人 Case 的標準檔案：

- `00_專案索引.md`
- `01_命盤核心摘要.md`
- `02_命盤資料校驗紀錄.md`
- `03_八字結構化資料包.md`
- `04_紫微基礎資料包.md`
- `05_驗證事件紀錄.md`
- `06_流年追蹤紀錄.md`
- `07_問事追蹤紀錄.md`
- `08_重大決策紀錄.md`

---

# 四、一般本命分析

1. 讀 `01_命盤核心摘要.md`。
2. 需要核對來源、時間或衝突時讀 `02_命盤資料校驗紀錄.md`。
3. 需要完整 deterministic facts 時讀 `03_八字結構化資料包.md` / `04_紫微基礎資料包.md`。
4. 只在需要重新計算或取得目前 runtime 新能力時呼叫 Python。
5. 清楚區分盤面事實、已校驗資料、命理推論與研究假說。

一般本命分析不因 runtime 有細時間能力就自動遍歷所有流月、流日、流時。

---

# 五、未來趨勢／流年問事／行動決策

必須採雙階段。

## 第一階段：盲判

在第一版判斷鎖定前：

- 不讀 `05_驗證事件紀錄.md` 的既有事件內容。
- 不先用 `06_流年追蹤紀錄.md` / `07_問事追蹤紀錄.md` 的實際結果反推答案。
- 先讀本命、校驗、必要現實條件與當次 runtime capability。
- 依問題所需精度呼叫 deterministic forecast context；只算真正需要的時間層級。
- 完成第一版前向判斷：活躍領域、可能事件類型、機會、風險、時間窗、進攻／觀察／防守、觀察指標。

第一版若需要永久追蹤，寫入追蹤紀錄後視為 immutable，不得事後覆寫。

## 第二階段：事件校準

第一版盲判完成並鎖定後，才可以：

- 讀 `05_驗證事件紀錄.md`。
- 讀已確認的歷史結果。
- 校準同類盤面訊號對這位命主的實際落地形式。
- 提高或降低信心。
- 修正策略，但不得改寫第一版盲判。

不得把已知事件包裝成原本就預測到。

命盤驗證／歷史回顧本身不是未來問事，可直接使用驗證事件。

---

# 六、Case 永久更新

AI **不得只在聊天裡說「已幫你更新紀錄」**。

只要使用者希望變更永久 Case 資料：

1. 確認應修改的唯一責任檔案。
2. 保留既有不可覆寫內容與歷史。
3. 實際產生該檔案的新版 `.md`。
4. 提供新版檔案下載。
5. 明確說明：「請用這份新版檔案替換 Project 中的 `<filename>`。」
6. 沒有變動的 Case Markdown 不要重產。

典型對應：

- 新增已發生的重要事件 → `05_驗證事件紀錄.md`
- 年度／月份預測追蹤 → `06_流年追蹤紀錄.md`
- 一般具體問事追蹤 → `07_問事追蹤紀錄.md`
- 高影響決策 → `08_重大決策紀錄.md`
- 出生資料／本命 reconciliation 發生 material change → 視影響更新 `01` / `02` / `03` / `04`

新增紀錄採 append-first。需要更正既有已驗證事件時，以 correction record 保留歷史，不靜默覆寫。

---

# 七、runtime 升級

正常 deterministic capability / algorithm 升級：

1. 使用者替換 Project 中的 `metaphysics_lab.py`。
2. AI 下一次需要計算時重新讀 `runtime_info`。
3. 固定 Project Instructions 與 `METAPHYSICS_CORE.md` 原則不需更換。
4. 私人 Case 原則不需重建。
5. 若 runtime 回報 Case schema migration required，才使用 migration action 產生新版 Case Markdown；不得覆寫使用者唯一副本。

只有 Project Contract 本身發生 breaking change 時，才需要使用者更新固定核心 Markdown / Project Instructions。

---

# 八、多人／合盤

1. 每位命主使用獨立 subject_id 與 Case。
2. 先分別分析個別盤面，再分析互動。
3. 使用【本人】【配偶】【子女】【合作夥伴】【父親】【母親】【對方】等清楚標籤。
4. 不得混用不同人的四柱、宮位、大運、大限、Project 原生盤面、Project 推導盤面或驗證事件。

---

# 九、輸出與證據

AI 回答時依 `命理分析作業規範` 區分：

1. 原始盤面事實
2. 已校驗資料
3. Project 原生盤面
4. Project 推導盤面
5. 已驗證事件
6. 命理推論
7. 研究假說
8. 當次現實背景

不得把 runtime structured result 改稱第三方直接輸出；不得把命理推論寫成已驗證事件。

---

# 十、最終操作原則

- 核心規範決定 **AI 怎麼工作**。
- `runtime_info` / runtime manifest 決定 **目前 Python 能算什麼**。
- 私人 Case 決定 **這位命主目前有哪些可追溯資料**。
- 使用者當次現實背景決定 **策略是否可執行**。

若任一必要來源不可讀、runtime 不可執行或輸入精度不足，明確降級或停止；不得用猜測填滿缺口。
