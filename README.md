# Metaphysics Lab

Metaphysics Lab 是一套把**命盤計算**和**AI 命理解讀**分開的命理分析系統。

核心概念很簡單：**Python 負責固定計算，AI 負責解讀。** 一般使用者不需要先理解 repo、模組或 capability，也不需要自己決定八字／紫微該跑哪個程式。

目前正式版本為 **v1.3.0（2026-08-23）**。

## 第一次使用

到 GitHub Release 頁面下方的**下載區（GitHub 顯示為 Assets）**，只下載下面 3 個檔案即可。**不需要下載 Source code，也不需要解壓縮原始碼。**

| 用途 | 實際檔名 | 你要做什麼 |
|---|---|---|
| **命理計算程式** | `metaphysics_lab.py` | 上傳到 ChatGPT Project 或 Claude Project |
| **命理分析核心規則** | `metaphysics_core.md` | 上傳到 Project |
| **Project 設定指令** | `project_instructions.md` | 打開後，把全文貼到 Project Instructions |

設定完成後，先對 AI 說：

> **「開始建立我的命理專案。」**

### 目前建議的首次建立流程（過渡期）

在 **Portable Offline Natal Pipeline** 完成並通過正式驗證前，第一次建立命理 Project 時，**建議優先先取得 Astralium 的八字與紫微命盤，再貼回 Project**。

這是目前的過渡期建議流程，目的是避免不同 ChatGPT／Claude Python sandbox 缺少必要套件、無法連網或無法可靠解析出生地時，使用者只輸入出生年月日時與出生地就直接遇到錯誤。

建議流程：

1. 完成上面 3 個檔案的 Project 設定。
2. 對 AI 說：**「開始建立我的命理專案。」**
3. AI 應先請你開啟 Astralium 官方網站：<https://getastralium.com/>。
4. 在 Astralium 輸入你的性別、出生日期、出生時間與出生地，分別取得**八字命盤**與**紫微命盤**。
5. 把 Astralium 產出的八字與紫微資料貼回 Project；若目前只有其中一份，也可以先貼已有的資料。
6. Metaphysics Lab 會先把這些資料保存為 **External Natal Source**，再依目前 runtime 能力進行 Project 原生計算、交叉校驗與後續分析。

如果目前的 AI 執行環境無法完成 Project 原生本命計算，系統必須保留 Astralium 原始資料並明確標示來源，**不得假裝已完成 Project 原生計算**。

Astralium 仍然不是 Metaphysics Lab 的永久必要依賴。等 Portable Offline Natal Pipeline 完成並通過 clean-environment qualification 後，正式主要流程會再回到「只有出生資料即可建立 Project 原生命盤」，Astralium 則回到可選的交叉校驗來源。

完整命盤、流年、合盤或重大決策需要較多推理；如果你使用的平台提供**較高推理強度**或深度思考模式，可以優先使用。

詳細步驟：

- [快速開始](docs/快速開始.md)
- [安裝到 ChatGPT / Claude Project](docs/安裝到ChatGPT-Project.md)
- [命盤資料準備指南](docs/命盤資料準備指南.md)
- [Astralium 資料取得指南](docs/Astralium資料取得指南.md)
- [更新與版本同步](docs/更新與版本同步.md)

## 命盤資料可以怎麼提供？

目前建議依下面順序使用：

1. **推薦：出生資料 + Astralium**：先提供出生資料，並貼上 Astralium 八字／紫微命盤。現階段這是最穩定的首次建立方式，也能留下後續 Project Natal reconciliation 與 qualification 所需的 External 基準資料。
2. **只有第三方排盤**：只有 Astralium、其他排盤網站、命理軟體或命理師提供的結構化命盤，也可以先保存與分析；系統不會因此假裝已完成 Project 原生計算。
3. **只有出生資料**：Metaphysics Lab 的正式產品方向仍是由性別、出生日期、出生時間與出生地建立 Project 原生八字／紫微命盤；但在 Portable Offline Natal Pipeline 完成前，不保證所有 ChatGPT／Claude 執行環境都能直接完成這條流程。

第三方排盤與 Project 自己計算的結果會分開保存；有差異就明確標示，不會為了讓兩邊看起來一致而互相覆寫。

## 出生時間不確定也不要亂猜

如果只知道「大概晚上7、8點」、一段時間範圍，甚至完全不知道出生時間，系統不會自行補 12:00、區間中點或任意時辰。

資料足夠時，系統可以保留多個候選狀態，只把所有候選都一致的部分視為已確定資料；需要唯一出生時辰才能成立的結論則保持未確定。這類技術流程在系統內稱為 Candidate Envelope，詳細規則見[命盤資料準備指南](docs/命盤資料準備指南.md)。

## 一個 Project 可以管理多人

你可以在同一個 Project 管理本人、家人、朋友或合作對象。系統會先辨識目前是在問哪一位命主，再讀取對應的私人 Case，避免不同人的命盤與事件紀錄混在一起。

公開文件中的姓名、日期與識別碼都是**虛構示例**。例如某位命主可能顯示為 Alex，但真正私人 Project 可以使用你自己習慣的暱稱或標籤。

## 問未來時，先看盤再校準

流年、未來趨勢與重大決策採「**先盲判，再事件校準**」：第一版先根據盤面與必要現實條件完成，不先偷看已驗證事件；之後才用你已確認的人生事件校準落地形式與信心。

Project 原生本命與由本命／運限／目標時間建立的 **Project 推導盤面** 會分開標示，避免把衍生計算冒充原始第三方資料。

## 如果 AI 無法執行 Python

AI 必須明確說明**無法執行 Python**，不得假裝已跑過命盤計算。這時可以先保留 Astralium 等 External Natal Source；若仍需要 Project 原生計算，也可以在本機使用同一個命理計算程式：

```bash
python metaphysics_lab.py request --input request.json --pretty
```

把輸出的 JSON 結果交回 AI，再繼續解讀。

## 隱私

私人出生資料、`命主索引.md`、Case Markdown、事件紀錄、PDF、截圖與**私人 Astralium raw chart** 不應提交到公開／共用 GitHub repo；這些資料留在你自己的 Project 或本機。

## 想看技術細節？

一般使用者不需要閱讀開發 Phase 或能力狀態表。若你要追蹤技術版本、完整變更與架構：

- [VERSION.md](VERSION.md)：技術版本與能力狀態
- [CHANGELOG.md](CHANGELOG.md)：正式版本與尚未發布的變更
- [架構說明](docs/架構說明.md)
- [資料治理](docs/資料治理.md)

目前實際可執行的能力仍以程式回傳的 `runtime_info` 為技術權威來源；正式發版不會自動把仍在實驗中的能力升為 Stable。這項規則主要供開發與稽核使用，一般使用者不需要自行判讀。