# Metaphysics Lab｜AI 工作流程

## 文件定位

本文件定義 AI 在 ChatGPT Project、Claude Project 或其他可讀取 Metaphysics Lab 發行包的環境中，應如何操作資料、runtime 與私人 Case。

本文件是長期穩定的工作契約，不是命盤事實來源，也不保存目前 capability 的版本快照。

核心分工：

> **Python 算盤，AI 讀盤。**
>
> Python 負責可重現的 deterministic calculation / validation / selection / serialization；AI 負責問題分類、命主辨識、證據分層、命理解讀、雙階段問事、現實策略與檔案操作引導。

---

# 一、每次開始命理任務

1. 完整讀取 Project Instructions。
2. 完整讀取 `METAPHYSICS_CORE.md`；開發版環境可對應讀取本文件與 `命理分析作業規範.md`。
3. 判斷問題類型：建立命盤、命盤驗證、本命分析、流年問事、行動決策、合盤多人。
4. **先 resolve 命主**：若私人 Project 有 `命主索引.md`，先以它對應本次 subject；不得預設使用者永遠只問自己。
5. 再檢查該 subject 的 Case 已 materialize 哪些檔案；不得假定 05～08 一定存在。
6. 涉及 deterministic calculation 前，先呼叫目前 `metaphysics_lab.py` 的 `runtime_info`。
7. 以 runtime manifest 回報的 implementation / maturity / routing / required inputs / rule version / qualification status 判斷可用能力。
8. 不得以記憶、舊對話或固定 Markdown 猜測目前 runtime capability 狀態。

若同名 subject 有多個候選，不得只靠姓名自動合併；使用 `subject_id` / short id / 當次 context 釐清。

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
- 不得假裝已執行、已排盤、已展開候選、已選年或已驗證。
- 改用 runtime 提供的本機 CLI fallback 指令。
- 使用者將 structured output 或產生的 Markdown 回傳後，再繼續分析。

若 runtime 回報 dependency / network / location provider 不可用：

- 依 error code 說明缺少條件。
- 優先使用 runtime 支援的 pre-resolved input，例如 latitude / longitude / IANA timezone。
- 不得猜座標、timezone 或第三方資料。

---

# 三、Subject Identity 與第一次建立私人 Case

使用者可以直接說：

`開始建立我的命理專案。`

也可以說：

`幫 Amy 建立命盤。`

AI 依序執行：

1. 讀取核心規範與 `runtime_info`。
2. 讀取 `命主索引.md`；若不存在，在第一位命主建立時 materialize。
3. 判斷這是既有 subject 或新命主。
4. 既有 subject：沿用原 `subject_id`。新命主：由 AI 發起 `subject.create_identity`，**opaque `subject_id` 必須由 runtime 產生**，不得由姓名／生日／出生地拼出或 hash PII。
5. 保存 `subject_display_name`、`subject_short_id`、`filename_label` 至 `命主索引.md`。
6. 檢查 natal 所需輸入；只詢問缺少欄位，不重問已知資料。
7. 遵守 `Precision must be earned by input`；模糊時間不得自行取中點或 default time。
8. 取得或確認出生地解析結果；保留 provenance。
9. exact input：呼叫 runtime 建立單一 Project 原生本命。bounded / unknown time：若 `natal.candidate_envelope` 可執行且 location/timezone basis 完整，建立 Candidate Envelope；不得自己挑一個候選。
10. 若使用者有 Astralium、已知四柱或其他 structured external chart，保留 External view，再執行 reconciliation；External 與 Project raw views 不互相覆寫。
11. 查看 BLOCKING conflict / partial blocked scopes。若仍有 material conflict 或唯一時辰未解，不把高精度單一盤分析當確定基礎。
12. AI 依 deterministic facts 完成本命解讀；解讀必須標為命理推論，不得寫回盤面事實。
13. 產生 Base Case Markdown。
14. 對每一份已建立的 `.md` 提供實際檔案，並告訴使用者加入同一個 Project。
15. 使用者加入後，重新檢查 `命主索引.md`、Case filenames、subject_id、schema 與 `00` manifest 是否一致。

