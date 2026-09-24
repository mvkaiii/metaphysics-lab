# 安裝到 ChatGPT / Claude Project

這份文件只處理安裝與第一次啟動。一般使用者不需要理解開發 repo，也不需要自己拼裝 Python 模組。

> 以下姓名、日期與識別碼都是**虛構示例**。

## 1. 下載與安裝

目前最新正式版本為 **v1.7.0｜2026-09-24**，GitHub Release `v1.7.0` 已正式建立。v1.7.0 維持 **Case Schema 1.1**，既有私人 Case 不需要重建。

優先下載 `Metaphysics-Lab-v1.7.0-User-Package.zip`；解壓後就是下面三個檔案。也可以在 Assets 單獨下載。

| 用途 | 實際檔名 | 安裝方式 |
|---|---|---|
| **命理計算程式** | `metaphysics_lab.py` | 上傳到 Project |
| **命理分析核心規則** | `metaphysics_core.md` | 上傳到 Project |
| **Project 設定指令** | `project_instructions.txt` | 全文貼到 Project Instructions |

實際操作：

1. 上傳 `metaphysics_lab.py` 到 Project。
2. 上傳 `metaphysics_core.md` 到 Project。
3. 開啟 Project Instructions，把 `project_instructions.txt` 的全文複製進去。

也就是**兩個上傳檔＋一份貼進 Project Instructions 的文字**。不需要下載 Source code，也不需要解壓縮原始碼。

如果你是從 **v1.6.0 升級到 v1.7.0**，請三個檔案一起同步，不要只換 Runtime。保留 `命主索引.md`、既有 Case、驗證事件、流年／問事／重大決策紀錄與已鎖定預測；Case Schema 1.1 沒有 migration，也不要做破壞性 Case 重建。

ChatGPT Project 與 Claude Project 的介面名稱可能不同，但概念相同。

## 2. 推理模式

完整本命、流年、多人合盤或重大決策通常需要較多推理。如果平台提供**較高推理強度**或深度思考模式，可以優先使用；不要把文件綁死在某個平台特定的模式名稱。

## 3. 第一次啟動

三個檔案設定完成後，直接說：

> **「開始建立我的命理專案。」**

AI 應自行進入初始化流程，而不是要求你先讀技術文件。

## 4. 命盤資料有三種提供方式

### 只有出生資料

通常提供性別、出生日期、出生時間、出生地，由 Metaphysics Lab 建立 Project 原生命盤。

### 出生資料 + Astralium

如果另有 Astralium 八字／紫微或其他第三方排盤，可以一起提供作為**可選**交叉校驗來源。

### 只有第三方排盤

如果目前只有 Astralium 或其他結構化命盤，也可以先保存 External 資料；系統不會把第三方資料冒充成 Project 已自行計算的命盤。

## 5. 多人 Project

同一個 Project 可以管理多人。AI 會先讀取或建立：

```text
命主索引.md
```

每位命主都有自己的 `subject_id`，用來避免不同人的 Case 混在一起；這個 ID 不由姓名、生日或出生地推導。

虛構範例：

```text
subject_display_name: Alex
subject_id: subj_7f3a2c91d4e8
subject_short_id: 7F3A2C
```

Case Schema 1.1 的實際檔名格式是：

```text
<filename_label>_<SUBJECT_SHORT_ID>_<slot>_<canonical_title>.md
```

例如：

```text
Alex_7F3A2C_01_命盤核心摘要.md
```

`01_命盤核心摘要.md` 是內部 canonical slot；一般使用者看到的實際檔案會帶命主名稱與短識別碼。

## 6. 出生時間不確定

如果只知道大概時段，AI 不得自行補一個精確時間。

當 `runtime_info` 顯示 `natal.candidate_envelope` 可執行，而且必要出生資料足夠時，系統可以建立 **Candidate Envelope**，保留不同時間可能造成的候選狀態。

這時可以建立 `partial` Case；所有候選一致的部分可先使用，需要唯一出生時間才能成立的結論則保持未確定。即使候選最後只剩一種盤面結構，也不代表原始出生時間已被外部證實。

## 7. 第一次 Case 會看到什麼

建立完成後，系統先建立基礎 Case，不會先產生一堆空白追蹤檔。虛構命主 Alex 例如：

```text
Alex_7F3A2C_00_專案索引.md
Alex_7F3A2C_01_命盤核心摘要.md
Alex_7F3A2C_02_命盤資料校驗紀錄.md
Alex_7F3A2C_03_八字結構化資料包.md
Alex_7F3A2C_04_紫微基礎資料包.md
```

之後真的有驗證事件、流年追蹤、一般問事或重大決策時，才逐步新增對應紀錄。

v1.7 的 **Case Doctor** 會先做只讀診斷，必要時提出 reconciliation dry-run；它不會自行刪除 legacy 或其他使用者檔案。

## 8. 問未來的順序

如果需要歷史事件校準，AI 會先完成未受歷史事件影響的第一版盤面判斷，再請你驗證過去事件，最後才做第二階段校準。這樣可以避免先知道答案後再修改第一版預測。

v1.7 可主動顯示 **3～4 個**後續詢問方向，**預設 3 個**；建議只是導航，不限制自由輸入，也不能提高原本證據允許的 specificity 或信心。

## 9. Astralium／第三方盤的資料邊界

第三方盤是 External source，不是安裝必要條件。若同時有 Project 自算命盤與第三方盤，應保留：

```text
External / Project / Resolved
MATCH / EQUIVALENT / CONFLICT / NOT_COMPARABLE
```

兩邊原始資料不互相覆寫。

## 10. 如果 AI 無法執行 Python

Project 能保存 Python 檔，不代表每次對話都能執行 Python。

若當次環境**無法執行 Python**，AI 必須明確說明，**不得假裝**已經跑過新的命盤計算。

本機 fallback：

```bash
python metaphysics_lab.py request --input request.json --pretty
```

或：

```bash
python metaphysics_lab.py request --input - --pretty
```

把 JSON 結果交回 AI 後繼續分析。

## 11. 平常更新

一般 Runtime-only 更新通常只需要替換 Project 裡的 `metaphysics_lab.py`；但 **v1.6.0 → v1.7.0** 因 Project Contract 升到 1.2，請把 `metaphysics_lab.py`、`metaphysics_core.md`、`project_instructions.txt` 三個發行面一起同步。

`命主索引.md` 與私人 Case 不需要重建；本次 Case Schema 仍維持 1.1。

## 12. 隱私

`命主索引.md`、出生資料、Case Markdown、事件紀錄、第三方 raw chart、PDF 與截圖都屬私人資料，不要提交回公開／共用 GitHub repo。

完整升級規則與 v1.7 邊界請見[更新與版本同步](更新與版本同步.md)與[發布說明-v1.7.0](發布說明-v1.7.0.md)。