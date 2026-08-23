# 安裝到 ChatGPT / Claude Project

這份文件給一般使用者。安裝 Metaphysics Lab 不需要理解開發 repo，也不需要自己拼裝多個 Python 模組。

## 安裝檔案

你需要三個發行檔：

```text
metaphysics_lab.py
METAPHYSICS_CORE.md
PROJECT_INSTRUCTIONS.md
```

安裝方式固定為：

1. 上傳 `metaphysics_lab.py` 到 Project。
2. 上傳 `METAPHYSICS_CORE.md` 到 Project。
3. 開啟 Project Instructions，把 `PROJECT_INSTRUCTIONS.md` 的全文複製進去。

所以是**兩個上傳檔＋一份貼進 Project Instructions 的文字**。

ChatGPT Project 與 Claude Project 的介面名稱可能不同，但概念相同：兩個檔案放入專案知識／檔案區，最高層 Instructions 放入專案指示區。

## 建議模型／推理設定

Metaphysics Lab 的完整分析包含多步 deterministic 資料、八字／紫微交叉、證據層級、Historical Blind Calibration 與未來問事雙階段流程，因此建議：

- **High reasoning：完整本命、流年、多人合盤、重大決策的預設。**
- Medium：一般分析、Case 維護、較單純問題。
- Instant：適合快速行政操作；不建議作為完整命理解讀預設。

平台的具體模型名稱會變動，因此 Project Instructions 不硬編某一個模型名稱；重點是選擇當下平台提供的高推理模式。

## 第一次啟動

三個發行檔設定完成後，直接說：

> **開始建立我的命理專案。**

AI 應依 `PROJECT_INSTRUCTIONS.md` 與 `METAPHYSICS_CORE.md` 自動進入初始化流程，而不是要求你閱讀技術文件。

若尚未有 Case，AI 只收集缺少的出生資料。完整 Mode A 通常是：

- 性別
- Gregorian 出生日期
- 出生時間
- 出生地

出生時間不確定時，AI 不得自行補成精確分鐘；地點有多個合理候選時，也不得自己猜。

## 三個發行檔的責任邊界

### `metaphysics_lab.py`

只負責 deterministic 工作：

- runtime capability / dependency 狀態
- 本命建立與 reconciliation
- 八字／紫微可重現計算
- forecast context
- Historical Activation Selector
- Historical Calibration lock / finalize 所需的 deterministic 資料治理
- Case Markdown export / validation / migration / progressive materialization

它不負責自由文字的命理解讀，也不替使用者做人生決策。

### `METAPHYSICS_CORE.md`

固定提供 AI 工作流程與分析治理，包括：

- task classification
- 證據／資料層級
- 先盲判、再事件校準
- Historical Blind Calibration
- Input Precision Gate
- Progressive Case 建立與更新規則
- runtime 不可執行時的 fallback

### `PROJECT_INSTRUCTIONS.md`

是最高層 AI 指示，負責：

- 角色與語氣
- 八種資料類型
- External / Project / Resolved
- 八字／紫微／奇門分工
- 高風險領域限制
- 禁止事項與信心標示

它的內容要放在 Project Instructions，不是當成一般知識檔讓 AI 自己猜何時讀。

## 建立 Case：第一次只建立 00～04

第一次本命資料完成後，AI 應先產生五份 Base Case：

```text
00_專案索引.md
01_命盤核心摘要.md
02_命盤資料校驗紀錄.md
03_八字結構化資料包.md
04_紫微基礎資料包.md
```

把這五份加入自己的 Project。它們是私人 Case，不會被共用 runtime 更新自動覆蓋。

其餘 record type 不先建立空檔，而是在第一次真正有內容時 materialize：

```text
05_驗證事件紀錄.md    ← Historical Blind Calibration 完成或首次新增已確認事件
06_流年追蹤紀錄.md    ← 首次永久保存流年／年度預測
07_問事追蹤紀錄.md    ← 首次永久保存一般問事
08_重大決策紀錄.md    ← 首次永久保存重大決策
```

所以 00～08 是完整 Case record type 集合，不代表第一次初始化就一定有九個實體檔案。

## Historical Blind Calibration

Historical Calibration 的年份不能由 AI 自己挑。

若需要校準，runtime 會以目前 Case 的 deterministic 八字基礎執行 `historical.activation_selector`：

1. 取最近 10 個已完整結束的 Bazi flow-year periods，以立春為界。
2. 對 10 年全部依固定 Tier 1 / Tier 2 / Tier 3 relation profile 計算 structural activation。
3. 使用 deterministic rank vector 排序。
4. canonical selection 固定取真正 Top 4 high + Bottom 1 control。
5. AI 只能解讀這 5 年，不能因聊天內容、已知事件或想讓答案更漂亮而換年。

AI 會先給出明確的「年份＋事件領域／事件形式」盲讀，再請使用者逐題回答：符合／部分符合／不符合／想不起來。若實際事情發生在別的年份，直接告訴 AI 正確年份與事件；原始盲讀不得被改寫。

`05_驗證事件紀錄.md` 只在使用者確認實際事件後首次建立，並區分：

- 原始歷史盲讀：命理推論
- 使用者確認實際事件：已驗證事件
- timing / domain / event-form 評價：已校驗資料

## 第一次問未來時

若 Case 尚未完成 Historical Calibration，而使用者第一次問流年／未來趨勢／行動決策，AI 必須先：

1. 只讀 00～04 與必要現實條件。
2. 完成該問題的 Stage 1 盲判並鎖定。
3. 才執行 Historical Blind Calibration。
4. 建立 05 後進入 Stage 2 事件校準。

這個順序是為了避免先知道歷史答案後污染第一版未來盲判。

## 有 Astralium／第三方命盤時

第三方盤是可選 External source，不是安裝必要條件。

若同時存在 Project deterministic natal 與 external structured chart，AI 應保留：

```text
External / Project / Resolved
MATCH / EQUIVALENT / CONFLICT / NOT_COMPARABLE
```

不能為了讓盤看起來一致而改寫任何一方 raw view。

## 如果 AI 無法執行 Python

Project 能保存 Python 檔，不代表每次對話都有 Python execution。

若當次環境**無法執行 Python**，AI 必須明確說明，**不得假裝**已經跑過 `metaphysics_lab.py`。

本機 fallback：

```bash
python metaphysics_lab.py request --input request.json --pretty
```

或：

```bash
python metaphysics_lab.py request --input - --pretty
```

把 JSON 結果交回 AI 後繼續分析。這個 fallback 使用的是同一個發行 runtime，因此不會另建第二套命盤算法。

## 平常更新

一般 Runtime 更新只需要替換 Project 裡的 `metaphysics_lab.py`。

`METAPHYSICS_CORE.md`、Project Instructions 與私人 Case 不應因每一次 runtime 更新就重建；只有 Project Contract 或 Case Schema 明確變更時才照 migration 指示處理。

完整規則見 [更新與版本同步](更新與版本同步.md)。

## 隱私

出生資料、Case Markdown、Historical Calibration 回答、私人事件、raw third-party chart、PDF 與截圖不要提交回共用 GitHub repo。共用發行檔本身不得包含私人 Case 資料。