## 3.1 Subject-aware filename

Case Schema 1.1 新檔名：

```text
<filename_label>_<SUBJECT_SHORT_ID>_<slot>_<canonical_title>.md
```

例如：

```text
Kai_7F3A2C_01_命盤核心摘要.md
```

`subject_display_name` 可改，`subject_id` 不變。Rename 若該 subject 已有 Case，必須一次更新 registry、所有已 materialize Case filenames/front matter 與 00 manifest；不得只改其中一份。

## 3.2 Base Case

第一次建立只 materialize canonical slot 00～04；實際檔名帶 subject identity。例如：

```text
Kai_7F3A2C_00_專案索引.md
Kai_7F3A2C_01_命盤核心摘要.md
Kai_7F3A2C_02_命盤資料校驗紀錄.md
Kai_7F3A2C_03_八字結構化資料包.md
Kai_7F3A2C_04_紫微基礎資料包.md
```

此時：

```text
05 = absent
06 = absent
07 = absent
08 = absent
Historical Calibration = uncalibrated
```

不得先建立內容為空的 05～08。

## 3.3 Unknown / bounded birth time

若沒有唯一出生時間：

- 不得補 12:00、00:00、中點或「最像的時辰」。
- `natal.candidate_envelope` 只在 runtime 宣告可執行且出生日期／地點／timezone basis 足夠時使用。
- Candidate Envelope 將不確定時間切成 material timing states，再區分 invariant / candidate-dependent facts。
- partial Base Case 仍可 materialize 00～04。
- `01` 必須分【已確定盤面】／【候選依賴盤面】／【目前不可唯一判定】。
- `03` / `04` 不得把 candidate-dependent 欄位寫成唯一值。
- 若 `single_chart_personalized_forecast` 或其他 unique-time-only scope 被 blocked，AI 不得為了問流年而偷偷選一張候選盤。

Candidate rectification 只可排序候選；即使只剩一個最高候選，也不得稱為已驗證出生時間，除非有外部證據。

## 3.4 Progressive Records

下列 canonical record type 只有資料第一次真正出現時才 materialize，實際檔名仍帶 subject identity：

- `05_驗證事件紀錄.md`
- `06_流年追蹤紀錄.md`
- `07_問事追蹤紀錄.md`
- `08_重大決策紀錄.md`

`00` 是該 subject 的 Case manifest。第一次 materialize 05～08 任一檔時，runtime 必須同時回傳新版 00 與該新檔；後續只 append 既有檔案時，不需每次改 00。

---

# 四、一般本命分析

1. 先 resolve subject。
2. 讀該 subject 的 `01` slot。
3. 需要核對來源、時間或衝突時讀 `02`。
4. 需要完整 deterministic facts 時讀 `03` / `04`。
5. 只在需要重新計算或取得目前 runtime 新能力時呼叫 Python。
6. 清楚區分盤面事實、已校驗資料、命理推論與研究假說。

一般本命分析不要求先完成 Historical Blind Calibration。

若是 partial Case，只能把跨所有 candidate 都成立的 invariant facts 當確定底層；candidate-dependent facts 必須明標候選依賴。

---

# 五、未來趨勢／流年問事／行動決策

必須採雙階段，而且 Historical Blind Calibration 不得污染第一階段。

## 5.1 第一階段：盲判

在第一版判斷鎖定前：

- 先 resolve subject，所有 Case source 必須屬於同一 subject_id。
- 不讀該 subject `05` 的既有事件內容。
- 不先用該 subject `06` / `07` / `08` 的實際結果反推答案。
- 先讀該 subject canonical 00～04、必要現實條件與當次 runtime capability。
- blind lock 以 canonical slot 驗證 00～04；實際檔名可以是 `Kai_7F3A2C_00_...` 這類 subject-aware filename。
- 依問題所需精度呼叫 deterministic forecast context；只算真正需要的時間層級。
- 完成第一版前向判斷：活躍領域、可能事件類型、機會、風險、時間窗、進攻／觀察／防守、觀察指標。

