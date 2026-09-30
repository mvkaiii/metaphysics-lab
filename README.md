# Metaphysics Lab

Metaphysics Lab 是一套把**命盤計算**和**AI 命理解讀**分開的命理分析系統。

核心概念很簡單：**Python 負責固定計算，AI 負責解讀。** 一般使用者不需要先理解程式碼儲存庫、模組或功能狀態，也不需要自己決定八字／紫微該執行哪個程式。

目前最新正式版本為 **v1.8.0｜2026-09-30**。v1.8.0 維持 **Case Schema 1.1 / Project Contract 1.2**，既有 Case 不需要重建；AI Distribution Runtime 為 `1.4-exp`。本版新增公開的八字大運時間軸，並採用預設精簡呈現；仍在實驗階段的功能不會因此自動升級為穩定狀態。

正式下載頁：[Metaphysics Lab v1.8.0](https://github.com/mvkaiii/metaphysics-lab/releases/tag/v1.8.0)。到 GitHub 正式發布頁的**下載區（GitHub 顯示為 Assets）**，優先下載 `Metaphysics-Lab-v1.8.0-User-Package.zip`。**不要把 GitHub 自動產生的原始碼壓縮檔（Source code ZIP）當成使用者安裝包。**

## 最新版安裝／升級操作

1. 下載 `Metaphysics-Lab-v1.8.0-User-Package.zip`。
2. 解壓縮後確認只有 `metaphysics_lab.py`、`metaphysics_core.md`、`project_instructions.txt` 三個正式檔案。
3. 新 Project：上傳 `metaphysics_lab.py` 與 `metaphysics_core.md`，再把 `project_instructions.txt` 全文貼到 Project Instructions。
4. 從 v1.7.1 升到 v1.8.0：**三檔一起同步**。v1.8 同時更新執行程式、核心呈現規則與 Project Instructions。
5. **保留** `命主索引.md`、私人 Case、本命資料、驗證事件、追蹤紀錄與所有已鎖定預測；Case Schema 仍是 1.1，不要重建 `subject_id`、清空 05～08，或重做既有已鎖定的第一版盲判。
6. 完成後請 AI 執行 `runtime_info`，確認 Release `1.8.0`、Project Contract `1.2`、Runtime Schema `1.1`、Case Schema `1.1`、AI Distribution Runtime `1.4-exp`、Capability Manifest `1.0`。

## 第一次建立命理專案

使用者安裝包（User Package）內固定只有下面 3 個檔案，也可以從同一個正式發布頁的下載區個別下載。

| 用途 | 實際檔名 | 你要做什麼 |
|---|---|---|
| **命理計算程式** | `metaphysics_lab.py` | 上傳到 ChatGPT Project 或 Claude Project |
| **命理分析核心規則** | `metaphysics_core.md` | 上傳到 Project |
| **Project 設定指令** | `project_instructions.txt` | 打開後，把全文貼到 Project Instructions |

如果你已經是 **v1.7.1**，升到 **v1.8.0** 請同步三檔：`metaphysics_lab.py`、`metaphysics_core.md` 與 `project_instructions.txt`。這是因為 v1.8 除了更新執行程式，也加入大運視覺化公開功能與預設精簡呈現規則；Case Schema 仍維持 1.1，不需要重建私人 Case。

設定完成後，先對 AI 說：

> **「開始建立我的命理專案。」**

### 首次建立流程：先確認出生資料

AI 先確認建立完整本命所需的出生資料，只追問缺少欄位：

- 性別
- 西元（Gregorian）出生日期
- 出生時間
- 出生地

目前單一檔案版的執行程式已內建固定版本的核心曆法元件，以及一份有限但有版本管理的**離線地點資料庫（offline registry）**。出生地若能在這份資料庫中找到，就可以直接建立 Project 原生命盤，**不需要網路**，也**不需要額外 Python 套件**。

出生地解析順序固定：

1. 若使用者或 AI 執行環境已提供完整的 `resolved_location`，直接使用並保留來源與版本紀錄。
2. 否則先查 Project 內建的離線地點資料庫。
3. 內建地點資料庫找不到時，系統預設停止並要求補充資料，不會自行猜測；只有明確啟用網路地點查詢時，才改用網路服務協助解析。
4. 若同一個離線地名別名對應多個候選地點，直接回報無法唯一判定，不用網路結果偷偷覆蓋。

內建離線地點資料庫不是全球地理資料庫；它的涵蓋範圍有限，而且有版本管理。未支援的地點可以提供已確認的座標與 IANA 時區，或明確選擇啟用網路地點查詢。

Astralium 仍然可以提供八字／紫微第三方排盤，但現在定位為**可選的第三方本命來源（External Natal Source）／交叉校驗來源**，不是首次建立 Project 的必要前置步驟，也不是 Project 原生命盤的計算依據。

完整命盤、流年、合盤或重大決策需要較多推理；如果你使用的平台提供**較高推理強度**或深度思考模式，可以優先使用。

詳細步驟：

- [快速開始](docs/快速開始.md)
- [安裝到 ChatGPT / Claude Project](docs/安裝到ChatGPT-Project.md)
- [命盤資料準備指南](docs/命盤資料準備指南.md)
- [Astralium 資料取得指南](docs/Astralium資料取得指南.md)
- [更新與版本同步](docs/更新與版本同步.md)
- [v1.8.0 發布說明](docs/發布說明-v1.8.0.md)

## 命盤資料可以怎麼提供？

目前建議依下面順序使用：

1. **只有出生資料**：提供性別、出生日期、出生時間與出生地。內建離線地點資料庫支援的地點可以直接建立 Project 原生八字／紫微命盤；不需要網路，也不需要額外 Python 套件。
2. **出生資料 + Astralium**：若手上已有 Astralium 八字／紫微命盤，可以一起提供，作為第三方本命來源，與 Project 原生命盤做校驗／交叉比對。
3. **只有第三方排盤**：只有 Astralium、其他排盤網站、命理軟體或命理師提供的結構化命盤，也可以先保存與分析；系統不會因此假裝已完成 Project 原生計算。

第三方排盤與 Project 自己計算的結果會分開保存；有差異就明確標示，不會為了讓兩邊看起來一致而互相覆寫。

## 出生時間不確定也不要亂猜

如果只知道「大概晚上7、8點」、一段時間範圍，甚至完全不知道出生時間，系統不會自行補 12:00、區間中點或任意時辰。

資料足夠時，系統可以保留多個候選狀態，只把所有候選都一致的部分視為已確定資料；需要唯一出生時辰才能成立的結論則保持未確定。這類流程稱為**候選盤面集合（Candidate Envelope）**，詳細規則見[命盤資料準備指南](docs/命盤資料準備指南.md)。

## 一個 Project 可以管理多人

你可以在同一個 Project 管理本人、家人、朋友或合作對象。系統會先辨識目前是在問哪一位命主，再讀取對應的私人 Case，避免不同人的命盤與事件紀錄混在一起。

公開文件中的姓名、日期與識別碼都是**虛構示例**。例如某位命主可能顯示為 Alex，但真正私人 Project 可以使用你自己習慣的暱稱或標籤。

## 問未來時，先看盤再校準

流年、未來趨勢與重大決策採「**先盲判，再事件校準**」：第一版先根據盤面與必要現實條件完成，不先偷看已驗證事件；之後才用你已確認的人生事件校準落地形式與信心。

Project 原生本命與由本命／運限／目標時間建立的 **Project 推導盤面** 會分開標示，避免把衍生計算冒充原始第三方資料。

## v1.7 的使用導航與可靠性

v1.7 新增**引導式追問（Guided Inquiry）**：AI 可以主動顯示 3～4 個後續詢問方向，預設 3 個，但你仍可自由輸入任何問題；這些建議只是導航，不是新的命理證據，也不能提高原本證據允許的結論具體程度或信心。

**個案資料檢查（Case Doctor）**用來找出資料權限來源、舊版資料、重複資料與內容衝突，並可先提供不會直接修改檔案的校驗預演；它不會自行刪除使用者檔案。**前瞻驗證 2.0（Prospective Validation 2.0）**會區分乾淨前瞻、條件式前瞻、當時未知但已存在的事實，以及事後校準情境，避免把已知安排混入乾淨預測命中率。

## 如果 AI 無法執行 Python

AI 必須明確說明**無法執行 Python**，不得假裝已跑過命盤計算。這時可以先保留 Astralium 等第三方本命來源；若仍需要 Project 原生計算，也可以在本機使用同一個命理計算程式：

```bash
python metaphysics_lab.py request --input request.json --pretty
```

把輸出的 JSON 結果交回 AI，再繼續解讀。

## 隱私

私人出生資料、`命主索引.md`、Case Markdown、事件紀錄、PDF、截圖與**私人 Astralium 原始命盤資料**不應提交到公開／共用 GitHub 儲存庫；這些資料留在你自己的 Project 或本機。

## 想看技術細節？

一般使用者不需要閱讀開發階段（Phase）或能力狀態表。若你要追蹤技術版本、完整變更與架構：

- [VERSION.md](VERSION.md)：技術版本與能力狀態
- [CHANGELOG.md](CHANGELOG.md)：正式版本與尚未發布的變更
- [架構說明](docs/架構說明.md)
- [資料治理](docs/資料治理.md)

目前實際可執行的能力仍以程式回傳的 `runtime_info` 為技術權威來源；正式發版不會自動把仍在實驗中的能力升級為穩定狀態（Stable）。這項規則主要供開發與稽核使用，一般使用者不需要自行判讀。