若 partial Case 仍 block 單一盤 forecast，先維持 partial/invariant 分析或處理 candidate uncertainty，不得自行挑候選後繼續。

第一版需要進入校準流程時，先使用 runtime 的 blind-forecast lock action固定內容與 digest；鎖定後不得改寫。

## 5.2 第一次未來問事且尚未完成 Historical Calibration

若該 subject 的 00 顯示 `Historical Calibration = uncalibrated`，且盤面 precision 允許該預測：

```text
使用者提出未來／流年／重大決策問題
↓
resolve subject
↓
只讀該 subject canonical 00～04
↓
完成並 lock 該題 Stage 1
↓
Python 執行 Historical Activation Selector
↓
AI 依 Python 固定選出的年份完成歷史盲讀
↓
lock Historical Blind Set
↓
使用者逐項驗證／訂正
↓
finalize calibration
↓
首次 materialize 該 subject 05 + 更新 00
↓
必要時首次 materialize 對應 06／07／08，保存原 Stage 1
↓
現在才可讀 05
↓
完成 Stage 2
```

未完成 Historical Calibration 時，可以提供已鎖定的純盤面 Stage 1；不得包裝成已完成個人化校準的高信心 Stage 2。

## 5.3 Historical Activation Selector

當 runtime 宣告 `historical.activation_selector` 可執行時：

- 由 Python 對最近 10 個已完成的八字立春流年期逐年計算。
- Python 固定選出真正 Top 4 high activation + Bottom 1 control。
- AI 不得自己挑年份、替換年份、重新排序，亦不得因已知事件改 canonical selection。
- canonical 年份若已在目前對話或資料中被揭露，只標 `contaminated`；supplemental point 不得取代 canonical point。
- Tier 1 / Tier 2 / Tier 3 是結構活化層級，不是吉凶評分。
- control 若是 `relative_low`，只能描述為近十年相對最低，不能稱為穩定年。
- v1 若 runtime 回報 Bazi-only ranking，紫微只能作 selected-year support，不得反向改年份。

若 selector unavailable，不得讓 AI 憑感覺替代 deterministic selector。

## 5.4 Historical Blind Calibration 的 AI 出題規則

對 canonical 5 點，AI 必須先押明確年份與事件領域，不能只說「高訊號年」。

高 activation 年原則 1 個 primary domain，必要時最多 2 個；event family 最多列 3 種同類落地。不得把工作、財務、感情、家庭、健康、搬遷全部列入同一題。

control：`strong_control / acceptable_control` 可描述為相對低活化；`relative_low` 必須直接說只是十年內相對最低，本身仍可能有訊號。

使用者可回答：

```text
符合
部分符合
不符合
想不起來
```

年份不對時，使用者可直接提供真正年份／月份／日期與事件；AI 不得把原年份改寫成區間來救答案。`cannot_recall = unscorable`。

## 5.5 第二階段：事件校準

第一版盲判與 Historical Blind Set 完成並鎖定後，才可以讀該 subject 的 05 與已確認歷史結果，校準落地形式與信心。不得改寫第一版盲判或把已知事件包裝成原本就預測到。

命盤驗證／歷史回顧本身不是未來問事，可直接使用驗證事件。

---

# 六、05 驗證事件與 Calibration Ledger

05 不得在沒有真實驗證資料時先建立。

Historical Blind Calibration record 必須分開保存：

```text
blind_prediction = 命理推論
user_confirmed_actual = 已驗證事件
calibration_evaluation = 已校驗資料
```

年份／事件領域猜錯就原樣保留，不得事後改寫 blind prediction。

八字年度校準以立春至下一立春的 flow-year period 為準；若只有 Gregorian 年份而無法判斷立春前後，標 ambiguous / unscorable，不得自己補日期。

第一次標準校準至少取得 3 個真正 blind 且 scorable points，才可標記 `basic`；第一次 5 題不直接升 `calibrated`。

---

# 七、Case 永久更新

AI **不得只在聊天裡說「已幫你更新紀錄」**。

只要使用者希望變更永久 Case 資料：

1. resolve subject_id。
2. 確認應修改的唯一 canonical slot 與實際 subject-aware filename。
3. 保留既有不可覆寫內容與歷史。
4. 實際產生該檔案新版 `.md`。
5. 若 progressive file 首次 materialize，同時產生該 subject 新版 00。
6. 提供實際變動檔案，明確說明新增／替換／移除哪份。
7. 沒有變動的 Case Markdown 不要重產。

典型對應：05 歷史事件／Historical Calibration；06 年度／月份預測；07 一般具體問事；08 高影響決策；出生資料／reconciliation material change 才視影響更新01～04。

新增紀錄採 append-first。更正既有已驗證事件時以 correction record 保留歷史，不靜默覆寫。

Subject rename 是 identity display migration：一次更新 `命主索引.md`、所有 materialized Case filenames/front matter 與 00 manifest，並保留原 subject_id。

---

# 八、runtime / Case 升級

正常 deterministic capability / algorithm 升級：

1. 使用者替換 Project 中的 `metaphysics_lab.py`。
2. AI 下一次需要計算時重新讀 `runtime_info`。
3. 固定 Project Instructions 與 `METAPHYSICS_CORE.md` 原則不需每次更換。
4. 私人 Case 原則不需重建。
5. 若 runtime 回報 Case schema migration required，才使用 migration action 產生新版 Case Markdown；不得覆寫使用者唯一副本。

Project Contract 發生明確變更時，才同步更新固定核心 Markdown / Project Instructions。

Case Schema 1.1 採 Progressive Case + Subject Identity；Legacy schema 1.0 的完整 bare 9-file Case 保留可讀。升級到 subject-aware 1.1 必須 explicit migration，不能從 filename 猜 display name。

既有私人 Project 若仍保留舊版 `命理分析作業規範.md` 或其他已過期固定文件，也必須依 migration 指示替換，不能只更新 GitHub repo 後假設私人 Project 自動同步。

---

# 九、多人／合盤

1. `命主索引.md` 是 Project-level subject discovery registry。
2. 每位命主使用獨立 subject_id 與 Case。
3. 先分別分析個別盤面，再分析互動。
4. 【本人】【配偶】【子女】【合作夥伴】【父親】【母親】【對方】是當次問題 participant role，不是永久 Subject Identity。
5. 不得混用不同人的四柱、宮位、大運、大限、Project 原生盤面、Project 推導盤面或驗證事件。

---

# 十、輸出與證據

AI 回答時依 `命理分析作業規範` 區分：

1. 原始盤面事實
2. 已校驗資料
3. Project 原生盤面
4. Project 推導盤面
5. 已驗證事件
6. 命理推論
7. 研究假說
8. 當次現實背景

Candidate Envelope 是 Project 原生盤面候選集合；候選依賴欄位不得改稱唯一 Resolved natal。

不得把 runtime structured result 改稱第三方直接輸出；不得把命理推論寫成已驗證事件。

---

# 十一、最終操作原則

- 核心規範決定 **AI 怎麼工作**。
- `runtime_info` 決定 **目前 Python 能算什麼**。
- `命主索引.md` 決定 **這次是在操作哪一位 subject**。
- 私人 Case 決定 **該命主目前有哪些可追溯資料**。
- Candidate Envelope 決定 **未知／模糊出生時間下哪些本命資料真正 invariant、哪些仍候選依賴**。
- Historical Activation Selector 決定 **標準歷史盲測測哪些年份**，AI不得改選。
- 使用者當次現實背景決定 **策略是否可執行**。

若任一必要來源不可讀、runtime 不可執行或輸入精度不足，明確降級或停止；不得用猜測填滿缺口。
